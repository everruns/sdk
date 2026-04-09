//! Integration tests for Everruns SDK

use everruns_sdk::{
    CreateAgentRequest, CreateBudgetRequest, CreateFileRequest, CreateSessionRequest, Everruns,
    InitialFile, SetConnectionRequest, TopUpRequest, UpdateBudgetRequest, UpdateFileRequest,
};
use wiremock::{
    Mock, MockServer, ResponseTemplate,
    matchers::{body_json, method, path, query_param},
};

#[test]
fn test_client_creation() {
    let result = Everruns::new("evr_test_key");
    assert!(result.is_ok());
}

#[test]
fn test_client_from_env_missing() {
    // Ensure env var is not set
    // SAFETY: This test runs single-threaded and only removes a test-specific env var
    unsafe { std::env::remove_var("EVERRUNS_API_KEY") };
    let result = Everruns::from_env();
    assert!(result.is_err());
}

#[test]
fn test_custom_base_url() {
    let result = Everruns::with_base_url("evr_test_key", "https://custom.example.com/api");
    assert!(result.is_ok());
}

#[test]
fn test_base_url_normalization_adds_trailing_slash() {
    // Base URL without trailing slash should be normalized to have one
    let client = Everruns::with_base_url("evr_test_key", "https://custom.example.com/api")
        .expect("client creation should succeed");

    // Debug output includes the base_url field
    let debug_str = format!("{:?}", client);
    // The base URL should have a trailing slash after normalization
    assert!(
        debug_str.contains("https://custom.example.com/api/"),
        "base URL should be normalized with trailing slash"
    );
}

#[test]
fn test_base_url_normalization_preserves_trailing_slash() {
    // Base URL with trailing slash should remain unchanged
    let client = Everruns::with_base_url("evr_test_key", "https://custom.example.com/api/")
        .expect("client creation should succeed");

    let debug_str = format!("{:?}", client);
    assert!(
        debug_str.contains("https://custom.example.com/api/"),
        "base URL with trailing slash should be preserved"
    );
}

