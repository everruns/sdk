//! Public data models generated from the Everruns OpenAPI document.
//!
//! Regenerate with `just generate`. Do not edit by hand.

use serde::{Deserialize, Serialize};

/// Agent configuration for agentic loop.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Agent {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub archived_at: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub capabilities: Vec<AgentCapabilityConfig>,
    pub created_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub default_model_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub default_version_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub deleted_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub forked_from_agent_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub forked_from_version_id: Option<String>,
    #[serde(default)]
    pub harness_id: String,
    pub id: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub initial_files: Vec<InitialFile>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_iterations: Option<u64>,
    #[serde(rename = "mcpServers")]
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mcp_servers: Option<serde_json::Value>,
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub network_access: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parallel_tool_calls: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub root_agent_id: Option<String>,
    pub status: AgentStatus,
    pub system_prompt: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tools: Vec<ToolDefinition>,
    pub updated_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub usage: Option<TokenUsage>,
}

/// Response from on-demand agent analysis (built-in rules + LLM checkers)
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct AgentAnalysisResponse {
    pub findings: Vec<Finding>,
}

/// Per-agent capability configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct AgentCapabilityConfig {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub config: Option<serde_json::Value>,
    #[serde(rename = "ref")]
    pub capability_ref: String,
}

impl AgentCapabilityConfig {
    pub fn new(capability_ref: impl Into<String>) -> Self {
        Self {
            config: None,
            capability_ref: capability_ref.into(),
        }
    }

    pub fn config(mut self, config: serde_json::Value) -> Self {
        self.config = Some(config);
        self
    }
}

/// Agent lifecycle status.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum AgentStatus {
    #[serde(rename = "active")]
    Active,
    #[serde(rename = "archived")]
    Archived,
    #[serde(rename = "deleted")]
    Deleted,
}

/// Immutable snapshot of an Agent's authored and resolved runtime config.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct AgentVersion {
    pub agent_id: String,
    pub authored_config: serde_json::Value,
    pub change_kind: AgentVersionChangeKind,
    pub config_hash: String,
    pub created_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub created_by_principal_id: Option<String>,
    pub id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub is_published: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent_version_id: Option<String>,
    pub resolved_config: serde_json::Value,
    pub semver_major: i32,
    pub semver_minor: i32,
    pub semver_patch: i32,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_version_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub summary: Option<String>,
    pub version: String,
    pub version_number: i32,
}

/// Reason a version was created. Stored as lower_snake_case text.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum AgentVersionChangeKind {
    #[serde(rename = "auto")]
    Auto,
    #[serde(rename = "manual")]
    Manual,
    #[serde(rename = "patch")]
    Patch,
    #[serde(rename = "minor")]
    Minor,
    #[serde(rename = "major")]
    Major,
    #[serde(rename = "import")]
    Import,
    #[serde(rename = "rollback")]
    Rollback,
    #[serde(rename = "fork")]
    Fork,
}

/// Response body for agent version diff.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct AgentVersionDiffResponse {
    pub authored_diff: serde_json::Value,
    pub from_version_id: serde_json::Value,
    pub resolved_diff: serde_json::Value,
    pub to_version_id: serde_json::Value,
}

/// Budget — a spending cap for a subject in a currency.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Budget {
    pub balance: f64,
    pub created_at: String,
    pub currency: String,
    pub id: String,
    pub limit: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
    pub organization_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub period: Option<BudgetPeriod>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub period_started_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub soft_limit: Option<f64>,
    pub status: BudgetStatus,
    pub subject_id: String,
    pub subject_type: serde_json::Value,
    pub updated_at: String,
}

/// Result of checking all budgets for a session.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct BudgetCheckResult {
    pub action: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub balance: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub budget_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub currency: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error_code: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error_fields: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
}

/// Budget period configuration for recurring budgets.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum BudgetPeriod {
    #[serde(rename = "duration")]
    Duration { seconds: i64 },
    #[serde(rename = "rolling")]
    Rolling { window: String },
    #[serde(rename = "calendar")]
    Calendar { unit: String },
}

/// Budget status.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum BudgetStatus {
    #[serde(rename = "active")]
    Active,
    #[serde(rename = "paused")]
    Paused,
    #[serde(rename = "exhausted")]
    Exhausted,
    #[serde(rename = "disabled")]
    Disabled,
}

/// Built-in tool configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct BuiltinTool {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub category: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub deferrable: Option<serde_json::Value>,
    pub description: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub full_parameters: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hints: Option<serde_json::Value>,
    pub name: String,
    pub parameters: serde_json::Value,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub policy: Option<serde_json::Value>,
}

impl BuiltinTool {
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        parameters: serde_json::Value,
    ) -> Self {
        Self {
            category: None,
            deferrable: None,
            description: description.into(),
            display_name: None,
            full_parameters: None,
            hints: None,
            name: name.into(),
            parameters,
            policy: None,
        }
    }

    pub fn category(mut self, category: impl Into<String>) -> Self {
        self.category = Some(category.into());
        self
    }

    pub fn deferrable(mut self, deferrable: serde_json::Value) -> Self {
        self.deferrable = Some(deferrable);
        self
    }

    pub fn display_name(mut self, display_name: impl Into<String>) -> Self {
        self.display_name = Some(display_name.into());
        self
    }

    pub fn full_parameters(mut self, full_parameters: serde_json::Value) -> Self {
        self.full_parameters = Some(full_parameters);
        self
    }

    pub fn hints(mut self, hints: serde_json::Value) -> Self {
        self.hints = Some(hints);
        self
    }

    pub fn policy(mut self, policy: serde_json::Value) -> Self {
        self.policy = Some(policy);
        self
    }
}

