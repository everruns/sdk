//! Dad Jokes Agent - Everruns SDK Example
//!
//! Run: cargo run
//! Run with verbose: cargo run -- --verbose

use everruns_sdk::Everruns;
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let verbose = std::env::args().any(|a| a == "--verbose" || a == "-v");
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
    println!("Created session: {}\n", session.id);

    // Send message
    client
        .messages()
        .create(&session.id, "Tell me a dad joke")
        .await?;

    // Stream events
    let mut stream = client.events().stream(&session.id);
    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                if verbose {
                    println!(
                        "\n[EVENT] {}: {}",
                        e.event_type,
                        serde_json::to_string_pretty(&e.data)?
                    );
                }
                match e.event_type.as_str() {
                    "input.message" => {
                        if let Some(text) = extract_text(&e.data) {
                            println!("Input: {}", text);
                        } else {
                            println!("Input (raw): {}", serde_json::to_string_pretty(&e.data)?);
                        }
                    }
                    "output.message.completed" => {
                        if let Some(text) = extract_text(&e.data) {
                            println!("Output: {}", text);
                        } else {
                            println!("Output (raw): {}", serde_json::to_string_pretty(&e.data)?);
                        }
                    }
                    "turn.completed" => {
                        println!("\n[Turn completed]");
                        break;
                    }
                    "turn.failed" => {
                        println!("\n[Turn failed]");
                        break;
                    }
                    _ => {}
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

fn extract_text(data: &serde_json::Value) -> Option<String> {
    let content = data.get("message")?.get("content")?.as_array()?;
    let texts: Vec<&str> = content
        .iter()
        .filter_map(|part| {
            if part.get("type")?.as_str()? == "text" {
                part.get("text")?.as_str()
            } else {
                None
            }
        })
        .collect();
    if texts.is_empty() {
        None
    } else {
        Some(texts.join(""))
    }
}

fn dev_client() -> Result<Everruns, everruns_sdk::Error> {
    let org = std::env::var("EVERRUNS_ORG").expect("EVERRUNS_ORG required");
    let key = std::env::var("EVERRUNS_API_KEY").expect("EVERRUNS_API_KEY required");

    match std::env::var("EVERRUNS_API_URL") {
        Ok(url) => Everruns::with_base_url(key, org, &url),
        Err(_) => Everruns::new(key, org),
    }
}
