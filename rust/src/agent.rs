//! Agent client: call one agent from code through the Agent Execution API.
//!
//! [`AgentClient`] holds a credential that reaches one agent's session routes and
//! nothing else (an agent key `evr_ak_...`, a runtime token, an identity-provider
//! token, or a member's personal access token when the agent allows it). It is
//! the recommended way to call an agent from an application. The management
//! client [`Everruns`](crate::Everruns) is for managing Everruns (agents,
//! harnesses, workspaces) with a personal access token.
//!
//! The same routes and shapes are served by the Everruns server
//! (`{api}/v1/channels/{channel_id}`) and by a serve app
//! (`{host}/v1/channels/{agent}`), so one client works against both.
//!
//! Design decisions:
//! - Requests, error mapping and the SSE reader are the management client's
//!   (`send_request`, `EventStream`); only URLs and headers differ.
//! - Headers are `Authorization: Bearer <credential>`, plus `End-User` on a
//!   [`for_end_user`](AgentClient::for_end_user) client and `Idempotency-Key` when the
//!   caller passes one. There is no `X-Org-Id`: the agent URL names the agent and
//!   its organization.
//! - Payloads that the server projects per agent (sessions, cards, events) are
//!   typed loosely and tolerate unknown fields.

use crate::auth::ApiKey;
use crate::client::send_request;
use crate::error::{Error, Result};
use crate::models::Event;
use crate::sse::{EventStream, StreamOptions};
use futures_util::StreamExt;
use reqwest::header::{AUTHORIZATION, CONTENT_TYPE, HeaderMap, HeaderValue};
use serde::{Deserialize, Serialize};
use url::Url;

/// Environment variable holding the agent base URL.
pub const AGENT_URL_ENV: &str = "EVERRUNS_AGENT_URL";
/// Environment variable holding the agent credential.
pub const AGENT_KEY_ENV: &str = "EVERRUNS_AGENT_KEY";

/// Request header naming the end user a call acts for.
pub const END_USER_HEADER: &str = "End-User";
/// Request header that makes `create_session` and `send_message` safe to retry.
pub const IDEMPOTENCY_KEY_HEADER: &str = "Idempotency-Key";

/// Client for one agent, reached through its Agent Execution API base URL.
///
/// ```rust,no_run
/// use everruns_sdk::AgentClient;
///
/// # async fn example() -> Result<(), everruns_sdk::Error> {
/// // From EVERRUNS_AGENT_URL and EVERRUNS_AGENT_KEY.
/// let agent = AgentClient::from_env()?;
///
/// // One call: creates a session, sends the message, waits for the turn and
/// // returns the assistant's reply.
/// let reply = agent.run("What can you do?", None).await?;
/// println!("{reply}");
///
/// // Act for one of your own users (needs a key that holds `end_user`).
/// let alice = agent.for_end_user("customer-42");
/// let session = alice.create_session(Some("Billing question"), None).await?;
/// alice.send_message(&session.id, "Where is my invoice?", None).await?;
///
/// // Hand a browser a short-lived token instead of the key.
/// let token = alice.runtime_token().await?;
/// println!("expires in {}s", token.expires_in);
/// # Ok(())
/// # }
/// ```
#[derive(Clone)]
pub struct AgentClient {
    http: reqwest::Client,
    /// Agent base URL with a trailing slash, so relative joins append.
    base_url: Url,
    credential: ApiKey,
    end_user: Option<HeaderValue>,
}

/// Builder for [`AgentClient`].
#[derive(Debug, Clone, Default)]
pub struct AgentClientBuilder {
    agent_url: Option<String>,
    credential: Option<ApiKey>,
    end_user: Option<String>,
}

impl AgentClientBuilder {
    /// Set the agent base URL, e.g. `https://app.everruns.com/api/v1/channels/apichan_...`.
    pub fn agent_url(mut self, agent_url: impl Into<String>) -> Self {
        self.agent_url = Some(agent_url.into());
        self
    }

    /// Set the bearer credential: an agent key, runtime token, or IdP/PAT token.
    pub fn credential(mut self, credential: impl Into<String>) -> Self {
        self.credential = Some(ApiKey::new(credential));
        self
    }