#[tokio::test]
async fn test_create_session_with_initial_files() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/sessions"))
        .and(body_json(serde_json::json!({
            "agent_id": "agent_123",
            "title": "Session with files",
            "model_id": "model_123",
            "initial_files": [
                {
                    "path": "/workspace/README.md",
                    "content": "# hello\n",
                    "encoding": "text",
                    "is_readonly": true
                }
            ]
        })))
        .respond_with(ResponseTemplate::new(201).set_body_json(serde_json::json!({
            "id": "session_123",
            "organization_id": "org_123",
            "harness_id": "harness_123",
            "agent_id": "agent_123",
            "title": "Session with files",
            "status": "started",
            "created_at": "2026-03-13T00:00:00Z",
            "updated_at": "2026-03-13T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let session = client
        .sessions()
        .create_with_options(
            CreateSessionRequest::new()
                .agent_id("agent_123")
                .title("Session with files")
                .model_id("model_123")
                .initial_files(vec![
                    InitialFile::new("/workspace/README.md", "# hello\n")
                        .encoding("text")
                        .is_readonly(true),
                ]),
        )
        .await
        .expect("session creation should succeed");

    assert_eq!(session.id, "session_123");
}

#[tokio::test]
async fn test_create_agent_with_initial_files() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/agents"))
        .and(body_json(serde_json::json!({
            "name": "starter-agent",
            "system_prompt": "You keep files ready.",
            "initial_files": [
                {
                    "path": "/workspace/README.md",
                    "content": "# starter\n",
                    "encoding": "text",
                    "is_readonly": true
                }
            ]
        })))
        .respond_with(ResponseTemplate::new(201).set_body_json(serde_json::json!({
            "id": "agent_123",
            "name": "starter-agent",
            "description": null,
            "system_prompt": "You keep files ready.",
            "default_model_id": null,
            "tags": [],
            "capabilities": [],
            "initial_files": [{
                "path": "/workspace/README.md",
                "content": "# starter\n",
                "encoding": "text",
                "is_readonly": true
            }],
            "status": "active",
            "created_at": "2026-03-13T00:00:00Z",
            "updated_at": "2026-03-13T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let agent = client
        .agents()
        .create_with_options(
            CreateAgentRequest::new("starter-agent", "You keep files ready.").initial_files(vec![
                InitialFile::new("/workspace/README.md", "# starter\n")
                    .encoding("text")
                    .is_readonly(true),
            ]),
        )
        .await
        .expect("agent creation should succeed");

    assert_eq!(agent.id, "agent_123");
    assert_eq!(agent.initial_files.len(), 1);
}

#[tokio::test]
async fn test_create_session_with_locale() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/sessions"))
        .and(body_json(serde_json::json!({
            "title": "Localized session",
            "locale": "uk-UA"
        })))
        .respond_with(ResponseTemplate::new(201).set_body_json(serde_json::json!({
            "id": "session_456",
            "organization_id": "org_123",
            "harness_id": "harness_123",
            "title": "Localized session",
            "locale": "uk-UA",
            "status": "started",
            "created_at": "2026-03-13T00:00:00Z",
            "updated_at": "2026-03-13T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let session = client
        .sessions()
        .create_with_options(
            CreateSessionRequest::new()
                .title("Localized session")
                .locale("uk-UA"),
        )
        .await
        .expect("session creation should succeed");

    assert_eq!(session.id, "session_456");
    assert_eq!(session.locale.as_deref(), Some("uk-UA"));
}

// --- Session Files Tests ---

#[tokio::test]
async fn test_session_files_list() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("GET"))
        .and(path("/v1/sessions/sess_123/fs"))
        .and(query_param("recursive", "true"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "data": [{
                "id": "file_001",
                "session_id": "sess_123",
                "path": "/workspace/hello.txt",
                "name": "hello.txt",
                "is_directory": false,
                "is_readonly": false,
                "size_bytes": 5,
                "created_at": "2026-03-20T00:00:00Z",
                "updated_at": "2026-03-20T00:00:00Z"
            }],
            "total": 1,
            "offset": 0,
            "limit": 100
        })))
        .mount(&server)
        .await;

    let files = client
        .session_files()
        .list("sess_123", None, Some(true))
        .await
        .expect("list should succeed");

    assert_eq!(files.data.len(), 1);
    assert_eq!(files.data[0].name, "hello.txt");
    assert!(!files.data[0].is_directory);
}

#[tokio::test]
async fn test_session_files_read() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("GET"))
        .and(path("/v1/sessions/sess_123/fs/workspace/hello.txt"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "id": "file_001",
            "session_id": "sess_123",
            "path": "/workspace/hello.txt",
            "name": "hello.txt",
            "is_directory": false,
            "is_readonly": false,
            "size_bytes": 5,
            "content": "hello",
            "encoding": "text",
            "created_at": "2026-03-20T00:00:00Z",
            "updated_at": "2026-03-20T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let file = client
        .session_files()
        .read("sess_123", "/workspace/hello.txt")
        .await
        .expect("read should succeed");

    assert_eq!(file.content.as_deref(), Some("hello"));
    assert_eq!(file.encoding.as_deref(), Some("text"));
}

#[tokio::test]
async fn test_session_files_create() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/sessions/sess_123/fs/workspace/new.txt"))
        .and(body_json(serde_json::json!({
            "content": "new content",
            "encoding": "text"
        })))
        .respond_with(ResponseTemplate::new(201).set_body_json(serde_json::json!({
            "id": "file_002",
            "session_id": "sess_123",
            "path": "/workspace/new.txt",
            "name": "new.txt",
            "is_directory": false,
            "is_readonly": false,
            "size_bytes": 11,
            "content": "new content",
            "encoding": "text",
            "created_at": "2026-03-20T00:00:00Z",
            "updated_at": "2026-03-20T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let file = client
        .session_files()
        .create(
            "sess_123",
            "/workspace/new.txt",
            "new content",
            Some("text"),
        )
        .await
        .expect("create should succeed");

    assert_eq!(file.name, "new.txt");
    assert_eq!(file.content.as_deref(), Some("new content"));
}

#[tokio::test]
async fn test_session_files_create_dir() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/sessions/sess_123/fs/workspace/subdir"))
        .and(body_json(serde_json::json!({
            "is_directory": true
        })))
        .respond_with(ResponseTemplate::new(201).set_body_json(serde_json::json!({
            "id": "file_003",
            "session_id": "sess_123",
            "path": "/workspace/subdir",
            "name": "subdir",
            "is_directory": true,
            "is_readonly": false,
            "size_bytes": 0,
            "created_at": "2026-03-20T00:00:00Z",
            "updated_at": "2026-03-20T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let file = client
        .session_files()
        .create_dir("sess_123", "/workspace/subdir")
        .await
        .expect("create_dir should succeed");

    assert!(file.is_directory);
    assert_eq!(file.name, "subdir");
}

#[tokio::test]
async fn test_session_files_update() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("PUT"))
        .and(path("/v1/sessions/sess_123/fs/workspace/hello.txt"))
        .and(body_json(serde_json::json!({
            "content": "updated"
        })))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "id": "file_001",
            "session_id": "sess_123",
            "path": "/workspace/hello.txt",
            "name": "hello.txt",
            "is_directory": false,
            "is_readonly": false,
            "size_bytes": 7,
            "content": "updated",
            "encoding": "text",
            "created_at": "2026-03-20T00:00:00Z",
            "updated_at": "2026-03-20T00:00:01Z"
        })))
        .mount(&server)
        .await;

    let file = client
        .session_files()
        .update("sess_123", "/workspace/hello.txt", "updated", None)
        .await
        .expect("update should succeed");

    assert_eq!(file.content.as_deref(), Some("updated"));
}

#[tokio::test]
async fn test_session_files_delete() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("DELETE"))
        .and(path("/v1/sessions/sess_123/fs/workspace/hello.txt"))
        .respond_with(
            ResponseTemplate::new(200).set_body_json(serde_json::json!({"deleted": true})),
        )
        .mount(&server)
        .await;

    let resp = client
        .session_files()
        .delete("sess_123", "/workspace/hello.txt", None)
        .await
        .expect("delete should succeed");

    assert!(resp.deleted);
}

#[tokio::test]
async fn test_session_files_move() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/sessions/sess_123/fs/_/move"))
        .and(body_json(serde_json::json!({
            "src_path": "/workspace/old.txt",
            "dst_path": "/workspace/new.txt"
        })))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "id": "file_001",
            "session_id": "sess_123",
            "path": "/workspace/new.txt",
            "name": "new.txt",
            "is_directory": false,
            "is_readonly": false,
            "size_bytes": 5,
            "created_at": "2026-03-20T00:00:00Z",
            "updated_at": "2026-03-20T00:00:01Z"
        })))
        .mount(&server)
        .await;

    let file = client
        .session_files()
        .move_file("sess_123", "/workspace/old.txt", "/workspace/new.txt")
        .await
        .expect("move should succeed");

    assert_eq!(file.path, "/workspace/new.txt");
}

