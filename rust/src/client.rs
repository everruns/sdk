//! Main client for Everruns API

use crate::auth::ApiKey;
use crate::error::{Error, Result};
use crate::models::*;
use reqwest::header::{AUTHORIZATION, CONTENT_TYPE, HeaderMap, HeaderValue};
use url::Url;

const DEFAULT_BASE_URL: &str = "https://custom.example.com/api";

/// Main client for interacting with the Everruns API
#[derive(Clone)]
pub struct Everruns {
    http: reqwest::Client,
    base_url: Url,
    api_key: ApiKey,
}

impl Everruns {
    /// Create a new client with explicit API key
    pub fn new(api_key: impl Into<String>) -> Result<Self> {
        Self::with_base_url(api_key, DEFAULT_BASE_URL)
    }

    /// Create a new client using environment variables.
    ///
    /// Reads `EVERRUNS_API_KEY` (required) and `EVERRUNS_API_URL` (optional).
    pub fn from_env() -> Result<Self> {
        let api_key = ApiKey::from_env()?;
        let base_url =
            std::env::var("EVERRUNS_API_URL").unwrap_or_else(|_| DEFAULT_BASE_URL.to_string());
        Self::with_api_key_and_url(api_key, &base_url)
    }

    /// Create a new client with a custom base URL
    pub fn with_base_url(api_key: impl Into<String>, base_url: &str) -> Result<Self> {
        let api_key = ApiKey::new(api_key);
        Self::with_api_key_and_url(api_key, base_url)
    }

    /// Create a new client with an ApiKey instance
    pub fn with_api_key(api_key: ApiKey) -> Result<Self> {
        Self::with_api_key_and_url(api_key, DEFAULT_BASE_URL)
    }

    fn with_api_key_and_url(api_key: ApiKey, base_url: &str) -> Result<Self> {
        let http = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()?;

        // Ensure base URL has trailing slash for correct URL joining.
        // Url::join follows RFC 3986: without trailing slash, relative paths
        // replace the last path segment instead of appending.
        // Example: "http://host/api" + "v1/x" = "http://host/v1/x" (wrong)
        //          "http://host/api/" + "v1/x" = "http://host/api/v1/x" (correct)
        let normalized = if base_url.ends_with('/') {
            base_url.to_string()
        } else {
            format!("{}/", base_url)
        };
        let base_url = Url::parse(&normalized)?;

        Ok(Self {
            http,
            base_url,
            api_key,
        })
    }

