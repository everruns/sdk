# everruns-sdk

Rust SDK for the Everruns API.

## Installation

```bash
cargo add everruns-sdk
```

## Quick Start

```rust
use everruns_sdk::{CreateSessionRequest, Everruns};

#[tokio::main]
async fn main() -> Result<(), everruns_sdk::Error> {
    // Uses EVERRUNS_API_KEY and optional EVERRUNS_ORG_ID environment variables
    let client = Everruns::from_env()?;

    // Create an agent
    let agent = client.agents().create(
        "Assistant",
        "You are a helpful assistant."
    ).await?;

    // Create a session
    let session = client
        .sessions()
        .create_with_options(CreateSessionRequest::new().agent_id(&agent.id))
        .await?;

    // Send a message
    client.messages().create(&session.id, "Hello!").await?;

    Ok(())
}
```

## Initial Files

```rust
use everruns_sdk::{CreateSessionRequest, InitialFile};

let session = client
    .sessions()
    .create_with_options(
        CreateSessionRequest::new()
            .agent_id(&agent.id)
            .initial_files(vec![
                InitialFile::new("/workspace/README.md", "# Demo Project\n")
                    .encoding("text")
                    .is_readonly(true),
                InitialFile::new("/workspace/src/app.py", "print(\"hello\")\n")
                    .encoding("text"),
            ]),
    )
    .await?;
```

Runnable example: [`examples/initial_files.rs`](examples/initial_files.rs)

## Agent Versions

```rust
use everruns_sdk::{AgentVersionChangeKind, CreateAgentVersionRequest};

let version = client
    .agents()
    .create_version(
        "agent_...",
        CreateAgentVersionRequest::new()
            .change_kind(AgentVersionChangeKind::Manual)
            .summary("Baseline"),
    )
    .await?;

let versions = client.agents().list_versions("agent_...").await?;
let diff = client
    .agents()
    .diff_versions("agent_...", "agentver_1", &version.id)
    .await?;
```

## Workspaces

Workspaces hold files shared across sessions.

```rust
use everruns_sdk::CreateWorkspaceRequest;

let workspace = client
    .workspaces()
    .create(CreateWorkspaceRequest::new("team-docs"))
    .await?;

client
    .workspace_files()
    .create(&workspace.id, "/notes/welcome.md", "# Welcome\n", Some("text"))
    .await?;
let file = client
    .workspace_files()
    .read(&workspace.id, "/notes/welcome.md")
    .await?;
let files = client
    .workspace_files()
    .list(&workspace.id, None, Some(true))
    .await?;
```

Runnable example: [`examples/workspaces.rs`](examples/workspaces.rs)

## Memories

Memories are long-term, searchable knowledge stores for agents.

```rust
use everruns_sdk::CreateMemoryRequest;

let memory = client
    .memories()
    .create(CreateMemoryRequest::new("product-knowledge"))
    .await?;

client
    .memories()
    .create_file(&memory.id, "/facts/product.md", "# Product\n", Some("text"))
    .await?;
let results = client.memories().grep_files(&memory.id, "product", None).await?;
client.memories().sync(&memory.id).await?;
```

Runnable example: [`examples/memories.rs`](examples/memories.rs)

## Authentication

The SDK uses personal access token authentication. Set the `EVERRUNS_API_KEY` environment variable or pass the token explicitly. For personal access tokens with access to multiple organizations, set `EVERRUNS_ORG_ID` or pass `org_id` explicitly:

```rust
// From environment variable
let client = Everruns::from_env()?;
```

Or with an explicit token and organization:

```rust
let client = Everruns::builder()
    .api_key("evr_pat_...")
    .org_id("org_...")
    .build()?;
```

## Streaming Events

The SDK supports SSE streaming with automatic reconnection:

```rust
use futures::StreamExt;
use everruns_sdk::StreamOptions;

let stream = client.events().stream(
    &session.id,
    StreamOptions::default().exclude(vec!["output.message.delta".into()])
).await?;

while let Some(event) = stream.next().await {
    match event?.event_type.as_str() {
        "output.message.completed" => {
            println!("Message: {:?}", event.data);
        }
        "turn.completed" => {
            println!("Turn completed");
            break;
        }
        "turn.failed" => {
            eprintln!("Turn failed: {:?}", event.data);
            break;
        }
        _ => {}
    }
}
```

## Error Handling

```rust
use everruns_sdk::Error;

match client.agents().get("invalid-id").await {
    Ok(agent) => println!("Agent: {:?}", agent),
    Err(Error::Authentication(_)) => eprintln!("Invalid personal access token"),
    Err(Error::NotFound(_)) => eprintln!("Agent not found"),
    Err(Error::RateLimit { retry_after }) => {
        eprintln!("Rate limited, retry after {:?}", retry_after);
    }
    Err(e) => eprintln!("Error: {}", e),
}
```

## License

MIT