#[tokio::test]
async fn test_session_files_copy() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/sessions/sess_123/fs/_/copy"))
        .and(body_json(serde_json::json!({
            "src_path": "/workspace/original.txt",
            "dst_path": "/workspace/copy.txt"
        })))
        .respond_with(ResponseTemplate::new(201).set_body_json(serde_json::json!({
            "id": "file_004",
            "session_id": "sess_123",
            "path": "/workspace/copy.txt",
            "name": "copy.txt",
            "is_directory": false,
            "is_readonly": false,
            "size_bytes": 5,
            "created_at": "2026-03-20T00:00:00Z",
            "updated_at": "2026-03-20T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let file = client
        .session_files()
        .copy_file("sess_123", "/workspace/original.txt", "/workspace/copy.txt")
        .await
        .expect("copy should succeed");

    assert_eq!(file.path, "/workspace/copy.txt");
}

#[tokio::test]
async fn test_session_files_grep() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/sessions/sess_123/fs/_/grep"))
        .and(body_json(serde_json::json!({
            "pattern": "TODO"
        })))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "data": [{
                "path": "/workspace/main.rs",
                "matches": [{
                    "path": "/workspace/main.rs",
                    "line_number": 10,
                    "line": "// TODO: fix this"
                }]
            }],
            "total": 1,
            "offset": 0,
            "limit": 100
        })))
        .mount(&server)
        .await;

    let results = client
        .session_files()
        .grep("sess_123", "TODO", None)
        .await
        .expect("grep should succeed");

    assert_eq!(results.data.len(), 1);
    assert_eq!(results.data[0].matches.len(), 1);
    assert_eq!(results.data[0].matches[0].line, "// TODO: fix this");
}

