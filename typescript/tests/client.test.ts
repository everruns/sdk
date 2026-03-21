import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiKey } from "../src/auth.js";
import { Everruns } from "../src/client.js";
import {
  generateAgentId,
  generateHarnessId,
  extractToolCalls,
  toolResult,
  toolError,
  type AgentCapabilityConfig,
  type CapabilityInfo,
  type CreateAgentRequest,
  type CreateMessageRequest,
  type CreateSessionRequest,
  type ExternalActor,
  type FileInfo,
  type SessionFile,
  type FileStat,
  type GrepResult,
  type Message,
} from "../src/models.js";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("ApiKey", () => {
  it("should create from string", () => {
    const key = new ApiKey("evr_test_key");
    expect(key.toHeader()).toBe("evr_test_key");
  });

  it("should throw on empty key", () => {
    expect(() => new ApiKey("")).toThrow("API key cannot be empty");
  });
});

describe("Everruns", () => {
  it("should create client with explicit key", () => {
    const client = new Everruns({
      apiKey: "evr_test_key",
    });
    expect(client).toBeDefined();
    expect(client.agents).toBeDefined();
    expect(client.sessions).toBeDefined();
    expect(client.messages).toBeDefined();
    expect(client.events).toBeDefined();
    expect(client.capabilities).toBeDefined();
  });

  it("should create client with ApiKey instance", () => {
    const apiKey = new ApiKey("evr_test_key");
    const client = new Everruns({
      apiKey,
    });
    expect(client).toBeDefined();
  });

  it("should use custom base URL", () => {
    const client = new Everruns({
      apiKey: "evr_test_key",
      baseUrl: "https://custom.api.com",
    });
    // URLs include the /v1 prefix for API versioning
    expect(client.getStreamUrl("/test")).toBe("https://custom.api.com/v1/test");
  });

  it("should normalize base URL with trailing slash", () => {
    const client = new Everruns({
      apiKey: "evr_test_key",
      baseUrl: "https://custom.api.com/api/",
    });
    // Trailing slash is removed, /v1 prefix is added
    expect(client.getStreamUrl("/agents")).toBe(
      "https://custom.api.com/api/v1/agents",
    );
  });

  it("should create session with initial files", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({
        id: "session_123",
        harness_id: "harness_123",
        agent_id: "agent_123",
        status: "active",
        created_at: "2026-03-13T00:00:00Z",
        updated_at: "2026-03-13T00:00:00Z",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({
      apiKey: "evr_test_key",
    });

    await client.sessions.create({
      agentId: "agent_123",
      title: "Session with files",
      modelId: "model_123",
      initialFiles: [
        {
          path: "/workspace/README.md",
          content: "# hello\n",
          encoding: "text",
          isReadonly: true,
        },
      ],
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          agent_id: "agent_123",
          title: "Session with files",
          model_id: "model_123",
          initial_files: [
            {
              path: "/workspace/README.md",
              content: "# hello\n",
              encoding: "text",
              is_readonly: true,
            },
          ],
        }),
        headers: expect.objectContaining({
          Authorization: "evr_test_key",
          "Content-Type": "application/json",
        }),
      }),
    );
  });

  it("should create agent with initial files", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({
        id: "agent_123",
        name: "Starter Agent",
        system_prompt: "You keep files ready.",
        initial_files: [
          {
            path: "/workspace/README.md",
            content: "# starter\n",
            encoding: "text",
            is_readonly: true,
          },
        ],
        status: "active",
        created_at: "2026-03-13T00:00:00Z",
        updated_at: "2026-03-13T00:00:00Z",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({
      apiKey: "evr_test_key",
    });

    await client.agents.create({
      name: "Starter Agent",
      systemPrompt: "You keep files ready.",
      initialFiles: [
        {
          path: "/workspace/README.md",
          content: "# starter\n",
          encoding: "text",
          isReadonly: true,
        },
      ],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/agents",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          name: "Starter Agent",
          system_prompt: "You keep files ready.",
          initial_files: [
            {
              path: "/workspace/README.md",
              content: "# starter\n",
              encoding: "text",
              is_readonly: true,
            },
          ],
        }),
      }),
    );
  });

  it("should create session with locale", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({
        id: "session_456",
        harness_id: "harness_123",
        title: "Localized session",
        locale: "uk-UA",
        status: "active",
        created_at: "2026-03-13T00:00:00Z",
        updated_at: "2026-03-13T00:00:00Z",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({
      apiKey: "evr_test_key",
    });

    await client.sessions.create({
      title: "Localized session",
      locale: "uk-UA",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          title: "Localized session",
          locale: "uk-UA",
        }),
      }),
    );
  });
});

