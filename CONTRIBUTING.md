# Contributing to Everruns SDK

We welcome contributions! Released under MIT license.

## What We're Looking For

- Bug fixes in existing SDKs
- Making SDKs more idiomatic for each language
- Documentation and cookbook improvements
- Test coverage improvements

**Note:** We're not adding SDKs for other languages at this time.
Feel free to create external SDKs and we may link to them.

## Setup

**All SDKs:** Install `just` command runner (optional but recommended)

### TypeScript

```bash
cd typescript && npm ci
npm test
npm run lint
```

### Python

```bash
cd python
uv sync --all-extras
uv run pytest
uv run ruff check .
```

### Rust

```bash
cd rust
cargo test
cargo clippy -- -D warnings
```

## Pull Request Process

1. Fork and clone the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Install dependencies for relevant SDK(s)
4. Make changes with tests (coverage ≥80%)
5. Run `just pre-pr` to verify all checks pass
6. Push and submit a PR using the template

## Testing

```bash
just test              # All SDKs
just test-rust         # Rust only
just test-python       # Python only
just test-typescript   # TypeScript only
just coverage          # Generate coverage reports
```

## Code Style

- **Rust:** `cargo fmt`, `cargo clippy`
- **Python:** `ruff format`, `ruff check`
- **TypeScript:** `prettier`, `eslint`

## Regenerating Types

When OpenAPI spec changes:

```bash
just generate          # Regenerate all SDK types
```
