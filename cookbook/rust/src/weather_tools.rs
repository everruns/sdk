//! Local Tools Example - Everruns SDK
//!
//! Demonstrates client-side tool execution: the agent requests a tool call,
//! the client executes it locally, and sends the result back.
//!
//! Run: cargo run --bin weather-tools
//! Run with verbose: cargo run --bin weather-tools -- --verbose

use everruns_sdk::{ContentPart, Everruns, extract_tool_calls};
use futures::StreamExt;

/// Simulated local weather lookup.
fn get_weather(city: &str) -> serde_json::Value {
    // In a real app this would call a weather API.
    let (temp, condition) = match city.to_lowercase().as_str() {
        "paris" => (18, "partly cloudy"),
        "tokyo" => (22, "sunny"),
        "new york" => (15, "rainy"),
        _ => (20, "clear"),
    };
    serde_json::json!({
        "city": city,
        "temperature_celsius": temp,
        "condition": condition
    })
}

/// Dispatch a tool call by name and return a ContentPart with the result.
fn handle_tool_call(call_id: &str, name: &str, arguments: &serde_json::Value) -> ContentPart {
    match name {
        "get_weather" => {
            let city = arguments
                .get("city")
                .and_then(|v| v.as_str())
                .unwrap_or("unknown");
            let result = get_weather(city);
            ContentPart::tool_result(call_id, result)
        }
        _ => ContentPart::tool_error(call_id, format!("Unknown tool: {}", name)),
    }
}

const SYSTEM_PROMPT: &str = "\
You are a helpful weather assistant. You have access to a tool called `get_weather` \
that accepts a JSON argument `{\"city\": \"<city name>\"}` and returns current weather. \
When the user asks about weather, call the tool and then summarize the result.";

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let verbose = std::env::args().any(|a| a == "--verbose" || a == "-v");
    let client = Everruns::from_env()?;

    // Create agent with tool-aware system prompt
    let agent = client
        .agents()
        .create("Weather Assistant", SYSTEM_PROMPT)
        .await?;
    println!("Created agent: {}", agent.id);

    // Create session
    let session = client.sessions().create(&agent.id).await?;
    println!("Created session: {}\n", session.id);

    // Send user message
    client
        .messages()
        .create(&session.id, "What's the weather like in Paris?")
        .await?;

    // Stream events and handle tool calls
    use everruns_sdk::sse::StreamOptions;
    let mut stream = client
        .events()
        .stream_with_options(&session.id, StreamOptions::default().with_max_retries(3));

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
                    "output.message.completed" => {
                        // Check for tool calls in the completed message
                        let tool_calls = extract_tool_calls(&e.data);
                        if !tool_calls.is_empty() {
                            println!("Agent requested {} tool call(s)", tool_calls.len());
                            let results: Vec<ContentPart> = tool_calls
                                .iter()
                                .map(|tc| {
                                    println!("  -> Executing {}({})", tc.name, tc.arguments);
                                    handle_tool_call(tc.id, tc.name, tc.arguments)
                                })
                                .collect();

                            // Send tool results back
                            client
                                .messages()
                                .create_tool_results(&session.id, results)
                                .await?;
                            println!("  <- Sent tool results\n");
                        } else if let Some(text) = extract_text(&e.data) {
                            println!("Assistant: {}", text);
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
