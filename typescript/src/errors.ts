/**
 * Error types for Everruns SDK.
 */

export class EverrunsError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "EverrunsError";
  }
}

export class ApiError extends EverrunsError {
  readonly statusCode: number;
  readonly body?: unknown;

  constructor(statusCode: number, message: string, body?: unknown) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
    this.body = body;
  }
}

export class AuthenticationError extends ApiError {
  constructor(message: string = "Authentication failed") {
    super(401, message);
    this.name = "AuthenticationError";
  }
}

export class NotFoundError extends ApiError {
  constructor(resource: string) {
    super(404, \`\${resource} not found\`);
    this.name = "NotFoundError";
  }
}

export class RateLimitError extends ApiError {
  readonly retryAfter?: number;

  constructor(retryAfter?: number) {
    super(429, "Rate limit exceeded");
    this.name = "RateLimitError";
    this.retryAfter = retryAfter;
  }
}

export class ConnectionError extends EverrunsError {
  constructor(message: string = "Connection failed") {
    super(message);
    this.name = "ConnectionError";
  }
}
