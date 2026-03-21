"""Tests for Everruns SDK client."""

import json
import os

import httpx
import pytest
import respx

from everruns_sdk import (
    ApiError,
    ApiKey,
    Everruns,
    InitialFile,
)


def test_api_key_creation():
    """Test API key creation."""
    key = ApiKey("evr_test_key")
    assert key.value == "evr_test_key"


def test_api_key_repr():
    """Test API key representation hides the key."""
    key = ApiKey("evr_test_key_12345")
    assert "evr_test" in repr(key)
    assert "12345" not in repr(key)


def test_api_key_from_env():
    """Test API key from environment variable."""
    os.environ["EVERRUNS_API_KEY"] = "evr_from_env"
    try:
        key = ApiKey.from_env()
        assert key.value == "evr_from_env"
    finally:
        del os.environ["EVERRUNS_API_KEY"]


def test_api_key_from_env_missing():
    """Test API key from missing environment variable."""
    if "EVERRUNS_API_KEY" in os.environ:
        del os.environ["EVERRUNS_API_KEY"]

    with pytest.raises(ValueError):
        ApiKey.from_env()


def test_client_creation():
    """Test client creation with explicit API key."""
    client = Everruns(api_key="evr_test_key")
    assert client._api_key.value == "evr_test_key"


def test_client_from_env():
    """Test client creation from environment variable."""
    os.environ["EVERRUNS_API_KEY"] = "evr_from_env"
    try:
        client = Everruns()
        assert client._api_key.value == "evr_from_env"
    finally:
        del os.environ["EVERRUNS_API_KEY"]


def test_client_missing_api_key():
    """Test client creation fails without API key."""
    if "EVERRUNS_API_KEY" in os.environ:
        del os.environ["EVERRUNS_API_KEY"]

    with pytest.raises(ValueError):
        Everruns()


def test_base_url_normalization_adds_trailing_slash():
    """Test that base URL without trailing slash gets one added."""
    client = Everruns(api_key="evr_test_key", base_url="https://custom.example.com/api")
    # Base URL should have trailing slash for correct URL joining
    assert client._base_url == "https://custom.example.com/api/"


def test_base_url_normalization_preserves_single_trailing_slash():
    """Test that base URL with trailing slash is normalized correctly."""
    client = Everruns(api_key="evr_test_key", base_url="https://custom.example.com/api/")
    assert client._base_url == "https://custom.example.com/api/"


def test_url_path_construction():
    """Test that URL paths are constructed correctly."""
    client = Everruns(api_key="evr_test_key", base_url="https://custom.example.com/api")
    # The _url method should produce relative paths without leading slash
    assert client._url("/agents") == "v1/agents"
    assert client._url("/sessions/123") == "v1/sessions/123"


def test_capabilities_subclient():
    """Test that capabilities sub-client is available."""
    client = Everruns(api_key="evr_test_key")
    assert client.capabilities is not None


def test_agent_capability_config_model():
    """Test AgentCapabilityConfig model."""
    from everruns_sdk import AgentCapabilityConfig

    config = AgentCapabilityConfig(ref="current_time")
    assert config.ref == "current_time"
    assert config.config is None

    config_with_opts = AgentCapabilityConfig(ref="web_fetch", config={"timeout": 30})
    assert config_with_opts.ref == "web_fetch"
    assert config_with_opts.config == {"timeout": 30}


def test_capability_info_model():
    """Test CapabilityInfo model."""
    from everruns_sdk import CapabilityInfo

    info = CapabilityInfo(
        id="current_time",
        name="Current Time",
        description="Provides current time",
        status="active",
    )
    assert info.id == "current_time"
    assert info.is_mcp is False


def test_capability_info_full_fields():
    """Test CapabilityInfo with all fields."""
    from everruns_sdk import CapabilityInfo

    info = CapabilityInfo(
        id="web_fetch",
        name="Web Fetch",
        description="Fetch web pages",
        status="active",
        category="utilities",
        dependencies=["current_time"],
        icon="globe",
        is_mcp=True,
    )
    assert info.category == "utilities"
    assert info.dependencies == ["current_time"]
    assert info.icon == "globe"
    assert info.is_mcp is True


