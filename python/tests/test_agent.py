"""Tests for the AgentClient client (AgentClient Execution API)."""

import json
import warnings

import httpx
import pytest
import respx

import everruns_sdk.client as client_module
from everruns_sdk import (
    AgentClient,
    ApiError,
    AuthenticationError,
    Everruns,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from everruns_sdk.errors import EverrunsError

BASE = "https://example.test/api/v1/channels/apichan_1"
SESSION = {"id": "session_1", "status": "idle", "created_at": "t", "updated_at": "t"}


def make_agent(**kwargs) -> AgentClient:
    return AgentClient(agent_url=BASE, credential="evr_ak_secret", **kwargs)


def sse_body(events: list[dict]) -> str:
    frames = ["event: connected\ndata: {}\n\n"]
    for event in events:
        frames.append(f"event: {event['type']}\nid: {event['id']}\ndata: {json.dumps(event)}\n\n")
    return "".join(frames)


def evt(n: int, type_: str, data: dict) -> dict:
    return {
        "id": f"event_{n}",
        "type": type_,
        "ts": "2024-01-01T00:00:00Z",
        "session_id": "session_1",
        "sequence": n,
        "data": data,
    }


def reply(text: str) -> dict:
    return {"message": {"id": "m", "role": "agent", "content": [{"type": "text", "text": text}]}}


def test_missing_url_or_credential(monkeypatch):
    monkeypatch.delenv("EVERRUNS_AGENT_URL", raising=False)
    monkeypatch.delenv("EVERRUNS_AGENT_KEY", raising=False)
    with pytest.raises(ValueError):
        AgentClient(credential="k")
    with pytest.raises(ValueError):
        AgentClient(agent_url=BASE)


def test_from_env(monkeypatch):
    monkeypatch.setenv("EVERRUNS_AGENT_URL", BASE + "/")
    monkeypatch.setenv("EVERRUNS_AGENT_KEY", "evr_ak_env")
    agent = AgentClient()
    assert agent._base_url == BASE
    assert agent._api_key.value == "evr_ak_env"


@pytest.mark.parametrize("url", [BASE, BASE + "/"])
@respx.mock
async def test_url_joining_and_card_at_base(url):
    card = respx.get(BASE).mock(return_value=httpx.Response(200, json={"name": "Support"}))
    created = respx.post(f"{BASE}/sessions").mock(return_value=httpx.Response(201, json=SESSION))
    agent = AgentClient(agent_url=url, credential="evr_ak_secret")
    assert (await agent.card())["name"] == "Support"
    assert (await agent.create_session())["id"] == "session_1"
    assert card.called and created.called
    await agent.close()


@respx.mock
async def test_auth_header_and_no_management_headers():
    route = respx.get(f"{BASE}/sessions/session_1").mock(
        return_value=httpx.Response(200, json=SESSION)
    )
    agent = make_agent()
    await agent.get_session("session_1")
    headers = route.calls[0].request.headers
    assert headers["authorization"] == "evr_ak_secret"
    assert "end-user" not in headers
    assert "x-org-id" not in headers
    assert "everruns-change-reason" not in headers
    await agent.close()


@respx.mock
async def test_for_end_user_sets_header_and_shares_pool():
    route = respx.get(f"{BASE}/sessions").mock(return_value=httpx.Response(200, json={"data": []}))
    agent = make_agent()
    alice = agent.for_end_user("customer-42")
    assert alice._client is agent._client
    await alice.list_sessions(limit=5, page_token="p")
    await agent.list_sessions()
    assert route.calls[0].request.headers["end-user"] == "customer-42"
    assert route.calls[0].request.url.params["limit"] == "5"
    assert route.calls[0].request.url.params["page_token"] == "p"
    assert "end-user" not in route.calls[1].request.headers
    await alice.close()  # no-op: pool stays open
    assert not agent._client.is_closed
    await agent.close()
    assert agent._client.is_closed


def test_for_end_user_rejects_bad_value():
    with pytest.raises(ValidationError):
        make_agent().for_end_user("a\nb")


@respx.mock
async def test_idempotency_key_passthrough():
    sessions = respx.post(f"{BASE}/sessions").mock(return_value=httpx.Response(201, json=SESSION))
    messages = respx.post(f"{BASE}/sessions/session_1/messages").mock(
        return_value=httpx.Response(201, json={"id": "m1"})
    )
    agent = make_agent()
    await agent.create_session("Hi", idempotency_key="k1")
    await agent.send_message("session_1", "hello", idempotency_key="k2")
    await agent.create_session()
    assert sessions.calls[0].request.headers["idempotency-key"] == "k1"
    assert json.loads(sessions.calls[0].request.content) == {"title": "Hi"}
    assert "idempotency-key" not in sessions.calls[1].request.headers
    assert json.loads(sessions.calls[1].request.content) == {}
    assert messages.calls[0].request.headers["idempotency-key"] == "k2"
    assert json.loads(messages.calls[0].request.content) == {
        "message": {"role": "user", "content": [{"type": "text", "text": "hello"}]}
    }
    await agent.close()


@pytest.mark.parametrize(
    "status,exc,code",
    [
        (401, AuthenticationError, "unauthorized"),
        (403, ApiError, "forbidden"),
        (404, NotFoundError, "not_found"),
        (422, ApiError, "idempotency_key_reuse"),
        (429, RateLimitError, "rate_limited"),
    ],
)
@respx.mock
async def test_error_mapping(status, exc, code):
    respx.post(f"{BASE}/sessions").mock(
        return_value=httpx.Response(status, json={"error": {"code": code, "message": "nope"}})
    )
    agent = make_agent()
    with pytest.raises(exc) as info:
        await agent.create_session()
    assert info.value.status_code == status
    assert info.value.code == code
    assert info.value.message == "nope"
    await agent.close()


@respx.mock
async def test_other_operations_routes():
    cancel = respx.post(f"{BASE}/sessions/s/cancel").mock(return_value=httpx.Response(200, json={}))
    answers = respx.post(f"{BASE}/sessions/s/question-answers").mock(
        return_value=httpx.Response(200, json={})
    )
    approvals = respx.post(f"{BASE}/sessions/s/tool-approvals").mock(
        return_value=httpx.Response(200, json={})
    )
    events = respx.get(f"{BASE}/sessions/s/events").mock(
        return_value=httpx.Response(200, json={"data": [evt(3, "turn.started", {})]})
    )
    agent = make_agent()
    await agent.cancel("s")
    await agent.answer_questions("s", {"answers": []})
    await agent.submit_tool_approvals("s", {"decisions": []})
    listed = await agent.list_events("s", after_sequence=2, limit=10)
    assert listed[0].type == "turn.started"
    assert json.loads(answers.calls[0].request.content) == {"answers": []}
    assert json.loads(approvals.calls[0].request.content) == {"decisions": []}
    assert events.calls[0].request.url.params["after_sequence"] == "2"
    assert cancel.called
    await agent.close()


@respx.mock
async def test_runtime_token():
    route = respx.post(f"{BASE}/runtime-auth").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "t",
                "token_type": "Bearer",
                "expires_in": 900,
                "virtual_user_id": "u",
            },
        )
    )
    agent = make_agent()
    with pytest.raises(ValidationError):
        await agent.runtime_token()
    token = await agent.for_end_user("customer-42").runtime_token()
    assert token["access_token"] == "t"
    assert route.calls[0].request.headers["end-user"] == "customer-42"
    await agent.close()


