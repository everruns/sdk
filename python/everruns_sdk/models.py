"""Data models for Everruns API."""

from __future__ import annotations

import re
import secrets
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


def generate_agent_id() -> str:
    """Generate a random agent ID in the format ``agent_<32-hex>``."""
    return f"agent_{secrets.token_hex(16)}"


def generate_harness_id() -> str:
    """Generate a random harness ID in the format ``harness_<32-hex>``."""
    return f"harness_{secrets.token_hex(16)}"


# Addressable name validation: lowercase alphanumeric segments separated by hyphens.
# Shared by harness names and agent names.
_ADDRESSABLE_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_ADDRESSABLE_NAME_MAX_LENGTH = 64


def _validate_addressable_name(name: str, *, label: str) -> str:
    """Validate an addressable name and return it if valid.

    Names must match ``[a-z0-9]+(-[a-z0-9]+)*`` and be at most 64 characters.

    Raises:
        ValueError: If the name is invalid.
    """
    if len(name) > _ADDRESSABLE_NAME_MAX_LENGTH:
        raise ValueError(
            f"{label} must be at most {_ADDRESSABLE_NAME_MAX_LENGTH} characters, got {len(name)}"
        )
    if not _ADDRESSABLE_NAME_PATTERN.match(name):
        raise ValueError(f"{label} must match pattern [a-z0-9]+(-[a-z0-9]+)*, got {name!r}")
    return name


def validate_harness_name(name: str) -> str:
    """Validate a harness name and return it if valid.

    Harness names must match ``[a-z0-9]+(-[a-z0-9]+)*`` and be at most 64 characters.

    Raises:
        ValueError: If the name is invalid.
    """
    return _validate_addressable_name(name, label="harness_name")


def validate_agent_name(name: str) -> str:
    """Validate an agent name and return it if valid.

    Agent names must match ``[a-z0-9]+(-[a-z0-9]+)*`` and be at most 64 characters.

    Raises:
        ValueError: If the name is invalid.
    """
    return _validate_addressable_name(name, label="agent_name")


class AgentCapabilityConfig(BaseModel):
    """Per-agent capability configuration."""

    ref: str = Field(description="Reference to the capability ID")
    config: Optional[dict[str, Any]] = None


class ToolDefinition(BaseModel):
    """Tool definition in agent/session configuration."""

    type: Literal["client_side", "builtin"] = "client_side"
    name: str
    description: str
    parameters: Any
    display_name: Optional[str] = None
    category: Optional[str] = None
    hints: Optional[dict[str, Any]] = None
    deferrable: Optional[dict[str, Any]] = None
    policy: Optional[Literal["auto", "requires_approval", "client_side"]] = None


class CapabilityInfo(BaseModel):
    """Public capability information."""

    id: str
    name: str
    description: str
    status: str
    category: Optional[str] = None
    dependencies: list[str] = Field(default_factory=list)
    icon: Optional[str] = None
    is_mcp: bool = False
    display_name: Optional[str] = None
    features: list[str] = Field(default_factory=list)
    is_skill: bool = False
    risk_level: Optional[str] = None


class Agent(BaseModel):
    """Agent configuration."""

    id: str
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: str
    default_model_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    capabilities: list[AgentCapabilityConfig] = Field(default_factory=list)
    tools: list[ToolDefinition] = Field(default_factory=list)
    initial_files: list[InitialFile] = Field(default_factory=list)
    status: Literal["active", "archived"]
    created_at: str
    updated_at: str


AgentVersionChangeKind = Literal["manual", "patch", "minor", "major", "import", "rollback", "fork"]


class AgentVersion(BaseModel):
    """Immutable snapshot of an agent configuration."""

    id: str
    agent_id: str
    version_number: int
    semver_major: int
    semver_minor: int
    semver_patch: int
    version: str
    change_kind: AgentVersionChangeKind
    config_hash: str
    authored_config: dict[str, Any]
    resolved_config: dict[str, Any]
    created_at: str
    created_by_principal_id: Optional[str] = None
    parent_version_id: Optional[str] = None
    source_version_id: Optional[str] = None
    summary: Optional[str] = None


