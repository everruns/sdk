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
    initial_files: list[InitialFile] = Field(default_factory=list)
    status: Literal["active", "archived"]
    created_at: str
    updated_at: str


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


# --- Session Filesystem Models ---


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
    """Extract tool call info from event data (``data.message.content``)."""
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
