# Changelog

All notable changes to the Everruns SDKs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-01-25

### Added

**All SDKs:**
- Initial release with core functionality
- `Everruns` client with `agents`, `sessions`, `messages`, `events` sub-clients
- `ApiKey` authentication with `EVERRUNS_API_KEY` environment variable support
- SSE streaming with automatic reconnection via `since_id`
- Event filtering with `exclude` parameter
- Typed error handling

**Rust SDK (everruns-sdk):**
- Async/await API with tokio
- `EventStream` implementing `futures::Stream`
- Secure API key handling with `secrecy` crate

**Python SDK (everruns-sdk):**
- Async client with httpx
- Pydantic models for request/response validation
- `EventStream` async iterator

**TypeScript SDK (@everruns/sdk):**
- Native fetch-based client
- TypeScript interfaces with full type safety
- `EventStream` async iterator with eventsource-parser
