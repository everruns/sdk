"""Public data models generated from the Everruns OpenAPI document."""

from __future__ import annotations

import re
import secrets
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Regenerate with `just generate`. Do not edit by hand.


class Agent(BaseModel):
    """Agent configuration for agentic loop."""

    archived_at: Optional[str] = None
    capabilities: Optional[list[AgentCapabilityConfig]] = Field(default_factory=list)
    created_at: str
    default_model_id: Optional[str] = None
    default_version_id: Optional[str] = None
    deleted_at: Optional[str] = None
    description: Optional[str] = None
    display_name: Optional[str] = None
    forked_from_agent_id: Optional[str] = None
    forked_from_version_id: Optional[str] = None
    harness_id: str
    id: str
    initial_files: Optional[list[InitialFile]] = Field(default_factory=list)
    max_iterations: Optional[int] = None
    mcp_servers: Optional[Any] = Field(default=None, alias="mcpServers")
    name: str
    network_access: Optional[NetworkAccessList] = None
    parallel_tool_calls: Optional[bool] = None
    root_agent_id: Optional[str] = None
    status: AgentStatus
    system_prompt: str
    tags: Optional[list[str]] = Field(default_factory=list)
    tools: Optional[list[ToolDefinition]] = Field(default_factory=list)
    updated_at: str
    usage: Optional[TokenUsage] = None

    model_config = ConfigDict(populate_by_name=True)


class AgentAnalysisResponse(BaseModel):
    """Response from on-demand agent analysis (built-in rules + LLM checkers)"""

    findings: list[Finding]

    model_config = ConfigDict(populate_by_name=True)


class AgentCapabilityConfig(BaseModel):
    """Per-agent capability configuration"""

    config: Optional[Any] = None
    ref: str

    model_config = ConfigDict(populate_by_name=True)


AgentStatus = Literal["active", "archived", "deleted"]


class AgentVersion(BaseModel):
    """Immutable snapshot of an Agent's authored and resolved runtime config."""

    agent_id: str
    authored_config: dict[str, Any]
    change_kind: AgentVersionChangeKind
    config_hash: str
    created_at: str
    created_by_principal_id: Optional[str] = None
    id: str
    is_published: Optional[bool] = None
    parent_version_id: Optional[str] = None
    resolved_config: dict[str, Any]
    semver_major: int
    semver_minor: int
    semver_patch: int
    source_version_id: Optional[str] = None
    summary: Optional[str] = None
    version: str
    version_number: int

    model_config = ConfigDict(populate_by_name=True)


AgentVersionChangeKind = Literal[
    "auto", "manual", "patch", "minor", "major", "import", "rollback", "fork"
]


class AgentVersionDiffResponse(BaseModel):
    """Response body for agent version diff."""

    authored_diff: Any
    from_version_id: Any
    resolved_diff: Any
    to_version_id: Any

    model_config = ConfigDict(populate_by_name=True)


class Budget(BaseModel):
    """Budget — a spending cap for a subject in a currency."""

    balance: float
    created_at: str
    currency: str
    id: str
    limit: float
    metadata: Optional[Any] = None
    organization_id: str
    period: Optional[BudgetPeriod] = None
    period_started_at: Optional[str] = None
    soft_limit: Optional[float] = None
    status: BudgetStatus
    subject_id: str
    subject_type: Any
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class BudgetCheckResult(BaseModel):
    """Result of checking all budgets for a session."""

    action: str
    balance: Optional[float] = None
    budget_id: Optional[str] = None
    currency: Optional[str] = None
    error_code: Optional[str] = None
    error_fields: Optional[dict[str, Any]] = None
    message: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class BudgetPeriod(BaseModel):
    """Budget period configuration for recurring budgets."""

    seconds: Optional[int] = None
    type: Literal["duration", "rolling", "calendar"]
    window: Optional[str] = None
    unit: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


BudgetStatus = Literal["active", "paused", "exhausted", "disabled"]