#[tokio::test]
async fn test_session_files_stat() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/sessions/sess_123/fs/_/stat"))
        .and(body_json(serde_json::json!({
            "path": "/workspace/hello.txt"
        })))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "path": "/workspace/hello.txt",
            "name": "hello.txt",
            "is_directory": false,
            "is_readonly": false,
            "size_bytes": 5,
            "created_at": "2026-03-20T00:00:00Z",
            "updated_at": "2026-03-20T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let stat = client
        .session_files()
        .stat("sess_123", "/workspace/hello.txt")
        .await
        .expect("stat should succeed");

    assert_eq!(stat.name, "hello.txt");
    assert_eq!(stat.size_bytes, 5);
    assert!(!stat.is_directory);
}

// --- Connections Tests ---

#[tokio::test]
async fn test_connections_set() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/user/connections/daytona"))
        .and(body_json(serde_json::json!({
            "api_key": "dtn_secret_key"
        })))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "provider": "daytona",
            "created_at": "2026-03-31T00:00:00Z",
            "updated_at": "2026-03-31T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let conn = client
        .connections()
        .set("daytona", "dtn_secret_key")
        .await
        .expect("set connection should succeed");

    assert_eq!(conn.provider, "daytona");
}

#[tokio::test]
async fn test_connections_list() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("GET"))
        .and(path("/v1/user/connections"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "data": [{
                "provider": "daytona",
                "created_at": "2026-03-31T00:00:00Z",
                "updated_at": "2026-03-31T00:00:00Z"
            }],
            "total": 1,
            "offset": 0,
            "limit": 100
        })))
        .mount(&server)
        .await;

    let connections = client
        .connections()
        .list()
        .await
        .expect("list connections should succeed");

    assert_eq!(connections.data.len(), 1);
    assert_eq!(connections.data[0].provider, "daytona");
}

#[tokio::test]
async fn test_connections_remove() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("DELETE"))
        .and(path("/v1/user/connections/daytona"))
        .respond_with(ResponseTemplate::new(204))
        .mount(&server)
        .await;

    client
        .connections()
        .remove("daytona")
        .await
        .expect("remove connection should succeed");
}

// --- Session Secrets Tests ---

#[tokio::test]
async fn test_session_set_secrets() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("PUT"))
        .and(path("/v1/sessions/sess_123/storage/secrets"))
        .and(body_json(serde_json::json!({
            "secrets": {
                "OPENAI_API_KEY": "sk-abc123",
                "DB_PASSWORD": "hunter2"
            }
        })))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({})))
        .mount(&server)
        .await;

    let mut secrets = std::collections::HashMap::new();
    secrets.insert("OPENAI_API_KEY".to_string(), "sk-abc123".to_string());
    secrets.insert("DB_PASSWORD".to_string(), "hunter2".to_string());

    client
        .sessions()
        .set_secrets("sess_123", &secrets)
        .await
        .expect("set_secrets should succeed");
}

#[tokio::test]
async fn test_session_set_secrets_empty() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("PUT"))
        .and(path("/v1/sessions/sess_123/storage/secrets"))
        .and(body_json(serde_json::json!({
            "secrets": {}
        })))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({})))
        .mount(&server)
        .await;

    let secrets = std::collections::HashMap::new();
    client
        .sessions()
        .set_secrets("sess_123", &secrets)
        .await
        .expect("set_secrets with empty map should succeed");
}

// --- Budget Tests ---

