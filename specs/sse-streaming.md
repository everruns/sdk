# SSE Streaming

## Connection

```
GET /v1/sessions/{id}/sse
Accept: text/event-stream
```

## Query Parameters

- `since_id` - Resume from event ID (UUIDv7, monotonically increasing)
- `exclude` - Array of event types to filter out

## Event Format

```
event: <event_type>
data: {"id":"...","type":"<event_type>","ts":"...","session_id":"...","data":{...}}
```

## Event Types

### Input
- `input.message`

### Output
- `output.message.started`
- `output.message.delta`
- `output.message.completed`

### Turn Lifecycle
- `turn.started`
- `turn.completed`
- `turn.failed`
- `turn.cancelled`

### Tool Execution
- `tool.started`
- `tool.completed`

## Reconnection

SDKs must implement automatic reconnection:

1. Track `since_id` from last received event
2. On disconnect, reconnect with `?since_id=<last_id>`
3. Use exponential backoff (1s, 2s, 4s, ... max 30s)
