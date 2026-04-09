"""Main client for Everruns API."""

from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from everruns_sdk.auth import ApiKey
from everruns_sdk.errors import ApiError
from everruns_sdk.models import (
    Agent,
    AgentCapabilityConfig,
    Budget,
    BudgetCheckResult,
    CapabilityInfo,
    Connection,
    ContentPart,
    Controls,
    CreateAgentRequest,
    CreateMessageRequest,
    CreateSessionRequest,
    DeleteFileResponse,
    Event,
    FileInfo,
    FileStat,
    GrepResult,
    InitialFile,
    LedgerEntry,
    Message,
    MessageInput,
    ResumeSessionResponse,
    Session,
    SessionFile,
    validate_agent_name,
    validate_harness_name,
)
from everruns_sdk.sse import EventStream, StreamOptions

DEFAULT_BASE_URL = "https://custom.example.com/api"


def _is_html_response(body: str) -> bool:
    """Check if the body looks like an HTML response."""
    trimmed = body.lstrip()
    return trimmed.startswith("<!DOCTYPE") or trimmed.lower().startswith("<html")


class Everruns:
    """Main client for interacting with the Everruns API.

    Args:
        api_key: API key (optional, defaults to EVERRUNS_API_KEY env var)
        base_url: Base URL for the API (optional)

    Example:
        >>> client = Everruns()
        >>> agent = await client.agents.create("assistant", "You are helpful.")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize Everruns client.

        Args:
            api_key: API key (falls back to EVERRUNS_API_KEY env var)
            base_url: API base URL (falls back to EVERRUNS_API_URL env var,
                      then DEFAULT_BASE_URL)
        """
        if api_key is None:
            api_key = os.environ.get("EVERRUNS_API_KEY")
            if not api_key:
                raise ValueError(
                    "API key not provided. Set EVERRUNS_API_KEY environment variable "
                    "or pass api_key parameter."
                )
        if base_url is None:
            base_url = os.environ.get("EVERRUNS_API_URL", DEFAULT_BASE_URL)

        self._api_key = ApiKey(api_key)
        # Ensure base URL has trailing slash for correct URL joining.
        # httpx follows RFC 3986: without trailing slash, relative paths
        # replace the last path segment instead of appending.
        # Example: "http://host/api" + "v1/x" = "http://host/v1/x" (wrong)
        #          "http://host/api/" + "v1/x" = "http://host/api/v1/x" (correct)
        self._base_url = base_url.rstrip("/") + "/"
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

    @property
    def capabilities(self) -> CapabilitiesClient:
        """Get the capabilities client."""
        return CapabilitiesClient(self)

    @property
    def session_files(self) -> "SessionFilesClient":
        """Get the session files client."""
        return SessionFilesClient(self)

    @property
    def connections(self) -> "ConnectionsClient":
        """Get the connections client."""
        return ConnectionsClient(self)

    @property
    def budgets(self) -> "BudgetsClient":
        """Get the budgets client."""
        return BudgetsClient(self)

    def _url(self, path: str) -> str:
        # Use relative path (no leading slash) for correct joining with base URL.
        # The path parameter starts with "/" (e.g., "/agents"), so we strip it.
        path_without_slash = path.lstrip("/")
        return f"v1/{path_without_slash}"

    async def _get(self, path: str) -> Any:
        resp = await self._client.get(self._url(path))
        return await self._handle_response(resp)

    async def _get_text(self, path: str) -> str:
        resp = await self._client.get(self._url(path))
        if resp.is_success:
            return resp.text
        await self._raise_error(resp)
        return ""  # unreachable

    async def _post(self, path: str, data: Any) -> Any:
        resp = await self._client.post(self._url(path), json=data)
        return await self._handle_response(resp)

    async def _post_text(self, path: str, content: str) -> Any:
        resp = await self._client.post(
            self._url(path),
            content=content,
            headers={"Content-Type": "text/plain"},
        )
        return await self._handle_response(resp)

    async def _patch(self, path: str, data: Any) -> Any:
        resp = await self._client.patch(self._url(path), json=data)
        return await self._handle_response(resp)

    async def _put(self, path: str, data: Any) -> Any:
        resp = await self._client.put(self._url(path), json=data)
        return await self._handle_response(resp)

    async def _put_empty(self, path: str) -> None:
        resp = await self._client.put(self._url(path))
        if not resp.is_success:
            await self._raise_error(resp)

    async def _delete(self, path: str) -> None:
        resp = await self._client.delete(self._url(path))
        if not resp.is_success:
            await self._raise_error(resp)

    async def _delete_json(self, path: str) -> Any:
        resp = await self._client.delete(self._url(path))
        return await self._handle_response(resp)

    async def _handle_response(self, resp: httpx.Response) -> Any:
        if resp.is_success:
            return resp.json()
        await self._raise_error(resp)

    async def _raise_error(self, resp: httpx.Response) -> None:
        try:
            body = resp.json()
        except Exception:
            # Simplify HTML responses to avoid verbose error messages
            text = resp.text
            if _is_html_response(text):
                message = f"HTTP {resp.status_code}"
            else:
                message = text
            body = {"error": {"code": "unknown", "message": message}}
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

    async def list(self, *, search: Optional[str] = None) -> list[Agent]:
        """List all agents.

        Args:
            search: Case-insensitive name/description search.
        """
        path = "/agents"
        if search:
            path += f"?search={search}"
        resp = await self._client._get(path)
        return [Agent(**a) for a in resp.get("data", [])]

    async def get(self, agent_id: str) -> Agent:
        """Get an agent by ID."""
        resp = await self._client._get(f"/agents/{agent_id}")
        return Agent(**resp)

    async def create(
        self,
        name: str,
        system_prompt: str,
        *,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        default_model_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        capabilities: Optional[list[AgentCapabilityConfig]] = None,
        initial_files: Optional[list[InitialFile]] = None,
    ) -> Agent:
        """Create a new agent with a server-assigned ID.

        Args:
            name: Addressable name, unique per org
                (format: ``[a-z0-9]+(-[a-z0-9]+)*``, max 64 chars).
            system_prompt: System prompt defining agent behavior.
            display_name: Human-readable display name shown in UI.
                Falls back to ``name`` when absent.
            description: Human-readable description.
            default_model_id: Default LLM model ID.
            tags: Tags for organizing agents.
            capabilities: Capabilities to enable.
            initial_files: Starter files copied into each new session for this agent.

        Raises:
            ValueError: If ``name`` fails validation.
        """
        validate_agent_name(name)
        req = CreateAgentRequest(
            name=name,
            display_name=display_name,
            system_prompt=system_prompt,
            description=description,
            default_model_id=default_model_id,
            tags=tags or [],
            capabilities=capabilities or [],
            initial_files=initial_files or [],
        )
        resp = await self._client._post("/agents", req.model_dump(exclude_none=True))
        return Agent(**resp)

    async def apply(
        self,
        id: str,
        name: str,
        system_prompt: str,
        *,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        default_model_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        capabilities: Optional[list[AgentCapabilityConfig]] = None,
        initial_files: Optional[list[InitialFile]] = None,
    ) -> Agent:
        """Create or update an agent with a client-supplied ID (upsert).

        If an agent with the given ID exists, it is updated.
        If not, a new agent is created with that ID.

        Args:
            id: Agent ID (format: ``agent_<32-hex>``). Use
                :func:`~everruns_sdk.generate_agent_id` to create one.
            name: Addressable name, unique per org
                (format: ``[a-z0-9]+(-[a-z0-9]+)*``, max 64 chars).
            system_prompt: System prompt defining agent behavior.
            display_name: Human-readable display name shown in UI.
            description: Human-readable description.
            default_model_id: Default LLM model ID.
            tags: Tags for organizing agents.
            capabilities: Capabilities to enable.
            initial_files: Starter files copied into each new session for this agent.

        Raises:
            ValueError: If ``name`` fails validation.
        """
        validate_agent_name(name)
        req = CreateAgentRequest(
            id=id,
            name=name,
            display_name=display_name,
            system_prompt=system_prompt,
            description=description,
            default_model_id=default_model_id,
            tags=tags or [],
            capabilities=capabilities or [],
            initial_files=initial_files or [],
        )
        resp = await self._client._post("/agents", req.model_dump(exclude_none=True))
        return Agent(**resp)

    async def apply_by_name(
        self,
        name: str,
        system_prompt: str,
        *,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        default_model_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        capabilities: Optional[list[AgentCapabilityConfig]] = None,
        initial_files: Optional[list[InitialFile]] = None,
    ) -> Agent:
        """Create or update an agent by name (upsert).

        If an agent with the given ``name`` exists in the org, it is updated.
        If not, a new agent is created.

        Args:
            name: Addressable name, unique per org
                (format: ``[a-z0-9]+(-[a-z0-9]+)*``, max 64 chars).
            system_prompt: System prompt defining agent behavior.
            display_name: Human-readable display name shown in UI.
            description: Human-readable description.
            default_model_id: Default LLM model ID.
            tags: Tags for organizing agents.
            capabilities: Capabilities to enable.
            initial_files: Starter files copied into each new session for this agent.

        Raises:
            ValueError: If ``name`` fails validation.
        """
        validate_agent_name(name)
        req = CreateAgentRequest(
            name=name,
            display_name=display_name,
            system_prompt=system_prompt,
            description=description,
            default_model_id=default_model_id,
            tags=tags or [],
            capabilities=capabilities or [],
            initial_files=initial_files or [],
        )
        resp = await self._client._post("/agents", req.model_dump(exclude_none=True))
        return Agent(**resp)

    async def copy(self, agent_id: str) -> Agent:
        """Copy an agent, creating a new agent with the same configuration."""
        resp = await self._client._post(f"/agents/{agent_id}/copy", {})
        return Agent(**resp)

    async def delete(self, agent_id: str) -> None:
        """Delete (archive) an agent."""
        await self._client._delete(f"/agents/{agent_id}")

    async def import_agent(self, content: str) -> Agent:
        """Import an agent from Markdown, YAML, JSON, or plain text."""
        resp = await self._client._post_text("/agents/import", content)
        return Agent(**resp)

    async def export(self, agent_id: str) -> str:
        """Export an agent as Markdown with YAML front matter."""
        return await self._client._get_text(f"/agents/{agent_id}/export")