def test_create_agent_request_with_capabilities():
    """Test CreateAgentRequest serialization with capabilities."""
    from everruns_sdk.models import AgentCapabilityConfig, CreateAgentRequest

    req = CreateAgentRequest(
        name="Test Agent",
        system_prompt="You are helpful.",
        capabilities=[
            AgentCapabilityConfig(ref="current_time"),
            AgentCapabilityConfig(ref="web_fetch", config={"timeout": 30}),
        ],
    )
    data = req.model_dump(exclude_none=True)
    assert data["name"] == "Test Agent"
    assert len(data["capabilities"]) == 2
    assert data["capabilities"][0]["ref"] == "current_time"
    assert data["capabilities"][1]["ref"] == "web_fetch"
    assert data["capabilities"][1]["config"] == {"timeout": 30}


def test_create_agent_request_with_initial_files():
    """Test CreateAgentRequest serialization with initial_files."""
    from everruns_sdk.models import CreateAgentRequest

    req = CreateAgentRequest(
        name="Starter Agent",
        system_prompt="You keep files ready.",
        initial_files=[
            InitialFile(
                path="/workspace/README.md",
                content="# starter\n",
                encoding="text",
                is_readonly=True,
            )
        ],
    )
    data = req.model_dump(exclude_none=True)
    assert data["initial_files"] == [
        {
            "path": "/workspace/README.md",
            "content": "# starter\n",
            "encoding": "text",
            "is_readonly": True,
        }
    ]


def test_create_session_request_with_capabilities():
    """Test CreateSessionRequest serialization with capabilities."""
    from everruns_sdk.models import AgentCapabilityConfig, CreateSessionRequest

    req = CreateSessionRequest(
        harness_id="harness_abc123",
        agent_id="agent_123",
        capabilities=[AgentCapabilityConfig(ref="current_time")],
    )
    data = req.model_dump(exclude_none=True)
    assert data["harness_id"] == "harness_abc123"
    assert data["agent_id"] == "agent_123"
    assert len(data["capabilities"]) == 1
    assert data["capabilities"][0]["ref"] == "current_time"


def test_create_session_request_without_agent():
    """Test CreateSessionRequest without agent_id or harness_id."""
    from everruns_sdk.models import CreateSessionRequest

    req = CreateSessionRequest()
    data = req.model_dump(exclude_none=True)
    assert "harness_id" not in data
    assert "agent_id" not in data


def test_create_session_request_with_tags():
    """Test CreateSessionRequest with tags."""
    from everruns_sdk.models import CreateSessionRequest

    req = CreateSessionRequest(
        harness_id="harness_abc123",
        tags=["debug", "urgent"],
    )
    data = req.model_dump(exclude_none=True)
    assert data["tags"] == ["debug", "urgent"]


def test_create_session_request_with_locale():
    """Test CreateSessionRequest serialization with locale."""
    from everruns_sdk.models import CreateSessionRequest

    req = CreateSessionRequest(locale="uk-UA")
    data = req.model_dump(exclude_none=True)
    assert data["locale"] == "uk-UA"


def test_api_error_from_response_handles_string_error_body():
    """Test ApiError parsing when error payload is a string."""
    err = ApiError.from_response(400, {"error": "harness not found"})

    assert err.code == "unknown"
    assert err.message == "harness not found"
    assert err.status_code == 400


def test_agent_deserialization_with_capabilities():
    """Test Agent model deserialization with capabilities."""
    from everruns_sdk.models import Agent

    agent = Agent(
        id="agent_123",
        name="Test Agent",
        system_prompt="You are helpful.",
        status="active",
        capabilities=[{"ref": "current_time"}, {"ref": "web_fetch", "config": {"timeout": 30}}],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )
    assert len(agent.capabilities) == 2
    assert agent.capabilities[0].ref == "current_time"
    assert agent.capabilities[1].config == {"timeout": 30}