describe("AgentCapabilityConfig", () => {
  it("should create with just ref", () => {
    const config: AgentCapabilityConfig = { ref: "current_time" };
    expect(config.ref).toBe("current_time");
    expect(config.config).toBeUndefined();
  });

  it("should create with ref and config", () => {
    const config: AgentCapabilityConfig = {
      ref: "web_fetch",
      config: { timeout: 30 },
    };
    expect(config.ref).toBe("web_fetch");
    expect(config.config).toEqual({ timeout: 30 });
  });
});

describe("CreateAgentRequest with capabilities", () => {
  it("should include capabilities in request body", () => {
    const request: CreateAgentRequest = {
      name: "Test Agent",
      systemPrompt: "You are helpful.",
      capabilities: [
        { ref: "current_time" },
        { ref: "web_fetch", config: { timeout: 30 } },
      ],
    };

    const body = JSON.stringify({
      name: request.name,
      system_prompt: request.systemPrompt,
      capabilities: request.capabilities,
    });
    const parsed = JSON.parse(body);

    expect(parsed.capabilities).toHaveLength(2);
    expect(parsed.capabilities[0].ref).toBe("current_time");
    expect(parsed.capabilities[1].ref).toBe("web_fetch");
    expect(parsed.capabilities[1].config.timeout).toBe(30);
  });

  it("should work without capabilities", () => {
    const request: CreateAgentRequest = {
      name: "Test Agent",
      systemPrompt: "You are helpful.",
    };
    expect(request.capabilities).toBeUndefined();
  });
});

describe("CreateSessionRequest", () => {
  it("should include harness_id and capabilities in request body", () => {
    const request: CreateSessionRequest = {
      harnessId: "harness_abc123",
      agentId: "agent_123",
      capabilities: [{ ref: "current_time" }],
    };

    const body = JSON.stringify({
      harness_id: request.harnessId,
      agent_id: request.agentId,
      capabilities: request.capabilities,
    });
    const parsed = JSON.parse(body);

    expect(parsed.harness_id).toBe("harness_abc123");
    expect(parsed.agent_id).toBe("agent_123");
    expect(parsed.capabilities).toHaveLength(1);
    expect(parsed.capabilities[0].ref).toBe("current_time");
  });

  it("should work without agentId or harnessId (both optional)", () => {
    const request: CreateSessionRequest = {};
    expect(request.harnessId).toBeUndefined();
    expect(request.agentId).toBeUndefined();
    expect(request.capabilities).toBeUndefined();
  });

  it("should include tags", () => {
    const request: CreateSessionRequest = {
      harnessId: "harness_abc123",
      tags: ["debug", "urgent"],
    };
    expect(request.tags).toEqual(["debug", "urgent"]);
  });
});

describe("generateAgentId", () => {
  it("should return id with agent_ prefix", () => {
    const id = generateAgentId();
    expect(id.startsWith("agent_")).toBe(true);
  });

  it("should have 32 hex characters after prefix", () => {
    const id = generateAgentId();
    const hex = id.slice("agent_".length);
    expect(hex).toHaveLength(32);
    expect(/^[0-9a-f]{32}$/.test(hex)).toBe(true);
  });

  it("should generate unique ids", () => {
    const id1 = generateAgentId();
    const id2 = generateAgentId();
    expect(id1).not.toBe(id2);
  });
});

