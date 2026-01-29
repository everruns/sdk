/**
 * Basic usage example for Everruns SDK.
 *
 * Set EVERRUNS_API_KEY environment variable before running:
 * export EVERRUNS_API_KEY=evr_...
 * npx tsx examples/basic.ts
 */
import { Everruns } from "@everruns/sdk";

async function main() {
  // Create client using EVERRUNS_API_KEY env var
  const client = Everruns.fromEnv();

  // Create an agent
  const agent = await client.agents.create({
    name: "Assistant",
    systemPrompt: "You are a helpful assistant.",
  });
  console.log("Created agent:");
  console.log("  Name:", agent.name);
  console.log("  ID:", agent.id);
  console.log("  Created:", agent.createdAt);

  // Create a session
  const session = await client.sessions.create({ agentId: agent.id });
  console.log("Created session:");
  console.log("  ID:", session.id);
  console.log("  Agent:", session.agentId);
  console.log("  Status:", session.status);
  console.log("  Created:", session.createdAt);

  // Send a message
  const message = await client.messages.create(session.id, {
    text: "Hello! What can you help me with?",
  });
  console.log("Sent message:", message.id);

  // Stream events
  console.log("Streaming events...");
  const stream = client.events.stream(session.id, {
    exclude: ["output.message.delta"],
  });

  for await (const event of stream) {
    console.log(`[${event.type}]`, JSON.stringify(event.data).slice(0, 100));

    if (event.type === "turn.completed" || event.type === "turn.failed") {
      break;
    }
  }

  console.log("Done!");
}

main().catch(console.error);
