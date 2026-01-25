//! Image Attachments Cookbook
//!
//! Demonstrates attaching images to messages.

use cookbook_common::{cleanup, dev_client, init_tracing};
use everruns_sdk::{ContentPart, CreateMessageRequest, MessageInput, MessageRole};
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
            "Vision Agent",
            "You are a helpful assistant that can analyze images. Describe what you see concisely.",
        )
        .await?;
    tracing::info!("Created agent: {}", agent.id);

    let session = client.sessions().create(&agent.id).await?;
    tracing::info!("Created session: {}", session.id);

    // 1. Send message with image URL
    tracing::info!("--- Image via URL ---");

    // Small 1x1 red PNG for testing (base64 of minimal valid PNG)
    let test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==";

    let req = CreateMessageRequest {
        message: MessageInput {
            role: MessageRole::User,
            content: vec![
                ContentPart::Image {
                    base64: Some(test_image_base64.to_string()),
                    url: None,
                },
                ContentPart::Text {
                    text: "This is a test image (1x1 pixel). Just confirm you received an image."
                        .to_string(),
                },
            ],
        },
        controls: None,
    };

    client
        .messages()
        .create_with_options(&session.id, req)
        .await?;
    tracing::info!("Sent message with base64 image");

    // Stream response
    let mut stream = client.events().stream(&session.id);
    while let Some(event) = stream.next().await {
        match event {
            Ok(e) => {
                if e.event_type == "content.done"
                    && let Some(text) = e.data.get("text")
                {
                    tracing::info!("Agent response: {}", text);
                }
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

    // 2. Show pattern for image URL
    tracing::info!("--- Image URL Pattern (example) ---");
    tracing::info!("To use an image URL:");
    tracing::info!(
        r#"  ContentPart::Image {{
    url: Some("https://example.com/image.png".to_string()),
    base64: None,
  }}"#
    );

    // 3. Show pattern for uploaded image
    tracing::info!("--- Uploaded Image Pattern (example) ---");
    tracing::info!("To use an uploaded image by ID:");
    tracing::info!(
        r#"  ContentPart::ImageFile {{
    image_id: "img_abc123".to_string(),
  }}"#
    );
    tracing::info!("Image upload API: POST /v1/orgs/{{org}}/images");

    // Cleanup
    cleanup(&client, &session.id, &agent.id).await;
    tracing::info!("Image attachments cookbook completed");

    Ok(())
}
