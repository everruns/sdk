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

## Changelog Format

```markdown
## [0.1.0] - 2024-01-25

### Added
- Initial release
- Support for agents, sessions, messages
- SSE streaming with auto-reconnection

### Changed
- ...

### Fixed
- ...
```