/// Public capability information (without internal details)
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct CapabilityInfo {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_count: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub category: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub config_schema: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub config_ui_schema: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub dependencies: Vec<String>,
    pub description: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub docs_slug: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub features: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub harness_count: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub icon: Option<String>,
    pub id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub is_guardrail: Option<bool>,
    #[serde(default)]
    pub is_mcp: bool,
    #[serde(default)]
    pub is_skill: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub localizations: Option<std::collections::HashMap<String, serde_json::Value>>,
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub risk_level: Option<String>,
    pub status: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub system_prompt: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tool_definitions: Vec<serde_json::Value>,
}

/// Client-side tool - executed by the client, not the server
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ClientSideTool {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub category: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub deferrable: Option<serde_json::Value>,
    pub description: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub full_parameters: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hints: Option<serde_json::Value>,
    pub name: String,
    pub parameters: serde_json::Value,
}

impl ClientSideTool {
    pub fn new(
        name: impl Into<String>,
        description: impl Into<String>,
        parameters: serde_json::Value,
    ) -> Self {
        Self {
            category: None,
            deferrable: None,
            description: description.into(),
            display_name: None,
            full_parameters: None,
            hints: None,
            name: name.into(),
            parameters,
        }
    }

    pub fn category(mut self, category: impl Into<String>) -> Self {
        self.category = Some(category.into());
        self
    }

    pub fn deferrable(mut self, deferrable: serde_json::Value) -> Self {
        self.deferrable = Some(deferrable);
        self
    }

    pub fn display_name(mut self, display_name: impl Into<String>) -> Self {
        self.display_name = Some(display_name.into());
        self
    }

    pub fn full_parameters(mut self, full_parameters: serde_json::Value) -> Self {
        self.full_parameters = Some(full_parameters);
        self
    }

    pub fn hints(mut self, hints: serde_json::Value) -> Self {
        self.hints = Some(hints);
        self
    }
}

/// A single tool result from the client
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ClientToolResult {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub result: Option<serde_json::Value>,
    pub tool_call_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Connection {
    pub provider: String,
    pub created_at: String,
    pub updated_at: String,
}

/// A part of message content - can be text, image, image_file, tool_call, or tool_result
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ContentPart {
    #[serde(rename = "text")]
    Text { text: String },
    #[serde(rename = "image")]
    Image {
        #[serde(default, skip_serializing_if = "Option::is_none")]
        base64: Option<String>,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        url: Option<String>,
    },
    #[serde(rename = "image_file")]
    ImageFile { image_id: String },
    #[serde(rename = "tool_call")]
    ToolCall {
        arguments: serde_json::Value,
        id: String,
        name: String,
    },
    #[serde(rename = "tool_result")]
    ToolResult {
        #[serde(default, skip_serializing_if = "Option::is_none")]
        error: Option<String>,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        result: Option<serde_json::Value>,
        tool_call_id: String,
    },
}

/// Runtime controls for message processing
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct Controls {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error_disclosure: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hints: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub locale: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub model_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reasoning: Option<serde_json::Value>,
}

/// Request to copy a file
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct CopyFileRequest {
    pub dst_path: String,
    pub src_path: String,
}

impl CopyFileRequest {
    pub fn new(src_path: impl Into<String>, dst_path: impl Into<String>) -> Self {
        Self {
            dst_path: dst_path.into(),
            src_path: src_path.into(),
        }
    }
}

/// Request to create a new agent
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct CreateAgentRequest {
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub capabilities: Vec<AgentCapabilityConfig>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub default_model_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub harness_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub harness_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub id: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub initial_files: Vec<InitialFile>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_iterations: Option<u64>,
    #[serde(rename = "mcpServers")]
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mcp_servers: Option<serde_json::Value>,
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub network_access: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parallel_tool_calls: Option<bool>,
    pub system_prompt: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tools: Vec<ToolDefinition>,
}

impl CreateAgentRequest {
    pub fn new(name: impl Into<String>, system_prompt: impl Into<String>) -> Self {
        Self {
            capabilities: Vec::new(),
            default_model_id: None,
            description: None,
            display_name: None,
            harness_id: None,
            harness_name: None,
            id: None,
            initial_files: Vec::new(),
            max_iterations: None,
            mcp_servers: None,
            name: name.into(),
            network_access: None,
            parallel_tool_calls: None,
            system_prompt: system_prompt.into(),
            tags: Vec::new(),
            tools: Vec::new(),
        }
    }

    pub fn capabilities(mut self, capabilities: Vec<AgentCapabilityConfig>) -> Self {
        self.capabilities = capabilities;
        self
    }

    pub fn default_model_id(mut self, default_model_id: impl Into<String>) -> Self {
        self.default_model_id = Some(default_model_id.into());
        self
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }

    pub fn display_name(mut self, display_name: impl Into<String>) -> Self {
        self.display_name = Some(display_name.into());
        self
    }

    pub fn harness_id(mut self, harness_id: impl Into<String>) -> Self {
        self.harness_id = Some(harness_id.into());
        self
    }

    pub fn harness_name(mut self, harness_name: impl Into<String>) -> Self {
        self.harness_name = Some(harness_name.into());
        self
    }

    pub fn id(mut self, id: impl Into<String>) -> Self {
        self.id = Some(id.into());
        self
    }

    pub fn initial_files(mut self, initial_files: Vec<InitialFile>) -> Self {
        self.initial_files = initial_files;
        self
    }

    pub fn max_iterations(mut self, max_iterations: u64) -> Self {
        self.max_iterations = Some(max_iterations);
        self
    }

    pub fn mcp_servers(mut self, mcp_servers: serde_json::Value) -> Self {
        self.mcp_servers = Some(mcp_servers);
        self
    }

    pub fn network_access(mut self, network_access: serde_json::Value) -> Self {
        self.network_access = Some(network_access);
        self
    }

    pub fn parallel_tool_calls(mut self, parallel_tool_calls: bool) -> Self {
        self.parallel_tool_calls = Some(parallel_tool_calls);
        self
    }

    pub fn tags(mut self, tags: Vec<String>) -> Self {
        self.tags = tags;
        self
    }

    pub fn tools(mut self, tools: Vec<ToolDefinition>) -> Self {
        self.tools = tools;
        self
    }
}

/// Request body for the `create_agent_version` operation.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct CreateAgentVersionRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub change_kind: Option<AgentVersionChangeKind>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub summary: Option<String>,
}