    /// Get the agents client
    pub fn agents(&self) -> AgentsClient<'_> {
        AgentsClient { client: self }
    }

    /// Get the sessions client
    pub fn sessions(&self) -> SessionsClient<'_> {
        SessionsClient { client: self }
    }

    /// Get the messages client
    pub fn messages(&self) -> MessagesClient<'_> {
        MessagesClient { client: self }
    }

    /// Get the events client
    pub fn events(&self) -> EventsClient<'_> {
        EventsClient { client: self }
    }

    /// Get the capabilities client
    pub fn capabilities(&self) -> CapabilitiesClient<'_> {
        CapabilitiesClient { client: self }
    }

    /// Get the session files client
    pub fn session_files(&self) -> SessionFilesClient<'_> {
        SessionFilesClient { client: self }
    }

    pub(crate) fn url(&self, path: &str) -> Url {
        // Use relative path (no leading slash) for correct joining with base URL.
        // The path parameter starts with "/" (e.g., "/agents"), so we strip it.
        let path_without_slash = path.strip_prefix('/').unwrap_or(path);
        let full_path = format!("v1/{}", path_without_slash);
        self.base_url.join(&full_path).expect("valid URL")
    }

    fn headers(&self) -> HeaderMap {
        let mut headers = HeaderMap::new();
        headers.insert(
            AUTHORIZATION,
            HeaderValue::from_str(self.api_key.expose()).expect("valid header"),
        );
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
        headers
    }

    pub(crate) async fn get<T: serde::de::DeserializeOwned>(&self, path: &str) -> Result<T> {
        let resp = self
            .http
            .get(self.url(path))
            .headers(self.headers())
            .send()
            .await?;

        self.handle_response(resp).await
    }

    pub(crate) async fn get_url<T: serde::de::DeserializeOwned>(&self, url: Url) -> Result<T> {
        let resp = self.http.get(url).headers(self.headers()).send().await?;

        self.handle_response(resp).await
    }

    pub(crate) async fn post<T: serde::de::DeserializeOwned, B: serde::Serialize>(
        &self,
        path: &str,
        body: &B,
    ) -> Result<T> {
        let resp = self
            .http
            .post(self.url(path))
            .headers(self.headers())
            .json(body)
            .send()
            .await?;

        self.handle_response(resp).await
    }

    #[allow(dead_code)]
    pub(crate) async fn patch<T: serde::de::DeserializeOwned, B: serde::Serialize>(
        &self,
        path: &str,
        body: &B,
    ) -> Result<T> {
        let resp = self
            .http
            .patch(self.url(path))
            .headers(self.headers())
            .json(body)
            .send()
            .await?;

        self.handle_response(resp).await
    }

    pub(crate) async fn post_text<T: serde::de::DeserializeOwned>(
        &self,
        path: &str,
        body: &str,
    ) -> Result<T> {
        let mut headers = self.headers();
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("text/plain"));
        let resp = self
            .http
            .post(self.url(path))
            .headers(headers)
            .body(body.to_string())
            .send()
            .await?;

        self.handle_response(resp).await
    }

    pub(crate) async fn get_text(&self, path: &str) -> Result<String> {
        let resp = self
            .http
            .get(self.url(path))
            .headers(self.headers())
            .send()
            .await?;

        if resp.status().is_success() {
            Ok(resp.text().await?)
        } else {
            let status = resp.status().as_u16();
            let body = resp.text().await.unwrap_or_default();
            Err(Error::from_api_response(status, &body))
        }
    }

    pub(crate) async fn put<T: serde::de::DeserializeOwned, B: serde::Serialize>(
        &self,
        path: &str,
        body: &B,
    ) -> Result<T> {
        let resp = self
            .http
            .put(self.url(path))
            .headers(self.headers())
            .json(body)
            .send()
            .await?;

        self.handle_response(resp).await
    }

    pub(crate) async fn put_empty(&self, path: &str) -> Result<()> {
        let resp = self
            .http
            .put(self.url(path))
            .headers(self.headers())
            .send()
            .await?;

        if resp.status().is_success() {
            Ok(())
        } else {
            let status = resp.status().as_u16();
            let body = resp.text().await.unwrap_or_default();
            Err(Error::from_api_response(status, &body))
        }
    }

    pub(crate) async fn delete(&self, path: &str) -> Result<()> {
        let resp = self
            .http
            .delete(self.url(path))
            .headers(self.headers())
            .send()
            .await?;

        if resp.status().is_success() {
            Ok(())
        } else {
            let status = resp.status().as_u16();
            let body = resp.text().await.unwrap_or_default();
            Err(Error::from_api_response(status, &body))
        }
    }

    pub(crate) async fn delete_url<T: serde::de::DeserializeOwned>(&self, url: Url) -> Result<T> {
        let resp = self.http.delete(url).headers(self.headers()).send().await?;

        self.handle_response(resp).await
    }

    async fn handle_response<T: serde::de::DeserializeOwned>(
        &self,
        resp: reqwest::Response,
    ) -> Result<T> {
        if resp.status().is_success() {
            Ok(resp.json().await?)
        } else {
            let status = resp.status().as_u16();
            let body = resp.text().await.unwrap_or_default();
            Err(Error::from_api_response(status, &body))
        }
    }

    /// Get the SSE URL for a session
    pub(crate) fn sse_url(
        &self,
        session_id: &str,
        since_id: Option<&str>,
        types: &[&str],
        exclude: &[&str],
    ) -> Url {
        let mut url = self.url(&format!("/sessions/{}/sse", session_id));
        if let Some(id) = since_id {
            url.query_pairs_mut().append_pair("since_id", id);
        }
        for t in types {
            url.query_pairs_mut().append_pair("types", t);
        }
        for e in exclude {
            url.query_pairs_mut().append_pair("exclude", e);
        }
        url
    }

    pub(crate) fn auth_header(&self) -> String {
        self.api_key.expose().to_string()
    }
}

/// Client for agent operations
pub struct AgentsClient<'a> {
    client: &'a Everruns,
}

impl<'a> AgentsClient<'a> {
    /// List all agents
    pub async fn list(&self) -> Result<ListResponse<Agent>> {
        self.client.get("/agents").await
    }