class AgentVersionDiffResponse(BaseModel):
    """Diff between two saved agent versions."""

    from_version_id: str
    to_version_id: str
    authored_diff: Any
    resolved_diff: Any


class CreateAgentVersionRequest(BaseModel):
    """Request to save the current agent configuration as a version."""

    change_kind: Optional[AgentVersionChangeKind] = None
    summary: Optional[str] = None


class SetDefaultAgentVersionRequest(BaseModel):
    """Request to set the default version for an agent."""

    version_id: str


class ForkAgentVersionRequest(BaseModel):
    """Request to create a new agent from a saved version."""

    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None


class RollbackAgentVersionRequest(BaseModel):
    """Request to restore an agent from a saved version."""

    save_version: Optional[bool] = None
    summary: Optional[str] = None


class CreateAgentRequest(BaseModel):
    """Request to create an agent."""

    id: Optional[str] = Field(
        default=None,
        description="Client-supplied agent ID (format: agent_{32-hex}). Auto-generated if omitted.",
    )
    name: str = Field(
        description=(
            "Addressable name, unique per org. Format: [a-z0-9]+(-[a-z0-9]+)*, max 64 chars."
        ),
    )
    display_name: Optional[str] = Field(
        default=None,
        description="Human-readable display name shown in UI. Falls back to name when absent.",
    )
    system_prompt: str
    description: Optional[str] = None
    default_model_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    capabilities: list[AgentCapabilityConfig] = Field(default_factory=list)
    tools: list[ToolDefinition] = Field(default_factory=list)
    initial_files: list[InitialFile] = Field(default_factory=list)


class Session(BaseModel):
    """Session representing an active conversation."""

    id: str
    organization_id: str
    harness_id: str
    agent_id: Optional[str] = None
    title: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    locale: Optional[str] = None
    model_id: Optional[str] = None
    capabilities: list[AgentCapabilityConfig] = Field(default_factory=list)
    tools: list[ToolDefinition] = Field(default_factory=list)
    status: Literal["started", "active", "idle", "waitingfortoolresults"]
    created_at: str
    updated_at: str
    usage: Optional[TokenUsage] = None
    active_schedule_count: Optional[int] = None
    features: list[str] = Field(default_factory=list)
    is_pinned: Optional[bool] = None


