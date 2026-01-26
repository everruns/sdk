/**
 * Dad Jokes Agent - Everruns SDK Example
 *
 * Run: npx tsx src/main.ts
 * Run with verbose: npx tsx src/main.ts --verbose
 */

import { Everruns } from "@everruns/sdk";

async function main() {
  const verbose =
    process.argv.includes("--verbose") || process.argv.includes("-v");
  const client = devClient();

  // Create agent
  const agent = await client.agents.create({
    name: "Dad Jokes Bot",
    systemPrompt: "You are a dad joke expert. Tell one short, cheesy dad joke.",
  });
  console.log(`Created agent: ${agent.id}`);

  // Create session
  const session = await client.sessions.create({ agentId: agent.id });
  console.log(`Created session: ${session.id}\n`);

  // Send message
  await client.messages.create(session.id, {
    text: "Tell me a dad joke",
  });

  // Stream events
  const stream = client.events.stream(session.id);

  for await (const event of stream) {
    if (verbose) {
      console.log(
        `\n[EVENT] ${event.type}: ${JSON.stringify(event.data, null, 2)}`,
      );
    }

    switch (event.type) {
      case "input.message": {
        const text = extractText(event.data);
        if (text) {
          console.log(`Input: ${text}`);
        } else {
          console.log(`Input (raw): ${JSON.stringify(event.data, null, 2)}`);
        }
        break;
      }

      case "output.message.completed": {
        const text = extractText(event.data);
        if (text) {
          console.log(`Output: ${text}`);
        } else {
          console.log(`Output (raw): ${JSON.stringify(event.data, null, 2)}`);
        }
        break;
      }

      case "turn.completed":
        console.log("\n[Turn completed]");
        return;

      case "turn.failed":
        console.log("\n[Turn failed]");
        return;
    }
  }
}

interface MessageData {
  message?: {
    content?: Array<{
      type: string;
      text?: string;
    }>;
  };
}

function extractText(data: unknown): string | null {
  const messageData = data as MessageData;
  const content = messageData?.message?.content;

  if (!Array.isArray(content)) {
    return null;
  }

  const texts = content
    .filter((part) => part.type === "text")
    .map((part) => part.text ?? "");

  return texts.length > 0 ? texts.join("") : null;
}

function devClient(): Everruns {
  const apiKey = process.env.EVERRUNS_API_KEY;
  if (!apiKey) {
    throw new Error("EVERRUNS_API_KEY environment variable required");
  }

  const baseUrl = process.env.EVERRUNS_API_URL;

  return new Everruns({ apiKey, baseUrl });
}

main().catch(console.error);