describe("generateHarnessId", () => {
  it("should return id with harness_ prefix", () => {
    const id = generateHarnessId();
    expect(id.startsWith("harness_")).toBe(true);
  });

  it("should have 32 hex characters after prefix", () => {
    const id = generateHarnessId();
    const hex = id.slice("harness_".length);
    expect(hex).toHaveLength(32);
    expect(/^[0-9a-f]{32}$/.test(hex)).toBe(true);
  });

  it("should generate unique ids", () => {
    const id1 = generateHarnessId();
    const id2 = generateHarnessId();
    expect(id1).not.toBe(id2);
  });
});

describe("EventsClient URL building", () => {
  it("should expand exclude as repeated query keys for events list", () => {
    // Verify the URLSearchParams approach used by EventsClient.list()
    // produces repeated keys, not comma-separated values
    const params = new URLSearchParams();
    params.set("since_id", "evt_001");
    for (const e of ["output.message.delta", "reason.thinking.delta"]) {
      params.append("exclude", e);
    }
    const query = params.toString();
    // Must produce repeated keys: exclude=a&exclude=b
    expect(query).toBe(
      "since_id=evt_001&exclude=output.message.delta&exclude=reason.thinking.delta",
    );
    expect(query).not.toContain("exclude=output.message.delta%2C");
  });

  it("should handle single exclude value", () => {
    const params = new URLSearchParams();
    for (const e of ["output.message.delta"]) {
      params.append("exclude", e);
    }
    expect(params.toString()).toBe("exclude=output.message.delta");
  });

  it("should produce empty query for no options", () => {
    const params = new URLSearchParams();
    expect(params.toString()).toBe("");
  });
});

describe("CreateAgentRequest with client-supplied ID", () => {
  it("should include id in request body", () => {
    const id = generateAgentId();
    const request: CreateAgentRequest = {
      id,
      name: "Test Agent",
      systemPrompt: "You are helpful.",
    };

    const body = JSON.stringify({
      id: request.id,
      name: request.name,
      system_prompt: request.systemPrompt,
    });
    const parsed = JSON.parse(body);

    expect(parsed.id).toBe(id);
    expect(parsed.name).toBe("Test Agent");
  });

  it("should work without id", () => {
    const request: CreateAgentRequest = {
      name: "Test Agent",
      systemPrompt: "You are helpful.",
    };
    expect(request.id).toBeUndefined();
  });
});

describe("ExternalActor", () => {
  it("should serialize with all fields", () => {
    const actor: ExternalActor = {
      actorId: "U12345",
      source: "slack",
      actorName: "Alice",
      metadata: { channel: "general" },
    };
    expect(actor.actorId).toBe("U12345");
    expect(actor.source).toBe("slack");
    expect(actor.actorName).toBe("Alice");
    expect(actor.metadata?.channel).toBe("general");
  });

  it("should work with minimal fields", () => {
    const actor: ExternalActor = {
      actorId: "bot1",
      source: "discord",
    };
    expect(actor.actorId).toBe("bot1");
    expect(actor.actorName).toBeUndefined();
    expect(actor.metadata).toBeUndefined();
  });
});

describe("Message with new fields", () => {
  it("should include external_actor and phase", () => {
    const msg: Message = {
      id: "msg_123",
      sessionId: "session_456",
      role: "user",
      content: [{ type: "text", text: "hello" }],
      createdAt: "2024-01-01T00:00:00Z",
      externalActor: { actorId: "U99", source: "slack" },
      phase: "Commentary",
    };
    expect(msg.externalActor?.actorId).toBe("U99");
    expect(msg.phase).toBe("Commentary");
  });

  it("should work without external_actor and phase", () => {
    const msg: Message = {
      id: "msg_123",
      sessionId: "session_456",
      role: "assistant",
      content: [{ type: "text", text: "hi" }],
      createdAt: "2024-01-01T00:00:00Z",
    };
    expect(msg.externalActor).toBeUndefined();
    expect(msg.phase).toBeUndefined();
  });
});

