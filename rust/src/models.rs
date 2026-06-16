//! Data models for Everruns API
//!
//! These types represent the request and response objects used by the API.

use serde::{Deserialize, Serialize};

/// Per-agent capability configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct AgentCapabilityConfig {
    /// Reference to the capability ID
    #[serde(rename = "ref")]
    pub capability_ref: String,
    /// Per-agent configuration for this capability (capability-specific)
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub config: Option<serde_json::Value>,
}

impl AgentCapabilityConfig {
    /// Create a new capability config with just a ref
    pub fn new(capability_ref: impl Into<String>) -> Self {
        Self {
            capability_ref: capability_ref.into(),
            config: None,
        }
    }

    /// Set the config
    pub fn config(mut self, config: serde_json::Value) -> Self {
        self.config = Some(config);
        self
    }
}

/// Client-side tool definition executed by SDK users.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ClientSideTool {
    pub name: String,
    pub description: String,
    pub parameters: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub category: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hints: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub deferrable: Option<serde_json::Value>,
}

/// Built-in tool definition executed by the server.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct BuiltinTool {
    pub name: String,
    pub description: String,
    pub parameters: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub category: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub hints: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub deferrable: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub policy: Option<String>,
}

impl ClientSideTool {
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        parameters: serde_json::Value,
    ) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            parameters,
            display_name: None,
            category: None,
            hints: None,
            deferrable: None,
        }
    }

    pub fn display_name(mut self, display_name: impl Into<String>) -> Self {
        self.display_name = Some(display_name.into());
        self
    }
}

impl BuiltinTool {
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        parameters: serde_json::Value,
    ) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            parameters,
            display_name: None,
            category: None,
            hints: None,
            deferrable: None,
            policy: None,
        }
    }
}

/// Tool definition in agent/session configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ToolDefinition {
    ClientSide(ClientSideTool),
    Builtin(BuiltinTool),
}

impl ToolDefinition {
    pub fn client_side(
        name: impl Into<String>,
        description: impl Into<String>,
        parameters: serde_json::Value,
    ) -> Self {
        Self::ClientSide(ClientSideTool::new(name, description, parameters))
    }

    pub fn builtin(
        name: impl Into<String>,
        description: impl Into<String>,
        parameters: serde_json::Value,
    ) -> Self {
        Self::Builtin(BuiltinTool::new(name, description, parameters))
    }
}

/// Public capability information
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct CapabilityInfo {
    pub id: String,
    pub name: String,
    pub description: String,
    pub status: String,
    #[serde(default)]
    pub category: Option<String>,
    #[serde(default)]
    pub dependencies: Vec<String>,
    #[serde(default)]
    pub icon: Option<String>,
    #[serde(default)]
    pub is_mcp: bool,
    /// Human-readable display name for UI rendering
    #[serde(default)]
    pub display_name: Option<String>,
    /// UI feature strings this capability contributes to
    #[serde(default)]
    pub features: Vec<String>,
    /// Whether this is an Agent Skill capability
    #[serde(default)]
    pub is_skill: bool,
    /// Risk level for approval requirements (TM-AGENT-005)
    #[serde(default)]
    pub risk_level: Option<String>,
}

/// Agent configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Agent {
    pub id: String,
    /// Addressable name, unique per org (e.g. "customer-support").
    pub name: String,
    /// Human-readable display name shown in UI. Falls back to `name` when absent.
    #[serde(default)]
    pub display_name: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    pub system_prompt: String,
    #[serde(default)]
    pub default_model_id: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub capabilities: Vec<AgentCapabilityConfig>,
    #[serde(default)]
    pub initial_files: Vec<InitialFile>,
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

/// Reason a saved agent version was created.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum AgentVersionChangeKind {
    Manual,
    Patch,
    Minor,
    Major,
    Import,
    Rollback,
    Fork,
}

/// Immutable snapshot of an agent configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct AgentVersion {
    pub id: String,
    pub agent_id: String,
    pub version_number: i32,
    pub semver_major: i32,
    pub semver_minor: i32,
    pub semver_patch: i32,
    pub version: String,
    pub change_kind: AgentVersionChangeKind,
    pub config_hash: String,
    pub authored_config: serde_json::Value,
    pub resolved_config: serde_json::Value,
    pub created_at: String,
    #[serde(default)]
    pub created_by_principal_id: Option<String>,
    #[serde(default)]
    pub parent_version_id: Option<String>,
    #[serde(default)]
    pub source_version_id: Option<String>,
    #[serde(default)]
    pub summary: Option<String>,
}

/// Diff between two saved agent versions.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct AgentVersionDiffResponse {
    pub from_version_id: String,
    pub to_version_id: String,
    pub authored_diff: serde_json::Value,
    pub resolved_diff: serde_json::Value,
}

