# API Surface

## Scope

SDKs cover agents and sessions functionality. No durable execution endpoints.

## Covered Endpoints

### Agents
- `POST /v1/agents` - Create agent (server-assigned ID) or upsert with client-supplied ID
- `GET /v1/agents` - List agents (supports `search` query param)
- `GET /v1/agents/{id}` - Get agent
- `PATCH /v1/agents/{id}` - Update agent
- `DELETE /v1/agents/{id}` - Archive agent
- `POST /v1/agents/import` - Import agent from Markdown/YAML/JSON/text or built-in example via `from-example`
- `GET /v1/agents/{id}/export` - Export agent as Markdown
- `POST /v1/agents/{id}/copy` - Copy an agent
- `GET /v1/agents/{id}/stats` - Get aggregate usage stats for an agent

#### Agent Names

Agent `name` is a URL/CLI-friendly addressable slug, **unique per org**.
Must match `[a-z0-9]+(-[a-z0-9]+)*`, max 64 characters (same rules as harness names).
Client-side validated via `validate_agent_name()`.

The optional `display_name` field provides a human-readable label for UI rendering
(e.g. `"Customer Support Agent"`). Falls back to `name` when absent.

#### Upsert Semantics

`POST /v1/agents` supports two upsert modes:

- **By ID**: When `id` is provided (format: `agent_<32-hex>`), if an agent with that ID
  exists it is updated, otherwise a new agent is created. All SDKs expose `apply()`.
- **By name**: When `name` matches an existing agent in the org, that agent is updated.
  All SDKs expose `apply_by_name()` / `applyByName()`.

When `id` is omitted, the server auto-generates one (plain create).
Agent create/update payloads also support optional `initial_files` starter files that are copied into each new session for that agent.

### Sessions
- `POST /v1/sessions` - Create session (harness_id optional, defaults to Generic harness)
- `GET /v1/sessions` - List sessions (supports `search` query param)
  Request supports optional `agent_id` search filtering.
- `GET /v1/sessions/{id}` - Get session
- `PATCH /v1/sessions/{id}` - Update session
- `DELETE /v1/sessions/{id}` - Delete session
- `POST /v1/sessions/{id}/cancel` - Cancel turn
- `PUT /v1/sessions/{id}/pin` - Pin session for current user
- `DELETE /v1/sessions/{id}/pin` - Unpin session for current user
- `GET /v1/sessions/{id}/export` - Export session messages as JSONL

#### Harness Identification

Sessions accept harness identification via one of two parameters (mutually exclusive):

- **`harness_name`** (preferred): Human-readable name like `generic` or `deep-research`.
  Must match `[a-z0-9]+(-[a-z0-9]+)*`, max 64 characters. Client-side validated.
- **`harness_id`**: Opaque ID (format: `harness_<32-hex>`). Use `generate_harness_id()` to create one.

If neither is provided, the server defaults to the Generic harness.
Providing both `harness_id` and `harness_name` raises a client-side validation error.
Agent is optional on session creation — sessions can run without an agent.
Session create/update payloads support optional `title`, `locale`, `model_id`, `tags`, `capabilities`, and `initial_files` starter files.

### Capabilities
- `GET /v1/capabilities` - List available capabilities (supports `search`, `offset`, `limit`)
- `GET /v1/capabilities/{id}` - Get capability details

### Messages
- `POST /v1/sessions/{id}/messages` - Create message (supports `external_actor` for channel identity)
- `GET /v1/sessions/{id}/messages` - List messages

### Events
- `GET /v1/sessions/{id}/events` - List events (polling, supports `limit`/`before_sequence` backward pagination)
- `GET /v1/sessions/{id}/sse` - SSE stream (supports `limit`/`before_sequence` backward pagination)

### Images
- `POST /v1/images` - Upload image
- `GET /v1/images` - List images
- `GET /v1/images/{id}` - Get image
- `DELETE /v1/images/{id}` - Delete image
- `GET /v1/images/{id}/thumbnail` - Get image thumbnail

### Session Filesystem
- `GET /v1/sessions/{id}/fs` - List root directory (supports `recursive` query param)
- `GET /v1/sessions/{id}/fs/{path}` - Read file content or list directory
- `POST /v1/sessions/{id}/fs/{path}` - Create file or directory
- `PUT /v1/sessions/{id}/fs/{path}` - Update file content
- `DELETE /v1/sessions/{id}/fs/{path}` - Delete file or directory (supports `recursive` query param)
- `POST /v1/sessions/{id}/fs/_/move` - Move/rename file
- `POST /v1/sessions/{id}/fs/_/copy` - Copy file
- `POST /v1/sessions/{id}/fs/_/grep` - Search files with regex
- `POST /v1/sessions/{id}/fs/_/stat` - Get file/directory metadata

### Tool Results
- `POST /v1/sessions/{id}/tool-results` - Submit tool results

### Session Databases
- `GET /v1/sessions/{id}/databases` - List databases
- `POST /v1/sessions/{id}/databases` - Create database
- `GET /v1/sessions/{id}/databases/{name}` - Get database
- `DELETE /v1/sessions/{id}/databases/{name}` - Delete database
- `GET /v1/sessions/{id}/databases/{name}/schema` - Get database schema

### Session Storage
- `GET /v1/sessions/{id}/storage/keys` - List key-value storage
- `GET /v1/sessions/{id}/storage/secrets` - List secrets

## Not Covered (Out of SDK Scope)

Server administration endpoints not exposed via SDK:

### Agents
- `POST /v1/agents/preview` - Preview final agent shape

### Organizations
- `GET /v1/orgs` - List organizations
- `POST /v1/orgs` - Create organization
- `GET /v1/orgs/{org}` - Get organization
- `PATCH /v1/orgs/{org}` - Update organization
- `DELETE /v1/orgs/{org}` - Delete organization
- `POST /v1/users/me/switch-org` - Switch organization

### LLM Providers
- `POST /v1/llm-providers/{id}/sync-models` - Sync models
