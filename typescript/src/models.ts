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
  /** Human-readable display name for UI rendering */
  displayName?: string | null;
  /** UI feature strings this capability contributes to */
  features?: string[];
  /** Whether this is an Agent Skill capability */
  isSkill?: boolean;
  /** Risk level for approval requirements (TM-AGENT-005) */
  riskLevel?: "low" | "medium" | "high" | null;
}

export interface Agent {
  id: string;
  /** Addressable name, unique per org (e.g. "customer-support"). */
  name: string;
  /** Human-readable display name shown in UI. Falls back to name when absent. */
  displayName?: string | null;
  systemPrompt: string;
  model?: string;
  capabilities?: AgentCapabilityConfig[];
  initialFiles?: InitialFile[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateAgentRequest {
  /** Client-supplied agent ID (format: agent_{32-hex}). Auto-generated if omitted. */
  id?: string;
  /**
   * Addressable name, unique per org.
   * Format: [a-z0-9]+(-[a-z0-9]+)*, max 64 chars.
   * When a name matches an existing agent, the endpoint has upsert semantics.
   */
  name: string;
  /** Human-readable display name shown in UI. Falls back to name when absent. */
  displayName?: string;
  systemPrompt: string;
  model?: string;
  capabilities?: AgentCapabilityConfig[];
  initialFiles?: InitialFile[];
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

/**
 * Generate a random harness ID in the format `harness_<32-hex>`.
 */
export function generateHarnessId(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  const hex = Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return `harness_${hex}`;
}

export interface Session {
  id: string;
  harnessId: string;
  agentId?: string | null;
  status: "started" | "active" | "idle" | "waitingfortoolresults";
  title?: string | null;
  tags?: string[];
  locale?: string | null;
  modelId?: string | null;
  capabilities?: AgentCapabilityConfig[];
  createdAt: string;
  updatedAt: string;
  /** Number of active (enabled) schedules for this session */
  activeScheduleCount?: number | null;
  /** Aggregated UI features from all active capabilities */
  features?: string[];
  /** Whether this session is pinned by the current user */
  isPinned?: boolean | null;
}

export interface InitialFile {
  path: string;
  content: string;
  encoding?: "text" | "base64";
  isReadonly?: boolean;
}

export interface CreateSessionRequest {
  harnessId?: string;
  /**
   * Human-readable harness name (e.g. "generic", "deep-research").
   * Preferred over harnessId. Must match [a-z0-9]+(-[a-z0-9]+)*, max 64 chars.
   * Cannot be used together with harnessId.
   */
  harnessName?: string;
  agentId?: string;
  title?: string;
  locale?: string;
  modelId?: string;
  tags?: string[];
  capabilities?: AgentCapabilityConfig[];
  initialFiles?: InitialFile[];
}

/** Addressable name validation pattern: lowercase alphanumeric segments separated by hyphens */
const ADDRESSABLE_NAME_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;
const ADDRESSABLE_NAME_MAX_LENGTH = 64;

function validateAddressableName(name: string, label: string): void {
  if (name.length > ADDRESSABLE_NAME_MAX_LENGTH) {
    throw new Error(
      `${label} must be at most ${ADDRESSABLE_NAME_MAX_LENGTH} characters, got ${name.length}`,
    );
  }
  if (!ADDRESSABLE_NAME_PATTERN.test(name)) {
    throw new Error(
      `${label} must match pattern [a-z0-9]+(-[a-z0-9]+)*, got "${name}"`,
    );
  }
}

/**
 * Validate a harness name.
 *
 * @param name - The harness name to validate
 * @throws Error if the name is invalid
 */
export function validateHarnessName(name: string): void {
  validateAddressableName(name, "harness_name");
}

/**
 * Validate an agent name.
 *
 * @param name - The agent name to validate
 * @throws Error if the name is invalid
 */
export function validateAgentName(name: string): void {
  validateAddressableName(name, "agent_name");
}

/** External actor identity for messages from external channels (Slack, Discord, etc.) */
export interface ExternalActor {
  /** Opaque actor identifier from the source channel */
  actorId: string;
  /** Source channel identifier (e.g. "slack", "discord") */
  source: string;
  /** Resolved display name (falls back to actorId if absent) */
  actorName?: string | null;
  /** Channel-specific metadata */
  metadata?: Record<string, string> | null;
}

export interface Message {
  id: string;
  sessionId: string;
  role: "user" | "assistant" | "tool_result";
  content: ContentPart[];
  createdAt: string;
  /** External actor identity (for messages from external channels) */
  externalActor?: ExternalActor | null;
  /** Execution phase for multi-step tool-calling flows */
  phase?: "Commentary" | "FinalAnswer" | null;
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
export function toolResult(toolCallId: string, result: unknown): ContentPart {
  return { type: "tool_result", tool_call_id: toolCallId, result };
}

/** Create a tool result content part with an error */
export function toolError(toolCallId: string, error: string): ContentPart {
  return { type: "tool_result", tool_call_id: toolCallId, error };
}

/** Extract tool calls from event data (`data.message.content`) */
export function extractToolCalls(
  data: Record<string, unknown>,
): ToolCallInfo[] {
  const message = data.message as { content?: unknown[] } | undefined;
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
  /** External actor identity (for messages from external channels like Slack) */
  externalActor?: ExternalActor;
}

export interface Event {
  id: string;
  type: string;
  data: Record<string, unknown>;
  createdAt: string;
}

/** Options for backward pagination on event list endpoints */
export interface ListEventsOptions {
  /** Max events to return (backward pagination, 1-1000) */
  limit?: number;
  /** Cursor for backward pagination: only return events with sequence < this value */
  beforeSequence?: number;
}

// --- Session Filesystem Models ---

/** File metadata without content */
export interface FileInfo {
  id: string;
  sessionId: string;
  path: string;
  name: string;
  isDirectory: boolean;
  isReadonly: boolean;
  sizeBytes: number;
  createdAt: string;
  updatedAt: string;
}

/** Complete file with content */
export interface SessionFile {
  id: string;
  sessionId: string;
  path: string;
  name: string;
  isDirectory: boolean;
  isReadonly: boolean;
  sizeBytes: number;
  createdAt: string;
  updatedAt: string;
  content?: string | null;
  encoding?: string | null;
}

/** File stat information */
export interface FileStat {
  path: string;
  name: string;
  isDirectory: boolean;
  isReadonly: boolean;
  sizeBytes: number;
  createdAt: string;
  updatedAt: string;
}

/** Single grep match */
export interface GrepMatch {
  path: string;
  lineNumber: number;
  line: string;
}

/** Grep result for a file */
export interface GrepResult {
  path: string;
  matches: GrepMatch[];
}

/** Response for delete operation */
export interface DeleteFileResponse {
  deleted: boolean;
}

// --- Budget Models ---

/** Budget period configuration for recurring budgets */
export interface BudgetPeriod {
  type: "rolling" | "calendar";
  /** Window duration for rolling periods (e.g. "24h") */
  window?: string;
  /** Calendar unit for calendar periods (e.g. "month") */
  unit?: string;
}

/** Budget — a spending cap for a subject in a currency */
export interface Budget {
  id: string;
  organizationId: string;
  subjectType: string;
  subjectId: string;
  currency: string;
  limit: number;
  softLimit?: number | null;
  balance: number;
  period?: BudgetPeriod | null;
  metadata?: Record<string, unknown> | null;
  status: "active" | "paused" | "exhausted" | "disabled";
  createdAt: string;
  updatedAt: string;
}

/** Request to create a budget */
export interface CreateBudgetRequest {
  subjectType: string;
  subjectId: string;
  currency: string;
  limit: number;
  softLimit?: number;
  period?: BudgetPeriod;
  metadata?: Record<string, unknown>;
}

/** Request to update a budget */
export interface UpdateBudgetRequest {
  limit?: number;
  softLimit?: number | null;
  status?: string;
  metadata?: Record<string, unknown>;
}

/** Request to top up a budget */
export interface TopUpRequest {
  amount: number;
  description?: string;
}

/** Ledger entry recording resource consumption or credit */
export interface LedgerEntry {
  id: string;
  budgetId: string;
  amount: number;
  meterSource: string;
  refType?: string | null;
  refId?: string | null;
  sessionId?: string | null;
  description?: string | null;
  createdAt: string;
}

/** Result of checking all budgets for a session */
export interface BudgetCheckResult {
  action: string;
  message?: string | null;
  budgetId?: string | null;
  balance?: number | null;
  currency?: string | null;
}

/** Response from session resume endpoint */
export interface ResumeSessionResponse {
  resumedBudgets: number;
  sessionId: string;
}

// --- Connections Models ---

/** A user connection to an external provider */
export interface Connection {
  provider: string;
  createdAt: string;
  updatedAt: string;
}

/** Paginated list response */
export interface ListResponse<T> {
  data: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface StreamOptions {
  /** Resume from this event ID */
  sinceId?: string;
  /** Positive type filter: only return events matching these types */
  types?: string[];
  /** Event types to exclude from the stream (applied after `types` filter) */
  exclude?: string[];
  /** Maximum number of reconnection attempts (undefined = unlimited) */
  maxRetries?: number;
  /** Idle timeout in ms for detecting half-open connections.
   * When no chunks arrive within this duration, the stream reconnects.
   * Default: 45000 (1.5× the server's 30s heartbeat interval). */
  idleTimeoutMs?: number;
}