    /// List agents matching a search query (case-insensitive name/description match)
    pub async fn search(&self, query: &str) -> Result<ListResponse<Agent>> {
        let mut url = self.client.url("/agents");
        url.query_pairs_mut().append_pair("search", query);
        self.client.get_url(url).await
    }

    /// Get an agent by ID
    pub async fn get(&self, id: &str) -> Result<Agent> {
        self.client.get(&format!("/agents/{}", id)).await
    }

    /// Create a new agent with a server-assigned ID
    pub async fn create(&self, name: &str, system_prompt: &str) -> Result<Agent> {
        let req = CreateAgentRequest::new(name, system_prompt);
        self.client.post("/agents", &req).await
    }

    /// Create an agent with full options
    pub async fn create_with_options(&self, req: CreateAgentRequest) -> Result<Agent> {
        self.client.post("/agents", &req).await
    }

    /// Create or update an agent with a client-supplied ID (upsert).
    ///
    /// If an agent with the given ID exists, it is updated.
    /// If not, a new agent is created with that ID.
    ///
    /// Use [`generate_agent_id`] to create a properly formatted ID.
    pub async fn apply(&self, id: &str, name: &str, system_prompt: &str) -> Result<Agent> {
        let req = CreateAgentRequest::new(name, system_prompt).id(id);
        self.client.post("/agents", &req).await
    }

    /// Create or update an agent with full options (upsert).
    ///
    /// The `id` parameter is set on the request, overriding any existing value.
    pub async fn apply_with_options(&self, id: &str, req: CreateAgentRequest) -> Result<Agent> {
        let req = req.id(id);
        self.client.post("/agents", &req).await
    }

    /// Copy an agent, creating a new agent with the same configuration
    pub async fn copy(&self, id: &str) -> Result<Agent> {
        self.client
            .post::<Agent, _>(&format!("/agents/{}/copy", id), &())
            .await
    }

    /// Delete (archive) an agent
    pub async fn delete(&self, id: &str) -> Result<()> {
        self.client.delete(&format!("/agents/{}", id)).await
    }

    /// Import an agent from Markdown, YAML, JSON, or plain text
    pub async fn import(&self, content: &str) -> Result<Agent> {
        self.client.post_text("/agents/import", content).await
    }

    /// Export an agent as Markdown with YAML front matter
    pub async fn export(&self, id: &str) -> Result<String> {
        self.client
            .get_text(&format!("/agents/{}/export", id))
            .await
    }
}

/// Client for session operations
pub struct SessionsClient<'a> {
    client: &'a Everruns,
}

impl<'a> SessionsClient<'a> {
    /// List all sessions
    pub async fn list(&self) -> Result<ListResponse<Session>> {
        self.client.get("/sessions").await
    }

    /// List sessions matching a search query (case-insensitive title match)
    pub async fn search(&self, query: &str) -> Result<ListResponse<Session>> {
        let mut url = self.client.url("/sessions");
        url.query_pairs_mut().append_pair("search", query);
        self.client.get_url(url).await
    }

    /// Get a session by ID
    pub async fn get(&self, id: &str) -> Result<Session> {
        self.client.get(&format!("/sessions/{}", id)).await
    }

    /// Create a new session (server defaults to Generic harness)
    pub async fn create(&self) -> Result<Session> {
        let req = CreateSessionRequest::new();
        self.client.post("/sessions", &req).await
    }

    /// Create a session with full options
    pub async fn create_with_options(&self, req: CreateSessionRequest) -> Result<Session> {
        self.client.post("/sessions", &req).await
    }

    /// Delete a session
    pub async fn delete(&self, id: &str) -> Result<()> {
        self.client.delete(&format!("/sessions/{}", id)).await
    }

    /// Cancel the current turn in a session
    pub async fn cancel(&self, id: &str) -> Result<()> {
        self.client
            .post::<serde_json::Value, _>(&format!("/sessions/{}/cancel", id), &())
            .await?;
        Ok(())
    }

    /// Pin a session for the current user
    pub async fn pin(&self, id: &str) -> Result<()> {
        self.client
            .put_empty(&format!("/sessions/{}/pin", id))
            .await
    }

    /// Unpin a session for the current user
    pub async fn unpin(&self, id: &str) -> Result<()> {
        self.client.delete(&format!("/sessions/{}/pin", id)).await
    }
}