def test_agent_deserialization_without_capabilities():
    """Test Agent model backward compat without capabilities."""
    from everruns_sdk.models import Agent

    agent = Agent(
        id="agent_123",
        name="Test Agent",
        system_prompt="You are helpful.",
        status="active",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )
    assert agent.capabilities == []


def test_session_deserialization_with_capabilities():
    """Test Session model deserialization with capabilities."""
    from everruns_sdk.models import Session

    session = Session(
        id="session_456",
        organization_id="org_789",
        harness_id="harness_abc123",
        agent_id="agent_123",
        status="active",
        capabilities=[{"ref": "current_time"}],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )
    assert len(session.capabilities) == 1
    assert session.capabilities[0].ref == "current_time"
    assert session.harness_id == "harness_abc123"


def test_session_deserialization_without_agent():
    """Test Session model deserialization without agent_id."""
    from everruns_sdk.models import Session

    session = Session(
        id="session_456",
        organization_id="org_789",
        harness_id="harness_abc123",
        status="started",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )
    assert session.agent_id is None
    assert session.harness_id == "harness_abc123"


def test_session_waiting_for_tool_results_status():
    """Test Session with waitingfortoolresults status."""
    from everruns_sdk.models import Session

    session = Session(
        id="session_456",
        organization_id="org_789",
        harness_id="harness_abc123",
        status="waitingfortoolresults",
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )
    assert session.status == "waitingfortoolresults"


def test_generate_agent_id_format():
    """Test generate_agent_id returns proper format."""
    from everruns_sdk import generate_agent_id

    agent_id = generate_agent_id()
    assert agent_id.startswith("agent_")
    hex_part = agent_id[len("agent_") :]
    assert len(hex_part) == 32
    int(hex_part, 16)  # validates it's valid hex


def test_generate_agent_id_unique():
    """Test generate_agent_id returns unique values."""
    from everruns_sdk import generate_agent_id

    id1 = generate_agent_id()
    id2 = generate_agent_id()
    assert id1 != id2


def test_generate_harness_id_format():
    """Test generate_harness_id returns proper format."""
    from everruns_sdk import generate_harness_id

    harness_id = generate_harness_id()
    assert harness_id.startswith("harness_")
    hex_part = harness_id[len("harness_") :]
    assert len(hex_part) == 32
    int(hex_part, 16)  # validates it's valid hex


def test_generate_harness_id_unique():
    """Test generate_harness_id returns unique values."""
    from everruns_sdk import generate_harness_id

    id1 = generate_harness_id()
    id2 = generate_harness_id()
    assert id1 != id2


def test_create_agent_request_with_id():
    """Test CreateAgentRequest serialization with client-supplied ID."""
    from everruns_sdk.models import CreateAgentRequest, generate_agent_id

    agent_id = generate_agent_id()
    req = CreateAgentRequest(
        id=agent_id,
        name="Test Agent",
        system_prompt="You are helpful.",
    )
    data = req.model_dump(exclude_none=True)
    assert data["id"] == agent_id
    assert data["name"] == "Test Agent"


def test_create_agent_request_without_id():
    """Test CreateAgentRequest omits id when not set."""
    from everruns_sdk.models import CreateAgentRequest

    req = CreateAgentRequest(
        name="Test Agent",
        system_prompt="You are helpful.",
    )
    data = req.model_dump(exclude_none=True)
    assert "id" not in data


def test_external_actor_round_trip():
    """Test ExternalActor model round-trip."""
    from everruns_sdk import ExternalActor

    actor = ExternalActor(
        actor_id="U12345",
        source="slack",
        actor_name="Alice",
        metadata={"channel": "general"},
    )
    data = actor.model_dump()
    assert data["actor_id"] == "U12345"
    assert data["source"] == "slack"
    assert data["actor_name"] == "Alice"
    assert data["metadata"]["channel"] == "general"

    # Round-trip via JSON
    json_str = actor.model_dump_json()
    roundtrip = ExternalActor.model_validate_json(json_str)
    assert roundtrip.actor_id == "U12345"
    assert roundtrip.source == "slack"


def test_external_actor_minimal():
    """Test ExternalActor with only required fields."""
    from everruns_sdk import ExternalActor

    actor = ExternalActor(actor_id="bot1", source="discord")
    assert actor.actor_name is None
    assert actor.metadata is None


