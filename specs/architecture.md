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
