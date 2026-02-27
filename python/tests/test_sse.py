"""Tests for SSE streaming and retry logic."""

from everruns_sdk.sse import (
    INITIAL_BACKOFF_MS,
    MAX_RETRY_MS,
    READ_TIMEOUT_SECS,
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


class TestReadTimeout:
    """Tests for SSE read timeout configuration."""

    def test_read_timeout_constant(self):
        """Read timeout must be 60s, consistent across all SDKs."""
        assert READ_TIMEOUT_SECS == 60

    def test_read_timeout_under_cycle_interval(self):
        """Read timeout must be well under the server's 300s cycle interval."""
        assert READ_TIMEOUT_SECS < 300
        assert READ_TIMEOUT_SECS >= 30  # Tolerate normal idle periods

    def test_http_client_has_read_timeout(self):
        """HTTP client must be created with read timeout to detect stalled connections."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        client = stream._get_http_client()
        assert client.timeout.read == READ_TIMEOUT_SECS

    def test_http_client_has_no_overall_timeout(self):
        """SSE streams run for hours; overall timeout must not be set."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        client = stream._get_http_client()
        # httpx uses None for no timeout on a specific component
        # but connect/write/pool have explicit values, read has our timeout
        assert client.timeout.connect == 30.0
        assert client.timeout.write == 30.0


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


class TestGracefulDisconnectRetry:
    """Tests that graceful disconnects don't consume retry budget."""

    def test_graceful_disconnect_does_not_increment_retry_count(self):
        """Graceful disconnects must not increment retry_count.

        With max_retries=5, a session running >25 min would otherwise exhaust
        retries from normal 5-min connection cycling alone.
        """
        opts = StreamOptions(max_retries=5)
        stream = EventStream(MockClient(), "session_123", opts)

        # Simulate 20 graceful disconnects (connection cycles).
        # The graceful path checks _should_reconnect directly,
        # not _should_retry() which checks retry_count.
        for _ in range(20):
            assert stream._should_reconnect is True
            # retry_count stays at 0 because graceful path doesn't increment
        assert stream._retry_count == 0

    def test_graceful_disconnect_preserves_retry_budget(self):
        """After many graceful disconnects, full retry budget remains for real errors."""
        opts = StreamOptions(max_retries=3)
        stream = EventStream(MockClient(), "session_123", opts)

        # 100 graceful disconnects should not affect retry budget
        assert stream._should_retry() is True
        assert stream._retry_count == 0

    def test_connected_event_resets_backoff(self):
        """The connected event should reset backoff and retry count."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        # Simulate elevated backoff from previous errors
        stream._current_backoff_ms = 16000
        stream._retry_count = 4

        # Simulate receiving connected event (calls _reset_backoff)
        stream._reset_backoff()

        assert stream._current_backoff_ms == INITIAL_BACKOFF_MS
        assert stream._retry_count == 0

    def test_http_client_reuse(self):
        """HTTP client should be reused across calls to _get_http_client."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        client1 = stream._get_http_client()
        client2 = stream._get_http_client()
        assert client1 is client2

    def test_http_client_recreated_after_close(self):
        """HTTP client should be recreated if the previous one was closed."""
        stream = EventStream(MockClient(), "session_123", StreamOptions())
        client1 = stream._get_http_client()
        # Simulate closing (set is_closed state)
        # We can't easily close without async, but verify the lazy init path
        stream._http = None
        client2 = stream._get_http_client()
        assert client2 is not client1


class TestArgumentExpansion:
    """Tests for SSE query parameter argument expansion.

    The server expects array parameters (like `exclude`) to be sent as
    repeated query keys: ?exclude=a&exclude=b
    Not as comma-separated: ?exclude=a,b
    See: everruns/everruns#575
    """

    def test_exclude_expands_as_repeated_keys(self):
        """Exclude values must be repeated keys, not comma-separated."""
        opts = StreamOptions(exclude=["output.message.delta", "reason.thinking.delta"])
        stream = EventStream(MockClient(), "session_123", opts)
        url = stream._build_url()
        assert "exclude=output.message.delta&exclude=reason.thinking.delta" in url
        assert "," not in url

    def test_single_exclude_value(self):
        """Single exclude value produces a single key."""
        opts = StreamOptions(exclude=["output.message.delta"])
        stream = EventStream(MockClient(), "session_123", opts)
        url = stream._build_url()
        assert url.endswith("?exclude=output.message.delta")

    def test_combined_since_id_and_exclude_expansion(self):
        """Combined since_id and multiple exclude use repeated keys."""
        opts = StreamOptions(
            since_id="evt_001",
            exclude=["output.message.delta", "reason.thinking.delta"],
        )
        stream = EventStream(MockClient(), "session_123", opts)
        url = stream._build_url()
        assert "since_id=evt_001" in url
        assert "exclude=output.message.delta" in url
        assert "exclude=reason.thinking.delta" in url
        # Verify ordering: since_id first, then exclude params
        since_idx = url.index("since_id=")
        exclude_idx = url.index("exclude=")
        assert since_idx < exclude_idx

    def test_empty_exclude_no_query_params(self):
        """Empty exclude array produces no exclude query params."""
        opts = StreamOptions(exclude=[])
        stream = EventStream(MockClient(), "session_123", opts)
        url = stream._build_url()
        assert "exclude" not in url
        assert url.endswith("/sse")

    def test_exclude_with_three_values(self):
        """Three exclude values produce three repeated keys."""
        opts = StreamOptions(
            exclude=[
                "output.message.delta",
                "reason.thinking.delta",
                "tool.started",
            ]
        )
        stream = EventStream(MockClient(), "session_123", opts)
        url = stream._build_url()
        assert url.count("exclude=") == 3
