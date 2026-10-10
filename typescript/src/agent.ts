/**
 * Agent client: call one agent from code through the Agent Execution API.
 *
 * Holds a credential that reaches one agent's session routes and nothing else
 * (an agent key `evr_ak_...`, a runtime token, an identity-provider token, or a
 * member's personal access token when the agent allows it). The same routes are
 * served by the everruns server (`{api}/v1/channels/{channel_id}`) and by a
 * serve app (`{host}/v1/channels/{agent}`). See specs/agent-client.md.
 *
 * Decision: no `X-Org-Id` and no change-reason header; the agent URL already
 * names the agent and its organization.
 */
import {
  ApiError,
  AuthenticationError,
  EverrunsError,
  NotFoundError,
  RateLimitError,
  ValidationError,
} from "./errors.js";
import type { Event } from "./models.js";
import { EventStream } from "./sse.js";

/** Reconnects `run` allows after the stream ends or drops without a result. */
const RUN_MAX_RETRIES = 5;

/** Request header naming the application user a key acts for. */
export const END_USER_HEADER = "End-User";

export interface AgentClientOptions {
  /** Agent base URL. Defaults to `EVERRUNS_AGENT_URL`. */
  agentUrl?: string;
  /** Bearer credential. Defaults to `EVERRUNS_AGENT_KEY`. */
  credential?: string;
  /** Sent as `End-User` on every request (needs a key holding `end_user`). */
  endUser?: string;
}

/** Agent card served at the agent base URL. */
export interface AgentCard {
  name: string;
  description?: string | null;
  streaming: boolean;
  input: { text: boolean; images: boolean; files: boolean };
  auth: { type: string; issuer?: string | null }[];
  conversation_starters: string[];
  links: Record<string, string | null | undefined>;
  [key: string]: unknown;
}

/** A session as the agent API returns it. Unknown fields are kept. */
export interface AgentSession {
  id: string;
  title?: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  pending_questions?: unknown[];
  pending_approvals?: unknown[];
  [key: string]: unknown;
}

/** A message the agent API accepted. */
export interface AgentMessage {
  id: string;
  [key: string]: unknown;
}

export interface AgentSessionList {
  data: AgentSession[];
  next_page_token?: string | null;
}

/** Response of the `runtime-auth` exchange: hand `access_token` to a browser. */
export interface RuntimeToken {
  access_token: string;
  token_type: string;
  expires_in: number;
  virtual_user_id: string;
}

export interface CreateAgentSessionOptions {
  title?: string;
  idempotencyKey?: string;
}

export interface ListAgentSessionsOptions {
  limit?: number;
  pageToken?: string;
}

export interface ListAgentEventsOptions {
  /** Return events after this sequence number (exclusive). */
  afterSequence?: number;
  limit?: number;
}

export interface SendAgentMessageOptions {
  idempotencyKey?: string;
}

export interface StreamAgentEventsOptions {
  /** Resume after this event id. */
  sinceId?: string;
  /** Replay events after this sequence first (`0`: the whole session). */
  afterSequence?: number;
  maxRetries?: number;
  idleTimeoutMs?: number;
}

/**
 * Client for one agent.
 *
 * @example
 * ```typescript
 * const agent = new AgentClient(); // EVERRUNS_AGENT_URL + EVERRUNS_AGENT_KEY
 * console.log(await agent.run("Hello!"));
 *
 * const alice = agent.forEndUser("customer-42");
 * const token = await alice.runtimeToken(); // for a browser
 * ```
 */
export class AgentClient {
  private readonly agentUrl: string;
  private readonly credential: string;
  private readonly endUser?: string;

  constructor(options: AgentClientOptions = {}) {
    const agentUrl = options.agentUrl ?? process.env.EVERRUNS_AGENT_URL;
    const credential = options.credential ?? process.env.EVERRUNS_AGENT_KEY;
    if (!agentUrl) {
      throw new ValidationError(
        "agent URL is required: pass agentUrl or set EVERRUNS_AGENT_URL",
      );
    }
    if (!credential) {
      throw new ValidationError(
        "credential is required: pass credential or set EVERRUNS_AGENT_KEY",
      );
    }
    if (options.endUser !== undefined && options.endUser.length === 0) {
      throw new ValidationError("endUser cannot be empty");
    }
    this.agentUrl = trimTrailingSlashes(agentUrl);
    this.credential = credential;
    this.endUser = options.endUser;
  }

