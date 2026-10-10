# TypeScript Cookbook

Dad Jokes Agent - creates an agent, sends a message, streams the response.

## Run

```bash
# Terminal 1: Start server
export DEFAULT_ANTHROPIC_API_KEY=sk-ant-...  # or DEFAULT_OPENAI_API_KEY
DEV_MODE=1 everruns-server

# Terminal 2: Run example
export EVERRUNS_API_KEY=fake-key
export EVERRUNS_API_URL=http://localhost:9000
npm install
npx tsx src/main.ts
```

## Agent client

`src/agent_client.ts` calls an existing agent with an agent key instead of a
management token:

```bash
export EVERRUNS_AGENT_URL=https://app.everruns.com/api/v1/channels/apichan_...
export EVERRUNS_AGENT_KEY=evr_ak_...
npx tsx src/agent_client.ts
```
