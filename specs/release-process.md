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

### Release Steps

1. Update version in package manifest
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.1.0`
4. Push tag: `git push origin v0.1.0`
5. CI publishes to registries

### CI Workflow

Triggered on `v*` tags:

```yaml
on:
  push:
    tags:
      - "v*"
```

### Required Secrets

Configure in GitHub Settings → Secrets → Actions:

| Secret | Registry | How to obtain |
|--------|----------|---------------|
| `CARGO_REGISTRY_TOKEN` | crates.io | https://crates.io/settings/tokens |

### Trusted Publishing

Python and TypeScript use OIDC Trusted Publishing (no secrets needed):

**PyPI:**
1. Go to https://pypi.org/manage/account/publishing/
2. Add trusted publisher:
   - Owner: `everruns`
   - Repository: `sdk`
   - Workflow: `publish.yml`

**npm:**
1. Go to https://www.npmjs.com/package/@everruns/sdk/access
2. Configure publishing access → Require two-factor authentication or an automation or publish access token
3. Link to GitHub Actions:
   - Repository: `everruns/sdk`
   - Workflow: `publish.yml`

## Changelog Format

GitHub releases style with PR links:

```markdown
## [0.1.0] - 2026-01-29

### What's Changed

* feat(rust): add Rust SDK implementation ([#2](https://github.com/everruns/sdk/pull/2)) by @username
* fix: correct URL joining ([#18](https://github.com/everruns/sdk/pull/18)) by @username

**Full Changelog**: https://github.com/everruns/sdk/commits/v0.1.0
```