/// Request to save the current agent configuration as a version.
#[derive(Debug, Clone, Default, Serialize)]
#[non_exhaustive]
pub struct CreateAgentVersionRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub change_kind: Option<AgentVersionChangeKind>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub summary: Option<String>,
}

impl CreateAgentVersionRequest {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn change_kind(mut self, change_kind: AgentVersionChangeKind) -> Self {
        self.change_kind = Some(change_kind);
        self
    }

    pub fn summary(mut self, summary: impl Into<String>) -> Self {
        self.summary = Some(summary.into());
        self
    }
}

/// Request to set the default version for an agent.
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct SetDefaultAgentVersionRequest {
    pub version_id: String,
}

impl SetDefaultAgentVersionRequest {
    pub fn new(version_id: impl Into<String>) -> Self {
        Self {
            version_id: version_id.into(),
        }
    }
}

/// Request to create a new agent from a saved version.
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct ForkAgentVersionRequest {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

impl ForkAgentVersionRequest {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            display_name: None,
            description: None,
        }
    }

    pub fn display_name(mut self, display_name: impl Into<String>) -> Self {
        self.display_name = Some(display_name.into());
        self
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }
}

/// Request to restore an agent from a saved version.
#[derive(Debug, Clone, Default, Serialize)]
#[non_exhaustive]
pub struct RollbackAgentVersionRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub save_version: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub summary: Option<String>,
}

impl RollbackAgentVersionRequest {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn save_version(mut self, save_version: bool) -> Self {
        self.save_version = Some(save_version);
        self
    }

    pub fn summary(mut self, summary: impl Into<String>) -> Self {
        self.summary = Some(summary.into());
        self
    }
}

/// Request to create an agent
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CreateAgentRequest {
    /// Client-supplied agent ID (format: agent_{32-hex}).
    /// If not provided, one is auto-generated by the server.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub id: Option<String>,
    /// Addressable name, unique per org.
    /// Format: `[a-z0-9]+(-[a-z0-9]+)*`, max 64 chars.
    pub name: String,
    /// Human-readable display name shown in UI. Falls back to `name` when absent.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    pub system_prompt: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default_model_id: Option<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub capabilities: Vec<AgentCapabilityConfig>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub tools: Vec<ToolDefinition>,
    #[serde(skip_serializing_if = "Vec::is_empty", default)]
    pub initial_files: Vec<InitialFile>,
}

impl CreateAgentRequest {
    /// Create a new request with required fields
    pub fn new(name: impl Into<String>, system_prompt: impl Into<String>) -> Self {
        Self {
            id: None,
            name: name.into(),
            display_name: None,
            system_prompt: system_prompt.into(),
            description: None,
            default_model_id: None,
            tags: vec![],
            capabilities: vec![],
            tools: vec![],
            initial_files: vec![],
        }
    }

    /// Set a client-supplied agent ID
    pub fn id(mut self, id: impl Into<String>) -> Self {
        self.id = Some(id.into());
        self
    }

    /// Set the human-readable display name
    pub fn display_name(mut self, display_name: impl Into<String>) -> Self {
        self.display_name = Some(display_name.into());
        self
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

    /// Set the capabilities
    pub fn capabilities(mut self, capabilities: Vec<AgentCapabilityConfig>) -> Self {
        self.capabilities = capabilities;
        self
    }

    /// Set client-side tools for this agent
    pub fn tools(mut self, tools: Vec<ToolDefinition>) -> Self {
        self.tools = tools;
        self
    }

    /// Set the starter files copied into each new session for this agent
    pub fn initial_files(mut self, initial_files: Vec<InitialFile>) -> Self {
        self.initial_files = initial_files;
        self
    }
}

/// Generate a random agent ID in the format `agent_<32-hex>`.
pub fn generate_agent_id() -> String {
    let mut bytes = [0u8; 16];
    getrandom::fill(&mut bytes).expect("failed to generate random bytes");
    let hex: String = bytes.iter().map(|b| format!("{:02x}", b)).collect();
    format!("agent_{}", hex)
}

/// Generate a random harness ID in the format `harness_<32-hex>`.
pub fn generate_harness_id() -> String {
    let mut bytes = [0u8; 16];
    getrandom::fill(&mut bytes).expect("failed to generate random bytes");
    let hex: String = bytes.iter().map(|b| format!("{:02x}", b)).collect();
    format!("harness_{}", hex)
}

/// Session representing an active conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Session {
    pub id: String,
    pub organization_id: String,
    pub harness_id: String,
    #[serde(default)]
    pub agent_id: Option<String>,
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub tags: Vec<String>,
    #[serde(default)]
    pub locale: Option<String>,
    #[serde(default)]
    pub model_id: Option<String>,
    #[serde(default)]
    pub capabilities: Vec<AgentCapabilityConfig>,
    pub status: SessionStatus,
    pub created_at: String,
    pub updated_at: String,
    #[serde(default)]
    pub usage: Option<TokenUsage>,
    /// Number of active (enabled) schedules for this session
    #[serde(default)]
    pub active_schedule_count: Option<i32>,
    /// Aggregated UI features from all active capabilities
    #[serde(default)]
    pub features: Vec<String>,
    /// Whether this session is pinned by the current user
    #[serde(default)]
    pub is_pinned: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SessionStatus {
    Started,
    Active,
    Idle,
    #[serde(rename = "waitingfortoolresults")]
    WaitingForToolResults,
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

/// Aggregate usage statistics for an agent or harness.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ResourceStats {
    pub session_count: u64,
    pub active_session_count: u64,
    pub idle_session_count: u64,
    pub started_session_count: u64,
    pub waiting_for_tool_results_session_count: u64,
    pub execution_count: u64,
    pub total_session_duration_ms: u64,
    #[serde(default)]
    pub avg_session_duration_ms: Option<u64>,
    pub total_input_tokens: u64,
    pub total_output_tokens: u64,
    pub total_cache_read_tokens: u64,
    pub total_cache_creation_tokens: u64,
    #[serde(default)]
    pub first_session_at: Option<String>,
    #[serde(default)]
    pub last_session_at: Option<String>,
    #[serde(default)]
    pub last_execution_at: Option<String>,
}

/// Status of a health check run.
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum HealthCheckStatus {
    Pending,
    Running,
    Completed,
    Failed,
}

/// Aggregate metrics across all cases in a health check run.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct HealthCheckSummary {
    pub total: i32,
    pub passed: i32,
    pub failed: i32,
    pub errored: i32,
    pub pass_rate: f64,
    pub avg_score: f64,
    pub avg_turns: f64,
    pub total_input_tokens: u64,
    pub total_output_tokens: u64,
}

