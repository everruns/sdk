"""Data models for Everruns API."""

from __future__ import annotations

import secrets
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


def generate_agent_id() -> str:
    """Generate a random agent ID in the format ``agent_<32-hex>``."""
    return f"agent_{secrets.token_hex(16)}"


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


class Agent(BaseModel):
    """Agent configuration."""

    id: str
    name: str
    description: Optional[str] = None
    system_prompt: str
    default_model_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    capabilities: list[AgentCapabilityConfig] = Field(default_factory=list)
    status: Literal["active", "archived"]
    created_at: str
    updated_at: str


class CreateAgentRequest(BaseModel):
    """Request to create an agent."""

    id: Optional[str] = Field(
        default=None,
        description="Client-supplied agent ID (format: agent_{32-hex}). Auto-generated if omitted.",
    )
    name: str
    system_prompt: str
    description: Optional[str] = None
    default_model_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    capabilities: list[AgentCapabilityConfig] = Field(default_factory=list)


class Session(BaseModel):
    """Session representing an active conversation."""

    id: str
    organization_id: str
    agent_id: str
    title: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    model_id: Optional[str] = None
    capabilities: list[AgentCapabilityConfig] = Field(default_factory=list)
    status: Literal["started", "active", "idle"]
    created_at: str
    updated_at: str
    usage: Optional[TokenUsage] = None


class TokenUsage(BaseModel):
    """Token usage statistics."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0


class CreateSessionRequest(BaseModel):
    """Request to create a session."""

    agent_id: str
    title: Optional[str] = None
    model_id: Optional[str] = None
    capabilities: list[AgentCapabilityConfig] = Field(default_factory=list)


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
    total: int
    offset: int
    limit: int


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
