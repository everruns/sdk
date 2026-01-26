# Everruns SDK

Official client libraries for the [Everruns API](https://everruns.com). Build AI agent applications with typed, async SDKs for Rust, Python, and TypeScript.

## Installation

**Rust**
```toml
[dependencies]
everruns-sdk = "0.1"
```

**Python** (3.10+)
```bash
pip install everruns-sdk
```

**TypeScript** (Node 18+)
```bash
npm install @everruns/sdk
```

## Quick Start

Set your API key:
```bash
export EVERRUNS_API_KEY=evr_your_key_here
```

### Rust

```rust
use everruns_sdk::Everruns;
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = Everruns::from_env("my-org")?;

    // Create an agent
    let agent = client.agents().create(
        "Assistant",
        "You are a helpful assistant."
    ).await?;

    // Start a session
    let session = client.sessions().create(&agent.id).await?;

    // Send a message
    client.messages().create(&session.id, "Hello!").await?;

    // Stream the response
    let mut stream = client.events().stream(&session.id);
    while let Some(event) = stream.next().await {
        let event = event?;
        println!("{}", event.event_type);
        if event.event_type == "turn.completed" {
            break;
        }
    }

    Ok(())
}
```

### Python

```python
import asyncio
from everruns_sdk import Everruns

async def main():
    client = Everruns(org="my-org")

    # Create an agent
    agent = await client.agents.create(
        name="Assistant",
        system_prompt="You are a helpful assistant."
    )

    # Start a session
    session = await client.sessions.create(agent_id=agent.id)

    # Send a message
    await client.messages.create(session.id, "Hello!")

    # Stream the response
    async for event in client.events.stream(session.id):
        print(event.type)
        if event.type == "turn.completed":
            break

    await client.close()

asyncio.run(main())
```

### TypeScript

```typescript
import { Everruns } from "@everruns/sdk";

async function main() {
  const client = Everruns.fromEnv("my-org");

  // Create an agent
  const agent = await client.agents.create({
    name: "Assistant",
    systemPrompt: "You are a helpful assistant.",
  });

  // Start a session
  const session = await client.sessions.create({ agentId: agent.id });

  // Send a message
  await client.messages.create(session.id, { text: "Hello!" });

  // Stream the response
  for await (const event of client.events.stream(session.id)) {
    console.log(event.type);
    if (event.type === "turn.completed") break;
  }
}

main();
```

## Features

- **Consistent API** across Rust, Python, and TypeScript
- **Async/await** patterns throughout
- **SSE streaming** with automatic reconnection
- **Typed models** generated from OpenAPI spec
- **Sub-client organization**: `.agents()`, `.sessions()`, `.messages()`, `.events()`

## API Coverage

| Resource | Operations |
|----------|------------|
| Agents | Create, list, get, update, archive |
| Sessions | Create, list, get, update, delete, cancel |
| Messages | Create, list |
| Events | Poll, stream (SSE) |
| Filesystem | List, read, write session files |
| Images | Upload, retrieve |

## Event Types

| Category | Events |
|----------|--------|
| Input | `input.message` |
| Output | `output.message.started`, `output.message.delta`, `output.message.completed` |
| Turn | `turn.started`, `turn.completed`, `turn.failed`, `turn.cancelled` |
| Tool | `tool.started`, `tool.completed` |

## Authentication

All SDKs read from `EVERRUNS_API_KEY` environment variable by default, or accept an explicit key:

```rust
// Rust
let client = Everruns::new("evr_...", "my-org");
```

```python
# Python
client = Everruns(api_key="evr_...", org="my-org")
```

```typescript
// TypeScript
const client = new Everruns({ apiKey: "evr_...", org: "my-org" });
```

## Error Handling

Consistent error types across all SDKs:

| Error | Description |
|-------|-------------|
| `AuthenticationError` | Invalid or missing API key |
| `NotFoundError` | Resource not found (404) |
| `RateLimitError` | Rate limited (429), includes `retry_after` |
| `ApiError` | General API errors |

## Documentation

- [Getting Started](docs/getting-started.md)
- [API Surface](specs/api-surface.md)
- [SSE Streaming](specs/sse-streaming.md)
- [Error Handling](specs/error-handling.md)
- [Architecture](specs/architecture.md)

## Examples

See the [`cookbook/`](cookbook/) directory for runnable examples, including a complete [Dad Jokes agent](cookbook/rust/README.md) in Rust.

Each SDK also has basic examples:
- [`rust/examples/basic.rs`](rust/examples/basic.rs)
- [`python/examples/basic.py`](python/examples/basic.py)
- [`typescript/examples/basic.ts`](typescript/examples/basic.ts)

## Development

```bash
just setup    # Install dependencies for all SDKs
just test     # Run all tests
just lint     # Run all linters
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

MIT