  /** Create a client from `EVERRUNS_AGENT_URL` and `EVERRUNS_AGENT_KEY`. */
  static fromEnv(): AgentClient {
    return new AgentClient();
  }

  /**
   * Derive a client that sends `End-User: <id>` on every request. It shares
   * this client's configuration; this client is left unchanged.
   */
  forEndUser(endUser: string): AgentClient {
    return new AgentClient({
      agentUrl: this.agentUrl,
      credential: this.credential,
      endUser,
    });
  }

  /** The agent card (`GET` on the base URL itself). */
  async card(): Promise<AgentCard> {
    return this.request<AgentCard>("");
  }

  /** Create a session. */
  async createSession(
    options: CreateAgentSessionOptions = {},
  ): Promise<AgentSession> {
    const body: Record<string, unknown> = {};
    if (options.title !== undefined) body.title = options.title;
    return this.request<AgentSession>("/sessions", {
      method: "POST",
      body: JSON.stringify(body),
      headers: idempotencyHeaders(options.idempotencyKey),
    });
  }

  /** List the caller's sessions. */
  async listSessions(
    options: ListAgentSessionsOptions = {},
  ): Promise<AgentSessionList> {
    const params = new URLSearchParams();
    if (options.limit != null) params.set("limit", String(options.limit));
    if (options.pageToken) params.set("page_token", options.pageToken);
    return this.request<AgentSessionList>(`/sessions${queryString(params)}`);
  }

  /** Get a session, including `pending_questions` and `pending_approvals`. */
  async getSession(sessionId: string): Promise<AgentSession> {
    return this.request<AgentSession>(`/sessions/${sessionId}`);
  }

