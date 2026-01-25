//! Dad Jokes Agent
//!
//! Creates a dad jokes agent and asks for a joke about the current time.

use chrono::Local;
use cookbook_common::{cleanup, dev_client, init_tracing};
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
            "You are a dad joke expert. You tell cheesy, family-friendly dad jokes. \
             Always respond with exactly one dad joke, followed by a brief explanation \
             of why it's funny (because dad jokes need explaining).",
        )
        .await?;
    println!("Created agent: {}", agent.id);

    // Create session
    let session = client.sessions().create(&agent.id).await?;
    println!("Created session: {}", session.id);

    // Get current time
    let now = Local::now();
    let time_str = now.format("%H:%M").to_string();
    let prompt = format!(
        "Tell me a dad joke about the time. It's currently {}. \
         Make it relevant to this specific time if possible!",
        time_str
    );
    println!("\nAsking: {}", prompt);

    // Send message
    client.messages().create(&session.id, &prompt).await?;

    // Stream response
    println!("\nAgent response:");
    println!("---");
    let mut stream = client.events().stream(&session.id);
    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                if e.event_type == "content.delta"
                    && let Some(text) = e.data.get("text").and_then(|v| v.as_str())
                {
                    print!("{}", text);
                }
                if e.event_type == "turn.completed" {
                    break;
                }
            }
            Err(e) => {
                eprintln!("\nStream error: {}", e);
                break;
            }
        }
    }
    println!("\n---");

    // Cleanup
    cleanup(&client, &session.id, &agent.id).await;
    println!("\nCleaned up agent and session");

    Ok(())
}
