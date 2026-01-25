"""Authentication utilities for Everruns SDK."""

import os


class ApiKey:
    """API key for authenticating with Everruns.
    
    Args:
        key: The API key string (should start with 'evr_')
    """
    
    def __init__(self, key: str):
        if not key:
            raise ValueError("API key cannot be empty")
        self._key = key
    
    @classmethod
    def from_env(cls, env_var: str = "EVERRUNS_API_KEY") -> "ApiKey":
        """Create an API key from an environment variable.
        
        Args:
            env_var: Name of the environment variable
            
        Returns:
            ApiKey instance
            
        Raises:
            ValueError: If the environment variable is not set
        """
        key = os.environ.get(env_var)
        if not key:
            raise ValueError(f"Environment variable {env_var} is not set")
        return cls(key)
    
    @property
    def value(self) -> str:
        """Get the API key value."""
        return self._key
    
    def __repr__(self) -> str:
        if len(self._key) > 8:
            return f"ApiKey({self._key[:8]}...)"
        return "ApiKey(***)"
