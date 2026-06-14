"""Main client for Everruns API."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Literal, Optional
from urllib.parse import urlencode

import httpx

from everruns_sdk.auth import ApiKey
from everruns_sdk.errors import ApiError, ValidationError
from everruns_sdk.models import (
    Agent,
    AgentAnalysisResponse,
    AgentCapabilityConfig,
    AgentVersion,
    AgentVersionChangeKind,
    AgentVersionDiffResponse,
    AnalyzeAgentRequest,
    Budget,
    BudgetCheckResult,
    CapabilityInfo,
    ClientToolResult,
    Connection,
    ContentPart,
    Controls,
    CreateAgentRequest,
    CreateAgentVersionRequest,
    CreateMemoryFileRequest,
    CreateMemoryRequest,
    CreateMessageRequest,
    CreateSessionRequest,
    CreateWorkspaceRequest,
    DeleteFileResponse,
    Event,
    FileInfo,
    FileStat,
    ForkAgentVersionRequest,
    GrepResult,
    GuardrailExamplesResponse,
    GuardrailsDryRunRequest,
    GuardrailsDryRunResponse,
    InitialFile,
    LedgerEntry,
    ListResponse,
    Memory,
    MemoryFile,
    MemoryFileInfo,
    MemoryGrepResult,
    Message,
    MessageInput,
    ResourceStats,
    ResumeSessionResponse,
    RollbackAgentVersionRequest,
    Session,
    SessionFile,
    SetDefaultAgentVersionRequest,
    SubmitToolResultsRequest,
    SubmitToolResultsResponse,
    ToolDefinition,
    UpdateMemoryFileRequest,
    UpdateMemoryRequest,
    UpdateWorkspaceRequest,
    Workspace,
    validate_agent_name,
    validate_harness_name,
)
from everruns_sdk.sse import EventStream, StreamOptions

DEFAULT_BASE_URL = "https://custom.example.com/api"


def _is_html_response(body: str) -> bool:
    """Check if the body looks like an HTML response."""
    trimmed = body.lstrip()
    return trimmed.startswith("<!DOCTYPE") or trimmed.lower().startswith("<html")


def _with_query(path: str, params: dict[str, Any]) -> str:
    """Append URL-encoded query params to a path."""
    query = urlencode(
        [(key, value) for key, value in params.items() if value is not None],
        doseq=True,
    )
    if not query:
        return path
    return f"{path}?{query}"


def _validate_org_id(org_id: Optional[str]) -> Optional[str]:
    if org_id is None:
        return None
    if not org_id:
        raise ValidationError("org_id cannot be empty")
    if any(char in org_id for char in ("\r", "\n", "\0")):
        raise ValidationError("org_id contains invalid header characters")
    return org_id


class Everruns:
    """Main client for interacting with the Everruns API.

    Args:
        api_key: API key (optional, defaults to EVERRUNS_API_KEY env var)
        base_url: Base URL for the API (optional)
        org_id: Organization ID (optional, defaults to EVERRUNS_ORG_ID env var)

    Example:
        >>> client = Everruns()
        >>> agent = await client.agents.create("assistant", "You are helpful.")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        org_id: Optional[str] = None,
    ):
        """Initialize Everruns client.

        Args:
            api_key: API key (falls back to EVERRUNS_API_KEY env var)
            base_url: API base URL (falls back to EVERRUNS_API_URL env var,
                      then DEFAULT_BASE_URL)
            org_id: Organization ID sent as X-Org-Id (falls back to
                    EVERRUNS_ORG_ID env var)
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
        if org_id is None:
            org_id = os.environ.get("EVERRUNS_ORG_ID") or None

        self._api_key = ApiKey(api_key)
        self._org_id = _validate_org_id(org_id)
        # Ensure base URL has trailing slash for correct URL joining.
        # httpx follows RFC 3986: without trailing slash, relative paths
        # replace the last path segment instead of appending.
        # Example: "http://host/api" + "v1/x" = "http://host/v1/x" (wrong)
        #          "http://host/api/" + "v1/x" = "http://host/api/v1/x" (correct)
        self._base_url = base_url.rstrip("/") + "/"
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=self._auth_headers(),
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
    def workspaces(self) -> "WorkspacesClient":
        """Get the workspaces client."""
        return WorkspacesClient(self)

    @property
    def workspace_files(self) -> "WorkspaceFilesClient":
        """Get the workspace files client."""
        return WorkspaceFilesClient(self)

    @property
    def memories(self) -> "MemoriesClient":
        """Get the memories client."""
        return MemoriesClient(self)

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

    def _auth_headers(self, *, content_type: Optional[str] = "application/json") -> dict[str, str]:
        headers = {"Authorization": self._api_key.value}
        if content_type is not None:
            headers["Content-Type"] = content_type
        if self._org_id is not None:
            headers["X-Org-Id"] = self._org_id
        return headers

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
            headers=self._auth_headers(content_type="text/plain"),
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

    async def stats(self, agent_id: str) -> ResourceStats:
        """Get aggregate usage stats for an agent."""
        resp = await self._client._get(f"/agents/{agent_id}/stats")
        return ResourceStats(**resp)

    async def list_versions(self, agent_id: str) -> list[AgentVersion]:
        """List saved versions for an agent."""
        resp = await self._client._get(f"/agents/{agent_id}/versions")
        return [AgentVersion(**version) for version in resp]

    async def create_version(
        self,
        agent_id: str,
        *,
        change_kind: Optional[AgentVersionChangeKind] = None,
        summary: Optional[str] = None,
    ) -> AgentVersion:
        """Save the current agent configuration as a version."""
        req = CreateAgentVersionRequest(change_kind=change_kind, summary=summary)
        resp = await self._client._post(
            f"/agents/{agent_id}/versions",
            req.model_dump(exclude_none=True),
        )
        return AgentVersion(**resp)

    async def set_default_version(self, agent_id: str, version_id: str) -> Agent:
        """Set the default version for an agent."""
        req = SetDefaultAgentVersionRequest(version_id=version_id)
        resp = await self._client._post(
            f"/agents/{agent_id}/versions/default",
            req.model_dump(exclude_none=True),
        )
        return Agent(**resp)

    async def diff_versions(
        self,
        agent_id: str,
        from_version_id: str,
        to_version_id: str,
    ) -> AgentVersionDiffResponse:
        """Diff two saved agent versions."""
        resp = await self._client._get(
            f"/agents/{agent_id}/versions/{from_version_id}/diff/{to_version_id}"
        )
        return AgentVersionDiffResponse(**resp)

    async def fork_version(
        self,
        agent_id: str,
        version_id: str,
        *,
        name: str,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Agent:
        """Create a new agent from a saved version."""
        validate_agent_name(name)
        req = ForkAgentVersionRequest(
            name=name,
            display_name=display_name,
            description=description,
        )
        resp = await self._client._post(
            f"/agents/{agent_id}/versions/{version_id}/fork",
            req.model_dump(exclude_none=True),
        )
        return Agent(**resp)

    async def rollback_version(
        self,
        agent_id: str,
        version_id: str,
        *,
        save_version: Optional[bool] = None,
        summary: Optional[str] = None,
    ) -> Agent:
        """Restore an agent from a saved version."""
        req = RollbackAgentVersionRequest(save_version=save_version, summary=summary)
        resp = await self._client._post(
            f"/agents/{agent_id}/versions/{version_id}/rollback",
            req.model_dump(exclude_none=True),
        )
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
        tools: Optional[list[ToolDefinition]] = None,
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
            tools: Client-side tools to expose to the agent.
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
            tools=tools or [],
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
        tools: Optional[list[ToolDefinition]] = None,
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
            tools: Client-side tools to expose to the agent.
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
            tools=tools or [],
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
        tools: Optional[list[ToolDefinition]] = None,
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
            tools: Client-side tools to expose to the agent.
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
            tools=tools or [],
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

    async def import_example(self, example_name: str) -> Agent:
        """Import an agent from a built-in example."""
        path = _with_query("/agents/import", {"from-example": example_name})
        resp = await self._client._post_text(path, "")
        return Agent(**resp)

    async def export(self, agent_id: str) -> str:
        """Export an agent as Markdown with YAML front matter."""
        return await self._client._get_text(f"/agents/{agent_id}/export")

    async def analyze(
        self,
        system_prompt: str,
        *,
        capabilities: Optional[list[AgentCapabilityConfig]] = None,
        tools: Optional[list[dict[str, Any]]] = None,
        mcp_servers: Optional[dict[str, Any]] = None,
    ) -> AgentAnalysisResponse:
        """Run advisory checks against an agent shape."""
        req = AnalyzeAgentRequest(
            system_prompt=system_prompt,
            capabilities=capabilities or [],
            tools=tools or [],
            mcpServers=mcp_servers,
        )
        resp = await self._client._post(
            "/agents/analyze",
            req.model_dump(by_alias=True, exclude_none=True),
        )
        return AgentAnalysisResponse(**resp)


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
        tools: Optional[list[ToolDefinition]] = None,
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
            tools: Session-level client-side tools.
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
            tools=tools or [],
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
    ) -> SubmitToolResultsResponse:
        """Send tool results back to the session.

        Use after receiving tool calls from a ``tool.call_requested``
        event to provide results from locally-executed tools.
        """
        tool_results = []
        for part in results:
            if part.type != "tool_result" or part.tool_call_id is None:
                raise ValueError("create_tool_results accepts only tool_result content parts")
            tool_results.append(
                ClientToolResult(
                    tool_call_id=part.tool_call_id,
                    result=part.result,
                    error=part.error,
                )
            )
        req = SubmitToolResultsRequest(tool_results=tool_results)
        delay = 0.1
        for attempt in range(6):
            try:
                resp = await self._client._post(
                    f"/sessions/{session_id}/tool-results",
                    req.model_dump(exclude_none=True),
                )
                return SubmitToolResultsResponse(**resp)
            except ApiError as exc:
                if attempt >= 5 or not _is_tool_results_pending_conflict(exc):
                    raise
                await asyncio.sleep(delay)
                delay *= 2
        raise RuntimeError("unreachable")


class EventsClient:
    """Client for event operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def list(
        self,
        session_id: str,
        *,
        since_id: Optional[str] = None,
        types: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
        limit: Optional[int] = None,
        before_sequence: Optional[int] = None,
        after_sequence: Optional[int] = None,
        around: Optional[str] = None,
        window: Optional[int] = None,
        from_ts: Optional[str] = None,
        to_ts: Optional[str] = None,
        turn_id: Optional[str] = None,
        exec_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        tool_name: Optional[str] = None,
        q: Optional[str] = None,
        order_desc: Optional[bool] = None,
    ) -> list[Event]:
        """List events in a session.

        Args:
            session_id: Session ID.
            since_id: Return events after this event ID.
            types: Positive type filter.
            exclude: Event types to exclude.
            limit: Max events to return (backward pagination).
            before_sequence: Cursor for backward pagination (sequence < value).
            after_sequence: Forward cursor (sequence > value).
            around: Anchor event ID for centered windows.
            window: Events to return on each side of ``around``.
            from_ts: Lower ``created_at`` bound (RFC 3339).
            to_ts: Upper ``created_at`` bound (RFC 3339).
            turn_id: Filter by turn ID.
            exec_id: Filter by execution ID.
            trace_id: Filter by trace ID.
            tags: Tag any-match filter.
            tool_name: Filter tool events by tool name.
            q: Full-text search query.
            order_desc: Return newest first when true.
        """
        path = _with_query(
            f"/sessions/{session_id}/events",
            {
                "since_id": since_id,
                "types": types,
                "exclude": exclude,
                "limit": limit,
                "before_sequence": before_sequence,
                "after_sequence": after_sequence,
                "around": around,
                "window": window,
                "from_ts": from_ts,
                "to_ts": to_ts,
                "turn_id": turn_id,
                "exec_id": exec_id,
                "trace_id": trace_id,
                "tags": tags,
                "tool_name": tool_name,
                "q": q,
                "order_desc": str(order_desc).lower() if order_desc is not None else None,
            },
        )
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


