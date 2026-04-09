/**
 * Everruns API client.
 */
import { ApiKey } from "./auth.js";
import {
  Agent,
  Budget,
  BudgetCheckResult,
  CapabilityInfo,
  Connection,
  ContentPart,
  CreateAgentRequest,
  CreateBudgetRequest,
  DeleteFileResponse,
  Session,
  CreateSessionRequest,
  FileInfo,
  FileStat,
  GrepResult,
  LedgerEntry,
  Message,
  CreateMessageRequest,
  Event,
  ListEventsOptions,
  ListResponse,
  ResumeSessionResponse,
  SessionFile,
  StreamOptions,
  TopUpRequest,
  UpdateBudgetRequest,
  validateAgentName,
  validateHarnessName,
} from "./models.js";
import {
  ApiError,
  AuthenticationError,
  NotFoundError,
  RateLimitError,
} from "./errors.js";
import { EventStream } from "./sse.js";

export interface EverrunsOptions {
  apiKey?: string | ApiKey;
  baseUrl?: string;
}

export class Everruns {
  private readonly apiKey: ApiKey;
  private readonly baseUrl: string;

  readonly agents: AgentsClient;
  readonly sessions: SessionsClient;
  readonly messages: MessagesClient;
  readonly events: EventsClient;
  readonly capabilities: CapabilitiesClient;
  readonly sessionFiles: SessionFilesClient;
  readonly connections: ConnectionsClient;
  readonly budgets: BudgetsClient;

  constructor(options: EverrunsOptions = {}) {
    if (options.apiKey instanceof ApiKey) {
      this.apiKey = options.apiKey;
    } else if (options.apiKey) {
      this.apiKey = new ApiKey(options.apiKey);
    } else {
      this.apiKey = ApiKey.fromEnv();
    }
    // Normalize base URL: remove trailing slash to avoid double slashes
    // when joining with paths that start with "/".
    // Example: "http://host/api/" + "/v1/agents" = "http://host/api//v1/agents" (wrong)
    //          "http://host/api" + "/v1/agents" = "http://host/api/v1/agents" (correct)
    const rawBaseUrl = options.baseUrl ?? "https://custom.example.com/api";
    this.baseUrl = rawBaseUrl.replace(/\/+$/, "");

    this.agents = new AgentsClient(this);
    this.sessions = new SessionsClient(this);
    this.messages = new MessagesClient(this);
    this.events = new EventsClient(this);
    this.capabilities = new CapabilitiesClient(this);
    this.sessionFiles = new SessionFilesClient(this);
    this.connections = new ConnectionsClient(this);
    this.budgets = new BudgetsClient(this);
  }

  /**
   * Create a client using environment variables.
   *
   * Reads `EVERRUNS_API_KEY` (required) and `EVERRUNS_API_URL` (optional).
   */
  static fromEnv(): Everruns {
    const baseUrl = process.env.EVERRUNS_API_URL;
    return new Everruns({ baseUrl });
  }

  /**
   * Build full URL from a path, adding the /v1 prefix.
   * Path should start with "/" (e.g., "/agents").
   */
  private url(path: string): string {
    // Ensure path starts with "/" for consistency
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;
    return `${this.baseUrl}/v1${normalizedPath}`;
  }