class BuiltinTool(BaseModel):
    """Built-in tool configuration"""

    category: Optional[str] = None
    deferrable: Optional[Any] = None
    description: str
    display_name: Optional[str] = None
    full_parameters: Optional[Any] = None
    hints: Optional[Any] = None
    name: str
    parameters: Any
    policy: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class CapabilityInfo(BaseModel):
    """Public capability information (without internal details)"""

    agent_count: Optional[int] = None
    category: Optional[str] = None
    config_schema: Optional[dict[str, Any]] = None
    config_ui_schema: Optional[dict[str, Any]] = None
    dependencies: Optional[list[str]] = Field(default_factory=list)
    description: str
    docs_slug: Optional[str] = None
    features: Optional[list[str]] = Field(default_factory=list)
    harness_count: Optional[int] = None
    icon: Optional[str] = None
    id: str
    is_guardrail: Optional[bool] = None
    is_mcp: bool = False
    is_skill: bool = False
    localizations: Optional[dict[str, Any]] = None
    name: str
    risk_level: Optional[Any] = None
    status: str
    system_prompt: Optional[str] = None
    tool_definitions: Optional[list[dict[str, Any]]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class ClientSideTool(BaseModel):
    """Client-side tool - executed by the client, not the server"""

    category: Optional[str] = None
    deferrable: Optional[Any] = None
    description: str
    display_name: Optional[str] = None
    full_parameters: Optional[Any] = None
    hints: Optional[Any] = None
    name: str
    parameters: Any

    model_config = ConfigDict(populate_by_name=True)


class ClientToolResult(BaseModel):
    """A single tool result from the client"""

    error: Optional[str] = None
    result: Optional[Any] = None
    tool_call_id: str

    model_config = ConfigDict(populate_by_name=True)


class Connection(BaseModel):
    provider: str
    created_at: str
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class ContentPart(BaseModel):
    """A part of message content - can be text, image, image_file, tool_call, or tool_result"""

    text: Optional[str] = None
    type: Literal["text", "image", "image_file", "tool_call", "tool_result"]
    base64: Optional[str] = None
    media_type: Optional[str] = None
    url: Optional[str] = None
    filename: Optional[str] = None
    image_id: Optional[str] = None
    arguments: Optional[Any] = None
    id: Optional[str] = None
    name: Optional[str] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    tool_call_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)

    @staticmethod
    def make_text(text: str) -> "ContentPart":
        return ContentPart(type="text", text=text)

    @staticmethod
    def make_tool_result(tool_call_id: str, result: Any) -> "ContentPart":
        return ContentPart(type="tool_result", tool_call_id=tool_call_id, result=result)

    @staticmethod
    def make_tool_error(tool_call_id: str, error: str) -> "ContentPart":
        return ContentPart(type="tool_result", tool_call_id=tool_call_id, error=error)

    def is_tool_call(self) -> bool:
        return self.type == "tool_call"

    def as_tool_call(self) -> Optional["ToolCallInfo"]:
        if not self.is_tool_call() or not self.id or not self.name:
            return None
        return ToolCallInfo(id=self.id, name=self.name, arguments=self.arguments or {})


class Controls(BaseModel):
    """Runtime controls for message processing"""

    error_disclosure: Optional[str] = None
    hints: Optional[dict[str, Any]] = None
    locale: Optional[str] = None
    model_id: Optional[str] = None
    reasoning: Optional[Any] = None

    model_config = ConfigDict(populate_by_name=True)


class CopyFileRequest(BaseModel):
    """Request to copy a file"""

    dst_path: str
    src_path: str

    model_config = ConfigDict(populate_by_name=True)


class CostTier(BaseModel):
    """A pricing tier that activates above a context token threshold."""

    above_tokens: int
    cache_read: Optional[float] = None
    input: float
    output: float

    model_config = ConfigDict(populate_by_name=True)


