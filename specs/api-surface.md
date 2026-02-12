# API Surface

## Scope

SDKs cover agents and sessions functionality. No durable execution endpoints.

## Covered Endpoints

### Agents
- `POST /v1/agents` - Create agent (server-assigned ID) or upsert with client-supplied ID
- `GET /v1/agents` - List agents
- `GET /v1/agents/{id}` - Get agent
- `PATCH /v1/agents/{id}` - Update agent
- `DELETE /v1/agents/{id}` - Archive agent
- `POST /v1/agents/import` - Import agent from Markdown/YAML/JSON/text
- `GET /v1/agents/{id}/export` - Export agent as Markdown

#### Client-Supplied Agent IDs

The `POST /v1/agents` endpoint accepts an optional `id` field in the request body.
When `id` is provided (format: `agent_<32-hex>`), the endpoint has upsert semantics:
if an agent with that ID exists it is updated, otherwise a new agent is created.
When `id` is omitted, the server auto-generates one (plain create).

### Sessions
- `POST /v1/sessions` - Create session (supports capabilities)
- `GET /v1/sessions` - List sessions
- `GET /v1/sessions/{id}` - Get session
- `PATCH /v1/sessions/{id}` - Update session
- `DELETE /v1/sessions/{id}` - Delete session
- `POST /v1/sessions/{id}/cancel` - Cancel turn

### Capabilities
- `GET /v1/capabilities` - List available capabilities
- `GET /v1/capabilities/{id}` - Get capability details

### Messages
- `POST /v1/sessions/{id}/messages` - Create message
- `GET /v1/sessions/{id}/messages` - List messages

### Events
- `GET /v1/sessions/{id}/events` - List events (polling)
- `GET /v1/sessions/{id}/sse` - SSE stream

### Images
- `POST /v1/images` - Upload image
- `GET /v1/images` - List images
- `GET /v1/images/{id}` - Get image
- `DELETE /v1/images/{id}` - Delete image
- `GET /v1/images/{id}/thumbnail` - Get image thumbnail

### Session Filesystem
- `GET /v1/sessions/{id}/fs` - List files
- `GET /v1/sessions/{id}/fs/{path}` - Read file
- `PUT /v1/sessions/{id}/fs/{path}` - Write file

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