/// Outcome of a single case after the agent ran and was scored.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct HealthCheckCaseResult {
    pub name: String,
    pub user_message: String,
    pub rubric: String,
    pub passed: bool,
    pub score: f64,
    pub judge_reason: String,
    pub deterministic_reason: String,
    pub turns: i32,
    pub latency_ms: u64,
    #[serde(default)]
    pub error: Option<String>,
    #[serde(default)]
    pub session_id: Option<String>,
}

/// API view of a behavioral health check run for an agent.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct HealthCheckRun {
    pub id: String,
    pub config_hash: String,
    pub status: HealthCheckStatus,
    pub created_at: String,
    #[serde(default)]
    pub agent_id: Option<String>,
    #[serde(default)]
    pub model_id: Option<String>,
    #[serde(default)]
    pub completed_at: Option<String>,
    #[serde(default)]
    pub error_message: Option<String>,
    #[serde(default)]
    pub summary: Option<HealthCheckSummary>,
    #[serde(default)]
    pub results: Option<Vec<HealthCheckCaseResult>>,
}

/// Starter file copied into a new session workspace
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct InitialFile {
    pub path: String,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_readonly: Option<bool>,
}

impl InitialFile {
    /// Create a new initial file with required fields
    pub fn new(path: impl Into<String>, content: impl Into<String>) -> Self {
        Self {
            path: path.into(),
            content: content.into(),
            encoding: None,
            is_readonly: None,
        }
    }

    /// Set the content encoding
    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }

    /// Set the readonly flag
    pub fn is_readonly(mut self, is_readonly: bool) -> Self {
        self.is_readonly = Some(is_readonly);
        self
    }
}

/// Shared validation for addressable names (harness names, agent names).
/// Pattern: `[a-z0-9]+(-[a-z0-9]+)*`, max 64 characters.
fn validate_addressable_name(name: &str, label: &str) -> crate::error::Result<()> {
    const MAX_LEN: usize = 64;
    if name.len() > MAX_LEN {
        return Err(crate::error::Error::Validation(format!(
            "{} must be at most {} characters, got {}",
            label,
            MAX_LEN,
            name.len()
        )));
    }
    // Pattern: [a-z0-9]+(-[a-z0-9]+)*
    let valid = !name.is_empty()
        && name.split('-').all(|seg| {
            !seg.is_empty()
                && seg
                    .chars()
                    .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit())
        });
    if !valid {
        return Err(crate::error::Error::Validation(format!(
            "{} must match pattern [a-z0-9]+(-[a-z0-9]+)*, got {:?}",
            label, name
        )));
    }
    Ok(())
}

/// Validate a harness name.
/// Pattern: `[a-z0-9]+(-[a-z0-9]+)*`, max 64 characters.
pub fn validate_harness_name(name: &str) -> crate::error::Result<()> {
    validate_addressable_name(name, "harness_name")
}

/// Validate an agent name.
/// Pattern: `[a-z0-9]+(-[a-z0-9]+)*`, max 64 characters.
pub fn validate_agent_name(name: &str) -> crate::error::Result<()> {
    validate_addressable_name(name, "agent_name")
}

