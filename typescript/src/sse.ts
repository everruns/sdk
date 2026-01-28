/**
 * Server-Sent Events streaming for Everruns API.
 */
import { createParser, type EventSourceMessage } from "eventsource-parser";
import { Event } from "./models.js";
import { ConnectionError } from "./errors.js";

/**
 * Async iterator for SSE events with automatic reconnection.
 */
export class EventStream implements AsyncIterable<Event> {
  private readonly url: string;
  private readonly authHeader: string;
  private lastEventId?: string;
  private abortController?: AbortController;

  constructor(url: string, authHeader: string) {
    this.url = url;
    this.authHeader = authHeader;
  }

  /**
   * Abort the stream.
   */
  abort(): void {
    this.abortController?.abort();
  }

  async *[Symbol.asyncIterator](): AsyncGenerator<Event> {
    this.abortController = new AbortController();

    while (true) {
      try {
        const url = this.lastEventId
          ? `${this.url}${this.url.includes("?") ? "&" : "?"}since_id=${this.lastEventId}`
          : this.url;

        const response = await fetch(url, {
          headers: {
            Authorization: this.authHeader,
            Accept: "text/event-stream",
            "Cache-Control": "no-cache",
          },
          signal: this.abortController.signal,
        });

        if (!response.ok) {
          throw new ConnectionError(
            `Stream connection failed: ${response.status}`,
          );
        }

        if (!response.body) {
          throw new ConnectionError("No response body");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        const eventQueue: Event[] = [];
        let resolveNext: ((value: IteratorResult<Event>) => void) | null = null;

        const parser = createParser({
          onEvent: (event: EventSourceMessage) => {
            if (event.event === "done") {
              return;
            }
            try {
              const data = JSON.parse(event.data) as Event;
              this.lastEventId = data.id;
              if (resolveNext) {
                resolveNext({ value: data, done: false });
                resolveNext = null;
              } else {
                eventQueue.push(data);
              }
            } catch {
              // Skip malformed events
            }
          },
        });

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          parser.feed(chunk);

          while (eventQueue.length > 0) {
            yield eventQueue.shift()!;
          }
        }

        // Stream ended normally
        return;
      } catch (error) {
        if (error instanceof Error && error.name === "AbortError") {
          return;
        }
        // Reconnect after brief delay
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
    }
  }
}