  /** Send a user text message. */
  async sendMessage(
    sessionId: string,
    text: string,
    options: SendAgentMessageOptions = {},
  ): Promise<AgentMessage> {
    return this.request<AgentMessage>(`/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({
        message: { role: "user", content: [{ type: "text", text }] },
      }),
      headers: idempotencyHeaders(options.idempotencyKey),
    });
  }

  /** Cancel the session's running turn. */
  async cancel(sessionId: string): Promise<unknown> {
    return this.request(`/sessions/${sessionId}/cancel`, { method: "POST" });
  }

  /** List events; page forward with `afterSequence` (exclusive). */
  async listEvents(
    sessionId: string,
    options: ListAgentEventsOptions = {},
  ): Promise<Event[]> {
    const params = new URLSearchParams();
    if (options.afterSequence != null) {
      params.set("after_sequence", String(options.afterSequence));
    }
    if (options.limit != null) params.set("limit", String(options.limit));
    const response = await this.request<{ data: Event[] }>(
      `/sessions/${sessionId}/events${queryString(params)}`,
    );
    return response.data;
  }

  /**
   * Follow a session's events over SSE, with the SDK's reconnect rules
   * (specs/sse-streaming.md).
   */
  streamEvents(
    sessionId: string,
    options: StreamAgentEventsOptions = {},
  ): EventStream {
    const { afterSequence, ...streamOptions } = options;
    return new EventStream(
      this.url(`/sessions/${sessionId}/sse`),
      this.authorization(),
      streamOptions,
      undefined,
      { headers: this.endUserHeaders(), afterSequence },
    );
  }

  /** Answer the session's pending questions (pass-through JSON body). */
  async answerQuestions(sessionId: string, answers: unknown): Promise<unknown> {
    return this.request(`/sessions/${sessionId}/question-answers`, {
      method: "POST",
      body: JSON.stringify(answers),
    });
  }

  /** Decide the session's gated tool calls (pass-through JSON body). */
  async submitToolApprovals(
    sessionId: string,
    decisions: unknown,
  ): Promise<unknown> {
    return this.request(`/sessions/${sessionId}/tool-approvals`, {
      method: "POST",
      body: JSON.stringify(decisions),
    });
  }

  /**
   * Exchange the key for a short-lived runtime token to hand to a browser.
   * Needs `End-User`: call it on a {@link AgentClient.forEndUser} client.
   */
  async runtimeToken(): Promise<RuntimeToken> {
    return this.request<RuntimeToken>("/runtime-auth", { method: "POST" });
  }

  /**
   * Send `text` and return the agent's final reply.
   *
   * Creates a session when `sessionId` is not given, sends the message,
   * follows the stream until the turn completes (`turn.completed`) and returns
   * the last assistant message text. A failed turn (`turn.failed`) raises
   * {@link EverrunsError}.
   */
  async run(text: string, sessionId?: string): Promise<string> {
    // A stream without a cursor is live only and would miss a turn that
    // finishes quickly. A new session replays from 0; an existing one resumes
    // after its newest event, read before sending so earlier turns are skipped.
    const id = sessionId ?? (await this.createSession()).id;
    const after = sessionId === undefined ? 0 : await this.latestSequence(id);
    await this.sendMessage(id, text);

    const stream = this.streamEvents(id, {
      afterSequence: after,
      maxRetries: RUN_MAX_RETRIES,
    });
    let reply = "";
    try {
      for await (const event of stream) {
        if (event.type === "output.message.completed") {
          reply = messageText(event.data) ?? reply;
        } else if (event.type === "turn.completed") {
          return reply;
        } else if (event.type === "turn.failed") {
          throw new EverrunsError(`Turn failed: ${failureMessage(event.data)}`);
        }
      }
    } finally {
      stream.abort();
    }
    throw new EverrunsError("Stream ended before the turn completed");
  }

  /** Newest event sequence of a session (0 when it has none). */
  private async latestSequence(sessionId: string): Promise<number> {
    const limit = 500;
    let latest = 0;
    for (;;) {
      const page = await this.listEvents(sessionId, {
        afterSequence: latest,
        limit,
      });
      let next = latest;
      for (const event of page) {
        const sequence = (event as { sequence?: unknown }).sequence;
        if (typeof sequence === "number" && sequence > next) next = sequence;
      }
      if (page.length < limit || next === latest) return next;
      latest = next;
    }
  }

  private url(path: string): string {
    return `${this.agentUrl}${path}`;
  }

  private authorization(): string {
    return `Bearer ${this.credential}`;
  }

  private endUserHeaders(): Record<string, string> {
    return this.endUser === undefined
      ? {}
      : { [END_USER_HEADER]: this.endUser };
  }

  private async request<T>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    const response = await fetch(this.url(path), {
      ...options,
      headers: {
        Authorization: this.authorization(),
        "Content-Type": "application/json",
        ...this.endUserHeaders(),
        ...(options.headers as Record<string, string> | undefined),
      },
    });
    if (!response.ok) {
      throw await errorFromResponse(response);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  }
}

function idempotencyHeaders(key?: string): Record<string, string> {
  return key ? { "Idempotency-Key": key } : {};
}

function queryString(params: URLSearchParams): string {
  const query = params.toString();
  return query ? `?${query}` : "";
}

function trimTrailingSlashes(value: string): string {
  let end = value.length;
  while (end > 0 && value.charCodeAt(end - 1) === 47) {
    end -= 1;
  }
  return value.slice(0, end);
}

/** Map a non-2xx response to the SDK's error types, keeping the problem `code`. */
async function errorFromResponse(response: Response): Promise<ApiError> {
  const text = await response.text().catch(() => "");
  let body: unknown = text || undefined;
  let code: string | undefined;
  let detail: string | undefined;
  try {
    const parsed = JSON.parse(text) as Record<string, unknown>;
    body = parsed;
    if (typeof parsed.code === "string") code = parsed.code;
    const message = parsed.message ?? parsed.detail ?? parsed.error;
    if (typeof message === "string") detail = message;
  } catch {
    // Not JSON (or empty): keep the raw text.
  }
  const withCode = <E extends ApiError>(error: E): E => {
    Object.assign(error, { body, code });
    return error;
  };
  if (response.status === 401) {
    return withCode(new AuthenticationError(detail));
  }
  if (response.status === 404) {
    return withCode(new NotFoundError("Resource"));
  }
  if (response.status === 429) {
    const retryAfter = response.headers.get("Retry-After");
    return withCode(
      new RateLimitError(retryAfter ? parseInt(retryAfter, 10) : undefined),
    );
  }
  return new ApiError(
    response.status,
    detail ?? `API error: ${response.statusText || response.status}`,
    body,
    code,
  );
}

function messageText(data: unknown): string | undefined {
  const content = (data as { message?: { content?: unknown } })?.message
    ?.content;
  if (!Array.isArray(content)) return undefined;
  const texts = content
    .filter((part) => part?.type === "text")
    .map((part) => (part.text as string | undefined) ?? "");
  return texts.length > 0 ? texts.join("") : undefined;
}

function failureMessage(data: unknown): string {
  const d = data as { error?: unknown; message?: unknown } | undefined;
  const detail = d?.error ?? d?.message;
  if (typeof detail === "string") return detail;
  if (detail !== undefined) return JSON.stringify(detail);
  return "unknown error";
}
