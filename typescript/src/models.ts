/** Public data models generated from the Everruns OpenAPI document. */

// Regenerate with `just generate`. Do not edit by hand.

/** Agent configuration for agentic loop. */
export interface Agent {
  capabilities?: AgentCapabilityConfig[];
  createdAt: string;
  model?: string | null;
  displayName?: string | null;
  harnessId: string;
  id: string;
  initialFiles?: InitialFile[];
  name: string;
  parallelToolCalls?: boolean | null;
  systemPrompt: string;
  tools?: ToolDefinition[];
  updatedAt: string;
}

/** Response from on-demand agent analysis (built-in rules + LLM checkers) */
export interface AgentAnalysisResponse {
  findings: Finding[];
}

/** Per-agent capability configuration */
export interface AgentCapabilityConfig {
  config?: unknown;
  ref: string;
}

export type AgentStatus = "active" | "archived" | "deleted";

/** Immutable snapshot of an Agent's authored and resolved runtime config. */
export interface AgentVersion {
  agent_id: string;
  authored_config: Record<string, unknown>;
  change_kind: AgentVersionChangeKind;
  config_hash: string;
  created_at: string;
  created_by_principal_id?: string | null;
  id: string;
  is_published: boolean;
  parent_version_id?: string | null;
  resolved_config: Record<string, unknown>;
  semver_major: number;
  semver_minor: number;
  semver_patch: number;
  source_version_id?: string | null;
  summary?: string | null;
  version: string;
  version_number: number;
}

export type AgentVersionChangeKind =
  | "auto"
  | "manual"
  | "patch"
  | "minor"
  | "major"
  | "import"
  | "rollback"
  | "fork";

/** Response body for agent version diff. */
export interface AgentVersionDiffResponse {
  authored_diff: unknown;
  from_version_id: unknown;
  resolved_diff: unknown;
  to_version_id: unknown;
}

/** Budget — a spending cap for a subject in a currency. */
export interface Budget {
  balance: number;
  createdAt: string;
  currency: string;
  id: string;
  limit: number;
  metadata?: unknown;
  organizationId: string;
  period?: BudgetPeriod | null;
  periodStartedAt?: string | null;
  softLimit?: number | null;
  status: BudgetStatus;
  subjectId: string;
  subjectType: unknown;
  updatedAt: string;
}

/** Result of checking all budgets for a session. */
export interface BudgetCheckResult {
  action: string;
  balance?: number | null;
  budgetId?: string | null;
  currency?: string | null;
  errorCode?: string | null;
  errorFields?: Record<string, unknown> | null;
  message?: string | null;
}

/** Budget period configuration for recurring budgets. */
export interface BudgetPeriod {
  seconds?: number;
  type: "duration" | "rolling" | "calendar";
  window?: string;
  unit?: string;
}

export type BudgetStatus = "active" | "paused" | "exhausted" | "disabled";

/** Built-in tool configuration */
export interface BuiltinTool {
  category?: string | null;
  deferrable?: unknown;
  description: string;
  display_name?: string | null;
  full_parameters?: unknown;
  hints?: unknown;
  name: string;
  parameters: unknown;
  policy?: unknown;
}

/** Public capability information (without internal details) */
export interface CapabilityInfo {
  agentCount?: number;
  category?: string | null;
  configSchema?: Record<string, unknown>;
  configUiSchema?: Record<string, unknown>;
  dependencies?: string[];
  description: string;
  docsSlug?: string | null;
  features?: string[];
  harnessCount?: number;
  icon?: string | null;
  id: string;
  isGuardrail?: boolean;
  isMcp?: boolean;
  isSkill?: boolean;
  localizations?: Record<string, unknown>;
  name: string;
  riskLevel?: unknown;
  status: string;
  systemPrompt?: string | null;
  toolDefinitions?: Record<string, unknown>[];
}

/** Client-side tool - executed by the client, not the server */
export interface ClientSideTool {
  category?: string | null;
  deferrable?: unknown;
  description: string;
  display_name?: string | null;
  full_parameters?: unknown;
  hints?: unknown;
  name: string;
  parameters: unknown;
}

/** A single tool result from the client */
export interface ClientToolResult {
  error?: string | null;
  result?: unknown;
  tool_call_id: string;
}

export interface Connection {
  provider: string;
  createdAt: string;
  updatedAt: string;
}