/// Request to create a session
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CreateSessionRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub harness_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub harness_name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub title: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub locale: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub model_id: Option<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub capabilities: Vec<AgentCapabilityConfig>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub tools: Vec<ToolDefinition>,
    #[serde(skip_serializing_if = "Vec::is_empty", default)]
    pub initial_files: Vec<InitialFile>,
}

impl Default for CreateSessionRequest {
    fn default() -> Self {
        Self::new()
    }
}

impl CreateSessionRequest {
    /// Create a new request (server defaults to Generic harness)
    pub fn new() -> Self {
        Self {
            harness_id: None,
            harness_name: None,
            agent_id: None,
            title: None,
            locale: None,
            model_id: None,
            tags: vec![],
            capabilities: vec![],
            tools: vec![],
            initial_files: vec![],
        }
    }

    /// Set the harness ID
    pub fn harness_id(mut self, harness_id: impl Into<String>) -> Self {
        self.harness_id = Some(harness_id.into());
        self
    }

    /// Set the harness name (preferred over harness_id).
    /// Must match `[a-z0-9]+(-[a-z0-9]+)*`, max 64 characters.
    /// Cannot be used together with `harness_id`.
    pub fn harness_name(mut self, harness_name: impl Into<String>) -> Self {
        self.harness_name = Some(harness_name.into());
        self
    }

    /// Set the agent ID
    pub fn agent_id(mut self, agent_id: impl Into<String>) -> Self {
        self.agent_id = Some(agent_id.into());
        self
    }

    /// Set the session title
    pub fn title(mut self, title: impl Into<String>) -> Self {
        self.title = Some(title.into());
        self
    }

    /// Set the session locale
    pub fn locale(mut self, locale: impl Into<String>) -> Self {
        self.locale = Some(locale.into());
        self
    }

    /// Set the model ID
    pub fn model_id(mut self, model_id: impl Into<String>) -> Self {
        self.model_id = Some(model_id.into());
        self
    }

    /// Set the tags
    pub fn tags(mut self, tags: Vec<String>) -> Self {
        self.tags = tags;
        self
    }

    /// Set the capabilities
    pub fn capabilities(mut self, capabilities: Vec<AgentCapabilityConfig>) -> Self {
        self.capabilities = capabilities;
        self
    }

    /// Set client-side tools for this session
    pub fn tools(mut self, tools: Vec<ToolDefinition>) -> Self {
        self.tools = tools;
        self
    }

    /// Set the initial files copied into the session workspace
    pub fn initial_files(mut self, initial_files: Vec<InitialFile>) -> Self {
        self.initial_files = initial_files;
        self
    }
}

/// External actor identity for messages from external channels (Slack, Discord, etc.)
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ExternalActor {
    /// Opaque actor identifier from the source channel
    pub actor_id: String,
    /// Source channel identifier (e.g. "slack", "discord")
    pub source: String,
    /// Resolved display name (falls back to actor_id if absent)
    #[serde(default)]
    pub actor_name: Option<String>,
    /// Channel-specific metadata
    #[serde(default)]
    pub metadata: Option<std::collections::HashMap<String, String>>,
}

impl ExternalActor {
    /// Create a new ExternalActor with required fields
    pub fn new(actor_id: impl Into<String>, source: impl Into<String>) -> Self {
        Self {
            actor_id: actor_id.into(),
            source: source.into(),
            actor_name: None,
            metadata: None,
        }
    }

    /// Set the display name
    pub fn actor_name(mut self, name: impl Into<String>) -> Self {
        self.actor_name = Some(name.into());
        self
    }

    /// Set metadata
    pub fn metadata(mut self, metadata: std::collections::HashMap<String, String>) -> Self {
        self.metadata = Some(metadata);
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
    /// External actor identity (for messages from external channels)
    #[serde(default)]
    pub external_actor: Option<ExternalActor>,
    /// Execution phase for multi-step tool-calling flows
    #[serde(default)]
    pub phase: Option<String>,
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

impl ContentPart {
    /// Create a text content part
    pub fn text(text: impl Into<String>) -> Self {
        Self::Text { text: text.into() }
    }

    /// Create a tool result content part with a successful result
    pub fn tool_result(tool_call_id: impl Into<String>, result: serde_json::Value) -> Self {
        Self::ToolResult {
            tool_call_id: tool_call_id.into(),
            result: Some(result),
            error: None,
        }
    }

    /// Create a tool result content part with an error
    pub fn tool_error(tool_call_id: impl Into<String>, error: impl Into<String>) -> Self {
        Self::ToolResult {
            tool_call_id: tool_call_id.into(),
            result: None,
            error: Some(error.into()),
        }
    }

    /// Returns true if this is a tool call content part
    pub fn is_tool_call(&self) -> bool {
        matches!(self, Self::ToolCall { .. })
    }

    /// Extract tool call info if this is a tool call content part
    pub fn as_tool_call(&self) -> Option<ToolCallInfo<'_>> {
        match self {
            Self::ToolCall {
                id,
                name,
                arguments,
            } => Some(ToolCallInfo {
                id,
                name,
                arguments,
            }),
            _ => None,
        }
    }
}

/// Borrowed view of a tool call content part
#[derive(Debug, Clone)]
pub struct ToolCallInfo<'a> {
    pub id: &'a str,
    pub name: &'a str,
    pub arguments: &'a serde_json::Value,
}

