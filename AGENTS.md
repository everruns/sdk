## Coding-agent guidance

### Style

Telegraph. Drop filler/grammar. Min tokens.

### Critical Thinking

Fix root cause. Unsure: read more code; if stuck, ask w/ short options. Unrecognized changes: assume other agent; keep going. If causes issues, stop + ask.

### Principles

- Consistent API across all language SDKs
- Code testable, runnable locally
- Small, incremental PR-sized changes
- No backward compat needed (pre-1.0)

### Specs

`specs/` contains SDK specifications. New code should comply with these or propose changes.

- `specs/architecture.md` - SDK architecture, generation strategy, hybrid approach
- `specs/api-surface.md` - Covered API endpoints (agents, sessions, messages, events)
- `specs/auth.md` - EVERRUNS_API_KEY pattern, auth header format
- `specs/sse-streaming.md` - SSE reconnection, since_id, event types
- `specs/error-handling.md` - Error types per language, retry patterns
- `specs/release-process.md` - Versioning, changelog, publishing to registries

### OpenAPI

`openapi/openapi.json` - Source of truth synced from [everruns/everruns](https://github.com/everruns/everruns).

Source location: `docs/api/openapi.json` in everruns/everruns repo.

To update: `curl -s "https://raw.githubusercontent.com/everruns/everruns/main/docs/api/openapi.json" > openapi/openapi.json`

### GitHub API Access

Public repos (e.g., everruns/everruns) accessible via GitHub API without auth:
```bash
curl -s "https://api.github.com/repos/everruns/everruns/contents"
curl -s "https://raw.githubusercontent.com/everruns/everruns/main/path/to/file"
```

### Cloud Agent Start

```bash
just setup              # Install deps for all SDKs
just test               # Run all tests
just lint               # Run all linters
```

### Per-Language Dev

```bash
just test-rust          # cd rust && cargo test
just test-python        # cd python && uv run pytest
just test-typescript    # cd typescript && npm test
just generate           # Regenerate types from OpenAPI
```

### Rust

- Stable Rust, toolchain in `rust-toolchain.toml`
- `cargo fmt` and `cargo clippy -- -D warnings`

### Python

- Python 3.10+, managed via `uv`
- `ruff format` and `ruff check`

### TypeScript

- Node 22+, npm
- `prettier` and `oxlint`

### Pre-PR Checklist

1. Formatters and linters: `just lint`
2. Tests: `just test`
3. Rebase on main: `git fetch origin main && git rebase origin/main`
4. Smoke test new functionality
5. CI green before merge
6. Resolve all PR comments

### CI

- GitHub Actions. Check via `gh` tool.
- **NEVER merge when CI is red.** No exceptions.

### Commits

[Conventional Commits](https://www.conventionalcommits.org): `type(scope): description`

Types: feat, fix, docs, refactor, test, chore

Scopes: rust, python, typescript, docs, ci

### PRs

**REQUIRED:** Use `.github/pull_request_template.md`. Squash and Merge.

See `CONTRIBUTING.md` for details.