def _is_tool_results_pending_conflict(error: ApiError) -> bool:
    return error.status_code == 409 and "not waiting for tool results" in error.message


class CapabilitiesClient:
    """Client for capability operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def list_page(
        self,
        *,
        search: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> ListResponse:
        """List capabilities with pagination metadata."""
        path = _with_query(
            "/capabilities",
            {
                "search": search,
                "offset": offset,
                "limit": limit,
            },
        )
        resp = await self._client._get(path)
        return ListResponse.model_validate(resp)

    async def list(
        self,
        *,
        search: Optional[str] = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[CapabilityInfo]:
        """List available capabilities."""
        page = await self.list_page(search=search, offset=offset, limit=limit)
        return [CapabilityInfo(**c) for c in page.data]

    async def get(self, capability_id: str) -> CapabilityInfo:
        """Get a specific capability by ID."""
        resp = await self._client._get(f"/capabilities/{capability_id}")
        return CapabilityInfo(**resp)

    async def list_guardrail_examples(self) -> GuardrailExamplesResponse:
        """List adoptable guardrail presets."""
        resp = await self._client._get("/capabilities/guardrails/examples")
        return GuardrailExamplesResponse(**resp)

    async def dry_run_guardrails(
        self,
        config: dict[str, Any],
        stage: Literal["output", "tool_use", "tool_output"],
        text: str,
        *,
        tool_name: Optional[str] = None,
    ) -> GuardrailsDryRunResponse:
        """Evaluate a guardrails config against sample content."""
        req = GuardrailsDryRunRequest(
            config=config,
            stage=stage,
            text=text,
            tool_name=tool_name,
        )
        resp = await self._client._post(
            "/capabilities/guardrails/dry-run",
            req.model_dump(exclude_none=True),
        )
        return GuardrailsDryRunResponse(**resp)


class WorkspacesClient:
    """Client for workspace operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def list(
        self,
        *,
        search: Optional[str] = None,
        include_archived: Optional[bool] = None,
    ) -> list[Workspace]:
        """List workspaces."""
        include_archived_param = None if include_archived is None else str(include_archived).lower()
        path = _with_query(
            "/workspaces",
            {"search": search, "include_archived": include_archived_param},
        )
        resp = await self._client._get(path)
        return [Workspace(**w) for w in resp.get("data", [])]

    async def create(self, name: str, *, description: Optional[str] = None) -> Workspace:
        """Create a workspace."""
        req = CreateWorkspaceRequest(name=name, description=description)
        resp = await self._client._post("/workspaces", req.model_dump(exclude_none=True))
        return Workspace(**resp)

    async def get(self, workspace_id: str) -> Workspace:
        """Get a workspace by ID."""
        resp = await self._client._get(f"/workspaces/{workspace_id}")
        return Workspace(**resp)

    async def update(
        self,
        workspace_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Workspace:
        """Update a workspace."""
        req = UpdateWorkspaceRequest(name=name, description=description, status=status)
        resp = await self._client._patch(
            f"/workspaces/{workspace_id}",
            req.model_dump(exclude_none=True),
        )
        return Workspace(**resp)

    async def delete(self, workspace_id: str) -> None:
        """Archive a workspace."""
        await self._client._delete(f"/workspaces/{workspace_id}")


class WorkspaceFilesClient:
    """Client for workspace filesystem operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def list(
        self,
        workspace_id: str,
        path: Optional[str] = None,
        *,
        recursive: Optional[bool] = None,
    ) -> list[FileInfo]:
        """List files in a directory.

        Args:
            workspace_id: Workspace ID.
            path: Directory path (defaults to root).
            recursive: List recursively.
        """
        if path:
            api_path = f"/workspaces/{workspace_id}/fs/{path.lstrip('/')}"
        else:
            api_path = f"/workspaces/{workspace_id}/fs"
        params: list[str] = []
        if recursive:
            params.append("recursive=true")
        if params:
            api_path += "?" + "&".join(params)
        resp = await self._client._get(api_path)
        return [FileInfo(**f) for f in resp.get("data", [])]

    async def read(self, workspace_id: str, path: str) -> SessionFile:
        """Read a file's content.

        Args:
            workspace_id: Workspace ID.
            path: File path.
        """
        resp = await self._client._get(f"/workspaces/{workspace_id}/fs/{path.lstrip('/')}")
        return SessionFile(**resp)

    async def create(
        self,
        workspace_id: str,
        path: str,
        content: str,
        *,
        encoding: Optional[str] = None,
        is_readonly: Optional[bool] = None,
    ) -> SessionFile:
        """Create a file.

        Args:
            workspace_id: Workspace ID.
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
        resp = await self._client._post(f"/workspaces/{workspace_id}/fs/{path.lstrip('/')}", body)
        return SessionFile(**resp)

    async def create_dir(self, workspace_id: str, path: str) -> SessionFile:
        """Create a directory.

        Args:
            workspace_id: Workspace ID.
            path: Directory path.
        """
        resp = await self._client._post(
            f"/workspaces/{workspace_id}/fs/{path.lstrip('/')}",
            {"is_directory": True},
        )
        return SessionFile(**resp)

    async def update(
        self,
        workspace_id: str,
        path: str,
        content: str,
        *,
        encoding: Optional[str] = None,
        is_readonly: Optional[bool] = None,
    ) -> SessionFile:
        """Update a file's content.

        Args:
            workspace_id: Workspace ID.
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
        resp = await self._client._put(f"/workspaces/{workspace_id}/fs/{path.lstrip('/')}", body)
        return SessionFile(**resp)

    async def delete(
        self,
        workspace_id: str,
        path: str,
        *,
        recursive: Optional[bool] = None,
    ) -> DeleteFileResponse:
        """Delete a file or directory.

        Args:
            workspace_id: Workspace ID.
            path: File or directory path.
            recursive: Delete recursively (for directories).
        """
        api_path = f"/workspaces/{workspace_id}/fs/{path.lstrip('/')}"
        if recursive:
            api_path += "?recursive=true"
        resp = await self._client._delete_json(api_path)
        return DeleteFileResponse(**resp)

    async def move_file(
        self,
        workspace_id: str,
        src_path: str,
        dst_path: str,
    ) -> SessionFile:
        """Move/rename a file.

        Args:
            workspace_id: Workspace ID.
            src_path: Source path.
            dst_path: Destination path.
        """
        resp = await self._client._post(
            f"/workspaces/{workspace_id}/fs/_/move",
            {"src_path": src_path, "dst_path": dst_path},
        )
        return SessionFile(**resp)

    async def copy_file(
        self,
        workspace_id: str,
        src_path: str,
        dst_path: str,
    ) -> SessionFile:
        """Copy a file.

        Args:
            workspace_id: Workspace ID.
            src_path: Source path.
            dst_path: Destination path.
        """
        resp = await self._client._post(
            f"/workspaces/{workspace_id}/fs/_/copy",
            {"src_path": src_path, "dst_path": dst_path},
        )
        return SessionFile(**resp)

    async def grep(
        self,
        workspace_id: str,
        pattern: str,
        *,
        path_pattern: Optional[str] = None,
    ) -> list[GrepResult]:
        """Search files with regex.

        Args:
            workspace_id: Workspace ID.
            pattern: Regex pattern to search for.
            path_pattern: Optional path pattern to filter files.
        """
        body: dict[str, Any] = {"pattern": pattern}
        if path_pattern is not None:
            body["path_pattern"] = path_pattern
        resp = await self._client._post(f"/workspaces/{workspace_id}/fs/_/grep", body)
        return [GrepResult(**r) for r in resp.get("data", [])]

    async def stat(self, workspace_id: str, path: str) -> FileStat:
        """Get file or directory stat.

        Args:
            workspace_id: Workspace ID.
            path: File or directory path.
        """
        resp = await self._client._post(f"/workspaces/{workspace_id}/fs/_/stat", {"path": path})
        return FileStat(**resp)


class MemoriesClient:
    """Client for memory operations."""

    def __init__(self, client: Everruns):
        self._client = client

    async def list(
        self,
        *,
        search: Optional[str] = None,
        include_archived: Optional[bool] = None,
    ) -> list[Memory]:
        """List memories."""
        include_archived_param = None if include_archived is None else str(include_archived).lower()
        path = _with_query(
            "/memories",
            {"search": search, "include_archived": include_archived_param},
        )
        resp = await self._client._get(path)
        return [Memory(**m) for m in resp.get("data", [])]

    async def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        source: Optional[dict[str, Any]] = None,
    ) -> Memory:
        """Create a memory."""
        req = CreateMemoryRequest(name=name, description=description, source=source)
        resp = await self._client._post("/memories", req.model_dump(exclude_none=True))
        return Memory(**resp)

    async def get(self, memory_id: str) -> Memory:
        """Get a memory by ID."""
        resp = await self._client._get(f"/memories/{memory_id}")
        return Memory(**resp)

    async def update(
        self,
        memory_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        source: Optional[dict[str, Any]] = None,
    ) -> Memory:
        """Update a memory."""
        req = UpdateMemoryRequest(name=name, description=description, source=source)
        resp = await self._client._patch(
            f"/memories/{memory_id}",
            req.model_dump(exclude_none=True),
        )
        return Memory(**resp)

    async def delete(self, memory_id: str) -> None:
        """Archive a memory."""
        await self._client._delete(f"/memories/{memory_id}")

    async def sync(self, memory_id: str) -> Memory:
        """Trigger memory sync now."""
        resp = await self._client._post(f"/memories/{memory_id}/sync", {})
        return Memory(**resp)

    async def list_files(self, memory_id: str) -> list[MemoryFileInfo]:
        """List memory files at the root."""
        resp = await self._client._get(f"/memories/{memory_id}/fs")
        return [MemoryFileInfo(**item) for item in resp.get("data", [])]

    async def read_file(self, memory_id: str, path: str) -> MemoryFile:
        """Read a memory file."""
        resp = await self._client._get(f"/memories/{memory_id}/fs/{path.lstrip('/')}")
        return MemoryFile(**resp)

    async def download_file(self, memory_id: str, path: str) -> str:
        """Download a memory file as text."""
        return await self._client._get_text(
            f"/memories/{memory_id}/fs/_/download/{path.lstrip('/')}"
        )

    async def create_file(
        self,
        memory_id: str,
        path: str,
        content: str,
        *,
        encoding: Optional[str] = None,
    ) -> MemoryFileInfo:
        """Create a memory file."""
        req = CreateMemoryFileRequest(content=content, encoding=encoding)
        resp = await self._client._post(
            f"/memories/{memory_id}/fs/{path.lstrip('/')}",
            req.model_dump(exclude_none=True),
        )
        return MemoryFileInfo(**resp)

    async def create_dir(self, memory_id: str, path: str) -> MemoryFileInfo:
        """Create a memory directory."""
        req = CreateMemoryFileRequest(is_directory=True)
        resp = await self._client._post(
            f"/memories/{memory_id}/fs/{path.lstrip('/')}",
            req.model_dump(exclude_none=True),
        )
        return MemoryFileInfo(**resp)

    async def update_file(
        self,
        memory_id: str,
        path: str,
        content: str,
        *,
        encoding: Optional[str] = None,
    ) -> MemoryFile:
        """Update a memory file."""
        req = UpdateMemoryFileRequest(content=content, encoding=encoding)
        resp = await self._client._put(
            f"/memories/{memory_id}/fs/{path.lstrip('/')}",
            req.model_dump(exclude_none=True),
        )
        return MemoryFile(**resp)

    async def delete_file(self, memory_id: str, path: str) -> None:
        """Delete a memory file or directory."""
        await self._client._delete(f"/memories/{memory_id}/fs/{path.lstrip('/')}")

    async def grep_files(
        self,
        memory_id: str,
        pattern: str,
        *,
        path_pattern: Optional[str] = None,
    ) -> list[MemoryGrepResult]:
        """Search memory files by regex."""
        body: dict[str, Any] = {"pattern": pattern}
        if path_pattern is not None:
            body["path_pattern"] = path_pattern
        resp = await self._client._post(f"/memories/{memory_id}/fs/_/grep", body)
        return [MemoryGrepResult(**item) for item in resp.get("data", [])]

    async def stat_file(self, memory_id: str, path: str) -> MemoryFileInfo:
        """Stat a memory file or directory."""
        resp = await self._client._post(f"/memories/{memory_id}/fs/_/stat", {"path": path})
        return MemoryFileInfo(**resp)


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