/// Client for message operations
pub struct MessagesClient<'a> {
    client: &'a Everruns,
}

impl<'a> MessagesClient<'a> {
    /// List messages in a session
    pub async fn list(&self, session_id: &str) -> Result<ListResponse<Message>> {
        self.client
            .get(&format!("/sessions/{}/messages", session_id))
            .await
    }

    /// Create a new message (send text)
    pub async fn create(&self, session_id: &str, text: &str) -> Result<Message> {
        let req = CreateMessageRequest::user_text(text);
        self.client
            .post(&format!("/sessions/{}/messages", session_id), &req)
            .await
    }

    /// Send tool results back to the session.
    ///
    /// Use this after receiving tool calls from an `output.message.completed`
    /// event to provide results from locally-executed tools.
    pub async fn create_tool_results(
        &self,
        session_id: &str,
        results: Vec<ContentPart>,
    ) -> Result<Message> {
        let req = CreateMessageRequest::tool_results(results);
        self.client
            .post(&format!("/sessions/{}/messages", session_id), &req)
            .await
    }

    /// Create a message with full options
    pub async fn create_with_options(
        &self,
        session_id: &str,
        req: CreateMessageRequest,
    ) -> Result<Message> {
        self.client
            .post(&format!("/sessions/{}/messages", session_id), &req)
            .await
    }
}

/// Client for event operations
pub struct EventsClient<'a> {
    client: &'a Everruns,
}

/// Options for listing events with backward pagination
#[derive(Debug, Clone, Default)]
pub struct ListEventsOptions {
    /// Positive type filter
    pub types: Vec<String>,
    /// Event types to exclude
    pub exclude: Vec<String>,
    /// Max events to return (backward pagination)
    pub limit: Option<u32>,
    /// Cursor for backward pagination: only return events with sequence < this value
    pub before_sequence: Option<i32>,
}

impl<'a> EventsClient<'a> {
    /// List events in a session
    pub async fn list(&self, session_id: &str) -> Result<ListResponse<Event>> {
        self.client
            .get(&format!("/sessions/{}/events", session_id))
            .await
    }

    /// List events with options (filtering, backward pagination)
    pub async fn list_with_options(
        &self,
        session_id: &str,
        options: &ListEventsOptions,
    ) -> Result<ListResponse<Event>> {
        let mut url = self.client.url(&format!("/sessions/{}/events", session_id));
        for t in &options.types {
            url.query_pairs_mut().append_pair("types", t);
        }
        for e in &options.exclude {
            url.query_pairs_mut().append_pair("exclude", e);
        }
        if let Some(limit) = options.limit {
            url.query_pairs_mut()
                .append_pair("limit", &limit.to_string());
        }
        if let Some(seq) = options.before_sequence {
            url.query_pairs_mut()
                .append_pair("before_sequence", &seq.to_string());
        }
        self.client.get_url(url).await
    }

    /// Stream events from a session via SSE
    pub fn stream(&self, session_id: &str) -> crate::sse::EventStream {
        crate::sse::EventStream::new(
            self.client.clone(),
            session_id.to_string(),
            crate::sse::StreamOptions::default(),
        )
    }

    /// Stream events with options
    pub fn stream_with_options(
        &self,
        session_id: &str,
        options: crate::sse::StreamOptions,
    ) -> crate::sse::EventStream {
        crate::sse::EventStream::new(self.client.clone(), session_id.to_string(), options)
    }
}

/// Client for capability operations
pub struct CapabilitiesClient<'a> {
    client: &'a Everruns,
}

impl<'a> CapabilitiesClient<'a> {
    /// List all available capabilities
    pub async fn list(&self) -> Result<ListResponse<CapabilityInfo>> {
        self.client.get("/capabilities").await
    }

    /// Get a specific capability by ID
    pub async fn get(&self, id: &str) -> Result<CapabilityInfo> {
        self.client.get(&format!("/capabilities/{}", id)).await
    }
}

/// Client for session filesystem operations
pub struct SessionFilesClient<'a> {
    client: &'a Everruns,
}

