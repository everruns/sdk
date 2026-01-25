"""Main client for Everruns API."""

from __future__ import annotations
import os
from typing import Any, AsyncIterator, Optional

import httpx

from everruns_sdk.auth import ApiKey
from everruns_sdk.errors import ApiError
from everruns_sdk.models import (
    Agent,
    CreateAgentRequest,
    Session,
    CreateSessionRequest,
    Message,
    CreateMessageRequest,
    MessageInput,
    ContentPart,
    Event,
    ListResponse,
    Controls,
)
from everruns_sdk.sse import EventStream, StreamOptions


DEFAULT_BASE_URL = "https://app.everruns.com/api"


class Everruns:
    """Main client for interacting with the Everruns API.
    
    Args:
        org: Organization ID
        api_key: API key (optional, defaults to EVERRUNS_API_KEY env var)
        base_url: Base URL for the API (optional)
        
    Example:
        >>> client = Everruns(org="my-org")
        >>> agent = await client.agents.create("Assistant", "You are helpful.")
    """
    
    def __init__(
        self,
        org: str,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
    ):
        if api_key is None:
            api_key = os.environ.get("EVERRUNS_API_KEY")
            if not api_key:
                raise ValueError(
                    "API key not provided. Set EVERRUNS_API_KEY environment variable "
                    "or pass api_key parameter."
                )
        
        self._api_key = ApiKey(api_key)
        self._org = org
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": self._api_key.value,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
    
    @property
    def agents(self) -> AgentsClient:
        """Get the agents client."""
        return AgentsClient(self)
    
    @property
    def sessions(self) -> SessionsClient:
        """Get the sessions client."""
        return SessionsClient(self)
    
    @property
    def messages(self) -> MessagesClient:
        """Get the messages client."""
        return MessagesClient(self)
    
    @property
    def events(self) -> EventsClient:
        """Get the events client."""
        return EventsClient(self)
    
    def _url(self, path: str) -> str:
        return f"/v1/orgs/{self._org}{path}"
    
    async def _get(self, path: str) -> Any:
        resp = await self._client.get(self._url(path))
        return await self._handle_response(resp)
    
    async def _post(self, path: str, data: Any) -> Any:
        resp = await self._client.post(self._url(path), json=data)
        return await self._handle_response(resp)
    
    async def _patch(self, path: str, data: Any) -> Any:
        resp = await self._client.patch(self._url(path), json=data)
        return await self._handle_response(resp)
    
    async def _delete(self, path: str) -> None:
        resp = await self._client.delete(self._url(path))
        if not resp.is_success:
            await self._raise_error(resp)
    
    async def _handle_response(self, resp: httpx.Response) -> Any:
        if resp.is_success:
            return resp.json()
        await self._raise_error(resp)
    
    async def _raise_error(self, resp: httpx.Response) -> None:
        try:
            body = resp.json()
        except Exception:
            body = {"error": {"code": "unknown", "message": resp.text}}
        raise ApiError.from_response(resp.status_code, body)
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self) -> "Everruns":
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.close()


class AgentsClient:
    """Client for agent operations."""
    
    def __init__(self, client: Everruns):
        self._client = client
    
    async def list(self) -> list[Agent]:
        """List all agents."""
        resp = await self._client._get("/agents")
        return [Agent(**a) for a in resp.get("data", [])]
    
    async def get(self, agent_id: str) -> Agent:
        """Get an agent by ID."""
        resp = await self._client._get(f"/agents/{agent_id}")
        return Agent(**resp)
    
    async def create(
        self,
        name: str,
        system_prompt: str,
        description: Optional[str] = None,
        default_model_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> Agent:
        """Create a new agent."""
        req = CreateAgentRequest(
            name=name,
            system_prompt=system_prompt,
            description=description,
            default_model_id=default_model_id,
            tags=tags or [],
        )
        resp = await self._client._post("/agents", req.model_dump(exclude_none=True))
        return Agent(**resp)
    
    async def delete(self, agent_id: str) -> None:
        """Delete (archive) an agent."""
        await self._client._delete(f"/agents/{agent_id}")


class SessionsClient:
    """Client for session operations."""
    
    def __init__(self, client: Everruns):
        self._client = client
    
    async def list(self, agent_id: Optional[str] = None) -> list[Session]:
        """List all sessions."""
        path = "/sessions"
        if agent_id:
            path += f"?agent_id={agent_id}"
        resp = await self._client._get(path)
        return [Session(**s) for s in resp.get("data", [])]
    
    async def get(self, session_id: str) -> Session:
        """Get a session by ID."""
        resp = await self._client._get(f"/sessions/{session_id}")
        return Session(**resp)
    
    async def create(
        self,
        agent_id: str,
        title: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> Session:
        """Create a new session."""
        req = CreateSessionRequest(
            agent_id=agent_id,
            title=title,
            model_id=model_id,
        )
        resp = await self._client._post("/sessions", req.model_dump(exclude_none=True))
        return Session(**resp)
    
    async def delete(self, session_id: str) -> None:
        """Delete a session."""
        await self._client._delete(f"/sessions/{session_id}")
    
    async def cancel(self, session_id: str) -> None:
        """Cancel the current turn in a session."""
        await self._client._post(f"/sessions/{session_id}/cancel", {})


class MessagesClient:
    """Client for message operations."""
    
    def __init__(self, client: Everruns):
        self._client = client
    
    async def list(self, session_id: str) -> list[Message]:
        """List messages in a session."""
        resp = await self._client._get(f"/sessions/{session_id}/messages")
        return [Message(**m) for m in resp.get("data", [])]
    
    async def create(
        self,
        session_id: str,
        text: str,
        controls: Optional[Controls] = None,
    ) -> Message:
        """Create a new message (send text)."""
        req = CreateMessageRequest(
            message=MessageInput(
                role="user",
                content=[ContentPart(type="text", text=text)],
            ),
            controls=controls,
        )
        resp = await self._client._post(
            f"/sessions/{session_id}/messages",
            req.model_dump(exclude_none=True),
        )
        return Message(**resp)


class EventsClient:
    """Client for event operations."""
    
    def __init__(self, client: Everruns):
        self._client = client
    
    async def list(self, session_id: str) -> list[Event]:
        """List events in a session."""
        resp = await self._client._get(f"/sessions/{session_id}/events")
        return [Event(**e) for e in resp.get("data", [])]
    
    def stream(
        self,
        session_id: str,
        exclude: Optional[list[str]] = None,
        since_id: Optional[str] = None,
    ) -> EventStream:
        """Stream events from a session via SSE."""
        options = StreamOptions(exclude=exclude or [], since_id=since_id)
        return EventStream(self._client, session_id, options)
