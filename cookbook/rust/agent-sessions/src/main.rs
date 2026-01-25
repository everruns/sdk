//! Agent Sessions Cookbook
//!
//! Demonstrates agent and session lifecycle management.

use cookbook_common::{cleanup, cleanup_agent, dev_client, init_tracing};
use everruns_sdk::{CreateAgentRequest, CreateSessionRequest};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing();

    let client = dev_client()?;
    tracing::info!("Client initialized");

    // 1. Create a basic agent
    tracing::info!("--- Create Basic Agent ---");
    let agent = client
        .agents()
        .create("Basic Agent", "You are a helpful assistant.")
        .await?;
    tracing::info!("Created agent: {} ({})", agent.name, agent.id);
    tracing::info!("  Status: {:?}", agent.status);
    tracing::info!("  Created: {}", agent.created_at);

    // 2. Create agent with full options
    tracing::info!("--- Create Agent with Options ---");
    let req = CreateAgentRequest {
        name: "Full Options Agent".to_string(),
        system_prompt: "You are an expert assistant with specific capabilities.".to_string(),
        description: Some("A demonstration agent with all options configured".to_string()),
        default_model_id: Some("claude-sonnet-4-20250514".to_string()),
        tags: vec!["demo".to_string(), "cookbook".to_string()],
    };
    let full_agent = client.agents().create_with_options(req).await?;
    tracing::info!(
        "Created full agent: {} ({})",
        full_agent.name,
        full_agent.id
    );
    tracing::info!("  Description: {:?}", full_agent.description);
    tracing::info!("  Model: {:?}", full_agent.default_model_id);
    tracing::info!("  Tags: {:?}", full_agent.tags);

    // 3. List agents
    tracing::info!("--- List Agents ---");
    let agents = client.agents().list().await?;
    tracing::info!("Found {} agents (showing first 5):", agents.total);
    for a in agents.data.iter().take(5) {
        tracing::info!("  - {} ({:?})", a.name, a.status);
    }

    // 4. Get agent by ID
    tracing::info!("--- Get Agent by ID ---");
    let retrieved = client.agents().get(&agent.id).await?;
    tracing::info!("Retrieved: {} ({})", retrieved.name, retrieved.id);

    // 5. Create basic session
    tracing::info!("--- Create Basic Session ---");
    let session = client.sessions().create(&agent.id).await?;
    tracing::info!("Created session: {}", session.id);
    tracing::info!("  Agent ID: {}", session.agent_id);
    tracing::info!("  Status: {:?}", session.status);

    // 6. Create session with options
    tracing::info!("--- Create Session with Options ---");
    let req = CreateSessionRequest {
        agent_id: full_agent.id.clone(),
        title: Some("Cookbook Demo Session".to_string()),
        model_id: Some("gpt-4o".to_string()), // Override agent's default model
    };
    let full_session = client.sessions().create_with_options(req).await?;
    tracing::info!("Created session: {}", full_session.id);
    tracing::info!("  Title: {:?}", full_session.title);
    tracing::info!("  Model: {:?}", full_session.model_id);

    // 7. List sessions
    tracing::info!("--- List Sessions ---");
    let sessions = client.sessions().list().await?;
    tracing::info!("Found {} sessions", sessions.total);

    // 8. Get session by ID
    tracing::info!("--- Get Session by ID ---");
    let retrieved_session = client.sessions().get(&session.id).await?;
    tracing::info!("Retrieved session: {}", retrieved_session.id);
    tracing::info!("  Status: {:?}", retrieved_session.status);

    // 9. Cleanup
    tracing::info!("--- Cleanup ---");
    cleanup(&client, &session.id, &agent.id).await;
    cleanup(&client, &full_session.id, &full_agent.id).await;
    tracing::info!("Cleaned up all resources");

    // 10. Verify cleanup
    tracing::info!("--- Verify Cleanup ---");
    match client.agents().get(&agent.id).await {
        Ok(_) => tracing::warn!("Agent still exists"),
        Err(_) => tracing::info!("Agent correctly deleted"),
    }

    // Also demonstrate deleting without session (agent only)
    let temp_agent = client
        .agents()
        .create("Temporary Agent", "Temporary")
        .await?;
    cleanup_agent(&client, &temp_agent.id).await;
    tracing::info!("Deleted standalone agent");

    tracing::info!("Agent sessions cookbook completed");
    Ok(())
}
