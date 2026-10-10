//! Agent Client Example - Everruns SDK
//!
//! Calls an existing agent with an agent key: no management token, no agent
//! creation. Create the agent and its API channel in Everruns first.
//!
//! Run: cargo run --bin agent-client
//! Needs EVERRUNS_AGENT_URL and EVERRUNS_AGENT_KEY.

use everruns_sdk::AgentClient;
use futures::StreamExt;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let agent = AgentClient::from_env()?;
    println!("Agent: {}\n", agent.card().await?.name);

    // One call: session, message, wait for the turn, final text.
    println!("{}\n", agent.run("Tell me a dad joke", None).await?);

    // Or follow the stream yourself.
    let session = agent.create_session(Some("Cookbook"), None).await?;
    agent
        .send_message(&session.id, "Tell me another one", None)
        .await?;
    let mut stream = agent.stream_events(&session.id, None, Some(0));
    while let Some(event) = stream.next().await {
        let event = event?;
        match event.event_type.as_str() {
            "turn.completed" => break,
            "turn.failed" => return Err("turn failed".into()),
            "output.message.completed" => {
                println!("{}", event.data["message"]["content"][0]["text"])
            }
            _ => {}
        }
    }
    stream.stop();
    Ok(())
}