class SessionsClient:
    """Client for session operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def list(
        self,
        agent_id: Optional[str] = None,
        *,
        search: Optional[str] = None,
    ) -> list[Session]:
        """List all sessions.

        Args:
            agent_id: Filter by agent ID.
            search: Case-insensitive title search.
        """
        params: list[str] = []
        if agent_id:
            params.append(f"agent_id={agent_id}")
        if search:
            params.append(f"search={search}")
        path = "/sessions"
        if params:
            path += "?" + "&".join(params)
        resp = await self._client._get(path)
        return [Session(**s) for s in resp.get("data", [])]

    async def get(self, session_id: str) -> Session:
        """Get a session by ID."""
        resp = await self._client._get(f"/sessions/{session_id}")
        return Session(**resp)

    async def create(
        self,
        harness_id: Optional[str] = None,
        *,
        harness_name: Optional[str] = None,
        agent_id: Optional[str] = None,
        title: Optional[str] = None,
        locale: Optional[str] = None,
        model_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        capabilities: Optional[list[AgentCapabilityConfig]] = None,
        initial_files: Optional[list[InitialFile]] = None,
    ) -> Session:
        """Create a new session.

        Args:
            harness_id: Harness ID (format: ``harness_<32-hex>``). Optional;
                server defaults to the Generic harness if omitted.
            harness_name: Human-readable harness name (e.g. ``generic``,
                ``deep-research``). Preferred over ``harness_id``.
                Must match ``[a-z0-9]+(-[a-z0-9]+)*``, max 64 characters.
                Cannot be used together with ``harness_id``.
            agent_id: Agent ID (optional).
            title: Human-readable title.
            locale: Session locale (BCP 47, for example ``uk-UA``).
            model_id: LLM model ID override.
            tags: Tags for organizing sessions.
            capabilities: Session-level capabilities (additive to agent capabilities).
            initial_files: Starter files copied into the session workspace.

        Raises:
            ValueError: If both ``harness_id`` and ``harness_name`` are provided,
                or if ``harness_name`` fails validation.
        """
        if harness_id is not None and harness_name is not None:
            raise ValueError("Cannot specify both harness_id and harness_name")
        if harness_name is not None:
            validate_harness_name(harness_name)
        req = CreateSessionRequest(
            harness_id=harness_id,
            harness_name=harness_name,
            agent_id=agent_id,
            title=title,
            locale=locale,
            model_id=model_id,
            tags=tags or [],
            capabilities=capabilities or [],
            initial_files=initial_files,
        )
        resp = await self._client._post("/sessions", req.model_dump(exclude_none=True))
        return Session(**resp)

    async def delete(self, session_id: str) -> None:
        """Delete a session."""
        await self._client._delete(f"/sessions/{session_id}")

    async def cancel(self, session_id: str) -> None:
        """Cancel the current turn in a session."""
        await self._client._post(f"/sessions/{session_id}/cancel", {})

    async def pin(self, session_id: str) -> None:
        """Pin a session for the current user."""
        await self._client._put_empty(f"/sessions/{session_id}/pin")

    async def unpin(self, session_id: str) -> None:
        """Unpin a session for the current user."""
        await self._client._delete(f"/sessions/{session_id}/pin")

    async def budgets(self, session_id: str) -> list[Budget]:
        """List budgets for a session.

        Args:
            session_id: Session ID.
        """
        resp = await self._client._get(f"/sessions/{session_id}/budgets")
        return [Budget(**b) for b in resp]

    async def budget_check(self, session_id: str) -> BudgetCheckResult:
        """Check all budgets in hierarchy for a session.

        Args:
            session_id: Session ID.
        """
        resp = await self._client._get(f"/sessions/{session_id}/budget-check")
        return BudgetCheckResult(**resp)

    async def resume(self, session_id: str) -> ResumeSessionResponse:
        """Resume paused budgets for a session.

        Args:
            session_id: Session ID.
        """
        resp = await self._client._post(f"/sessions/{session_id}/resume", {})
        return ResumeSessionResponse(**resp)

    async def set_secrets(self, session_id: str, secrets: dict[str, str]) -> None:
        """Batch-set encrypted secrets for a session.

        Args:
            session_id: Session ID.
            secrets: Map of secret name to secret value.
        """
        await self._client._put(
            f"/sessions/{session_id}/storage/secrets",
            {"secrets": secrets},
        )

    async def export(self, session_id: str) -> str:
        """Export a session's messages as JSONL.

        Args:
            session_id: Session ID.
        """
        return await self._client._get_text(f"/sessions/{session_id}/export")


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

    async def create_tool_results(
        self,
        session_id: str,
        results: list[ContentPart],
    ) -> Message:
        """Send tool results back to the session.

        Use after receiving tool calls from an ``output.message.completed``
        event to provide results from locally-executed tools.
        """
        req = CreateMessageRequest(
            message=MessageInput.tool_results(results),
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

    async def list(
        self,
        session_id: str,
        *,
        types: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
        limit: Optional[int] = None,
        before_sequence: Optional[int] = None,
    ) -> list[Event]:
        """List events in a session.

        Args:
            session_id: Session ID.
            types: Positive type filter.
            exclude: Event types to exclude.
            limit: Max events to return (backward pagination).
            before_sequence: Cursor for backward pagination (sequence < value).
        """
        path = f"/sessions/{session_id}/events"
        params: list[str] = []
        if types:
            for t in types:
                params.append(f"types={t}")
        if exclude:
            for e in exclude:
                params.append(f"exclude={e}")
        if limit is not None:
            params.append(f"limit={limit}")
        if before_sequence is not None:
            params.append(f"before_sequence={before_sequence}")
        if params:
            path += "?" + "&".join(params)
        resp = await self._client._get(path)
        return [Event(**e) for e in resp.get("data", [])]

    def stream(
        self,
        session_id: str,
        *,
        types: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
        since_id: Optional[str] = None,
    ) -> EventStream:
        """Stream events from a session via SSE."""
        options = StreamOptions(types=types or [], exclude=exclude or [], since_id=since_id)
        return EventStream(self._client, session_id, options)


class CapabilitiesClient:
    """Client for capability operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def list(self) -> list[CapabilityInfo]:
        """List all available capabilities."""
        resp = await self._client._get("/capabilities")
        return [CapabilityInfo(**c) for c in resp.get("data", [])]

    async def get(self, capability_id: str) -> CapabilityInfo:
        """Get a specific capability by ID."""
        resp = await self._client._get(f"/capabilities/{capability_id}")
        return CapabilityInfo(**resp)