/// A single tool result from the client.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ClientToolResult {
    pub tool_call_id: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

/// Request to submit client-side tool results.
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct SubmitToolResultsRequest {
    pub tool_results: Vec<ClientToolResult>,
}

/// Response from submitting tool results.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct SubmitToolResultsResponse {
    pub accepted: u64,
    pub status: String,
}

/// Request to create a message
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CreateMessageRequest {
    pub message: MessageInput,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub controls: Option<Controls>,
    /// External actor identity (for messages from external channels like Slack)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub external_actor: Option<ExternalActor>,
}

impl CreateMessageRequest {
    /// Create a new request with message input
    pub fn new(message: MessageInput) -> Self {
        Self {
            message,
            controls: None,
            external_actor: None,
        }
    }

    /// Create a user text message
    pub fn user_text(text: impl Into<String>) -> Self {
        Self::new(MessageInput::user_text(text))
    }

    /// Create a tool result message containing one or more tool results
    pub fn tool_results(results: Vec<ContentPart>) -> Self {
        Self::new(MessageInput::tool_results(results))
    }

    /// Set the controls
    pub fn controls(mut self, controls: Controls) -> Self {
        self.controls = Some(controls);
        self
    }

    /// Set the external actor identity
    pub fn external_actor(mut self, actor: ExternalActor) -> Self {
        self.external_actor = Some(actor);
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

    /// Create a tool result message containing one or more tool results
    pub fn tool_results(results: Vec<ContentPart>) -> Self {
        Self::new(MessageRole::ToolResult, results)
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
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ListResponse<T> {
    pub data: Vec<T>,
    #[serde(default)]
    pub total: u64,
    #[serde(default)]
    pub offset: u64,
    #[serde(default)]
    pub limit: u64,
}

/// SSE Event from the server
#[derive(Debug, Clone, Serialize, Deserialize)]
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

impl Event {
    /// Extract tool calls from an `output.message.completed` event's data.
    ///
    /// Returns tool call content parts found in `data.message.content`.
    pub fn tool_calls(&self) -> Vec<ToolCallInfo<'_>> {
        extract_tool_calls(&self.data)
    }
}

/// Extract tool call info from `tool.call_requested` or `output.message.completed` event data.
pub fn extract_tool_calls(data: &serde_json::Value) -> Vec<ToolCallInfo<'_>> {
    if let Some(tool_calls) = data.get("tool_calls").and_then(|c| c.as_array()) {
        return tool_calls
            .iter()
            .filter_map(|part| {
                Some(ToolCallInfo {
                    id: part.get("id")?.as_str()?,
                    name: part.get("name")?.as_str()?,
                    arguments: part.get("arguments")?,
                })
            })
            .collect();
    }

    let Some(content) = data
        .get("message")
        .and_then(|m| m.get("content"))
        .and_then(|c| c.as_array())
    else {
        return vec![];
    };
    content
        .iter()
        .filter_map(|part| {
            if part.get("type")?.as_str()? != "tool_call" {
                return None;
            }
            Some(ToolCallInfo {
                id: part.get("id")?.as_str()?,
                name: part.get("name")?.as_str()?,
                arguments: part.get("arguments")?,
            })
        })
        .collect()
}

/// Context for an event
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct EventContext {
    #[serde(default)]
    pub turn_id: Option<String>,
    #[serde(default)]
    pub input_message_id: Option<String>,
}

// --- Workspace Models ---

/// Workspace resource.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Workspace {
    pub id: String,
    pub name: String,
    pub status: String,
    pub created_at: String,
    pub updated_at: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub archived_at: Option<String>,
    #[serde(default)]
    pub deleted_at: Option<String>,
}

/// Request to create a workspace.
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CreateWorkspaceRequest {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

impl CreateWorkspaceRequest {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            description: None,
        }
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }
}

/// Request to update a workspace.
#[derive(Debug, Clone, Default, Serialize)]
#[non_exhaustive]
pub struct UpdateWorkspaceRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
}

impl UpdateWorkspaceRequest {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn name(mut self, name: impl Into<String>) -> Self {
        self.name = Some(name.into());
        self
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }

    pub fn status(mut self, status: impl Into<String>) -> Self {
        self.status = Some(status.into());
        self
    }
}

// --- Workspace Filesystem Models ---