/** A part of message content - can be text, image, image_file, tool_call, or tool_result */
export interface ContentPart {
  text?: string;
  type: "text" | "image" | "image_file" | "tool_call" | "tool_result";
  base64?: string | null;
  media_type?: string | null;
  url?: string | null;
  filename?: string | null;
  image_id?: string;
  arguments?: unknown;
  id?: string;
  name?: string;
  error?: string | null;
  result?: unknown;
  tool_call_id?: string;
}

/** Runtime controls for message processing */
export interface Controls {
  errorDisclosure?: string | null;
  hints?: Record<string, unknown> | null;
  locale?: string | null;
  modelId?: string | null;
  reasoning?: unknown | null;
}

/** Request to copy a file */
export interface CopyFileRequest {
  dstPath: string;
  srcPath: string;
}

/** Request to create a new agent */
export interface CreateAgentRequest {
  capabilities?: AgentCapabilityConfig[];
  model?: string | null;
  description?: string | null;
  displayName?: string | null;
  harnessId?: string | null;
  harnessName?: string | null;
  id?: string | null;
  initialFiles?: InitialFile[];
  maxIterations?: number | null;
  mcpServers?: unknown;
  name: string;
  networkAccess?: unknown | null;
  parallelToolCalls?: boolean | null;
  systemPrompt: string;
  tags?: string[];
  tools?: ToolDefinition[];
}

/** Request body for the `create_agent_version` operation. */
export interface CreateAgentVersionRequest {
  changeKind?: AgentVersionChangeKind | null;
  summary?: string | null;
}

/** Request body for creating a spending budget. */
export interface CreateBudgetRequest {
  currency: string;
  limit: number;
  metadata?: unknown;
  period?: BudgetPeriod | null;
  softLimit?: number | null;
  subjectId: string;
  subjectType: string;
}

/** Request to create a file */
export interface CreateFileRequest {
  content?: string | null;
  encoding?: string | null;
  isDirectory?: boolean | null;
  isReadonly?: boolean | null;
}

export interface CreateMemoryFileRequest {
  content?: string | null;
  encoding?: string | null;
  isDirectory?: boolean | null;
}

/** Request body for the `create_memory` operation. */
export interface CreateMemoryRequest {
  description?: string | null;
  name: string;
  source?: CreateMemorySourceRequest | null;
}

export type CreateMemorySourceRequest =
  | (GitHubMemorySourceRequest & { type: "github" })
  | (GitMemorySourceRequest & { type: "git" });

/** Request to create a message */
export interface CreateMessageRequest {
  addressedParticipantId?: string | null;
  controls?: Controls | null;
  externalActor?: ExternalActor | null;
  message: MessageInput;
  metadata?: Record<string, unknown> | null;
  tags?: string[] | null;
}

/** Request to create a session */
export interface CreateSessionRequest {
  agentId?: string | null;
  agentIdentityId?: string | null;
  agentName?: string | null;
  capabilities?: AgentCapabilityConfig[];
  harnessId?: string | null;
  harnessName?: string | null;
  hints?: Record<string, unknown> | null;
  initialFiles?: InitialFile[];
  locale?: string | null;
  maxIterations?: number | null;
  mcpServers?: unknown;
  modelId?: string | null;
  networkAccess?: unknown | null;
  parallelToolCalls?: boolean | null;
  systemPrompt?: string | null;
  tags?: string[];
  title?: string | null;
  tools?: ToolDefinition[];
  workspaceId?: string | null;
}

export interface CreateWorkspaceRequest {
  description?: string | null;
  name: string;
}

/** Response for delete operation */
export interface DeleteFileResponse {
  deleted: boolean;
}

/** Standard event following the Everruns event protocol. */
export interface Event {
  data: Record<string, unknown>;
  id: string;
  createdAt: string;
  type: string;
}

/** Context for event correlation and tracing */
export interface EventContext {
  execId?: string | null;
  inputMessageId?: string | null;
  parentSpanId?: string | null;
  spanId?: string | null;
  traceId?: string | null;
  turnId?: string | null;
}

/** External actor identity for messages originating from external channels */
export interface ExternalActor {
  actorId: string;
  actorName?: string | null;
  metadata?: Record<string, string> | null;
  source: string;
}

/** File metadata without content */
export interface FileInfo {
  created_at: string;
  id: string;
  is_directory: boolean;
  is_readonly: boolean;
  name: string;
  path: string;
  session_id: string;
  size_bytes: number;
  updated_at: string;
}

