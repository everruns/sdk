# Error Handling

Demonstrates graceful handling of API errors.

## Covered Scenarios

- **Authentication errors**: Invalid or missing API key
- **Not found errors**: Accessing non-existent resources
- **Rate limiting**: Handling 429 responses with retry-after
- **Validation errors**: Invalid request parameters
- **Network errors**: Connection failures and timeouts

## Run

```bash
export EVERRUNS_ORG=your-org
export EVERRUNS_API_KEY=your-key
# Optional: export EVERRUNS_API_URL=http://localhost:8080/api

cargo run -p error-handling
```

## Key Patterns

```rust
match client.agents().get("nonexistent").await {
    Ok(agent) => println!("Found: {}", agent.name),
    Err(Error::NotFound { .. }) => println!("Agent not found"),
    Err(Error::Authentication { .. }) => println!("Invalid API key"),
    Err(Error::RateLimit { retry_after, .. }) => {
        println!("Rate limited, retry after {:?}", retry_after);
    }
    Err(e) => println!("Other error: {}", e),
}
```
