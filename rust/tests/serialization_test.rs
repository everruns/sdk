//! Serialization tests for SDK output types
//!
//! All output types must be serializable to support caching, logging, and persistence.

use everruns_sdk::{Agent, Event, ListResponse, Message, Session};

/// Test that ListResponse<Agent> can be serialized and deserialized (round-trip)
#[test]
fn test_list_response_agent_serialization() {
    let json = r#"{
        "data": [{
            "id": "agent_123",
            "name": "Test Agent",
            "description": "A test agent",
            "system_prompt": "You are helpful.",
            "default_model_id": null,
            "tags": ["test"],
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }],
        "total": 1,
        "offset": 0,
        "limit": 20
    }"#;

    // Deserialize
    let response: ListResponse<Agent> =
        serde_json::from_str(json).expect("ListResponse<Agent> should deserialize");
    assert_eq!(response.data.len(), 1);
    assert_eq!(response.data[0].id, "agent_123");

    // Serialize back (this is the key test - output types must be serializable)
    let serialized =
        serde_json::to_string(&response).expect("ListResponse<Agent> should serialize");
    assert!(serialized.contains("agent_123"));
    assert!(serialized.contains("Test Agent"));

    // Round-trip: deserialize again to verify
    let roundtrip: ListResponse<Agent> =
        serde_json::from_str(&serialized).expect("Round-trip should work");
    assert_eq!(roundtrip.data[0].id, "agent_123");
    assert_eq!(roundtrip.total, 1);
}

/// Test that ListResponse<Session> can be serialized
#[test]
fn test_list_response_session_serialization() {
    let json = r#"{
        "data": [{
            "id": "session_456",
            "organization_id": "org_789",
            "agent_id": "agent_123",
            "title": "Test Session",
            "tags": [],
            "model_id": "claude-3-opus",
            "status": "active",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50,
                "cache_read_tokens": 10
            }
        }],
        "total": 1,
        "offset": 0,
        "limit": 20
    }"#;

    let response: ListResponse<Session> =
        serde_json::from_str(json).expect("ListResponse<Session> should deserialize");

    let serialized =
        serde_json::to_string(&response).expect("ListResponse<Session> should serialize");

    let roundtrip: ListResponse<Session> =
        serde_json::from_str(&serialized).expect("Round-trip should work");
    assert_eq!(roundtrip.data[0].id, "session_456");
    assert!(roundtrip.data[0].usage.is_some());
}

/// Test that ListResponse<Message> can be serialized
#[test]
fn test_list_response_message_serialization() {
    let json = r#"{
        "data": [{
            "id": "msg_001",
            "session_id": "session_456",
            "sequence": 1,
            "role": "user",
            "content": [{"type": "text", "text": "Hello!"}],
            "thinking": null,
            "tags": [],
            "created_at": "2024-01-01T00:00:00Z"
        }],
        "total": 1,
        "offset": 0,
        "limit": 20
    }"#;

    let response: ListResponse<Message> =
        serde_json::from_str(json).expect("ListResponse<Message> should deserialize");

    let serialized =
        serde_json::to_string(&response).expect("ListResponse<Message> should serialize");

    let roundtrip: ListResponse<Message> =
        serde_json::from_str(&serialized).expect("Round-trip should work");
    assert_eq!(roundtrip.data[0].id, "msg_001");
}

/// Test that Event can be serialized and deserialized
#[test]
fn test_event_serialization() {
    let json = r#"{
        "id": "evt_123",
        "type": "output.message.done",
        "ts": "2024-01-01T00:00:00Z",
        "session_id": "session_456",
        "data": {"message_id": "msg_001"},
        "context": {
            "turn_id": "turn_789",
            "input_message_id": "msg_000"
        }
    }"#;

    let event: Event = serde_json::from_str(json).expect("Event should deserialize");
    assert_eq!(event.id, "evt_123");
    assert_eq!(event.event_type, "output.message.done");

    // Serialize back
    let serialized = serde_json::to_string(&event).expect("Event should serialize");
    assert!(serialized.contains("evt_123"));
    assert!(serialized.contains("output.message.done"));

    // Round-trip
    let roundtrip: Event = serde_json::from_str(&serialized).expect("Round-trip should work");
    assert_eq!(roundtrip.id, "evt_123");
    assert_eq!(roundtrip.context.turn_id, Some("turn_789".to_string()));
}

/// Test that ListResponse<Event> can be serialized
#[test]
fn test_list_response_event_serialization() {
    let json = r#"{
        "data": [{
            "id": "evt_123",
            "type": "turn.started",
            "ts": "2024-01-01T00:00:00Z",
            "session_id": "session_456",
            "data": {},
            "context": {}
        }],
        "total": 1,
        "offset": 0,
        "limit": 20
    }"#;

    let response: ListResponse<Event> =
        serde_json::from_str(json).expect("ListResponse<Event> should deserialize");

    let serialized =
        serde_json::to_string(&response).expect("ListResponse<Event> should serialize");

    let roundtrip: ListResponse<Event> =
        serde_json::from_str(&serialized).expect("Round-trip should work");
    assert_eq!(roundtrip.data[0].id, "evt_123");
}

/// Test that Event serialization preserves the "type" field name (not "event_type")
#[test]
fn test_event_type_field_rename() {
    let json = r#"{
        "id": "evt_123",
        "type": "output.message.delta",
        "ts": "2024-01-01T00:00:00Z",
        "session_id": "session_456",
        "data": {"delta": "hello"}
    }"#;

    let event: Event = serde_json::from_str(json).expect("Event should deserialize");

    // Serialized output should use "type" (the API field name), not "event_type"
    let serialized = serde_json::to_string(&event).expect("Event should serialize");

    // Parse as raw JSON to check the field name
    let raw: serde_json::Value = serde_json::from_str(&serialized).unwrap();
    assert!(
        raw.get("type").is_some(),
        "Serialized Event should have 'type' field"
    );
    assert!(
        raw.get("event_type").is_none(),
        "Serialized Event should NOT have 'event_type' field"
    );
}