class CreateAgentRequest(BaseModel):
    """Request to create a new agent"""

    capabilities: Optional[list[AgentCapabilityConfig]] = Field(default_factory=list)
    default_model_id: Optional[str] = None
    description: Optional[str] = None
    display_name: Optional[str] = None
    harness_id: Optional[str] = None
    harness_name: Optional[str] = None
    id: Optional[str] = None
    initial_files: Optional[list[InitialFile]] = Field(default_factory=list)
    max_iterations: Optional[int] = None
    mcp_servers: Optional[Any] = Field(default=None, alias="mcpServers")
    name: str
    network_access: Optional[NetworkAccessList] = None
    parallel_tool_calls: Optional[bool] = None
    system_prompt: str
    tags: Optional[list[str]] = Field(default_factory=list)
    tools: Optional[list[ToolDefinition]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class CreateAgentVersionRequest(BaseModel):
    """Request body for the `create_agent_version` operation."""

    change_kind: Optional[AgentVersionChangeKind] = None
    summary: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class CreateBudgetRequest(BaseModel):
    """Request body for creating a spending budget."""

    currency: str
    limit: float
    metadata: Optional[Any] = None
    period: Optional[BudgetPeriod] = None
    soft_limit: Optional[float] = None
    subject_id: str
    subject_type: str

    model_config = ConfigDict(populate_by_name=True)


class CreateFileRequest(BaseModel):
    """Request to create a file"""

    content: Optional[str] = None
    encoding: Optional[str] = None
    is_directory: Optional[bool] = None
    is_readonly: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class CreateHarnessRequest(BaseModel):
    """Request to create a new harness"""

    capabilities: Optional[list[AgentCapabilityConfig]] = Field(default_factory=list)
    default_model_id: Optional[str] = None
    description: Optional[str] = None
    display_name: Optional[str] = None
    embedder_metadata: Optional[dict[str, str]] = None
    initial_files: Optional[list[InitialFile]] = Field(default_factory=list)
    mcp_servers: Optional[Any] = Field(default=None, alias="mcpServers")
    name: str
    network_access: Optional[NetworkAccessList] = None
    parent_harness_id: Optional[str] = None
    system_prompt: Optional[str] = None
    tags: Optional[list[str]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class CreateMemoryFileRequest(BaseModel):
    content: Optional[str] = None
    encoding: Optional[str] = None
    is_directory: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class CreateMemoryRequest(BaseModel):
    """Request body for the `create_memory` operation."""

    description: Optional[str] = None
    name: str
    source: Optional[CreateMemorySourceRequest] = None

    model_config = ConfigDict(populate_by_name=True)


class CreateMessageRequest(BaseModel):
    """Request to create a message"""

    addressed_participant_id: Optional[str] = None
    controls: Optional[Controls] = None
    external_actor: Optional[ExternalActor] = None
    message: MessageInput
    metadata: Optional[dict[str, Any]] = None
    tags: Optional[list[str]] = None

    model_config = ConfigDict(populate_by_name=True)


class CreateSessionRequest(BaseModel):
    """Request to create a session"""

    agent_id: Optional[str] = None
    agent_identity_id: Optional[str] = None
    agent_name: Optional[str] = None
    capabilities: Optional[list[AgentCapabilityConfig]] = Field(default_factory=list)
    harness_id: Optional[str] = None
    harness_name: Optional[str] = None
    hints: Optional[dict[str, Any]] = None
    initial_files: Optional[list[InitialFile]] = Field(default_factory=list)
    locale: Optional[str] = None
    max_iterations: Optional[int] = None
    mcp_servers: Optional[Any] = Field(default=None, alias="mcpServers")
    model_id: Optional[str] = None
    network_access: Optional[NetworkAccessList] = None
    parallel_tool_calls: Optional[bool] = None
    system_prompt: Optional[str] = None
    tags: Optional[list[str]] = Field(default_factory=list)
    title: Optional[str] = None
    tools: Optional[list[ToolDefinition]] = Field(default_factory=list)
    workspace_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class CreateWorkspaceRequest(BaseModel):
    description: Optional[str] = None
    name: str

    model_config = ConfigDict(populate_by_name=True)


class DeleteFileResponse(BaseModel):
    """Response for delete operation"""

    deleted: bool

    model_config = ConfigDict(populate_by_name=True)


class Event(BaseModel):
    """Standard event following the Everruns event protocol."""

    context: EventContext = Field(default_factory=lambda: EventContext())
    data: Any
    id: str
    metadata: Optional[Any] = None
    sequence: Optional[int] = None
    session_id: str
    tags: Optional[list[str]] = None
    ts: str
    type: str

    model_config = ConfigDict(populate_by_name=True)

    def tool_calls(self) -> list[ToolCallInfo]:
        return extract_tool_calls(self.data)


class EventContext(BaseModel):
    """Context for event correlation and tracing"""

    exec_id: Optional[str] = None
    input_message_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    span_id: Optional[str] = None
    trace_id: Optional[str] = None
    turn_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ExternalActor(BaseModel):
    """External actor identity for messages originating from external channels"""

    actor_id: str
    actor_name: Optional[str] = None
    metadata: Optional[dict[str, str]] = None
    source: str

    model_config = ConfigDict(populate_by_name=True)


class FileInfo(BaseModel):
    """File metadata without content"""

    created_at: str
    id: str
    is_directory: bool
    is_readonly: bool
    name: str
    path: str
    session_id: str
    size_bytes: int
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class FileStat(BaseModel):
    """File stat information"""

    created_at: str
    is_directory: bool
    is_readonly: bool
    name: str
    path: str
    size_bytes: int
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class Finding(BaseModel):
    """A single advisory finding about an agent configuration."""

    category: Any
    fix: Optional[str] = None
    location: Optional[FindingLocation] = None
    message: str
    rule_id: str
    severity: Any
    source: Any

    model_config = ConfigDict(populate_by_name=True)


class FindingLocation(BaseModel):
    """Pointer to the config field (and optional byte span within it) a finding"""

    end: Optional[int] = None
    field: str
    start: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)


class ForkAgentVersionRequest(BaseModel):
    """Request body for the `fork_agent_version` operation."""

    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class GitHubMemorySourceRequest(BaseModel):
    """Request body for GitHub memory source."""

    branch: Optional[str] = None
    repository: str
    root_folder: Optional[str] = None
    sync_interval_secs: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)


class GitMemorySourceRequest(BaseModel):
    """Request body for git memory source."""

    branch: Optional[str] = None
    root_folder: Optional[str] = None
    sync_interval_secs: Optional[int] = None
    url: str

    model_config = ConfigDict(populate_by_name=True)


