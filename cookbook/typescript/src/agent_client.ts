/**
 * AgentClient - Everruns SDK Example
 *
 * Calls an existing agent with an agent key: no management token needed.
 *
 * export EVERRUNS_AGENT_URL=https://app.everruns.com/api/v1/channels/apichan_...
 * export EVERRUNS_AGENT_KEY=evr_ak_...
 * Run: npx tsx src/agent_client.ts
 */

import { AgentClient } from "@everruns/sdk";

async function main() {
  // Reads EVERRUNS_AGENT_URL and EVERRUNS_AGENT_KEY
  const agent = new AgentClient();

  const card = await agent.card();
  console.log(`Agent: ${card.name}\n`);

  // One call: create a session, send a message, wait for the final reply
  const reply = await agent.run("Tell me a dad joke");
  console.log(`Reply: ${reply}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
