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
- `GET /v1/images/{id}` - Get image

### Session Filesystem
- `GET /v1/sessions/{id}/fs` - List files
- `GET /v1/sessions/{id}/fs/{path}` - Read file
- `PUT /v1/sessions/{id}/fs/{path}` - Write file
