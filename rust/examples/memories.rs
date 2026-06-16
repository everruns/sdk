//! Example: create a memory, add files, and search them
//!
//! Run with:
//! `EVERRUNS_API_KEY=evr_... cargo run --example memories`

use everruns_sdk::{CreateMemoryRequest, Error, Everruns};

#[tokio::main]
async fn main() -> Result<(), Error> {
    let client = Everruns::from_env()?;

    let memory = client
        .memories()
        .create(
            CreateMemoryRequest::new("memories-example-rs")
                .description("Long-term knowledge for the agent"),
        )
        .await?;
    println!("Created memory {}", memory.id);

    client
        .memories()
        .create_file(
            &memory.id,
            "/facts/product.md",
            "# Product\n\nEverruns runs autonomous agents.\n",
            Some("text"),
        )
        .await?;

    let results = client
        .memories()
        .grep_files(&memory.id, "agents", None)
        .await?;
    println!("Found {} match(es) for 'agents'", results.data.len());

    let files = client.memories().list_files(&memory.id).await?;
    println!("Memory has {} file(s)", files.data.len());

    client.memories().delete(&memory.id).await?;
    println!("Archived memory");

    Ok(())
}
