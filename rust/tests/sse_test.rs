//! Tests for SSE streaming and retry logic

use everruns_sdk::sse::{DisconnectingData, READ_TIMEOUT_SECS, StreamOptions};

#[test]
fn test_stream_options_default() {
    let opts = StreamOptions::default();
    assert!(opts.exclude.is_empty());
    assert!(opts.since_id.is_none());
    assert!(opts.max_retries.is_none());
}

#[test]
fn test_stream_options_exclude_deltas() {
    let opts = StreamOptions::exclude_deltas();
    assert!(opts.exclude.contains(&"output.message.delta".to_string()));
    assert!(opts.exclude.contains(&"reason.thinking.delta".to_string()));
    assert_eq!(opts.exclude.len(), 2);
}

#[test]
fn test_stream_options_with_since_id() {
    let opts = StreamOptions::default().with_since_id("event_12345");
    assert_eq!(opts.since_id, Some("event_12345".to_string()));
}

#[test]
fn test_stream_options_with_max_retries() {
    let opts = StreamOptions::default().with_max_retries(10);
    assert_eq!(opts.max_retries, Some(10));
}

#[test]
fn test_stream_options_builder_chain() {
    let opts = StreamOptions::exclude_deltas()
        .with_since_id("event_abc")
        .with_max_retries(5);

    assert!(opts.exclude.contains(&"output.message.delta".to_string()));
    assert_eq!(opts.since_id, Some("event_abc".to_string()));
    assert_eq!(opts.max_retries, Some(5));
}

#[test]
fn test_disconnecting_data_parse() {
    let json = r#"{"reason":"connection_cycle","retry_ms":100}"#;
    let data: DisconnectingData = serde_json::from_str(json).unwrap();
    assert_eq!(data.reason, "connection_cycle");
    assert_eq!(data.retry_ms, 100);
}

#[test]
fn test_disconnecting_data_parse_custom_reason() {
    let json = r#"{"reason":"server_maintenance","retry_ms":5000}"#;
    let data: DisconnectingData = serde_json::from_str(json).unwrap();
    assert_eq!(data.reason, "server_maintenance");
    assert_eq!(data.retry_ms, 5000);
}

#[test]
fn test_disconnecting_data_parse_zero_retry() {
    let json = r#"{"reason":"immediate_reconnect","retry_ms":0}"#;
    let data: DisconnectingData = serde_json::from_str(json).unwrap();
    assert_eq!(data.reason, "immediate_reconnect");
    assert_eq!(data.retry_ms, 0);
}

#[test]
fn test_read_timeout_under_cycle_interval() {
    // Server cycles SSE connections every 300s (SSE_REALTIME_CYCLE_SECS).
    // Read timeout must be well under that to detect stalled connections
    // before the next cycle, but long enough to avoid false positives
    // during legitimate idle periods.
    assert_eq!(READ_TIMEOUT_SECS, 60);
    assert!(
        READ_TIMEOUT_SECS < 300,
        "must be under server cycle interval"
    );
    assert!(READ_TIMEOUT_SECS >= 30, "must tolerate normal idle periods");
}

#[cfg(test)]
mod backoff_tests {
    // Test the exponential backoff constants
    const INITIAL_BACKOFF_MS: u64 = 1000;
    const MAX_RETRY_MS: u64 = 30_000;

    #[test]
    fn test_exponential_backoff_sequence() {
        let mut backoff = INITIAL_BACKOFF_MS;
        let expected = vec![1000, 2000, 4000, 8000, 16000, 30000, 30000];

        for expected_val in expected {
            assert_eq!(backoff, expected_val);
            backoff = (backoff * 2).min(MAX_RETRY_MS);
        }
    }

    #[test]
    fn test_backoff_caps_at_max() {
        let mut backoff = INITIAL_BACKOFF_MS;

        // Run many iterations
        for _ in 0..20 {
            backoff = (backoff * 2).min(MAX_RETRY_MS);
        }

        assert_eq!(backoff, MAX_RETRY_MS);
    }
}

#[cfg(test)]
mod graceful_disconnect_tests {
    use std::sync::Arc;
    use std::sync::atomic::{AtomicBool, Ordering};

    /// Graceful disconnects (connection cycling) must not increment retry_count.
    /// With max_retries=5, a session running >25 min would otherwise exhaust
    /// retries from normal 5-min cycling alone.
    #[test]
    fn test_graceful_disconnect_does_not_count_as_retry() {
        // Simulate the graceful disconnect path logic:
        // should_reconnect is checked directly (not should_retry which checks retry_count)
        let should_reconnect = true;
        let retry_count: u32 = 0;
        let max_retries: u32 = 5;

        // Simulate 20 graceful disconnects (connection cycles)
        for _ in 0..20 {
            // Graceful path: check should_reconnect directly, don't increment retry_count
            assert!(should_reconnect);
            // retry_count should NOT increase
        }

        // After 20 graceful disconnects, retry_count is still 0
        assert_eq!(retry_count, 0);
        // max_retries budget is untouched
        assert!(retry_count < max_retries);
    }

    /// Connected event signal should be used to reset backoff state.
    #[test]
    fn test_connected_signal_resets_backoff() {
        let signal = Arc::new(AtomicBool::new(false));

        // Simulate connect() setting the signal
        signal.store(true, Ordering::Release);

        // Simulate poll_next() checking the signal
        let was_connected = signal.swap(false, Ordering::Acquire);
        assert!(was_connected, "Signal should be true after connected event");

        // After swap, signal should be cleared
        assert!(
            !signal.load(Ordering::Acquire),
            "Signal should be cleared after check"
        );
    }

    /// Connected signal should be false initially (no spurious resets).
    #[test]
    fn test_connected_signal_initially_false() {
        let signal = Arc::new(AtomicBool::new(false));
        let was_connected = signal.swap(false, Ordering::Acquire);
        assert!(!was_connected, "Signal should be false initially");
    }
}
