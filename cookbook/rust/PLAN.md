# Rust SDK Cookbooks - Implementation Plan

## Overview

Runnable examples demonstrating Rust SDK usage against a live Everruns environment.

## Requirements

### Dev Environment Setup

```bash
# Install Everruns CLI from main repo (dev mode)
cargo install --git https://github.com/everruns/everruns everruns-cli

# Configure for local/dev environment
export EVERRUNS_API_URL=http://localhost:8080/api  # or staging URL
export EVERRUNS_API_KEY=your-api-key
export EVERRUNS_ORG=your-org-id

# For agent model providers (used in CI)
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
```

### CI Integration

- Cookbooks checked with `cargo fmt --check` and `cargo clippy -D warnings`
- Cookbooks compile (no runtime in CI by default)
- Secrets available: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- Optional: E2E test job with live API (gated on schedule/manual trigger)

## Cookbook Structure

```
cookbook/
├── README.md                    # Overview + dev setup
└── rust/
    ├── PLAN.md                  # This file
    ├── Cargo.toml               # Workspace for all cookbooks
    ├── common/                  # Shared utilities
    │   ├── Cargo.toml
    │   └── src/lib.rs           # Dev client helper, cleanup
    ├── error-handling/
    │   ├── Cargo.toml
    │   ├── README.md
    │   └── src/main.rs
    ├── streaming-events/
    │   ├── Cargo.toml
    │   ├── README.md
    │   └── src/main.rs
    ├── agent-sessions/
    │   ├── Cargo.toml
    │   ├── README.md
    │   └── src/main.rs
    ├── file-operations/
    │   ├── Cargo.toml
    │   ├── README.md
    │   └── src/main.rs
    └── image-attachments/
        ├── Cargo.toml
        ├── README.md
        └── src/main.rs
```

## Cookbooks

### 1. error-handling

Demonstrates graceful API error handling:
- Authentication errors (invalid API key)
- Not found errors (missing agent/session)
- Rate limiting with retry-after
- Validation errors
- Network errors with retry

### 2. streaming-events

Demonstrates SSE event streaming:
- Basic event stream consumption
- Filtering events by type (exclude delta for summaries)
- Reconnection with `since_id`
- Event type handling (turn.started, content.delta, turn.completed)
- Cancellation mid-stream

### 3. agent-sessions

Demonstrates agent and session lifecycle:
- Create agent with system prompt
- Create agent with full options (model, tags, description)
- List and filter agents
- Create session with agent
- Session with custom model override
- Session cleanup and deletion

### 4. file-operations

Demonstrates session filesystem:
- List files in session workspace
- Read file contents
- Write file to session
- Multi-file operations

### 5. image-attachments

Demonstrates image handling:
- Upload image via base64
- Attach image to message
- Upload image file
- Reference uploaded image in message

## Common Utilities (cookbook-common)

```rust
//! Shared utilities for cookbook examples

use everruns_sdk::{Everruns, Error};

/// Create a dev client from environment
///
/// Uses EVERRUNS_API_URL if set, otherwise defaults to production.
pub fn dev_client() -> Result<Everruns, Error> {
    let org = std::env::var("EVERRUNS_ORG")
        .expect("EVERRUNS_ORG must be set");

    if let Ok(base_url) = std::env::var("EVERRUNS_API_URL") {
        let api_key = std::env::var("EVERRUNS_API_KEY")
            .expect("EVERRUNS_API_KEY must be set");
        Everruns::with_base_url(api_key, org, &base_url)
    } else {
        Everruns::from_env(org)
    }
}

/// Cleanup helper - delete session and agent
pub async fn cleanup(client: &Everruns, session_id: &str, agent_id: &str) {
    let _ = client.sessions().delete(session_id).await;
    let _ = client.agents().delete(agent_id).await;
}
```

## CI Workflow Addition

```yaml
# Add to .github/workflows/ci.yml

check-cookbooks:
  needs: changes
  if: needs.changes.outputs.rust == 'true' || needs.changes.outputs.cookbook == 'true'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: dtolnay/rust-toolchain@stable
    - uses: Swatinem/rust-cache@v2
      with:
        workspaces: cookbook/rust
    - name: Check cookbooks compile
      run: cd cookbook/rust && cargo check --all
    - name: Lint cookbooks
      run: |
        cd cookbook/rust
        cargo fmt --check --all
        cargo clippy --all -- -D warnings

# Optional: E2E cookbook tests (manual/scheduled)
test-cookbooks-e2e:
  if: github.event_name == 'workflow_dispatch' || github.event_name == 'schedule'
  runs-on: ubuntu-latest
  env:
    EVERRUNS_API_URL: ${{ secrets.EVERRUNS_API_URL }}
    EVERRUNS_API_KEY: ${{ secrets.EVERRUNS_API_KEY }}
    EVERRUNS_ORG: ${{ secrets.EVERRUNS_ORG }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  steps:
    - uses: actions/checkout@v4
    - uses: dtolnay/rust-toolchain@stable
    - uses: Swatinem/rust-cache@v2
      with:
        workspaces: cookbook/rust
    - name: Run agent-sessions cookbook
      run: cd cookbook/rust && cargo run -p agent-sessions
```

## Justfile Additions

```just
# Lint Rust cookbooks
lint-cookbooks-rust:
    cd cookbook/rust && cargo fmt --check --all
    cd cookbook/rust && cargo clippy --all -- -D warnings

# Check cookbooks compile
check-cookbooks:
    cd cookbook/rust && cargo check --all

# Run a specific cookbook (requires env vars)
run-cookbook name:
    cd cookbook/rust && cargo run -p {{name}}
```

## Path Filter Addition

Add to `.github/workflows/ci.yml` changes job:

```yaml
cookbook:
  - 'cookbook/**'
```

## Execution

Each cookbook is a standalone binary:

```bash
# Run a cookbook
cd cookbook/rust
cargo run -p error-handling
cargo run -p streaming-events
cargo run -p agent-sessions
cargo run -p file-operations
cargo run -p image-attachments
```
