//! Example: use a session's workspace and manage its files
//!
//! Every session owns a workspace; there is no standalone workspace creation.
//!
//! Run with:
//! `EVERRUNS_API_KEY=evr_... cargo run --example workspaces`

use everruns_sdk::{Error, Everruns};

#[tokio::main]
async fn main() -> Result<(), Error> {
    let client = Everruns::from_env()?;

    let session = client.sessions().create().await?;
    let workspace_id = session
        .workspace_id
        .clone()
        .expect("session should expose its workspace_id");
    let workspace = client.workspaces().get(&workspace_id).await?;
    println!("Session {} uses workspace {}", session.id, workspace.id);

    client
        .workspace_files()
        .create(
            &workspace.id,
            "/notes/welcome.md",
            "# Welcome\n\nWorkspace files live here.\n",
            Some("text"),
        )
        .await?;

    let file = client
        .workspace_files()
        .read(&workspace.id, "/notes/welcome.md")
        .await?;
    println!("Read {}:", file.path);
    println!("{}", file.content.unwrap_or_default());

    let files = client
        .workspace_files()
        .list(&workspace.id, None, Some(true))
        .await?;
    println!("Workspace has {} file(s)", files.data.len());

    client.sessions().delete(&session.id).await?;
    println!("Deleted session");

    Ok(())
}
