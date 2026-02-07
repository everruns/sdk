# SDK Features Specification

Language-agnostic requirements for all Everruns SDKs.

## Overview

Everruns SDKs provide typed clients for the Everruns API. All language implementations must follow these specifications to ensure consistent behavior and developer experience.

## Client Initialization

### Parameters

| Parameter | Env Variable | Description |
|-----------|--------------|-------------|
| `api_key` | `EVERRUNS_API_KEY` | API key |
| `api_url` | `EVERRUNS_API_URL` | API base URL (optional, for testing/self-hosted) |

All parameters can be omitted if the corresponding environment variable is set.

### Initialization Patterns

```
# From environment (recommended) - api_key from env var
client = Everruns()

# Explicit API key
client = Everruns(api_key="evr_...")

# Custom base URL
client = Everruns(api_url="https://custom.example.com/api")
```

## Resource Sub-Clients

SDKs expose resource-specific sub-clients for better ergonomics:

| Sub-Client | Operations |
|------------|------------|
| `client.agents` | CRUD for agents, import/export |
| `client.sessions` | CRUD for sessions, cancel turn |
| `client.messages` | Create/list messages |
| `client.events` | List events, SSE streaming |
| `client.capabilities` | List/get available capabilities |

## Core Features

### 1. Type Safety

- All API request/response types auto-generated from OpenAPI
- Strongly typed in all languages (generics, type hints, interfaces)
- No `any` types in public API surface
- **All output/response types must be serializable** (for caching, logging, persistence)
  - Rust: Derive `Serialize` + `Deserialize`
  - Python: Support `json.dumps()` via Pydantic or dataclasses
  - TypeScript: Plain objects serializable with `JSON.stringify()`

### 2. Async-First Design

| Language | Async Pattern |
|----------|---------------|
| Rust | `async fn` with tokio runtime |
| Python | `async/await` with asyncio |
| TypeScript | `Promise`-based, async/await |

**Note:** Sync wrappers are NOT required for v1.

### 3. SSE Streaming

Real-time event streaming via Server-Sent Events:

- Auto-reconnection with exponential backoff (1s, 2s, 4s, ... max 30s)
- Resume from `since_id` after disconnect
- Event filtering via `exclude` parameter
- Iterator/stream interface (language-appropriate)

### 4. Error Handling

Typed error hierarchy:

```
EverrunsError (base)
├── ApiError (HTTP errors with status code)
│   ├── NotFoundError (404)
│   ├── RateLimitError (429)
│   └── ValidationError (400, 422)
├── AuthenticationError (401)
└── NetworkError (connection failures)
```

### 5. Retry Behavior

| Condition | Action |
|-----------|--------|
| 429 Rate Limited | Retry with `Retry-After` header |
| 5xx Server Error | Retry with exponential backoff |
| 4xx Client Error | No retry (except 429) |
| Network Error | Retry with exponential backoff |

Max retries: 3. Max backoff: 30s.

### 6. Timeout Configuration

Default timeout: 30 seconds.

SDKs should allow per-request timeout override where language idioms support it.

## Capabilities

Capabilities add tools and system prompt modifications to agents and sessions.

### AgentCapabilityConfig

| Field | Type | Description |
|-------|------|-------------|
| `ref` | string (required) | Capability ID (e.g., `"current_time"`, `"web_fetch"`) |
| `config` | object (optional) | Per-agent configuration for the capability |

### Setting Capabilities

Capabilities can be set at both agent and session level:

```
# On agent creation
agent = client.agents.create("Assistant", "You are helpful.",
    capabilities=[{ref: "current_time"}, {ref: "web_fetch"}])

# On session creation (additive to agent capabilities)
session = client.sessions.create(agent_id,
    capabilities=[{ref: "current_time"}])
```

### Listing Capabilities

```
# List all available capabilities
capabilities = client.capabilities.list()

# Get a specific capability
capability = client.capabilities.get("current_time")
```

