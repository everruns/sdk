//! Basic example of using the Everruns SDK

use everruns_sdk::{Error, Everruns};
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize client from environment
    let client = Everruns::from_env()?;

    // Create an agent
    let agent = client
        .agents()
        .create(
            "Example Assistant",
            "You are a helpful assistant for examples.",
        )
        .await?;
    println!("Created agent:");
    println!("  Name: {}", agent.name);
    println!("  ID: {}", agent.id);
    println!("  Status: {:?}", agent.status);
    println!("  Created: {}", agent.created_at);

    // Create a session
    let session = client.sessions().create(&agent.id).await?;
    println!("Created session:");
    println!("  ID: {}", session.id);
    println!("  Agent: {}", session.agent_id);
    println!("  Status: {:?}", session.status);
    println!("  Created: {}", session.created_at);

    // Send a message
    let _message = client
        .messages()
        .create(&session.id, "Hello, how are you?")
        .await?;
    println!("Sent message");

    // Stream events
    let mut stream = client.events().stream(&session.id);
    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                println!("Event: {} - {}", e.event_type, e.id);
                if e.event_type == "turn.completed" {
                    break;
                }
            }
            Err(e) => {
                eprintln!("Error: {}", e);
                break;
            }
        }
    }

    // Clean up
    client.sessions().delete(&session.id).await?;
    client.agents().delete(&agent.id).await?;

    Ok(())
}
