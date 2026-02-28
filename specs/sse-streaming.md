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
| `types` | string[] | Positive type filter: only return events matching these types |
| `exclude` | string[] | Event types to exclude (applied after `types` filter) |

### Array Parameter Expansion

Array parameters like `types` and `exclude` MUST be sent as **repeated query keys** (one key per value), not as comma-separated values or bracket syntax. This matches the `style: form, explode: true` convention in the OpenAPI spec.

```
Correct:   ?types=turn.started&types=turn.completed
Correct:   ?exclude=output.message.delta&exclude=reason.thinking.delta
Wrong:     ?exclude=output.message.delta,reason.thinking.delta
Wrong:     ?exclude[]=output.message.delta&exclude[]=reason.thinking.delta
```

When both `types` and `exclude` are provided, `types` narrows first (positive filter), then `exclude` removes from that set (negative filter). Both accept only known event types (max 25 per parameter). Unknown types return 400.

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
idle_deadline: timer | null      # Poll-level idle timer (reset on each yielded event)
idle_timeout: duration           # Configurable idle timeout duration (default 45s)
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
| READ_TIMEOUT_SECS | 45 | Secondary safety net for stalled connections |
| DEFAULT_IDLE_TIMEOUT_SECS | 45 | Poll-level idle timeout (primary stall detection) |

#### Why 45s for READ_TIMEOUT

