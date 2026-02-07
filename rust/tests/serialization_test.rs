//! Serialization tests for SDK output types
//!
//! All output types must be serializable to support caching, logging, and persistence.

use everruns_sdk::{
    Agent, AgentCapabilityConfig, CapabilityInfo, CreateAgentRequest, CreateSessionRequest, Event,
    ListResponse, Message, Session, generate_agent_id,
};

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
            "capabilities": [{"ref": "current_time"}, {"ref": "web_fetch", "config": {"timeout": 30}}],
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

/// Test AgentCapabilityConfig serialization
#[test]
fn test_agent_capability_config_serialization() {
    let config = AgentCapabilityConfig::new("current_time");
    let serialized = serde_json::to_string(&config).expect("should serialize");
    assert!(serialized.contains("\"ref\":\"current_time\""));

    // With config
    let config_with_opts =
        AgentCapabilityConfig::new("web_fetch").config(serde_json::json!({"timeout": 30}));
    let serialized = serde_json::to_string(&config_with_opts).expect("should serialize");
    assert!(serialized.contains("\"ref\":\"web_fetch\""));
    assert!(serialized.contains("\"config\":"));

    // Deserialize
    let json = r#"{"ref": "current_time", "config": {"key": "value"}}"#;
    let deserialized: AgentCapabilityConfig =
        serde_json::from_str(json).expect("should deserialize");
    assert_eq!(deserialized.capability_ref, "current_time");
    assert!(deserialized.config.is_some());
}

/// Test CapabilityInfo deserialization
#[test]
fn test_capability_info_deserialization() {
    let json = r#"{
        "id": "current_time",
        "name": "Current Time",
        "description": "Provides the current time",
        "status": "active",
        "category": "utilities",
        "dependencies": [],
        "icon": "clock",
        "is_mcp": false
    }"#;

    let info: CapabilityInfo = serde_json::from_str(json).expect("should deserialize");
    assert_eq!(info.id, "current_time");
    assert_eq!(info.name, "Current Time");
    assert_eq!(info.status, "active");
    assert!(!info.is_mcp);

    // Round-trip
    let serialized = serde_json::to_string(&info).expect("should serialize");
    let roundtrip: CapabilityInfo =
        serde_json::from_str(&serialized).expect("round-trip should work");
    assert_eq!(roundtrip.id, "current_time");
}

/// Test Agent with capabilities deserialization
#[test]
fn test_agent_with_capabilities() {
    let json = r#"{
        "id": "agent_123",
        "name": "Test Agent",
        "system_prompt": "You are helpful.",
        "tags": [],
        "capabilities": [
            {"ref": "current_time"},
            {"ref": "web_fetch", "config": {"timeout": 30}}
        ],
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }"#;

    let agent: Agent = serde_json::from_str(json).expect("should deserialize");
    assert_eq!(agent.capabilities.len(), 2);
    assert_eq!(agent.capabilities[0].capability_ref, "current_time");
    assert_eq!(agent.capabilities[1].capability_ref, "web_fetch");
}

/// Test Session with capabilities deserialization
#[test]
fn test_session_with_capabilities() {
    let json = r#"{
        "id": "session_456",
        "organization_id": "org_789",
        "agent_id": "agent_123",
        "tags": [],
        "capabilities": [{"ref": "current_time"}],
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }"#;

    let session: Session = serde_json::from_str(json).expect("should deserialize");
    assert_eq!(session.capabilities.len(), 1);
    assert_eq!(session.capabilities[0].capability_ref, "current_time");
}

/// Test CreateAgentRequest serialization with capabilities
#[test]
fn test_create_agent_request_with_capabilities() {
    let req = CreateAgentRequest::new("Test Agent", "You are helpful.").capabilities(vec![
        AgentCapabilityConfig::new("current_time"),
        AgentCapabilityConfig::new("web_fetch").config(serde_json::json!({"timeout": 30})),
    ]);

    let serialized = serde_json::to_string(&req).expect("should serialize");
    let raw: serde_json::Value = serde_json::from_str(&serialized).unwrap();

    assert_eq!(raw["name"], "Test Agent");
    assert_eq!(raw["system_prompt"], "You are helpful.");
    let caps = raw["capabilities"].as_array().unwrap();
    assert_eq!(caps.len(), 2);
    assert_eq!(caps[0]["ref"], "current_time");
    assert_eq!(caps[1]["ref"], "web_fetch");
    assert_eq!(caps[1]["config"]["timeout"], 30);
}