describe("CapabilityInfo with riskLevel", () => {
  it("should include riskLevel", () => {
    const info: CapabilityInfo = {
      id: "shell_exec",
      name: "Shell Exec",
      description: "Execute shell commands",
      status: "active",
      riskLevel: "high",
    };
    expect(info.riskLevel).toBe("high");
  });

  it("should work without riskLevel", () => {
    const info: CapabilityInfo = {
      id: "current_time",
      name: "Current Time",
      description: "Get current time",
      status: "active",
    };
    expect(info.riskLevel).toBeUndefined();
  });
});

describe("CreateMessageRequest with external_actor", () => {
  it("should include external_actor", () => {
    const req: CreateMessageRequest = {
      message: {
        role: "user",
        content: [{ type: "text", text: "hello" }],
      },
      externalActor: { actorId: "U12345", source: "slack" },
    };
    expect(req.externalActor?.actorId).toBe("U12345");
  });

  it("should work without external_actor", () => {
    const req: CreateMessageRequest = {
      message: {
        role: "user",
        content: [{ type: "text", text: "hello" }],
      },
    };
    expect(req.externalActor).toBeUndefined();
  });
});

describe("extractToolCalls", () => {
  it("should extract tool calls from event data", () => {
    const data = {
      message: {
        content: [
          { type: "text", text: "thinking..." },
          {
            type: "tool_call",
            id: "tc_1",
            name: "web_search",
            arguments: { query: "test" },
          },
          {
            type: "tool_call",
            id: "tc_2",
            name: "read_file",
            arguments: { path: "/tmp/test" },
          },
        ],
      },
    };

    const calls = extractToolCalls(data);
    expect(calls).toHaveLength(2);
    expect(calls[0].id).toBe("tc_1");
    expect(calls[0].name).toBe("web_search");
    expect(calls[0].arguments).toEqual({ query: "test" });
    expect(calls[1].id).toBe("tc_2");
    expect(calls[1].name).toBe("read_file");
  });

  it("should return empty array for no tool calls", () => {
    const data = {
      message: {
        content: [{ type: "text", text: "just text" }],
      },
    };
    expect(extractToolCalls(data)).toHaveLength(0);
  });

  it("should return empty array for missing message", () => {
    expect(extractToolCalls({})).toHaveLength(0);
  });
});

describe("toolResult and toolError helpers", () => {
  it("should create tool result content part", () => {
    const part = toolResult("tc_1", { answer: 42 });
    expect(part.type).toBe("tool_result");
    expect(part.tool_call_id).toBe("tc_1");
    expect(part.result).toEqual({ answer: 42 });
  });

  it("should create tool error content part", () => {
    const part = toolError("tc_1", "something failed");
    expect(part.type).toBe("tool_result");
    expect(part.tool_call_id).toBe("tc_1");
    expect(part.error).toBe("something failed");
  });
});

// --- Session Files Tests ---

const FILE_RESPONSE = {
  id: "file_001",
  session_id: "sess_123",
  path: "/workspace/hello.txt",
  name: "hello.txt",
  is_directory: false,
  is_readonly: false,
  size_bytes: 5,
  content: "hello",
  encoding: "text",
  created_at: "2026-03-20T00:00:00Z",
  updated_at: "2026-03-20T00:00:00Z",
};

