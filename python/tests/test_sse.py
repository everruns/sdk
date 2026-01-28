"""Tests for SSE streaming and retry logic."""

from everruns_sdk.sse import (
    INITIAL_BACKOFF_MS,
    MAX_RETRY_MS,
    DisconnectingData,
    EventStream,
    StreamOptions,
    _GracefulDisconnectError,
)


class MockApiKey:
    """Mock API key for testing."""

    value = "test_key"


class MockClient:
    """Mock client for testing EventStream."""

    _base_url = "https://api.example.com"
    _api_key = MockApiKey()


class TestStreamOptions:
    """Tests for StreamOptions."""

    def test_default_options(self):
        """Test default stream options."""
        opts = StreamOptions()
        assert opts.exclude == []
        assert opts.since_id is None
        assert opts.max_retries is None

    def test_exclude_deltas(self):
        """Test exclude_deltas factory method."""
        opts = StreamOptions.exclude_deltas()
        assert "output.message.delta" in opts.exclude
        assert "reason.thinking.delta" in opts.exclude
        assert len(opts.exclude) == 2

    def test_with_since_id(self):
        """Test since_id configuration."""
        opts = StreamOptions(since_id="event_12345")
        assert opts.since_id == "event_12345"

    def test_with_max_retries(self):
        """Test max_retries configuration."""
        opts = StreamOptions(max_retries=10)
        assert opts.max_retries == 10

    def test_full_configuration(self):
        """Test fully configured options."""
        opts = StreamOptions(
            exclude=["output.message.delta"],
            since_id="event_abc",
            max_retries=5,
        )
        assert opts.exclude == ["output.message.delta"]
        assert opts.since_id == "event_abc"
        assert opts.max_retries == 5


class TestDisconnectingData:
    """Tests for DisconnectingData."""

    def test_basic_data(self):
        """Test basic disconnecting data."""
        data = DisconnectingData(reason="connection_cycle", retry_ms=100)
        assert data.reason == "connection_cycle"
        assert data.retry_ms == 100

    def test_custom_reason(self):
        """Test custom reason."""
        data = DisconnectingData(reason="server_maintenance", retry_ms=5000)
        assert data.reason == "server_maintenance"
        assert data.retry_ms == 5000

    def test_zero_retry(self):
        """Test zero retry delay."""
        data = DisconnectingData(reason="immediate", retry_ms=0)
        assert data.retry_ms == 0


class TestGracefulDisconnectError:
    """Tests for _GracefulDisconnectError exception."""

    def test_exception_message(self):
        """Test exception message format."""
        exc = _GracefulDisconnectError(100)
        assert exc.retry_ms == 100
        assert "100ms" in str(exc)

    def test_exception_retry_value(self):
        """Test retry value is preserved."""
        exc = _GracefulDisconnectError(5000)
        assert exc.retry_ms == 5000


class TestBackoffLogic:
    """Tests for exponential backoff calculations."""

    def test_exponential_backoff_sequence(self):
        """Test the exponential backoff sequence."""
        backoff = INITIAL_BACKOFF_MS
        expected = [1000, 2000, 4000, 8000, 16000, 30000, 30000]

        for expected_val in expected:
            assert backoff == expected_val
            backoff = min(backoff * 2, MAX_RETRY_MS)

    def test_backoff_caps_at_max(self):
        """Test backoff doesn't exceed max."""
        backoff = INITIAL_BACKOFF_MS

        # Run many iterations
        for _ in range(20):
            backoff = min(backoff * 2, MAX_RETRY_MS)

        assert backoff == MAX_RETRY_MS

    def test_initial_backoff_value(self):
        """Test initial backoff is 1 second."""
        assert INITIAL_BACKOFF_MS == 1000

    def test_max_backoff_value(self):
        """Test max backoff is 30 seconds."""
        assert MAX_RETRY_MS == 30000


class TestEventStreamState:
    """Tests for EventStream state management."""

    def test_initial_state(self):
        """Test initial stream state."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        assert stream.last_event_id is None
        assert stream.retry_count == 0
        assert stream._should_reconnect is True

    def test_stop_prevents_reconnect(self):
        """Test stop() prevents further reconnection."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        stream.stop()
        assert stream._should_reconnect is False

    def test_url_building_basic(self):
        """Test basic URL building."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        url = stream._build_url()
        assert url == "https://api.example.com/v1/sessions/session_123/sse"

    def test_url_building_with_since_id(self):
        """Test URL building with since_id."""
        opts = StreamOptions(since_id="event_abc")
        stream = EventStream(MockClient(), "session_123", opts)
        url = stream._build_url()
        assert "since_id=event_abc" in url

    def test_url_building_with_exclude(self):
        """Test URL building with exclude parameters."""
        opts = StreamOptions(exclude=["output.message.delta", "reason.thinking.delta"])
        stream = EventStream(MockClient(), "session_123", opts)
        url = stream._build_url()
        assert "exclude=output.message.delta" in url
        assert "exclude=reason.thinking.delta" in url

    def test_retry_delay_graceful(self):
        """Test retry delay for graceful disconnect."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        stream._graceful_disconnect = True
        stream._server_retry_ms = 200
        assert stream._get_retry_delay() == 0.2  # 200ms in seconds

    def test_retry_delay_unexpected(self):
        """Test retry delay for unexpected disconnect."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        stream._graceful_disconnect = False
        assert stream._get_retry_delay() == 1.0  # Initial backoff 1s

    def test_should_retry_with_max_retries(self):
        """Test should_retry respects max_retries."""
        opts = StreamOptions(max_retries=3)
        stream = EventStream(MockClient(), "session_123", opts)

        assert stream._should_retry() is True
        stream._retry_count = 2
        assert stream._should_retry() is True
        stream._retry_count = 3
        assert stream._should_retry() is False

    def test_should_retry_unlimited(self):
        """Test should_retry with unlimited retries."""
        opts = StreamOptions()  # No max_retries
        stream = EventStream(MockClient(), "session_123", opts)
        stream._retry_count = 1000
        assert stream._should_retry() is True

    def test_reset_backoff(self):
        """Test backoff reset after successful event."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        stream._current_backoff_ms = 16000
        stream._retry_count = 5
        stream._reset_backoff()
        assert stream._current_backoff_ms == INITIAL_BACKOFF_MS
        assert stream._retry_count == 0

    def test_update_backoff(self):
        """Test backoff update after failure."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        assert stream._current_backoff_ms == INITIAL_BACKOFF_MS

        stream._graceful_disconnect = False
        stream._update_backoff()
        assert stream._current_backoff_ms == 2000

        stream._update_backoff()
        assert stream._current_backoff_ms == 4000