impl CreateAgentVersionRequest {
    pub fn new() -> Self {
        Self {
            change_kind: None,
            summary: None,
        }
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

/// Request body for creating a spending budget.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct CreateBudgetRequest {
    pub currency: String,
    pub limit: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub period: Option<BudgetPeriod>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub soft_limit: Option<f64>,
    pub subject_id: String,
    pub subject_type: String,
}

impl CreateBudgetRequest {
    pub fn new(
        subject_type: impl Into<String>,
        subject_id: impl Into<String>,
        currency: impl Into<String>,
        limit: f64,
    ) -> Self {
        Self {
            currency: currency.into(),
            limit,
            metadata: None,
            period: None,
            soft_limit: None,
            subject_id: subject_id.into(),
            subject_type: subject_type.into(),
        }
    }

    pub fn metadata(mut self, metadata: serde_json::Value) -> Self {
        self.metadata = Some(metadata);
        self
    }

    pub fn period(mut self, period: BudgetPeriod) -> Self {
        self.period = Some(period);
        self
    }

    pub fn soft_limit(mut self, soft_limit: f64) -> Self {
        self.soft_limit = Some(soft_limit);
        self
    }
}

/// Request to create a file
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct CreateFileRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub is_directory: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub is_readonly: Option<bool>,
}

impl CreateFileRequest {
    pub fn content(mut self, content: impl Into<String>) -> Self {
        self.content = Some(content.into());
        self
    }

    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }

    pub fn is_directory(mut self, is_directory: bool) -> Self {
        self.is_directory = Some(is_directory);
        self
    }

    pub fn is_readonly(mut self, is_readonly: bool) -> Self {
        self.is_readonly = Some(is_readonly);
        self
    }

    pub fn file(content: impl Into<String>) -> Self {
        Self {
            content: Some(content.into()),
            encoding: None,
            is_directory: None,
            is_readonly: None,
        }
    }

    pub fn directory() -> Self {
        Self {
            content: None,
            encoding: None,
            is_directory: Some(true),
            is_readonly: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct CreateMemoryFileRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub is_directory: Option<bool>,
}

impl CreateMemoryFileRequest {
    pub fn content(mut self, content: impl Into<String>) -> Self {
        self.content = Some(content.into());
        self
    }

    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }

    pub fn is_directory(mut self, is_directory: bool) -> Self {
        self.is_directory = Some(is_directory);
        self
    }

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
}

/// Request body for the `create_memory` operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct CreateMemoryRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source: Option<serde_json::Value>,
}

impl CreateMemoryRequest {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            description: None,
            name: name.into(),
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

/// Request body for the `create_memory_source` operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum CreateMemorySourceRequest {
    #[serde(rename = "github")]
    Github {
        #[serde(default, skip_serializing_if = "Option::is_none")]
        branch: Option<String>,
        repository: String,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        root_folder: Option<String>,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        sync_interval_secs: Option<i32>,
    },
    #[serde(rename = "git")]
    Git {
        #[serde(default, skip_serializing_if = "Option::is_none")]
        branch: Option<String>,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        root_folder: Option<String>,
        #[serde(default, skip_serializing_if = "Option::is_none")]
        sync_interval_secs: Option<i32>,
        url: String,
    },
}

/// Request to create a message
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct CreateMessageRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub addressed_participant_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub controls: Option<Controls>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub external_actor: Option<ExternalActor>,
    pub message: MessageInput,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata: Option<std::collections::HashMap<String, serde_json::Value>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub tags: Option<Vec<String>>,
}

impl CreateMessageRequest {
    pub fn new(message: MessageInput) -> Self {
        Self {
            addressed_participant_id: None,
            controls: None,
            external_actor: None,
            message,
            metadata: None,
            tags: None,
        }
    }

    pub fn addressed_participant_id(mut self, addressed_participant_id: impl Into<String>) -> Self {
        self.addressed_participant_id = Some(addressed_participant_id.into());
        self
    }

    pub fn controls(mut self, controls: Controls) -> Self {
        self.controls = Some(controls);
        self
    }

    pub fn external_actor(mut self, external_actor: ExternalActor) -> Self {
        self.external_actor = Some(external_actor);
        self
    }

