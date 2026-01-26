# Cookbook Specification

Runnable examples demonstrating SDK capabilities.

## Purpose

Cookbooks provide practical, copy-paste-ready examples that:
- Validate SDK functionality against a live server
- Serve as integration tests (compile/parse check in CI)
- Document real-world usage patterns

## Structure

```
cookbook/
├── README.md           # Server setup, links to language cookbooks
├── rust/               # Rust cookbook
│   ├── README.md
│   ├── Cargo.toml
│   └── src/main.rs
├── python/             # Python cookbook
│   ├── README.md
│   ├── pyproject.toml
│   └── src/main.py
└── typescript/         # TypeScript cookbook
    ├── README.md
    ├── package.json
    ├── tsconfig.json
    └── src/main.ts
```

## Required Example: Dad Jokes Agent

Each language must implement the "Dad Jokes Agent" demonstrating:

1. **Client initialization** - Read from environment variables
2. **Agent creation** - Create agent with name and system prompt
3. **Session creation** - Create session for the agent
4. **Message sending** - Send user message
5. **Event streaming** - Stream and handle SSE events
6. **Text extraction** - Parse message content from event data

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `EVERRUNS_API_KEY` | Yes | API key for authentication |
| `EVERRUNS_API_URL` | No | Override base URL (default: production) |

### Agent Configuration

```
Name: "Dad Jokes Bot"
System Prompt: "You are a dad joke expert. Tell one short, cheesy dad joke."
User Message: "Tell me a dad joke"
```

### Event Handling

Handle these event types:
- `input.message` - Print user message text
- `output.message.completed` - Print agent response text
- `turn.completed` - Exit successfully
- `turn.failed` - Exit with error indication

### Output Format

```
Created agent: agt_...
Created session: ses_...

Input: Tell me a dad joke
Output: [dad joke here]

[Turn completed]
```

### Verbose Mode

Support `--verbose` or `-v` flag to print full JSON event payloads.

## CI Requirements

Cookbooks must:
- Compile/parse successfully (checked in CI)
- Pass linting for the language
- NOT require a running server (CI only validates syntax/types)

### CI Job Structure

Single `check-cookbooks` job that:
1. Sets up toolchains for all languages
2. Checks each cookbook compiles/parses
3. Runs language-specific linters

## Local Development

### Server Setup

```bash
cargo install --git https://github.com/everruns/everruns everruns-server
export DEFAULT_ANTHROPIC_API_KEY=sk-ant-...
DEV_MODE=1 everruns-server
```

### Running Cookbooks

```bash
# Common dev environment
export EVERRUNS_API_KEY=fake-key
export EVERRUNS_API_URL=http://localhost:9000

# Rust
cd cookbook/rust && cargo run

# Python
cd cookbook/python && uv run python src/main.py

# TypeScript
cd cookbook/typescript && npx tsx src/main.ts
```

## Justfile Commands

| Command | Description |
|---------|-------------|
| `check-cookbook` | Check all cookbooks compile |
| `check-cookbook-rust` | Check Rust cookbook |
| `check-cookbook-python` | Check Python cookbook |
| `check-cookbook-typescript` | Check TypeScript cookbook |
| `lint-cookbook` | Lint all cookbooks |
| `run-cookbook-rust` | Run Rust cookbook |
| `run-cookbook-python` | Run Python cookbook |
| `run-cookbook-typescript` | Run TypeScript cookbook |

## Text Extraction

Events contain nested message data. Extract text parts:

```json
{
  "message": {
    "content": [
      { "type": "text", "text": "The actual joke" }
    ]
  }
}
```

Filter by `type == "text"` and concatenate all text values.
