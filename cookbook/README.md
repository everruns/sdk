# Everruns SDK Cookbook

Practical, runnable recipes for common use cases.

## Quick Start

### Prerequisites

```bash
# Install Everruns CLI (dev mode)
cargo install --git https://github.com/everruns/everruns everruns-cli

# Set environment variables
export EVERRUNS_ORG=your-org-id
export EVERRUNS_API_KEY=your-api-key

# Optional: Use dev/staging environment
export EVERRUNS_API_URL=http://localhost:8080/api
```

### Run a Cookbook

```bash
# From repo root
just run-cookbook agent-sessions
just run-cookbook streaming-events
just run-cookbook error-handling

# Or directly
cd cookbook/rust && cargo run -p agent-sessions
```

## Recipes

| Recipe | Description |
|--------|-------------|
| [error-handling](rust/error-handling/) | Handle API errors gracefully |
| [streaming-events](rust/streaming-events/) | Subscribe to SSE events |
| [agent-sessions](rust/agent-sessions/) | Create agents and manage sessions |
| [file-operations](rust/file-operations/) | Upload and manage files |
| [image-attachments](rust/image-attachments/) | Attach images to messages |

## Structure

```
cookbook/
├── README.md          # This file
└── rust/              # Rust implementations
    ├── Cargo.toml     # Workspace
    ├── common/        # Shared utilities
    └── <recipe>/      # Individual recipes
```

## Development

### Lint Cookbooks

```bash
just lint-cookbooks
```

### Format Cookbooks

```bash
just fmt-cookbooks
```

### Check Compile

```bash
just check-cookbooks
```

## CI

Cookbooks are checked in CI:
- Compile check (`cargo check`)
- Format check (`cargo fmt --check`)
- Lint check (`cargo clippy -D warnings`)

Model provider API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) are available in CI secrets for E2E testing.
