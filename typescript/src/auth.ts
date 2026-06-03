/**
 * Personal access token authentication for Everruns API.
 */
export class ApiKey {
  private readonly key: string;

  constructor(key: string) {
    if (!key) {
      throw new Error("personal access token cannot be empty");
    }
    this.key = key;
  }

  /**
   * Create an ApiKey from the EVERRUNS_API_KEY environment variable.
   * @throws Error if the environment variable is not set
   */
  static fromEnv(): ApiKey {
    const key = process.env.EVERRUNS_API_KEY;
    if (!key) {
      throw new Error(
        "EVERRUNS_API_KEY environment variable is not set. " +
          "Set it to your Everruns personal access token or pass the token explicitly.",
      );
    }
    return new ApiKey(key);
  }

  /**
   * Get the authorization header value.
   */
  toHeader(): string {
    return this.key;
  }
}
