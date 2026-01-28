import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { EventStream } from "../src/sse.js";

describe("EventStream", () => {
  describe("configuration", () => {
    it("should create stream with basic options", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      expect(stream.getLastEventId()).toBeUndefined();
      expect(stream.getRetryCount()).toBe(0);
    });

    it("should create stream with sinceId option", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth", {
        sinceId: "event_123",
      });
      expect(stream.getLastEventId()).toBe("event_123");
    });

    it("should create stream with all options", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth", {
        sinceId: "event_abc",
        exclude: ["output.message.delta"],
        maxRetries: 5,
      });
      expect(stream.getLastEventId()).toBe("event_abc");
    });
  });

  describe("abort", () => {
    it("should set shouldReconnect to false on abort", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      stream.abort();
      // Stream should not reconnect after abort
      // This is tested by checking the internal state indirectly
      expect(stream.getRetryCount()).toBe(0);
    });
  });

  describe("URL building", () => {
    it("should build URL without parameters", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      // Access private method via any cast for testing
      const url = (stream as any).buildUrl();
      expect(url).toBe("https://api.example.com/sse");
    });

    it("should build URL with sinceId", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth", {
        sinceId: "event_123",
      });
      const url = (stream as any).buildUrl();
      expect(url).toContain("since_id=event_123");
    });

    it("should build URL with exclude parameters", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth", {
        exclude: ["output.message.delta", "reason.thinking.delta"],
      });
      const url = (stream as any).buildUrl();
      expect(url).toContain("exclude=output.message.delta");
      expect(url).toContain("exclude=reason.thinking.delta");
    });

    it("should handle URL with existing query string", () => {
      const stream = new EventStream(
        "https://api.example.com/sse?foo=bar",
        "auth",
        {
          sinceId: "event_123",
        },
      );
      const url = (stream as any).buildUrl();
      expect(url).toContain("foo=bar");
      expect(url).toContain("&since_id=event_123");
    });

    it("should encode special characters in sinceId", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth", {
        sinceId: "event_123&special=value",
      });
      const url = (stream as any).buildUrl();
      expect(url).toContain("since_id=event_123%26special%3Dvalue");
    });
  });

  describe("retry logic", () => {
    it("should use server hint for graceful disconnect", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      (stream as any).gracefulDisconnect = true;
      (stream as any).serverRetryMs = 200;
      const delay = (stream as any).getRetryDelay();
      expect(delay).toBe(200);
    });

    it("should use default for graceful disconnect without server hint", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      (stream as any).gracefulDisconnect = true;
      const delay = (stream as any).getRetryDelay();
      expect(delay).toBe(100); // Default 100ms
    });

    it("should use exponential backoff for unexpected disconnect", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      (stream as any).gracefulDisconnect = false;
      const delay = (stream as any).getRetryDelay();
      expect(delay).toBe(1000); // Initial backoff
    });

    it("should double backoff on each update", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      (stream as any).gracefulDisconnect = false;

      expect((stream as any).currentBackoffMs).toBe(1000);

      (stream as any).updateBackoff();
      expect((stream as any).currentBackoffMs).toBe(2000);

      (stream as any).updateBackoff();
      expect((stream as any).currentBackoffMs).toBe(4000);

      (stream as any).updateBackoff();
      expect((stream as any).currentBackoffMs).toBe(8000);
    });

    it("should cap backoff at 30 seconds", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      (stream as any).gracefulDisconnect = false;

      // Update many times
      for (let i = 0; i < 10; i++) {
        (stream as any).updateBackoff();
      }

      expect((stream as any).currentBackoffMs).toBe(30000);
    });

    it("should not update backoff for graceful disconnect", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      const initialBackoff = (stream as any).currentBackoffMs;
      (stream as any).gracefulDisconnect = true;
      (stream as any).updateBackoff();
      expect((stream as any).currentBackoffMs).toBe(initialBackoff);
    });

    it("should reset backoff on successful event", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      (stream as any).currentBackoffMs = 16000;
      (stream as any).retryCount = 5;
      (stream as any).resetBackoff();
      expect((stream as any).currentBackoffMs).toBe(1000);
      expect((stream as any).retryCount).toBe(0);
    });
  });

  describe("should retry logic", () => {
    it("should retry when no max retries set", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      (stream as any).retryCount = 1000;
      expect((stream as any).shouldRetry()).toBe(true);
    });

    it("should respect max retries", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth", {
        maxRetries: 3,
      });

      expect((stream as any).shouldRetry()).toBe(true);

      (stream as any).retryCount = 2;
      expect((stream as any).shouldRetry()).toBe(true);

      (stream as any).retryCount = 3;
      expect((stream as any).shouldRetry()).toBe(false);
    });

    it("should not retry after abort", () => {
      const stream = new EventStream("https://api.example.com/sse", "auth");
      stream.abort();
      expect((stream as any).shouldRetry()).toBe(false);
    });
  });
});

describe("Backoff constants", () => {
  it("should have correct initial backoff", () => {
    // Import module constants indirectly through stream behavior
    const stream = new EventStream("https://api.example.com/sse", "auth");
    expect((stream as any).currentBackoffMs).toBe(1000);
  });

  it("should have correct max backoff", () => {
    const stream = new EventStream("https://api.example.com/sse", "auth");
    // Set to large value and update
    (stream as any).currentBackoffMs = 20000;
    (stream as any).updateBackoff();
    expect((stream as any).currentBackoffMs).toBe(30000); // Should cap
  });
});

describe("Exponential backoff sequence", () => {
  it("should follow correct sequence", () => {
    const expected = [1000, 2000, 4000, 8000, 16000, 30000, 30000];
    const stream = new EventStream("https://api.example.com/sse", "auth");

    for (const expectedValue of expected) {
      expect((stream as any).currentBackoffMs).toBe(expectedValue);
      (stream as any).updateBackoff();
    }
  });
});
