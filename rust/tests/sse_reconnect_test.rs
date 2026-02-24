//! Smoke tests for SSE reconnection behavior.
//!
//! Tests the actual EventStream reconnection loop against a mock SSE server
//! to verify:
//! - Bug 1: Graceful disconnects don't consume retry budget
//! - Bug 2: Connected event resets backoff after errors
//! - Bug 3: HTTP client reused across reconnections (verified via request count)

use everruns_sdk::Everruns;
use futures::StreamExt;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use wiremock::matchers::{method, path_regex};
use wiremock::{Mock, MockServer, ResponseTemplate};

/// Custom wiremock responder that returns different SSE bodies per call.
struct SseResponder {
    call_count: Arc<AtomicUsize>,
    responses: Vec<String>,
}

impl wiremock::Respond for SseResponder {
    fn respond(&self, _request: &wiremock::Request) -> ResponseTemplate {
        let n = self.call_count.fetch_add(1, Ordering::SeqCst);
        let idx = n.min(self.responses.len() - 1);
        // set_body_raw lets us control content-type (set_body_string forces text/plain)
        ResponseTemplate::new(200)
            .insert_header("Cache-Control", "no-cache")
            .set_body_raw(self.responses[idx].as_bytes(), "text/event-stream")
    }
}

fn make_event_json(id: &str, event_type: &str) -> String {
    format!(
        r#"{{"id":"{}","type":"{}","ts":"2024-01-01T00:00:00Z","session_id":"sess_1","data":{{}}}}"#,
        id, event_type
    )
}

fn sse_event(event_type: &str, data: &str) -> String {
    format!("event: {}\ndata: {}\n\n", event_type, data)
}

/// Graceful disconnect (connection_cycle) must not consume retry budget.
///
/// With max_retries=3, the stream should survive unlimited graceful disconnects
/// because they don't increment retry_count.
#[tokio::test]
async fn test_graceful_disconnect_preserves_retry_budget() {
    let mock_server = MockServer::start().await;
    let call_count = Arc::new(AtomicUsize::new(0));

    let responses = vec![
        // First connection: connected + event + disconnecting
        format!(
            "{}{}{}",
            sse_event("connected", "{}"),
            sse_event(
                "output.message.started",
                &make_event_json("evt_001", "output.message.started"),
            ),
            sse_event(
                "disconnecting",
                r#"{"reason":"connection_cycle","retry_ms":10}"#,
            ),
        ),
        // Second connection: connected + event (stream ends normally)
        format!(
            "{}{}",
            sse_event("connected", "{}"),
            sse_event(
                "output.message.completed",
                &make_event_json("evt_002", "output.message.completed"),
            ),
        ),
    ];

    Mock::given(method("GET"))
        .and(path_regex("/v1/sessions/.*/sse"))
        .respond_with(SseResponder {
            call_count: call_count.clone(),
            responses,
        })
        .mount(&mock_server)
        .await;

    let client = Everruns::with_base_url("test_key", &mock_server.uri()).unwrap();
    let opts = everruns_sdk::sse::StreamOptions::default().with_max_retries(3);
    let mut stream = client.events().stream_with_options("sess_1", opts);

    // Collect 2 events: one from each connection
    let events: Vec<_> = stream.by_ref().take(2).collect().await;
    stream.stop();

    assert_eq!(events.len(), 2);

    let evt1 = events[0].as_ref().expect("first event should be Ok");
    let evt2 = events[1].as_ref().expect("second event should be Ok");
    assert_eq!(evt1.id, "evt_001");
    assert_eq!(evt2.id, "evt_002");

    // Bug 1: Graceful disconnect did NOT consume retry budget
    assert_eq!(
        stream.retry_count(),
        0,
        "Graceful disconnect must not increment retry_count"
    );

    // Reconnection happened (2 HTTP requests made)
    assert_eq!(
        call_count.load(Ordering::SeqCst),
        2,
        "Should have made exactly 2 connections"
    );
}

/// After an unexpected disconnect, a successful reconnection with `connected`
/// event must reset the backoff and retry count.
#[tokio::test]
async fn test_connected_event_resets_backoff_after_error() {
    let mock_server = MockServer::start().await;
    let call_count = Arc::new(AtomicUsize::new(0));

    let responses = vec![
        // First connection: connected + event (then stream ends = unexpected disconnect)
        format!(
            "{}{}",
            sse_event("connected", "{}"),
            sse_event(
                "output.message.started",
                &make_event_json("evt_001", "output.message.started"),
            ),
        ),
        // Second connection: connected + event
        format!(
            "{}{}",
            sse_event("connected", "{}"),
            sse_event(
                "output.message.completed",
                &make_event_json("evt_002", "output.message.completed"),
            ),
        ),
    ];

    Mock::given(method("GET"))
        .and(path_regex("/v1/sessions/.*/sse"))
        .respond_with(SseResponder {
            call_count: call_count.clone(),
            responses,
        })
        .mount(&mock_server)
        .await;

    let client = Everruns::with_base_url("test_key", &mock_server.uri()).unwrap();
    let opts = everruns_sdk::sse::StreamOptions::default().with_max_retries(5);
    let mut stream = client.events().stream_with_options("sess_1", opts);

    // Collect 2 events
    let events: Vec<_> = stream.by_ref().take(2).collect().await;
    stream.stop();

    assert_eq!(events.len(), 2);

    let evt1 = events[0].as_ref().expect("first event should be Ok");
    let evt2 = events[1].as_ref().expect("second event should be Ok");
    assert_eq!(evt1.id, "evt_001");
    assert_eq!(evt2.id, "evt_002");

    // Bug 2: After successful reconnection with `connected` event,
    // backoff is reset. The data event also resets backoff.
    // So retry_count should be 0 (reset by connected/event).
    assert_eq!(
        stream.retry_count(),
        0,
        "Backoff should be reset after successful reconnect"
    );

    // Two connections were made
    assert_eq!(call_count.load(Ordering::SeqCst), 2);
}
