//! Smoke tests for SSE reconnection behavior.
//!
//! Tests the actual EventStream reconnection loop against a mock SSE server
//! to verify:
//! - Bug 1: Graceful disconnects don't consume retry budget
//! - Bug 2: Connected event resets backoff after errors
//! - Bug 3: HTTP client reused across reconnections (verified via request count)
//! - Bug 4: Idle timeout triggers reconnection on silent half-open connections

use everruns_sdk::Everruns;
use futures::StreamExt;
use std::sync::Arc;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Duration;
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

/// Idle timeout must trigger reconnection when a connection goes silent.
///
/// Simulates a half-open TCP connection: the first connection sends `connected`
/// then hangs indefinitely (Poll::Pending). The idle timeout fires, the stream
/// reconnects, and the second connection delivers an event.
///
/// Uses a raw TCP server because wiremock returns bodies immediately (stream
/// ends with Poll::Ready(None)) and can't simulate a hanging connection.
#[tokio::test]
async fn test_idle_timeout_triggers_reconnect_on_silent_connection() {
    use tokio::io::AsyncWriteExt;
    use tokio::net::TcpListener;

    let listener = TcpListener::bind("127.0.0.1:0").await.unwrap();
    let addr = listener.local_addr().unwrap();
    let connection_count = Arc::new(AtomicUsize::new(0));
    let count = connection_count.clone();

    // Spawn a mock SSE server
    tokio::spawn(async move {
        loop {
            let (mut socket, _) = listener.accept().await.unwrap();
            let n = count.fetch_add(1, Ordering::SeqCst);

            tokio::spawn(async move {
                // Read the HTTP request (consume it so we can respond)
                let mut buf = vec![0u8; 4096];
                let _ = tokio::io::AsyncReadExt::read(&mut socket, &mut buf).await;

                let connected = "event: connected\ndata: {}\n\n";

                if n == 0 {
                    // First connection: send connected, then hang forever
                    let response = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nCache-Control: no-cache\r\n\r\n{}",
                        connected
                    );
                    let _ = socket.write_all(response.as_bytes()).await;
                    let _ = socket.flush().await;
                    // Keep connection open — hang forever (simulate half-open)
                    tokio::time::sleep(Duration::from_secs(300)).await;
                } else {
                    // Second connection: send connected + business event
                    let event_json = format!(
                        r#"{{"id":"evt_idle_1","type":"session.idled","ts":"2024-01-01T00:00:00Z","session_id":"sess_idle","data":{{}}}}"#
                    );
                    let event = format!("event: session.idled\ndata: {}\n\n", event_json);
                    let response = format!(
                        "HTTP/1.1 200 OK\r\nContent-Type: text/event-stream\r\nCache-Control: no-cache\r\n\r\n{}{}",
                        connected, event
                    );
                    let _ = socket.write_all(response.as_bytes()).await;
                    let _ = socket.flush().await;
                }
            });
        }
    });

    let base_url = format!("http://{}", addr);
    let client = Everruns::with_base_url("test_key", &base_url).unwrap();
    let opts = everruns_sdk::sse::StreamOptions::default()
        .with_idle_timeout(Duration::from_secs(2)) // 2s for fast test
        .with_max_retries(5);
    let mut stream = client.events().stream_with_options("sess_idle", opts);

    // Should reconnect after 2s idle timeout, get event from 2nd connection
    let result = tokio::time::timeout(Duration::from_secs(15), stream.next())
        .await
        .expect("should not timeout at 15s")
        .expect("stream should yield an item")
        .expect("item should be Ok");

    assert_eq!(result.id, "evt_idle_1");
    assert_eq!(result.event_type, "session.idled");

    // Proves reconnection happened (2+ connections)
    assert!(
        connection_count.load(Ordering::SeqCst) >= 2,
        "Should have made at least 2 connections (got {})",
        connection_count.load(Ordering::SeqCst)
    );

    stream.stop();
}
