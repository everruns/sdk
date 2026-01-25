# File Operations

Demonstrates session filesystem operations.

## Covered Scenarios

- **List files**: List files in session workspace
- **Read file**: Read file contents
- **Write file**: Write content to session
- **Multi-file**: Multiple file operations

## Run

```bash
export EVERRUNS_ORG=your-org
export EVERRUNS_API_KEY=your-key
# Optional: export EVERRUNS_API_URL=http://localhost:8080/api

cargo run -p file-operations
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sessions/{id}/fs` | List files |
| GET | `/sessions/{id}/fs/{path}` | Read file |
| PUT | `/sessions/{id}/fs/{path}` | Write file |

## Note

File operations work on the session's isolated filesystem. Files persist for the session lifetime but are cleaned up when the session is deleted.
