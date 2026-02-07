import { describe, it, expect } from "vitest";
import { ApiKey } from "../src/auth.js";
import { Everruns } from "../src/client.js";
import type {
  AgentCapabilityConfig,
  CreateAgentRequest,
  CreateSessionRequest,
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

describe("CreateSessionRequest with capabilities", () => {
  it("should include capabilities in request body", () => {
    const request: CreateSessionRequest = {
      agentId: "agent_123",
      capabilities: [{ ref: "current_time" }],
    };

    const body = JSON.stringify({
      agent_id: request.agentId,
      capabilities: request.capabilities,
    });
    const parsed = JSON.parse(body);

    expect(parsed.capabilities).toHaveLength(1);
    expect(parsed.capabilities[0].ref).toBe("current_time");
  });

  it("should work without capabilities", () => {
    const request: CreateSessionRequest = {
      agentId: "agent_123",
    };
    expect(request.capabilities).toBeUndefined();
  });
});