describe("SessionFilesClient", () => {
  it("should have sessionFiles on client", () => {
    const client = new Everruns({ apiKey: "evr_test_key" });
    expect(client.sessionFiles).toBeDefined();
  });

  it("should list files", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        data: [FILE_RESPONSE],
        total: 1,
        offset: 0,
        limit: 100,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    const response = await client.sessionFiles.list("sess_123", {
      recursive: true,
    });

    expect(response.data).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs?recursive=true",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  it("should list files with path", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: [], total: 0, offset: 0, limit: 100 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    await client.sessionFiles.list("sess_123", { path: "/workspace" });

    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  it("should read a file", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => FILE_RESPONSE,
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    const file = await client.sessionFiles.read(
      "sess_123",
      "/workspace/hello.txt",
    );

    expect(file.content).toBe("hello");
    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/hello.txt",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  it("should create a file", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => FILE_RESPONSE,
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    await client.sessionFiles.create(
      "sess_123",
      "/workspace/new.txt",
      "hello",
      { encoding: "text" },
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/new.txt",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ content: "hello", encoding: "text" }),
      }),
    );
  });

  it("should create a directory", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => ({ ...FILE_RESPONSE, is_directory: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    await client.sessionFiles.createDir("sess_123", "/workspace/subdir");

    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/subdir",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ is_directory: true }),
      }),
    );
  });

  it("should update a file", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => FILE_RESPONSE,
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    await client.sessionFiles.update(
      "sess_123",
      "/workspace/hello.txt",
      "updated",
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/hello.txt",
      expect.objectContaining({
        method: "PUT",
        body: JSON.stringify({ content: "updated" }),
      }),
    );
  });

  it("should delete a file", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ deleted: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    const resp = await client.sessionFiles.delete(
      "sess_123",
      "/workspace/hello.txt",
    );

    expect(resp.deleted).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/hello.txt",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("should delete recursively", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ deleted: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    await client.sessionFiles.delete("sess_123", "/workspace/dir", {
      recursive: true,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/workspace/dir?recursive=true",
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("should move a file", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => FILE_RESPONSE,
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    await client.sessionFiles.moveFile(
      "sess_123",
      "/workspace/old.txt",
      "/workspace/new.txt",
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/_/move",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          src_path: "/workspace/old.txt",
          dst_path: "/workspace/new.txt",
        }),
      }),
    );
  });

  it("should copy a file", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => FILE_RESPONSE,
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    await client.sessionFiles.copyFile(
      "sess_123",
      "/workspace/original.txt",
      "/workspace/copy.txt",
    );

    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/_/copy",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          src_path: "/workspace/original.txt",
          dst_path: "/workspace/copy.txt",
        }),
      }),
    );
  });

  it("should grep files", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        data: [
          {
            path: "/workspace/main.rs",
            matches: [
              {
                path: "/workspace/main.rs",
                line_number: 10,
                line: "// TODO: fix this",
              },
            ],
          },
        ],
        total: 1,
        offset: 0,
        limit: 100,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    const results = await client.sessionFiles.grep("sess_123", "TODO");

    expect(results).toHaveLength(1);
    expect(results[0].matches).toHaveLength(1);
    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/_/grep",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ pattern: "TODO" }),
      }),
    );
  });

  it("should stat a file", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        path: "/workspace/hello.txt",
        name: "hello.txt",
        is_directory: false,
        is_readonly: false,
        size_bytes: 5,
        created_at: "2026-03-20T00:00:00Z",
        updated_at: "2026-03-20T00:00:00Z",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    const stat = await client.sessionFiles.stat(
      "sess_123",
      "/workspace/hello.txt",
    );

    expect(stat.name).toBe("hello.txt");
    expect(fetchMock).toHaveBeenCalledWith(
      "https://custom.example.com/api/v1/sessions/sess_123/fs/_/stat",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ path: "/workspace/hello.txt" }),
      }),
    );
  });

  it("should handle list response without pagination fields", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: [FILE_RESPONSE] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    const response = await client.sessionFiles.list("sess_123");

    expect(response.data).toHaveLength(1);
    expect(response.total).toBe(0);
    expect(response.offset).toBe(0);
    expect(response.limit).toBe(0);
  });

  it("should handle list response with pagination fields", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        data: [FILE_RESPONSE],
        total: 42,
        offset: 10,
        limit: 20,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const client = new Everruns({ apiKey: "evr_test_key" });
    const response = await client.sessionFiles.list("sess_123");

    expect(response.data).toHaveLength(1);
    expect(response.total).toBe(42);
    expect(response.offset).toBe(10);
    expect(response.limit).toBe(20);
  });
});