The server sends heartbeat comments (`: heartbeat\n\n`) every 30s ([everruns/everruns#603](https://github.com/everruns/everruns/issues/603)). These reset the TCP read timer but are ignored by spec-compliant SSE parsers.

- **Must be > 30s** — allow at least one heartbeat interval
- **45s** — missing a single heartbeat reliably indicates a stalled connection
- Retry logic reconnects transparently with no data loss (via `since_id`)

#### Poll-Level Idle Timeout (Primary Stall Detection)

**`reqwest::Client::read_timeout` is ineffective on already-streaming SSE responses.** Despite documentation saying it applies to "time between receiving bytes," it does not fire once `reqwest_eventsource` takes over the response stream. Additionally, SSE heartbeat comments (`: heartbeat\n\n`) are consumed silently by `reqwest_eventsource` and never reach `EventStream::poll_next()`.

**Result:** When a TCP connection goes half-open (server closed, client doesn't know), `stream.next()` returns `Poll::Pending` forever. No timeout, no error, no recovery.

**Fix:** SDKs MUST implement a poll-level idle timeout inside the stream's poll function that races against the inner stream. When no events are yielded within `idle_timeout`, the stream drops the connection and reconnects.

```rust
// In poll_next():
// 1. Start idle timer when connection is established
// 2. Reset idle timer on every yielded event
// 3. If idle timer fires → drop connection, schedule reconnect
```

The idle timeout is configurable via `StreamOptions::with_idle_timeout()`. Default: 45s.

**Important:** The idle timer only resets on yielded business events, not on SSE comments (which are invisible to the SDK). Callers with long-idle sessions can increase the timeout.

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
2. **Use read timeout** - 45s as secondary safety net (see [Why 45s](#why-45s-for-read_timeout))
3. **Implement poll-level idle timeout** - 45s default, primary stall detection (see [Poll-Level Idle Timeout](#poll-level-idle-timeout-primary-stall-detection))
4. **Handle heartbeats** - Server sends `: heartbeat\n\n` every 30s; these reset the read timer but NOT the idle timer (SSE parsers consume comments silently)

```python
# Python example
timeout = httpx.Timeout(
    connect=30.0,
    read=READ_TIMEOUT_SECS,  # 45s — detect stalled connections
    write=30.0,
    pool=30.0,
)
```

```rust
// Rust example
let client = reqwest::Client::builder()
    .read_timeout(Duration::from_secs(READ_TIMEOUT_SECS)) // 45s
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

  // Positive type filter: only return events matching these types
  types?: string[];

  // Event types to exclude (applied after types filter)
  exclude?: string[];

  // Max reconnection attempts (undefined = unlimited)
  maxRetries?: number;

  // Poll-level idle timeout for detecting half-open connections (default: 45s)
  idleTimeout?: Duration;
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
Base:      /v1/sessions/{session_id}/sse
since_id:  /v1/sessions/{session_id}/sse?since_id={event_id}
types:     /v1/sessions/{session_id}/sse?types=turn.started&types=turn.completed
exclude:   /v1/sessions/{session_id}/sse?exclude=output.message.delta
Combined:  /v1/sessions/{session_id}/sse?since_id={id}&types=turn.started&exclude=output.message.delta
```

Note: URL-encode special characters in `since_id`. Each `types` and `exclude` value MUST be a separate query key (see [Array Parameter Expansion](#array-parameter-expansion)).

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
1. **StreamOptions** - Default, exclude_deltas, since_id, max_retries, idle_timeout
2. **DisconnectingData parsing** - Valid JSON, missing fields, edge cases
3. **Backoff calculations** - Sequence, max cap, reset
4. **URL building** - Basic, with params, encoding
5. **Argument expansion** - `types` and `exclude` use repeated keys (not comma-separated), combined params, empty arrays
6. **Retry logic** - Graceful vs unexpected, max retries
7. **State management** - last_event_id, retry_count, stop()
8. **Read timeout** - Constant value is 45s, above heartbeat interval (30s), HTTP client configured with it
9. **Idle timeout** - Default is 45s, configurable via `with_idle_timeout()`

### Smoke / Integration Tests
10. **Graceful disconnect reconnection** - Mock SSE server sends `connected` → event → `disconnecting`, verify stream reconnects, receives events from second connection, and `retry_count` stays 0
11. **Backoff reset on reconnection** - After unexpected disconnect (elevated backoff), verify successful reconnection with `connected` event resets backoff to initial values
12. **Multiple graceful disconnects** - Verify stream survives many sequential graceful disconnects without exhausting `max_retries`
13. **HTTP client reuse** - Verify the same HTTP client instance is used across reconnections
14. **Idle timeout reconnection** - Mock SSE server sends `connected` then hangs silent; verify idle timeout fires, stream reconnects, and receives events from second connection

## Implementation Checklist

For new language SDKs:

- [ ] StreamOptions with sinceId, types, exclude, maxRetries, idleTimeout
- [ ] DisconnectingData model
- [ ] EventStream async iterator
- [ ] Graceful disconnect handling (debug log)
- [ ] Exponential backoff (1s-30s)
- [ ] Read timeout (45s, secondary safety net)
- [ ] Poll-level idle timeout (45s default, primary stall detection)
- [ ] No overall timeout
- [ ] since_id tracking
- [ ] Backoff reset on success and on `connected` event
- [ ] Graceful disconnects do NOT increment retry_count
- [ ] HTTP client reused across reconnections
- [ ] stop/abort method
- [ ] URL building with encoding
- [ ] Unit tests for all above

## Server-Side Heartbeats

The server sends periodic SSE comment heartbeats every 30s ([everruns/everruns#603](https://github.com/everruns/everruns/issues/603)):

```
: heartbeat

```

These are SSE comments (lines starting with `:`) — spec-compliant parsers ignore them automatically. They reset the TCP read timer, allowing reliable detection of stalled connections.

### How Heartbeats Work

1. **Server sends `: heartbeat\n\n` every 30s** across all SSE streams
2. **Read timeout (45s) > heartbeat interval (30s)** — a missing heartbeat means the connection is stalled
3. **No SDK code changes needed for parsing** — SSE parsers already ignore comment lines
4. **Read timeout triggers reconnection** — retry logic reconnects transparently via `since_id`

### Configuration (Server-Side)

| Setting | Default | Env Var |
|---------|---------|---------|
| Heartbeat interval | 30s | `SSE_HEARTBEAT_INTERVAL_SECS` |

Heartbeats fire continuously regardless of other server activity and are orthogonal to the 300s connection cycle.
