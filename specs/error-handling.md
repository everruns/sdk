# Error Handling

## Error Response Format

```json
{
  "error": {
    "code": "not_found",
    "message": "Agent not found"
  }
}
```

## HTTP Status Codes

- `400` - Bad request (validation error)
- `401` - Unauthorized (invalid/missing API key)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `422` - Unprocessable entity (business logic error)
- `429` - Rate limited
- `500` - Internal server error

## SDK Error Types

### Rust

```rust
pub enum Error {
    Api(ApiError),
    Network(reqwest::Error),
    Auth(AuthError),
    Timeout,
}
```

### Python

```python
class EverrunsError(Exception): ...
class ApiError(EverrunsError): ...
class AuthenticationError(EverrunsError): ...
class NotFoundError(ApiError): ...
class RateLimitError(ApiError): ...
```

### TypeScript

```typescript
class EverrunsError extends Error {}
class ApiError extends EverrunsError {}
class AuthenticationError extends EverrunsError {}
class NotFoundError extends ApiError {}
class RateLimitError extends ApiError {}
```

## HTML Response Handling

When the API returns an HTML response instead of JSON (e.g., from a reverse proxy 404 page), SDKs simplify the error message to avoid verbose HTML in error output.

Detection: Response body starting with `<!DOCTYPE` or `<html` (case-insensitive).

Behavior:
- Rust: Sets message to `"HTTP {status}"` instead of raw HTML
- Python: Sets message to `"HTTP {status}"` instead of raw HTML
- TypeScript: Omits the body from ApiError instead of including raw HTML

## Retry Strategy

- Retry on 429 (rate limit) with Retry-After header
- Retry on 5xx with exponential backoff
- Do not retry on 4xx (except 429)
