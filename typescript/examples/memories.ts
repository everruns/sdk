/**
 * Example: create a memory, add files, and search them.
 *
 * Run with:
 * `EVERRUNS_API_KEY=evr_... npx tsx examples/memories.ts`
 */

import { Everruns } from "../src/index.js";

async function main() {
  const client = Everruns.fromEnv();

  const memory = await client.memories.create({
    name: "memories-example-ts",
    description: "Long-term knowledge for the agent",
  });
  console.log("Created memory", memory.id);

  await client.memories.createFile(memory.id, "/facts/product.md", {
    content: "# Product\n\nEverruns runs autonomous agents.\n",
    encoding: "text",
  });

  const results = await client.memories.grepFiles(memory.id, "agents");
  console.log(`Found ${results.length} match(es) for 'agents'`);

  const files = await client.memories.listFiles(memory.id);
  console.log(`Memory has ${files.length} file(s)`);

  await client.memories.delete(memory.id);
  console.log("Archived memory");
}

main().catch(console.error);
