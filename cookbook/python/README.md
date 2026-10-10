# Python Cookbook

Dad Jokes Agent - creates an agent, sends a message, streams the response.

## Run

```bash
# Terminal 1: Start server
export DEFAULT_ANTHROPIC_API_KEY=sk-ant-...  # or DEFAULT_OPENAI_API_KEY
DEV_MODE=1 everruns-server

# Terminal 2: Run example
export EVERRUNS_API_KEY=fake-key
export EVERRUNS_API_URL=http://localhost:9000
uv run python src/main.py
```

## Agent client

`src/agent_client.py` calls one agent with an agent key instead of a personal
access token (`AgentClient` from `everruns_sdk`). Set `EVERRUNS_AGENT_URL` and
`EVERRUNS_AGENT_KEY`, then `uv run python src/agent_client.py`.
