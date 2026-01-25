"""Error types for Everruns SDK."""

from typing import Optional


class EverrunsError(Exception):
    """Base exception for Everruns SDK errors."""
    pass


class ApiError(EverrunsError):
    """Error returned by the Everruns API.
    
    Attributes:
        code: Error code from the API
        message: Human-readable error message
        status_code: HTTP status code
    """
    
    def __init__(self, code: str, message: str, status_code: int):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(f"{code}: {message}")
    
    @classmethod
    def from_response(cls, status_code: int, body: dict) -> "ApiError":
        """Create an ApiError from an API response."""
        error = body.get("error", {})
        code = error.get("code", "unknown")
        message = error.get("message", str(body))
        
        # Return specific error types for common status codes
        if status_code == 401:
            return AuthenticationError(code, message, status_code)
        elif status_code == 404:
            return NotFoundError(code, message, status_code)
        elif status_code == 429:
            return RateLimitError(code, message, status_code)
        
        return cls(code, message, status_code)


class AuthenticationError(ApiError):
    """Authentication failed (401)."""
    pass


class NotFoundError(ApiError):
    """Resource not found (404)."""
    pass


class RateLimitError(ApiError):
    """Rate limit exceeded (429)."""
    pass
