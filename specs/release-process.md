# Release Process

## Versioning

SDKs follow semver independently from Everruns server.

- Major: Breaking API changes
- Minor: New features, new endpoints
- Patch: Bug fixes, documentation

## Publishing

### Package Names

- Rust: `everruns-sdk` (crates.io)
- Python: `everruns-sdk` (PyPI)
- TypeScript: `@everruns/sdk` (npm)

### Release Flow

Release uses a **prep PR** pattern. When merged, CI automatically creates the
GitHub Release, tags the commit, and triggers publishing to all registries.

```
1. Create prep PR (version bump + changelog)
2. Review and merge to main (squash merge)
3. release.yml detects "chore(release): prepare vX.Y.Z" commit
4. Creates GitHub Release with tag vX.Y.Z
5. publish.yml publishes to crates.io, PyPI, and npm
```

### Prep PR Steps

When asked to release version X.Y.Z:

1. Update version in all manifests:
   - `rust/Cargo.toml`
   - `python/pyproject.toml`
   - `typescript/package.json`
2. Update `CHANGELOG.md` with new release section
3. Run verification: `just pre-pr` and `just publish-dry-run`
4. Commit with message: `chore(release): prepare vX.Y.Z`
5. Push to feature branch
6. Create PR titled: `chore(release): prepare vX.Y.Z`

The commit message `chore(release): prepare vX.Y.Z` is the sentinel that
triggers the automated release pipeline after merge to main.

### CI Workflows

**release.yml** — Triggered on push to `main`:

- Only runs when commit message starts with `chore(release): prepare v`
- Extracts version from commit message
- Verifies version matches all three SDK manifests
- Extracts release notes from CHANGELOG.md
- Creates GitHub Release with tag `vX.Y.Z`
- Triggers publish.yml

**publish.yml** — Triggered on GitHub Release published:

- Verifies tag version matches each SDK manifest
- Publishes Rust SDK to crates.io
- Publishes Python SDK to PyPI (OIDC Trusted Publishing)
- Publishes TypeScript SDK to npm

### Required Secrets

Configure in GitHub Settings → Secrets → Actions:

| Secret | Registry | How to obtain |
|--------|----------|---------------|
| `CARGO_REGISTRY_TOKEN` | crates.io | https://crates.io/settings/tokens |
| `NPM_TOKEN` | npm | https://www.npmjs.com/settings/~/tokens (Granular, with 2FA bypass) |

### Trusted Publishing (PyPI)

Python uses OIDC Trusted Publishing (no secret needed):

1. Go to https://pypi.org/manage/account/publishing/
2. Add trusted publisher:
   - Owner: `everruns`
   - Repository: `sdk`
   - Workflow: `publish.yml`

### npm Provenance

npm uses token auth + provenance attestation (`--provenance` flag).
Provenance links published packages to their source in GitHub Actions.

## Changelog Format

Each release section in `CHANGELOG.md` follows this structure:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Highlights

- 2-5 bullet points summarizing the most impactful changes
- Focus on user-facing features and improvements

### Breaking Changes

- **Short description**: Detailed explanation and migration steps.
  - Before: `old_api()`
  - After: `new_api()`

### What's Changed

* feat(scope): description ([#N](https://github.com/everruns/sdk/pull/N)) by @author
* fix(scope): description ([#N](https://github.com/everruns/sdk/pull/N)) by @author

**Full Changelog**: https://github.com/everruns/sdk/compare/vPREVIOUS...vX.Y.Z
```

### Changelog Rules

- `### Highlights` — 2-5 user-facing summaries (always included)
- `### Breaking Changes` — included for minor/major versions with migration guides
- `### What's Changed` — single flat list (not split into Added/Changed/Fixed)
- PRs listed in descending order by PR number (newest first)
- Format per line: `* type(scope): description ([#N](URL)) by @author`
- Ends with `**Full Changelog**: URL` compare link
