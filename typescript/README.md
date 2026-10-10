# @everruns/sdk

TypeScript SDK for the Everruns API.

## Installation

```bash
npm install @everruns/sdk
```

## Call your agent from code

Use `AgentClient` to call one agent from an application. It holds an agent key
(`evr_ak_...`) that reaches that agent's sessions and nothing else.

```typescript
import { AgentClient } from "@everruns/sdk";

// Reads EVERRUNS_AGENT_URL and EVERRUNS_AGENT_KEY
const agent = new AgentClient();
// or: new AgentClient({ agentUrl: "https://app.everruns.com/api/v1/channels/apichan_...", credential: "evr_ak_..." })

// One call: creates a session, sends the message, waits for the turn
console.log(await agent.run("What can you do?"));

// Act for one of your application's users (the key needs the `end_user` permission)
const alice = agent.forEndUser("customer-42");
console.log(await alice.run("Where is my order?"));

// For a browser or mobile app, never ship the key: mint a short-lived runtime token
const { access_token } = await alice.runtimeToken();
// ...then, in the browser:
const browser = new AgentClient({
  agentUrl: "https://app.everruns.com/api/v1/channels/apichan_...",
  credential: access_token,
});
```

For more control use `createSession`, `sendMessage`, `streamEvents`, `listEvents`,
`getSession`, `cancel`, `answerQuestions` and `submitToolApprovals`.

The management client below (`Everruns`, with a personal access token) is for
managing Everruns: agents, harnesses, workspaces. Its `sessions.create` and
`messages.create` are deprecated for calling an agent; use `AgentClient` instead.

## Management Quick Start

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

## Agent Harness

Each agent owns a harness. Set it on create/update with `harnessName` (preferred) or `harnessId` (mutually exclusive); omit both to default to the org's `generic` harness. A session created from the agent runs on the agent's harness.

```typescript
// Create an agent on a specific harness
const agent = await client.agents.create({
  name: "researcher",
  systemPrompt: "You do deep research.",
  harnessName: "deep-research",
});

// Agent-first session: runs on the agent's harness
const session = await client.sessions.create({ agentName: "researcher" });
```

## Harnesses & Models

Discover and manage harnesses, and browse available models to choose a `defaultModelId`.

```typescript
// Browse harnesses, then create one
const harnesses = await client.harnesses.list(); // or .search("research")
const harness = await client.harnesses.get(harnesses.data[0].id);
const custom = await client.harnesses.create({
  name: "my-harness",
  systemPrompt: "Base instructions for every session.",
});
const examples = await client.harnesses.listExamples();

// List models to pick a default for an agent
const models = await client.models.list();
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

## Change Reasons

Record why a change was made. `withReason` derives a client that sends the
reason with every API request it makes; the server stores it in the changed
entity's history. The original client stays unchanged:

```typescript
await client.withReason("retire the unused agent").agents.delete("agent_123");

const scoped = client.withReason("rotate prompts for the Q3 launch");
await scoped.agents.delete("agent_456");
```

The reason travels in the `Everruns-Change-Reason` header, UTF-8
percent-encoded. A blank reason sends no header. The server trims the reason and rejects it with HTTP 400 (`invalid_change_reason`) when it is longer than 1000 characters, contains control characters other than newline and tab, or looks like it contains a credential.

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
