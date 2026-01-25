# Dad Jokes Agent

Creates a dad jokes agent that knows the current time.

## Run

```bash
# Start the server (from everruns/everruns repo)
cargo install --git https://github.com/everruns/everruns-control-panel

# Set environment
export EVERRUNS_ORG=your-org
export EVERRUNS_API_KEY=your-key
export EVERRUNS_API_URL=http://localhost:9000/api

# Run the cookbook
cargo run -p dad-jokes
```

## What it does

1. Creates an agent with a dad jokes personality
2. Creates a session
3. Asks for a dad joke about the current time
4. Streams and prints the response
5. Cleans up