class TokenUsage(BaseModel):
    """Token usage statistics."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0


class ResourceStats(BaseModel):
    """Aggregate usage statistics for an agent or harness."""

    session_count: int
    active_session_count: int
    idle_session_count: int
    started_session_count: int
    waiting_for_tool_results_session_count: int
    execution_count: int
    total_session_duration_ms: int
    avg_session_duration_ms: Optional[int] = None
    total_input_tokens: int
    total_output_tokens: int
    total_cache_read_tokens: int
    total_cache_creation_tokens: int
    first_session_at: Optional[str] = None
    last_session_at: Optional[str] = None
    last_execution_at: Optional[str] = None


class InitialFile(BaseModel):
    """Starter file copied into a new session workspace."""

    path: str
    content: str
    encoding: Optional[Literal["text", "base64"]] = None
    is_readonly: Optional[bool] = None


class CreateSessionRequest(BaseModel):
    """Request to create a session."""

    harness_id: Optional[str] = None
    harness_name: Optional[str] = None
    agent_id: Optional[str] = None
    title: Optional[str] = None
    locale: Optional[str] = None
    model_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    capabilities: list[AgentCapabilityConfig] = Field(default_factory=list)
    tools: list[ToolDefinition] = Field(default_factory=list)
    initial_files: Optional[list[InitialFile]] = None


class ExternalActor(BaseModel):
    """External actor identity for messages from external channels (Slack, Discord, etc.)."""

    actor_id: str
    source: str
    actor_name: Optional[str] = None
    metadata: Optional[dict[str, str]] = None


class Message(BaseModel):
    """Message in a session."""

    id: str
    session_id: str
    sequence: int
    role: Literal["user", "agent", "tool_result"]
    content: list[ContentPart]
    thinking: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    created_at: str
    external_actor: Optional[ExternalActor] = None
    phase: Optional[Literal["Commentary", "FinalAnswer"]] = None


class ContentPart(BaseModel):
    """Content part within a message."""

    type: Literal["text", "image", "image_file", "tool_call", "tool_result"]
    text: Optional[str] = None
    url: Optional[str] = None
    base64: Optional[str] = None
    image_id: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    arguments: Optional[dict[str, Any]] = None
    tool_call_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None

    @staticmethod
    def make_text(text: str) -> "ContentPart":
        """Create a text content part."""
        return ContentPart(type="text", text=text)

    @staticmethod
    def make_tool_result(tool_call_id: str, result: Any) -> "ContentPart":
        """Create a tool result content part with a successful result."""
        return ContentPart(type="tool_result", tool_call_id=tool_call_id, result=result)

    @staticmethod
    def make_tool_error(tool_call_id: str, error: str) -> "ContentPart":
        """Create a tool result content part with an error."""
        return ContentPart(type="tool_result", tool_call_id=tool_call_id, error=error)

    def is_tool_call(self) -> bool:
        """Returns True if this is a tool call content part."""
        return self.type == "tool_call"

    def as_tool_call(self) -> Optional["ToolCallInfo"]:
        """Extract tool call info if this is a tool call content part."""
        if self.type != "tool_call" or self.id is None or self.name is None:
            return None
        return ToolCallInfo(id=self.id, name=self.name, arguments=self.arguments or {})


class ClientToolResult(BaseModel):
    """A single tool result from the client."""

    tool_call_id: str
    result: Optional[Any] = None
    error: Optional[str] = None


class SubmitToolResultsRequest(BaseModel):
    """Request to submit client-side tool results."""

    tool_results: list[ClientToolResult]


class SubmitToolResultsResponse(BaseModel):
    """Response from submitting tool results."""

    accepted: int
    status: str


class ToolCallInfo(BaseModel):
    """Extracted tool call information."""

    id: str
    name: str
    arguments: dict[str, Any]


class CreateMessageRequest(BaseModel):
    """Request to create a message."""

    message: MessageInput
    controls: Optional[Controls] = None
    external_actor: Optional[ExternalActor] = None


class MessageInput(BaseModel):
    """Input for creating a message."""

    role: Literal["user", "agent", "tool_result"]
    content: list[ContentPart]

    @staticmethod
    def tool_results(results: list[ContentPart]) -> "MessageInput":
        """Create a tool result message containing one or more tool results."""
        return MessageInput(role="tool_result", content=results)


class Controls(BaseModel):
    """Controls for message generation."""

    model_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


class Event(BaseModel):
    """SSE Event from the server."""

    id: str
    type: str = Field(alias="type")
    ts: str
    session_id: str
    data: dict[str, Any]
    context: EventContext = Field(default_factory=lambda: EventContext())

    model_config = ConfigDict(populate_by_name=True)

    def tool_calls(self) -> list[ToolCallInfo]:
        """Extract tool calls from an ``output.message.completed`` event's data."""
        return extract_tool_calls(self.data)


class EventContext(BaseModel):
    """Event context for correlation."""

    turn_id: Optional[str] = None
    input_message_id: Optional[str] = None


class ListResponse(BaseModel):
    """Paginated list response."""

    data: list[Any]
    total: int = 0
    offset: int = 0
    limit: int = 0


# --- Workspace Models ---


class Workspace(BaseModel):
    """Workspace resource."""

    id: str
    name: str
    status: str
    created_at: str
    updated_at: str
    description: Optional[str] = None
    archived_at: Optional[str] = None
    deleted_at: Optional[str] = None