### CapabilityInfo

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Capability identifier |
| `name` | string | Display name |
| `description` | string | What the capability provides |
| `status` | string | Current status |
| `category` | string? | Category for grouping |
| `dependencies` | string[] | IDs of dependent capabilities |
| `is_mcp` | bool | Whether this is an MCP server capability |

## Agent Import/Export

### Import

Import an agent from Markdown (with YAML front matter), pure YAML, JSON, or plain text:

```
# Import from markdown
agent = client.agents.import("---\nname: Assistant\n---\nYou are helpful.")

# Import plain text (treated as system prompt)
agent = client.agents.import("You are a helpful assistant.")
```

- Content-Type: `text/plain`
- Returns: `Agent` object

### Export

Export an agent as Markdown with YAML front matter:

```
markdown = client.agents.export(agent_id)
```

- Returns: string (Markdown with YAML front matter)

## Agent ID Generation

SDKs provide a helper to generate properly formatted agent IDs:

| Language | Function |
|----------|----------|
| Rust | `generate_agent_id()` |
| Python | `generate_agent_id()` |
| TypeScript | `generateAgentId()` |

IDs follow the format `agent_<32-hex>` (16 random bytes, hex-encoded).

## Convenience Methods

### Simple Create Methods

Each resource supports both simple and full-options creation:

```
# Simple create (server-assigned ID)
agent = client.agents.create("Assistant", "You are helpful.")

# Full options (may include client-supplied ID)
agent = client.agents.create_with_options(CreateAgentRequest(...))
```

### Agent Upsert (apply)

`apply` creates or updates an agent with a client-supplied ID.
If the agent exists, it is updated; if not, it is created with that ID.

```
# Generate a stable ID
id = generate_agent_id()

# Upsert — safe to call repeatedly
agent = client.agents.apply(id, "Assistant", "You are helpful.")
```

This is useful for declarative agent management where the caller controls identity.
Callers that don't need stable IDs should use `create` instead.

### Text Message Shorthand

```
# Simple text message
message = client.messages.create(session_id, "Hello!")

# Full multimodal message
message = client.messages.create_with_options(session_id, CreateMessageRequest(...))
```

## Pagination

List endpoints return offset-based paginated responses:

```json
{
  "data": [...],
  "total": 100,
  "offset": 0,
  "limit": 20
}
```

SDKs must support:
- `offset` parameter (number of items to skip)
- `limit` parameter (max items per page, default: 20)
- Helper for iterating all pages (nice-to-have for v1)

## Logging & Debugging

### Debug Mode

SDKs should support debug logging via environment variable:

```
EVERRUNS_DEBUG=1
```

When enabled, log:
- HTTP request method, URL, headers (redact auth)
- HTTP response status, timing
- SSE connection events

### Request IDs

All API responses include `X-Request-Id` header. SDKs should:
- Expose request ID on error objects
- Log request ID in debug mode

## Resource Cleanup

### Context Managers / RAII

| Language | Pattern |
|----------|---------|
| Rust | `Drop` trait, or explicit `.close()` |
| Python | `async with client:` context manager |
| TypeScript | Explicit `.close()` method |

SDKs must properly close HTTP clients and SSE connections.

## API Key Security

- Never log API keys
- Mask keys in debug output (`evr_****...`)
- Store internally with minimal exposure
- Rust: Use `secrecy` crate or similar

## HTTP Client Requirements

| Requirement | Details |
|-------------|---------|
| HTTP/2 | Preferred where available |
| Keep-alive | Connection pooling |
| Compression | Accept gzip/br responses |
| User-Agent | `everruns-{lang}-sdk/{version}` |

## Version Headers

All requests include:

```
X-SDK-Version: everruns-rust-sdk/0.1.0
User-Agent: everruns-rust-sdk/0.1.0
```

## Testing Requirements

- Unit tests for all public methods
- Integration tests against mock server
- Examples that compile/run successfully

## Documentation Requirements

- README with quick start
- API docs generated from code (rustdoc, pydoc, typedoc)
- At least one runnable example

## Non-Goals (v1)

These are explicitly out of scope for initial release:

- Sync client wrappers
- Automatic pagination iteration
- Request caching
- Offline mode
