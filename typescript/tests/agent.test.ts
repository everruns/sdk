import { afterEach, describe, expect, it, vi } from "vitest";
import { AgentClient } from "../src/agent.js";
import * as sdk from "../src/index.js";
import {
  ApiError,
  AuthenticationError,
  EverrunsError,
  NotFoundError,
  RateLimitError,
  ValidationError,
} from "../src/errors.js";

const BASE = "https://example.test/api/v1/channels/apichan_1";

interface Call {
  url: string;
  init: RequestInit;
  headers: Record<string, string>;
}

function jsonResponse(body: unknown, status = 200, headers = {}): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

/** Stub fetch with a queue of responses; returns the recorded calls. */
function mockFetch(...responses: (Response | (() => Response))[]): Call[] {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init: RequestInit = {}) => {
      calls.push({
        url,
        init,
        headers: { ...(init.headers as Record<string, string>) },
      });
      const next = responses.shift();
      if (!next) throw new Error("unexpected fetch");
      return typeof next === "function" ? next() : next;
    }),
  );
  return calls;
}

function sse(events: { id: string; type: string; data?: unknown }[]): Response {
  const body = events
    .map(
      (e) =>
        `event: ${e.type}\ndata: ${JSON.stringify({
          id: e.id,
          type: e.type,
          data: e.data ?? {},
          createdAt: "2024-01-01T00:00:00Z",
        })}\n\n`,
    )
    .join("");
  return new Response(body, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

const reply = (id: string, text: string) => ({
  id,
  type: "output.message.completed",
  data: { message: { content: [{ type: "text", text }] } },
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("AgentClient construction", () => {
  it("exports the agent client as AgentClient", () => {
    expect(sdk.AgentClient).toBe(AgentClient);
  });

  it("reads URL and credential from env", async () => {
    vi.stubEnv("EVERRUNS_AGENT_URL", BASE);
    vi.stubEnv("EVERRUNS_AGENT_KEY", "evr_ak_env");
    const calls = mockFetch(jsonResponse({ name: "a" }));
    await new AgentClient().card();
    expect(calls[0].url).toBe(BASE);
    expect(calls[0].headers.Authorization).toBe("Bearer evr_ak_env");
  });

  it("rejects a missing URL or credential", () => {
    vi.stubEnv("EVERRUNS_AGENT_URL", "");
    vi.stubEnv("EVERRUNS_AGENT_KEY", "");
    expect(() => new AgentClient({ credential: "k" })).toThrow(ValidationError);
    expect(() => new AgentClient({ agentUrl: BASE })).toThrow(ValidationError);
  });
});

describe("AgentClient requests", () => {
  it("sends the bearer credential and no org or reason headers", async () => {
    const calls = mockFetch(jsonResponse({ data: [] }));
    const agent = new AgentClient({ agentUrl: BASE, credential: "evr_ak_x" });
    await agent.listSessions({ limit: 5, pageToken: "tok" });
    expect(calls[0].url).toBe(`${BASE}/sessions?limit=5&page_token=tok`);
    expect(calls[0].headers.Authorization).toBe("Bearer evr_ak_x");
    expect(calls[0].headers["End-User"]).toBeUndefined();
    expect(calls[0].headers["X-Org-Id"]).toBeUndefined();
    expect(calls[0].headers["Everruns-Change-Reason"]).toBeUndefined();
  });

  it("joins URLs with and without a trailing slash; card hits the base", async () => {
    const calls = mockFetch(
      jsonResponse({ name: "a" }),
      jsonResponse({ name: "a" }),
      jsonResponse({ id: "s1" }, 201),
    );
    await new AgentClient({ agentUrl: `${BASE}/`, credential: "k" }).card();
    await new AgentClient({ agentUrl: `${BASE}//`, credential: "k" }).card();
    await new AgentClient({ agentUrl: BASE, credential: "k" }).createSession();
    expect(calls.map((c) => c.url)).toEqual([BASE, BASE, `${BASE}/sessions`]);
  });

  it("forEndUser sends End-User and leaves the original unchanged", async () => {
    const calls = mockFetch(jsonResponse({}), jsonResponse({}));
    const agent = new AgentClient({ agentUrl: BASE, credential: "k" });
    const alice = agent.forEndUser("customer-42");
    await alice.getSession("s1");
    await agent.getSession("s1");
    expect(calls[0].url).toBe(`${BASE}/sessions/s1`);
    expect(calls[0].headers["End-User"]).toBe("customer-42");
    expect(calls[0].headers.Authorization).toBe("Bearer k");
    expect(calls[1].headers["End-User"]).toBeUndefined();
  });

  it("createSession posts title and Idempotency-Key", async () => {
    const calls = mockFetch(jsonResponse({ id: "s1" }, 201), jsonResponse({}));
    const agent = new AgentClient({ agentUrl: BASE, credential: "k" });
    await agent.createSession({ title: "Hi", idempotencyKey: "key-1" });
    await agent.createSession();
    expect(calls[0].init.method).toBe("POST");
    expect(JSON.parse(calls[0].init.body as string)).toEqual({ title: "Hi" });
    expect(calls[0].headers["Idempotency-Key"]).toBe("key-1");
    expect(JSON.parse(calls[1].init.body as string)).toEqual({});
    expect(calls[1].headers["Idempotency-Key"]).toBeUndefined();
  });

  it("sendMessage posts the text message body and Idempotency-Key", async () => {
    const calls = mockFetch(jsonResponse({ id: "m1" }, 201));
    await new AgentClient({ agentUrl: BASE, credential: "k" }).sendMessage(
      "s1",
      "hello",
      { idempotencyKey: "key-2" },
    );
    expect(calls[0].url).toBe(`${BASE}/sessions/s1/messages`);
    expect(JSON.parse(calls[0].init.body as string)).toEqual({
      message: { role: "user", content: [{ type: "text", text: "hello" }] },
    });
    expect(calls[0].headers["Idempotency-Key"]).toBe("key-2");
  });

  it("covers cancel, listEvents, answers, approvals and runtime token", async () => {
    const calls = mockFetch(
      jsonResponse({}),
      jsonResponse({ data: [{ id: "e1", type: "x" }] }),
      jsonResponse({}),
      jsonResponse({}),
      jsonResponse({
        access_token: "t",
        token_type: "Bearer",
        expires_in: 900,
        virtual_user_id: "u",
      }),
    );
    const agent = new AgentClient({
      agentUrl: BASE,
      credential: "k",
    }).forEndUser("u1");
    await agent.cancel("s1");
    const events = await agent.listEvents("s1", {
      afterSequence: 3,
      limit: 10,
    });
    await agent.answerQuestions("s1", { answers: [] });
    await agent.submitToolApprovals("s1", { decisions: [] });
    const token = await agent.runtimeToken();
    expect(events).toHaveLength(1);
    expect(token.access_token).toBe("t");
    expect(calls.map((c) => `${c.init.method ?? "GET"} ${c.url}`)).toEqual([
      `POST ${BASE}/sessions/s1/cancel`,
      `GET ${BASE}/sessions/s1/events?after_sequence=3&limit=10`,
      `POST ${BASE}/sessions/s1/question-answers`,
      `POST ${BASE}/sessions/s1/tool-approvals`,
      `POST ${BASE}/runtime-auth`,
    ]);
    expect(calls[4].headers["End-User"]).toBe("u1");
  });
});

describe("AgentClient error mapping", () => {
  const agent = () => new AgentClient({ agentUrl: BASE, credential: "k" });

  it("maps 401 to AuthenticationError", async () => {
    mockFetch(jsonResponse({ code: "unauthorized" }, 401));
    await expect(agent().card()).rejects.toBeInstanceOf(AuthenticationError);
  });

  it("maps 403 with its code", async () => {
    mockFetch(
      jsonResponse({ code: "end_user_not_allowed", message: "no" }, 403),
    );
    const error = await agent()
      .getSession("s1")
      .catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.statusCode).toBe(403);
    expect(error.code).toBe("end_user_not_allowed");
    expect(error.message).toBe("no");
  });

  it("maps 404 to NotFoundError", async () => {
    mockFetch(jsonResponse({ code: "not_found" }, 404));
    const error = await agent()
      .getSession("s1")
      .catch((e) => e);
    expect(error).toBeInstanceOf(NotFoundError);
    expect(error.code).toBe("not_found");
  });

  it("maps 422 with its problem code", async () => {
    mockFetch(jsonResponse({ code: "invalid_message", message: "bad" }, 422));
    const error = await agent()
      .sendMessage("s1", "")
      .catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.statusCode).toBe(422);
    expect(error.code).toBe("invalid_message");
  });

  it("maps 429 to RateLimitError with Retry-After", async () => {
    mockFetch(jsonResponse({}, 429, { "Retry-After": "7" }));
    const error = await agent()
      .card()
      .catch((e) => e);
    expect(error).toBeInstanceOf(RateLimitError);
    expect(error.retryAfter).toBe(7);
  });
});

describe("AgentClient streaming and run", () => {
  const agent = () =>
    new AgentClient({ agentUrl: BASE, credential: "evr_ak_s" }).forEndUser(
      "u1",
    );

  it("streamEvents hits /sse with auth, End-User and after_sequence", async () => {
    const calls = mockFetch(sse([{ id: "e1", type: "turn.started" }]));
    const stream = agent().streamEvents("s1", {
      afterSequence: 0,
      maxRetries: 0,
    });
    const seen: string[] = [];
    for await (const event of stream) {
      seen.push(event.type);
      stream.abort();
    }
    expect(seen).toEqual(["turn.started"]);
    expect(calls[0].url).toBe(`${BASE}/sessions/s1/sse?after_sequence=0`);
    expect(calls[0].headers.Authorization).toBe("Bearer evr_ak_s");
    expect(calls[0].headers["End-User"]).toBe("u1");
    expect(calls[0].headers["X-Org-Id"]).toBeUndefined();
  });

  it("run creates a session and returns the last assistant text", async () => {
    const calls = mockFetch(
      jsonResponse({ id: "s1" }, 201),
      jsonResponse({ id: "m1" }, 201),
      sse([
        { id: "e1", type: "turn.started" },
        reply("e2", "draft"),
        reply("e3", "final answer"),
        { id: "e4", type: "turn.completed" },
      ]),
    );
    expect(await agent().run("hi")).toBe("final answer");
    expect(calls.map((c) => c.url)).toEqual([
      `${BASE}/sessions`,
      `${BASE}/sessions/s1/messages`,
      `${BASE}/sessions/s1/sse?after_sequence=0`,
    ]);
  });

  it("run in an existing session streams after the newest sequence", async () => {
    const calls = mockFetch(
      jsonResponse({
        data: [
          { id: "e1", type: "turn.completed", sequence: 1 },
          { id: "e2", type: "turn.completed", sequence: 2 },
        ],
      }),
      jsonResponse({ id: "m2" }, 201),
      sse([reply("e4", "new reply"), { id: "e5", type: "turn.completed" }]),
    );
    expect(await agent().run("again", "s9")).toBe("new reply");
    expect(calls.map((c) => c.url)).toEqual([
      `${BASE}/sessions/s9/events?after_sequence=0&limit=500`,
      `${BASE}/sessions/s9/messages`,
      `${BASE}/sessions/s9/sse?after_sequence=2`,
    ]);
  });

  it("run throws when the stream ends before the turn completes", async () => {
    vi.useFakeTimers();
    try {
      const calls = mockFetch(
        jsonResponse({ id: "s1" }, 201),
        jsonResponse({ id: "m1" }, 201),
        ...Array.from({ length: 10 }, () => () => sse([])),
      );
      const result = new AgentClient({ agentUrl: BASE, credential: "k" })
        .run("hi")
        .catch((e) => e);
      await vi.advanceTimersByTimeAsync(120_000);
      const error = await result;
      expect(error).toBeInstanceOf(EverrunsError);
      expect(error.message).toContain("before the turn completed");
      expect(calls.length).toBeGreaterThan(3);
    } finally {
      vi.useRealTimers();
    }
  });

  it("run raises on turn.failed", async () => {
    mockFetch(
      jsonResponse({ id: "s1" }, 201),
      jsonResponse({ id: "m1" }, 201),
      sse([
        { id: "e1", type: "turn.started" },
        { id: "e2", type: "turn.failed", data: { error: "model unavailable" } },
      ]),
    );
    const error = await agent()
      .run("hi")
      .catch((e) => e);
    expect(error).toBeInstanceOf(EverrunsError);
    expect(error.message).toContain("model unavailable");
  });
});
