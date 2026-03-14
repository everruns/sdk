## Coding-agent guidance

Always make sure you are working on top of latest main from remote. Especially in worktrees: fetch `origin/main`, branch from it, rebase onto it before shipping.

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
- `specs/shipping.md` - Ship workflow phases, quality core, test coverage requirements

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

Fresh cloud environment? Install tools, then use Doppler for all secret-backed commands:

```bash
./scripts/init-cloud-env.sh   # Installs just, gh CLI, doppler
export PATH="$HOME/.cargo/bin:$PATH"  # Apply PATH in current shell
```

Use Doppler for GitHub CLI and any command needing secrets:

```bash
export GH_TOKEN=$(doppler secrets get GITHUB_TOKEN --plain)
gh auth status                # Verify GitHub access
just setup                    # Install deps for all SDKs
just test                     # Run all tests
just lint                     # Run all linters
```

`DOPPLER_TOKEN` is pre-set in cloud environments. All secrets (`GITHUB_TOKEN`, API keys) live in Doppler.

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

### Commands

`.claude/commands/` contains agent commands.

- `ship.md` - Full shipping workflow: test, verify artifacts, smoke test, push, PR, merge

### Shipping

"Ship" means: the change is **merged to main**. Not just "PR created" — merged. The full flow: implement with comprehensive test coverage (positive and negative paths), complete the Pre-PR Checklist, create PR, wait for CI green, squash-merge, confirm merge. Shipping is not done until the PR is merged.

Use the [`/ship`](.claude/commands/ship.md) command to execute the full shipping workflow. When asked to "ship", "fix and ship", or "ship it" — run all 8 phases through to merge. Do not stop at PR creation.

### Pre-PR Checklist

1. Pre-push checks: `just pre-push` (lint + commit attribution ~30s)
2. Formatters and linters: `just lint`
3. Tests: `just test`
4. Rebase on main: `git fetch origin main && git rebase origin/main`
5. Smoke test new functionality
6. CI green before merge
7. Resolve all PR comments: `gh pr view <num> --repo everruns/sdk --comments`

### CI

- GitHub Actions. Check via `gh` tool.
- **NEVER merge when CI is red.** No exceptions.

### Commits

[Conventional Commits](https://www.conventionalcommits.org): `type(scope): description`

Types: feat, fix, docs, refactor, test, chore

Scopes: rust, python, typescript, docs, ci

### Attribution

All commits **MUST** be attributed to the real human user, never to a coding agent or bot.

**Identity resolution** (implemented in `scripts/lib/common.sh`):

1. Check current `git config user.name` / `user.email`
2. **If both are present and represent a real human → use as-is. No env vars needed.**
3. Only if missing or agent-like (matches `claude|cursor|copilot|github-actions|bot|ai-agent|openai|anthropic|gpt`) → fall back to `GIT_USER_NAME` / `GIT_USER_EMAIL` env vars
4. If env vars also missing → **stop and ask the user** — do not commit with default/bot identity

`GIT_USER_NAME` and `GIT_USER_EMAIL` are **only required** when `git config user.name` / `user.email` are missing or resolve to an agent identity. If the existing git config already has a real human name and email, no environment variables are needed.

```bash
# Only needed when git config is missing or agent-like:
export GIT_USER_NAME="Your Name"
export GIT_USER_EMAIL="your@email.com"

# Or use the helper directly
source scripts/lib/common.sh
configure_commit_git_identity_if_needed
```

**Enforcement:**

- `just pre-push` validates commit identity + scans outgoing commits for agent authors
- `just test-git-identity` runs the identity helper test suite
- CI and pre-push checks will reject agent-authored commits

**Prohibited:**

- Do NOT set `GIT_AUTHOR_NAME`, `GIT_COMMITTER_NAME`, or `user.name` to any AI/bot identity (Claude, Cursor, Copilot, github-actions[bot])
- Do NOT use `Co-authored-by` trailers referencing AI tools
- Do NOT add "generated by", "authored by AI", or similar attribution in commit messages
- NEVER add links to Claude sessions in PR body or commits
- Merge commits must also use the real user as author — never use agent identities

### PRs

**REQUIRED:** Use `.github/pull_request_template.md`. Squash and Merge.

Cloud env PR creation (origin uses proxy, not GitHub directly):
```bash
# Must specify --repo and --head explicitly
gh pr create --repo everruns/sdk --head <branch-name> --title "..." --body "..."
```

See `CONTRIBUTING.md` for details.
