/**
 * Everruns SDK for TypeScript/Node.js
 *
 * @example
 * ```typescript
 * import { Everruns } from "@everruns/sdk";
 *
 * // Uses EVERRUNS_API_KEY environment variable
 * const client = Everruns.fromEnv();
 *
 * // Create an agent
 * const agent = await client.agents.create({
 *   name: "assistant",
 *   systemPrompt: "You are a helpful assistant."
 * });
 *
 * // Create a session
 * const session = await client.sessions.create({ agentId: agent.id });
 *
 * // Send a message
 * await client.messages.create(session.id, "Hello!");
 * ```
 */

export {
  Everruns,
  type EverrunsOptions,
  CHANGE_REASON_HEADER,
  MAX_CHANGE_REASON_CHARS,
  encodeChangeReason,
} from "./client.js";
export { ApiKey } from "./auth.js";
export * from "./models.js";
export {
  AgentClient,
  END_USER_HEADER,
  type AgentClientOptions,
  type AgentCard,
  type AgentSession,
  type AgentSessionList,
  type AgentMessage,
  type RuntimeToken,
  type CreateAgentSessionOptions,
  type ListAgentSessionsOptions,
  type ListAgentEventsOptions,
  type SendAgentMessageOptions,
  type StreamAgentEventsOptions,
} from "./agent.js";
export * from "./errors.js";
export {
  EventStream,
  READ_TIMEOUT_MS,
  DEFAULT_IDLE_TIMEOUT_MS,
} from "./sse.js";
