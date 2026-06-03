/**
 * Basic usage example for Everruns SDK.
 *
 * Set EVERRUNS_API_KEY environment variable before running:
 * export EVERRUNS_API_KEY=evr_...
 * npx tsx examples/basic.ts
 */
import { Everruns } from "../src/index.js";

const EVENT_WAIT_MS = 45_000;

async function main() {
  // Create client using EVERRUNS_API_KEY env var
  const client = Everruns.fromEnv();

  // Create an agent with current_time capability
  const agent = await client.agents.create({
    name: "example-assistant-ts",
    systemPrompt: "You are a helpful assistant.",
    capabilities: [{ ref: "current_time" }],
  });
  console.log("Created agent:");
  console.log("  Name:", agent.name);
  console.log("  ID:", agent.id);
  console.log("  Capabilities:", agent.capabilities);
  console.log("  Created:", agent.createdAt);

  // Create a session (agent is optional)
  const session = await client.sessions.create({
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

  const events = stream[Symbol.asyncIterator]();
  try {
    while (true) {
      let next: Awaited<ReturnType<typeof events.next>>;
      try {
        next = await withTimeout(events.next(), EVENT_WAIT_MS);
      } catch {
        console.log("Timed out waiting for turn events; ending demo.");
        break;
      }
      if (next.done) break;

      const event = next.value;
      console.log(`[${event.type}]`, JSON.stringify(event.data).slice(0, 100));

      if (
        event.type === "output.message.completed" ||
        event.type === "turn.completed" ||
        event.type === "turn.failed"
      ) {
        break;
      }
    }
  } finally {
    stream.abort();
  }

  console.log("Done!");
}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout")), ms);
    promise.then(
      (value) => {
        clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        clearTimeout(timer);
        reject(error);
      },
    );
  });
}

main().catch(console.error);
