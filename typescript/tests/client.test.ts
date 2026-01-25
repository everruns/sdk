import { describe, it, expect } from "vitest";
import { ApiKey } from "../src/auth.js";
import { Everruns } from "../src/client.js";

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
      org: "test-org",
    });
    expect(client).toBeDefined();
    expect(client.agents).toBeDefined();
    expect(client.sessions).toBeDefined();
    expect(client.messages).toBeDefined();
    expect(client.events).toBeDefined();
  });

  it("should create client with ApiKey instance", () => {
    const apiKey = new ApiKey("evr_test_key");
    const client = new Everruns({
      apiKey,
      org: "test-org",
    });
    expect(client).toBeDefined();
  });

  it("should use custom base URL", () => {
    const client = new Everruns({
      apiKey: "evr_test_key",
      org: "test-org",
      baseUrl: "https://custom.api.com",
    });
    expect(client.getStreamUrl("/test")).toBe(
      "https://custom.api.com/orgs/test-org/test"
    );
  });
});