class CreateWorkspaceRequest(BaseModel):
    """Request to create a workspace."""

    name: str
    description: Optional[str] = None


class UpdateWorkspaceRequest(BaseModel):
    """Request to update a workspace."""

    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


# --- Workspace Filesystem Models ---


class FileInfo(BaseModel):
    """File metadata without content."""

    id: str
    session_id: str
    path: str
    name: str
    is_directory: bool
    is_readonly: bool
    size_bytes: int
    created_at: str
    updated_at: str


class SessionFile(BaseModel):
    """Complete file with content."""

    id: str
    session_id: str
    path: str
    name: str
    is_directory: bool
    is_readonly: bool
    size_bytes: int
    created_at: str
    updated_at: str
    content: Optional[str] = None
    encoding: Optional[str] = None


class FileStat(BaseModel):
    """File stat information."""

    path: str
    name: str
    is_directory: bool
    is_readonly: bool
    size_bytes: int
    created_at: str
    updated_at: str


class GrepMatch(BaseModel):
    """Single grep match."""

    path: str
    line_number: int
    line: str


class GrepResult(BaseModel):
    """Grep result for a file."""

    path: str
    matches: list[GrepMatch]


class DeleteFileResponse(BaseModel):
    """Response for delete operation."""

    deleted: bool


# --- Memory Models ---


class Memory(BaseModel):
    """Workspace memory resource."""

    id: str
    name: str
    source_type: str
    source: dict[str, Any]
    is_readonly: bool
    sync_status: str
    status: str
    created_at: str
    updated_at: str
    description: Optional[str] = None
    last_sync_error: Optional[str] = None
    last_synced_at: Optional[str] = None
    archived_at: Optional[str] = None
    deleted_at: Optional[str] = None


class CreateMemoryRequest(BaseModel):
    """Request to create a workspace memory."""

    name: str
    description: Optional[str] = None
    source: Optional[dict[str, Any]] = None


class UpdateMemoryRequest(BaseModel):
    """Request to update a workspace memory."""

    name: Optional[str] = None
    description: Optional[str] = None
    source: Optional[dict[str, Any]] = None


class MemoryFileInfo(BaseModel):
    """Memory file metadata."""

    path: str
    is_directory: bool
    size_bytes: int
    created_at: str
    updated_at: str
    content_hash: Optional[str] = None


class MemoryFile(BaseModel):
    """Memory file content."""

    path: str
    content: str
    encoding: str
    size_bytes: int
    created_at: str
    updated_at: str
    content_hash: Optional[str] = None


class CreateMemoryFileRequest(BaseModel):
    """Request to create a memory file or directory."""

    content: Optional[str] = None
    encoding: Optional[str] = None
    is_directory: Optional[bool] = None


class UpdateMemoryFileRequest(BaseModel):
    """Request to update a memory file."""

    content: Optional[str] = None
    encoding: Optional[str] = None


class MemoryGrepResult(BaseModel):
    """Memory grep result entry."""

    path: str
    size_bytes: int


# --- Agent Analysis and Guardrail Models ---


class AnalyzeAgentRequest(BaseModel):
    """Request to run advisory checks against an agent shape."""

    system_prompt: str
    capabilities: list[AgentCapabilityConfig] = []
    tools: list[dict[str, Any]] = []
    mcp_servers: Optional[dict[str, Any]] = Field(default=None, alias="mcpServers")


class FindingLocation(BaseModel):
    """Finding location in authored config."""

    field: str
    start: Optional[int] = None
    end: Optional[int] = None


class Finding(BaseModel):
    """Advisory agent finding."""

    rule_id: str
    severity: str
    category: str
    source: str
    message: str
    location: Optional[FindingLocation] = None
    fix: Optional[str] = None


class AgentAnalysisResponse(BaseModel):
    """Response from agent analysis."""

    findings: list[Finding]


