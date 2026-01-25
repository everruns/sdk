# API Surface

## Scope

SDKs cover agents and sessions functionality. No durable execution endpoints.

## Covered Endpoints

### Agents
- `POST /v1/orgs/{org}/agents` - Create agent
- `GET /v1/orgs/{org}/agents` - List agents
- `GET /v1/orgs/{org}/agents/{id}` - Get agent
- `PATCH /v1/orgs/{org}/agents/{id}` - Update agent
- `DELETE /v1/orgs/{org}/agents/{id}` - Archive agent

### Sessions
- `POST /v1/orgs/{org}/sessions` - Create session
- `GET /v1/orgs/{org}/sessions` - List sessions
- `GET /v1/orgs/{org}/sessions/{id}` - Get session
- `PATCH /v1/orgs/{org}/sessions/{id}` - Update session
- `DELETE /v1/orgs/{org}/sessions/{id}` - Delete session
- `POST /v1/orgs/{org}/sessions/{id}/cancel` - Cancel turn

### Messages
- `POST /v1/orgs/{org}/sessions/{id}/messages` - Create message
- `GET /v1/orgs/{org}/sessions/{id}/messages` - List messages

### Events
- `GET /v1/orgs/{org}/sessions/{id}/events` - List events (polling)
- `GET /v1/orgs/{org}/sessions/{id}/sse` - SSE stream

### Images
- `POST /v1/orgs/{org}/images` - Upload image
- `GET /v1/orgs/{org}/images/{id}` - Get image

### Session Filesystem
- `GET /v1/orgs/{org}/sessions/{id}/fs` - List files
- `GET /v1/orgs/{org}/sessions/{id}/fs/{path}` - Read file
- `PUT /v1/orgs/{org}/sessions/{id}/fs/{path}` - Write file
