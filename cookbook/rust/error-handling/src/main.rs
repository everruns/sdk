//! Error Handling Cookbook
//!
//! Demonstrates graceful handling of various API errors.

use cookbook_common::{cleanup_agent, dev_client, init_tracing};
use everruns_sdk::Error;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing();

    let client = dev_client()?;
    tracing::info!("Client initialized");

    // 1. Not Found Error (API error with 404 status)
    tracing::info!("--- Not Found Error ---");
    match client.agents().get("nonexistent-agent-id").await {
        Ok(agent) => tracing::info!("Found agent: {}", agent.name),
        Err(Error::Api {
            status: 404,
            message,
            ..
        }) => {
            tracing::info!("Expected NotFound (404): {}", message);
        }
        Err(e) => tracing::info!("Error: {}", e),
    }

    // 2. Validation Error - Create agent with empty name
    tracing::info!("--- Validation Error ---");
    match client.agents().create("", "System prompt").await {
        Ok(agent) => {
            tracing::info!("Created agent (unexpected): {}", agent.id);
            cleanup_agent(&client, &agent.id).await;
        }
        Err(Error::Api {
            status: 400,
            message,
            code,
        }) => {
            tracing::info!("Expected validation error (400): {} - {}", code, message);
        }
        Err(e) => tracing::info!("Error: {}", e),
    }

    // 3. Demonstrate error matching patterns
    tracing::info!("--- Error Matching Patterns ---");
    let result = client.sessions().get("nonexistent-session").await;
    handle_api_error(result);

    // 4. Create and delete to show successful flow
    tracing::info!("--- Successful Flow ---");
    let agent = client
        .agents()
        .create("Error Handling Test", "You are a test agent.")
        .await?;
    tracing::info!("Created agent: {}", agent.id);

    // Delete the agent
    client.agents().delete(&agent.id).await?;
    tracing::info!("Deleted agent");

    // 5. Try to access deleted agent
    tracing::info!("--- Accessing Deleted Resource ---");
    match client.agents().get(&agent.id).await {
        Ok(_) => tracing::warn!("Agent still exists (unexpected)"),
        Err(Error::Api { status: 404, .. }) => {
            tracing::info!("Correctly got 404 for deleted agent");
        }
        Err(e) => tracing::info!("Error: {}", e),
    }

    tracing::info!("Error handling cookbook completed");
    Ok(())
}

/// Demonstrates comprehensive error handling pattern
fn handle_api_error<T>(result: Result<T, Error>) {
    match result {
        Ok(_) => tracing::info!("Request succeeded"),
        Err(Error::Auth(msg)) => {
            tracing::error!("Authentication failed: {}", msg);
            tracing::error!("Check EVERRUNS_API_KEY environment variable");
        }
        Err(Error::Api {
            status: 404,
            message,
            ..
        }) => {
            tracing::warn!("Resource not found: {}", message);
        }
        Err(Error::Api {
            status: 429,
            message,
            ..
        }) => {
            tracing::warn!("Rate limited: {}", message);
            tracing::info!("Implement retry with exponential backoff");
        }
        Err(Error::Api {
            status: 400,
            message,
            code,
        }) => {
            tracing::warn!("Validation error: {} - {}", code, message);
        }
        Err(Error::Api {
            status,
            message,
            code,
        }) => {
            tracing::error!("API error ({}): {} - {}", status, code, message);
        }
        Err(Error::Network(e)) => {
            tracing::error!("Network error: {}", e);
            tracing::error!("Check EVERRUNS_API_URL and network connectivity");
        }
        Err(Error::EnvVar(var)) => {
            tracing::error!("Missing environment variable: {}", var);
        }
        Err(e) => {
            tracing::error!("Other error: {}", e);
        }
    }
}
