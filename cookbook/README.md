# Everruns SDK Cookbook

Example: Dad Jokes Agent - creates an agent, sends a message, streams the response.

## Run

```bash
# Start server
cargo install --git https://github.com/everruns/everruns everruns-server
source .env  # needs ANTHROPIC_API_KEY or OPENAI_API_KEY
DEV_MODE=1 everruns-server

# Run example (in another terminal)
export EVERRUNS_ORG=org_00000000000000000000000000000001
export EVERRUNS_API_KEY=fake-key
export EVERRUNS_API_URL=http://localhost:9000

cd cookbook/rust
cargo run
```

## Structure

```
cookbook/
├── README.md
└── rust/
    ├── Cargo.toml
    └── src/main.rs
```
