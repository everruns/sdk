"""Server-Sent Events (SSE) streaming with automatic reconnection.

Implements robust SSE streaming with:
- Automatic reconnection on disconnect
- Server retry hints
- Graceful handling of `disconnecting` events
- Exponential backoff for unexpected disconnections
- Resume from last event ID via `since_id`
"""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, AsyncIterator, Optional

import httpx
from httpx_sse import aconnect_sse

from everruns_sdk.models import Event

if TYPE_CHECKING:
    from everruns_sdk.client import Everruns

logger = logging.getLogger(__name__)

# Default retry delay when server doesn't provide a hint
DEFAULT_RETRY_MS = 1000
# Maximum retry delay for exponential backoff
MAX_RETRY_MS = 30_000
# Initial retry delay for exponential backoff
INITIAL_BACKOFF_MS = 1000
# Read timeout for detecting stalled connections (2 minutes)
READ_TIMEOUT_SECS = 120


@dataclass
class StreamOptions:
    """Options for SSE streaming."""

    exclude: list[str] = field(default_factory=list)
    since_id: Optional[str] = None
    max_retries: Optional[int] = None

    @classmethod
    def exclude_deltas(cls) -> "StreamOptions":
        """Create options that exclude delta events."""
        return cls(exclude=["output.message.delta", "reason.thinking.delta"])


@dataclass
class DisconnectingData:
    """Data from a disconnecting event."""

    reason: str
    retry_ms: int


class EventStream:
    """A stream of SSE events from a session with automatic reconnection.

    This stream handles:
    - Graceful `disconnecting` events from the server
    - Unexpected connection drops with exponential backoff
    - Server retry hints
    - Automatic resume using `since_id`

    Usage:
        >>> async for event in client.events.stream(session_id):
        ...     print(event.type, event.data)
    """

    def __init__(
        self,
        client: "Everruns",
        session_id: str,
        options: StreamOptions,
    ):
        self._client = client
        self._session_id = session_id
        self._options = options
        self._last_event_id: Optional[str] = None
        self._server_retry_ms: Optional[int] = None
        self._current_backoff_ms: int = INITIAL_BACKOFF_MS
        self._retry_count: int = 0
        self._should_reconnect: bool = True
        self._graceful_disconnect: bool = False

    @property
    def last_event_id(self) -> Optional[str]:
        """Get the last received event ID (for resuming)."""
        return self._last_event_id

    @property
    def retry_count(self) -> int:
        """Get the current retry count."""
        return self._retry_count

    def stop(self) -> None:
        """Stop the stream and prevent further reconnection attempts."""
        self._should_reconnect = False

    def _build_url(self) -> str:
        """Build the SSE URL with query parameters."""
        # base_url already has trailing slash, use relative path
        base = self._client._base_url.rstrip("/")
        url = f"{base}/v1/sessions/{self._session_id}/sse"
        params = []

        since_id = self._last_event_id or self._options.since_id
        if since_id:
            params.append(f"since_id={since_id}")

        for e in self._options.exclude:
            params.append(f"exclude={e}")

        if params:
            url += "?" + "&".join(params)

        return url

    def _get_retry_delay(self) -> float:
        """Get the retry delay in seconds."""
        if self._graceful_disconnect:
            # Use server hint for graceful disconnect, or short default
            return (self._server_retry_ms or 100) / 1000.0
        else:
            # Use exponential backoff for unexpected disconnects
            return self._current_backoff_ms / 1000.0

    def _update_backoff(self) -> None:
        """Update backoff delay for next retry."""
        if not self._graceful_disconnect:
            self._current_backoff_ms = min(self._current_backoff_ms * 2, MAX_RETRY_MS)

    def _reset_backoff(self) -> None:
        """Reset backoff after successful event."""
        self._current_backoff_ms = INITIAL_BACKOFF_MS
        self._retry_count = 0

    def _should_retry(self) -> bool:
        """Check if we should retry the connection."""
        if not self._should_reconnect:
            return False
        if self._options.max_retries is not None:
            return self._retry_count < self._options.max_retries
        return True

    async def __aiter__(self) -> AsyncIterator[Event]:
        """Iterate over SSE events with automatic reconnection."""
        while self._should_reconnect:
            try:
                async for event in self._connect():
                    yield event
            except _GracefulDisconnectError as e:
                # Server-initiated graceful disconnect
                self._server_retry_ms = e.retry_ms
                self._graceful_disconnect = True

                if self._should_retry():
                    self._retry_count += 1
                    delay = self._get_retry_delay()
                    logger.debug(f"Graceful reconnect in {delay}s")
                    await asyncio.sleep(delay)
                    self._graceful_disconnect = False
                    continue
                else:
                    break
            except (httpx.HTTPError, httpx.StreamError, ConnectionError) as e:
                # Unexpected disconnect - use exponential backoff
                self._graceful_disconnect = False

                if self._should_retry():
                    self._retry_count += 1
                    delay = self._get_retry_delay()
                    self._update_backoff()
                    logger.debug(f"Reconnecting in {delay}s (attempt {self._retry_count}): {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise
            except asyncio.CancelledError:
                # Clean shutdown
                break
            else:
                # Stream ended normally - always retry to handle read timeout case
                if self._should_retry():
                    self._retry_count += 1
                    delay = self._get_retry_delay()
                    self._update_backoff()
                    logger.debug(
                        f"Stream ended, reconnecting in {delay}s (attempt {self._retry_count})"
                    )
                    await asyncio.sleep(delay)
                    continue
                break

    async def _connect(self) -> AsyncIterator[Event]:
        """Connect to SSE endpoint and yield events."""
        url = self._build_url()
        logger.debug(f"Connecting to SSE: {url}")

        # Use long timeouts for SSE - connections can last hours
        timeout = httpx.Timeout(
            connect=30.0,
            read=READ_TIMEOUT_SECS,  # Detect stalled connections
            write=30.0,
            pool=30.0,
        )

        async with httpx.AsyncClient(timeout=timeout) as http:
            async with aconnect_sse(
                http,
                "GET",
                url,
                headers={
                    "Authorization": self._client._api_key.value,
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache",
                },
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    # Handle special lifecycle events
                    if sse.event == "connected":
                        logger.debug("SSE connected event received")
                        continue

                    if sse.event == "disconnecting":
                        # Parse disconnecting data for retry hint
                        try:
                            data = json.loads(sse.data)
                            disconnect_data = DisconnectingData(
                                reason=data.get("reason", "unknown"),
                                retry_ms=data.get("retry_ms", 100),
                            )
                            logger.debug(
                                f"SSE disconnecting: reason={disconnect_data.reason}, "
                                f"retry_ms={disconnect_data.retry_ms}"
                            )
                            raise _GracefulDisconnectError(disconnect_data.retry_ms)
                        except (json.JSONDecodeError, KeyError):
                            logger.debug("SSE disconnecting event received (no data)")
                            raise _GracefulDisconnectError(100)

                    # Parse and yield regular events
                    if sse.event == "message" or sse.event:
                        try:
                            data = json.loads(sse.data)
                            event = Event(**data)
                            self._last_event_id = event.id
                            self._reset_backoff()
                            yield event
                        except (json.JSONDecodeError, TypeError, KeyError):
                            # Skip malformed events
                            logger.debug(f"Skipping malformed event: {sse.event}")


class _GracefulDisconnectError(Exception):
    """Internal exception to signal graceful disconnect."""

    def __init__(self, retry_ms: int):
        self.retry_ms = retry_ms
        super().__init__(f"Graceful disconnect, retry in {retry_ms}ms")
