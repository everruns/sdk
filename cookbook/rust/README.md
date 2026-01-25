# Rust SDK Cookbooks

## Setup

```bash
# Install and start server in dev mode
cargo install --git https://github.com/everruns/everruns everruns-server
DEV_MODE=1 everruns-server

# Set environment (dev mode values)
export EVERRUNS_ORG=org_00000000000000000000000000000001
export EVERRUNS_API_KEY=fake-key
export EVERRUNS_API_URL=http://localhost:9000
```

## Run

```bash
cargo run -p dad-jokes
```

## Recipes

- [dad-jokes](dad-jokes/) - Dad jokes agent example