    pub fn metadata(
        mut self,
        metadata: std::collections::HashMap<String, serde_json::Value>,
    ) -> Self {
        self.metadata = Some(metadata);
        self
    }

    pub fn tags(mut self, tags: Vec<String>) -> Self {
        self.tags = Some(tags);
        self
    }
}

/// Request to create a session
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct CreateSessionRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_identity_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_name: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub capabilities: Vec<AgentCapabilityConfig>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub harness_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub harness_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hints: Option<std::collections::HashMap<String, serde_json::Value>>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub initial_files: Vec<InitialFile>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub locale: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_iterations: Option<u64>,
    #[serde(rename = "mcpServers")]
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mcp_servers: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub model_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub network_access: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parallel_tool_calls: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub system_prompt: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub title: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tools: Vec<ToolDefinition>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub workspace_id: Option<String>,
}

impl CreateSessionRequest {
    pub fn new() -> Self {
        Self {
            agent_id: None,
            agent_identity_id: None,
            agent_name: None,
            capabilities: Vec::new(),
            harness_id: None,
            harness_name: None,
            hints: None,
            initial_files: Vec::new(),
            locale: None,
            max_iterations: None,
            mcp_servers: None,
            model_id: None,
            network_access: None,
            parallel_tool_calls: None,
            system_prompt: None,
            tags: Vec::new(),
            title: None,
            tools: Vec::new(),
            workspace_id: None,
        }
    }

    pub fn agent_id(mut self, agent_id: impl Into<String>) -> Self {
        self.agent_id = Some(agent_id.into());
        self
    }

    pub fn agent_identity_id(mut self, agent_identity_id: impl Into<String>) -> Self {
        self.agent_identity_id = Some(agent_identity_id.into());
        self
    }

    pub fn agent_name(mut self, agent_name: impl Into<String>) -> Self {
        self.agent_name = Some(agent_name.into());
        self
    }

    pub fn capabilities(mut self, capabilities: Vec<AgentCapabilityConfig>) -> Self {
        self.capabilities = capabilities;
        self
    }

    pub fn harness_id(mut self, harness_id: impl Into<String>) -> Self {
        self.harness_id = Some(harness_id.into());
        self
    }

    pub fn harness_name(mut self, harness_name: impl Into<String>) -> Self {
        self.harness_name = Some(harness_name.into());
        self
    }

    pub fn hints(mut self, hints: std::collections::HashMap<String, serde_json::Value>) -> Self {
        self.hints = Some(hints);
        self
    }

    pub fn initial_files(mut self, initial_files: Vec<InitialFile>) -> Self {
        self.initial_files = initial_files;
        self
    }

    pub fn locale(mut self, locale: impl Into<String>) -> Self {
        self.locale = Some(locale.into());
        self
    }

    pub fn max_iterations(mut self, max_iterations: u64) -> Self {
        self.max_iterations = Some(max_iterations);
        self
    }

    pub fn mcp_servers(mut self, mcp_servers: serde_json::Value) -> Self {
        self.mcp_servers = Some(mcp_servers);
        self
    }

    pub fn model_id(mut self, model_id: impl Into<String>) -> Self {
        self.model_id = Some(model_id.into());
        self
    }

    pub fn network_access(mut self, network_access: serde_json::Value) -> Self {
        self.network_access = Some(network_access);
        self
    }

    pub fn parallel_tool_calls(mut self, parallel_tool_calls: bool) -> Self {
        self.parallel_tool_calls = Some(parallel_tool_calls);
        self
    }

    pub fn system_prompt(mut self, system_prompt: impl Into<String>) -> Self {
        self.system_prompt = Some(system_prompt.into());
        self
    }

    pub fn tags(mut self, tags: Vec<String>) -> Self {
        self.tags = tags;
        self
    }

    pub fn title(mut self, title: impl Into<String>) -> Self {
        self.title = Some(title.into());
        self
    }

    pub fn tools(mut self, tools: Vec<ToolDefinition>) -> Self {
        self.tools = tools;
        self
    }

    pub fn workspace_id(mut self, workspace_id: impl Into<String>) -> Self {
        self.workspace_id = Some(workspace_id.into());
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct CreateWorkspaceRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub name: String,
}

impl CreateWorkspaceRequest {
    pub fn new(name: impl Into<String>) -> Self {
        Self {
            description: None,
            name: name.into(),
        }
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }
}

/// Response for delete operation
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct DeleteFileResponse {
    pub deleted: bool,
}

/// Standard event following the Everruns event protocol.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Event {
    #[serde(default)]
    pub context: EventContext,
    pub data: serde_json::Value,
    pub id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sequence: Option<i32>,
    pub session_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub tags: Option<Vec<String>>,
    pub ts: String,
    #[serde(rename = "type")]
    pub event_type: String,
}

/// Context for event correlation and tracing
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct EventContext {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub exec_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub input_message_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent_span_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub span_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub trace_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub turn_id: Option<String>,
}

/// External actor identity for messages originating from external channels
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ExternalActor {
    pub actor_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub actor_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata: Option<std::collections::HashMap<String, String>>,
    pub source: String,
}

impl ExternalActor {
    pub fn new(actor_id: impl Into<String>, source: impl Into<String>) -> Self {
        Self {
            actor_id: actor_id.into(),
            actor_name: None,
            metadata: None,
            source: source.into(),
        }
    }

