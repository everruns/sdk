/**
 * Server-Sent Events streaming with automatic reconnection.
 *
 * Implements robust SSE streaming with:
 * - Automatic reconnection on disconnect
 * - Server retry hints
 * - Graceful handling of `disconnecting` events
 * - Exponential backoff for unexpected disconnections
 * - Resume from last event ID via `since_id`
 */
import { createParser, type EventSourceMessage } from "eventsource-parser";
import { Event, StreamOptions } from "./models.js";
import { ConnectionError } from "./errors.js";

/** Maximum retry delay for exponential backoff */
const MAX_RETRY_MS = 30_000;
/** Initial retry delay for exponential backoff */
const INITIAL_BACKOFF_MS = 1000;
/** Read timeout for detecting stalled connections (2 minutes) */
const READ_TIMEOUT_MS = 120_000;

/**
 * Data from a disconnecting event.
 */
export interface DisconnectingData {
  /** Reason for disconnection (e.g., "connection_cycle") */
  reason: string;
  /** Suggested retry delay in milliseconds */
  retry_ms: number;
}

/**
 * Async iterator for SSE events with automatic reconnection.
 *
 * This stream handles:
 * - Graceful `disconnecting` events from the server
 * - Unexpected connection drops with exponential backoff
 * - Server retry hints
 * - Automatic resume using `since_id`
 *
 * @example
 * ```typescript
 * const stream = client.events.stream(sessionId);
 * for await (const event of stream) {
 *   console.log(event.type, event.data);
 * }
 * ```
 */
export class EventStream implements AsyncIterable<Event> {
  private readonly baseUrl: string;
  private readonly authHeader: string;
  private readonly options: StreamOptions;
  private lastEventId?: string;
  private abortController?: AbortController;
  private serverRetryMs?: number;
  private currentBackoffMs: number = INITIAL_BACKOFF_MS;
  private retryCount: number = 0;
  private shouldReconnect: boolean = true;
  private gracefulDisconnect: boolean = false;

  constructor(url: string, authHeader: string, options: StreamOptions = {}) {
    this.baseUrl = url;
    this.authHeader = authHeader;
    this.options = options;
    this.lastEventId = options.sinceId;
  }

  /**
   * Get the last received event ID (for resuming).
   */
  getLastEventId(): string | undefined {
    return this.lastEventId;
  }

  /**
   * Get the current retry count.
   */
  getRetryCount(): number {
    return this.retryCount;
  }

  /**
   * Abort the stream and prevent further reconnection attempts.
   */
  abort(): void {
    this.shouldReconnect = false;
    this.abortController?.abort();
  }

  private buildUrl(): string {
    let url = this.baseUrl;
    const params: string[] = [];

    if (this.lastEventId) {
      params.push(`since_id=${encodeURIComponent(this.lastEventId)}`);
    }

    if (this.options.exclude) {
      for (const e of this.options.exclude) {
        params.push(`exclude=${encodeURIComponent(e)}`);
      }
    }

    if (params.length > 0) {
      const separator = url.includes("?") ? "&" : "?";
      url += separator + params.join("&");
    }

    return url;
  }

  private getRetryDelay(): number {
    if (this.gracefulDisconnect) {
      // Use server hint for graceful disconnect, or short default
      return this.serverRetryMs ?? 100;
    } else {
      // Use exponential backoff for unexpected disconnects
      return this.currentBackoffMs;
    }
  }

  private updateBackoff(): void {
    if (!this.gracefulDisconnect) {
      this.currentBackoffMs = Math.min(this.currentBackoffMs * 2, MAX_RETRY_MS);
    }
  }

  private resetBackoff(): void {
    this.currentBackoffMs = INITIAL_BACKOFF_MS;
    this.retryCount = 0;
  }

