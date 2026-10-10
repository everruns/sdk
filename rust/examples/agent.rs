//! Call an agent from code with an agent key.
//!
//! Needs a real agent URL and key:
//!
//! ```bash
//! export EVERRUNS_AGENT_URL=https://app.everruns.com/api/v1/channels/apichan_...
//! export EVERRUNS_AGENT_KEY=evr_ak_...
//! cargo run --example agent
//! ```

use everruns_sdk::{AgentClient, Error};

#[tokio::main]
async fn main() -> Result<(), Error> {
    // Reads EVERRUNS_AGENT_URL and EVERRUNS_AGENT_KEY.
    let agent = AgentClient::from_env()?;

    let card = agent.card().await?;
    println!("Agent: {}", card.name);

    // One call: new session, send, wait for the turn, return the reply.
    let reply = agent.run("Say hello in one sentence.", None).await?;
    println!("Reply: {reply}");

    // Run again in a session of your own.
    let session = agent.create_session(Some("Example"), None).await?;
    let second = agent.run("Now say goodbye.", Some(&session.id)).await?;
    println!("Second reply: {second}");
    Ok(())
}
