//! Example: create a session with initial files
//!
//! Run with:
//! `EVERRUNS_API_KEY=evr_... cargo run --example initial_files`

use everruns_sdk::{CreateSessionRequest, Error, Everruns, InitialFile};

#[tokio::main]
async fn main() -> Result<(), Error> {
    let client = Everruns::from_env()?;

    let agent = client
        .agents()
        .create(
            "Initial Files Example",
            "You are a helpful assistant. Read the starter files before answering.",
        )
        .await?;

    let session = client
        .sessions()
        .create_with_options(
            CreateSessionRequest::new()
                .agent_id(&agent.id)
                .title("Session with starter files")
                .initial_files(vec![
                    InitialFile::new(
                        "/workspace/README.md",
                        "# Demo Project\n\nThis workspace contains starter files.\n",
                    )
                    .encoding("text")
                    .is_readonly(true),
                    InitialFile::new(
                        "/workspace/src/app.py",
                        "def greet(name: str) -> str:\n    return f\"hello, {name}\"\n",
                    )
                    .encoding("text"),
                ]),
        )
        .await?;

    println!("Created session {}", session.id);
    println!("Starter files:");
    println!("  - /workspace/README.md");
    println!("  - /workspace/src/app.py");

    let message = client
        .messages()
        .create(
            &session.id,
            "Summarize the project and suggest one improvement to src/app.py.",
        )
        .await?;

    println!("Created message {}", message.id);

    client.sessions().delete(&session.id).await?;
    client.agents().delete(&agent.id).await?;

    Ok(())
}
