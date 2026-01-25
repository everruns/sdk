# Rust SDK Cookbooks

Runnable examples demonstrating Everruns Rust SDK usage.

## Prerequisites

```bash
# Install Everruns CLI from main repo (dev mode)
cargo install --git https://github.com/everruns/everruns everruns-cli

# Configure environment
export EVERRUNS_ORG=your-org-id
export EVERRUNS_API_KEY=your-api-key

# Optional: Point to dev/staging environment
export EVERRUNS_API_URL=http://localhost:8080/api

# For agent model providers (required for live tests)
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
```

## Recipes

| Recipe | Description |
|--------|-------------|
| [error-handling](error-handling/) | Handle API errors gracefully |
| [streaming-events](streaming-events/) | Subscribe to SSE events |
| [agent-sessions](agent-sessions/) | Create agents and manage sessions |
| [file-operations](file-operations/) | Session filesystem operations |
| [image-attachments](image-attachments/) | Attach images to messages |

## Run

```bash
# Run a specific cookbook
cargo run -p agent-sessions
cargo run -p streaming-events
cargo run -p error-handling
cargo run -p file-operations
cargo run -p image-attachments

# Or from repo root
just run-cookbook agent-sessions
```

## Development

```bash
# Check compile
cargo check --all

# Format
cargo fmt --all

# Lint
cargo clippy --all -- -D warnings
```

## Structure

```
rust/
├── Cargo.toml              # Workspace definition
├── common/                 # Shared utilities (cookbook-common crate)
│   ├── Cargo.toml
│   └── src/lib.rs          # dev_client(), cleanup helpers
├── error-handling/
│   ├── Cargo.toml
│   ├── README.md
│   └── src/main.rs
├── streaming-events/
│   ├── ...
└── ...
```

## Common Utilities

The `cookbook-common` crate provides shared helpers:

```rust
use cookbook_common::{dev_client, cleanup, init_tracing};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    init_tracing();  // Set up logging

    let client = dev_client()?;  // Create client from env vars

    // ... do work ...

    cleanup(&client, &session.id, &agent.id).await;  // Clean up resources
    Ok(())
}
```
