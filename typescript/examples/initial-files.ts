/**
 * Example: create a session with initial files.
 *
 * Run with:
 * `EVERRUNS_API_KEY=evr_... npx tsx examples/initial-files.ts`
 */

import { Everruns } from "../src/index.js";

async function main() {
  const client = Everruns.fromEnv();

  const agent = await client.agents.applyByName({
    name: "initial-files-example",
    systemPrompt:
      "You are a helpful assistant. Read the starter files before answering.",
  });

  const session = await client.sessions.create({
    agentId: agent.id,
    title: "Session with starter files",
    initialFiles: [
      {
        path: "/workspace/README.md",
        content: "# Demo Project\n\nThis workspace contains starter files.\n",
        encoding: "text",
        isReadonly: true,
      },
      {
        path: "/workspace/src/app.py",
        content: 'def greet(name: str) -> str:\n    return f"hello, {name}"\n',
        encoding: "text",
      },
    ],
  });

  console.log("Created session", session.id);
  console.log("Starter files:");
  console.log("  - /workspace/README.md");
  console.log("  - /workspace/src/app.py");

  const message = await client.messages.create(
    session.id,
    "Summarize the project and suggest one improvement to src/app.py.",
  );

  console.log("Created message", message.id);
}

main().catch(console.error);
