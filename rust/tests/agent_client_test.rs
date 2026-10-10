//! Tests for the agent client against a mock HTTP server.

use everruns_sdk::{AgentClient, Error};
use serde_json::json;
use wiremock::matchers::{body_json, header, method, path, query_param};
use wiremock::{Match, Mock, MockServer, Request, ResponseTemplate};

/// Matches requests that do not carry the named header.
struct NoHeader(&'static str);

impl Match for NoHeader {
    fn matches(&self, request: &Request) -> bool {
        !request.headers.contains_key(self.0)
    }
}

fn client(server: &MockServer) -> AgentClient {
    AgentClient::new(
        format!("{}/v1/channels/chan_1", server.uri()),
        "evr_ak_test",
    )
    .unwrap()
}

fn session_json() -> serde_json::Value {
    json!({
        "id": "sess_1", "title": "T", "status": "idle",
        "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z",
        "pending_questions": [], "pending_approvals": [], "future_field": 1
    })
}

fn sse(events: &[(&str, serde_json::Value)]) -> ResponseTemplate {
    let mut body = String::from("event: connected\ndata: {}\n\n");
    for (i, (ty, data)) in events.iter().enumerate() {
        let event = json!({
            "id": format!("evt_{i}"), "type": ty, "ts": "2026-01-01T00:00:00Z",
            "session_id": "sess_1", "data": data
        });
        body.push_str(&format!("id: evt_{i}\nevent: {ty}\ndata: {event}\n\n"));
    }
    ResponseTemplate::new(200).set_body_raw(body.into_bytes(), "text/event-stream")
}

#[test]
fn missing_url_or_credential_is_a_config_error() {
    assert!(matches!(
        AgentClient::new("", "evr_ak_x"),
        Err(Error::Validation(_))
    ));
    assert!(matches!(
        AgentClient::new("http://localhost/v1/channels/a", ""),
        Err(Error::Validation(_))
    ));
}

#[test]
fn trailing_slash_is_removed() {
    let c = AgentClient::new("http://localhost/v1/channels/a/", "k").unwrap();
    assert_eq!(c.agent_url(), "http://localhost/v1/channels/a");
}

#[test]
fn debug_hides_the_credential() {
    let c = AgentClient::new("http://localhost/v1/channels/a", "evr_ak_secretsecret").unwrap();
    assert!(!format!("{c:?}").contains("secretsecret"));
}

#[tokio::test]
async fn card_is_read_from_the_base_url_with_bearer_auth() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/v1/channels/chan_1"))
        .and(header("authorization", "Bearer evr_ak_test"))
        .and(NoHeader("end-user"))
        .and(NoHeader("x-org-id"))
        .and(NoHeader("everruns-change-reason"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "name": "Support", "streaming": true,
            "input": {"text": true, "images": false, "files": false},
            "auth": [{"type": "agent_key"}, {"type": "oidc", "issuer": "https://i"}],
            "conversation_starters": ["Hi"],
            "links": {"sessions": "/v1/channels/chan_1/sessions"}
        })))
        .expect(1)
        .mount(&server)
        .await;

    // Trailing slash on the configured URL must not change the route.
    let c = AgentClient::new(
        format!("{}/v1/channels/chan_1/", server.uri()),
        "evr_ak_test",
    )
    .unwrap();
    let card = c.card().await.unwrap();
    assert_eq!(card.name, "Support");
    assert!(card.streaming && card.input.text && !card.input.images);
    assert_eq!(card.auth[1].issuer.as_deref(), Some("https://i"));
}

#[tokio::test]
async fn for_end_user_sets_the_header_on_the_derived_client_only() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/v1/channels/chan_1/sessions/sess_1"))
        .and(header("end-user", "customer-42"))
        .respond_with(ResponseTemplate::new(200).set_body_json(session_json()))
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/v1/channels/chan_1/sessions/sess_2"))
        .and(NoHeader("end-user"))
        .respond_with(ResponseTemplate::new(200).set_body_json(session_json()))
        .expect(1)
        .mount(&server)
        .await;

    let base = client(&server);
    let alice = base.for_end_user("customer-42");
    let s = alice.get_session("sess_1").await.unwrap();
    assert_eq!(s.id, "sess_1");
    assert_eq!(s.extra["future_field"], 1);
    base.get_session("sess_2").await.unwrap();
}

