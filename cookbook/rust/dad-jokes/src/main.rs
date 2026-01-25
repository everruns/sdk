//! Dad Jokes Agent
//!
//! Creates a dad jokes agent and asks for a joke.

use cookbook_common::{dev_client, init_tracing};
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing();

    let client = dev_client()?;
    println!("Connected to Everruns API");

    // Create dad jokes agent
    let agent = client
        .agents()
        .create(
            "Dad Jokes Bot",
            "You are a dad joke expert. Tell one short, cheesy dad joke.",
        )
        .await?;
    println!("Created agent: {}", agent.id);

    // Create session
    let session = client.sessions().create(&agent.id).await?;
    println!("Created session: {}", session.id);

    // Ask for a joke
    println!("\nAsking for a dad joke...\n");
    client
        .messages()
        .create(&session.id, "Tell me a dad joke")
        .await?;

    // Stream response
    let mut stream = client.events().stream(&session.id);
    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                if let Some(text) = e.data.get("text").and_then(|v| v.as_str()) {
                    print!("{}", text);
                }
                if e.event_type == "turn.completed" {
                    println!();
                    break;
                }
            }
            Err(e) => {
                eprintln!("\nStream error: {}", e);
                break;
            }
        }
    }

    Ok(())
}
