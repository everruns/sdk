//! File Operations Cookbook
//!
//! Demonstrates session filesystem operations.
//!
//! Note: The file operations API is not yet implemented in the SDK.
//! This cookbook shows the expected patterns once available.

use cookbook_common::{cleanup, dev_client, init_tracing};
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing();

    let client = dev_client()?;
    tracing::info!("Client initialized");

    // Create test agent and session
    let agent = client
        .agents()
        .create(
            "File Operations Agent",
            "You are an assistant that can work with files. When asked to create a file, use the appropriate tool.",
        )
        .await?;
    tracing::info!("Created agent: {}", agent.id);

    let session = client.sessions().create(&agent.id).await?;
    tracing::info!("Created session: {}", session.id);

    // Demonstrate file operations through agent interaction
    // The agent can create/read files via tool use
    tracing::info!("--- File Operations via Agent ---");

    // Ask the agent to create a file
    client
        .messages()
        .create(
            &session.id,
            "Create a file called 'hello.txt' with the content 'Hello from cookbook!'",
        )
        .await?;

    // Stream events to see the file creation
    let mut stream = client.events().stream(&session.id);
    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => match e.event_type.as_str() {
                "tool.started" => {
                    if let Some(name) = e.data.get("name") {
                        tracing::info!("Tool started: {}", name);
                    }
                }
                "tool.completed" => {
                    tracing::info!("Tool completed");
                }
                "turn.completed" => {
                    tracing::info!("Turn completed");
                    break;
                }
                _ => {}
            },
            Err(e) => {
                tracing::error!("Stream error: {}", e);
                break;
            }
        }
    }

    // Ask the agent to read the file back
    tracing::info!("--- Read File via Agent ---");
    client
        .messages()
        .create(
            &session.id,
            "Read the content of 'hello.txt' and tell me what it says.",
        )
        .await?;

    let mut stream = client.events().stream(&session.id);
    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                if e.event_type == "content.done"
                    && let Some(text) = e.data.get("text")
                {
                    tracing::info!("Agent response: {}", text);
                }
                if e.event_type == "turn.completed" {
                    break;
                }
            }
            Err(e) => {
                tracing::error!("Stream error: {}", e);
                break;
            }
        }
    }

    // Note about direct file API
    tracing::info!("--- Direct File API ---");
    tracing::info!("Direct file operations (list, read, write) via SDK:");
    tracing::info!("  client.files().list(&session.id)");
    tracing::info!("  client.files().read(&session.id, \"path/to/file\")");
    tracing::info!("  client.files().write(&session.id, \"path/to/file\", content)");
    tracing::info!("These methods are planned for future SDK versions.");

    // Cleanup
    cleanup(&client, &session.id, &agent.id).await;
    tracing::info!("File operations cookbook completed");

    Ok(())
}
