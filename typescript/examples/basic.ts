/**
 * Basic usage example for Everruns SDK.
 *
 * Set EVERRUNS_API_KEY environment variable before running:
 * export EVERRUNS_API_KEY=evr_...
 * npx tsx examples/basic.ts
 */
import { Everruns, generateHarnessId } from "../src/index.js";

async function main() {
  // Create client using EVERRUNS_API_KEY env var
  const client = Everruns.fromEnv();

  // Create an agent with current_time capability
  const agent = await client.agents.create({
    name: "Assistant",
    systemPrompt: "You are a helpful assistant.",
    capabilities: [{ ref: "current_time" }],
  });
  console.log("Created agent:");
  console.log("  Name:", agent.name);
  console.log("  ID:", agent.id);
  console.log("  Capabilities:", agent.capabilities);
  console.log("  Created:", agent.createdAt);

  // Create a session with a harness (agent is optional)
  const harnessId = generateHarnessId();
  const session = await client.sessions.create({
    harnessId,
    agentId: agent.id,
    capabilities: [{ ref: "current_time" }],
  });
  console.log("Created session:");
  console.log("  ID:", session.id);
  console.log("  Harness:", session.harnessId);
  console.log("  Agent:", session.agentId);
  console.log("  Status:", session.status);
  console.log("  Created:", session.createdAt);

  // Send a message that uses the current_time capability
  const message = await client.messages.create(
    session.id,
    "What time is it right now? Generate a short joke about the current time.",
  );
  console.log("Sent message:", message.id);

  // Stream events
  console.log("Streaming events...");
  const stream = client.events.stream(session.id, {
    exclude: ["output.message.delta"],
  });

  for await (const event of stream) {
    console.log(`[${event.type}]`, JSON.stringify(event.data).slice(0, 100));

    if (
      event.type === "output.message.completed" ||
      event.type === "turn.completed" ||
      event.type === "turn.failed"
    ) {
      break;
    }
  }

  console.log("Done!");
}

main().catch(console.error);
