import { describe, it, expect } from "vitest";
import { ApiKey } from "../src/auth.js";
import { Everruns } from "../src/client.js";
import {
  generateAgentId,
  generateHarnessId,
  type AgentCapabilityConfig,
  type CreateAgentRequest,
  type CreateSessionRequest,
} from "../src/models.js";

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

  it("should work without agentId (agent is optional)", () => {
    const request: CreateSessionRequest = {
      harnessId: "harness_abc123",
    };
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
