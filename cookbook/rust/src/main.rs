//! Dad Jokes Agent - Everruns SDK Example
//!
//! Run: cargo run

use everruns_sdk::Everruns;
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = dev_client()?;

    // Create agent
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

    // Send message
    println!("\nAsking for a dad joke...\n");
    client
        .messages()
        .create(&session.id, "Tell me a dad joke")
        .await?;

    // Stream events
    let mut stream = client.events().stream(&session.id);
    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                println!("[{}] {}", e.event_type, serde_json::to_string(&e.data)?);
                if e.event_type == "turn.completed" || e.event_type == "turn.failed" {
                    break;
                }
            }
            Err(e) => {
                eprintln!("Stream error: {}", e);
                break;
            }
        }
    }

    Ok(())
}

fn dev_client() -> Result<Everruns, everruns_sdk::Error> {
    let org = std::env::var("EVERRUNS_ORG").expect("EVERRUNS_ORG required");
    let key = std::env::var("EVERRUNS_API_KEY").expect("EVERRUNS_API_KEY required");

    match std::env::var("EVERRUNS_API_URL") {
        Ok(url) => Everruns::with_base_url(key, org, &url),
        Err(_) => Everruns::new(key, org),
    }
}
