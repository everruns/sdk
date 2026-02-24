/**
 * Smoke tests for SSE reconnection behavior.
 *
 * Tests the actual EventStream reconnection loop with mocked fetch()
 * to verify:
 * - Bug 1: Graceful disconnects don't consume retry budget
 * - Bug 2: Connected event resets backoff after errors
 */
import { describe, it, expect, vi, afterEach } from "vitest";
import { EventStream } from "../src/sse.js";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

/**
 * Create a ReadableStream that yields SSE event chunks one at a time.
 * Each chunk is a complete SSE event (fields + blank line terminator).
 */
function createSseStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  let index = 0;
  return new ReadableStream({
    pull(controller) {
      if (index < chunks.length) {
        controller.enqueue(encoder.encode(chunks[index]));
        index++;
      } else {
        controller.close();
      }
    },
  });
}

function sseEvent(eventType: string, data: string): string {
  return `event: ${eventType}\ndata: ${data}\n\n`;
}

function makeEventJson(id: string, type: string): string {
  return JSON.stringify({
    id,
    type,
    data: {},
    createdAt: "2024-01-01T00:00:00Z",
  });
}

describe("SSE reconnection smoke tests", () => {
  it("graceful disconnect preserves retry budget", async () => {
    let callCount = 0;

    globalThis.fetch = vi.fn(async () => {
      callCount++;

      if (callCount === 1) {
        // First connection: connected + event + disconnecting
        return new Response(
          createSseStream([
            sseEvent("connected", "{}"),
            sseEvent(
              "output.message.started",
              makeEventJson("evt_001", "output.message.started"),
            ),
            sseEvent(
              "disconnecting",
              '{"reason":"connection_cycle","retry_ms":10}',
            ),
          ]),
          { status: 200, headers: { "Content-Type": "text/event-stream" } },
        );
      }

      // Second connection: connected + event
      return new Response(
        createSseStream([
          sseEvent("connected", "{}"),
          sseEvent(
            "output.message.completed",
            makeEventJson("evt_002", "output.message.completed"),
          ),
        ]),
        { status: 200, headers: { "Content-Type": "text/event-stream" } },
      );
    }) as typeof fetch;

    const stream = new EventStream("https://api.example.com/sse", "auth", {
      maxRetries: 3,
    });

    const events: unknown[] = [];
    for await (const event of stream) {
      events.push(event);
      if (events.length >= 2) {
        stream.abort();
      }
    }

    expect(events).toHaveLength(2);
    expect((events[0] as { id: string }).id).toBe("evt_001");
    expect((events[1] as { id: string }).id).toBe("evt_002");

    // Bug 1: Graceful disconnect did NOT consume retry budget
    expect(stream.getRetryCount()).toBe(0);

    // Reconnection happened
    expect(callCount).toBe(2);
  });

  it("connected event resets backoff after unexpected disconnect", async () => {
    let callCount = 0;

    globalThis.fetch = vi.fn(async () => {
      callCount++;

      if (callCount === 1) {
        // First connection: connected + event (then stream ends = unexpected)
        return new Response(
          createSseStream([
            sseEvent("connected", "{}"),
            sseEvent(
              "output.message.started",
              makeEventJson("evt_001", "output.message.started"),
            ),
          ]),
          { status: 200, headers: { "Content-Type": "text/event-stream" } },
        );
      }

      // Second connection: connected + event
      return new Response(
        createSseStream([
          sseEvent("connected", "{}"),
          sseEvent(
            "output.message.completed",
            makeEventJson("evt_002", "output.message.completed"),
          ),
        ]),
        { status: 200, headers: { "Content-Type": "text/event-stream" } },
      );
    }) as typeof fetch;

    const stream = new EventStream("https://api.example.com/sse", "auth", {
      maxRetries: 5,
    });

    const events: unknown[] = [];
    for await (const event of stream) {
      events.push(event);
      if (events.length >= 2) {
        stream.abort();
      }
    }

    expect(events).toHaveLength(2);
    expect((events[0] as { id: string }).id).toBe("evt_001");
    expect((events[1] as { id: string }).id).toBe("evt_002");

    // Bug 2: After successful reconnection with connected event,
    // backoff is reset by both the connected event and the data event.
    expect(stream.getRetryCount()).toBe(0);

    // Two connections were made
    expect(callCount).toBe(2);
  });

  it("survives multiple graceful disconnects without exhausting retries", async () => {
    let callCount = 0;

    globalThis.fetch = vi.fn(async () => {
      callCount++;

      const eventId = `evt_${String(callCount).padStart(3, "0")}`;
      const chunks = [
        sseEvent("connected", "{}"),
        sseEvent(
          "output.message.started",
          makeEventJson(eventId, "output.message.started"),
        ),
      ];

      // First 4 connections end with graceful disconnect
      if (callCount < 5) {
        chunks.push(
          sseEvent(
            "disconnecting",
            '{"reason":"connection_cycle","retry_ms":1}',
          ),
        );
      }

      return new Response(createSseStream(chunks), {
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
      });
    }) as typeof fetch;

    const stream = new EventStream("https://api.example.com/sse", "auth", {
      maxRetries: 2, // Only 2 retries for errors, but graceful shouldn't count
    });

    const events: unknown[] = [];
    for await (const event of stream) {
      events.push(event);
      if (events.length >= 5) {
        stream.abort();
      }
    }

    // 5 events from 5 connections, all via graceful disconnect
    expect(events).toHaveLength(5);

    // Bug 1: retry_count is still 0 despite 4 graceful disconnects
    expect(stream.getRetryCount()).toBe(0);
    expect(callCount).toBe(5);
  });
});
