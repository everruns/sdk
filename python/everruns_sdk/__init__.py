"""Everruns SDK for Python

A typed client for the Everruns API.

Quick Start:
    >>> from everruns_sdk import Everruns
    >>> client = Everruns()  # uses EVERRUNS_API_KEY
    >>> agent = await client.agents.create("Assistant", "You are helpful.")
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
    ContentPart,
    Controls,
    Event,
    Message,
    Session,
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
    "Session",
    "Message",
    "Event",
    "ContentPart",
    "Controls",
]

__version__ = "0.1.0"
