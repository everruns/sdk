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
  role: "user" | "assistant";
  content: ContentPart[];
  createdAt: string;
}

export interface ContentPart {
  type: "text" | "image";
  text?: string;
  imageUrl?: string;
}

export interface MessageInput {
  role: "user";
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
