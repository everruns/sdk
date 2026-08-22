/** Public data models generated from the Everruns OpenAPI document. */

// Regenerate with `just generate`. Do not edit by hand.

/** Agent configuration for agentic loop. */
export interface Agent {
  capabilities?: AgentCapabilityConfig[];
  created_at: string;
  model?: string | null;
  display_name?: string | null;
  harness_id: string;
  id: string;
  initial_files?: InitialFile[];
  name: string;
  parallel_tool_calls?: boolean | null;
  system_prompt: string;
  tools?: ToolDefinition[];
  updated_at: string;
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

/** Budget — a stored spending cap for a platform subject. */
export interface Budget {
  balance: number;
  created_at: string;
  currency: string;
  id: string;
  limit: number;
  metadata?: unknown;
  organization_id: string;
  period?: BudgetPeriod | null;
  period_started_at?: string | null;
  soft_limit?: number | null;
  status: BudgetStatus;
  subject_id: string;
  subject_type: unknown;
  updated_at: string;
}

/** Result of checking all budgets for a session. */
export interface BudgetCheckResult {
  action: string;
  balance?: number | null;
  budget_id?: string | null;
  currency?: string | null;
  error_code?: string | null;
  error_fields?: Record<string, unknown> | null;
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
  agent_count?: number;
  category?: string | null;
  config_schema?: Record<string, unknown>;
  config_ui_schema?: Record<string, unknown>;
  dependencies?: string[];
  description: string;
  docs_slug?: string | null;
  features?: string[];
  harness_count?: number;
  icon?: string | null;
  id: string;
  is_guardrail?: boolean;
  is_mcp?: boolean;
  is_skill?: boolean;
  localizations?: Record<string, unknown>;
  name: string;
  risk_level?: unknown;
  status: string;
  system_prompt?: string | null;
  tool_definitions?: Record<string, unknown>[];
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
  created_at: string;
  updated_at: string;
}

/** A part of message content - can be text, image, image_file, tool_call, or tool_result */
export interface ContentPart {
  annotations?: unknown[];
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
  speed?: string | null;
  verbosity?: string | null;
}

/** Request to copy a file */
export interface CopyFileRequest {
  dstPath: string;
  srcPath: string;
}

/** A pricing tier that activates above a context token threshold. */
export interface CostTier {
  aboveTokens: number;
  cacheRead?: number | null;
  input: number;
  output: number;
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
  networkAccess?: NetworkAccessList | null;
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

/** Request to create a new harness */
export interface CreateHarnessRequest {
  capabilities?: AgentCapabilityConfig[];
  defaultModelId?: string | null;
  description?: string | null;
  displayName?: string | null;
  embedderMetadata?: Record<string, string>;
  initialFiles?: InitialFile[];
  mcpServers?: unknown;
  name: string;
  networkAccess?: NetworkAccessList | null;
  parentHarnessId?: string | null;
  systemPrompt?: string | null;
  tags?: string[];
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
  goal?: string | null;
  harnessId?: string | null;
  harnessName?: string | null;
  hints?: Record<string, unknown> | null;
  initialFiles?: InitialFile[];
  locale?: string | null;
  maxIterations?: number | null;
  mcpServers?: unknown;
  modelId?: string | null;
  networkAccess?: NetworkAccessList | null;
  parallelToolCalls?: boolean | null;
  source?: string | null;
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

export type DriverId = string;

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

/** Harness configuration for sessions. */
export interface Harness {
  archived_at?: string | null;
  capabilities?: AgentCapabilityConfig[];
  created_at: string;
  default_model_id?: string | null;
  deleted_at?: string | null;
  description?: string | null;
  display_name?: string | null;
  embedder_metadata?: Record<string, string>;
  id: string;
  initial_files?: InitialFile[];
  is_built_in?: boolean;
  mcpServers?: unknown;
  name: string;
  network_access?: NetworkAccessList | null;
  parallel_tool_calls?: boolean | null;
  parent_harness_id?: string | null;
  status: HarnessStatus;
  system_prompt?: string | null;
  tags?: string[];
  updated_at: string;
}

/** A read-only harness example defined in code. */
export interface HarnessExample {
  capabilities: AgentCapabilityConfig[];
  description: string;
  devOnly: boolean;
  displayName: string;
  name: string;
  parentName?: string | null;
  tags: string[];
}

export type HarnessStatus = "active" | "archived" | "deleted";

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

/** Immutable platform ledger record for resource consumption or credit. */
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
  owner_agent_id?: string | null;
  owner_user_id?: string | null;
  scope: string;
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
  created_at: string;
  external_actor?: ExternalActor | null;
  id: string;
  metadata?: Record<string, unknown> | null;
  phase?: unknown | null;
  role: "user" | "assistant" | "tool_result";
  thinking_signature?: string | null;
}

export type MessageRole = "system" | "user" | "agent" | "tool_result";

export type Modality = "text" | "image" | "audio" | "video" | "pdf";

/** Cost information for the model (per million tokens) */
export interface ModelCost {
  cacheRead?: number | null;
  costTiers?: CostTier[];
  input: number;
  output: number;
}

/** Token limits for the model */
export interface ModelLimits {
  context: number;
  input?: number | null;
  maxMedia?: number | null;
  output: number;
}

/** Model modalities for input and output */
export interface ModelModalities {
  input: Modality[];
  output: Modality[];
}

/** LLM Model Profile describing model capabilities */
export interface ModelProfile {
  attachment: boolean;
  cost?: ModelCost | null;
  description?: string | null;
  family: string;
  knowledge?: string | null;
  lastUpdated?: string | null;
  limits?: ModelLimits | null;
  modalities?: ModelModalities | null;
  name: string;
  openWeights: boolean;
  reasoning: boolean;
  reasoningEffort?: ReasoningEffortConfig | null;
  releaseDate?: string | null;
  speed?: unknown | null;
  structuredOutput: boolean;
  supportedParameters?: string[];
  supportsPhases?: boolean;
  temperature: boolean;
  toolCall: boolean;
  toolSearch?: boolean;
  verbosity?: unknown | null;
}

export type ModelSource = "manual" | "discovered" | "predefined";

export type ModelVendor =
  | "openai"
  | "anthropic"
  | "google"
  | "nvidia"
  | "qwen"
  | "microsoft"
  | "meta"
  | "minimax"
  | "moonshot"
  | "xai"
  | "llmsim";

/** LLM Model with provider info */
export interface ModelWithProvider {
  capabilities: string[];
  created_at: string;
  display_name: string;
  enabled: boolean;
  healthy: boolean;
  id: string;
  is_favorite: boolean;
  model_id: string;
  model_vendor?: ModelVendor | null;
  profile?: ModelProfile | null;
  provider_id: string;
  provider_name: string;
  provider_type: DriverId;
  source: ModelSource;
  updated_at: string;
}

/** Request to move/rename a file */
export interface MoveFileRequest {
  dstPath: string;
  srcPath: string;
}

/** Network access list controlling which hosts/URLs an agent session can reach. */
export interface NetworkAccessList {
  allowed?: string[];
  blocked?: string[];
}

export type ReasoningEffort =
  "none" | "minimal" | "low" | "medium" | "high" | "xhigh";

/** Reasoning effort configuration for a model */
export interface ReasoningEffortConfig {
  default: ReasoningEffort;
  values: ReasoningEffortValue[];
}

/** Named reasoning effort value for UI display */
export interface ReasoningEffortValue {
  name: string;
  value: ReasoningEffort;
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
  resumed_budgets: number;
  session_id: string;
}

/** Request body for the `rollback_agent_version` operation. */
export interface RollbackAgentVersionRequest {
  saveVersion?: boolean;
  summary?: string | null;
}

/** Session - instance of agentic loop execution. */
export interface Session {
  active_schedule_count?: number | null;
  activity?: unknown;
  agent_id?: string | null;
  agent_identity_id?: string | null;
  agent_version_id?: string | null;
  blueprint_config?: Record<string, unknown> | null;
  blueprint_id?: string | null;
  capabilities?: AgentCapabilityConfig[];
  created_at: string;
  effective_owner?: unknown | null;
  features?: string[];
  finished_at?: string | null;
  forked_from_sequence?: number | null;
  forked_from_session_id?: string | null;
  goal?: string | null;
  harness_id: string;
  hints?: Record<string, unknown> | null;
  id: string;
  initial_files?: InitialFile[];
  is_pinned?: boolean | null;
  locale?: string | null;
  max_iterations?: number | null;
  mcpServers?: unknown;
  model_id?: string | null;
  network_access?: NetworkAccessList | null;
  output_preview?: string | null;
  owner?: unknown | null;
  owner_principal_id: string;
  parallel_tool_calls?: boolean | null;
  parent_session_id?: string | null;
  preview?: string | null;
  resolved_owner_user_id?: string | null;
  run_summary?: string | null;
  source?: unknown;
  started_at?: string | null;
  status: SessionStatus;
  system_prompt?: string | null;
  tags?: string[];
  title?: string | null;
  tools?: ToolDefinition[];
  updated_at: string;
  workspace_id: string;
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
  "started" | "active" | "idle" | "waitingfortoolresults";

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

/** Request to update a harness. Only provided fields will be updated. */
export interface UpdateHarnessRequest {
  capabilities?: AgentCapabilityConfig[] | null;
  defaultModelId?: string | null;
  description?: string | null;
  displayName?: string | null;
  embedderMetadata?: Record<string, string> | null;
  initialFiles?: InitialFile[] | null;
  mcpServers?: unknown | null;
  name?: string | null;
  networkAccess?: NetworkAccessList | null;
  parentHarnessId?: string | null;
  status?: HarnessStatus | null;
  systemPrompt?: string | null;
  tags?: string[] | null;
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
