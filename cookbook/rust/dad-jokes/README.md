# Dad Jokes Agent

Creates a dad jokes agent and asks for a joke.

## Run

```bash
# Install and start server in dev mode
cargo install --git https://github.com/everruns/everruns everruns-server
DEV_MODE=1 everruns-server

# Set environment (dev mode values)
export EVERRUNS_ORG=org_00000000000000000000000000000001
export EVERRUNS_API_KEY=fake-key
export EVERRUNS_API_URL=http://localhost:9000

# Run the cookbook
cargo run -p dad-jokes
```

## What it does

1. Creates an agent with a dad jokes personality
2. Creates a session
3. Asks for a dad joke
4. Streams the response
5. Cleans up
