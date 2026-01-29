# everruns-sdk

Rust SDK for the Everruns API.

## Installation

\`\`\`bash
cargo add everruns-sdk
\`\`\`

## Quick Start

\`\`\`rust
use everruns_sdk::Everruns;

#[tokio::main]
async fn main() -> Result<(), everruns_sdk::Error> {
    // Uses EVERRUNS_API_KEY environment variable
    let client = Everruns::from_env()?;

    // Create an agent
    let agent = client.agents().create(
        "Assistant",
        "You are a helpful assistant."
    ).await?;

    // Create a session
    let session = client.sessions().create(&agent.id).await?;

    // Send a message
    client.messages().create(&session.id, "Hello!").await?;

    Ok(())
}
\`\`\`

## Authentication

The SDK uses API key authentication. Set the \`EVERRUNS_API_KEY\` environment variable or pass the key explicitly:

\`\`\`rust
// From environment variable
let client = Everruns::from_env()?;

// Explicit key
let client = Everruns::new("evr_...")?;
\`\`\`

## Streaming Events

The SDK supports SSE streaming with automatic reconnection:

\`\`\`rust
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
\`\`\`

## Error Handling

\`\`\`rust
use everruns_sdk::Error;

match client.agents().get("invalid-id").await {
    Ok(agent) => println!("Agent: {:?}", agent),
    Err(Error::Authentication(_)) => eprintln!("Invalid API key"),
    Err(Error::NotFound(_)) => eprintln!("Agent not found"),
    Err(Error::RateLimit { retry_after }) => {
        eprintln!("Rate limited, retry after {:?}", retry_after);
    }
    Err(e) => eprintln!("Error: {}", e),
}
\`\`\`

## License

MIT