  async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = this.url(path);
    const response = await fetch(url, {
      ...options,
      headers: {
        Authorization: this.apiKey.toHeader(),
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const body = await response.text().catch(() => undefined);
      if (response.status === 401) {
        throw new AuthenticationError();
      }
      if (response.status === 404) {
        throw new NotFoundError("Resource");
      }
      if (response.status === 429) {
        const retryAfter = response.headers.get("Retry-After");
        throw new RateLimitError(
          retryAfter ? parseInt(retryAfter, 10) : undefined,
        );
      }
      // Simplify HTML responses to avoid verbose error messages
      const simplifiedBody = body && isHtmlResponse(body) ? undefined : body;
      throw new ApiError(
        response.status,
        `API error: ${response.statusText}`,
        simplifiedBody,
      );
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json() as Promise<T>;
  }

  async fetchText(path: string, options: RequestInit = {}): Promise<string> {
    const url = this.url(path);
    const response = await fetch(url, {
      ...options,
      headers: {
        Authorization: this.apiKey.toHeader(),
        ...options.headers,
      },
    });

    if (!response.ok) {
      const body = await response.text().catch(() => undefined);
      if (response.status === 401) throw new AuthenticationError();
      if (response.status === 404) throw new NotFoundError("Resource");
      if (response.status === 429) {
        const retryAfter = response.headers.get("Retry-After");
        throw new RateLimitError(
          retryAfter ? parseInt(retryAfter, 10) : undefined,
        );
      }
      const simplifiedBody = body && isHtmlResponse(body) ? undefined : body;
      throw new ApiError(
        response.status,
        `API error: ${response.statusText}`,
        simplifiedBody,
      );
    }

    return response.text();
  }

  getStreamUrl(path: string): string {
    return this.url(path);
  }

  getAuthHeader(): string {
    return this.apiKey.toHeader();
  }
}

class AgentsClient {
  constructor(private readonly client: Everruns) {}

  /** Create a new agent with a server-assigned ID. */
  async create(request: CreateAgentRequest): Promise<Agent> {
    validateAgentName(request.name);
    return this.client.fetch("/agents", {
      method: "POST",
      body: JSON.stringify(toAgentBody(request)),
    });
  }

  /**
   * Create or update an agent with a client-supplied ID (upsert).
   *
   * If an agent with the given ID exists, it is updated.
   * If not, a new agent is created with that ID.
   *
   * Use {@link generateAgentId} to create a properly formatted ID.
   */
  async apply(id: string, request: CreateAgentRequest): Promise<Agent> {
    validateAgentName(request.name);
    return this.client.fetch("/agents", {
      method: "POST",
      body: JSON.stringify({ ...toAgentBody(request), id }),
    });
  }

  /**
   * Create or update an agent by name (upsert).
   *
   * If an agent with the given `name` exists in the org, it is updated.
   * If not, a new agent is created with that name.
   */
  async applyByName(request: CreateAgentRequest): Promise<Agent> {
    validateAgentName(request.name);
    return this.client.fetch("/agents", {
      method: "POST",
      body: JSON.stringify(toAgentBody(request)),
    });
  }

  async get(agentId: string): Promise<Agent> {
    return this.client.fetch(`/agents/${agentId}`);
  }

  async list(options?: { search?: string }): Promise<Agent[]> {
    const query = options?.search
      ? `?search=${encodeURIComponent(options.search)}`
      : "";
    const response = await this.client.fetch<{ agents: Agent[] }>(
      `/agents${query}`,
    );
    return response.agents;
  }

  /** Copy an agent, creating a new agent with the same configuration. */
  async copy(agentId: string): Promise<Agent> {
    return this.client.fetch(`/agents/${agentId}/copy`, { method: "POST" });
  }

  async delete(agentId: string): Promise<void> {
    await this.client.fetch(`/agents/${agentId}`, { method: "DELETE" });
  }

  /** Import an agent from Markdown, YAML, JSON, or plain text. */
  async import(content: string): Promise<Agent> {
    return this.client.fetch("/agents/import", {
      method: "POST",
      body: content,
      headers: { "Content-Type": "text/plain" },
    });
  }

  /** Export an agent as Markdown with YAML front matter. */
  async export(agentId: string): Promise<string> {
    return this.client.fetchText(`/agents/${agentId}/export`);
  }
}

class SessionsClient {
  constructor(private readonly client: Everruns) {}

  async create(request: CreateSessionRequest = {}): Promise<Session> {
    if (request.harnessId && request.harnessName) {
      throw new Error("Cannot specify both harnessId and harnessName");
    }
    if (request.harnessName) {
      validateHarnessName(request.harnessName);
    }
    const body: Record<string, unknown> = {};
    if (request.harnessId) {
      body.harness_id = request.harnessId;
    }
    if (request.harnessName) {
      body.harness_name = request.harnessName;
    }
    if (request.agentId) {
      body.agent_id = request.agentId;
    }
    if (request.title) {
      body.title = request.title;
    }
    if (request.locale) {
      body.locale = request.locale;
    }
    if (request.modelId) {
      body.model_id = request.modelId;
    }
    if (request.tags?.length) {
      body.tags = request.tags;
    }
    if (request.capabilities?.length) {
      body.capabilities = request.capabilities;
    }
    if (request.initialFiles !== undefined) {
      body.initial_files = request.initialFiles.map((file) => ({
        path: file.path,
        content: file.content,
        encoding: file.encoding,
        is_readonly: file.isReadonly,
      }));
    }
    return this.client.fetch("/sessions", {
      method: "POST",
      body: JSON.stringify(body),
    });
  }

  async get(sessionId: string): Promise<Session> {
    return this.client.fetch(`/sessions/${sessionId}`);
  }

  async list(options?: {
    agentId?: string;
    search?: string;
  }): Promise<Session[]> {
    const params = new URLSearchParams();
    if (options?.agentId) params.set("agent_id", options.agentId);
    if (options?.search) params.set("search", options.search);
    const query = params.toString() ? `?${params}` : "";
    const response = await this.client.fetch<{ sessions: Session[] }>(
      `/sessions${query}`,
    );
    return response.sessions;
  }

  /** Delete a session. */
  async delete(sessionId: string): Promise<void> {
    await this.client.fetch(`/sessions/${sessionId}`, { method: "DELETE" });
  }

  /** Cancel the current turn in a session. */
  async cancel(sessionId: string): Promise<void> {
    await this.client.fetch(`/sessions/${sessionId}/cancel`, {
      method: "POST",
    });
  }

  /** Pin a session for the current user. */
  async pin(sessionId: string): Promise<void> {
    await this.client.fetch(`/sessions/${sessionId}/pin`, {
      method: "PUT",
    });
  }

  /** Unpin a session for the current user. */
  async unpin(sessionId: string): Promise<void> {
    await this.client.fetch(`/sessions/${sessionId}/pin`, {
      method: "DELETE",
    });
  }

  /** List budgets for a session. */
  async budgets(sessionId: string): Promise<Budget[]> {
    return this.client.fetch(`/sessions/${sessionId}/budgets`);
  }

  /** Check all budgets in hierarchy for a session. */
  async budgetCheck(sessionId: string): Promise<BudgetCheckResult> {
    return this.client.fetch(`/sessions/${sessionId}/budget-check`);
  }

  /** Resume paused budgets for a session. */
  async resume(sessionId: string): Promise<ResumeSessionResponse> {
    return this.client.fetch(`/sessions/${sessionId}/resume`, {
      method: "POST",
    });
  }

  /** Batch-set encrypted secrets for a session. */
  async setSecrets(
    sessionId: string,
    secrets: Record<string, string>,
  ): Promise<void> {
    await this.client.fetch(`/sessions/${sessionId}/storage/secrets`, {
      method: "PUT",
      body: JSON.stringify({ secrets }),
    });
  }

  /** Export a session's messages as JSONL. */
  async export(sessionId: string): Promise<string> {
    return this.client.fetchText(`/sessions/${sessionId}/export`);
  }
}

class MessagesClient {
  constructor(private readonly client: Everruns) {}

  /**
   * Create a new message (send text).
   */
  async create(sessionId: string, text: string): Promise<Message>;
  async create(
    sessionId: string,
    request: CreateMessageRequest,
  ): Promise<Message>;
  async create(
    sessionId: string,
    textOrRequest: string | CreateMessageRequest,
  ): Promise<Message> {
    const request: CreateMessageRequest =
      typeof textOrRequest === "string"
        ? {
            message: {
              role: "user",
              content: [{ type: "text", text: textOrRequest }],
            },
          }
        : textOrRequest;
    return this.client.fetch(`/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /**
   * Send tool results back to the session.
   *
   * Use after receiving tool calls from an `output.message.completed`
   * event to provide results from locally-executed tools.
   */
  async createToolResults(
    sessionId: string,
    results: ContentPart[],
  ): Promise<Message> {
    const request: CreateMessageRequest = {
      message: { role: "tool_result", content: results },
    };
    return this.client.fetch(`/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async list(sessionId: string): Promise<Message[]> {
    const response = await this.client.fetch<{ messages: Message[] }>(
      `/sessions/${sessionId}/messages`,
    );
    return response.messages;
  }
}

class EventsClient {
  constructor(private readonly client: Everruns) {}

  async list(
    sessionId: string,
    options?: StreamOptions & ListEventsOptions,
  ): Promise<Event[]> {
    const params = new URLSearchParams();
    if (options?.sinceId) params.set("since_id", options.sinceId);
    if (options?.types) {
      for (const t of options.types) {
        params.append("types", t);
      }
    }
    if (options?.exclude) {
      for (const e of options.exclude) {
        params.append("exclude", e);
      }
    }
    if (options?.limit != null) params.set("limit", String(options.limit));
    if (options?.beforeSequence != null)
      params.set("before_sequence", String(options.beforeSequence));
    const query = params.toString() ? `?${params}` : "";
    const response = await this.client.fetch<{ events: Event[] }>(
      `/sessions/${sessionId}/events${query}`,
    );
    return response.events;
  }

  /**
   * Stream events from a session via SSE with automatic reconnection.
   *
   * The stream automatically handles:
   * - Server-initiated `disconnecting` events (connection cycling)
   * - Unexpected disconnections with exponential backoff
   * - Resume from last event ID via `since_id`
   *
   * @param sessionId - The session to stream events from
   * @param options - Optional stream configuration
   * @returns An async iterable of events
   *
   * @example
   * ```typescript
   * const stream = client.events.stream(sessionId);
   * for await (const event of stream) {
   *   console.log(event.type, event.data);
   * }
   * ```
   */
  stream(sessionId: string, options?: StreamOptions): EventStream {
    // Build base URL (without since_id - EventStream handles that for reconnection)
    const url = this.client.getStreamUrl(`/sessions/${sessionId}/sse`);
    return new EventStream(url, this.client.getAuthHeader(), options);
  }
}

class CapabilitiesClient {
  constructor(private readonly client: Everruns) {}

  /** List all available capabilities. */
  async list(): Promise<ListResponse<CapabilityInfo>> {
    const response = await this.client.fetch<
      ListResponse<CapabilityInfo>
    >("/capabilities");
    return { data: response.data, total: response.total ?? 0, offset: response.offset ?? 0, limit: response.limit ?? 0 };
  }

  /** Get a specific capability by ID. */
  async get(capabilityId: string): Promise<CapabilityInfo> {
    return this.client.fetch(`/capabilities/${capabilityId}`);
  }
}

class SessionFilesClient {
  constructor(private readonly client: Everruns) {}

  /** List files in a directory. */
  async list(
    sessionId: string,
    options?: { path?: string; recursive?: boolean },
  ): Promise<ListResponse<FileInfo>> {
    const fsPath = options?.path
      ? `/sessions/${sessionId}/fs/${options.path.replace(/^\//, "")}`
      : `/sessions/${sessionId}/fs`;
    const params = new URLSearchParams();
    if (options?.recursive) params.set("recursive", "true");
    const query = params.toString() ? `?${params}` : "";
    const response = await this.client.fetch<ListResponse<FileInfo>>(
      `${fsPath}${query}`,
    );
    return { data: response.data, total: response.total ?? 0, offset: response.offset ?? 0, limit: response.limit ?? 0 };
  }

  /** Read a file's content. */
  async read(sessionId: string, path: string): Promise<SessionFile> {
    return this.client.fetch(
      `/sessions/${sessionId}/fs/${path.replace(/^\//, "")}`,
    );
  }

  /** Create a file. */
  async create(
    sessionId: string,
    path: string,
    content: string,
    options?: { encoding?: string; isReadonly?: boolean },
  ): Promise<SessionFile> {
    const body: Record<string, unknown> = { content };
    if (options?.encoding) body.encoding = options.encoding;
    if (options?.isReadonly != null) body.is_readonly = options.isReadonly;
    return this.client.fetch(
      `/sessions/${sessionId}/fs/${path.replace(/^\//, "")}`,
      { method: "POST", body: JSON.stringify(body) },
    );
  }

  /** Create a directory. */
  async createDir(sessionId: string, path: string): Promise<SessionFile> {
    return this.client.fetch(
      `/sessions/${sessionId}/fs/${path.replace(/^\//, "")}`,
      { method: "POST", body: JSON.stringify({ is_directory: true }) },
    );
  }

  /** Update a file's content. */
  async update(
    sessionId: string,
    path: string,
    content: string,
    options?: { encoding?: string; isReadonly?: boolean },
  ): Promise<SessionFile> {
    const body: Record<string, unknown> = { content };
    if (options?.encoding) body.encoding = options.encoding;
    if (options?.isReadonly != null) body.is_readonly = options.isReadonly;
    return this.client.fetch(
      `/sessions/${sessionId}/fs/${path.replace(/^\//, "")}`,
      { method: "PUT", body: JSON.stringify(body) },
    );
  }

  /** Delete a file or directory. */
  async delete(
    sessionId: string,
    path: string,
    options?: { recursive?: boolean },
  ): Promise<DeleteFileResponse> {
    const params = new URLSearchParams();
    if (options?.recursive) params.set("recursive", "true");
    const query = params.toString() ? `?${params}` : "";
    return this.client.fetch(
      `/sessions/${sessionId}/fs/${path.replace(/^\//, "")}${query}`,
      { method: "DELETE" },
    );
  }

  /** Move/rename a file. */
  async moveFile(
    sessionId: string,
    srcPath: string,
    dstPath: string,
  ): Promise<SessionFile> {
    return this.client.fetch(`/sessions/${sessionId}/fs/_/move`, {
      method: "POST",
      body: JSON.stringify({ src_path: srcPath, dst_path: dstPath }),
    });
  }

  /** Copy a file. */
  async copyFile(
    sessionId: string,
    srcPath: string,
    dstPath: string,
  ): Promise<SessionFile> {
    return this.client.fetch(`/sessions/${sessionId}/fs/_/copy`, {
      method: "POST",
      body: JSON.stringify({ src_path: srcPath, dst_path: dstPath }),
    });
  }

  /** Search files with regex. */
  async grep(
    sessionId: string,
    pattern: string,
    options?: { pathPattern?: string },
  ): Promise<GrepResult[]> {
    const body: Record<string, unknown> = { pattern };
    if (options?.pathPattern) body.path_pattern = options.pathPattern;
    const response = await this.client.fetch<{ data: GrepResult[] }>(
      `/sessions/${sessionId}/fs/_/grep`,
      { method: "POST", body: JSON.stringify(body) },
    );
    return response.data;
  }

  /** Get file or directory stat. */
  async stat(sessionId: string, path: string): Promise<FileStat> {
    return this.client.fetch(`/sessions/${sessionId}/fs/_/stat`, {
      method: "POST",
      body: JSON.stringify({ path }),
    });
  }
}

class BudgetsClient {
  constructor(private readonly client: Everruns) {}

  /** Create a budget. */
  async create(request: CreateBudgetRequest): Promise<Budget> {
    return this.client.fetch("/budgets", {
      method: "POST",
      body: JSON.stringify({
        subject_type: request.subjectType,
        subject_id: request.subjectId,
        currency: request.currency,
        limit: request.limit,
        soft_limit: request.softLimit,
        period: request.period,
        metadata: request.metadata,
      }),
    });
  }

  /** List budgets, optionally filtered by subject. */
  async list(options?: {
    subjectType?: string;
    subjectId?: string;
  }): Promise<Budget[]> {
    const params = new URLSearchParams();
    if (options?.subjectType) params.set("subject_type", options.subjectType);
    if (options?.subjectId) params.set("subject_id", options.subjectId);
    const query = params.toString() ? `?${params}` : "";
    return this.client.fetch(`/budgets${query}`);
  }

  /** Get a budget by ID. */
  async get(budgetId: string): Promise<Budget> {
    return this.client.fetch(`/budgets/${budgetId}`);
  }

  /** Update a budget. */
  async update(
    budgetId: string,
    request: UpdateBudgetRequest,
  ): Promise<Budget> {
    return this.client.fetch(`/budgets/${budgetId}`, {
      method: "PATCH",
      body: JSON.stringify({
        limit: request.limit,
        soft_limit: request.softLimit,
        status: request.status,
        metadata: request.metadata,
      }),
    });
  }

  /** Delete (soft-delete) a budget. */
  async delete(budgetId: string): Promise<void> {
    await this.client.fetch(`/budgets/${budgetId}`, { method: "DELETE" });
  }

  /** Add credits to a budget. */
  async topUp(budgetId: string, request: TopUpRequest): Promise<Budget> {
    return this.client.fetch(`/budgets/${budgetId}/top-up`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  /** Get paginated ledger entries for a budget. */
  async ledger(
    budgetId: string,
    options?: { limit?: number; offset?: number },
  ): Promise<LedgerEntry[]> {
    const params = new URLSearchParams();
    if (options?.limit != null) params.set("limit", String(options.limit));
    if (options?.offset != null) params.set("offset", String(options.offset));
    const query = params.toString() ? `?${params}` : "";
    return this.client.fetch(`/budgets/${budgetId}/ledger${query}`);
  }

  /** Check budget status. */
  async check(budgetId: string): Promise<BudgetCheckResult> {
    return this.client.fetch(`/budgets/${budgetId}/check`);
  }
}

class ConnectionsClient {
  constructor(private readonly client: Everruns) {}

  /** Set an API key connection for a provider. */
  async set(provider: string, apiKey: string): Promise<Connection> {
    return this.client.fetch(`/user/connections/${provider}`, {
      method: "POST",
      body: JSON.stringify({ api_key: apiKey }),
    });
  }

  /** List all connections. */
  async list(): Promise<Connection[]> {
    const response = await this.client.fetch<{ data: Connection[] }>(
      "/user/connections",
    );
    return response.data;
  }

  /** Remove a connection. */
  async remove(provider: string): Promise<void> {
    await this.client.fetch(`/user/connections/${provider}`, {
      method: "DELETE",
    });
  }
}

/** Build the JSON body for agent creation from a CreateAgentRequest. */
function toAgentBody(request: CreateAgentRequest): Record<string, unknown> {
  const body: Record<string, unknown> = {
    name: request.name,
    system_prompt: request.systemPrompt,
    model: request.model,
  };
  if (request.id) {
    body.id = request.id;
  }
  if (request.displayName) {
    body.display_name = request.displayName;
  }
  if (request.capabilities?.length) {
    body.capabilities = request.capabilities;
  }
  if (request.initialFiles?.length) {
    body.initial_files = request.initialFiles.map((file) => ({
      path: file.path,
      content: file.content,
      encoding: file.encoding,
      is_readonly: file.isReadonly,
    }));
  }
  return body;
}

/** Check if the body looks like an HTML response */
function isHtmlResponse(body: string): boolean {
  const trimmed = body.trimStart();
  return (
    trimmed.startsWith("<!DOCTYPE") || trimmed.toLowerCase().startsWith("<html")
  );
}
