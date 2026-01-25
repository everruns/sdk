# @everruns/sdk

TypeScript SDK for the Everruns API.

## Installation

\`\`\`bash
npm install @everruns/sdk
\`\`\`

## Quick Start

\`\`\`typescript
import { Everruns } from "@everruns/sdk";

// Uses EVERRUNS_API_KEY environment variable
const client = Everruns.fromEnv("my-org");

// Create an agent
const agent = await client.agents.create({
  name: "Assistant",
  systemPrompt: "You are a helpful assistant."
});

// Create a session
const session = await client.sessions.create({ agentId: agent.id });

// Send a message
await client.messages.create(session.id, { text: "Hello!" });

// Stream events
for await (const event of client.events.stream(session.id)) {
  console.log(event.type, event.data);
}
\`\`\`

## Authentication

The SDK uses API key authentication. Set the \`EVERRUNS_API_KEY\` environment variable or pass the key explicitly:

\`\`\`typescript
// From environment variable
const client = Everruns.fromEnv("my-org");

// Explicit key
const client = new Everruns({
  apiKey: "evr_...",
  org: "my-org"
});
\`\`\`

## Streaming Events

The SDK supports SSE streaming with automatic reconnection:

\`\`\`typescript
const stream = client.events.stream(session.id, {
  exclude: ["output.message.delta"],  // Filter out delta events
  sinceId: "evt_..."                   // Resume from event ID
});

for await (const event of stream) {
  switch (event.type) {
    case "output.message.completed":
      console.log("Message:", event.data);
      break;
    case "turn.completed":
      console.log("Turn completed");
      stream.abort();  // Stop streaming
      break;
    case "turn.failed":
      console.error("Turn failed:", event.data);
      break;
  }
}
\`\`\`

## Error Handling

\`\`\`typescript
import { ApiError, AuthenticationError, RateLimitError } from "@everruns/sdk";

try {
  await client.agents.get("invalid-id");
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error("Invalid API key");
  } else if (error instanceof RateLimitError) {
    console.log(\`Retry after \${error.retryAfter} seconds\`);
  } else if (error instanceof ApiError) {
    console.error(\`API error \${error.statusCode}: \${error.message}\`);
  }
}
\`\`\`

## License

MIT
