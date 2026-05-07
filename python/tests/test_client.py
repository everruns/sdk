"""Tests for Everruns SDK client."""

import json
import os

import httpx
import pytest
import respx

from everruns_sdk import (
    ApiError,
    ApiKey,
    ContentPart,
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


def test_create_agent_request_with_tools():
    """Test CreateAgentRequest serialization with client-side tools."""
    from everruns_sdk.models import CreateAgentRequest, ToolDefinition

    req = CreateAgentRequest(
        name="test-agent",
        system_prompt="You are helpful.",
        tools=[
            ToolDefinition(
                name="get_weather",
                description="Get weather",
                parameters={"type": "object"},
            )
        ],
    )
    data = req.model_dump(exclude_none=True)
    assert data["tools"][0]["type"] == "client_side"
    assert data["tools"][0]["name"] == "get_weather"


def test_create_agent_request_with_initial_files():
    """Test CreateAgentRequest serialization with initial_files."""
    from everruns_sdk.models import CreateAgentRequest

    req = CreateAgentRequest(
        name="starter-agent",
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


def test_extract_tool_calls_from_requested_event():
    """Test extracting tool calls from tool.call_requested data."""
    from everruns_sdk import extract_tool_calls

    calls = extract_tool_calls(
        {
            "tool_calls": [
                {
                    "id": "call_123",
                    "name": "get_weather",
                    "arguments": {"city": "Paris"},
                }
            ]
        }
    )
    assert len(calls) == 1
    assert calls[0].id == "call_123"
    assert calls[0].name == "get_weather"
    assert calls[0].arguments == {"city": "Paris"}


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


def test_validate_harness_name_valid():
    """Test validate_harness_name accepts valid names."""
    from everruns_sdk import validate_harness_name

    validate_harness_name("generic")
    validate_harness_name("deep-research")
    validate_harness_name("my-harness-v2")
    validate_harness_name("a1b2")
    validate_harness_name("x")


def test_validate_harness_name_too_long():
    """Test validate_harness_name rejects names over 64 chars."""
    from everruns_sdk import validate_harness_name

    with pytest.raises(ValueError, match="at most 64 characters"):
        validate_harness_name("a" * 65)


def test_validate_harness_name_invalid_pattern():
    """Test validate_harness_name rejects invalid patterns."""
    from everruns_sdk import validate_harness_name

    with pytest.raises(ValueError, match="must match pattern"):
        validate_harness_name("UPPER")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_harness_name("has_underscore")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_harness_name("-leading-dash")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_harness_name("trailing-dash-")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_harness_name("double--dash")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_harness_name("")


def test_create_session_request_with_harness_name():
    """Test CreateSessionRequest serialization with harness_name."""
    from everruns_sdk.models import CreateSessionRequest

    req = CreateSessionRequest(harness_name="deep-research")
    data = req.model_dump(exclude_none=True)
    assert data["harness_name"] == "deep-research"
    assert "harness_id" not in data


def test_create_session_request_harness_name_and_id_both():
    """Test that both harness_id and harness_name can be set on the model."""
    from everruns_sdk.models import CreateSessionRequest

    # Both can be set on the model (validation is in the client)
    req = CreateSessionRequest(harness_id="harness_abc", harness_name="generic")
    data = req.model_dump(exclude_none=True)
    assert "harness_id" in data
    assert "harness_name" in data


def test_validate_agent_name_valid():
    """Test validate_agent_name accepts valid names."""
    from everruns_sdk import validate_agent_name

    validate_agent_name("customer-support")
    validate_agent_name("my-agent-v2")
    validate_agent_name("a1b2")
    validate_agent_name("x")


def test_validate_agent_name_too_long():
    """Test validate_agent_name rejects names over 64 chars."""
    from everruns_sdk import validate_agent_name

    with pytest.raises(ValueError, match="at most 64 characters"):
        validate_agent_name("a" * 65)


def test_validate_agent_name_invalid_pattern():
    """Test validate_agent_name rejects invalid patterns."""
    from everruns_sdk import validate_agent_name

    with pytest.raises(ValueError, match="must match pattern"):
        validate_agent_name("UPPER")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_agent_name("has_underscore")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_agent_name("-leading-dash")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_agent_name("trailing-dash-")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_agent_name("double--dash")
    with pytest.raises(ValueError, match="must match pattern"):
        validate_agent_name("")


def test_create_agent_request_with_display_name():
    """Test CreateAgentRequest serialization with display_name."""
    from everruns_sdk.models import CreateAgentRequest

    req = CreateAgentRequest(
        name="customer-support",
        display_name="Customer Support Agent",
        system_prompt="You are helpful.",
    )
    data = req.model_dump(exclude_none=True)
    assert data["name"] == "customer-support"
    assert data["display_name"] == "Customer Support Agent"


def test_create_agent_request_without_display_name():
    """Test CreateAgentRequest omits display_name when not set."""
    from everruns_sdk.models import CreateAgentRequest

    req = CreateAgentRequest(
        name="customer-support",
        system_prompt="You are helpful.",
    )
    data = req.model_dump(exclude_none=True)
    assert "display_name" not in data


def test_create_agent_request_with_id():
    """Test CreateAgentRequest serialization with client-supplied ID."""
    from everruns_sdk.models import CreateAgentRequest, generate_agent_id

    agent_id = generate_agent_id()
    req = CreateAgentRequest(
        id=agent_id,
        name="test-agent",
        system_prompt="You are helpful.",
    )
    data = req.model_dump(exclude_none=True)
    assert data["id"] == agent_id
    assert data["name"] == "test-agent"


def test_create_agent_request_without_id():
    """Test CreateAgentRequest omits id when not set."""
    from everruns_sdk.models import CreateAgentRequest

    req = CreateAgentRequest(
        name="test-agent",
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
        "tools": [],
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
                "name": "starter-agent",
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
            "starter-agent",
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


@pytest.mark.asyncio
@respx.mock
async def test_import_agent_from_example():
    route = respx.post(
        "https://custom.example.com/api/v1/agents/import?from-example=dad-jokes-agent"
    ).mock(
        return_value=httpx.Response(
            201,
            json={
                "id": "agent_123",
                "name": "dad-jokes-agent",
                "description": "Cracks jokes",
                "system_prompt": "Tell dad jokes.",
                "default_model_id": None,
                "tags": [],
                "capabilities": [],
                "initial_files": [],
                "status": "active",
                "created_at": "2026-04-15T00:00:00Z",
                "updated_at": "2026-04-15T00:00:00Z",
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        agent = await client.agents.import_example("dad-jokes-agent")
    finally:
        await client.close()

    assert agent.name == "dad-jokes-agent"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_agent_stats():
    route = respx.get("https://custom.example.com/api/v1/agents/agent_123/stats").mock(
        return_value=httpx.Response(
            200,
            json={
                "session_count": 4,
                "active_session_count": 1,
                "idle_session_count": 2,
                "started_session_count": 1,
                "waiting_for_tool_results_session_count": 0,
                "execution_count": 7,
                "total_session_duration_ms": 12345,
                "avg_session_duration_ms": 3086,
                "total_input_tokens": 100,
                "total_output_tokens": 50,
                "total_cache_read_tokens": 25,
                "total_cache_creation_tokens": 10,
                "first_session_at": "2026-05-01T00:00:00Z",
                "last_session_at": "2026-05-02T00:00:00Z",
                "last_execution_at": "2026-05-02T01:00:00Z",
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        stats = await client.agents.stats("agent_123")
    finally:
        await client.close()

    assert stats.session_count == 4
    assert stats.execution_count == 7
    assert stats.avg_session_duration_ms == 3086
    assert stats.total_input_tokens == 100
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_capabilities_list_with_options():
    route = respx.get(
        "https://custom.example.com/api/v1/capabilities?search=web&offset=20&limit=10"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "web_search",
                        "name": "web_search",
                        "description": "Search the web",
                        "status": "active",
                    }
                ],
                "total": 21,
                "offset": 20,
                "limit": 10,
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        page = await client.capabilities.list_page(search="web", offset=20, limit=10)
        items = await client.capabilities.list(search="web", offset=20, limit=10)
    finally:
        await client.close()

    assert page.total == 21
    assert page.offset == 20
    assert page.limit == 10
    assert len(items) == 1
    assert items[0].id == "web_search"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_create_tool_results_uses_tool_results_endpoint():
    route = respx.post("https://custom.example.com/api/v1/sessions/session_123/tool-results").mock(
        return_value=httpx.Response(
            200,
            json={
                "accepted": 1,
                "status": "active",
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        response = await client.messages.create_tool_results(
            session_id="session_123",
            results=[ContentPart.make_tool_result("call_123", {"weather": "sunny"})],
        )
    finally:
        await client.close()

    assert response.accepted == 1
    assert response.status == "active"
    assert route.called
    assert json.loads(route.calls[0].request.content) == {
        "tool_results": [
            {
                "tool_call_id": "call_123",
                "result": {"weather": "sunny"},
            }
        ]
    }


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


# --- Connections Tests ---

CONN_RESPONSE = {
    "provider": "daytona",
    "created_at": "2026-03-31T00:00:00Z",
    "updated_at": "2026-03-31T00:00:00Z",
}


@pytest.mark.asyncio
@respx.mock
async def test_connections_set():
    route = respx.post("https://custom.example.com/api/v1/user/connections/daytona").mock(
        return_value=httpx.Response(200, json=CONN_RESPONSE)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        conn = await client.connections.set("daytona", "dtn_secret_key")
    finally:
        await client.close()

    assert conn.provider == "daytona"
    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["api_key"] == "dtn_secret_key"


@pytest.mark.asyncio
@respx.mock
async def test_connections_list():
    route = respx.get("https://custom.example.com/api/v1/user/connections").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [CONN_RESPONSE],
                "total": 1,
                "offset": 0,
                "limit": 100,
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        connections = await client.connections.list()
    finally:
        await client.close()

    assert len(connections) == 1
    assert connections[0].provider == "daytona"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_connections_remove():
    route = respx.delete("https://custom.example.com/api/v1/user/connections/daytona").mock(
        return_value=httpx.Response(204)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        await client.connections.remove("daytona")
    finally:
        await client.close()

    assert route.called


# --- Session Secrets Tests ---


@pytest.mark.asyncio
@respx.mock
async def test_session_set_secrets():
    route = respx.put("https://custom.example.com/api/v1/sessions/sess_123/storage/secrets").mock(
        return_value=httpx.Response(200, json={})
    )

    client = Everruns(api_key="evr_test_key")
    try:
        await client.sessions.set_secrets(
            "sess_123",
            {"OPENAI_API_KEY": "sk-abc123", "DB_PASSWORD": "hunter2"},
        )
    finally:
        await client.close()

    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["secrets"]["OPENAI_API_KEY"] == "sk-abc123"
    assert body["secrets"]["DB_PASSWORD"] == "hunter2"


@pytest.mark.asyncio
@respx.mock
async def test_session_set_secrets_empty():
    route = respx.put("https://custom.example.com/api/v1/sessions/sess_123/storage/secrets").mock(
        return_value=httpx.Response(200, json={})
    )

    client = Everruns(api_key="evr_test_key")
    try:
        await client.sessions.set_secrets("sess_123", {})
    finally:
        await client.close()

    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["secrets"] == {}


# --- Budget Tests ---

BUDGET_RESPONSE = {
    "id": "bdgt_001",
    "organization_id": "org_123",
    "subject_type": "session",
    "subject_id": "sess_123",
    "currency": "usd",
    "limit": 10.0,
    "soft_limit": 8.0,
    "balance": 10.0,
    "status": "active",
    "created_at": "2026-04-01T00:00:00Z",
    "updated_at": "2026-04-01T00:00:00Z",
}


@pytest.mark.asyncio
@respx.mock
async def test_budgets_create():
    route = respx.post("https://custom.example.com/api/v1/budgets").mock(
        return_value=httpx.Response(201, json=BUDGET_RESPONSE)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        budget = await client.budgets.create("session", "sess_123", "usd", 10.0, soft_limit=8.0)
    finally:
        await client.close()

    assert budget.id == "bdgt_001"
    assert budget.balance == 10.0
    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["subject_type"] == "session"
    assert body["limit"] == 10.0
    assert body["soft_limit"] == 8.0


@pytest.mark.asyncio
@respx.mock
async def test_budgets_get():
    route = respx.get("https://custom.example.com/api/v1/budgets/bdgt_001").mock(
        return_value=httpx.Response(200, json=BUDGET_RESPONSE)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        budget = await client.budgets.get("bdgt_001")
    finally:
        await client.close()

    assert budget.id == "bdgt_001"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_budgets_list():
    route = respx.get("https://custom.example.com/api/v1/budgets?subject_type=session").mock(
        return_value=httpx.Response(200, json=[BUDGET_RESPONSE])
    )

    client = Everruns(api_key="evr_test_key")
    try:
        budgets = await client.budgets.list(subject_type="session")
    finally:
        await client.close()

    assert len(budgets) == 1
    assert budgets[0].id == "bdgt_001"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_budgets_update():
    updated = {**BUDGET_RESPONSE, "limit": 20.0}
    route = respx.patch("https://custom.example.com/api/v1/budgets/bdgt_001").mock(
        return_value=httpx.Response(200, json=updated)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        budget = await client.budgets.update("bdgt_001", limit=20.0)
    finally:
        await client.close()

    assert budget.limit == 20.0
    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["limit"] == 20.0


@pytest.mark.asyncio
@respx.mock
async def test_budgets_delete():
    route = respx.delete("https://custom.example.com/api/v1/budgets/bdgt_001").mock(
        return_value=httpx.Response(204)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        await client.budgets.delete("bdgt_001")
    finally:
        await client.close()

    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_budgets_top_up():
    topped_up = {**BUDGET_RESPONSE, "balance": 15.0}
    route = respx.post("https://custom.example.com/api/v1/budgets/bdgt_001/top-up").mock(
        return_value=httpx.Response(200, json=topped_up)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        budget = await client.budgets.top_up("bdgt_001", 5.0, description="manual")
    finally:
        await client.close()

    assert budget.balance == 15.0
    assert route.called
    body = json.loads(route.calls[0].request.content)
    assert body["amount"] == 5.0
    assert body["description"] == "manual"


@pytest.mark.asyncio
@respx.mock
async def test_budgets_ledger():
    route = respx.get("https://custom.example.com/api/v1/budgets/bdgt_001/ledger?limit=10").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": "le_001",
                    "budget_id": "bdgt_001",
                    "amount": 2.5,
                    "meter_source": "llm_tokens",
                    "created_at": "2026-04-01T00:00:00Z",
                }
            ],
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        entries = await client.budgets.ledger("bdgt_001", limit=10)
    finally:
        await client.close()

    assert len(entries) == 1
    assert entries[0].amount == 2.5
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_budgets_check():
    route = respx.get("https://custom.example.com/api/v1/budgets/bdgt_001/check").mock(
        return_value=httpx.Response(200, json={"action": "continue"})
    )

    client = Everruns(api_key="evr_test_key")
    try:
        result = await client.budgets.check("bdgt_001")
    finally:
        await client.close()

    assert result.action == "continue"
    assert route.called


# --- Session Budget Shortcuts Tests ---


@pytest.mark.asyncio
@respx.mock
async def test_session_budgets():
    route = respx.get("https://custom.example.com/api/v1/sessions/sess_123/budgets").mock(
        return_value=httpx.Response(200, json=[BUDGET_RESPONSE])
    )

    client = Everruns(api_key="evr_test_key")
    try:
        budgets = await client.sessions.budgets("sess_123")
    finally:
        await client.close()

    assert len(budgets) == 1
    assert budgets[0].id == "bdgt_001"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_session_budget_check():
    route = respx.get("https://custom.example.com/api/v1/sessions/sess_123/budget-check").mock(
        return_value=httpx.Response(
            200,
            json={
                "action": "warn",
                "message": "Budget running low",
                "budget_id": "bdgt_001",
                "balance": 1.5,
                "currency": "usd",
            },
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        result = await client.sessions.budget_check("sess_123")
    finally:
        await client.close()

    assert result.action == "warn"
    assert result.balance == 1.5
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_session_resume():
    route = respx.post("https://custom.example.com/api/v1/sessions/sess_123/resume").mock(
        return_value=httpx.Response(
            200,
            json={"resumed_budgets": 2, "session_id": "sess_123"},
        )
    )

    client = Everruns(api_key="evr_test_key")
    try:
        result = await client.sessions.resume("sess_123")
    finally:
        await client.close()

    assert result.resumed_budgets == 2
    assert result.session_id == "sess_123"
    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_session_export():
    jsonl = (
        '{"id":"msg_001","session_id":"sess_123","sequence":1,"role":"user",'
        '"content":[{"type":"text","text":"hello"}],"created_at":"2024-01-15T10:30:00.000Z"}\n'
        '{"id":"msg_002","session_id":"sess_123","sequence":2,"role":"agent",'
        '"content":[{"type":"text","text":"hi"}],"created_at":"2024-01-15T10:30:01.000Z"}\n'
    )
    route = respx.get("https://custom.example.com/api/v1/sessions/sess_123/export").mock(
        return_value=httpx.Response(200, text=jsonl)
    )

    client = Everruns(api_key="evr_test_key")
    try:
        result = await client.sessions.export("sess_123")
    finally:
        await client.close()

    assert "msg_001" in result
    assert "msg_002" in result
    assert route.called


def test_budget_model():
    """Test Budget model deserialization."""
    from everruns_sdk import Budget

    budget = Budget(**BUDGET_RESPONSE)
    assert budget.id == "bdgt_001"
    assert budget.subject_type == "session"
    assert budget.currency == "usd"
    assert budget.limit == 10.0
    assert budget.soft_limit == 8.0
    assert budget.balance == 10.0
    assert budget.status == "active"


def test_budget_model_without_optional_fields():
    """Test Budget model without optional fields."""
    from everruns_sdk import Budget

    budget = Budget(
        id="bdgt_001",
        organization_id="org_123",
        subject_type="session",
        subject_id="sess_123",
        currency="usd",
        limit=10.0,
        balance=10.0,
        status="active",
        created_at="2026-04-01T00:00:00Z",
        updated_at="2026-04-01T00:00:00Z",
    )
    assert budget.soft_limit is None
    assert budget.period is None
    assert budget.metadata is None