    pub fn actor_name(mut self, actor_name: impl Into<String>) -> Self {
        self.actor_name = Some(actor_name.into());
        self
    }

    pub fn metadata(mut self, metadata: std::collections::HashMap<String, String>) -> Self {
        self.metadata = Some(metadata);
        self
    }
}

/// File metadata without content
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct FileInfo {
    pub created_at: String,
    pub id: String,
    pub is_directory: bool,
    pub is_readonly: bool,
    pub name: String,
    pub path: String,
    pub session_id: String,
    pub size_bytes: i64,
    pub updated_at: String,
}

/// File stat information
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct FileStat {
    pub created_at: String,
    pub is_directory: bool,
    pub is_readonly: bool,
    pub name: String,
    pub path: String,
    pub size_bytes: i64,
    pub updated_at: String,
}

/// A single advisory finding about an agent configuration.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Finding {
    pub category: serde_json::Value,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub fix: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub location: Option<FindingLocation>,
    pub message: String,
    pub rule_id: String,
    pub severity: serde_json::Value,
    pub source: serde_json::Value,
}

/// Pointer to the config field (and optional byte span within it) a finding
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct FindingLocation {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub end: Option<i32>,
    pub field: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub start: Option<i32>,
}

/// Request body for the `fork_agent_version` operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ForkAgentVersionRequest {
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub display_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
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

/// Request body for GitHub memory source.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GitHubMemorySourceRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub branch: Option<String>,
    pub repository: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub root_folder: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sync_interval_secs: Option<i32>,
}

impl GitHubMemorySourceRequest {
    pub fn new(repository: impl Into<String>) -> Self {
        Self {
            branch: None,
            repository: repository.into(),
            root_folder: None,
            sync_interval_secs: None,
        }
    }

    pub fn branch(mut self, branch: impl Into<String>) -> Self {
        self.branch = Some(branch.into());
        self
    }

    pub fn root_folder(mut self, root_folder: impl Into<String>) -> Self {
        self.root_folder = Some(root_folder.into());
        self
    }

    pub fn sync_interval_secs(mut self, sync_interval_secs: i32) -> Self {
        self.sync_interval_secs = Some(sync_interval_secs);
        self
    }
}

/// Request body for git memory source.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GitMemorySourceRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub branch: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub root_folder: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub sync_interval_secs: Option<i32>,
    pub url: String,
}

impl GitMemorySourceRequest {
    pub fn new(url: impl Into<String>) -> Self {
        Self {
            branch: None,
            root_folder: None,
            sync_interval_secs: None,
            url: url.into(),
        }
    }

    pub fn branch(mut self, branch: impl Into<String>) -> Self {
        self.branch = Some(branch.into());
        self
    }

    pub fn root_folder(mut self, root_folder: impl Into<String>) -> Self {
        self.root_folder = Some(root_folder.into());
        self
    }

    pub fn sync_interval_secs(mut self, sync_interval_secs: i32) -> Self {
        self.sync_interval_secs = Some(sync_interval_secs);
        self
    }
}

/// Grep match result
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GrepMatch {
    pub line: String,
    pub line_number: u64,
    pub path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GrepRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub path_pattern: Option<String>,
    pub pattern: String,
}

impl GrepRequest {
    pub fn new(pattern: impl Into<String>) -> Self {
        Self {
            path_pattern: None,
            pattern: pattern.into(),
        }
    }

    pub fn path_pattern(mut self, path_pattern: impl Into<String>) -> Self {
        self.path_pattern = Some(path_pattern.into());
        self
    }
}

/// Grep result for a file
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GrepResult {
    pub matches: Vec<GrepMatch>,
    pub path: String,
}

/// Effective action of a hit after applying the config mode.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum GuardrailAction {
    #[serde(rename = "block")]
    Block,
    #[serde(rename = "log")]
    Log,
}

/// A read-only, adoptable guardrails preset from the gallery. Adopt by
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GuardrailExample {
    pub check_types: Vec<String>,
    pub config: serde_json::Value,
    pub data_egress: String,
    pub description: String,
    pub display_name: String,
    pub name: String,
    pub stages: Vec<String>,
    pub tags: Vec<String>,
}

/// Response for the `list_guardrail_examples` operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GuardrailExamplesResponse {
    pub examples: Vec<GuardrailExample>,
}

/// Pipeline stage a check applies to.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum GuardrailStage {
    #[serde(rename = "output")]
    Output,
    #[serde(rename = "tool_use")]
    ToolUse,
    #[serde(rename = "tool_output")]
    ToolOutput,
}

/// One triggered check from a guardrails dry run.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GuardrailsDryRunHit {
    pub action: String,
    pub check_id: String,
    pub check_index: i32,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub matched: Option<String>,
    pub reason_code: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub replacement: Option<String>,
    pub rule_type: String,
    pub stage: String,
}

/// Request body for the `dry_run_guardrails` operation: evaluate a
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GuardrailsDryRunRequest {
    pub config: serde_json::Value,
    pub stage: String,
    pub text: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
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

/// Response for the `dry_run_guardrails` operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct GuardrailsDryRunResponse {
    pub blocked: bool,
    pub hits: Vec<GuardrailsDryRunHit>,
}

/// Outcome of a single case after the agent ran and was scored.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct HealthCheckCaseResult {
    pub deterministic_reason: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub input_tokens: Option<i32>,
    pub judge_reason: String,
    pub latency_ms: i64,
    pub name: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub output_tokens: Option<i32>,
    pub passed: bool,
    pub rubric: String,
    pub score: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub session_id: Option<String>,
    pub turns: i32,
    pub user_message: String,
}