    /// Send `End-User` on every request (needs a key holding `end_user`).
    pub fn end_user(mut self, end_user: impl Into<String>) -> Self {
        self.end_user = Some(end_user.into());
        self
    }

    /// Build the client. A missing URL or credential falls back to
    /// `EVERRUNS_AGENT_URL` / `EVERRUNS_AGENT_KEY` and is an error when neither is set.
    pub fn build(self) -> Result<AgentClient> {
        let agent_url = match self.agent_url {
            Some(url) => url,
            None => std::env::var(AGENT_URL_ENV)
                .map_err(|_| Error::EnvVar(AGENT_URL_ENV.to_string()))?,
        };
        let credential = match self.credential {
            Some(credential) => credential,
            None => std::env::var(AGENT_KEY_ENV)
                .map(ApiKey::new)
                .map_err(|_| Error::EnvVar(AGENT_KEY_ENV.to_string()))?,
        };
        AgentClient::assemble(&agent_url, credential, self.end_user)
    }
}

impl AgentClient {
    /// Create a client builder.
    pub fn builder() -> AgentClientBuilder {
        AgentClientBuilder::default()
    }

    /// Create a client for `agent_url` with an explicit credential.
    pub fn new(agent_url: impl Into<String>, credential: impl Into<String>) -> Result<Self> {
        Self::builder()
            .agent_url(agent_url)
            .credential(credential)
            .build()
    }

    /// Create a client from `EVERRUNS_AGENT_URL` and `EVERRUNS_AGENT_KEY`.
    pub fn from_env() -> Result<Self> {
        Self::builder().build()
    }

    fn assemble(agent_url: &str, credential: ApiKey, end_user: Option<String>) -> Result<Self> {
        let agent_url = agent_url.trim().trim_end_matches('/');
        if agent_url.is_empty() {
            return Err(Error::Validation("agent_url cannot be empty".to_string()));
        }
        if credential.expose().is_empty() {
            return Err(Error::Validation("credential cannot be empty".to_string()));
        }
        // Trailing slash so `Url::join` appends instead of replacing the last segment.
        let base_url = Url::parse(&format!("{agent_url}/"))?;
        let end_user = end_user.map(|id| end_user_header(&id)).transpose()?;
        let http = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()?;
        Ok(Self {
            http,
            base_url,
            credential,
            end_user,
        })
    }

    /// Derive a client that acts for `end_user`, sent as `End-User` on every request.
    ///
    /// The derived client shares this client's configuration and connection
    /// pool; `self` is unchanged. The key must hold the `end_user` permission.
    /// An id the header cannot carry (control characters) is dropped, so the
    /// derived client then sends no `End-User`; use [`AgentClientBuilder::end_user`] to
    /// have such an id rejected as an error instead.
    pub fn for_end_user(&self, end_user: impl AsRef<str>) -> Self {
        Self {
            end_user: end_user_header(end_user.as_ref()).ok(),
            ..self.clone()
        }
    }

    /// The agent base URL, without a trailing slash.
    pub fn agent_url(&self) -> &str {
        self.base_url.as_str().trim_end_matches('/')
    }

    /// Join path segments onto the agent base URL. Segments are percent-encoded.
    fn url(&self, segments: &[&str]) -> Url {
        let mut url = self.base_url.clone();
        url.path_segments_mut()
            .expect("agent URL is hierarchical")
            .pop_if_empty()
            .extend(segments);
        url
    }

    fn auth_headers(&self) -> HeaderMap {
        let mut headers = HeaderMap::new();
        let mut auth = HeaderValue::from_str(&format!("Bearer {}", self.credential.expose()))
            .unwrap_or_else(|_| HeaderValue::from_static("Bearer"));
        auth.set_sensitive(true);
        headers.insert(AUTHORIZATION, auth);
        if let Some(end_user) = &self.end_user {
            headers.insert(END_USER_HEADER, end_user.clone());
        }
        headers
    }

    fn json_headers(&self, idempotency_key: Option<&str>) -> Result<HeaderMap> {
        let mut headers = self.auth_headers();
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
        if let Some(key) = idempotency_key {
            let value = HeaderValue::from_str(key)
                .map_err(|e| Error::Validation(format!("invalid idempotency key: {e}")))?;
            headers.insert(IDEMPOTENCY_KEY_HEADER, value);
        }
        Ok(headers)
    }

