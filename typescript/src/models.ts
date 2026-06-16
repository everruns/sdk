/**
 * Core data models for Everruns API.
 */

export interface AgentCapabilityConfig {
  /** Reference to the capability ID */
  ref: string;
  /** Per-agent configuration for this capability (capability-specific) */
  config?: Record<string, unknown>;
}

export interface ClientSideTool {
  type: "client_side";
  name: string;
  description: string;
  parameters: unknown;
  display_name?: string | null;
  category?: string | null;
  hints?: Record<string, unknown>;
  deferrable?: Record<string, unknown>;
}

export interface BuiltinTool {
  type: "builtin";
  name: string;
  description: string;
  parameters: unknown;
  display_name?: string | null;
  category?: string | null;
  hints?: Record<string, unknown>;
  deferrable?: Record<string, unknown>;
  policy?: "auto" | "requires_approval" | "client_side";
}

export type ToolDefinition = ClientSideTool | BuiltinTool;

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
  tools?: ToolDefinition[];
  initialFiles?: InitialFile[];
  createdAt: string;
  updatedAt: string;
}

export type AgentVersionChangeKind =
  | "manual"
  | "patch"
  | "minor"
  | "major"
  | "import"
  | "rollback"
  | "fork";

export interface AgentVersion {
  id: string;
  agent_id: string;
  version_number: number;
  semver_major: number;
  semver_minor: number;
  semver_patch: number;
  version: string;
  change_kind: AgentVersionChangeKind;
  config_hash: string;
  authored_config: Record<string, unknown>;
  resolved_config: Record<string, unknown>;
  created_at: string;
  created_by_principal_id?: string | null;
  parent_version_id?: string | null;
  source_version_id?: string | null;
  summary?: string | null;
}

export interface AgentVersionDiffResponse {
  from_version_id: string;
  to_version_id: string;
  authored_diff: unknown;
  resolved_diff: unknown;
}

export interface CreateAgentVersionRequest {
  changeKind?: AgentVersionChangeKind | null;
  summary?: string | null;
}

export interface SetDefaultAgentVersionRequest {
  versionId: string;
}

export interface ForkAgentVersionRequest {
  name: string;
  displayName?: string | null;
  description?: string | null;
}

export interface RollbackAgentVersionRequest {
  saveVersion?: boolean;
  summary?: string | null;
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
  tools?: ToolDefinition[];
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
  tools?: ToolDefinition[];
  createdAt: string;
  updatedAt: string;
  /** Number of active (enabled) schedules for this session */
  activeScheduleCount?: number | null;
  /** Aggregated UI features from all active capabilities */
  features?: string[];
  /** Whether this session is pinned by the current user */
  isPinned?: boolean | null;
}

/** Aggregate usage statistics for an agent or harness. */
export interface ResourceStats {
  session_count: number;
  active_session_count: number;
  idle_session_count: number;
  started_session_count: number;
  waiting_for_tool_results_session_count: number;
  execution_count: number;
  total_session_duration_ms: number;
  avg_session_duration_ms?: number | null;
  total_input_tokens: number;
  total_output_tokens: number;
  total_cache_read_tokens: number;
  total_cache_creation_tokens: number;
  first_session_at?: string | null;
  last_session_at?: string | null;
  last_execution_at?: string | null;
}

export type HealthCheckStatus = "pending" | "running" | "completed" | "failed";

/** Aggregate metrics across all cases in a health check run. */
export interface HealthCheckSummary {
  total: number;
  passed: number;
  failed: number;
  errored: number;
  pass_rate: number;
  avg_score: number;
  avg_turns: number;
  total_input_tokens: number;
  total_output_tokens: number;
}

/** Outcome of a single case after the agent ran and was scored. */
export interface HealthCheckCaseResult {
  name: string;
  user_message: string;
  rubric: string;
  passed: boolean;
  score: number;
  judge_reason: string;
  deterministic_reason: string;
  turns: number;
  latency_ms: number;
  error?: string | null;
  session_id?: string | null;
}