/// API view of a health check run.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct HealthCheckRun {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub completed_at: Option<String>,
    pub config_hash: String,
    pub created_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub error_message: Option<String>,
    pub id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub model_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub results: Option<Vec<HealthCheckCaseResult>>,
    pub status: HealthCheckStatus,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub summary: Option<HealthCheckSummary>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum HealthCheckStatus {
    #[serde(rename = "pending")]
    Pending,
    #[serde(rename = "running")]
    Running,
    #[serde(rename = "completed")]
    Completed,
    #[serde(rename = "failed")]
    Failed,
}

/// Aggregate metrics across all cases in a run.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct HealthCheckSummary {
    pub avg_score: f64,
    pub avg_turns: f64,
    pub errored: i32,
    pub failed: i32,
    pub pass_rate: f64,
    pub passed: i32,
    pub total: i32,
    pub total_input_tokens: i64,
    pub total_output_tokens: i64,
}

/// Starter file copied into a new session from an agent or harness.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct InitialFile {
    pub content: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub is_readonly: Option<bool>,
    pub path: String,
}

impl InitialFile {
    pub fn new(path: impl Into<String>, content: impl Into<String>) -> Self {
        Self {
            content: content.into(),
            encoding: None,
            is_readonly: None,
            path: path.into(),
        }
    }

    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }

    pub fn is_readonly(mut self, is_readonly: bool) -> Self {
        self.is_readonly = Some(is_readonly);
        self
    }
}

/// Immutable ledger entry recording resource consumption or credit against a budget.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct LedgerEntry {
    pub amount: f64,
    pub budget_id: String,
    pub created_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub id: String,
    pub meter_source: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ref_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub ref_type: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub session_id: Option<String>,
}

/// Response body for memory.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Memory {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub archived_at: Option<String>,
    pub created_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub deleted_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub id: String,
    pub is_readonly: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_sync_error: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_synced_at: Option<String>,
    pub name: String,
    pub source: serde_json::Value,
    pub source_type: String,
    pub status: String,
    pub sync_status: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct MemoryFile {
    pub content: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content_hash: Option<String>,
    pub created_at: String,
    pub encoding: String,
    pub path: String,
    pub size_bytes: i64,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct MemoryFileInfo {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content_hash: Option<String>,
    pub created_at: String,
    pub is_directory: bool,
    pub path: String,
    pub size_bytes: i64,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct MemoryGrepResult {
    pub path: String,
    pub size_bytes: i64,
}

/// A message in the conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Message {
    pub content: Vec<ContentPart>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub controls: Option<Controls>,
    pub created_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub external_actor: Option<ExternalActor>,
    pub id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub phase: Option<String>,
    pub role: MessageRole,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub thinking: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub thinking_signature: Option<String>,
}

/// Message role in the conversation
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum MessageRole {
    #[serde(rename = "system")]
    System,
    #[serde(rename = "user")]
    User,
    #[serde(rename = "agent")]
    Agent,
    #[serde(rename = "tool_result")]
    ToolResult,
}

/// Request to move/rename a file
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct MoveFileRequest {
    pub dst_path: String,
    pub src_path: String,
}

impl MoveFileRequest {
    pub fn new(src_path: impl Into<String>, dst_path: impl Into<String>) -> Self {
        Self {
            dst_path: dst_path.into(),
            src_path: src_path.into(),
        }
    }
}

/// Response body for resource stats.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ResourceStats {
    pub active_session_count: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub avg_session_duration_ms: Option<i64>,
    pub execution_count: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub first_session_at: Option<String>,
    pub idle_session_count: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_execution_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub last_session_at: Option<String>,
    pub session_count: i64,
    pub started_session_count: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub total_actual_cost_usd: Option<f64>,
    pub total_cache_creation_tokens: i64,
    pub total_cache_read_tokens: i64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub total_cost_usd: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub total_estimated_cost_usd: Option<f64>,
    pub total_input_tokens: i64,
    pub total_output_tokens: i64,
    pub total_session_duration_ms: i64,
    pub waiting_for_tool_results_session_count: i64,
}

/// Result of resuming budgets paused for a session.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ResumeSessionResponse {
    pub resumed_budgets: u64,
    pub session_id: String,
}

/// Request body for the `rollback_agent_version` operation.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct RollbackAgentVersionRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub save_version: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub summary: Option<String>,
}

