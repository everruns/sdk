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