/// File metadata without content
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct FileInfo {
    pub id: String,
    pub session_id: String,
    pub path: String,
    pub name: String,
    pub is_directory: bool,
    pub is_readonly: bool,
    pub size_bytes: i64,
    pub created_at: String,
    pub updated_at: String,
}

/// Complete file with content
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct SessionFile {
    pub id: String,
    pub session_id: String,
    pub path: String,
    pub name: String,
    pub is_directory: bool,
    pub is_readonly: bool,
    pub size_bytes: i64,
    pub created_at: String,
    pub updated_at: String,
    #[serde(default)]
    pub content: Option<String>,
    #[serde(default)]
    pub encoding: Option<String>,
}

/// File stat information (without id/session_id)
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct FileStat {
    pub path: String,
    pub name: String,
    pub is_directory: bool,
    pub is_readonly: bool,
    pub size_bytes: i64,
    pub created_at: String,
    pub updated_at: String,
}

/// Request to create a file or directory
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CreateFileRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_directory: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_readonly: Option<bool>,
}

impl CreateFileRequest {
    /// Create a request for a new file
    pub fn file(content: impl Into<String>) -> Self {
        Self {
            content: Some(content.into()),
            encoding: None,
            is_directory: None,
            is_readonly: None,
        }
    }

    /// Create a request for a new directory
    pub fn directory() -> Self {
        Self {
            content: None,
            encoding: None,
            is_directory: Some(true),
            is_readonly: None,
        }
    }

    /// Set the content encoding ("text" or "base64")
    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }

    /// Set the readonly flag
    pub fn is_readonly(mut self, is_readonly: bool) -> Self {
        self.is_readonly = Some(is_readonly);
        self
    }
}

/// Request to update a file
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct UpdateFileRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_readonly: Option<bool>,
}

impl UpdateFileRequest {
    /// Create a request to update file content
    pub fn content(content: impl Into<String>) -> Self {
        Self {
            content: Some(content.into()),
            encoding: None,
            is_readonly: None,
        }
    }

    /// Set the content encoding ("text" or "base64")
    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }

    /// Set the readonly flag
    pub fn is_readonly(mut self, is_readonly: bool) -> Self {
        self.is_readonly = Some(is_readonly);
        self
    }
}

/// Request to copy a file
#[derive(Debug, Clone, Serialize)]
pub struct CopyFileRequest {
    pub src_path: String,
    pub dst_path: String,
}

impl CopyFileRequest {
    pub fn new(src_path: impl Into<String>, dst_path: impl Into<String>) -> Self {
        Self {
            src_path: src_path.into(),
            dst_path: dst_path.into(),
        }
    }
}

/// Request to move/rename a file
#[derive(Debug, Clone, Serialize)]
pub struct MoveFileRequest {
    pub src_path: String,
    pub dst_path: String,
}

impl MoveFileRequest {
    pub fn new(src_path: impl Into<String>, dst_path: impl Into<String>) -> Self {
        Self {
            src_path: src_path.into(),
            dst_path: dst_path.into(),
        }
    }
}

/// Request to search files with regex
#[derive(Debug, Clone, Serialize)]
pub struct GrepRequest {
    pub pattern: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub path_pattern: Option<String>,
}

impl GrepRequest {
    pub fn new(pattern: impl Into<String>) -> Self {
        Self {
            pattern: pattern.into(),
            path_pattern: None,
        }
    }

    /// Set an optional path pattern to filter files
    pub fn path_pattern(mut self, path_pattern: impl Into<String>) -> Self {
        self.path_pattern = Some(path_pattern.into());
        self
    }
}

/// Request to get file stat
#[derive(Debug, Clone, Serialize)]
pub struct StatRequest {
    pub path: String,
}

impl StatRequest {
    pub fn new(path: impl Into<String>) -> Self {
        Self { path: path.into() }
    }
}

/// Single grep match
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GrepMatch {
    pub path: String,
    pub line_number: u64,
    pub line: String,
}

/// Grep result for a file
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GrepResult {
    pub path: String,
    pub matches: Vec<GrepMatch>,
}

/// Response for delete operations
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DeleteResponse {
    pub deleted: bool,
}

// --- Memory Models ---

/// Memory resource.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Memory {
    pub id: String,
    pub name: String,
    pub source_type: String,
    pub source: serde_json::Value,
    pub is_readonly: bool,
    pub sync_status: String,
    pub status: String,
    pub created_at: String,
    pub updated_at: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub last_sync_error: Option<String>,
    #[serde(default)]
    pub last_synced_at: Option<String>,
    #[serde(default)]
    pub archived_at: Option<String>,
    #[serde(default)]
    pub deleted_at: Option<String>,
}

/// Request to create a memory.
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CreateMemoryRequest {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source: Option<serde_json::Value>,
}

impl CreateMemoryRequest {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            description: None,
            source: None,
        }
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }

    pub fn source(mut self, source: serde_json::Value) -> Self {
        self.source = Some(source);
        self
    }
}

