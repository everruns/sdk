//! Local Tools Example - Everruns SDK
//!
//! Demonstrates client-side tool execution: the agent requests a tool call,
//! the client executes it locally, and sends the result back.
//!
//! Run: cargo run --bin weather-tools
//! Run with verbose: cargo run --bin weather-tools -- --verbose

use everruns_sdk::{
    ContentPart, CreateAgentRequest, CreateSessionRequest, Everruns, ToolDefinition,
    extract_tool_calls,
};
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

fn weather_tool() -> ToolDefinition {
    ToolDefinition::client_side(
        "get_weather",
        "Get current weather for a city.",
        serde_json::json!({
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["city"],
            "additionalProperties": false
        }),
    )
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
        .create_with_options(
            CreateAgentRequest::new("weather-assistant-rs", SYSTEM_PROMPT)
                .tools(vec![weather_tool()]),
        )
        .await?;
    println!("Created agent: {}", agent.id);

    // Create session
    let session = client
        .sessions()
        .create_with_options(
            CreateSessionRequest::new()
                .agent_id(&agent.id)
                .tools(vec![weather_tool()]),
        )
        .await?;
    println!("Created session: {}\n", session.id);

    let baseline_event_id = client
        .events()
        .list(&session.id)
        .await?
        .data
        .last()
        .map(|event| event.id.clone());

    // Stream events and handle tool calls
    use everruns_sdk::sse::StreamOptions;
    let mut options = StreamOptions::default().with_max_retries(3);
    if let Some(event_id) = baseline_event_id {
        options = options.with_since_id(event_id);
    }
    let event_client = client.clone();
    let event_session_id = session.id.clone();
    let event_task = tokio::spawn(async move {
        handle_events(event_client, event_session_id, options, verbose).await
    });
    tokio::time::sleep(std::time::Duration::from_millis(250)).await;

    // Send user message
    match tokio::time::timeout(
        std::time::Duration::from_secs(30),
        client
            .messages()
            .create(&session.id, "What's the weather like in Paris?"),
    )
    .await
    {
        Ok(result) => {
            result?;
        }
        Err(_) => {
            println!("Timed out waiting for message submission; ending demo.");
            return Ok(());
        }
    }

    match tokio::time::timeout(std::time::Duration::from_secs(60), event_task).await {
        Ok(joined) => joined
            .map_err(|err| std::io::Error::other(err.to_string()))?
            .map_err(std::io::Error::other)?,
        Err(_) => println!("Timed out waiting for turn completion; ending demo."),
    }

    Ok(())
}

async fn handle_events(
    client: Everruns,
    session_id: String,
    options: everruns_sdk::sse::StreamOptions,
    verbose: bool,
) -> Result<(), String> {
    let mut stream = client.events().stream_with_options(&session_id, options);
    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                if verbose {
                    println!(
                        "\n[EVENT] {}: {}",
                        e.event_type,
                        serde_json::to_string_pretty(&e.data).map_err(|err| err.to_string())?
                    );
                }
                match e.event_type.as_str() {
                    "tool.call_requested" => {
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
                                .create_tool_results(&session_id, results)
                                .await
                                .map_err(|err| err.to_string())?;
                            println!("  <- Sent tool results\n");
                        }
                    }
                    "output.message.completed" => {
                        if let Some(text) = extract_text(&e.data) {
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