/** API view of a behavioral health check run for an agent. */
export interface HealthCheckRun {
  id: string;
  config_hash: string;
  status: HealthCheckStatus;
  created_at: string;
  agent_id?: string | null;
  model_id?: string | null;
  completed_at?: string | null;
  error_message?: string | null;
  summary?: HealthCheckSummary | null;
  results?: HealthCheckCaseResult[] | null;
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
  tools?: ToolDefinition[];
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

/** A single tool result from the client. */
export interface ClientToolResult {
  tool_call_id: string;
  result?: unknown;
  error?: string;
}

/** Response from submitting tool results. */
export interface SubmitToolResultsResponse {
  accepted: number;
  status: string;
}

/** Extract tool calls from `tool.call_requested` or message event data. */
export function extractToolCalls(
  data: Record<string, unknown>,
): ToolCallInfo[] {
  const requested = data.tool_calls;
  if (Array.isArray(requested)) {
    return requested
      .filter((call) => {
        const c = call as Record<string, unknown>;
        return typeof c.id === "string" && typeof c.name === "string";
      })
      .map((call) => {
        const c = call as Record<string, unknown>;
        return {
          id: c.id as string,
          name: c.name as string,
          arguments: (c.arguments as Record<string, unknown>) ?? {},
        };
      });
  }

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

/** Options for filtering and pagination on event list endpoints */
export interface ListEventsOptions {
  /** Return events after this event ID */
  sinceId?: string;
  /** Positive type filter */
  types?: string[];
  /** Event types to exclude */
  exclude?: string[];
  /** Max events to return (backward pagination, 1-1000) */
  limit?: number;
  /** Cursor for backward pagination: only return events with sequence < this value */
  beforeSequence?: number;
  /** Forward cursor: only return events with sequence > this value */
  afterSequence?: number;
  /** Anchor event ID for centered windows */
  around?: string;
  /** Events to return on each side of around */
  window?: number;
  /** Lower created_at bound, RFC 3339 */
  fromTs?: string;
  /** Upper created_at bound, RFC 3339 */
  toTs?: string;
  /** Filter by turn ID */
  turnId?: string;
  /** Filter by execution ID */
  execId?: string;
  /** Filter by trace ID */
  traceId?: string;
  /** Tag any-match filter */
  tags?: string[];
  /** Filter tool events by tool name */
  toolName?: string;
  /** Full-text search query */
  q?: string;
  /** Return newest first when true */
  orderDesc?: boolean;
}

// --- Workspace Models ---

/** Workspace resource */
export interface Workspace {
  id: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
  description?: string | null;
  archived_at?: string | null;
  deleted_at?: string | null;
}

/** Request to create a workspace */
export interface CreateWorkspaceRequest {
  name: string;
  description?: string;
}

/** Request to update a workspace */
export interface UpdateWorkspaceRequest {
  name?: string;
  description?: string | null;
  status?: string;
}

// --- Workspace Filesystem Models ---

/** File metadata without content */
export interface FileInfo {
  id: string;
  session_id: string;
  path: string;
  name: string;
  is_directory: boolean;
  is_readonly: boolean;
  size_bytes: number;
  created_at: string;
  updated_at: string;
}

/** Complete file with content */
export interface SessionFile {
  id: string;
  session_id: string;
  path: string;
  name: string;
  is_directory: boolean;
  is_readonly: boolean;
  size_bytes: number;
  created_at: string;
  updated_at: string;
  content?: string | null;
  encoding?: string | null;
}

/** File stat information */
export interface FileStat {
  path: string;
  name: string;
  is_directory: boolean;
  is_readonly: boolean;
  size_bytes: number;
  created_at: string;
  updated_at: string;
}

/** Single grep match */
export interface GrepMatch {
  path: string;
  line_number: number;
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

// --- Memory Models ---

/** Workspace memory resource */
export interface Memory {
  id: string;
  name: string;
  source_type: string;
  source: Record<string, unknown>;
  is_readonly: boolean;
  sync_status: string;
  status: string;
  created_at: string;
  updated_at: string;
  description?: string | null;
  last_sync_error?: string | null;
  last_synced_at?: string | null;
  archived_at?: string | null;
  deleted_at?: string | null;
}

export interface GitHubMemorySourceRequest {
  type: "github";
  repository: string;
  branch?: string | null;
  root_folder?: string | null;
  sync_interval_secs?: number | null;
}

export interface GitMemorySourceRequest {
  type: "git";
  url: string;
  branch?: string | null;
  root_folder?: string | null;
  sync_interval_secs?: number | null;
}

export type CreateMemorySourceRequest =
  | GitHubMemorySourceRequest
  | GitMemorySourceRequest;

/** Request to create a memory */
export interface CreateMemoryRequest {
  name: string;
  description?: string | null;
  source?: CreateMemorySourceRequest | null;
}

/** Request to update a memory */
export interface UpdateMemoryRequest {
  name?: string | null;
  description?: string | null;
  source?: CreateMemorySourceRequest | null;
}

/** Memory file metadata */
export interface MemoryFileInfo {
  path: string;
  is_directory: boolean;
  size_bytes: number;
  created_at: string;
  updated_at: string;
  content_hash?: string | null;
}

/** Memory file content */
export interface MemoryFile {
  path: string;
  content: string;
  encoding: string;
  size_bytes: number;
  created_at: string;
  updated_at: string;
  content_hash?: string | null;
}

/** Request to create a memory file or directory */
export interface CreateMemoryFileRequest {
  content?: string;
  encoding?: string;
  isDirectory?: boolean;
}

/** Request to update a memory file */
export interface UpdateMemoryFileRequest {
  content?: string;
  encoding?: string;
}

/** Memory grep result entry */
export interface MemoryGrepResult {
  path: string;
  size_bytes: number;
}

// --- Agent Analysis and Guardrail Models ---

export interface AnalyzeAgentRequest {
  systemPrompt: string;
  capabilities?: AgentCapabilityConfig[];
  tools?: Record<string, unknown>[];
  mcpServers?: Record<string, unknown>;
}

export interface FindingLocation {
  field: string;
  start?: number | null;
  end?: number | null;
}

export interface Finding {
  rule_id: string;
  severity: string;
  category: string;
  source: string;
  message: string;
  location?: FindingLocation | null;
  fix?: string | null;
}

export interface AgentAnalysisResponse {
  findings: Finding[];
}

export type GuardrailStage = "output" | "tool_use" | "tool_output";
export type GuardrailAction = "block" | "log";

export interface GuardrailsDryRunRequest {
  config: Record<string, unknown>;
  stage: GuardrailStage;
  text: string;
  toolName?: string;
}

export interface GuardrailsDryRunHit {
  check_index: number;
  check_id: string;
  stage: GuardrailStage;
  rule_type: string;
  action: GuardrailAction;
  reason_code: string;
  matched?: string | null;
  replacement?: string | null;
}

export interface GuardrailsDryRunResponse {
  hits: GuardrailsDryRunHit[];
  blocked: boolean;
}

export interface GuardrailExample {
  name: string;
  display_name: string;
  description: string;
  tags: string[];
  check_types: string[];
  stages: string[];
  data_egress: string;
  config: Record<string, unknown>;
}

export interface GuardrailExamplesResponse {
  examples: GuardrailExample[];
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