class GrepMatch(BaseModel):
    """Grep match result"""

    line: str
    line_number: int
    path: str

    model_config = ConfigDict(populate_by_name=True)


class GrepRequest(BaseModel):
    path_pattern: Optional[str] = None
    pattern: str

    model_config = ConfigDict(populate_by_name=True)


class GrepResult(BaseModel):
    """Grep result for a file"""

    matches: list[GrepMatch]
    path: str

    model_config = ConfigDict(populate_by_name=True)


GuardrailAction = Literal["block", "log"]


class GuardrailExample(BaseModel):
    """A read-only, adoptable guardrails preset from the gallery. Adopt by"""

    check_types: list[str]
    config: dict[str, Any]
    data_egress: str
    description: str
    display_name: str
    name: str
    stages: list[str]
    tags: list[str]

    model_config = ConfigDict(populate_by_name=True)


class GuardrailExamplesResponse(BaseModel):
    """Response for the `list_guardrail_examples` operation."""

    examples: list[GuardrailExample]

    model_config = ConfigDict(populate_by_name=True)


GuardrailStage = Literal["output", "tool_use", "tool_output"]


class GuardrailsDryRunHit(BaseModel):
    """One triggered check from a guardrails dry run."""

    action: GuardrailAction
    check_id: str
    check_index: int
    matched: Optional[str] = None
    reason_code: str
    replacement: Optional[str] = None
    rule_type: str
    stage: GuardrailStage

    model_config = ConfigDict(populate_by_name=True)


class GuardrailsDryRunRequest(BaseModel):
    """Request body for the `dry_run_guardrails` operation: evaluate a"""

    config: dict[str, Any]
    stage: GuardrailStage
    text: str
    tool_name: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class GuardrailsDryRunResponse(BaseModel):
    """Response for the `dry_run_guardrails` operation."""

    blocked: bool
    hits: list[GuardrailsDryRunHit]

    model_config = ConfigDict(populate_by_name=True)


class Harness(BaseModel):
    """Harness configuration for sessions."""

    archived_at: Optional[str] = None
    capabilities: Optional[list[AgentCapabilityConfig]] = Field(default_factory=list)
    created_at: str
    default_model_id: Optional[str] = None
    deleted_at: Optional[str] = None
    description: Optional[str] = None
    display_name: Optional[str] = None
    embedder_metadata: Optional[dict[str, str]] = None
    id: str
    initial_files: Optional[list[InitialFile]] = Field(default_factory=list)
    is_built_in: Optional[bool] = None
    mcp_servers: Optional[Any] = Field(default=None, alias="mcpServers")
    name: str
    network_access: Optional[NetworkAccessList] = None
    parallel_tool_calls: Optional[bool] = None
    parent_harness_id: Optional[str] = None
    status: HarnessStatus
    system_prompt: Optional[str] = None
    tags: Optional[list[str]] = Field(default_factory=list)
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class HarnessExample(BaseModel):
    """A read-only harness example defined in code."""

    capabilities: list[AgentCapabilityConfig]
    description: str
    dev_only: bool
    display_name: str
    name: str
    parent_name: Optional[str] = None
    tags: list[str]

    model_config = ConfigDict(populate_by_name=True)


HarnessStatus = Literal["active", "archived", "deleted"]


class HealthCheckCaseResult(BaseModel):
    """Outcome of a single case after the agent ran and was scored."""

    deterministic_reason: str
    error: Optional[str] = None
    input_tokens: Optional[int] = None
    judge_reason: str
    latency_ms: int
    name: str
    output_tokens: Optional[int] = None
    passed: bool
    rubric: str
    score: float
    session_id: Optional[str] = None
    turns: int
    user_message: str

    model_config = ConfigDict(populate_by_name=True)


class HealthCheckRun(BaseModel):
    """API view of a health check run."""

    agent_id: Optional[str] = None
    completed_at: Optional[str] = None
    config_hash: str
    created_at: str
    error_message: Optional[str] = None
    id: str
    model_id: Optional[str] = None
    results: Optional[list[HealthCheckCaseResult]] = None
    status: HealthCheckStatus
    summary: Optional[HealthCheckSummary] = None

    model_config = ConfigDict(populate_by_name=True)


HealthCheckStatus = Literal["pending", "running", "completed", "failed"]


class HealthCheckSummary(BaseModel):
    """Aggregate metrics across all cases in a run."""

    avg_score: float
    avg_turns: float
    errored: int
    failed: int
    pass_rate: float
    passed: int
    total: int
    total_input_tokens: int
    total_output_tokens: int

    model_config = ConfigDict(populate_by_name=True)


class InitialFile(BaseModel):
    """Starter file copied into a new session from an agent or harness."""

    content: str
    encoding: Optional[str] = None
    is_readonly: Optional[bool] = None
    path: str

    model_config = ConfigDict(populate_by_name=True)


