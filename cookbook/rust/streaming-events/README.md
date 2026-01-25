# Streaming Events

Demonstrates SSE event streaming from sessions.

## Covered Scenarios

- **Basic streaming**: Consume events from a session
- **Event filtering**: Exclude delta events for summaries
- **Reconnection**: Use `since_id` for resumable streams
- **Event types**: Handle different event types
- **Cancellation**: Cancel a turn mid-stream

## Run

```bash
export EVERRUNS_ORG=your-org
export EVERRUNS_API_KEY=your-key
# Optional: export EVERRUNS_API_URL=http://localhost:8080/api

cargo run -p streaming-events
```

## Key Patterns

```rust
// Basic streaming
let mut stream = client.events().stream(&session.id);
while let Some(event) = stream.next().await {
    match event {
        Ok(e) => println!("{}: {}", e.event_type, e.id),
        Err(e) => break,
    }
}

// Stream with options (exclude deltas, resume from ID)
let options = StreamOptions::default()
    .exclude(&["content.delta"])
    .since_id("evt_abc123");
let mut stream = client.events().stream_with_options(&session.id, options);
```

## Event Types

| Event | Description |
|-------|-------------|
| `turn.started` | Agent turn has begun |
| `content.delta` | Incremental content update |
| `content.done` | Content block completed |
| `tool.started` | Tool invocation started |
| `tool.completed` | Tool invocation completed |
| `turn.completed` | Agent turn finished |