#[tokio::test]
async fn test_budgets_create() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/budgets"))
        .and(body_json(serde_json::json!({
            "subject_type": "session",
            "subject_id": "sess_123",
            "currency": "usd",
            "limit": 10.0,
            "soft_limit": 8.0
        })))
        .respond_with(ResponseTemplate::new(201).set_body_json(serde_json::json!({
            "id": "bdgt_001",
            "organization_id": "org_123",
            "subject_type": "session",
            "subject_id": "sess_123",
            "currency": "usd",
            "limit": 10.0,
            "soft_limit": 8.0,
            "balance": 10.0,
            "status": "active",
            "created_at": "2026-04-01T00:00:00Z",
            "updated_at": "2026-04-01T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let budget = client
        .budgets()
        .create(CreateBudgetRequest::new("session", "sess_123", "usd", 10.0).soft_limit(8.0))
        .await
        .expect("create budget should succeed");

    assert_eq!(budget.id, "bdgt_001");
    assert_eq!(budget.balance, 10.0);
}

#[tokio::test]
async fn test_budgets_get() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("GET"))
        .and(path("/v1/budgets/bdgt_001"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "id": "bdgt_001",
            "organization_id": "org_123",
            "subject_type": "session",
            "subject_id": "sess_123",
            "currency": "usd",
            "limit": 10.0,
            "balance": 7.5,
            "status": "active",
            "created_at": "2026-04-01T00:00:00Z",
            "updated_at": "2026-04-01T00:00:00Z"
        })))
        .mount(&server)
        .await;

    let budget = client
        .budgets()
        .get("bdgt_001")
        .await
        .expect("get budget should succeed");

    assert_eq!(budget.id, "bdgt_001");
    assert_eq!(budget.balance, 7.5);
}

#[tokio::test]
async fn test_budgets_list() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("GET"))
        .and(path("/v1/budgets"))
        .and(query_param("subject_type", "session"))
        .respond_with(
            ResponseTemplate::new(200).set_body_json(serde_json::json!([{
                "id": "bdgt_001",
                "organization_id": "org_123",
                "subject_type": "session",
                "subject_id": "sess_123",
                "currency": "usd",
                "limit": 10.0,
                "balance": 10.0,
                "status": "active",
                "created_at": "2026-04-01T00:00:00Z",
                "updated_at": "2026-04-01T00:00:00Z"
            }])),
        )
        .mount(&server)
        .await;

    let budgets = client
        .budgets()
        .list(Some("session"), None)
        .await
        .expect("list budgets should succeed");

    assert_eq!(budgets.len(), 1);
    assert_eq!(budgets[0].id, "bdgt_001");
}

#[tokio::test]
async fn test_budgets_update() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("PATCH"))
        .and(path("/v1/budgets/bdgt_001"))
        .and(body_json(serde_json::json!({
            "limit": 20.0
        })))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "id": "bdgt_001",
            "organization_id": "org_123",
            "subject_type": "session",
            "subject_id": "sess_123",
            "currency": "usd",
            "limit": 20.0,
            "balance": 17.5,
            "status": "active",
            "created_at": "2026-04-01T00:00:00Z",
            "updated_at": "2026-04-01T00:00:01Z"
        })))
        .mount(&server)
        .await;

    let budget = client
        .budgets()
        .update("bdgt_001", UpdateBudgetRequest::new().limit(20.0))
        .await
        .expect("update budget should succeed");

    assert_eq!(budget.limit, 20.0);
}

#[tokio::test]
async fn test_budgets_delete() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("DELETE"))
        .and(path("/v1/budgets/bdgt_001"))
        .respond_with(ResponseTemplate::new(204))
        .mount(&server)
        .await;

    client
        .budgets()
        .delete("bdgt_001")
        .await
        .expect("delete budget should succeed");
}

#[tokio::test]
async fn test_budgets_top_up() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/budgets/bdgt_001/top-up"))
        .and(body_json(serde_json::json!({
            "amount": 5.0,
            "description": "manual top-up"
        })))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "id": "bdgt_001",
            "organization_id": "org_123",
            "subject_type": "session",
            "subject_id": "sess_123",
            "currency": "usd",
            "limit": 10.0,
            "balance": 12.5,
            "status": "active",
            "created_at": "2026-04-01T00:00:00Z",
            "updated_at": "2026-04-01T00:00:01Z"
        })))
        .mount(&server)
        .await;

    let budget = client
        .budgets()
        .top_up(
            "bdgt_001",
            TopUpRequest::new(5.0).description("manual top-up"),
        )
        .await
        .expect("top_up should succeed");

    assert_eq!(budget.balance, 12.5);
}

