# Rust SDK Cookbooks

## Setup

```bash
# Install and start server
cargo install --git https://github.com/everruns/everruns everruns-server
DEV_MODE=1 everruns-server

# Set environment
export EVERRUNS_ORG=your-org
export EVERRUNS_API_KEY=your-key
export EVERRUNS_API_URL=http://localhost:9000/api
```

## Run

```bash
cargo run -p dad-jokes
```

## Recipes

- [dad-jokes](dad-jokes/) - Dad jokes agent with current time