/** File stat information */
export interface FileStat {
  created_at: string;
  is_directory: boolean;
  is_readonly: boolean;
  name: string;
  path: string;
  size_bytes: number;
  updated_at: string;
}

/** A single advisory finding about an agent configuration. */
export interface Finding {
  category: unknown;
  fix?: string | null;
  location?: FindingLocation | null;
  message: string;
  rule_id: string;
  severity: unknown;
  source: unknown;
}

/** Pointer to the config field (and optional byte span within it) a finding */
export interface FindingLocation {
  end?: number | null;
  field: string;
  start?: number | null;
}

/** Request body for the `fork_agent_version` operation. */
export interface ForkAgentVersionRequest {
  name: string;
  displayName?: string | null;
  description?: string | null;
}

/** Request body for GitHub memory source. */
export interface GitHubMemorySourceRequest {
  branch?: string | null;
  repository: string;
  root_folder?: string | null;
  sync_interval_secs?: number | null;
}

/** Request body for git memory source. */
export interface GitMemorySourceRequest {
  branch?: string | null;
  root_folder?: string | null;
  sync_interval_secs?: number | null;
  url: string;
}

/** Grep match result */
export interface GrepMatch {
  line: string;
  line_number: number;
  path: string;
}

export interface GrepRequest {
  pathPattern?: string | null;
  pattern: string;
}

/** Grep result for a file */
export interface GrepResult {
  matches: GrepMatch[];
  path: string;
}

export type GuardrailAction = "block" | "log";

/** A read-only, adoptable guardrails preset from the gallery. Adopt by */
export interface GuardrailExample {
  check_types: string[];
  config: Record<string, unknown>;
  data_egress: string;
  description: string;
  display_name: string;
  name: string;
  stages: string[];
  tags: string[];
}

/** Response for the `list_guardrail_examples` operation. */
export interface GuardrailExamplesResponse {
  examples: GuardrailExample[];
}

export type GuardrailStage = "output" | "tool_use" | "tool_output";

/** One triggered check from a guardrails dry run. */
export interface GuardrailsDryRunHit {
  action: GuardrailAction;
  check_id: string;
  check_index: number;
  matched?: string | null;
  reason_code: string;
  replacement?: string | null;
  rule_type: string;
  stage: GuardrailStage;
}

/** Request body for the `dry_run_guardrails` operation: evaluate a */
export interface GuardrailsDryRunRequest {
  config: Record<string, unknown>;
  stage: GuardrailStage;
  text: string;
  toolName?: string | null;
}

/** Response for the `dry_run_guardrails` operation. */
export interface GuardrailsDryRunResponse {
  blocked: boolean;
  hits: GuardrailsDryRunHit[];
}

/** Outcome of a single case after the agent ran and was scored. */
export interface HealthCheckCaseResult {
  deterministic_reason: string;
  error?: string | null;
  input_tokens?: number;
  judge_reason: string;
  latency_ms: number;
  name: string;
  output_tokens?: number;
  passed: boolean;
  rubric: string;
  score: number;
  session_id?: string | null;
  turns: number;
  user_message: string;
}

/** API view of a health check run. */
export interface HealthCheckRun {
  agent_id?: string | null;
  completed_at?: string | null;
  config_hash: string;
  created_at: string;
  error_message?: string | null;
  id: string;
  model_id?: string | null;
  results?: HealthCheckCaseResult[] | null;
  status: HealthCheckStatus;
  summary?: HealthCheckSummary | null;
}

export type HealthCheckStatus = "pending" | "running" | "completed" | "failed";

/** Aggregate metrics across all cases in a run. */
export interface HealthCheckSummary {
  avg_score: number;
  avg_turns: number;
  errored: number;
  failed: number;
  pass_rate: number;
  passed: number;
  total: number;
  total_input_tokens: number;
  total_output_tokens: number;
}

/** Starter file copied into a new session from an agent or harness. */
export interface InitialFile {
  content: string;
  encoding?: string;
  isReadonly?: boolean;
  path: string;
}

/** Immutable ledger entry recording resource consumption or credit against a budget. */
export interface LedgerEntry {
  amount: number;
  budgetId: string;
  createdAt: string;
  description?: string | null;
  id: string;
  meterSource: string;
  refId?: string | null;
  refType?: string | null;
  sessionId?: string | null;
}

