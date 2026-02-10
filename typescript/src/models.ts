/**
 * Core data models for Everruns API.
 */

export interface AgentCapabilityConfig {
  /** Reference to the capability ID */
  ref: string;
  /** Per-agent configuration for this capability (capability-specific) */
  config?: Record<string, unknown>;
}

export interface CapabilityInfo {
  id: string;
  name: string;
  description: string;
  status: string;
  category?: string | null;
  dependencies?: string[];
  icon?: string | null;
  isMcp?: boolean;
}

export interface Agent {
  id: string;
  name: string;
  systemPrompt: string;
  model?: string;
  capabilities?: AgentCapabilityConfig[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateAgentRequest {
  /** Client-supplied agent ID (format: agent_{32-hex}). Auto-generated if omitted. */
  id?: string;
  name: string;
  systemPrompt: string;
  model?: string;
  capabilities?: AgentCapabilityConfig[];
}

/**
 * Generate a random agent ID in the format `agent_<32-hex>`.
 */
export function generateAgentId(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  const hex = Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return `agent_${hex}`;
}

export interface Session {
  id: string;
  agentId: string;
  status: "active" | "completed" | "failed";
  capabilities?: AgentCapabilityConfig[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateSessionRequest {
  agentId: string;
  capabilities?: AgentCapabilityConfig[];
}

export interface Message {
  id: string;
  sessionId: string;
  role: "user" | "assistant" | "tool_result";
  content: ContentPart[];
  createdAt: string;
}

export interface ContentPart {
  type: "text" | "image" | "image_file" | "tool_call" | "tool_result";
  text?: string;
  imageUrl?: string;
  imageId?: string;
  /** Tool call ID (for tool_call parts) */
  id?: string;
  /** Tool name (for tool_call parts) */
  name?: string;
  /** Tool arguments (for tool_call parts) */
  arguments?: Record<string, unknown>;
  /** Tool call ID this result corresponds to (for tool_result parts) */
  tool_call_id?: string;
  /** Tool result value (for tool_result parts) */
  result?: unknown;
  /** Error message (for tool_result parts) */
  error?: string;
}

/** Extracted tool call information */
export interface ToolCallInfo {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

/** Create a tool result content part with a successful result */
export function toolResult(
  toolCallId: string,
  result: unknown,
): ContentPart {
  return { type: "tool_result", tool_call_id: toolCallId, result };
}

/** Create a tool result content part with an error */
export function toolError(
  toolCallId: string,
  error: string,
): ContentPart {
  return { type: "tool_result", tool_call_id: toolCallId, error };
}

/** Extract tool calls from event data (`data.message.content`) */
export function extractToolCalls(
  data: Record<string, unknown>,
): ToolCallInfo[] {
  const message = data.message as
    | { content?: unknown[] }
    | undefined;
  const content = message?.content;
  if (!Array.isArray(content)) return [];

  const calls: ToolCallInfo[] = [];
  for (const part of content) {
    const p = part as Record<string, unknown>;
    if (
      p.type === "tool_call" &&
      typeof p.id === "string" &&
      typeof p.name === "string"
    ) {
      calls.push({
        id: p.id,
        name: p.name,
        arguments: (p.arguments as Record<string, unknown>) ?? {},
      });
    }
  }
  return calls;
}

export interface MessageInput {
  role: "user" | "tool_result";
  content: ContentPart[];
}

export interface Controls {
  modelId?: string;
}

export interface CreateMessageRequest {
  message: MessageInput;
  controls?: Controls;
}

export interface Event {
  id: string;
  type: string;
  data: Record<string, unknown>;
  createdAt: string;
}

export interface StreamOptions {
  /** Resume from this event ID */
  sinceId?: string;
  /** Event types to exclude from the stream */
  exclude?: string[];
  /** Maximum number of reconnection attempts (undefined = unlimited) */
  maxRetries?: number;
}