class LedgerEntry(BaseModel):
    """Immutable ledger entry recording resource consumption or credit against a budget."""

    amount: float
    budget_id: str
    created_at: str
    description: Optional[str] = None
    id: str
    meter_source: str
    ref_id: Optional[str] = None
    ref_type: Optional[str] = None
    session_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class Memory(BaseModel):
    """Response body for memory."""

    archived_at: Optional[str] = None
    created_at: str
    deleted_at: Optional[str] = None
    description: Optional[str] = None
    id: str
    is_readonly: bool
    last_sync_error: Optional[str] = None
    last_synced_at: Optional[str] = None
    name: str
    source: Any
    source_type: str
    status: str
    sync_status: str
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class MemoryFile(BaseModel):
    content: str
    content_hash: Optional[str] = None
    created_at: str
    encoding: str
    path: str
    size_bytes: int
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class MemoryFileInfo(BaseModel):
    content_hash: Optional[str] = None
    created_at: str
    is_directory: bool
    path: str
    size_bytes: int
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class MemoryGrepResult(BaseModel):
    path: str
    size_bytes: int

    model_config = ConfigDict(populate_by_name=True)


class Message(BaseModel):
    """A message in the conversation"""

    content: list[ContentPart]
    controls: Optional[Controls] = None
    created_at: str
    external_actor: Optional[ExternalActor] = None
    id: str
    metadata: Optional[dict[str, Any]] = None
    phase: Optional[Any] = None
    role: MessageRole
    thinking: Optional[str] = None
    thinking_signature: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


MessageRole = Literal["system", "user", "agent", "tool_result"]

Modality = Literal["text", "image", "audio", "video", "pdf"]


class ModelCost(BaseModel):
    """Cost information for the model (per million tokens)"""

    cache_read: Optional[float] = None
    cost_tiers: Optional[list[CostTier]] = Field(default_factory=list)
    input: float
    output: float

    model_config = ConfigDict(populate_by_name=True)


class ModelLimits(BaseModel):
    """Token limits for the model"""

    context: int
    input: Optional[int] = None
    max_media: Optional[int] = None
    output: int

    model_config = ConfigDict(populate_by_name=True)


class ModelModalities(BaseModel):
    """Model modalities for input and output"""

    input: list[Modality]
    output: list[Modality]

    model_config = ConfigDict(populate_by_name=True)


class ModelProfile(BaseModel):
    """LLM Model Profile describing model capabilities"""

    attachment: bool
    cost: Optional[ModelCost] = None
    description: Optional[str] = None
    family: str
    knowledge: Optional[str] = None
    last_updated: Optional[str] = None
    limits: Optional[ModelLimits] = None
    modalities: Optional[ModelModalities] = None
    name: str
    open_weights: bool
    reasoning: bool
    reasoning_effort: Optional[ReasoningEffortConfig] = None
    release_date: Optional[str] = None
    structured_output: bool
    supported_parameters: Optional[list[str]] = Field(default_factory=list)
    supports_phases: Optional[bool] = None
    temperature: bool
    tool_call: bool
    tool_search: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


ModelSource = Literal["manual", "discovered", "predefined"]

ModelVendor = Literal[
    "openai",
    "anthropic",
    "google",
    "nvidia",
    "qwen",
    "microsoft",
    "minimax",
    "moonshot",
    "xai",
    "llmsim",
]


class ModelWithProvider(BaseModel):
    """LLM Model with provider info"""

    capabilities: list[str]
    created_at: str
    display_name: str
    enabled: bool
    healthy: bool
    id: str
    is_favorite: bool
    model_id: str
    model_vendor: Optional[ModelVendor] = None
    profile: Optional[ModelProfile] = None
    provider_id: str
    provider_name: str
    provider_type: DriverId
    source: ModelSource
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class MoveFileRequest(BaseModel):
    """Request to move/rename a file"""

    dst_path: str
    src_path: str

    model_config = ConfigDict(populate_by_name=True)


