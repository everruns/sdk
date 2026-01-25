# Everruns SDK Cookbook

Runnable examples for the Everruns SDK.

## Setup

```bash
# Start server (from everruns-control-panel repo)
cargo install --git https://github.com/everruns/everruns-control-panel

# Set environment
export EVERRUNS_ORG=your-org
export EVERRUNS_API_KEY=your-key
export EVERRUNS_API_URL=http://localhost:8080/api
```

## Run

```bash
cd cookbook/rust
cargo run -p dad-jokes
```

## Recipes

| Recipe | Description |
|--------|-------------|
| [dad-jokes](rust/dad-jokes/) | Dad jokes agent with current time |
