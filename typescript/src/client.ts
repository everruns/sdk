/**
 * Everruns API client.
 */
import { ApiKey } from "./auth.js";
import {
  Agent,
  CreateAgentRequest,
  Session,
  CreateSessionRequest,
  Message,
  CreateMessageRequest,
  Event,
  StreamOptions,
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

  getStreamUrl(path: string): string {
    return this.url(path);
  }

  getAuthHeader(): string {
    return this.apiKey.toHeader();
  }
}

class AgentsClient {
  constructor(private readonly client: Everruns) {}

  async create(request: CreateAgentRequest): Promise<Agent> {
    return this.client.fetch("/agents", {
      method: "POST",
      body: JSON.stringify({
        name: request.name,
        system_prompt: request.systemPrompt,
        model: request.model,
      }),
    });
  }

  async get(agentId: string): Promise<Agent> {
    return this.client.fetch(`/agents/${agentId}`);
  }

  async list(): Promise<Agent[]> {
    const response = await this.client.fetch<{ agents: Agent[] }>("/agents");
    return response.agents;
  }

  async delete(agentId: string): Promise<void> {
    await this.client.fetch(`/agents/${agentId}`, { method: "DELETE" });
  }
}

class SessionsClient {
  constructor(private readonly client: Everruns) {}

  async create(request: CreateSessionRequest): Promise<Session> {
    return this.client.fetch("/sessions", {
      method: "POST",
      body: JSON.stringify({ agent_id: request.agentId }),
    });
  }

  async get(sessionId: string): Promise<Session> {
    return this.client.fetch(`/sessions/${sessionId}`);
  }

  async list(agentId?: string): Promise<Session[]> {
    const query = agentId ? `?agent_id=${agentId}` : "";
    const response = await this.client.fetch<{ sessions: Session[] }>(
      `/sessions${query}`,
    );
    return response.sessions;
  }
}

class MessagesClient {
  constructor(private readonly client: Everruns) {}

  async create(
    sessionId: string,
    request: CreateMessageRequest,
  ): Promise<Message> {
    return this.client.fetch(`/sessions/${sessionId}/messages`, {
      method: "POST",
      body: JSON.stringify({
        text: request.text,
        image_urls: request.imageUrls,
      }),
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

  async list(sessionId: string, options?: StreamOptions): Promise<Event[]> {
    const params = new URLSearchParams();
    if (options?.sinceId) params.set("since_id", options.sinceId);
    if (options?.exclude) params.set("exclude", options.exclude.join(","));
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
    const url = this.client.getStreamUrl(`/v1/sessions/${sessionId}/sse`);
    return new EventStream(url, this.client.getAuthHeader(), options);
  }
}

/** Check if the body looks like an HTML response */
function isHtmlResponse(body: string): boolean {
  const trimmed = body.trimStart();
  return (
    trimmed.startsWith("<!DOCTYPE") || trimmed.toLowerCase().startsWith("<html")
  );
}