class NetworkAccessList(BaseModel):
    """Network access list controlling which hosts/URLs an agent session can reach."""

    allowed: Optional[list[str]] = Field(default_factory=list)
    blocked: Optional[list[str]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


ReasoningEffort = Literal["none", "minimal", "low", "medium", "high", "xhigh"]


class ReasoningEffortConfig(BaseModel):
    """Reasoning effort configuration for a model"""

    default: ReasoningEffort
    values: list[ReasoningEffortValue]

    model_config = ConfigDict(populate_by_name=True)


class ReasoningEffortValue(BaseModel):
    """Named reasoning effort value for UI display"""

    name: str
    value: ReasoningEffort

    model_config = ConfigDict(populate_by_name=True)


class ResourceStats(BaseModel):
    """Response body for resource stats."""

    active_session_count: int
    avg_session_duration_ms: Optional[int] = None
    execution_count: int
    first_session_at: Optional[str] = None
    idle_session_count: int
    last_execution_at: Optional[str] = None
    last_session_at: Optional[str] = None
    session_count: int
    started_session_count: int
    total_actual_cost_usd: Optional[float] = None
    total_cache_creation_tokens: int
    total_cache_read_tokens: int
    total_cost_usd: Optional[float] = None
    total_estimated_cost_usd: Optional[float] = None
    total_input_tokens: int
    total_output_tokens: int
    total_session_duration_ms: int
    waiting_for_tool_results_session_count: int

    model_config = ConfigDict(populate_by_name=True)


class ResumeSessionResponse(BaseModel):
    """Result of resuming budgets paused for a session."""

    resumed_budgets: int
    session_id: str

    model_config = ConfigDict(populate_by_name=True)


class RollbackAgentVersionRequest(BaseModel):
    """Request body for the `rollback_agent_version` operation."""

    save_version: Optional[bool] = None
    summary: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class Session(BaseModel):
    """Session - instance of agentic loop execution."""

    active_schedule_count: Optional[int] = None
    agent_id: Optional[str] = None
    agent_identity_id: Optional[str] = None
    agent_version_id: Optional[str] = None
    blueprint_config: Optional[dict[str, Any]] = None
    blueprint_id: Optional[str] = None
    capabilities: Optional[list[AgentCapabilityConfig]] = Field(default_factory=list)
    created_at: str
    effective_owner: Optional[Any] = None
    features: Optional[list[str]] = Field(default_factory=list)
    finished_at: Optional[str] = None
    forked_from_sequence: Optional[int] = None
    forked_from_session_id: Optional[str] = None
    harness_id: str
    hints: Optional[dict[str, Any]] = None
    id: str
    initial_files: Optional[list[InitialFile]] = Field(default_factory=list)
    is_pinned: Optional[bool] = None
    locale: Optional[str] = None
    max_iterations: Optional[int] = None
    mcp_servers: Optional[Any] = Field(default=None, alias="mcpServers")
    model_id: Optional[str] = None
    network_access: Optional[NetworkAccessList] = None
    organization_id: str
    output_preview: Optional[str] = None
    owner: Optional[Any] = None
    owner_principal_id: Optional[str] = None
    parallel_tool_calls: Optional[bool] = None
    parent_session_id: Optional[str] = None
    preview: Optional[str] = None
    resolved_owner_user_id: Optional[str] = None
    started_at: Optional[str] = None
    status: SessionStatus
    system_prompt: Optional[str] = None
    tags: Optional[list[str]] = Field(default_factory=list)
    title: Optional[str] = None
    tools: Optional[list[ToolDefinition]] = Field(default_factory=list)
    updated_at: str
    usage: Optional[TokenUsage] = None
    workspace_id: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class SessionFile(BaseModel):
    """Complete file with content"""

    content: Optional[str] = None
    created_at: str
    encoding: Optional[str] = None
    id: str
    is_directory: bool
    is_readonly: bool
    name: str
    path: str
    session_id: str
    size_bytes: int
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


SessionStatus = Literal["started", "active", "idle", "waitingfortoolresults"]


class SetDefaultAgentVersionRequest(BaseModel):
    """Request body for the `set_default_agent_version` operation."""

    version_id: str

    model_config = ConfigDict(populate_by_name=True)


class StatRequest(BaseModel):
    path: str

    model_config = ConfigDict(populate_by_name=True)


class SubmitToolResultsRequest(BaseModel):
    """Request to submit client-side tool results"""

    tool_results: list[ClientToolResult]

    model_config = ConfigDict(populate_by_name=True)


class SubmitToolResultsResponse(BaseModel):
    """Response from submitting tool results"""

    accepted: int
    status: str

    model_config = ConfigDict(populate_by_name=True)


class TokenUsage(BaseModel):
    """Token usage statistics"""

    actual_cost_usd: Optional[float] = None
    cache_creation_tokens: Optional[int] = None
    cache_read_tokens: Optional[int] = None
    effective_cost_usd: Optional[float] = None
    estimated_cost_usd: Optional[float] = None
    input_tokens: int
    output_tokens: int

    model_config = ConfigDict(populate_by_name=True)


class ToolDefinition(BaseModel):
    """Tool definition in agent configuration"""

    category: Optional[str] = None
    deferrable: Optional[Any] = None
    description: str
    display_name: Optional[str] = None
    full_parameters: Optional[Any] = None
    hints: Optional[Any] = None
    name: str
    parameters: Any
    policy: Optional[Any] = None
    type: Literal["builtin", "client_side"] = "client_side"

    model_config = ConfigDict(populate_by_name=True)


class TopUpRequest(BaseModel):
    amount: float
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class UpdateBudgetRequest(BaseModel):
    """Request body for changing a spending budget."""

    limit: Optional[float] = None
    metadata: Optional[Any] = None
    soft_limit: Optional[float] = None
    status: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class UpdateFileRequest(BaseModel):
    """Request to update a file"""

    content: Optional[str] = None
    encoding: Optional[str] = None
    is_readonly: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class UpdateHarnessRequest(BaseModel):
    """Request to update a harness. Only provided fields will be updated."""

    capabilities: Optional[list[AgentCapabilityConfig]] = None
    default_model_id: Optional[str] = None
    description: Optional[str] = None
    display_name: Optional[str] = None
    embedder_metadata: Optional[dict[str, str]] = None
    initial_files: Optional[list[InitialFile]] = None
    mcp_servers: Optional[Any] = Field(default=None, alias="mcpServers")
    name: Optional[str] = None
    network_access: Optional[NetworkAccessList] = None
    parent_harness_id: Optional[str] = None
    status: Optional[HarnessStatus] = None
    system_prompt: Optional[str] = None
    tags: Optional[list[str]] = None

    model_config = ConfigDict(populate_by_name=True)


class UpdateMemoryFileRequest(BaseModel):
    content: Optional[str] = None
    encoding: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class UpdateMemoryRequest(BaseModel):
    """Request body for the `update_memory` operation."""

    description: Optional[str] = None
    name: Optional[str] = None
    source: Optional[CreateMemorySourceRequest] = None

    model_config = ConfigDict(populate_by_name=True)


class UpdateWorkspaceRequest(BaseModel):
    description: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class Workspace(BaseModel):
    archived_at: Optional[str] = None
    created_at: str
    deleted_at: Optional[str] = None
    description: Optional[str] = None
    id: str
    name: str
    status: str
    updated_at: str

    model_config = ConfigDict(populate_by_name=True)


class AnalyzeAgentRequest(BaseModel):
    """Request to preview the final agent shape with capabilities applied"""

    capabilities: Optional[list[AgentCapabilityConfig]] = Field(default_factory=list)
    mcp_servers: Optional[Any] = Field(default=None, alias="mcpServers")
    system_prompt: str
    tools: Optional[list[dict[str, Any]]] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class ListEventsOptions(BaseModel):
    since_id: Optional[str] = None
    types: Optional[list[str]] = Field(default_factory=list)
    exclude: Optional[list[str]] = Field(default_factory=list)
    limit: Optional[int] = None
    before_sequence: Optional[int] = None
    after_sequence: Optional[int] = None
    around: Optional[str] = None
    window: Optional[int] = None
    from_ts: Optional[str] = None
    to_ts: Optional[str] = None
    turn_id: Optional[str] = None
    exec_id: Optional[str] = None
    trace_id: Optional[str] = None
    tags: Optional[list[str]] = Field(default_factory=list)
    tool_name: Optional[str] = None
    q: Optional[str] = None
    order_desc: Optional[bool] = None

    model_config = ConfigDict(populate_by_name=True)


class MessageInput(BaseModel):
    role: Literal["user", "tool_result"]
    content: list[ContentPart]

    model_config = ConfigDict(populate_by_name=True)

    @staticmethod
    def tool_results(results: list[ContentPart]) -> "MessageInput":
        return MessageInput(role="tool_result", content=results)


class SetConnectionRequest(BaseModel):
    api_key: str

    model_config = ConfigDict(populate_by_name=True)


class SetSecretsRequest(BaseModel):
    secrets: dict[str, str]

    model_config = ConfigDict(populate_by_name=True)


class StreamOptions(BaseModel):
    since_id: Optional[str] = None
    types: Optional[list[str]] = Field(default_factory=list)
    exclude: Optional[list[str]] = Field(default_factory=list)
    max_retries: Optional[int] = None
    idle_timeout_ms: Optional[int] = None

    model_config = ConfigDict(populate_by_name=True)


class ToolCallInfo(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]

    model_config = ConfigDict(populate_by_name=True)


class ListResponse(BaseModel):
    data: list[Any]
    total: int = 0
    offset: int = 0
    limit: int = 0


CreateMemorySourceRequest = GitHubMemorySourceRequest | GitMemorySourceRequest

DriverId = str


def generate_agent_id() -> str:
    return f"agent_{secrets.token_hex(16)}"


def generate_harness_id() -> str:
    return f"harness_{secrets.token_hex(16)}"


_ADDRESSABLE_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_ADDRESSABLE_NAME_MAX_LENGTH = 64


def _validate_addressable_name(name: str, *, label: str) -> str:
    if len(name) > _ADDRESSABLE_NAME_MAX_LENGTH:
        raise ValueError(f"{label} must be at most 64 characters, got {len(name)}")
    if not _ADDRESSABLE_NAME_PATTERN.match(name):
        raise ValueError(f"{label} must match pattern [a-z0-9]+(-[a-z0-9]+)*, got {name!r}")
    return name


def validate_harness_name(name: str) -> str:
    return _validate_addressable_name(name, label="harness_name")


def validate_agent_name(name: str) -> str:
    return _validate_addressable_name(name, label="agent_name")


def extract_tool_calls(data: dict[str, Any]) -> list[ToolCallInfo]:
    requested = data.get("tool_calls")
    if not isinstance(requested, list):
        message = data.get("message")
        requested = message.get("content", []) if isinstance(message, dict) else []
    results: list[ToolCallInfo] = []
    for call in requested:
        if not isinstance(call, dict):
            continue
        if call.get("type") not in (None, "tool_call"):
            continue
        call_id, call_name = call.get("id"), call.get("name")
        if call_id and call_name:
            results.append(
                ToolCallInfo(id=call_id, name=call_name, arguments=call.get("arguments", {}))
            )
    return results


Agent.model_rebuild()
AgentAnalysisResponse.model_rebuild()
AgentCapabilityConfig.model_rebuild()
AgentVersion.model_rebuild()
AgentVersionDiffResponse.model_rebuild()
Budget.model_rebuild()
BudgetCheckResult.model_rebuild()
BudgetPeriod.model_rebuild()
BuiltinTool.model_rebuild()
CapabilityInfo.model_rebuild()
ClientSideTool.model_rebuild()
ClientToolResult.model_rebuild()
Connection.model_rebuild()
ContentPart.model_rebuild()
Controls.model_rebuild()
CopyFileRequest.model_rebuild()
CostTier.model_rebuild()
CreateAgentRequest.model_rebuild()
CreateAgentVersionRequest.model_rebuild()
CreateBudgetRequest.model_rebuild()
CreateFileRequest.model_rebuild()
CreateHarnessRequest.model_rebuild()
CreateMemoryFileRequest.model_rebuild()
CreateMemoryRequest.model_rebuild()
CreateMessageRequest.model_rebuild()
CreateSessionRequest.model_rebuild()
CreateWorkspaceRequest.model_rebuild()
DeleteFileResponse.model_rebuild()
Event.model_rebuild()
EventContext.model_rebuild()
ExternalActor.model_rebuild()
FileInfo.model_rebuild()
FileStat.model_rebuild()
Finding.model_rebuild()
FindingLocation.model_rebuild()
ForkAgentVersionRequest.model_rebuild()
GitHubMemorySourceRequest.model_rebuild()
GitMemorySourceRequest.model_rebuild()
GrepMatch.model_rebuild()
GrepRequest.model_rebuild()
GrepResult.model_rebuild()
GuardrailExample.model_rebuild()
GuardrailExamplesResponse.model_rebuild()
GuardrailsDryRunHit.model_rebuild()
GuardrailsDryRunRequest.model_rebuild()
GuardrailsDryRunResponse.model_rebuild()
Harness.model_rebuild()
HarnessExample.model_rebuild()
HealthCheckCaseResult.model_rebuild()
HealthCheckRun.model_rebuild()
HealthCheckSummary.model_rebuild()
InitialFile.model_rebuild()
LedgerEntry.model_rebuild()
Memory.model_rebuild()
MemoryFile.model_rebuild()
MemoryFileInfo.model_rebuild()
MemoryGrepResult.model_rebuild()
Message.model_rebuild()
ModelCost.model_rebuild()
ModelLimits.model_rebuild()
ModelModalities.model_rebuild()
ModelProfile.model_rebuild()
ModelWithProvider.model_rebuild()
MoveFileRequest.model_rebuild()
NetworkAccessList.model_rebuild()
ReasoningEffortConfig.model_rebuild()
ReasoningEffortValue.model_rebuild()
ResourceStats.model_rebuild()
ResumeSessionResponse.model_rebuild()
RollbackAgentVersionRequest.model_rebuild()
Session.model_rebuild()
SessionFile.model_rebuild()
SetDefaultAgentVersionRequest.model_rebuild()
StatRequest.model_rebuild()
SubmitToolResultsRequest.model_rebuild()
SubmitToolResultsResponse.model_rebuild()
TokenUsage.model_rebuild()
ToolDefinition.model_rebuild()
TopUpRequest.model_rebuild()
UpdateBudgetRequest.model_rebuild()
UpdateFileRequest.model_rebuild()
UpdateHarnessRequest.model_rebuild()
UpdateMemoryFileRequest.model_rebuild()
UpdateMemoryRequest.model_rebuild()
UpdateWorkspaceRequest.model_rebuild()
Workspace.model_rebuild()
AnalyzeAgentRequest.model_rebuild()
ListEventsOptions.model_rebuild()
MessageInput.model_rebuild()
SetConnectionRequest.model_rebuild()
SetSecretsRequest.model_rebuild()
StreamOptions.model_rebuild()
ToolCallInfo.model_rebuild()
ListResponse.model_rebuild()
