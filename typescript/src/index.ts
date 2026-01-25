/**
 * Everruns SDK for TypeScript/Node.js
 *
 * @example
 * ```typescript
 * import { Everruns } from "@everruns/sdk";
 *
 * // Uses EVERRUNS_API_KEY environment variable
 * const client = Everruns.fromEnv("my-org");
 *
 * // Create an agent
 * const agent = await client.agents.create({
 *   name: "Assistant",
 *   systemPrompt: "You are a helpful assistant."
 * });
 *
 * // Create a session
 * const session = await client.sessions.create({ agentId: agent.id });
 *
 * // Send a message
 * await client.messages.create(session.id, { text: "Hello!" });
 * ```
 */

export { Everruns, type EverrunsOptions } from "./client.js";
export { ApiKey } from "./auth.js";
export * from "./models.js";
export * from "./errors.js";
export { EventStream } from "./sse.js";
