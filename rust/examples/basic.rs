//! Basic example of using the Everruns SDK

use everruns_sdk::{
    AgentCapabilityConfig, CreateAgentRequest, CreateSessionRequest, Error, Everruns,
};
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Initialize client from environment
    let client = Everruns::from_env()?;

    // Create an agent with current_time capability
    let agent = client
        .agents()
        .create_with_options(
            CreateAgentRequest::new(
                "Example Assistant",
                "You are a helpful assistant for examples.",
            )
            .capabilities(vec![AgentCapabilityConfig::new("current_time")]),
        )
        .await?;
    println!("Created agent:");
    println!("  Name: {}", agent.name);
    println!("  ID: {}", agent.id);
    println!("  Status: {:?}", agent.status);
    println!("  Capabilities: {:?}", agent.capabilities);
    println!("  Created: {}", agent.created_at);

    // Create a session (capabilities can also be added at session level)
    let session = client
        .sessions()
        .create_with_options(
            CreateSessionRequest::new(&agent.id)
                .capabilities(vec![AgentCapabilityConfig::new("current_time")]),
        )
        .await?;
    println!("Created session:");
    println!("  ID: {}", session.id);
    println!("  Agent: {}", session.agent_id);
    println!("  Status: {:?}", session.status);
    println!("  Created: {}", session.created_at);

    // Send a message that uses the current_time capability
    let _message = client
        .messages()
        .create(
            &session.id,
            "What time is it right now? Generate a short joke about the current time.",
        )
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