@respx.mock
async def test_run_returns_final_assistant_text():
    respx.post(f"{BASE}/sessions").mock(return_value=httpx.Response(201, json=SESSION))
    send = respx.post(f"{BASE}/sessions/session_1/messages").mock(
        return_value=httpx.Response(201, json={"id": "m1"})
    )
    stream = respx.get(f"{BASE}/sessions/session_1/sse").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=sse_body(
                [
                    evt(1, "turn.started", {"turn_id": "t"}),
                    evt(2, "output.message.completed", reply("first")),
                    evt(3, "output.message.completed", reply("final answer")),
                    evt(4, "turn.completed", {"turn_id": "t"}),
                ]
            ),
        )
    )
    agent = make_agent()
    assert await agent.run("hi") == "final answer"
    assert json.loads(send.calls[0].request.content)["message"]["content"][0]["text"] == "hi"
    assert stream.calls[0].request.url.params["after_sequence"] == "0"
    assert stream.calls[0].request.headers["authorization"] == "evr_ak_secret"
    await agent.close()


@respx.mock
async def test_run_existing_session_streams_after_history():
    respx.get(f"{BASE}/sessions/session_1/events").mock(
        side_effect=[
            httpx.Response(200, json={"data": [evt(7, "turn.completed", {})]}),
            httpx.Response(200, json={"data": []}),
        ]
    )
    respx.post(f"{BASE}/sessions/session_1/messages").mock(
        return_value=httpx.Response(201, json={"id": "m1"})
    )
    stream = respx.get(f"{BASE}/sessions/session_1/sse").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=sse_body(
                [
                    evt(9, "output.message.completed", reply("again")),
                    evt(10, "turn.completed", {}),
                ]
            ),
        )
    )
    agent = make_agent()
    assert await agent.run("more", session_id="session_1") == "again"
    assert stream.calls[0].request.url.params["after_sequence"] == "7"
    await agent.close()


@respx.mock
async def test_run_raises_on_turn_failed():
    respx.post(f"{BASE}/sessions").mock(return_value=httpx.Response(201, json=SESSION))
    respx.post(f"{BASE}/sessions/session_1/messages").mock(
        return_value=httpx.Response(201, json={"id": "m1"})
    )
    respx.get(f"{BASE}/sessions/session_1/sse").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=sse_body(
                [
                    evt(
                        1,
                        "turn.failed",
                        {"turn_id": "t", "error": "Model unavailable", "error_code": "provider"},
                    )
                ]
            ),
        )
    )
    agent = make_agent()
    with pytest.raises(EverrunsError, match="provider"):
        await agent.run("hi")
    await agent.close()


@respx.mock
async def test_management_client_warns_once(monkeypatch):
    monkeypatch.setattr(client_module, "_warned_deprecations", set())
    api = "https://api.test/api/v1"
    respx.post(f"{api}/sessions").mock(return_value=httpx.Response(500, json={}))
    respx.post(f"{api}/sessions/s/messages").mock(return_value=httpx.Response(500, json={}))
    client = Everruns(api_key="evr_pat_x", base_url="https://api.test/api")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        for _ in range(2):
            with pytest.raises(ApiError):
                await client.sessions.create()
            with pytest.raises(ApiError):
                await client.messages.create("s", "hi")
    deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
    assert len(deprecations) == 2
    assert all("AgentClient" in str(w.message) for w in deprecations)
    assert all(w.filename == __file__ for w in deprecations)
    await client.close()