def test_message_with_external_actor_and_phase():
    """Test Message with external_actor and phase fields."""
    from everruns_sdk.models import ExternalActor, Message

    msg = Message(
        id="msg_123",
        session_id="session_456",
        sequence=1,
        role="user",
        content=[{"type": "text", "text": "hello"}],
        created_at="2024-01-01T00:00:00Z",
        external_actor=ExternalActor(actor_id="U99", source="slack"),
        phase="Commentary",
    )
    assert msg.external_actor.actor_id == "U99"
    assert msg.phase == "Commentary"


def test_message_without_external_actor():
    """Test Message without external_actor (backward compat)."""
    from everruns_sdk.models import Message

    msg = Message(
        id="msg_123",
        session_id="session_456",
        sequence=2,
        role="agent",
        content=[{"type": "text", "text": "hi"}],
        created_at="2024-01-01T00:00:00Z",
    )
    assert msg.external_actor is None
    assert msg.phase is None


def test_capability_info_with_risk_level():
    """Test CapabilityInfo with risk_level field."""
    from everruns_sdk.models import CapabilityInfo

    info = CapabilityInfo(
        id="shell_exec",
        name="Shell Exec",
        description="Execute shell commands",
        status="active",
        risk_level="high",
    )
    assert info.risk_level == "high"


def test_capability_info_without_risk_level():
    """Test CapabilityInfo without risk_level (backward compat)."""
    from everruns_sdk.models import CapabilityInfo

    info = CapabilityInfo(
        id="current_time",
        name="Current Time",
        description="Get current time",
        status="active",
    )
    assert info.risk_level is None


def test_create_message_request_with_external_actor():
    """Test CreateMessageRequest with external_actor."""
    from everruns_sdk.models import CreateMessageRequest, ExternalActor

    req = CreateMessageRequest(
        message={"role": "user", "content": [{"type": "text", "text": "hello"}]},
        external_actor=ExternalActor(actor_id="U12345", source="slack"),
    )
    data = req.model_dump(exclude_none=True)
    assert data["external_actor"]["actor_id"] == "U12345"


def test_create_message_request_without_external_actor():
    """Test CreateMessageRequest without external_actor omits it."""
    from everruns_sdk.models import CreateMessageRequest

    req = CreateMessageRequest(
        message={"role": "user", "content": [{"type": "text", "text": "hello"}]},
    )
    data = req.model_dump(exclude_none=True)
    assert "external_actor" not in data


@pytest.mark.asyncio
@respx.mock
async def test_create_session_with_initial_files():
    route = respx.post("https://custom.example.com/api/v1/sessions").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "session_123",
                "organization_id": "org_123",
                "harness_id": "harness_123",
                "agent_id": "agent_123",
                "title": "Session with files",
                "status": "started",
                "created_at": "2026-03-13T00:00:00Z",
                "updated_at": "2026-03-13T00:00:00Z",
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        session = await client.sessions.create(
            agent_id="agent_123",
            title="Session with files",
            model_id="model_123",
            initial_files=[
                InitialFile(
                    path="/workspace/README.md",
                    content="# hello\n",
                    encoding="text",
                    is_readonly=True,
                )
            ],
        )
    finally:
        await client.close()

    assert session.id == "session_123"
    assert route.called
    assert json.loads(route.calls[0].request.content) == {
        "agent_id": "agent_123",
        "title": "Session with files",
        "model_id": "model_123",
        "tags": [],
        "capabilities": [],
        "initial_files": [
            {
                "path": "/workspace/README.md",
                "content": "# hello\n",
                "encoding": "text",
                "is_readonly": True,
            }
        ],
    }


