"""Smoke tests for SSE reconnection behavior.

Tests the actual EventStream reconnection loop with mocked _connect()
to verify:
- Bug 1: Graceful disconnects don't consume retry budget
- Bug 2: Connected event resets backoff after errors
- Bug 3: HTTP client reused across reconnections
- Bug 4: Idle timeout triggers reconnection on silent half-open connections
"""

import asyncio

import pytest

from everruns_sdk.models import Event
from everruns_sdk.sse import (
    INITIAL_BACKOFF_MS,
    EventStream,
    StreamOptions,
    _GracefulDisconnectError,
)


class MockApiKey:
    value = "test_key"


class MockClient:
    _base_url = "https://api.example.com"
    _api_key = MockApiKey()


def make_event(event_id: str, event_type: str) -> Event:
    return Event(
        id=event_id,
        type=event_type,
        ts="2024-01-01T00:00:00Z",
        session_id="sess_1",
        data={},
    )


@pytest.mark.asyncio
async def test_graceful_disconnect_preserves_retry_budget():
    """Graceful disconnect (connection_cycle) must not consume retry budget.

    With max_retries=3, the stream should survive unlimited graceful disconnects
    because they don't increment retry_count.
    """
    stream = EventStream(MockClient(), "sess_1", StreamOptions(max_retries=3))
    call_count = 0

    async def mock_connect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First connection: connected (resets backoff) + event + graceful disconnect
            stream._reset_backoff()
            yield make_event("evt_001", "output.message.started")
            raise _GracefulDisconnectError(10)
        elif call_count == 2:
            # Second connection: connected + event
            stream._reset_backoff()
            yield make_event("evt_002", "output.message.completed")

    stream._connect = mock_connect

    events = []
    async for event in stream:
        events.append(event)
        if len(events) >= 2:
            stream.stop()

    assert len(events) == 2
    assert events[0].id == "evt_001"
    assert events[1].id == "evt_002"

    # Bug 1: Graceful disconnect did NOT consume retry budget
    assert stream._retry_count == 0, "Graceful disconnect must not increment retry_count"

    # Reconnection happened
    assert call_count == 2, "Should have reconnected once"


@pytest.mark.asyncio
async def test_connected_event_resets_backoff_after_error():
    """After an unexpected disconnect, successful reconnection with `connected`
    event must reset the backoff and retry count.
    """
    stream = EventStream(MockClient(), "sess_1", StreamOptions(max_retries=5))
    call_count = 0

    async def mock_connect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First connection: connected + event + unexpected disconnect
            stream._reset_backoff()
            yield make_event("evt_001", "output.message.started")
            raise ConnectionError("connection lost")
        elif call_count == 2:
            # Second connection: connected event resets backoff (Bug 2)
            stream._reset_backoff()
            yield make_event("evt_002", "output.message.completed")

    stream._connect = mock_connect

    events = []
    async for event in stream:
        events.append(event)
        if len(events) >= 2:
            stream.stop()

    assert len(events) == 2
    assert events[0].id == "evt_001"
    assert events[1].id == "evt_002"

    # Bug 2: After successful reconnection, backoff is reset
    assert stream._current_backoff_ms == INITIAL_BACKOFF_MS, (
        "Backoff should be reset after successful reconnect"
    )
    assert stream._retry_count == 0, "Retry count should be reset after successful reconnect"

    # Two connections were made
    assert call_count == 2


@pytest.mark.asyncio
async def test_http_client_reused_across_reconnections():
    """HTTP client must be reused across reconnections for connection pooling."""
    stream = EventStream(MockClient(), "sess_1", StreamOptions(max_retries=3))

    # Get the HTTP client
    client1 = stream._get_http_client()

    # Simulate disconnect + reconnect scenario
    stream._graceful_disconnect = True
    stream._graceful_disconnect = False

    # Get the client again (as would happen on reconnection)
    client2 = stream._get_http_client()

    # Bug 3: Same client instance reused
    assert client1 is client2, "HTTP client must be reused across reconnections"

    # Cleanup
    await stream.aclose()


@pytest.mark.asyncio
async def test_idle_timeout_triggers_reconnect_on_silent_connection():
    """Idle timeout must trigger reconnection when _connect() hangs.

    Simulates a half-open TCP connection: the first _connect() yields nothing
    and hangs forever. The idle timeout fires, the stream reconnects, and the
    second _connect() delivers an event.
    """
    opts = StreamOptions(max_retries=5, idle_timeout=0.5)  # 500ms for fast test
    stream = EventStream(MockClient(), "sess_1", opts)
    call_count = 0

    async def mock_connect():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First connection: simulate connected event, then hang forever
            stream._reset_backoff()
            # Never yield an event — simulate half-open connection
            await asyncio.sleep(300)
            # unreachable, but needed for generator
            yield make_event("unreachable", "unreachable")  # pragma: no cover
        else:
            # Second connection: deliver an event
            stream._reset_backoff()
            yield make_event("evt_idle_1", "session.idled")

    stream._connect = mock_connect

    events = []
    async for event in stream:
        events.append(event)
        if len(events) >= 1:
            stream.stop()

    assert len(events) == 1
    assert events[0].id == "evt_idle_1"
    assert events[0].type == "session.idled"

    # Proves reconnection happened
    assert call_count >= 2, f"Should have reconnected (got {call_count} connections)"


@pytest.mark.asyncio
async def test_multiple_graceful_disconnects_in_sequence():
    """Stream should handle many graceful disconnects without exhausting retries."""
    stream = EventStream(MockClient(), "sess_1", StreamOptions(max_retries=2))
    call_count = 0

    async def mock_connect():
        nonlocal call_count
        call_count += 1
        stream._reset_backoff()
        yield make_event(f"evt_{call_count:03d}", "output.message.started")
        if call_count < 5:
            raise _GracefulDisconnectError(1)  # Minimal delay

    stream._connect = mock_connect

    events = []
    async for event in stream:
        events.append(event)
        if len(events) >= 5:
            stream.stop()

    # 5 events from 5 connections, all via graceful disconnect
    assert len(events) == 5
    # Bug 1: retry_count is still 0 despite 4 graceful disconnects
    assert stream._retry_count == 0
    assert call_count == 5