class GuardrailsDryRunRequest(BaseModel):
    """Request to evaluate guardrails against sample text."""

    config: dict[str, Any]
    stage: Literal["output", "tool_use", "tool_output"]
    text: str
    tool_name: Optional[str] = None


class GuardrailsDryRunHit(BaseModel):
    """One triggered guardrail check."""

    check_index: int
    check_id: str
    stage: str
    rule_type: str
    action: Literal["block", "log"]
    reason_code: str
    matched: Optional[str] = None
    replacement: Optional[str] = None


class GuardrailsDryRunResponse(BaseModel):
    """Guardrail dry-run response."""

    hits: list[GuardrailsDryRunHit]
    blocked: bool


class GuardrailExample(BaseModel):
    """Adoptable guardrail preset."""

    name: str
    display_name: str
    description: str
    tags: list[str]
    check_types: list[str]
    stages: list[str]
    data_egress: str
    config: dict[str, Any]


class GuardrailExamplesResponse(BaseModel):
    """Guardrail preset list response."""

    examples: list[GuardrailExample]


# --- Budget Models ---


class BudgetPeriod(BaseModel):
    """Budget period configuration for recurring budgets."""

    type: Literal["rolling", "calendar"]
    window: Optional[str] = None
    unit: Optional[str] = None


class Budget(BaseModel):
    """Budget — a spending cap for a subject in a currency."""

    id: str
    organization_id: str
    subject_type: str
    subject_id: str
    currency: str
    limit: float
    soft_limit: Optional[float] = None
    balance: float
    period: Optional[BudgetPeriod] = None
    metadata: Optional[dict[str, Any]] = None
    status: Literal["active", "paused", "exhausted", "disabled"]
    created_at: str
    updated_at: str


class CreateBudgetRequest(BaseModel):
    """Request to create a budget."""

    subject_type: str
    subject_id: str
    currency: str
    limit: float
    soft_limit: Optional[float] = None
    period: Optional[BudgetPeriod] = None
    metadata: Optional[dict[str, Any]] = None


class UpdateBudgetRequest(BaseModel):
    """Request to update a budget."""

    limit: Optional[float] = None
    soft_limit: Optional[Optional[float]] = None
    status: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class TopUpRequest(BaseModel):
    """Request to top up a budget."""

    amount: float
    description: Optional[str] = None


class LedgerEntry(BaseModel):
    """Ledger entry recording resource consumption or credit."""

    id: str
    budget_id: str
    amount: float
    meter_source: str
    ref_type: Optional[str] = None
    ref_id: Optional[str] = None
    session_id: Optional[str] = None
    description: Optional[str] = None
    created_at: str


class BudgetCheckResult(BaseModel):
    """Result of checking all budgets for a session."""

    action: str
    message: Optional[str] = None
    budget_id: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None


class ResumeSessionResponse(BaseModel):
    """Response from session resume endpoint."""

    resumed_budgets: int
    session_id: str


# --- Connections Models ---


class Connection(BaseModel):
    """A user connection to an external provider."""

    provider: str
    created_at: str
    updated_at: str


def extract_tool_calls(data: dict[str, Any]) -> list[ToolCallInfo]:
    """Extract tool call info from ``tool.call_requested`` or message event data."""
    requested = data.get("tool_calls")
    if isinstance(requested, list):
        results: list[ToolCallInfo] = []
        for call in requested:
            if not isinstance(call, dict):
                continue
            call_id = call.get("id")
            call_name = call.get("name")
            if call_id and call_name:
                results.append(
                    ToolCallInfo(id=call_id, name=call_name, arguments=call.get("arguments", {}))
                )
        return results

    message = data.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    results: list[ToolCallInfo] = []
    for part in content:
        if not isinstance(part, dict):
            continue
        if part.get("type") != "tool_call":
            continue
        call_id = part.get("id")
        call_name = part.get("name")
        if call_id and call_name:
            results.append(
                ToolCallInfo(id=call_id, name=call_name, arguments=part.get("arguments", {}))
            )
    return results
