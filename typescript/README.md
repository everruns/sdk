# @everruns/sdk

TypeScript SDK for the Everruns API.

## Installation

```bash
npm install @everruns/sdk
```

## Quick Start

```typescript
import { Everruns } from "@everruns/sdk";

// Uses EVERRUNS_API_KEY and optional EVERRUNS_ORG_ID environment variables
const client = Everruns.fromEnv();

// Create an agent
const agent = await client.agents.create({
name: "Assistant",
systemPrompt: "You are a helpful assistant."
});

// Create a session
const session = await client.sessions.create({ agentId: agent.id });

// Send a message
await client.messages.create(session.id, "Hello!");

// Stream events
for await (const event of client.events.stream(session.id)) {
console.log(event.type, event.data);
}
```

## Initial Files

```typescript
const session = await client.sessions.create({
agentId: "agent_...",
initialFiles: [
{
path: "/workspace/README.md",
content: "# Demo Project\n",
encoding: "text",
isReadonly: true,
},
{
path: "/workspace/src/app.py",
content: 'print("hello")\n',
encoding: "text",
},
],
});
```

Runnable example: [`examples/initial-files.ts`](examples/initial-files.ts)
Run locally from this repo with `npx tsx examples/initial-files.ts`.

## Agent Versions

```typescript
const version = await client.agents.createVersion("agent_...", {
changeKind: "manual",
summary: "Baseline",
});

const versions = await client.agents.listVersions("agent_...");
const diff = await client.agents.diffVersions("agent_...", "agentver_1", version.id);
const fork = await client.agents.forkVersion("agent_...", version.id, {
name: "forked-agent",
});
const rollback = await client.agents.rollbackVersion("agent_...", version.id, {
saveVersion: true,
});
```

## Workspaces

Workspaces hold files shared across sessions.

```typescript
const workspace = await client.workspaces.create({ name: "team-docs" });

await client.workspaceFiles.create(
workspace.id,
"/notes/welcome.md",
"# Welcome\n",
{ encoding: "text" },
);
const file = await client.workspaceFiles.read(workspace.id, "/notes/welcome.md");
const files = await client.workspaceFiles.list(workspace.id, { recursive: true });
```

Runnable example: [`examples/workspaces.ts`](examples/workspaces.ts)
Run locally from this repo with `npx tsx examples/workspaces.ts`.

## Memories

Memories are long-term, searchable knowledge stores for agents.

```typescript
const memory = await client.memories.create({ name: "product-knowledge" });

await client.memories.createFile(memory.id, "/facts/product.md", {
content: "# Product\n",
encoding: "text",
});
const results = await client.memories.grepFiles(memory.id, "product");
await client.memories.sync(memory.id);
```

Runnable example: [`examples/memories.ts`](examples/memories.ts)
Run locally from this repo with `npx tsx examples/memories.ts`.

## Authentication

The SDK uses personal access token authentication. Set the `EVERRUNS_API_KEY` environment variable or pass the token explicitly. For personal access tokens with access to multiple organizations, set `EVERRUNS_ORG_ID` or pass `orgId` explicitly:

```typescript
// From environment variable
const client = Everruns.fromEnv();
```

Or with an explicit token and organization:

```typescript
const client = new Everruns({
apiKey: "evr_pat_...",
orgId: "org_..."
});
```

## Streaming Events

The SDK supports SSE streaming with automatic reconnection:

```typescript
const stream = client.events.stream(session.id, {
exclude: ["output.message.delta"], // Filter out delta events
sinceId: "evt_..." // Resume from event ID
});

for await (const event of stream) {
switch (event.type) {
case "output.message.completed":
console.log("Message:", event.data);
break;
case "turn.completed":
console.log("Turn completed");
stream.abort(); // Stop streaming
break;
case "turn.failed":
console.error("Turn failed:", event.data);
break;
}
}
```

## Error Handling

```typescript
import { ApiError, AuthenticationError, RateLimitError } from "@everruns/sdk";

try {
await client.agents.get("invalid-id");
} catch (error) {
if (error instanceof AuthenticationError) {
console.error("Invalid personal access token");
} else if (error instanceof RateLimitError) {
console.log(`Retry after ${error.retryAfter} seconds`);
} else if (error instanceof ApiError) {
console.error(`API error ${error.statusCode}: ${error.message}`);
}
}
```

## License

MIT
