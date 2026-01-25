//! Data models for Everruns API
//!
//! These types represent the request and response objects used by the API.

use serde::{Deserialize, Serialize};

/// Agent configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Agent {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub description: Option<String>,
    pub system_prompt: String,
    #[serde(default)]
    pub default_model_id: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    pub status: AgentStatus,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum AgentStatus {
    Active,
    Archived,
}

/// Request to create an agent
#[derive(Debug, Clone, Serialize)]
pub struct CreateAgentRequest {
    pub name: String,
    pub system_prompt: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default_model_id: Option<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
}

/// Session representing an active conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub id: String,
    pub organization_id: String,
    pub agent_id: String,
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub model_id: Option<String>,
    pub status: SessionStatus,
    pub created_at: String,
    pub updated_at: String,
    #[serde(default)]
    pub usage: Option<TokenUsage>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SessionStatus {
    Started,
    Active,
    Idle,
}

/// Token usage statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenUsage {
    #[serde(default)]
    pub input_tokens: u64,
    #[serde(default)]
    pub output_tokens: u64,
    #[serde(default)]
    pub cache_read_tokens: u64,
}

/// Request to create a session
#[derive(Debug, Clone, Serialize)]
pub struct CreateSessionRequest {
    pub agent_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub title: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model_id: Option<String>,
}

/// Message in a session
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: String,
    pub session_id: String,
    pub sequence: u64,
    pub role: MessageRole,
    pub content: Vec<ContentPart>,
    #[serde(default)]
    pub thinking: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MessageRole {
    User,
    Agent,
    ToolResult,
}

/// Content part within a message
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ContentPart {
    Text { text: String },
    Image { url: Option<String>, base64: Option<String> },
    ImageFile { image_id: String },
    ToolCall { id: String, name: String, arguments: serde_json::Value },
    ToolResult { tool_call_id: String, result: Option<serde_json::Value>, error: Option<String> },
}

/// Request to create a message
#[derive(Debug, Clone, Serialize)]
pub struct CreateMessageRequest {
    pub message: MessageInput,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub controls: Option<Controls>,
}

#[derive(Debug, Clone, Serialize)]
pub struct MessageInput {
    pub role: MessageRole,
    pub content: Vec<ContentPart>,
}

/// Controls for message generation
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct Controls {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_tokens: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f32>,
}

/// Paginated list response
#[derive(Debug, Clone, Deserialize)]
pub struct ListResponse<T> {
    pub data: Vec<T>,
    pub total: u64,
    pub offset: u64,
    pub limit: u64,
}

/// SSE Event from the server
#[derive(Debug, Clone, Deserialize)]
pub struct Event {
    pub id: String,
    #[serde(rename = "type")]
    pub event_type: String,
    pub ts: String,
    pub session_id: String,
    pub data: serde_json::Value,
    #[serde(default)]
    pub context: EventContext,
}

#[derive(Debug, Clone, Deserialize, Default)]
pub struct EventContext {
    #[serde(default)]
    pub turn_id: Option<String>,
    #[serde(default)]
    pub input_message_id: Option<String>,
}