/// Request to update a memory.
#[derive(Debug, Clone, Default, Serialize)]
#[non_exhaustive]
pub struct UpdateMemoryRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source: Option<serde_json::Value>,
}

impl UpdateMemoryRequest {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn name(mut self, name: impl Into<String>) -> Self {
        self.name = Some(name.into());
        self
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }

    pub fn source(mut self, source: serde_json::Value) -> Self {
        self.source = Some(source);
        self
    }
}

/// Memory file metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct MemoryFileInfo {
    pub path: String,
    pub is_directory: bool,
    pub size_bytes: i64,
    pub created_at: String,
    pub updated_at: String,
    #[serde(default)]
    pub content_hash: Option<String>,
}

/// Memory file content.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct MemoryFile {
    pub path: String,
    pub content: String,
    pub encoding: String,
    pub size_bytes: i64,
    pub created_at: String,
    pub updated_at: String,
    #[serde(default)]
    pub content_hash: Option<String>,
}

/// Request to create a memory file or directory.
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CreateMemoryFileRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub is_directory: Option<bool>,
}

impl CreateMemoryFileRequest {
    pub fn file(content: impl Into<String>) -> Self {
        Self {
            content: Some(content.into()),
            encoding: None,
            is_directory: None,
        }
    }

    pub fn directory() -> Self {
        Self {
            content: None,
            encoding: None,
            is_directory: Some(true),
        }
    }

    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }
}

/// Request to update a memory file.
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct UpdateMemoryFileRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
}

impl UpdateMemoryFileRequest {
    pub fn content(content: impl Into<String>) -> Self {
        Self {
            content: Some(content.into()),
            encoding: None,
        }
    }

    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }
}

/// Memory grep result entry.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct MemoryGrepResult {
    pub path: String,
    pub size_bytes: i64,
}

// --- Agent Analysis and Guardrail Models ---

#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct AnalyzeAgentRequest {
    pub system_prompt: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub capabilities: Vec<AgentCapabilityConfig>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tools: Vec<serde_json::Value>,
    #[serde(rename = "mcpServers", skip_serializing_if = "Option::is_none")]
    pub mcp_servers: Option<serde_json::Value>,
}