#[tokio::test]
async fn test_budgets_ledger() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("GET"))
        .and(path("/v1/budgets/bdgt_001/ledger"))
        .and(query_param("limit", "10"))
        .respond_with(
            ResponseTemplate::new(200).set_body_json(serde_json::json!([{
                "id": "le_001",
                "budget_id": "bdgt_001",
                "amount": 2.5,
                "meter_source": "llm_tokens",
                "created_at": "2026-04-01T00:00:00Z"
            }])),
        )
        .mount(&server)
        .await;

    let entries = client
        .budgets()
        .ledger("bdgt_001", Some(10), None)
        .await
        .expect("ledger should succeed");

    assert_eq!(entries.len(), 1);
    assert_eq!(entries[0].amount, 2.5);
}

#[tokio::test]
async fn test_budgets_check() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("GET"))
        .and(path("/v1/budgets/bdgt_001/check"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "action": "continue"
        })))
        .mount(&server)
        .await;

    let result = client
        .budgets()
        .check("bdgt_001")
        .await
        .expect("check should succeed");

    assert_eq!(result.action, "continue");
}

// --- Session Budget Shortcuts Tests ---

#[tokio::test]
async fn test_session_budgets() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("GET"))
        .and(path("/v1/sessions/sess_123/budgets"))
        .respond_with(
            ResponseTemplate::new(200).set_body_json(serde_json::json!([{
                "id": "bdgt_001",
                "organization_id": "org_123",
                "subject_type": "session",
                "subject_id": "sess_123",
                "currency": "usd",
                "limit": 10.0,
                "balance": 7.5,
                "status": "active",
                "created_at": "2026-04-01T00:00:00Z",
                "updated_at": "2026-04-01T00:00:00Z"
            }])),
        )
        .mount(&server)
        .await;

    let budgets = client
        .sessions()
        .budgets("sess_123")
        .await
        .expect("session budgets should succeed");

    assert_eq!(budgets.len(), 1);
    assert_eq!(budgets[0].id, "bdgt_001");
}

#[tokio::test]
async fn test_session_budget_check() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("GET"))
        .and(path("/v1/sessions/sess_123/budget-check"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "action": "warn",
            "message": "Budget running low",
            "budget_id": "bdgt_001",
            "balance": 1.5,
            "currency": "usd"
        })))
        .mount(&server)
        .await;

    let result = client
        .sessions()
        .budget_check("sess_123")
        .await
        .expect("budget_check should succeed");

    assert_eq!(result.action, "warn");
    assert_eq!(result.balance, Some(1.5));
}

#[tokio::test]
async fn test_session_resume() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    Mock::given(method("POST"))
        .and(path("/v1/sessions/sess_123/resume"))
        .respond_with(ResponseTemplate::new(200).set_body_json(serde_json::json!({
            "resumed_budgets": 2,
            "session_id": "sess_123"
        })))
        .mount(&server)
        .await;

    let result = client
        .sessions()
        .resume("sess_123")
        .await
        .expect("resume should succeed");

    assert_eq!(result.resumed_budgets, 2);
    assert_eq!(result.session_id, "sess_123");
}

#[tokio::test]
async fn test_session_export() {
    let server = MockServer::start().await;
    let client = Everruns::with_base_url("evr_test_key", &server.uri()).expect("client");

    let jsonl = "{\"id\":\"msg_001\",\"session_id\":\"sess_123\",\"sequence\":1,\"role\":\"user\",\"content\":[{\"type\":\"text\",\"text\":\"hello\"}],\"created_at\":\"2024-01-15T10:30:00.000Z\"}\n{\"id\":\"msg_002\",\"session_id\":\"sess_123\",\"sequence\":2,\"role\":\"agent\",\"content\":[{\"type\":\"text\",\"text\":\"hi\"}],\"created_at\":\"2024-01-15T10:30:01.000Z\"}\n";

    Mock::given(method("GET"))
        .and(path("/v1/sessions/sess_123/export"))
        .respond_with(ResponseTemplate::new(200).set_body_string(jsonl))
        .mount(&server)
        .await;

    let result = client
        .sessions()
        .export("sess_123")
        .await
        .expect("export should succeed");

    assert!(result.contains("msg_001"));
    assert!(result.contains("msg_002"));
}