#[tokio::test]
async fn idempotency_key_is_passed_on_create_and_send() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/v1/channels/chan_1/sessions"))
        .and(header("idempotency-key", "k-1"))
        .and(body_json(json!({"title": "Hello"})))
        .respond_with(ResponseTemplate::new(201).set_body_json(session_json()))
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("POST"))
        .and(path("/v1/channels/chan_1/sessions/sess_1/messages"))
        .and(header("idempotency-key", "k-2"))
        .and(body_json(json!({
            "message": {"role": "user", "content": [{"type": "text", "text": "hi"}]}
        })))
        .respond_with(ResponseTemplate::new(201).set_body_json(json!({"id": "msg_1"})))
        .expect(1)
        .mount(&server)
        .await;

    let c = client(&server);
    c.create_session(Some("Hello"), Some("k-1")).await.unwrap();
    let msg = c.send_message("sess_1", "hi", Some("k-2")).await.unwrap();
    assert_eq!(msg["id"], "msg_1");
}

#[tokio::test]
async fn no_idempotency_key_header_unless_passed() {
    let server = MockServer::start().await;
    Mock::given(method("POST"))
        .and(path("/v1/channels/chan_1/sessions"))
        .and(NoHeader("idempotency-key"))
        .and(body_json(json!({})))
        .respond_with(ResponseTemplate::new(201).set_body_json(session_json()))
        .expect(1)
        .mount(&server)
        .await;
    client(&server).create_session(None, None).await.unwrap();
}

#[tokio::test]
async fn list_sessions_and_events_use_cursors() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/v1/channels/chan_1/sessions"))
        .and(query_param("limit", "5"))
        .and(query_param("page_token", "tok"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "data": [session_json()], "next_page_token": "next"
        })))
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/v1/channels/chan_1/sessions/sess_1/events"))
        .and(query_param("after_sequence", "7"))
        .and(query_param("limit", "10"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({"data": [{
            "id": "evt_8", "type": "turn.started", "ts": "2026-01-01T00:00:00Z",
            "session_id": "sess_1", "data": {}, "sequence": 8
        }]})))
        .expect(1)
        .mount(&server)
        .await;

    let c = client(&server);
    let page = c.list_sessions(Some(5), Some("tok")).await.unwrap();
    assert_eq!(page.data.len(), 1);
    assert_eq!(page.next_page_token.as_deref(), Some("next"));
    let events = c.list_events("sess_1", Some(7), Some(10)).await.unwrap();
    assert_eq!(events.data[0].sequence, Some(8));
}

#[tokio::test]
async fn cancel_answers_approvals_and_runtime_token_routes() {
    let server = MockServer::start().await;
    for (route, body) in [
        ("sessions/sess_1/cancel", json!({})),
        ("sessions/sess_1/question-answers", json!({"answers": [1]})),
        ("sessions/sess_1/tool-approvals", json!({"decisions": []})),
    ] {
        Mock::given(method("POST"))
            .and(path(format!("/v1/channels/chan_1/{route}")))
            .and(body_json(body))
            .respond_with(ResponseTemplate::new(200).set_body_json(json!({"ok": true})))
            .expect(1)
            .mount(&server)
            .await;
    }
    Mock::given(method("POST"))
        .and(path("/v1/channels/chan_1/runtime-auth"))
        .and(header("end-user", "u1"))
        .respond_with(ResponseTemplate::new(200).set_body_json(json!({
            "access_token": "rt_abc", "token_type": "Bearer",
            "expires_in": 900, "virtual_user_id": "vu_1"
        })))
        .expect(1)
        .mount(&server)
        .await;

    let c = client(&server);
    c.cancel("sess_1").await.unwrap();
    c.answer_questions("sess_1", &json!({"answers": [1]}))
        .await
        .unwrap();
    c.submit_tool_approvals("sess_1", &json!({"decisions": []}))
        .await
        .unwrap();
    let token = c.for_end_user("u1").runtime_token().await.unwrap();
    assert_eq!(token.access_token, "rt_abc");
    assert_eq!(token.expires_in, 900);
}

#[tokio::test]
async fn errors_map_to_api_errors() {
    let server = MockServer::start().await;
    for (status, code) in [
        (401, "unauthorized"),
        (403, "forbidden"),
        (404, "not_found"),
        (422, "invalid_request"),
        (429, "rate_limited"),
    ] {
        Mock::given(method("GET"))
            .and(path(format!("/v1/channels/chan_1/sessions/s{status}")))
            .respond_with(ResponseTemplate::new(status).set_body_json(json!({
                "error": {"code": code, "message": format!("m{status}")}
            })))
            .mount(&server)
            .await;
        let err = client(&server)
            .get_session(&format!("s{status}"))
            .await
            .unwrap_err();
        match err {
            Error::Api {
                code: c,
                message,
                status: s,
            } => {
                assert_eq!((c.as_str(), s), (code, status));
                assert_eq!(message, format!("m{status}"));
            }
            other => panic!("expected Api error, got {other:?}"),
        }
    }
}

