"""Authentication utilities for Everruns SDK."""

import os


class ApiKey:
    """Personal access token for authenticating with Everruns.

    Args:
        key: The token string (should start with 'evr_pat_')
    """

    def __init__(self, key: str):
        if not key:
            raise ValueError("personal access token cannot be empty")
        self._key = key

    @classmethod
    def from_env(cls, env_var: str = "EVERRUNS_API_KEY") -> "ApiKey":
        """Create a personal access token from an environment variable.

        Args:
            env_var: Name of the environment variable

        Returns:
            ApiKey instance wrapping a personal access token

        Raises:
            ValueError: If the environment variable is not set
        """
        key = os.environ.get(env_var)
        if not key:
            raise ValueError(f"Environment variable {env_var} is not set")
        return cls(key)

    @property
    def value(self) -> str:
        """Get the token value."""
        return self._key

    def __repr__(self) -> str:
        if len(self._key) > 8:
            return f"ApiKey({self._key[:8]}...)"
        return "ApiKey(***)"
