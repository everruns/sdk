"""Everruns SDK for Python

A typed client for the Everruns API.

Quick Start:
    >>> from everruns_sdk import Everruns
    >>> client = Everruns()  # uses EVERRUNS_API_KEY
    >>> agent = await client.agents.create("assistant", "You are helpful.")
"""

from everruns_sdk.auth import ApiKey
from everruns_sdk.client import Everruns
from everruns_sdk.errors import (
    ApiError,
    AuthenticationError,
    EverrunsError,
    NotFoundError,
    RateLimitError,
)
from everruns_sdk.models import (
    Agent,
    AgentCapabilityConfig,
    Budget,
    BudgetCheckResult,
    BudgetPeriod,
    CapabilityInfo,
    Connection,
    ContentPart,
    Controls,
    DeleteFileResponse,
    Event,
    ExternalActor,
    FileInfo,
    FileStat,
    GrepMatch,
    GrepResult,
    InitialFile,
    LedgerEntry,
    Message,
    ResumeSessionResponse,
    Session,
    SessionFile,
    ToolCallInfo,
    TopUpRequest,
    extract_tool_calls,
    generate_agent_id,
    generate_harness_id,
    validate_agent_name,
    validate_harness_name,
)

__all__ = [
    "Everruns",
    "ApiKey",
    "EverrunsError",
    "ApiError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "Agent",
    "AgentCapabilityConfig",
    "Budget",
    "BudgetCheckResult",
    "BudgetPeriod",
    "CapabilityInfo",
    "Connection",
    "DeleteFileResponse",
    "FileInfo",
    "FileStat",
    "GrepMatch",
    "GrepResult",
    "LedgerEntry",
    "ResumeSessionResponse",
    "Session",
    "SessionFile",
    "Message",
    "Event",
    "ExternalActor",
    "InitialFile",
    "ContentPart",
    "Controls",
    "ToolCallInfo",
    "TopUpRequest",
    "extract_tool_calls",
    "generate_agent_id",
    "generate_harness_id",
    "validate_agent_name",
    "validate_harness_name",
]

__version__ = "0.1.0"
