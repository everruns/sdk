/**
 * Core data models for Everruns API.
 */

export interface Agent {
  id: string;
  name: string;
  systemPrompt: string;
  model?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateAgentRequest {
  name: string;
  systemPrompt: string;
  model?: string;
}

export interface Session {
  id: string;
  agentId: string;
  status: "active" | "completed" | "failed";
  createdAt: string;
  updatedAt: string;
}

export interface CreateSessionRequest {
  agentId: string;
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

export interface CreateMessageRequest {
  text?: string;
  imageUrls?: string[];
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