/// Test CreateAgentRequest without capabilities omits empty array
#[test]
fn test_create_agent_request_without_capabilities() {
    let req = CreateAgentRequest::new("Test Agent", "You are helpful.");
    let serialized = serde_json::to_string(&req).expect("should serialize");
    // Empty capabilities vec should be skipped
    assert!(!serialized.contains("capabilities"));
}

/// Test CreateSessionRequest serialization with capabilities
#[test]
fn test_create_session_request_with_capabilities() {
    let req = CreateSessionRequest::new("agent_123")
        .capabilities(vec![AgentCapabilityConfig::new("current_time")]);

    let serialized = serde_json::to_string(&req).expect("should serialize");
    let raw: serde_json::Value = serde_json::from_str(&serialized).unwrap();

    assert_eq!(raw["agent_id"], "agent_123");
    let caps = raw["capabilities"].as_array().unwrap();
    assert_eq!(caps.len(), 1);
    assert_eq!(caps[0]["ref"], "current_time");
}

/// Test CreateSessionRequest without capabilities omits empty array
#[test]
fn test_create_session_request_without_capabilities() {
    let req = CreateSessionRequest::new("agent_123");
    let serialized = serde_json::to_string(&req).expect("should serialize");
    assert!(!serialized.contains("capabilities"));
}

/// Test Agent without capabilities field (backward compat)
#[test]
fn test_agent_without_capabilities() {
    let json = r#"{
        "id": "agent_123",
        "name": "Test Agent",
        "system_prompt": "You are helpful.",
        "tags": [],
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }"#;

    let agent: Agent = serde_json::from_str(json).expect("should deserialize without capabilities");
    assert!(agent.capabilities.is_empty());
}

/// Test Session without capabilities field (backward compat)
#[test]
fn test_session_without_capabilities() {
    let json = r#"{
        "id": "session_456",
        "organization_id": "org_789",
        "agent_id": "agent_123",
        "tags": [],
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }"#;

    let session: Session =
        serde_json::from_str(json).expect("should deserialize without capabilities");
    assert!(session.capabilities.is_empty());
}

/// Test generate_agent_id format
#[test]
fn test_generate_agent_id_format() {
    let id = generate_agent_id();
    assert!(id.starts_with("agent_"), "should start with agent_ prefix");
    let hex_part = &id["agent_".len()..];
    assert_eq!(hex_part.len(), 32, "hex part should be 32 chars");
    assert!(
        hex_part.chars().all(|c| c.is_ascii_hexdigit()),
        "hex part should be valid hex"
    );
}

/// Test generate_agent_id uniqueness
#[test]
fn test_generate_agent_id_unique() {
    let id1 = generate_agent_id();
    let id2 = generate_agent_id();
    assert_ne!(id1, id2, "generated IDs should be unique");
}

/// Test CreateAgentRequest serialization with client-supplied ID
#[test]
fn test_create_agent_request_with_id() {
    let id = generate_agent_id();
    let req = CreateAgentRequest::new("Test Agent", "You are helpful.").id(id.clone());

    let serialized = serde_json::to_string(&req).expect("should serialize");
    let raw: serde_json::Value = serde_json::from_str(&serialized).unwrap();

    assert_eq!(raw["id"], id);
    assert_eq!(raw["name"], "Test Agent");
}

/// Test CreateAgentRequest serialization without ID omits the field
#[test]
fn test_create_agent_request_without_id() {
    let req = CreateAgentRequest::new("Test Agent", "You are helpful.");
    let serialized = serde_json::to_string(&req).expect("should serialize");
    assert!(
        !serialized.contains("\"id\""),
        "id field should be omitted when None"
    );
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
