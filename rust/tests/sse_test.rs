//! Tests for SSE streaming and retry logic

use everruns_sdk::sse::{DisconnectingData, StreamOptions};

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
