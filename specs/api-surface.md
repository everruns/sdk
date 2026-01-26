# API Surface

## Scope

SDKs cover agents and sessions functionality. No durable execution endpoints.

## Covered Endpoints

### Agents
- `POST /v1/agents` - Create agent
- `GET /v1/agents` - List agents
- `GET /v1/agents/{id}` - Get agent
- `PATCH /v1/agents/{id}` - Update agent
- `DELETE /v1/agents/{id}` - Archive agent

### Sessions
- `POST /v1/sessions` - Create session
- `GET /v1/sessions` - List sessions
- `GET /v1/sessions/{id}` - Get session
- `PATCH /v1/sessions/{id}` - Update session
- `DELETE /v1/sessions/{id}` - Delete session
- `POST /v1/sessions/{id}/cancel` - Cancel turn

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
