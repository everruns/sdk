# SDK Architecture

## Overview

Everruns SDKs provide typed clients for the Everruns API across multiple languages.

## Generation Strategy: Hybrid Approach

| Layer | Approach | Rationale |
|-------|----------|-----------|
| Types/Models | Auto-generated from OpenAPI | 60+ schemas, keep in sync automatically |
| HTTP Client | Hand-written (thin wrapper) | Better ergonomics, resource sub-clients |
| SSE Streaming | Hand-written | OpenAPI generators don't handle SSE well |
| Auth Utilities | Hand-written | Multiple auth methods need consistent handling |

## Per-Language Tools

| Language | Type Generator | HTTP Library | SSE Library |
|----------|----------------|--------------|-------------|
| Rust | progenitor | reqwest | reqwest-eventsource |
| Python | datamodel-codegen | httpx | httpx-sse |
| TypeScript | openapi-typescript | fetch/undici | eventsource-parser |

## SDK Structure (per language)

```
<lang>/
├── src/
│   ├── generated/      # Auto-generated types
│   ├── client.{ext}    # Main client class
│   ├── auth.{ext}      # Authentication utilities
│   ├── sse.{ext}       # SSE streaming
│   └── errors.{ext}    # Error types
├── examples/
└── tests/
```

## URL Joining

All SDKs normalize base URLs and paths to ensure correct URL construction:

### The Problem

RFC 3986 URL joining has a common pitfall:
- Without trailing slash on base: `http://host/api` + `v1/agents` = `http://host/v1/agents` (loses `/api`)
- With trailing slash on base: `http://host/api/` + `v1/agents` = `http://host/api/v1/agents` (correct)

### The Solution

Each SDK normalizes URLs at client construction:

| SDK | Base URL | Path Format | Strategy |
|-----|----------|-------------|----------|
| Rust | Add trailing `/` | `v1/{path}` (relative) | `Url::join()` with normalized base |
| Python | Add trailing `/` | `v1/{path}` (relative) | httpx `base_url` param |
| TypeScript | Remove trailing `/` | `/v1/{path}` (absolute) | String concatenation |

### Implementation Pattern

```
// Rust/Python: ensure trailing slash, use relative paths
base = "http://host/api/"  // normalized
path = "v1/agents"         // no leading slash
result = join(base, path)  // "http://host/api/v1/agents"

// TypeScript: remove trailing slash, use absolute paths
base = "http://host/api"   // normalized (no trailing slash)
path = "/v1/agents"        // with leading slash
result = base + path       // "http://host/api/v1/agents"
```

### Testing Custom Base URLs

When testing with custom base URLs (e.g., `http://localhost:8080/api`):
- Rust/Python: Works regardless of trailing slash (normalized internally)
- TypeScript: Works regardless of trailing slash (normalized internally)
