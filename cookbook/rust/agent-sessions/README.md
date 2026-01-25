# Agent Sessions

Demonstrates agent and session lifecycle management.

## Covered Scenarios

- **Create agent**: Basic and with full options
- **List agents**: Retrieve all agents in org
- **Create session**: Basic and with model override
- **Session lifecycle**: Create, use, delete
- **Cleanup**: Proper resource cleanup

## Run

```bash
export EVERRUNS_ORG=your-org
export EVERRUNS_API_KEY=your-key
# Optional: export EVERRUNS_API_URL=http://localhost:8080/api

cargo run -p agent-sessions
```

## Key Patterns

```rust
// Create agent with full options
let req = CreateAgentRequest {
    name: "My Agent".to_string(),
    system_prompt: "You are helpful.".to_string(),
    description: Some("A demo agent".to_string()),
    default_model_id: Some("claude-sonnet-4-20250514".to_string()),
    tags: vec!["demo".to_string()],
};
let agent = client.agents().create_with_options(req).await?;

// Create session with model override
let req = CreateSessionRequest {
    agent_id: agent.id.clone(),
    title: Some("Test Session".to_string()),
    model_id: Some("gpt-4o".to_string()),
};
let session = client.sessions().create_with_options(req).await?;
```