/** Response body for memory. */
export interface Memory {
  archived_at?: string | null;
  created_at: string;
  deleted_at?: string | null;
  description?: string | null;
  id: string;
  is_readonly: boolean;
  last_sync_error?: string | null;
  last_synced_at?: string | null;
  name: string;
  source: unknown;
  source_type: string;
  status: string;
  sync_status: string;
  updated_at: string;
}

export interface MemoryFile {
  content: string;
  content_hash?: string | null;
  created_at: string;
  encoding: string;
  path: string;
  size_bytes: number;
  updated_at: string;
}

export interface MemoryFileInfo {
  content_hash?: string | null;
  created_at: string;
  is_directory: boolean;
  path: string;
  size_bytes: number;
  updated_at: string;
}

export interface MemoryGrepResult {
  path: string;
  size_bytes: number;
}

/** A message in the conversation */
export interface Message {
  content: ContentPart[];
  controls?: Controls | null;
  createdAt: string;
  externalActor?: ExternalActor | null;
  id: string;
  metadata?: Record<string, unknown> | null;
  phase?: unknown | null;
  role: "user" | "assistant" | "tool_result";
  thinkingSignature?: string | null;
}

export type MessageRole = "system" | "user" | "agent" | "tool_result";

/** Request to move/rename a file */
export interface MoveFileRequest {
  dstPath: string;
  srcPath: string;
}

/** Response body for resource stats. */
export interface ResourceStats {
  active_session_count: number;
  avg_session_duration_ms?: number | null;
  execution_count: number;
  first_session_at?: string | null;
  idle_session_count: number;
  last_execution_at?: string | null;
  last_session_at?: string | null;
  session_count: number;
  started_session_count: number;
  total_actual_cost_usd: number;
  total_cache_creation_tokens: number;
  total_cache_read_tokens: number;
  total_cost_usd: number;
  total_estimated_cost_usd: number;
  total_input_tokens: number;
  total_output_tokens: number;
  total_session_duration_ms: number;
  waiting_for_tool_results_session_count: number;
}

/** Result of resuming budgets paused for a session. */
export interface ResumeSessionResponse {
  resumedBudgets: number;
  sessionId: string;
}

/** Request body for the `rollback_agent_version` operation. */
export interface RollbackAgentVersionRequest {
  saveVersion?: boolean;
  summary?: string | null;
}

/** Session - instance of agentic loop execution. */
export interface Session {
  activeScheduleCount?: number | null;
  agentId?: string | null;
  agentIdentityId?: string | null;
  agentVersionId?: string | null;
  blueprintConfig?: Record<string, unknown> | null;
  blueprintId?: string | null;
  capabilities?: AgentCapabilityConfig[];
  createdAt: string;
  effectiveOwner?: unknown | null;
  features?: string[];
  finishedAt?: string | null;
  forkedFromSequence?: number | null;
  forkedFromSessionId?: string | null;
  harnessId: string;
  hints?: Record<string, unknown> | null;
  id: string;
  initialFiles?: InitialFile[];
  isPinned?: boolean | null;
  locale?: string | null;
  maxIterations?: number | null;
  mcpServers?: unknown;
  modelId?: string | null;
  networkAccess?: unknown | null;
  outputPreview?: string | null;
  owner?: unknown | null;
  ownerPrincipalId: string;
  parallelToolCalls?: boolean | null;
  parentSessionId?: string | null;
  preview?: string | null;
  resolvedOwnerUserId?: string | null;
  startedAt?: string | null;
  status: SessionStatus;
  systemPrompt?: string | null;
  tags?: string[];
  title?: string | null;
  tools?: ToolDefinition[];
  updatedAt: string;
  workspaceId: string;
}

/** Complete file with content */
export interface SessionFile {
  content?: string | null;
  created_at: string;
  encoding?: string;
  id: string;
  is_directory: boolean;
  is_readonly: boolean;
  name: string;
  path: string;
  session_id: string;
  size_bytes: number;
  updated_at: string;
}

export type SessionStatus =
  | "started"
  | "active"
  | "idle"
  | "waitingfortoolresults";

/** Request body for the `set_default_agent_version` operation. */
export interface SetDefaultAgentVersionRequest {
  versionId: string;
}

export interface StatRequest {
  path: string;
}

/** Request to submit client-side tool results */
export interface SubmitToolResultsRequest {
  toolResults: ClientToolResult[];
}

/** Response from submitting tool results */
export interface SubmitToolResultsResponse {
  accepted: number;
  status: string;
}