impl<'a> SessionFilesClient<'a> {
    /// List files in a directory
    pub async fn list(
        &self,
        session_id: &str,
        path: Option<&str>,
        recursive: Option<bool>,
    ) -> Result<ListResponse<FileInfo>> {
        let api_path = match path {
            Some(p) => format!("/sessions/{}/fs/{}", session_id, p.trim_start_matches('/')),
            None => format!("/sessions/{}/fs", session_id),
        };
        let mut url = self.client.url(&api_path);
        if let Some(true) = recursive {
            url.query_pairs_mut().append_pair("recursive", "true");
        }
        self.client.get_url(url).await
    }

    /// Read a file's content
    pub async fn read(&self, session_id: &str, path: &str) -> Result<SessionFile> {
        self.client
            .get(&format!(
                "/sessions/{}/fs/{}",
                session_id,
                path.trim_start_matches('/')
            ))
            .await
    }

    /// Create a file
    pub async fn create(
        &self,
        session_id: &str,
        path: &str,
        content: &str,
        encoding: Option<&str>,
    ) -> Result<SessionFile> {
        let mut req = CreateFileRequest::file(content);
        if let Some(enc) = encoding {
            req = req.encoding(enc);
        }
        self.client
            .post(
                &format!(
                    "/sessions/{}/fs/{}",
                    session_id,
                    path.trim_start_matches('/')
                ),
                &req,
            )
            .await
    }

    /// Create a file with full options
    pub async fn create_with_options(
        &self,
        session_id: &str,
        path: &str,
        req: CreateFileRequest,
    ) -> Result<SessionFile> {
        self.client
            .post(
                &format!(
                    "/sessions/{}/fs/{}",
                    session_id,
                    path.trim_start_matches('/')
                ),
                &req,
            )
            .await
    }

    /// Create a directory
    pub async fn create_dir(&self, session_id: &str, path: &str) -> Result<SessionFile> {
        self.create_with_options(session_id, path, CreateFileRequest::directory())
            .await
    }

    /// Update a file's content
    pub async fn update(
        &self,
        session_id: &str,
        path: &str,
        content: &str,
        encoding: Option<&str>,
    ) -> Result<SessionFile> {
        let mut req = UpdateFileRequest::content(content);
        if let Some(enc) = encoding {
            req = req.encoding(enc);
        }
        self.client
            .put(
                &format!(
                    "/sessions/{}/fs/{}",
                    session_id,
                    path.trim_start_matches('/')
                ),
                &req,
            )
            .await
    }

    /// Update a file with full options
    pub async fn update_with_options(
        &self,
        session_id: &str,
        path: &str,
        req: UpdateFileRequest,
    ) -> Result<SessionFile> {
        self.client
            .put(
                &format!(
                    "/sessions/{}/fs/{}",
                    session_id,
                    path.trim_start_matches('/')
                ),
                &req,
            )
            .await
    }

    /// Delete a file or directory
    pub async fn delete(
        &self,
        session_id: &str,
        path: &str,
        recursive: Option<bool>,
    ) -> Result<DeleteResponse> {
        let mut url = self.client.url(&format!(
            "/sessions/{}/fs/{}",
            session_id,
            path.trim_start_matches('/')
        ));
        if let Some(true) = recursive {
            url.query_pairs_mut().append_pair("recursive", "true");
        }
        self.client.delete_url(url).await
    }

    /// Move/rename a file
    pub async fn move_file(
        &self,
        session_id: &str,
        src_path: &str,
        dst_path: &str,
    ) -> Result<SessionFile> {
        let req = MoveFileRequest::new(src_path, dst_path);
        self.client
            .post(&format!("/sessions/{}/fs/_/move", session_id), &req)
            .await
    }

    /// Copy a file
    pub async fn copy_file(
        &self,
        session_id: &str,
        src_path: &str,
        dst_path: &str,
    ) -> Result<SessionFile> {
        let req = CopyFileRequest::new(src_path, dst_path);
        self.client
            .post(&format!("/sessions/{}/fs/_/copy", session_id), &req)
            .await
    }

    /// Search files with regex
    pub async fn grep(
        &self,
        session_id: &str,
        pattern: &str,
        path_pattern: Option<&str>,
    ) -> Result<ListResponse<GrepResult>> {
        let mut req = GrepRequest::new(pattern);
        if let Some(pp) = path_pattern {
            req = req.path_pattern(pp);
        }
        self.client
            .post(&format!("/sessions/{}/fs/_/grep", session_id), &req)
            .await
    }

