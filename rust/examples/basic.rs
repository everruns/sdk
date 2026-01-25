//! Basic example of using the Everruns SDK

use everruns_sdk::{Everruns, Error};
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize client from environment
    let client = Everruns::from_env("my-org")?;

    // Create an agent
    let agent = client.agents().create(
        "Example Assistant",
        "You are a helpful assistant for examples."
    ).await?;
    println!("Created agent: {}", agent.id);

    // Create a session
    let session = client.sessions().create(&agent.id).await?;
    println!("Created session: {}", session.id);

    // Send a message
    let _message = client.messages().create(&session.id, "Hello, how are you?").await?;
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