#[tokio::test]
async fn stream_events_sends_auth_and_cursor() {
    let server = MockServer::start().await;
    Mock::given(method("GET"))
        .and(path("/v1/channels/chan_1/sessions/sess_1/sse"))
        .and(header("authorization", "Bearer evr_ak_test"))
        .and(header("end-user", "u1"))
        .and(query_param("after_sequence", "0"))
        .respond_with(sse(&[("turn.started", json!({}))]))
        .expect(1..)
        .mount(&server)
        .await;
    use futures::StreamExt;
    let mut stream = client(&server)
        .for_end_user("u1")
        .stream_events("sess_1", None, Some(0));
    let first = stream.next().await.unwrap().unwrap();
    stream.stop();
    assert_eq!(first.event_type, "turn.started");
}

async fn mount_run_routes(server: &MockServer) {
    Mock::given(method("POST"))
        .and(path("/v1/channels/chan_1/sessions"))
        .respond_with(ResponseTemplate::new(201).set_body_json(session_json()))
        .expect(1)
        .mount(server)
        .await;
    Mock::given(method("POST"))
        .and(path("/v1/channels/chan_1/sessions/sess_1/messages"))
        .respond_with(ResponseTemplate::new(201).set_body_json(json!({"id": "msg_1"})))
        .expect(1)
        .mount(server)
        .await;
}

#[tokio::test]
async fn run_returns_the_final_assistant_text() {
    let server = MockServer::start().await;
    mount_run_routes(&server).await;
    let message = |text: &str| {
        json!({"message": {"role": "assistant", "content": [
            {"type": "text", "text": text}, {"type": "image", "url": "x"}
        ]}})
    };
    Mock::given(method("GET"))
        .and(path("/v1/channels/chan_1/sessions/sess_1/sse"))
        .and(query_param("after_sequence", "0"))
        .respond_with(sse(&[
            ("turn.started", json!({})),
            ("output.message.completed", message("thinking aloud")),
            ("output.message.completed", message("final answer")),
            ("turn.completed", json!({})),
        ]))
        .expect(1)
        .mount(&server)
        .await;

    let reply = client(&server).run("hello", None).await.unwrap();
    assert_eq!(reply, "final answer");
}

#[tokio::test]
async fn run_raises_on_turn_failed() {
    let server = MockServer::start().await;
    mount_run_routes(&server).await;
    Mock::given(method("GET"))
        .and(path("/v1/channels/chan_1/sessions/sess_1/sse"))
        .respond_with(sse(&[(
            "turn.failed",
            json!({"turn_id": "t", "error": "boom", "error_code": "llm_error"}),
        )]))
        .mount(&server)
        .await;

    match client(&server).run("hello", None).await.unwrap_err() {
        Error::TurnFailed { code, message } => {
            assert_eq!(code.as_deref(), Some("llm_error"));
            assert_eq!(message, "boom");
        }
        other => panic!("expected TurnFailed, got {other:?}"),
    }
}

#[tokio::test]
async fn run_on_an_existing_session_streams_after_the_newest_sequence() {
    let server = MockServer::start().await;
    let events_path = "/v1/channels/chan_1/sessions/sess_1/events";
    let event = |seq: i32| {
        json!({"id": format!("e{seq}"), "type": "turn.completed", "ts": "2026-01-01T00:00:00Z",
               "session_id": "sess_1", "data": {}, "sequence": seq})
    };
    // Two full pages of 100, then a short page: the newest sequence is 205.
    let page = |range: std::ops::RangeInclusive<i32>| json!({"data": range.map(event).collect::<Vec<_>>()});
    for (after, body) in [
        ("0", page(1..=100)),
        ("100", page(101..=200)),
        ("200", page(201..=205)),
    ] {
        Mock::given(method("GET"))
            .and(path(events_path))
            .and(query_param("after_sequence", after))
            .respond_with(ResponseTemplate::new(200).set_body_json(body))
            .expect(1)
            .mount(&server)
            .await;
    }
    Mock::given(method("POST"))
        .and(path("/v1/channels/chan_1/sessions/sess_1/messages"))
        .respond_with(ResponseTemplate::new(201).set_body_json(json!({"id": "msg_2"})))
        .expect(1)
        .mount(&server)
        .await;
    Mock::given(method("GET"))
        .and(path("/v1/channels/chan_1/sessions/sess_1/sse"))
        .and(query_param("after_sequence", "205"))
        .respond_with(sse(&[
            (
                "output.message.completed",
                json!({"message": {"content": [{"type": "text", "text": "new"}]}}),
            ),
            ("turn.completed", json!({})),
        ]))
        .expect(1)
        .mount(&server)
        .await;

    let reply = client(&server).run("again", Some("sess_1")).await.unwrap();
    assert_eq!(reply, "new");
}
