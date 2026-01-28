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

        let base_url = Url::parse(base_url)?;

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

    fn url(&self, path: &str) -> Url {
        let full_path = format!("/v1{}", path);
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
        exclude: &[&str],
    ) -> Url {
        let mut url = self.url(&format!("/sessions/{}/sse", session_id));
        if let Some(id) = since_id {
            url.query_pairs_mut().append_pair("since_id", id);
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

    /// Get an agent by ID
    pub async fn get(&self, id: &str) -> Result<Agent> {
        self.client.get(&format!("/agents/{}", id)).await
    }

    /// Create a new agent
    pub async fn create(&self, name: &str, system_prompt: &str) -> Result<Agent> {
        let req = CreateAgentRequest {
            name: name.to_string(),
            system_prompt: system_prompt.to_string(),
            description: None,
            default_model_id: None,
            tags: vec![],
        };
        self.client.post("/agents", &req).await
    }

    /// Create an agent with full options
    pub async fn create_with_options(&self, req: CreateAgentRequest) -> Result<Agent> {
        self.client.post("/agents", &req).await
    }

    /// Delete (archive) an agent
    pub async fn delete(&self, id: &str) -> Result<()> {
        self.client.delete(&format!("/agents/{}", id)).await
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

    /// Get a session by ID
    pub async fn get(&self, id: &str) -> Result<Session> {
        self.client.get(&format!("/sessions/{}", id)).await
    }

    /// Create a new session
    pub async fn create(&self, agent_id: &str) -> Result<Session> {
        let req = CreateSessionRequest {
            agent_id: agent_id.to_string(),
            title: None,
            model_id: None,
        };
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
        let req = CreateMessageRequest {
            message: MessageInput {
                role: MessageRole::User,
                content: vec![ContentPart::Text {
                    text: text.to_string(),
                }],
            },
            controls: None,
        };
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

impl<'a> EventsClient<'a> {
    /// List events in a session
    pub async fn list(&self, session_id: &str) -> Result<ListResponse<Event>> {
        self.client
            .get(&format!("/sessions/{}/events", session_id))
            .await
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

impl std::fmt::Debug for Everruns {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Everruns")
            .field("base_url", &self.base_url.as_str())
            .field("api_key", &self.api_key)
            .finish()
    }
}
