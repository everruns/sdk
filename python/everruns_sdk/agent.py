"""Agent client: call one agent from code through the Agent Execution API.

The management client (``Everruns``) holds a personal access token that reaches
every management route of an organization. ``AgentClient`` holds a credential that
reaches one agent's session routes and nothing else (an agent key ``evr_ak_...``,
a runtime token, an identity-provider token, or a member's personal access token
when the agent allows it). Use it to call an agent from an application.

The same routes are served by the everruns server
(``{api}/v1/channels/{channel_id}``) and by a serve app
(``{host}/v1/channels/{agent}``), so one client works against both.

Example:
    >>> agent = AgentClient()  # EVERRUNS_AGENT_URL and EVERRUNS_AGENT_KEY
    >>> print(await agent.run("What is the status of order 42?"))
"""

from __future__ import annotations

import os
import re
from typing import Any, Optional

import httpx

from everruns_sdk.auth import ApiKey
from everruns_sdk.client import _is_html_response, _with_query
from everruns_sdk.errors import ApiError, EverrunsError, ValidationError
from everruns_sdk.models import Event
from everruns_sdk.sse import EventStream, StreamOptions

END_USER_HEADER = "End-User"
IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"

_HEADER_FORBIDDEN = re.compile(r"[\r\n\0]")


def _header_value(name: str, value: str) -> str:
    if not value or _HEADER_FORBIDDEN.search(value):
        raise ValidationError(f"{name} is empty or contains invalid header characters")
    return value


