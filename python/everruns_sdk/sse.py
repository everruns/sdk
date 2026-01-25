"""Server-Sent Events (SSE) streaming."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, AsyncIterator, Optional

import httpx
from httpx_sse import aconnect_sse

from everruns_sdk.models import Event
from everruns_sdk.errors import EverrunsError

if TYPE_CHECKING:
    from everruns_sdk.client import Everruns


@dataclass
class StreamOptions:
    """Options for SSE streaming."""
    exclude: list[str] = field(default_factory=list)
    since_id: Optional[str] = None
    
    @classmethod
    def exclude_deltas(cls) -> "StreamOptions":
        """Create options that exclude delta events."""
        return cls(exclude=["output.message.delta", "reason.thinking.delta"])


class EventStream:
    """A stream of SSE events from a session.
    
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
    
    @property
    def last_event_id(self) -> Optional[str]:
        """Get the last received event ID (for resuming)."""
        return self._last_event_id
    
    def _build_url(self) -> str:
        """Build the SSE URL with query parameters."""
        url = f"{self._client._base_url}/v1/orgs/{self._client._org}/sessions/{self._session_id}/sse"
        params = []
        
        since_id = self._last_event_id or self._options.since_id
        if since_id:
            params.append(f"since_id={since_id}")
        
        for e in self._options.exclude:
            params.append(f"exclude={e}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    async def __aiter__(self) -> AsyncIterator[Event]:
        """Iterate over SSE events."""
        url = self._build_url()
        
        async with httpx.AsyncClient(timeout=None) as http:
            async with aconnect_sse(
                http,
                "GET",
                url,
                headers={"Authorization": self._client._api_key.value},
            ) as event_source:
                async for sse in event_source.aiter_sse():
                    if sse.event == "message" or sse.event:
                        try:
                            import json
                            data = json.loads(sse.data)
                            event = Event(**data)
                            self._last_event_id = event.id
                            yield event
                        except Exception as e:
                            # Skip malformed events
                            pass
