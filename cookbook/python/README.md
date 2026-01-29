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