class AgentClient:
    """Client for one agent's Agent Execution API.

    Args:
        agent_url: Agent base URL, e.g.
            ``https://app.everruns.com/api/v1/channels/apichan_...``
            (falls back to the ``EVERRUNS_AGENT_URL`` env var).
        credential: Bearer credential: agent key, runtime token, or IdP/PAT
            token (falls back to the ``EVERRUNS_AGENT_KEY`` env var).
        end_user: Optional end-user id sent as ``End-User`` on every request.
            Needs a key holding the ``end_user`` permission. Prefer
            :meth:`for_end_user`.

    Example:
        >>> agent = AgentClient(agent_url=url, credential="evr_ak_...")
        >>> alice = agent.for_end_user("customer-42")
        >>> reply = await alice.run("Hello!")
    """

    def __init__(
        self,
        agent_url: Optional[str] = None,
        credential: Optional[str] = None,
        end_user: Optional[str] = None,
    ):
        if agent_url is None:
            agent_url = os.environ.get("EVERRUNS_AGENT_URL")
        if not agent_url:
            raise ValueError(
                "Agent URL not provided. Set EVERRUNS_AGENT_URL environment variable "
                "or pass agent_url parameter."
            )
        if credential is None:
            credential = os.environ.get("EVERRUNS_AGENT_KEY")
        if not credential:
            raise ValueError(
                "Agent credential not provided. Set EVERRUNS_AGENT_KEY environment variable "
                "or pass credential parameter."
            )

        self._api_key = ApiKey(credential)
        self._base_url = agent_url.rstrip("/")
        self._end_user = _header_value(END_USER_HEADER, end_user) if end_user is not None else None
        self._owns_client = True
        self._client = httpx.AsyncClient(
            headers={"Authorization": self._api_key.value, "Content-Type": "application/json"},
            timeout=30.0,
        )

    def for_end_user(self, end_user: str) -> "AgentClient":
        """Derive a client that acts for one of your application's users.

        Sends ``End-User: <end_user>`` on every request. The derived client
        shares this client's configuration and connection pool, and this client
        is left unchanged. Closing the derived client is a no-op; close the
        client it was derived from.

        Example:
            >>> alice = agent.for_end_user("customer-42")
        """
        derived = object.__new__(AgentClient)
        derived.__dict__.update(self.__dict__)
        derived._end_user = _header_value(END_USER_HEADER, end_user)
        derived._owns_client = False
        return derived

    # -- plumbing -----------------------------------------------------------

    def _url(self, path: str) -> str:
        return f"{self._base_url}{path}"

    def _auth_headers(self, *, content_type: Optional[str] = "application/json") -> dict[str, str]:
        headers = {"Authorization": self._api_key.value}
        if content_type is not None:
            headers["Content-Type"] = content_type
        headers.update(self._request_headers())
        return headers

    def _request_headers(self, idempotency_key: Optional[str] = None) -> dict[str, str]:
        # Per request, because derived clients share one httpx client whose
        # default headers carry no end user.
        headers: dict[str, str] = {}
        if self._end_user is not None:
            headers[END_USER_HEADER] = self._end_user
        if idempotency_key is not None:
            headers[IDEMPOTENCY_KEY_HEADER] = _header_value(IDEMPOTENCY_KEY_HEADER, idempotency_key)
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any = None,
        idempotency_key: Optional[str] = None,
    ) -> Any:
        resp = await self._client.request(
            method,
            self._url(path),
            json=json,
            headers=self._request_headers(idempotency_key),
        )
        if resp.is_success:
            return resp.json() if resp.content else None
        try:
            body = resp.json()
        except Exception:
            text = resp.text
            message = f"HTTP {resp.status_code}" if _is_html_response(text) else text
            body = {"error": {"code": "unknown", "message": message}}
        raise ApiError.from_response(resp.status_code, body)

    # -- operations ---------------------------------------------------------

    async def card(self) -> dict[str, Any]:
        """Get the agent card: name, accepted input, credentials, conversation starters."""
        return await self._request("GET", "")

    async def create_session(
        self,
        title: Optional[str] = None,
        *,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        """Start a session.

        A retry with the same ``idempotency_key`` and body returns the first
        response instead of starting a second session.
        """
        body: dict[str, Any] = {} if title is None else {"title": title}
        return await self._request("POST", "/sessions", json=body, idempotency_key=idempotency_key)

    async def list_sessions(
        self,
        *,
        limit: Optional[int] = None,
        page_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """List this caller's sessions, most recently active first.

        Returns ``{"data": [...], "next_page_token": ...}``.
        """
        path = _with_query("/sessions", {"limit": limit, "page_token": page_token})
        return await self._request("GET", path)

    async def get_session(self, session_id: str) -> dict[str, Any]:
        """Get a session, including ``pending_questions`` and ``pending_approvals``."""
        return await self._request("GET", f"/sessions/{session_id}")

    async def send_message(
        self,
        session_id: str,
        text: str,
        *,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        """Send a user text message; starts a turn or steers the running one."""
        body = {"message": {"role": "user", "content": [{"type": "text", "text": text}]}}
        return await self._request(
            "POST",
            f"/sessions/{session_id}/messages",
            json=body,
            idempotency_key=idempotency_key,
        )

    async def cancel(self, session_id: str) -> Any:
        """Cancel the running turn."""
        return await self._request("POST", f"/sessions/{session_id}/cancel")

    async def list_events(
        self,
        session_id: str,
        *,
        after_sequence: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[Event]:
        """List events oldest first; page forward with ``after_sequence`` (exclusive)."""
        path = _with_query(
            f"/sessions/{session_id}/events",
            {"after_sequence": after_sequence, "limit": limit},
        )
        resp = await self._request("GET", path)
        return [Event(**e) for e in resp.get("data", [])]

    def stream_events(
        self,
        session_id: str,
        *,
        since_id: Optional[str] = None,
        after_sequence: Optional[int] = None,
        max_retries: Optional[int] = None,
    ) -> EventStream:
        """Follow a session's events live, with the SDK's SSE reconnect rules.

        Resume with ``since_id`` (the last event id received), or replay from
        ``after_sequence`` (``0`` replays the whole session).

        Example:
            >>> async for event in agent.stream_events(session_id, after_sequence=0):
            ...     print(event.type)
        """
        return EventStream(
            self,
            session_id,
            StreamOptions(
                since_id=since_id, after_sequence=after_sequence, max_retries=max_retries
            ),
            sse_path=f"sessions/{session_id}/sse",
        )

    async def answer_questions(self, session_id: str, answers: Any) -> Any:
        """Answer the agent's ``ask_user`` question set (JSON body passed through)."""
        return await self._request("POST", f"/sessions/{session_id}/question-answers", json=answers)

    async def submit_tool_approvals(self, session_id: str, decisions: Any) -> Any:
        """Allow or reject held-back tool calls (JSON body passed through)."""
        return await self._request("POST", f"/sessions/{session_id}/tool-approvals", json=decisions)

    async def runtime_token(self) -> dict[str, Any]:
        """Mint a short-lived runtime token for a browser or mobile app.

        Needs ``End-User``: call it on a :meth:`for_end_user` client. Returns
        ``{access_token, token_type, expires_in, virtual_user_id}``. The token
        works on this agent only; hand it to the app, never the agent key.
        """
        if self._end_user is None:
            raise ValidationError("runtime_token requires an end user: use for_end_user()")
        return await self._request("POST", "/runtime-auth")

    async def run(self, text: str, session_id: Optional[str] = None) -> str:
        """Send ``text`` and return the agent's final reply text.

        Creates a session when ``session_id`` is not given, sends the message,
        follows the stream until the turn completes, and returns the last
        assistant message text. Raises ``EverrunsError`` if the turn fails.
        """
        after_sequence = 0
        if session_id is None:
            session_id = (await self.create_session())["id"]
        else:
            after_sequence = await self._last_sequence(session_id)
        await self.send_message(session_id, text)

        reply = ""
        stream = self.stream_events(session_id, after_sequence=after_sequence)
        try:
            async for event in stream:
                if event.type == "output.message.completed":
                    reply = _assistant_text(event.data) or reply
                elif event.type == "turn.completed":
                    return reply
                elif event.type == "turn.failed":
                    data = event.data if isinstance(event.data, dict) else {}
                    raise EverrunsError(
                        f"turn failed: {data.get('error_code') or 'unknown'}: "
                        f"{data.get('error') or 'no detail'}"
                    )
        finally:
            stream.stop()
            await stream.aclose()
        raise EverrunsError("event stream ended before the turn completed")

    async def _last_sequence(self, session_id: str) -> int:
        """Sequence of the session's newest event, so a stream skips history."""
        last = 0
        while True:
            events = await self.list_events(session_id, after_sequence=last)
            sequences = [e.sequence for e in events if e.sequence is not None]
            if not sequences:
                return last
            last = max(sequences)

    async def close(self) -> None:
        """Close the HTTP client (a no-op on a client derived with ``for_end_user``)."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "AgentClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()


def _assistant_text(data: Any) -> str:
    """Text of an ``output.message.completed`` event, or ``""``."""
    message = data.get("message") if isinstance(data, dict) else None
    if not isinstance(message, dict) or message.get("role") not in (None, "agent", "assistant"):
        return ""
    parts = message.get("content") or []
    return "".join(
        p.get("text") or "" for p in parts if isinstance(p, dict) and p.get("type") == "text"
    )


__all__ = ["AgentClient", "END_USER_HEADER", "IDEMPOTENCY_KEY_HEADER"]
