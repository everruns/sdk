//! Example: create a workspace and manage its files
//!
//! Run with:
//! `EVERRUNS_API_KEY=evr_... cargo run --example workspaces`

use everruns_sdk::{CreateWorkspaceRequest, Error, Everruns};

#[tokio::main]
async fn main() -> Result<(), Error> {
    let client = Everruns::from_env()?;

    let workspace = client
        .workspaces()
        .create(
            CreateWorkspaceRequest::new("workspaces-example-rs")
                .description("Shared files for the team"),
        )
        .await?;
    println!("Created workspace {}", workspace.id);

    client
        .workspace_files()
        .create(
            &workspace.id,
            "/notes/welcome.md",
            "# Welcome\n\nShared workspace files live here.\n",
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

    client.workspaces().delete(&workspace.id).await?;
    println!("Archived workspace");

    Ok(())
}
