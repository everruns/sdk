"""Tests for Everruns SDK client."""

import os

import pytest

from everruns_sdk import ApiKey, Everruns


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
        agent_id="agent_123",
        capabilities=[AgentCapabilityConfig(ref="current_time")],
    )
    data = req.model_dump(exclude_none=True)
    assert data["agent_id"] == "agent_123"
    assert len(data["capabilities"]) == 1
    assert data["capabilities"][0]["ref"] == "current_time"


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
        agent_id="agent_123",
        status="active",
        capabilities=[{"ref": "current_time"}],
        created_at="2024-01-01T00:00:00Z",
        updated_at="2024-01-01T00:00:00Z",
    )
    assert len(session.capabilities) == 1
    assert session.capabilities[0].ref == "current_time"
