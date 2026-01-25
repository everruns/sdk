//! Streaming Events Cookbook
//!
//! Demonstrates SSE event streaming from sessions.

use cookbook_common::{cleanup, dev_client, init_tracing};
use everruns_sdk::sse::StreamOptions;
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
            "Streaming Test Agent",
            "You are a helpful assistant. Keep responses brief.",
        )
        .await?;
    tracing::info!("Created agent: {}", agent.id);

    let session = client.sessions().create(&agent.id).await?;
    tracing::info!("Created session: {}", session.id);

    // 1. Basic event streaming
    tracing::info!("--- Basic Event Streaming ---");
    client
        .messages()
        .create(&session.id, "Say hello in exactly 5 words.")
        .await?;
    tracing::info!("Sent message, starting stream...");

    let mut stream = client.events().stream(&session.id);
    let mut last_event_id: Option<String> = None;

    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                tracing::info!("Event: {} ({})", e.event_type, e.id);
                last_event_id = Some(e.id.clone());

                // Log event data based on type
                match e.event_type.as_str() {
                    "turn.started" => {
                        tracing::info!("  Turn started");
                    }
                    "content.delta" => {
                        if let Some(text) = e.data.get("text") {
                            tracing::debug!("  Delta: {}", text);
                        }
                    }
                    "content.done" => {
                        if let Some(text) = e.data.get("text") {
                            tracing::info!("  Content: {}", text);
                        }
                    }
                    "turn.completed" => {
                        tracing::info!("  Turn completed");
                        break;
                    }
                    _ => {}
                }
            }
            Err(e) => {
                tracing::error!("Stream error: {}", e);
                break;
            }
        }
    }

    // 2. Filtered streaming (exclude deltas)
    tracing::info!("--- Filtered Streaming (no deltas) ---");
    client
        .messages()
        .create(&session.id, "Count from 1 to 3.")
        .await?;

    let options = StreamOptions {
        exclude: vec!["content.delta".to_string()],
        since_id: None,
    };
    let mut stream = client.events().stream_with_options(&session.id, options);

    // Skip events we already saw
    let mut skip_until_new = last_event_id.is_some();

    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                if skip_until_new {
                    if Some(&e.id) == last_event_id.as_ref() {
                        skip_until_new = false;
                    }
                    continue;
                }

                tracing::info!("Event: {} ({})", e.event_type, e.id);

                if e.event_type == "turn.completed" {
                    last_event_id = Some(e.id);
                    break;
                }
            }
            Err(e) => {
                tracing::error!("Stream error: {}", e);
                break;
            }
        }
    }

    // 3. Resumable streaming with since_id
    tracing::info!("--- Resumable Streaming with since_id ---");
    client
        .messages()
        .create(&session.id, "What is 2+2?")
        .await?;

    if let Some(ref last_id) = last_event_id {
        tracing::info!("Resuming from event: {}", last_id);
        let options = StreamOptions {
            exclude: vec![],
            since_id: Some(last_id.clone()),
        };
        let mut stream = client.events().stream_with_options(&session.id, options);

        while let Some(event) = stream.next().await {
            match event {
                Ok(e) => {
                    tracing::info!("Event: {} ({})", e.event_type, e.id);
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
    }

    // Cleanup
    cleanup(&client, &session.id, &agent.id).await;
    tracing::info!("Streaming events cookbook completed");

    Ok(())
}