class SessionFilesClient:
    """Client for session filesystem operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def list(
        self,
        session_id: str,
        path: Optional[str] = None,
        *,
        recursive: Optional[bool] = None,
    ) -> list[FileInfo]:
        """List files in a directory.

        Args:
            session_id: Session ID.
            path: Directory path (defaults to root).
            recursive: List recursively.
        """
        if path:
            api_path = f"/sessions/{session_id}/fs/{path.lstrip('/')}"
        else:
            api_path = f"/sessions/{session_id}/fs"
        params: list[str] = []
        if recursive:
            params.append("recursive=true")
        if params:
            api_path += "?" + "&".join(params)
        resp = await self._client._get(api_path)
        return [FileInfo(**f) for f in resp.get("data", [])]

    async def read(self, session_id: str, path: str) -> SessionFile:
        """Read a file's content.

        Args:
            session_id: Session ID.
            path: File path.
        """
        resp = await self._client._get(f"/sessions/{session_id}/fs/{path.lstrip('/')}")
        return SessionFile(**resp)

    async def create(
        self,
        session_id: str,
        path: str,
        content: str,
        *,
        encoding: Optional[str] = None,
        is_readonly: Optional[bool] = None,
    ) -> SessionFile:
        """Create a file.

        Args:
            session_id: Session ID.
            path: File path.
            content: File content.
            encoding: Content encoding ("text" or "base64").
            is_readonly: Whether the file is read-only.
        """
        body: dict[str, Any] = {"content": content}
        if encoding is not None:
            body["encoding"] = encoding
        if is_readonly is not None:
            body["is_readonly"] = is_readonly
        resp = await self._client._post(f"/sessions/{session_id}/fs/{path.lstrip('/')}", body)
        return SessionFile(**resp)

    async def create_dir(self, session_id: str, path: str) -> SessionFile:
        """Create a directory.

        Args:
            session_id: Session ID.
            path: Directory path.
        """
        resp = await self._client._post(
            f"/sessions/{session_id}/fs/{path.lstrip('/')}",
            {"is_directory": True},
        )
        return SessionFile(**resp)

    async def update(
        self,
        session_id: str,
        path: str,
        content: str,
        *,
        encoding: Optional[str] = None,
        is_readonly: Optional[bool] = None,
    ) -> SessionFile:
        """Update a file's content.

        Args:
            session_id: Session ID.
            path: File path.
            content: New file content.
            encoding: Content encoding ("text" or "base64").
            is_readonly: Whether the file is read-only.
        """
        body: dict[str, Any] = {"content": content}
        if encoding is not None:
            body["encoding"] = encoding
        if is_readonly is not None:
            body["is_readonly"] = is_readonly
        resp = await self._client._put(f"/sessions/{session_id}/fs/{path.lstrip('/')}", body)
        return SessionFile(**resp)

    async def delete(
        self,
        session_id: str,
        path: str,
        *,
        recursive: Optional[bool] = None,
    ) -> DeleteFileResponse:
        """Delete a file or directory.

        Args:
            session_id: Session ID.
            path: File or directory path.
            recursive: Delete recursively (for directories).
        """
        api_path = f"/sessions/{session_id}/fs/{path.lstrip('/')}"
        if recursive:
            api_path += "?recursive=true"
        resp = await self._client._delete_json(api_path)
        return DeleteFileResponse(**resp)

    async def move_file(
        self,
        session_id: str,
        src_path: str,
        dst_path: str,
    ) -> SessionFile:
        """Move/rename a file.

        Args:
            session_id: Session ID.
            src_path: Source path.
            dst_path: Destination path.
        """
        resp = await self._client._post(
            f"/sessions/{session_id}/fs/_/move",
            {"src_path": src_path, "dst_path": dst_path},
        )
        return SessionFile(**resp)

    async def copy_file(
        self,
        session_id: str,
        src_path: str,
        dst_path: str,
    ) -> SessionFile:
        """Copy a file.

        Args:
            session_id: Session ID.
            src_path: Source path.
            dst_path: Destination path.
        """
        resp = await self._client._post(
            f"/sessions/{session_id}/fs/_/copy",
            {"src_path": src_path, "dst_path": dst_path},
        )
        return SessionFile(**resp)

    async def grep(
        self,
        session_id: str,
        pattern: str,
        *,
        path_pattern: Optional[str] = None,
    ) -> list[GrepResult]:
        """Search files with regex.

        Args:
            session_id: Session ID.
            pattern: Regex pattern to search for.
            path_pattern: Optional path pattern to filter files.
        """
        body: dict[str, Any] = {"pattern": pattern}
        if path_pattern is not None:
            body["path_pattern"] = path_pattern
        resp = await self._client._post(f"/sessions/{session_id}/fs/_/grep", body)
        return [GrepResult(**r) for r in resp.get("data", [])]

    async def stat(self, session_id: str, path: str) -> FileStat:
        """Get file or directory stat.

        Args:
            session_id: Session ID.
            path: File or directory path.
        """
        resp = await self._client._post(f"/sessions/{session_id}/fs/_/stat", {"path": path})
        return FileStat(**resp)


class BudgetsClient:
    """Client for budget operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def create(
        self,
        subject_type: str,
        subject_id: str,
        currency: str,
        limit: float,
        *,
        soft_limit: Optional[float] = None,
        period: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Budget:
        """Create a budget.

        Args:
            subject_type: Subject type (session, agent, user, org).
            subject_id: Subject entity ID.
            currency: Currency (usd, tokens, credits, etc).
            limit: Hard limit.
            soft_limit: Soft limit (triggers pause/warn).
            period: Period config for recurring budgets.
            metadata: Arbitrary metadata.
        """
        body: dict[str, Any] = {
            "subject_type": subject_type,
            "subject_id": subject_id,
            "currency": currency,
            "limit": limit,
        }
        if soft_limit is not None:
            body["soft_limit"] = soft_limit
        if period is not None:
            body["period"] = period
        if metadata is not None:
            body["metadata"] = metadata
        resp = await self._client._post("/budgets", body)
        return Budget(**resp)

    async def list(
        self,
        *,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
    ) -> list[Budget]:
        """List budgets, optionally filtered by subject.

        Args:
            subject_type: Filter by subject type.
            subject_id: Filter by subject ID.
        """
        params: list[str] = []
        if subject_type:
            params.append(f"subject_type={subject_type}")
        if subject_id:
            params.append(f"subject_id={subject_id}")
        path = "/budgets"
        if params:
            path += "?" + "&".join(params)
        resp = await self._client._get(path)
        return [Budget(**b) for b in resp]

    async def get(self, budget_id: str) -> Budget:
        """Get a budget by ID.

        Args:
            budget_id: Budget ID.
        """
        resp = await self._client._get(f"/budgets/{budget_id}")
        return Budget(**resp)

    async def update(
        self,
        budget_id: str,
        *,
        limit: Optional[float] = None,
        soft_limit: Optional[Optional[float]] = None,
        status: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Budget:
        """Update a budget.

        Args:
            budget_id: Budget ID.
            limit: New hard limit.
            soft_limit: New soft limit (None to remove).
            status: New status.
            metadata: New metadata.
        """
        body: dict[str, Any] = {}
        if limit is not None:
            body["limit"] = limit
        if soft_limit is not None:
            body["soft_limit"] = soft_limit
        if status is not None:
            body["status"] = status
        if metadata is not None:
            body["metadata"] = metadata
        resp = await self._client._patch(f"/budgets/{budget_id}", body)
        return Budget(**resp)

    async def delete(self, budget_id: str) -> None:
        """Delete (soft-delete) a budget.

        Args:
            budget_id: Budget ID.
        """
        await self._client._delete(f"/budgets/{budget_id}")

    async def top_up(
        self,
        budget_id: str,
        amount: float,
        *,
        description: Optional[str] = None,
    ) -> Budget:
        """Add credits to a budget.

        Args:
            budget_id: Budget ID.
            amount: Amount to add.
            description: Optional description.
        """
        body: dict[str, Any] = {"amount": amount}
        if description is not None:
            body["description"] = description
        resp = await self._client._post(f"/budgets/{budget_id}/top-up", body)
        return Budget(**resp)

    async def ledger(
        self,
        budget_id: str,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[LedgerEntry]:
        """Get paginated ledger entries for a budget.

        Args:
            budget_id: Budget ID.
            limit: Max entries to return.
            offset: Offset for pagination.
        """
        params: list[str] = []
        if limit is not None:
            params.append(f"limit={limit}")
        if offset is not None:
            params.append(f"offset={offset}")
        path = f"/budgets/{budget_id}/ledger"
        if params:
            path += "?" + "&".join(params)
        resp = await self._client._get(path)
        return [LedgerEntry(**e) for e in resp]

    async def check(self, budget_id: str) -> BudgetCheckResult:
        """Check budget status.

        Args:
            budget_id: Budget ID.
        """
        resp = await self._client._get(f"/budgets/{budget_id}/check")
        return BudgetCheckResult(**resp)


class ConnectionsClient:
    """Client for user connection operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def set(self, provider: str, api_key: str) -> Connection:
        """Set an API key connection for a provider.

        Args:
            provider: Provider name (e.g. "daytona").
            api_key: API key for the provider.
        """
        resp = await self._client._post(
            f"/user/connections/{provider}",
            {"api_key": api_key},
        )
        return Connection(**resp)

    async def list(self) -> list[Connection]:
        """List all connections."""
        resp = await self._client._get("/user/connections")
        return [Connection(**c) for c in resp.get("data", [])]

    async def remove(self, provider: str) -> None:
        """Remove a connection.

        Args:
            provider: Provider name (e.g. "daytona").
        """
        await self._client._delete(f"/user/connections/{provider}")
