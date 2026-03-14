"""Tests for Everruns SDK client."""

import json
import os

import httpx
import pytest
import respx

from everruns_sdk import ApiKey, Everruns, InitialFile


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