    async fn get<T: serde::de::DeserializeOwned>(&self, url: Url) -> Result<T> {
        let body = send_request(self.http.get(url).headers(self.json_headers(None)?)).await?;
        Ok(serde_json::from_str(&body)?)
    }

    async fn post<T: serde::de::DeserializeOwned>(
        &self,
        url: Url,
        body: &impl Serialize,
        idempotency_key: Option<&str>,
    ) -> Result<T> {
        let req = self
            .http
            .post(url)
            .headers(self.json_headers(idempotency_key)?)
            .body(serde_json::to_vec(body)?);
        let text = send_request(req).await?;
        Ok(serde_json::from_str(&text)?)
    }

    /// Fetch the agent card (`GET` on the base URL itself).
    pub async fn card(&self) -> Result<AgentCard> {
        let mut url = self.base_url.clone();
        // The card lives at the base URL itself, without the join slash.
        let path = url.path().trim_end_matches('/').to_string();
        url.set_path(&path);
        self.get(url).await
    }

    /// Create a session. Pass an `idempotency_key` to make retries safe.
    pub async fn create_session(
        &self,
        title: Option<&str>,
        idempotency_key: Option<&str>,
    ) -> Result<AgentSession> {
        let body = match title {
            Some(title) => serde_json::json!({ "title": title }),
            None => serde_json::json!({}),
        };
        self.post(self.url(&["sessions"]), &body, idempotency_key)
            .await
    }

    /// List the caller's sessions, one page at a time.
    ///
    /// Pass the previous page's `next_page_token` as `page_token` to continue.
    pub async fn list_sessions(
        &self,
        limit: Option<u32>,
        page_token: Option<&str>,
    ) -> Result<AgentSessionList> {
        let mut url = self.url(&["sessions"]);
        if let Some(limit) = limit {
            url.query_pairs_mut()
                .append_pair("limit", &limit.to_string());
        }
        if let Some(token) = page_token {
            url.query_pairs_mut().append_pair("page_token", token);
        }
        self.get(url).await
    }

    /// Get a session, including its pending questions and tool approvals.
    pub async fn get_session(&self, session_id: &str) -> Result<AgentSession> {
        self.get(self.url(&["sessions", session_id])).await
    }

    /// Send a user text message. Returns the stored message as the server sent it.
    /// Pass an `idempotency_key` to make retries safe.
    pub async fn send_message(
        &self,
        session_id: &str,
        text: &str,
        idempotency_key: Option<&str>,
    ) -> Result<serde_json::Value> {
        let body = serde_json::json!({
            "message": {"role": "user", "content": [{"type": "text", "text": text}]}
        });
        self.post(
            self.url(&["sessions", session_id, "messages"]),
            &body,
            idempotency_key,
        )
        .await
    }

    /// Cancel the session's running turn.
    pub async fn cancel(&self, session_id: &str) -> Result<serde_json::Value> {
        self.post_empty_object(&["sessions", session_id, "cancel"])
            .await
    }

    /// List events, oldest first. Page forward with `after_sequence` (exclusive).
    pub async fn list_events(
        &self,
        session_id: &str,
        after_sequence: Option<i32>,
        limit: Option<u32>,
    ) -> Result<AgentEventList> {
        let mut url = self.url(&["sessions", session_id, "events"]);
        if let Some(after) = after_sequence {
            url.query_pairs_mut()
                .append_pair("after_sequence", &after.to_string());
        }
        if let Some(limit) = limit {
            url.query_pairs_mut()
                .append_pair("limit", &limit.to_string());
        }
        self.get(url).await
    }

    /// Follow a session's events over SSE, with the SDK's reconnect rules.
    ///
    /// Resume after the last event you saw with `since_id`. A client that holds
    /// no events passes `after_sequence = Some(0)` to replay the whole session
    /// first; without a cursor the stream starts live.
    pub fn stream_events(
        &self,
        session_id: &str,
        since_id: Option<&str>,
        after_sequence: Option<i32>,
    ) -> EventStream {
        let options = match since_id {
            Some(id) => StreamOptions::default().with_since_id(id),
            None => StreamOptions::default(),
        };
        self.stream_with(session_id, after_sequence, options)
    }

