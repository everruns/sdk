/**
 * Call a real agent from code with the AgentClient client.
 *
 * export EVERRUNS_AGENT_URL=https://app.everruns.com/api/v1/channels/apichan_...
 * export EVERRUNS_AGENT_KEY=evr_ak_...
 * npx tsx examples/agent.ts
 */
import { AgentClient } from "../src/index.js";

async function main() {
  // Reads EVERRUNS_AGENT_URL and EVERRUNS_AGENT_KEY
  const agent = new AgentClient();

  const card = await agent.card();
  console.log(`Agent: ${card.name}`);

  // One call: create a session, send a message, wait for the final reply
  console.log(await agent.run("Say hello in one short sentence."));

  // Step by step, with streamed events
  const session = await agent.createSession({ title: "Example" });
  await agent.sendMessage(session.id, "Name three prime numbers.");
  const stream = agent.streamEvents(session.id, { afterSequence: 0 });
  for await (const event of stream) {
    console.log(event.type);
    if (event.type === "turn.completed" || event.type === "turn.failed") {
      stream.abort();
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
