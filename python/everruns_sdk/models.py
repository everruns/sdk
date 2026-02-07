"""Data models for Everruns API."""

from __future__ import annotations

import secrets
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


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


class CreateMessageRequest(BaseModel):
    """Request to create a message."""

    message: MessageInput
    controls: Optional[Controls] = None


class MessageInput(BaseModel):
    """Input for creating a message."""

    role: Literal["user", "agent", "tool_result"]
    content: list[ContentPart]


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

    class Config:
        populate_by_name = True


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