impl AnalyzeAgentRequest {
    pub fn new(system_prompt: impl Into<String>) -> Self {
        Self {
            system_prompt: system_prompt.into(),
            capabilities: Vec::new(),
            tools: Vec::new(),
            mcp_servers: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct AgentAnalysisResponse {
    pub findings: Vec<Finding>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Finding {
    pub rule_id: String,
    pub severity: String,
    pub category: String,
    pub source: String,
    pub message: String,
    #[serde(default)]
    pub location: Option<FindingLocation>,
    #[serde(default)]
    pub fix: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct FindingLocation {
    pub field: String,
    #[serde(default)]
    pub start: Option<u64>,
    #[serde(default)]
    pub end: Option<u64>,
}

#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct GuardrailsDryRunRequest {
    pub config: serde_json::Value,
    pub stage: String,
    pub text: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_name: Option<String>,
}

impl GuardrailsDryRunRequest {
    pub fn new(
        config: serde_json::Value,
        stage: impl Into<String>,
        text: impl Into<String>,
    ) -> Self {
        Self {
            config,
            stage: stage.into(),
            text: text.into(),
            tool_name: None,
        }
    }

    pub fn tool_name(mut self, tool_name: impl Into<String>) -> Self {
        self.tool_name = Some(tool_name.into());
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GuardrailsDryRunResponse {
    pub hits: Vec<GuardrailsDryRunHit>,
    pub blocked: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GuardrailsDryRunHit {
    pub check_index: i32,
    pub check_id: String,
    pub stage: String,
    pub rule_type: String,
    pub action: String,
    pub reason_code: String,
    #[serde(default)]
    pub matched: Option<String>,
    #[serde(default)]
    pub replacement: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GuardrailExamplesResponse {
    pub examples: Vec<GuardrailExample>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GuardrailExample {
    pub name: String,
    pub display_name: String,
    pub description: String,
    pub tags: Vec<String>,
    pub check_types: Vec<String>,
    pub stages: Vec<String>,
    pub data_egress: String,
    pub config: serde_json::Value,
}

// --- Budget Models ---

/// Budget status
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum BudgetStatus {
    Active,
    Paused,
    Exhausted,
    Disabled,
}

/// Budget period configuration for recurring budgets
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum BudgetPeriod {
    /// Rolling window (e.g. "last 24 hours")
    Rolling { window: String },
    /// Calendar-aligned (e.g. "per month")
    Calendar { unit: String },
}

/// Budget — a spending cap for a subject in a currency
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Budget {
    pub id: String,
    pub organization_id: String,
    pub subject_type: String,
    pub subject_id: String,
    pub currency: String,
    pub limit: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub soft_limit: Option<f64>,
    pub balance: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub period: Option<BudgetPeriod>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
    pub status: BudgetStatus,
    pub created_at: String,
    pub updated_at: String,
}

/// Request to create a budget
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct CreateBudgetRequest {
    pub subject_type: String,
    pub subject_id: String,
    pub currency: String,
    pub limit: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub soft_limit: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub period: Option<BudgetPeriod>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
}

impl CreateBudgetRequest {
    /// Create a new budget request with required fields
    pub fn new(
        subject_type: impl Into<String>,
        subject_id: impl Into<String>,
        currency: impl Into<String>,
        limit: f64,
    ) -> Self {
        Self {
            subject_type: subject_type.into(),
            subject_id: subject_id.into(),
            currency: currency.into(),
            limit,
            soft_limit: None,
            period: None,
            metadata: None,
        }
    }

    /// Set the soft limit
    pub fn soft_limit(mut self, soft_limit: f64) -> Self {
        self.soft_limit = Some(soft_limit);
        self
    }

    /// Set the period
    pub fn period(mut self, period: BudgetPeriod) -> Self {
        self.period = Some(period);
        self
    }

    /// Set metadata
    pub fn metadata(mut self, metadata: serde_json::Value) -> Self {
        self.metadata = Some(metadata);
        self
    }
}

/// Request to update a budget
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct UpdateBudgetRequest {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub limit: Option<f64>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub soft_limit: Option<Option<f64>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
}

impl UpdateBudgetRequest {
    /// Create a new empty update request
    pub fn new() -> Self {
        Self {
            limit: None,
            soft_limit: None,
            status: None,
            metadata: None,
        }
    }

    /// Set the limit
    pub fn limit(mut self, limit: f64) -> Self {
        self.limit = Some(limit);
        self
    }

    /// Set the soft limit (None to remove)
    pub fn soft_limit(mut self, soft_limit: Option<f64>) -> Self {
        self.soft_limit = Some(soft_limit);
        self
    }

    /// Set the status
    pub fn status(mut self, status: impl Into<String>) -> Self {
        self.status = Some(status.into());
        self
    }

    /// Set metadata
    pub fn metadata(mut self, metadata: serde_json::Value) -> Self {
        self.metadata = Some(metadata);
        self
    }
}

impl Default for UpdateBudgetRequest {
    fn default() -> Self {
        Self::new()
    }
}

/// Request to top up a budget
#[derive(Debug, Clone, Serialize)]
pub struct TopUpRequest {
    pub amount: f64,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

impl TopUpRequest {
    /// Create a new top-up request
    pub fn new(amount: f64) -> Self {
        Self {
            amount,
            description: None,
        }
    }

    /// Set the description
    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }
}

/// Ledger entry recording resource consumption or credit
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct LedgerEntry {
    pub id: String,
    pub budget_id: String,
    pub amount: f64,
    pub meter_source: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ref_type: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ref_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub session_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub created_at: String,
}

/// Result of checking all budgets for a session
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct BudgetCheckResult {
    pub action: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub budget_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub balance: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub currency: Option<String>,
}

/// Response from session resume endpoint
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResumeSessionResponse {
    pub resumed_budgets: i32,
    pub session_id: String,
}

// --- Connections Models ---

/// A user connection to an external provider
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Connection {
    pub provider: String,
    pub created_at: String,
    pub updated_at: String,
}

/// Request to set a connection API key
#[derive(Debug, Clone, Serialize)]
pub struct SetConnectionRequest {
    pub api_key: String,
}

impl SetConnectionRequest {
    pub fn new(api_key: impl Into<String>) -> Self {
        Self {
            api_key: api_key.into(),
        }
    }
}

// --- Session Secrets Models ---

/// Request to batch-set session secrets
#[derive(Debug, Clone, Serialize)]
pub struct SetSecretsRequest {
    pub secrets: std::collections::HashMap<String, String>,
}

impl SetSecretsRequest {
    pub fn new(secrets: std::collections::HashMap<String, String>) -> Self {
        Self { secrets }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn list_response_deserializes_without_pagination_fields() {
        let json = r#"{"data": [1, 2, 3]}"#;
        let resp: ListResponse<i32> = serde_json::from_str(json).unwrap();
        assert_eq!(resp.data, vec![1, 2, 3]);
        assert_eq!(resp.total, 0);
        assert_eq!(resp.offset, 0);
        assert_eq!(resp.limit, 0);
    }

    #[test]
    fn list_response_deserializes_with_pagination_fields() {
        let json = r#"{"data": ["a"], "total": 10, "offset": 5, "limit": 25}"#;
        let resp: ListResponse<String> = serde_json::from_str(json).unwrap();
        assert_eq!(resp.data, vec!["a"]);
        assert_eq!(resp.total, 10);
        assert_eq!(resp.offset, 5);
        assert_eq!(resp.limit, 25);
    }
}
