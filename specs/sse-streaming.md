# SSE Streaming

Server-Sent Events (SSE) streaming specification for Everruns SDKs.

## Connection

```
GET /v1/sessions/{id}/sse
Accept: text/event-stream
Cache-Control: no-cache
```

## Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `since_id` | string | Resume from event ID (UUIDv7, monotonically increasing) |
| `exclude` | string[] | Array of event types to filter out |

### Array Parameter Expansion

Array parameters like `exclude` MUST be sent as **repeated query keys** (one key per value), not as comma-separated values or bracket syntax. This matches the `style: form, explode: true` convention in the OpenAPI spec.

```
Correct:   ?exclude=output.message.delta&exclude=reason.thinking.delta
Wrong:     ?exclude=output.message.delta,reason.thinking.delta
Wrong:     ?exclude[]=output.message.delta&exclude[]=reason.thinking.delta
```

Reference: [everruns/everruns#575](https://github.com/everruns/everruns/pull/575) — the server uses `serde_html_form` which only supports the repeated-key format for deserializing arrays.

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

### Connection Lifecycle
- `connected` - Sent immediately when stream established
- `disconnecting` - Sent before server gracefully closes connection

## Connection Management

### Connection Cycling

The server automatically cycles SSE connections to prevent stale connections through proxies and load balancers:

| Stream Type | Cycle Interval |
|-------------|----------------|
| Session events | 5 minutes |
| Durable monitoring | 10 minutes |

Before closing, the server sends a `disconnecting` event:

```json
event: disconnecting
data: {"reason":"connection_cycle","retry_ms":100}
```

### Disconnecting Event Data

| Field | Type | Description |
|-------|------|-------------|
| `reason` | string | Reason for disconnect (e.g., `connection_cycle`, `server_maintenance`) |
| `retry_ms` | integer | Suggested delay before reconnecting (milliseconds) |

### Server Retry Hints

SSE events include `retry:` field hints (not directly in data, per SSE spec):

| Situation | Retry Hint |
|-----------|------------|
| Active streaming | 100ms |
| Idle | Backoff up to 500ms |
| After `disconnecting` | 100ms |

## SDK Implementation Requirements

All SDKs MUST implement automatic reconnection with the following behavior.

### State Management

SDKs must track:

```
last_event_id: string | null     # Last received event ID for resumption
server_retry_ms: int | null      # Server-provided retry hint
current_backoff_ms: int          # Current backoff delay
retry_count: int                 # Consecutive retry attempts
should_reconnect: bool           # Whether to continue reconnecting
graceful_disconnect: bool        # Whether last disconnect was graceful
```

### Reconnection Strategy

#### On Graceful Disconnect (`disconnecting` event)

1. Parse `retry_ms` from event data
2. Log at DEBUG level (expected behavior, not an error)
3. Reconnect after `retry_ms` delay (default 100ms if not provided)
4. Include `since_id` query parameter with last received event ID
5. **Do NOT increment `retry_count`** — graceful disconnects are planned server behavior, not errors. They must never exhaust `max_retries`.

```python
# Pseudocode
if event.type == "disconnecting":
    log.debug(f"Graceful disconnect: {event.reason}")
    await sleep(event.retry_ms / 1000)
    # NOTE: do NOT increment retry_count here
    reconnect(since_id=last_event_id)
```

#### On Unexpected Disconnect (network error, timeout, etc.)

1. Use exponential backoff: 1s, 2s, 4s, 8s, 16s, capped at 30s
2. Log at WARN/WARNING level
3. Reconnect with `since_id` query parameter
4. Reset backoff after receiving any successful event

```python
# Pseudocode
backoff_ms = 1000  # Initial
MAX_BACKOFF_MS = 30000

on_disconnect():
    log.warn(f"Unexpected disconnect, retrying in {backoff_ms}ms")
    await sleep(backoff_ms / 1000)
    backoff_ms = min(backoff_ms * 2, MAX_BACKOFF_MS)
    retry_count += 1
    reconnect(since_id=last_event_id)

on_event_received():
    backoff_ms = 1000  # Reset
    retry_count = 0
```

#### On `connected` Event

The server sends a `connected` event immediately after the SSE connection is established. SDKs MUST reset backoff and retry state upon receiving this event:

```python
# Pseudocode
if event.type == "connected":
    backoff_ms = 1000   # Reset to initial
    retry_count = 0     # Clear retry counter
```

This ensures that a successful reconnection clears any accumulated error backoff, even before data events arrive. Without this, a stream that reconnects during an idle period would retain elevated backoff from prior errors.

### Backoff Constants

| Constant | Value | Description |
|----------|-------|-------------|
| INITIAL_BACKOFF_MS | 1000 | Initial retry delay |
| MAX_BACKOFF_MS | 30000 | Maximum retry delay |
| READ_TIMEOUT_SECS | 120 | Detect stalled connections |

### Exponential Backoff Sequence

```
Attempt 1: 1000ms (1s)
Attempt 2: 2000ms (2s)
Attempt 3: 4000ms (4s)
Attempt 4: 8000ms (8s)
Attempt 5: 16000ms (16s)
Attempt 6+: 30000ms (30s) - capped
```

### HTTP Client Reuse

SDKs MUST reuse the HTTP client across reconnections. Creating a new HTTP client per reconnect:
- Discards the connection pool, forcing fresh TCP/TLS handshakes
- Prevents HTTP/2 multiplexing across reconnects
- Increases latency on every reconnection cycle

SDKs should create a dedicated SSE HTTP client once (with SSE-appropriate timeouts) and reuse it for all reconnection attempts.

### Long-Running Stream Support

SSE streams can run for hours. SDKs MUST:

1. **Disable overall request timeout** - Set to 0/None/infinite
2. **Use read timeout** - ~2 minutes to detect stalled connections
3. **Handle keep-alive** - Process periodic events to reset timeouts

```python
# Python example
timeout = httpx.Timeout(
    connect=30.0,
    read=120.0,      # 2 minute read timeout
    write=30.0,
    pool=30.0,
)
```

```rust
// Rust example
let client = reqwest::Client::builder()
    .timeout(Duration::from_secs(0))     // No overall timeout
    .read_timeout(Duration::from_secs(120))
    .build()?;
```

### Max Retries (Optional)

SDKs SHOULD support optional `max_retries` configuration:

```python
# Unlimited retries (default)
stream = client.events.stream(session_id)

# Limited retries
stream = client.events.stream(session_id, max_retries=5)
```

### Stop/Abort Method

SDKs MUST provide a way to stop the stream:

```python
stream.stop()   # Python
stream.abort()  # TypeScript
stream.stop()   # Rust
```

After stop/abort:
- No further reconnection attempts
- Current connection closed gracefully
- Iterator/stream terminates

## StreamOptions Configuration

```typescript
interface StreamOptions {
  // Resume from this event ID
  sinceId?: string;

  // Event types to exclude (reduces bandwidth)
  exclude?: string[];

  // Max reconnection attempts (undefined = unlimited)
  maxRetries?: number;
}
```

### Common Exclude Patterns

```typescript
// Exclude delta events (high volume, use completed instead)
const opts = { exclude: ["output.message.delta", "reason.thinking.delta"] };
```

## URL Building

SDKs must build SSE URLs correctly, using repeated keys for array parameters:

```
Base:   /v1/sessions/{session_id}/sse
With since_id: /v1/sessions/{session_id}/sse?since_id={event_id}
With exclude:  /v1/sessions/{session_id}/sse?exclude=output.message.delta
Combined:      /v1/sessions/{session_id}/sse?since_id={id}&exclude=type1&exclude=type2
```

Note: URL-encode special characters in `since_id`. Each `exclude` value MUST be a separate query key (see [Array Parameter Expansion](#array-parameter-expansion)).

## Event ID Handling

Event IDs are UUIDv7 (monotonically increasing by timestamp):
- Ensures reliable ordering
- No duplicate events on reconnection
- SDKs should update `last_event_id` for EVERY received event

```python
for event in stream:
    last_event_id = event.id  # Always update
    yield event
```

## Logging Guidelines

| Level | When |
|-------|------|
| DEBUG | Connected event, disconnecting event, reconnect attempts |
| TRACE | Skipped malformed events |
| WARN | Unexpected disconnects, network errors |
| ERROR | Max retries exceeded (if configured) |

## Testing Requirements

SDKs MUST test:

### Unit Tests
1. **StreamOptions** - Default, exclude_deltas, since_id, max_retries
2. **DisconnectingData parsing** - Valid JSON, missing fields, edge cases
3. **Backoff calculations** - Sequence, max cap, reset
4. **URL building** - Basic, with params, encoding
5. **Argument expansion** - `exclude` uses repeated keys (not comma-separated), combined params, empty arrays
6. **Retry logic** - Graceful vs unexpected, max retries
7. **State management** - last_event_id, retry_count, stop()

### Smoke / Integration Tests
8. **Graceful disconnect reconnection** - Mock SSE server sends `connected` → event → `disconnecting`, verify stream reconnects, receives events from second connection, and `retry_count` stays 0
9. **Backoff reset on reconnection** - After unexpected disconnect (elevated backoff), verify successful reconnection with `connected` event resets backoff to initial values
10. **Multiple graceful disconnects** - Verify stream survives many sequential graceful disconnects without exhausting `max_retries`
11. **HTTP client reuse** - Verify the same HTTP client instance is used across reconnections

## Implementation Checklist

For new language SDKs:

- [ ] StreamOptions with sinceId, exclude, maxRetries
- [ ] DisconnectingData model
- [ ] EventStream async iterator
- [ ] Graceful disconnect handling (debug log)
- [ ] Exponential backoff (1s-30s)
- [ ] Read timeout (2 minutes)
- [ ] No overall timeout
- [ ] since_id tracking
- [ ] Backoff reset on success and on `connected` event
- [ ] Graceful disconnects do NOT increment retry_count
- [ ] HTTP client reused across reconnections
- [ ] stop/abort method
- [ ] URL building with encoding
- [ ] Unit tests for all above
