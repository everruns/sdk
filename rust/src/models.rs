//! Data models for Everruns API
//!
//! These types represent the request and response objects used by the API.

use serde::{Deserialize, Serialize};

/// Agent configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
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
#[non_exhaustive]
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

impl CreateAgentRequest {
    /// Create a new request with required fields
    pub fn new(name: impl Into<String>, system_prompt: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            system_prompt: system_prompt.into(),
            description: None,
            default_model_id: None,
            tags: vec![],
        }
    }

    /// Set the description
    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }

    /// Set the default model ID
    pub fn default_model_id(mut self, model_id: impl Into<String>) -> Self {
        self.default_model_id = Some(model_id.into());
        self
    }

    /// Set the tags
    pub fn tags(mut self, tags: Vec<String>) -> Self {
        self.tags = tags;
        self
    }
}

/// Session representing an active conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
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
#[non_exhaustive]
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
#[non_exhaustive]
pub struct CreateSessionRequest {
    pub agent_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub title: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model_id: Option<String>,
}

impl CreateSessionRequest {
    /// Create a new request with the agent ID
    pub fn new(agent_id: impl Into<String>) -> Self {
        Self {
            agent_id: agent_id.into(),
            title: None,
            model_id: None,
        }
    }

    /// Set the session title
    pub fn title(mut self, title: impl Into<String>) -> Self {
        self.title = Some(title.into());
        self
    }

    /// Set the model ID
    pub fn model_id(mut self, model_id: impl Into<String>) -> Self {
        self.model_id = Some(model_id.into());
        self
    }
}

/// Message in a session
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
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
    Text {
        text: String,
    },
    Image {
        url: Option<String>,
        base64: Option<String>,
    },
    ImageFile {
        image_id: String,
    },
    ToolCall {
        id: String,
        name: String,
        arguments: serde_json::Value,
    },
    ToolResult {
        tool_call_id: String,
        result: Option<serde_json::Value>,
        error: Option<String>,
    },
}

/// Request to create a message
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CreateMessageRequest {
    pub message: MessageInput,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub controls: Option<Controls>,
}

impl CreateMessageRequest {
    /// Create a new request with message input
    pub fn new(message: MessageInput) -> Self {
        Self {
            message,
            controls: None,
        }
    }

    /// Create a user text message
    pub fn user_text(text: impl Into<String>) -> Self {
        Self::new(MessageInput::user_text(text))
    }

    /// Set the controls
    pub fn controls(mut self, controls: Controls) -> Self {
        self.controls = Some(controls);
        self
    }
}

/// Input for creating a message
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct MessageInput {
    pub role: MessageRole,
    pub content: Vec<ContentPart>,
}

impl MessageInput {
    /// Create a new message input
    pub fn new(role: MessageRole, content: Vec<ContentPart>) -> Self {
        Self { role, content }
    }

    /// Create a user text message
    pub fn user_text(text: impl Into<String>) -> Self {
        Self::new(
            MessageRole::User,
            vec![ContentPart::Text { text: text.into() }],
        )
    }
}

/// Controls for message generation
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Controls {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_tokens: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub temperature: Option<f32>,
}

impl Default for Controls {
    fn default() -> Self {
        Self::new()
    }
}

impl Controls {
    /// Create new empty controls
    pub fn new() -> Self {
        Self {
            model_id: None,
            max_tokens: None,
            temperature: None,
        }
    }

    /// Set the model ID
    pub fn model_id(mut self, model_id: impl Into<String>) -> Self {
        self.model_id = Some(model_id.into());
        self
    }

    /// Set the max tokens
    pub fn max_tokens(mut self, max_tokens: u32) -> Self {
        self.max_tokens = Some(max_tokens);
        self
    }

    /// Set the temperature
    pub fn temperature(mut self, temperature: f32) -> Self {
        self.temperature = Some(temperature);
        self
    }
}

/// Paginated list response
#[derive(Debug, Clone, Deserialize)]
#[non_exhaustive]
pub struct ListResponse<T> {
    pub data: Vec<T>,
    pub total: u64,
    pub offset: u64,
    pub limit: u64,
}

/// SSE Event from the server
#[derive(Debug, Clone, Deserialize)]
#[non_exhaustive]
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

/// Context for an event
#[derive(Debug, Clone, Deserialize, Default)]
#[non_exhaustive]
pub struct EventContext {
    #[serde(default)]
    pub turn_id: Option<String>,
    #[serde(default)]
    pub input_message_id: Option<String>,
}