/** Token usage statistics */
export interface TokenUsage {
  actualCostUsd?: number | null;
  cacheCreationTokens?: number | null;
  cacheReadTokens?: number | null;
  effectiveCostUsd?: number | null;
  estimatedCostUsd?: number | null;
  inputTokens: number;
  outputTokens: number;
}

export type ToolDefinition =
  | (BuiltinTool & { type: "builtin" })
  | (ClientSideTool & { type: "client_side" });

export interface TopUpRequest {
  amount: number;
  description?: string | null;
}

/** Request body for changing a spending budget. */
export interface UpdateBudgetRequest {
  limit?: number | null;
  metadata?: unknown;
  softLimit?: number | null;
  status?: string | null;
}

/** Request to update a file */
export interface UpdateFileRequest {
  content?: string | null;
  encoding?: string | null;
  isReadonly?: boolean | null;
}

export interface UpdateMemoryFileRequest {
  content?: string | null;
  encoding?: string | null;
}

/** Request body for the `update_memory` operation. */
export interface UpdateMemoryRequest {
  description?: string | null;
  name?: string | null;
  source?: CreateMemorySourceRequest | null;
}

export interface UpdateWorkspaceRequest {
  description?: string | null;
  name?: string | null;
  status?: string | null;
}

export interface Workspace {
  archived_at?: string | null;
  created_at: string;
  deleted_at?: string | null;
  description?: string | null;
  id: string;
  name: string;
  status: string;
  updated_at: string;
}

/** Request to preview the final agent shape with capabilities applied */
export interface AnalyzeAgentRequest {
  capabilities?: AgentCapabilityConfig[];
  mcpServers?: unknown;
  systemPrompt: string;
  tools?: Record<string, unknown>[];
}

export interface ListEventsOptions {
  sinceId?: string;
  types?: string[];
  exclude?: string[];
  limit?: number;
  beforeSequence?: number;
  afterSequence?: number;
  around?: string;
  window?: number;
  fromTs?: string;
  toTs?: string;
  turnId?: string;
  execId?: string;
  traceId?: string;
  tags?: string[];
  toolName?: string;
  q?: string;
  orderDesc?: boolean;
}

export interface MessageInput {
  role: "user" | "tool_result";
  content: ContentPart[];
}

export interface SetConnectionRequest {
  apiKey: string;
}

export interface SetSecretsRequest {
  secrets: Record<string, string>;
}

export interface StreamOptions {
  sinceId?: string;
  types?: string[];
  exclude?: string[];
  maxRetries?: number;
  idleTimeoutMs?: number;
}

export interface ToolCallInfo {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface ListResponse<T> {
  data: T[];
  total: number;
  offset: number;
  limit: number;
}

export function generateAgentId(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return `agent_${Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")}`;
}

export function generateHarnessId(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return `harness_${Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")}`;
}

const ADDRESSABLE_NAME_PATTERN = /^[a-z0-9]+(-[a-z0-9]+)*$/;

function validateAddressableName(name: string, label: string): void {
  if (name.length > 64)
    throw new Error(
      `${label} must be at most 64 characters, got ${name.length}`,
    );
  if (!ADDRESSABLE_NAME_PATTERN.test(name))
    throw new Error(
      `${label} must match pattern [a-z0-9]+(-[a-z0-9]+)*, got "${name}"`,
    );
}

export function validateHarnessName(name: string): void {
  validateAddressableName(name, "harness_name");
}

export function validateAgentName(name: string): void {
  validateAddressableName(name, "agent_name");
}

export function toolResult(toolCallId: string, result: unknown): ContentPart {
  return { type: "tool_result", tool_call_id: toolCallId, result };
}

export function toolError(toolCallId: string, error: string): ContentPart {
  return { type: "tool_result", tool_call_id: toolCallId, error };
}

export function extractToolCalls(
  data: Record<string, unknown>,
): ToolCallInfo[] {
  let requested = data.tool_calls;
  if (!Array.isArray(requested))
    requested =
      (data.message as { content?: unknown[] } | undefined)?.content ?? [];
  if (!Array.isArray(requested)) return [];
  return requested.flatMap((value) => {
    const call = value as Record<string, unknown>;
    if (call.type !== undefined && call.type !== "tool_call") return [];
    if (typeof call.id !== "string" || typeof call.name !== "string") return [];
    return [
      {
        id: call.id,
        name: call.name,
        arguments: (call.arguments as Record<string, unknown>) ?? {},
      },
    ];
  });
}
