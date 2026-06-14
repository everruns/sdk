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
- `GET /v1/agents/{id}/versions` - List saved agent versions
- `POST /v1/agents/{id}/versions` - Save the current agent configuration as a version
- `POST /v1/agents/{id}/versions/default` - Set the default version for an agent
- `GET /v1/agents/{id}/versions/{from_version_id}/diff/{to_version_id}` - Diff two agent versions
- `POST /v1/agents/{id}/versions/{version_id}/fork` - Create a new agent from a saved version
- `POST /v1/agents/{id}/versions/{version_id}/rollback` - Restore an agent from a saved version
- `POST /v1/agents/analyze` - Run advisory checks against an agent shape

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
Session create/update payloads support optional `title`, `locale`, `model_id`, `tags`, `capabilities`, `tools`, and `initial_files` starter files.

### Capabilities
- `GET /v1/capabilities` - List available capabilities (supports `search`, `offset`, `limit`)
- `GET /v1/capabilities/{id}` - Get capability details
- `GET /v1/capabilities/guardrails/examples` - List adoptable guardrail presets
- `POST /v1/capabilities/guardrails/dry-run` - Evaluate guardrail checks against sample text

### Messages
- `POST /v1/sessions/{id}/messages` - Create message (supports `external_actor` for channel identity)
- `GET /v1/sessions/{id}/messages` - List messages

### Events
- `GET /v1/sessions/{id}/events` - List events (polling, supports filtering, backward/forward pagination, centered windows, and full-text search)
- `GET /v1/sessions/{id}/sse` - SSE stream (supports `since_id`, `types`, and `exclude`)

### Images
- `POST /v1/images` - Upload image
- `GET /v1/images` - List images
- `GET /v1/images/{id}` - Get image
- `DELETE /v1/images/{id}` - Delete image
- `GET /v1/images/{id}/thumbnail` - Get image thumbnail

### Workspaces
- `GET /v1/workspaces` - List workspaces (supports `search`, `include_archived`)
- `POST /v1/workspaces` - Create workspace
- `GET /v1/workspaces/{workspace_id}` - Get workspace
- `PATCH /v1/workspaces/{workspace_id}` - Update workspace
- `DELETE /v1/workspaces/{workspace_id}` - Archive workspace

### Workspace Filesystem
- `GET /v1/workspaces/{workspace_id}/fs` - List root directory (supports `recursive` query param)
- `GET /v1/workspaces/{workspace_id}/fs/{path}` - Read file content or list directory
- `POST /v1/workspaces/{workspace_id}/fs/{path}` - Create file or directory
- `PUT /v1/workspaces/{workspace_id}/fs/{path}` - Update file content
- `DELETE /v1/workspaces/{workspace_id}/fs/{path}` - Delete file or directory (supports `recursive` query param)
- `POST /v1/workspaces/{workspace_id}/fs/_/move` - Move/rename file
- `POST /v1/workspaces/{workspace_id}/fs/_/copy` - Copy file
- `POST /v1/workspaces/{workspace_id}/fs/_/grep` - Search files with regex
- `POST /v1/workspaces/{workspace_id}/fs/_/stat` - Get file/directory metadata

### Memories
- `GET /v1/memories` - List memories (supports `search`, `include_archived`)
- `POST /v1/memories` - Create memory
- `GET /v1/memories/{memory_id}` - Get memory
- `PATCH /v1/memories/{memory_id}` - Update memory
- `DELETE /v1/memories/{memory_id}` - Archive memory
- `POST /v1/memories/{memory_id}/sync` - Trigger memory sync
- `GET /v1/memories/{memory_id}/fs` - List memory root
- `GET /v1/memories/{memory_id}/fs/{path}` - Read file or list directory
- `POST /v1/memories/{memory_id}/fs/{path}` - Create file or directory
- `PUT /v1/memories/{memory_id}/fs/{path}` - Update file content
- `DELETE /v1/memories/{memory_id}/fs/{path}` - Delete file or directory
- `GET /v1/memories/{memory_id}/fs/_/download/{path}` - Download raw file bytes
- `POST /v1/memories/{memory_id}/fs/_/grep` - Search memory files
- `POST /v1/memories/{memory_id}/fs/_/stat` - Get memory file metadata

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
- `POST /v1/agents/{id}/voice/sessions` - Create agent voice session

### Capabilities
- `POST /v1/capabilities` - Create persisted declarative capability
- `GET /v1/capabilities/declarative` - List persisted declarative capabilities
- `GET /v1/capabilities/declarative/config` - Get declarative capability config
- `GET /v1/capabilities/declarative/{id}` - Get persisted declarative capability
- `PATCH /v1/capabilities/declarative/{id}` - Update persisted declarative capability
- `DELETE /v1/capabilities/declarative/{id}` - Archive persisted declarative capability
- `POST /v1/capabilities/declarative/{id}/delete` - Permanently delete archived declarative capability

### Events
- `GET /v1/sessions/{id}/events/summary` - One-shot debug event summary

### Payments
- `GET /v1/payments/accounts` - List payment accounts
- `POST /v1/payments/accounts` - Create payment account
- `GET /v1/payments/accounts/{id}` - Get payment account
- `PATCH /v1/payments/accounts/{id}` - Update payment account
- `DELETE /v1/payments/accounts/{id}` - Disable payment account
- `GET /v1/payments/attempts` - List payment attempts
- `GET /v1/payments/policies` - List payment policies
- `POST /v1/payments/policies` - Create payment policy
- `GET /v1/payments/policies/{id}` - Get payment policy
- `PATCH /v1/payments/policies/{id}` - Update payment policy
- `DELETE /v1/payments/policies/{id}` - Disable payment policy

### Voice Sessions
- `POST /v1/sessions/chat/voice` - Create chat voice session
- `POST /v1/sessions/{id}/voice/calls` - Create voice call
- `POST /v1/sessions/{id}/voice/client-secret` - Create voice client secret
- `POST /v1/sessions/{id}/voice/{connection_id}/attach` - Attach voice call
- `POST /v1/sessions/{id}/voice/{connection_id}/end` - End voice call

### Organizations
- `GET /v1/orgs` - List organizations
- `POST /v1/orgs` - Create organization
- `GET /v1/orgs/{org}` - Get organization
- `PATCH /v1/orgs/{org}` - Update organization
- `DELETE /v1/orgs/{org}` - Delete organization
- `POST /v1/users/me/switch-org` - Switch organization

### Providers
- `POST /v1/providers/{id}/sync-models` - Sync models