impl RollbackAgentVersionRequest {
    pub fn new() -> Self {
        Self {
            save_version: None,
            summary: None,
        }
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

/// Session - instance of agentic loop execution.
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Session {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub active_schedule_count: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_identity_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub agent_version_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub blueprint_config: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub blueprint_id: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub capabilities: Vec<AgentCapabilityConfig>,
    pub created_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub effective_owner: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub features: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub finished_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub forked_from_sequence: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub forked_from_session_id: Option<String>,
    pub harness_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hints: Option<std::collections::HashMap<String, serde_json::Value>>,
    pub id: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub initial_files: Vec<InitialFile>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub is_pinned: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub locale: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_iterations: Option<u64>,
    #[serde(rename = "mcpServers")]
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mcp_servers: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub model_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub network_access: Option<serde_json::Value>,
    pub organization_id: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub output_preview: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub owner: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub owner_principal_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parallel_tool_calls: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub parent_session_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub preview: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub resolved_owner_user_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub started_at: Option<String>,
    pub status: SessionStatus,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub system_prompt: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub title: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tools: Vec<ToolDefinition>,
    pub updated_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub usage: Option<TokenUsage>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub workspace_id: Option<String>,
}

/// Complete file with content
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct SessionFile {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    pub created_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
    pub id: String,
    pub is_directory: bool,
    pub is_readonly: bool,
    pub name: String,
    pub path: String,
    pub session_id: String,
    pub size_bytes: i64,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum SessionStatus {
    #[serde(rename = "started")]
    Started,
    #[serde(rename = "active")]
    Active,
    #[serde(rename = "idle")]
    Idle,
    #[serde(rename = "waitingfortoolresults")]
    WaitingForToolResults,
}

/// Request body for the `set_default_agent_version` operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
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

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct StatRequest {
    pub path: String,
}

impl StatRequest {
    pub fn new(path: impl Into<String>) -> Self {
        Self { path: path.into() }
    }
}

/// Request to submit client-side tool results
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct SubmitToolResultsRequest {
    pub tool_results: Vec<ClientToolResult>,
}

impl SubmitToolResultsRequest {
    pub fn new(tool_results: Vec<ClientToolResult>) -> Self {
        Self { tool_results }
    }
}

/// Response from submitting tool results
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct SubmitToolResultsResponse {
    pub accepted: u64,
    pub status: String,
}

/// Token usage statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct TokenUsage {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub actual_cost_usd: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub cache_creation_tokens: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub cache_read_tokens: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub effective_cost_usd: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub estimated_cost_usd: Option<f64>,
    pub input_tokens: i32,
    pub output_tokens: i32,
}

/// Tool definition in agent configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum ToolDefinition {
    #[serde(rename = "builtin")]
    Builtin(BuiltinTool),
    #[serde(rename = "client_side")]
    ClientSide(ClientSideTool),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct TopUpRequest {
    pub amount: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
}

impl TopUpRequest {
    pub fn new(amount: f64) -> Self {
        Self {
            amount,
            description: None,
        }
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }
}

/// Request body for changing a spending budget.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct UpdateBudgetRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub limit: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub metadata: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub soft_limit: Option<Option<f64>>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
}

impl UpdateBudgetRequest {
    pub fn new() -> Self {
        Self {
            limit: None,
            metadata: None,
            soft_limit: None,
            status: None,
        }
    }

    pub fn limit(mut self, limit: f64) -> Self {
        self.limit = Some(limit);
        self
    }

    pub fn metadata(mut self, metadata: serde_json::Value) -> Self {
        self.metadata = Some(metadata);
        self
    }

    pub fn soft_limit(mut self, soft_limit: Option<f64>) -> Self {
        self.soft_limit = Some(soft_limit);
        self
    }

    pub fn status(mut self, status: impl Into<String>) -> Self {
        self.status = Some(status.into());
        self
    }
}

/// Request to update a file
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct UpdateFileRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub is_readonly: Option<bool>,
}

impl UpdateFileRequest {
    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }

    pub fn is_readonly(mut self, is_readonly: bool) -> Self {
        self.is_readonly = Some(is_readonly);
        self
    }

    pub fn content(content: impl Into<String>) -> Self {
        Self {
            content: Some(content.into()),
            encoding: None,
            is_readonly: None,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct UpdateMemoryFileRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub encoding: Option<String>,
}

impl UpdateMemoryFileRequest {
    pub fn encoding(mut self, encoding: impl Into<String>) -> Self {
        self.encoding = Some(encoding.into());
        self
    }

    pub fn content(content: impl Into<String>) -> Self {
        Self {
            content: Some(content.into()),
            encoding: None,
        }
    }
}

/// Request body for the `update_memory` operation.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct UpdateMemoryRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source: Option<serde_json::Value>,
}

impl UpdateMemoryRequest {
    pub fn new() -> Self {
        Self {
            description: None,
            name: None,
            source: None,
        }
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }

    pub fn name(mut self, name: impl Into<String>) -> Self {
        self.name = Some(name.into());
        self
    }