    fn stream_with(
        &self,
        session_id: &str,
        after_sequence: Option<i32>,
        options: StreamOptions,
    ) -> EventStream {
        let extra = after_sequence
            .map(|after| vec![("after_sequence", after.to_string())])
            .unwrap_or_default();
        EventStream::from_parts(
            self.url(&["sessions", session_id, "sse"]),
            self.auth_headers(),
            extra,
            options,
        )
    }

    /// Answer the session's pending questions. `answers` is passed through as the body.
    pub async fn answer_questions(
        &self,
        session_id: &str,
        answers: &serde_json::Value,
    ) -> Result<serde_json::Value> {
        self.post(
            self.url(&["sessions", session_id, "question-answers"]),
            answers,
            None,
        )
        .await
    }

    /// Settle the session's pending tool approvals. `decisions` is passed through as the body.
    pub async fn submit_tool_approvals(
        &self,
        session_id: &str,
        decisions: &serde_json::Value,
    ) -> Result<serde_json::Value> {
        self.post(
            self.url(&["sessions", session_id, "tool-approvals"]),
            decisions,
            None,
        )
        .await
    }

    /// Exchange the agent key for a short-lived runtime token to hand to a browser.
    ///
    /// Needs `End-User`: call it on a [`for_end_user`](AgentClient::for_end_user) client.
    pub async fn runtime_token(&self) -> Result<RuntimeToken> {
        self.post_empty_object(&["runtime-auth"]).await
    }

    async fn post_empty_object<T: serde::de::DeserializeOwned>(
        &self,
        segments: &[&str],
    ) -> Result<T> {
        self.post(self.url(segments), &serde_json::json!({}), None)
            .await
    }

    /// Send `text` and return the agent's final reply.
    ///
    /// Creates a session when `session_id` is `None`, sends the message,
    /// follows the event stream until the turn completes (`turn.completed`) and
    /// returns the text of the last assistant message. A failed turn
    /// (`turn.failed`) is returned as [`Error::TurnFailed`]; a stream that ends
    /// first is an [`Error::Sse`].
    ///
    /// On an existing session, `run` first pages [`list_events`](Self::list_events)
    /// to find the newest sequence, sends, and streams after it, so earlier
    /// turns are not replayed. A new session streams from sequence 0.
    pub async fn run(&self, text: &str, session_id: Option<&str>) -> Result<String> {
        let (session_id, after_sequence) = match session_id {
            Some(id) => (id.to_string(), self.newest_sequence(id).await?),
            None => (self.create_session(None, None).await?.id, 0),
        };
        self.send_message(&session_id, text, None).await?;

        // Bounded reconnects: a stream that keeps failing ends the call with an error.
        let options = StreamOptions::default().with_max_retries(5);
        let mut stream = self.stream_with(&session_id, Some(after_sequence), options);
        let mut reply = String::new();
        let outcome = loop {
            let Some(event) = stream.next().await else {
                break Err(Error::Sse("stream ended before the turn finished".into()));
            };
            let event = match event {
                Ok(event) => event,
                Err(e) => break Err(e),
            };
            match event.event_type.as_str() {
                "output.message.completed" => {
                    if let Some(text) = assistant_text(&event.data) {
                        reply = text;
                    }
                }
                "turn.completed" => break Ok(reply),
                "turn.failed" => {
                    break Err(Error::TurnFailed {
                        code: event
                            .data
                            .get("error_code")
                            .and_then(|v| v.as_str())
                            .map(str::to_string),
                        message: event
                            .data
                            .get("error")
                            .and_then(|v| v.as_str())
                            .unwrap_or("turn failed")
                            .to_string(),
                    });
                }
                _ => {}
            }
        };
        stream.stop();
        outcome
    }