  private shouldRetry(): boolean {
    if (!this.shouldReconnect) {
      return false;
    }
    if (this.options.maxRetries !== undefined) {
      return this.retryCount < this.options.maxRetries;
    }
    return true;
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async *[Symbol.asyncIterator](): AsyncGenerator<Event> {
    while (this.shouldReconnect) {
      this.abortController = new AbortController();

      try {
        for await (const event of this.connect()) {
          yield event;
        }

        // Stream ended normally - always retry to handle read timeout case
        if (this.shouldRetry()) {
          this.retryCount++;
          const delay = this.getRetryDelay();
          this.updateBackoff();
          console.debug(
            `Stream ended, reconnecting in ${delay}ms (attempt ${this.retryCount})`,
          );
          await this.sleep(delay);
          continue;
        }
        break;
      } catch (error) {
        if (error instanceof GracefulDisconnect) {
          // Server-initiated graceful disconnect
          this.serverRetryMs = error.retryMs;
          this.gracefulDisconnect = true;

          if (this.shouldRetry()) {
            this.retryCount++;
            const delay = this.getRetryDelay();
            console.debug(`Graceful reconnect in ${delay}ms`);
            await this.sleep(delay);
            this.gracefulDisconnect = false;
            continue;
          }
          break;
        }

        if (error instanceof Error && error.name === "AbortError") {
          // Clean shutdown
          break;
        }

        // Unexpected error - use exponential backoff
        this.gracefulDisconnect = false;

        if (this.shouldRetry()) {
          this.retryCount++;
          const delay = this.getRetryDelay();
          this.updateBackoff();
          console.debug(
            `Reconnecting after error in ${delay}ms (attempt ${this.retryCount}): ${error}`,
          );
          await this.sleep(delay);
          continue;
        }

        throw error;
      }
    }
  }

  private async *connect(): AsyncGenerator<Event> {
    const url = this.buildUrl();
    console.debug(`Connecting to SSE: ${url}`);

    // Create abort controller with timeout for stalled connections
    const timeoutId = setTimeout(() => {
      this.abortController?.abort();
    }, READ_TIMEOUT_MS);

    try {
      const response = await fetch(url, {
        headers: {
          Authorization: this.authHeader,
          Accept: "text/event-stream",
          "Cache-Control": "no-cache",
        },
        signal: this.abortController?.signal,
      });

      // Clear initial timeout, we'll reset it on each chunk
      clearTimeout(timeoutId);

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
      let readTimeoutId: ReturnType<typeof setTimeout> | undefined;

      const resetReadTimeout = () => {
        clearTimeout(readTimeoutId);
        readTimeoutId = setTimeout(() => {
          console.debug("SSE read timeout, triggering reconnect");
          reader.cancel();
        }, READ_TIMEOUT_MS);
      };

      const parser = createParser({
        onEvent: (event: EventSourceMessage) => {
          // Handle special lifecycle events
          if (event.event === "connected") {
            console.debug("SSE connected event received");
            return;
          }

          if (event.event === "disconnecting") {
            // Parse disconnecting data for retry hint
            try {
              const data = JSON.parse(event.data) as DisconnectingData;
              console.debug(
                `SSE disconnecting: reason=${data.reason}, retry_ms=${data.retry_ms}`,
              );
              throw new GracefulDisconnect(data.retry_ms);
            } catch (e) {
              if (e instanceof GracefulDisconnect) {
                throw e;
              }
              console.debug("SSE disconnecting event received (no data)");
              throw new GracefulDisconnect(100);
            }
          }

          if (event.event === "done") {
            return;
          }

          // Parse and yield regular events
          try {
            const data = JSON.parse(event.data) as Event;
            this.lastEventId = data.id;
            this.resetBackoff();
            eventQueue.push(data);
          } catch {
            // Skip malformed events
            console.trace(`Skipping malformed event: ${event.event}`);
          }
        },
      });

      resetReadTimeout();

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          // Reset timeout on each chunk received
          resetReadTimeout();

          const chunk = decoder.decode(value, { stream: true });
          parser.feed(chunk);

          // Yield any events that were parsed
          while (eventQueue.length > 0) {
            yield eventQueue.shift()!;
          }
        }
      } finally {
        clearTimeout(readTimeoutId);
      }
    } finally {
      clearTimeout(timeoutId);
    }
  }
}

/**
 * Internal error to signal graceful disconnect.
 */
class GracefulDisconnect extends Error {
  readonly retryMs: number;

  constructor(retryMs: number) {
    super(`Graceful disconnect, retry in ${retryMs}ms`);
    this.name = "GracefulDisconnect";
    this.retryMs = retryMs;
  }
}