    pub fn source(mut self, source: serde_json::Value) -> Self {
        self.source = Some(source);
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct UpdateWorkspaceRequest {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
}

impl UpdateWorkspaceRequest {
    pub fn new() -> Self {
        Self {
            description: None,
            name: None,
            status: None,
        }
    }

    pub fn description(mut self, description: impl Into<String>) -> Self {
        self.description = Some(description.into());
        self
    }

    pub fn name(mut self, name: impl Into<String>) -> Self {
        self.name = Some(name.into());
        self
    }

    pub fn status(mut self, status: impl Into<String>) -> Self {
        self.status = Some(status.into());
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct Workspace {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub archived_at: Option<String>,
    pub created_at: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub deleted_at: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    pub id: String,
    pub name: String,
    pub status: String,
    pub updated_at: String,
}

/// Request to preview the final agent shape with capabilities applied
#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct AnalyzeAgentRequest {
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub capabilities: Vec<AgentCapabilityConfig>,
    #[serde(rename = "mcpServers")]
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub mcp_servers: Option<serde_json::Value>,
    pub system_prompt: String,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tools: Vec<serde_json::Value>,
}

impl AnalyzeAgentRequest {
    pub fn new(system_prompt: impl Into<String>) -> Self {
        Self {
            capabilities: Vec::new(),
            mcp_servers: None,
            system_prompt: system_prompt.into(),
            tools: Vec::new(),
        }
    }

    pub fn capabilities(mut self, capabilities: Vec<AgentCapabilityConfig>) -> Self {
        self.capabilities = capabilities;
        self
    }

    pub fn mcp_servers(mut self, mcp_servers: serde_json::Value) -> Self {
        self.mcp_servers = Some(mcp_servers);
        self
    }

    pub fn tools(mut self, tools: Vec<serde_json::Value>) -> Self {
        self.tools = tools;
        self
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct ListEventsOptions {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub since_id: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub types: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub exclude: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub limit: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub before_sequence: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub after_sequence: Option<i64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub around: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub window: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub from_ts: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub to_ts: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub turn_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub exec_id: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub trace_id: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub tags: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub tool_name: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub q: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub order_desc: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct MessageInput {
    pub role: MessageRole,
    pub content: Vec<ContentPart>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
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

#[derive(Debug, Clone, Serialize, Deserialize)]
#[non_exhaustive]
pub struct SetSecretsRequest {
    pub secrets: std::collections::HashMap<String, String>,
}

impl SetSecretsRequest {
    pub fn new(secrets: std::collections::HashMap<String, String>) -> Self {
        Self { secrets }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
#[non_exhaustive]
pub struct StreamOptions {
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub since_id: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub types: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub exclude: Vec<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub max_retries: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub idle_timeout_ms: Option<i32>,
}

#[derive(Debug, Clone)]
pub struct ToolCallInfo<'a> {
    pub id: &'a str,
    pub name: &'a str,
    pub arguments: &'a serde_json::Value,
}

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

pub type DeleteResponse = DeleteFileResponse;

impl ContentPart {
    pub fn text(text: impl Into<String>) -> Self {
        Self::Text { text: text.into() }
    }

    pub fn tool_result(tool_call_id: impl Into<String>, result: serde_json::Value) -> Self {
        Self::ToolResult {
            tool_call_id: tool_call_id.into(),
            result: Some(result),
            error: None,
        }
    }

    pub fn tool_error(tool_call_id: impl Into<String>, error: impl Into<String>) -> Self {
        Self::ToolResult {
            tool_call_id: tool_call_id.into(),
            result: None,
            error: Some(error.into()),
        }
    }

    pub fn is_tool_call(&self) -> bool {
        matches!(self, Self::ToolCall { .. })
    }

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

impl MessageInput {
    pub fn new(role: MessageRole, content: Vec<ContentPart>) -> Self {
        Self { role, content }
    }

    pub fn user_text(text: impl Into<String>) -> Self {
        Self::new(MessageRole::User, vec![ContentPart::text(text)])
    }

    pub fn tool_results(results: Vec<ContentPart>) -> Self {
        Self::new(MessageRole::ToolResult, results)
    }
}

impl CreateMessageRequest {
    pub fn user_text(text: impl Into<String>) -> Self {
        Self::new(MessageInput::user_text(text))
    }
}

impl Event {
    pub fn tool_calls(&self) -> Vec<ToolCallInfo<'_>> {
        extract_tool_calls(&self.data)
    }
}

pub fn extract_tool_calls(data: &serde_json::Value) -> Vec<ToolCallInfo<'_>> {
    let requested = data
        .get("tool_calls")
        .and_then(|value| value.as_array())
        .or_else(|| data.get("message")?.get("content")?.as_array());
    requested
        .into_iter()
        .flatten()
        .filter_map(|part| {
            if part
                .get("type")
                .and_then(|value| value.as_str())
                .is_some_and(|kind| kind != "tool_call")
            {
                return None;
            }
            Some(ToolCallInfo {
                id: part.get("id")?.as_str()?,
                name: part.get("name")?.as_str()?,
                arguments: part.get("arguments").unwrap_or(&serde_json::Value::Null),
            })
        })
        .collect()
}

pub fn generate_agent_id() -> String {
    generate_id("agent")
}
pub fn generate_harness_id() -> String {
    generate_id("harness")
}

fn generate_id(prefix: &str) -> String {
    let mut bytes = [0u8; 16];
    getrandom::fill(&mut bytes).expect("failed to generate random bytes");
    let hex: String = bytes.iter().map(|byte| format!("{byte:02x}")).collect();
    format!("{prefix}_{hex}")
}

pub fn validate_harness_name(name: &str) -> crate::error::Result<()> {
    validate_addressable_name(name, "harness_name")
}
pub fn validate_agent_name(name: &str) -> crate::error::Result<()> {
    validate_addressable_name(name, "agent_name")
}

fn validate_addressable_name(name: &str, label: &str) -> crate::error::Result<()> {
    if name.len() > 64 {
        return Err(crate::error::Error::Validation(format!(
            "{label} must be at most 64 characters, got {}",
            name.len()
        )));
    }
    let valid = !name.is_empty()
        && name.split('-').all(|part| {
            !part.is_empty()
                && part
                    .chars()
                    .all(|ch| ch.is_ascii_lowercase() || ch.is_ascii_digit())
        });
    if !valid {
        return Err(crate::error::Error::Validation(format!(
            "{label} must match pattern [a-z0-9]+(-[a-z0-9]+)*, got {name:?}"
        )));
    }
    Ok(())
}