    /// Sequence of the session's newest event, 0 when it has none.
    async fn newest_sequence(&self, session_id: &str) -> Result<i32> {
        const PAGE: u32 = 100;
        let mut newest = 0;
        loop {
            let page = self
                .list_events(session_id, Some(newest), Some(PAGE))
                .await?;
            let last = page.data.iter().filter_map(|e| e.sequence).max();
            match last {
                Some(seq) if seq > newest => newest = seq,
                _ => return Ok(newest),
            }
            if page.data.len() < PAGE as usize {
                return Ok(newest);
            }
        }
    }
}

impl std::fmt::Debug for AgentClient {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("AgentClient")
            .field("agent_url", &self.agent_url())
            .field("credential", &self.credential)
            .field(
                "end_user",
                &self.end_user.as_ref().and_then(|v| v.to_str().ok()),
            )
            .finish()
    }
}

fn end_user_header(end_user: &str) -> Result<HeaderValue> {
    let end_user = end_user.trim();
    if end_user.is_empty() {
        return Err(Error::Validation("end_user cannot be empty".to_string()));
    }
    HeaderValue::from_str(end_user)
        .map_err(|e| Error::Validation(format!("invalid end_user header: {e}")))
}

/// Concatenated text parts of an `output.message.completed` payload.
fn assistant_text(data: &serde_json::Value) -> Option<String> {
    let parts = data.get("message")?.get("content")?.as_array()?;
    let text: String = parts
        .iter()
        .filter(|part| part.get("type").and_then(|t| t.as_str()) == Some("text"))
        .filter_map(|part| part.get("text").and_then(|t| t.as_str()))
        .collect();
    (!text.is_empty()).then_some(text)
}

/// What a caller learns from `GET {agent base URL}`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentCard {
    pub name: String,
    #[serde(default)]
    pub description: Option<String>,
    /// Session events can be followed live over SSE.
    #[serde(default)]
    pub streaming: bool,
    pub input: AgentCardInput,
    /// Credentials the agent accepts. Empty means anonymous.
    #[serde(default)]
    pub auth: Vec<AgentCardAuth>,
    #[serde(default)]
    pub conversation_starters: Vec<String>,
    pub links: AgentCardLinks,
}

/// Message content an agent accepts.
#[derive(Debug, Clone, Copy, Default, Serialize, Deserialize)]
pub struct AgentCardInput {
    #[serde(default)]
    pub text: bool,
    #[serde(default)]
    pub images: bool,
    #[serde(default)]
    pub files: bool,
}

/// One credential kind the agent accepts.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentCardAuth {
    /// e.g. `agent_key`, `oidc`, `oauth2`, `runtime_token`, `personal_access_token`.
    #[serde(rename = "type")]
    pub auth_type: String,
    /// Token issuer, for `oidc`.
    #[serde(default)]
    pub issuer: Option<String>,
}

/// Links from an agent card.
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct AgentCardLinks {
    #[serde(default)]
    pub sessions: Option<String>,
    #[serde(default)]
    pub ag_ui: Option<String>,
    #[serde(default)]
    pub a2a: Option<String>,
}

/// The agent's view of a session. Fields the server adds later land in `extra`.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSession {
    pub id: String,
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub status: String,
    #[serde(default)]
    pub created_at: String,
    #[serde(default)]
    pub updated_at: String,
    /// Questions waiting for an answer (see [`AgentClient::answer_questions`]).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pending_questions: Option<serde_json::Value>,
    /// Tool calls waiting for a decision (see [`AgentClient::submit_tool_approvals`]).
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub pending_approvals: Option<serde_json::Value>,
    #[serde(flatten)]
    pub extra: serde_json::Map<String, serde_json::Value>,
}

/// One page of sessions.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSessionList {
    pub data: Vec<AgentSession>,
    /// Pass to [`AgentClient::list_sessions`] for the next page; absent on the last page.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub next_page_token: Option<String>,
}

/// One page of events.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentEventList {
    pub data: Vec<Event>,
}

/// Result of [`AgentClient::runtime_token`].
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RuntimeToken {
    /// Bearer token for a browser; works on this agent only.
    pub access_token: String,
    #[serde(default)]
    pub token_type: String,
    /// Seconds until the token expires.
    pub expires_in: u64,
    #[serde(default)]
    pub virtual_user_id: Option<String>,
}