@pytest.mark.asyncio
@respx.mock
async def test_create_agent_with_initial_files():
    route = respx.post("https://custom.example.com/api/v1/agents").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "agent_123",
                "name": "Starter Agent",
                "system_prompt": "You keep files ready.",
                "initial_files": [
                    {
                        "path": "/workspace/README.md",
                        "content": "# starter\n",
                        "encoding": "text",
                        "is_readonly": True,
                    }
                ],
                "status": "active",
                "created_at": "2026-03-13T00:00:00Z",
                "updated_at": "2026-03-13T00:00:00Z",
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        agent = await client.agents.create(
            "Starter Agent",
            "You keep files ready.",
            initial_files=[
                InitialFile(
                    path="/workspace/README.md",
                    content="# starter\n",
                    encoding="text",
                    is_readonly=True,
                )
            ],
        )
    finally:
        await client.close()

    assert agent.id == "agent_123"
    assert route.called
    assert json.loads(route.calls[0].request.content)["initial_files"] == [
        {
            "path": "/workspace/README.md",
            "content": "# starter\n",
            "encoding": "text",
            "is_readonly": True,
        }
    ]


@pytest.mark.asyncio
@respx.mock
async def test_create_session_with_locale():
    route = respx.post("https://custom.example.com/api/v1/sessions").mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "session_456",
                "organization_id": "org_123",
                "harness_id": "harness_123",
                "title": "Localized session",
                "locale": "uk-UA",
                "status": "started",
                "created_at": "2026-03-13T00:00:00Z",
                "updated_at": "2026-03-13T00:00:00Z",
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        session = await client.sessions.create(title="Localized session", locale="uk-UA")
    finally:
        await client.close()

    assert session.id == "session_456"
    assert session.locale == "uk-UA"
    assert route.called
    assert json.loads(route.calls[0].request.content)["locale"] == "uk-UA"


# --- Session Files Tests ---

FILE_RESPONSE = {
    "id": "file_001",
    "session_id": "sess_123",
    "path": "/workspace/hello.txt",
    "name": "hello.txt",
    "is_directory": False,
    "is_readonly": False,
    "size_bytes": 5,
    "content": "hello",
    "encoding": "text",
    "created_at": "2026-03-20T00:00:00Z",
    "updated_at": "2026-03-20T00:00:00Z",
}


@pytest.mark.asyncio
@respx.mock
async def test_session_files_list():
    route = respx.get("https://custom.example.com/api/v1/sessions/sess_123/fs?recursive=true").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "file_001",
                        "session_id": "sess_123",
                        "path": "/workspace/hello.txt",
                        "name": "hello.txt",
                        "is_directory": False,
                        "is_readonly": False,
                        "size_bytes": 5,
                        "created_at": "2026-03-20T00:00:00Z",
                        "updated_at": "2026-03-20T00:00:00Z",
                    }
                ],
                "total": 1,
                "offset": 0,
                "limit": 100,
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        files = await client.session_files.list("sess_123", recursive=True)
    finally:
        await client.close()

    assert len(files) == 1
    assert files[0].name == "hello.txt"
    assert not files[0].is_directory
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_session_files_read():
    route = respx.get(
        "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/hello.txt"
    ).mock(return_value=httpx.Response(200, json=FILE_RESPONSE))

    client = Everruns(api_key="evr_test_key")
    try:
        file = await client.session_files.read("sess_123", "/workspace/hello.txt")
    finally:
        await client.close()

    assert file.content == "hello"
    assert file.encoding == "text"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_session_files_create():
    route = respx.post(
        "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/new.txt"
    ).mock(return_value=httpx.Response(201, json=FILE_RESPONSE))

    client = Everruns(api_key="evr_test_key")
    try:
        file = await client.session_files.create(
            "sess_123", "/workspace/new.txt", "hello", encoding="text"
        )
    finally:
        await client.close()

    assert file.name == "hello.txt"
    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["content"] == "hello"
    assert body["encoding"] == "text"


@pytest.mark.asyncio
@respx.mock
async def test_session_files_create_dir():
    route = respx.post(
        "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/subdir"
    ).mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "file_003",
                "session_id": "sess_123",
                "path": "/workspace/subdir",
                "name": "subdir",
                "is_directory": True,
                "is_readonly": False,
                "size_bytes": 0,
                "created_at": "2026-03-20T00:00:00Z",
                "updated_at": "2026-03-20T00:00:00Z",
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        file = await client.session_files.create_dir("sess_123", "/workspace/subdir")
    finally:
        await client.close()

    assert file.is_directory
    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["is_directory"] is True


