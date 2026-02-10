/**
 * Local Tools Example - Everruns SDK
 *
 * Demonstrates client-side tool execution: the agent requests a tool call,
 * the client executes it locally, and sends the result back.
 *
 * Run: npx tsx src/weather_tools.ts
 * Run with verbose: npx tsx src/weather_tools.ts --verbose
 */

import {
  Everruns,
  type ContentPart,
  type ToolCallInfo,
  extractToolCalls,
  toolResult,
  toolError,
} from "@everruns/sdk";

const SYSTEM_PROMPT =
  "You are a helpful weather assistant. You have access to a tool called `get_weather` " +
  'that accepts a JSON argument `{"city": "<city name>"}` and returns current weather. ' +
  "When the user asks about weather, call the tool and then summarize the result.";

const WEATHER_DATA: Record<string, [number, string]> = {
  paris: [18, "partly cloudy"],
  tokyo: [22, "sunny"],
  "new york": [15, "rainy"],
};

/** Simulated local weather lookup. */
function getWeather(city: string): Record<string, unknown> {
  const [temp, condition] = WEATHER_DATA[city.toLowerCase()] ?? [20, "clear"];
  return { city, temperature_celsius: temp, condition };
}

/** Dispatch a tool call by name and return a ContentPart with the result. */
function handleToolCall(call: ToolCallInfo): ContentPart {
  if (call.name === "get_weather") {
    const city = (call.arguments.city as string) ?? "unknown";
    return toolResult(call.id, getWeather(city));
  }
  return toolError(call.id, `Unknown tool: ${call.name}`);
}

interface MessageData {
  message?: {
    content?: Array<{ type: string; text?: string }>;
  };
}

function extractText(data: unknown): string | null {
  const d = data as MessageData;
  const content = d?.message?.content;
  if (!Array.isArray(content)) return null;
  const texts = content
    .filter((p) => p.type === "text")
    .map((p) => p.text ?? "");
  return texts.length > 0 ? texts.join("") : null;
}

async function main() {
  const verbose =
    process.argv.includes("--verbose") || process.argv.includes("-v");
  const client = devClient();

  // Create agent with tool-aware system prompt
  const agent = await client.agents.create({
    name: "Weather Assistant",
    systemPrompt: SYSTEM_PROMPT,
  });
  console.log(`Created agent: ${agent.id}`);

  // Create session
  const session = await client.sessions.create({ agentId: agent.id });
  console.log(`Created session: ${session.id}\n`);

  // Send user message
  await client.messages.create(session.id, "What's the weather like in Paris?");

  // Stream events and handle tool calls
  const stream = client.events.stream(session.id, { maxRetries: 3 });

  for await (const event of stream) {
    if (verbose) {
      console.log(
        `\n[EVENT] ${event.type}: ${JSON.stringify(event.data, null, 2)}`,
      );
    }

    switch (event.type) {
      case "output.message.completed": {
        const toolCalls = extractToolCalls(event.data);
        if (toolCalls.length > 0) {
          console.log(`Agent requested ${toolCalls.length} tool call(s)`);
          const results: ContentPart[] = toolCalls.map((tc) => {
            console.log(
              `  -> Executing ${tc.name}(${JSON.stringify(tc.arguments)})`,
            );
            return handleToolCall(tc);
          });

          // Send tool results back
          await client.messages.createToolResults(session.id, results);
          console.log("  <- Sent tool results\n");
        } else {
          const text = extractText(event.data);
          if (text) {
            console.log(`Assistant: ${text}`);
          }
        }
        break;
      }

      case "turn.completed":
        console.log("\n[Turn completed]");
        stream.abort();
        return;

      case "turn.failed":
        console.log("\n[Turn failed]");
        stream.abort();
        return;
    }
  }
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