    /// Get file or directory stat
    pub async fn stat(&self, session_id: &str, path: &str) -> Result<FileStat> {
        let req = StatRequest::new(path);
        self.client
            .post(&format!("/sessions/{}/fs/_/stat", session_id), &req)
            .await
    }
}

impl std::fmt::Debug for Everruns {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Everruns")
            .field("base_url", &self.base_url.as_str())
            .field("api_key", &self.api_key)
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_client() -> Everruns {
        Everruns::with_base_url("test_key", "https://api.example.com").unwrap()
    }

    #[test]
    fn test_sse_url_no_params() {
        let client = test_client();
        let url = client.sse_url("session_123", None, &[], &[]);
        assert_eq!(
            url.as_str(),
            "https://api.example.com/v1/sessions/session_123/sse"
        );
    }

    #[test]
    fn test_sse_url_with_since_id() {
        let client = test_client();
        let url = client.sse_url("session_123", Some("evt_001"), &[], &[]);
        assert_eq!(
            url.as_str(),
            "https://api.example.com/v1/sessions/session_123/sse?since_id=evt_001"
        );
    }

    #[test]
    fn test_sse_url_exclude_expands_as_repeated_keys() {
        let client = test_client();
        let url = client.sse_url(
            "session_123",
            None,
            &[],
            &["output.message.delta", "reason.thinking.delta"],
        );
        let url_str = url.as_str();
        // Must use repeated keys: ?exclude=a&exclude=b
        // Not comma-separated: ?exclude=a,b
        assert!(
            url_str.contains("exclude=output.message.delta"),
            "URL missing first exclude: {}",
            url_str
        );
        assert!(
            url_str.contains("exclude=reason.thinking.delta"),
            "URL missing second exclude: {}",
            url_str
        );
        assert!(
            !url_str.contains(','),
            "URL must not use comma-separated excludes: {}",
            url_str
        );
        assert_eq!(
            url_str,
            "https://api.example.com/v1/sessions/session_123/sse?exclude=output.message.delta&exclude=reason.thinking.delta"
        );
    }

    #[test]
    fn test_sse_url_single_exclude() {
        let client = test_client();
        let url = client.sse_url("session_123", None, &[], &["output.message.delta"]);
        assert_eq!(
            url.as_str(),
            "https://api.example.com/v1/sessions/session_123/sse?exclude=output.message.delta"
        );
    }

    #[test]
    fn test_sse_url_combined_since_id_and_exclude() {
        let client = test_client();
        let url = client.sse_url(
            "session_123",
            Some("evt_001"),
            &[],
            &["output.message.delta", "reason.thinking.delta"],
        );
        assert_eq!(
            url.as_str(),
            "https://api.example.com/v1/sessions/session_123/sse?since_id=evt_001&exclude=output.message.delta&exclude=reason.thinking.delta"
        );
    }

    #[test]
    fn test_sse_url_three_exclude_values() {
        let client = test_client();
        let url = client.sse_url(
            "session_123",
            None,
            &[],
            &[
                "output.message.delta",
                "reason.thinking.delta",
                "tool.started",
            ],
        );
        let url_str = url.as_str();
        assert_eq!(url_str.matches("exclude=").count(), 3);
    }

    #[test]
    fn test_sse_url_since_id_special_chars_encoded() {
        let client = test_client();
        let url = client.sse_url("session_123", Some("evt&id=1"), &[], &[]);
        let url_str = url.as_str();
        // URL should encode special characters
        assert!(!url_str.contains("evt&id=1"));
        assert!(url_str.contains("since_id=evt%26id%3D1"));
    }

    #[test]
    fn test_sse_url_with_types() {
        let client = test_client();
        let url = client.sse_url(
            "session_123",
            None,
            &["turn.started", "turn.completed"],
            &[],
        );
        assert_eq!(
            url.as_str(),
            "https://api.example.com/v1/sessions/session_123/sse?types=turn.started&types=turn.completed"
        );
    }

    #[test]
    fn test_sse_url_with_types_and_exclude() {
        let client = test_client();
        let url = client.sse_url(
            "session_123",
            Some("evt_001"),
            &["turn.started"],
            &["output.message.delta"],
        );
        assert_eq!(
            url.as_str(),
            "https://api.example.com/v1/sessions/session_123/sse?since_id=evt_001&types=turn.started&exclude=output.message.delta"
        );
    }
}