@pytest.mark.asyncio
@respx.mock
async def test_session_files_update():
    route = respx.put(
        "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/hello.txt"
    ).mock(return_value=httpx.Response(200, json=FILE_RESPONSE))

    client = Everruns(api_key="evr_test_key")
    try:
        file = await client.session_files.update("sess_123", "/workspace/hello.txt", "hello")
    finally:
        await client.close()

    assert file.content == "hello"
    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["content"] == "hello"


@pytest.mark.asyncio
@respx.mock
async def test_session_files_delete():
    route = respx.delete(
        "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/hello.txt"
    ).mock(return_value=httpx.Response(200, json={"deleted": True}))

    client = Everruns(api_key="evr_test_key")
    try:
        resp = await client.session_files.delete("sess_123", "/workspace/hello.txt")
    finally:
        await client.close()

    assert resp.deleted
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_session_files_move():
    route = respx.post("https://custom.example.com/api/v1/sessions/sess_123/fs/_/move").mock(
        return_value=httpx.Response(200, json=FILE_RESPONSE)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        await client.session_files.move_file("sess_123", "/workspace/old.txt", "/workspace/new.txt")
    finally:
        await client.close()

    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["src_path"] == "/workspace/old.txt"
    assert body["dst_path"] == "/workspace/new.txt"


@pytest.mark.asyncio
@respx.mock
async def test_session_files_copy():
    route = respx.post("https://custom.example.com/api/v1/sessions/sess_123/fs/_/copy").mock(
        return_value=httpx.Response(201, json=FILE_RESPONSE)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        await client.session_files.copy_file(
            "sess_123", "/workspace/original.txt", "/workspace/copy.txt"
        )
    finally:
        await client.close()

    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["src_path"] == "/workspace/original.txt"
    assert body["dst_path"] == "/workspace/copy.txt"


@pytest.mark.asyncio
@respx.mock
async def test_session_files_grep():
    route = respx.post("https://custom.example.com/api/v1/sessions/sess_123/fs/_/grep").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "path": "/workspace/main.rs",
                        "matches": [
                            {
                                "path": "/workspace/main.rs",
                                "line_number": 10,
                                "line": "// TODO: fix this",
                            }
                        ],
                    }
                ],
                "total": 1,
                "offset": 0,
                "limit": 100,
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        results = await client.session_files.grep("sess_123", "TODO")
    finally:
        await client.close()

    assert len(results) == 1
    assert len(results[0].matches) == 1
    assert results[0].matches[0].line == "// TODO: fix this"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_session_files_stat():
    route = respx.post("https://custom.example.com/api/v1/sessions/sess_123/fs/_/stat").mock(
        return_value=httpx.Response(
            200,
            json={
                "path": "/workspace/hello.txt",
                "name": "hello.txt",
                "is_directory": False,
                "is_readonly": False,
                "size_bytes": 5,
                "created_at": "2026-03-20T00:00:00Z",
                "updated_at": "2026-03-20T00:00:00Z",
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        stat = await client.session_files.stat("sess_123", "/workspace/hello.txt")
    finally:
        await client.close()

    assert stat.name == "hello.txt"
    assert stat.size_bytes == 5
    assert not stat.is_directory
    assert route.called


def test_list_response_without_pagination_fields():
    """ListResponse deserializes when server omits total/offset/limit."""
    from everruns_sdk.models import ListResponse

    resp = ListResponse.model_validate({"data": [1, 2, 3]})
    assert resp.data == [1, 2, 3]
    assert resp.total == 0
    assert resp.offset == 0
    assert resp.limit == 0


def test_list_response_with_pagination_fields():
    """ListResponse deserializes when server includes total/offset/limit."""
    from everruns_sdk.models import ListResponse

    resp = ListResponse.model_validate({"data": ["a"], "total": 10, "offset": 5, "limit": 25})
    assert resp.data == ["a"]
    assert resp.total == 10
    assert resp.offset == 5
    assert resp.limit == 25
