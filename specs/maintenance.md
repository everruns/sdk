# Maintenance

Periodic checklist to keep the SDK repo healthy. Run quarterly or when triggered by significant upstream changes.

## 1. Update Dependencies

Update all SDK dependencies to their latest versions, **including breaking/major version bumps**. This is a pre-1.0 SDK with no backward compatibility guarantees, so always upgrade to the newest release even if it contains breaking API changes. Fix any resulting compilation or test failures after upgrading.

### Rust

```bash
# Check outdated
cd rust && cargo outdated
# Update Cargo.toml versions, then:
cargo update && cargo build && cargo test
```

Key dependencies: `reqwest`, `eventsource-stream`, `tokio`, `serde`, `thiserror`, `secrecy`

### Python

```bash
# Check outdated
cd python && uv pip list --outdated
# Update version bounds in pyproject.toml, then:
uv sync --all-extras && uv run pytest
```

Key dependencies: `httpx`, `httpx-sse`, `pydantic`

### TypeScript

```bash
cd typescript && npm outdated
npm update && npm test
```

Key dependencies: `eventsource-parser`, `typescript`, `vitest`

### Cookbooks

Update cookbook dependency versions to match SDK changes:
- `cookbook/rust/Cargo.toml`
- `cookbook/python/pyproject.toml`
- `cookbook/typescript/package.json`

### Binary Size (Rust)

The Rust SDK links into other people's binaries, so its dependency graph is
their binary size. Check it whenever dependencies or features change.

#### Measure

[`cargo-bsize`](https://github.com/Boshen/cargo-bsize) reports size by section,
crate, function, and resolved feature list, and can rebuild under size levers to
measure them:

```bash
cargo install cargo-bsize
cd cookbook/rust && cargo bsize --bin dad-jokes         # full report
cargo bsize --bin dad-jokes --baseline path/to/old-bin  # what grew
cargo bsize --what-if --levers=opt-level=z,panic=abort  # measure build levers
```

The `Dependencies > Features` table is the one to read first: it lists every
crate's resolved feature set and who asked for it, which is where an SDK
dependency quietly costs a consumer.

Measure a *lean* consumer, not just the cookbook. The cookbook enables `tokio`
with `full` itself, so feature unification hides what the SDK alone pulls in.
Build a minimal crate that depends on the SDK plus `tokio` with only `rt` and
`macros`, `strip = true` in `[profile.release]`, and compare stripped binaries.

#### Rules for SDK dependencies

- No umbrella feature sets. `tokio` gets `["time"]`, not `["full"]`; a consumer
  enables what its own runtime needs.
- No facade crates. `futures-core` + `futures-util` (with
  `default-features = false`), not `futures`.
- `default-features = false` on `reqwest`, with only the features the SDK uses.
  `charset` in particular pulls in `encoding_rs` for a JSON-over-UTF-8 API.
- Anything a consumer might want to trade off goes behind a Cargo feature rather
  than being decided for them. TLS backend is the current example.
- Test both TLS backends before shipping a dependency change:
  `cargo check --lib` and
  `cargo check --lib --no-default-features --features native-tls`.

#### Reference measurements

Minimal client (create session + stream events), stripped release build,
x86_64-linux, as of reqwest 0.13:

| Configuration | Size |
|---|-----:|
| `rustls-tls` (default) | 6.5 MiB |
| `native-tls` | 3.0 MiB |
| `rustls-tls` + `opt-level = "z"` | ~4.6 MiB |
| `rustls-tls` + `panic = "abort"` | ~5.7 MiB |

Most of the default build is TLS: rustls plus its bundled aws-lc crypto (two
AES-GCM AVX-512 routines alone are 332 KiB each). `opt-level` and `panic` are
consumer profile settings, not something the SDK sets - document them, don't
force them.

### Verification

After all updates:

```bash
just pre-pr           # lint + test all SDKs
just check-cookbook    # verify cookbooks compile
just lint-cookbook     # lint cookbooks
```

## 2. Update OpenAPI Spec

Sync `openapi/openapi.json` from upstream:

```bash
curl -s "https://raw.githubusercontent.com/everruns/everruns/main/docs/api/openapi.json" > openapi/openapi.json
```

If spec changed:
1. Diff against current: `git diff openapi/openapi.json`
2. Regenerate public SDK models: `just generate`
3. Check for new endpoints not yet covered by SDKs
4. Update `specs/api-surface.md` if new endpoints added

## 3. Implement New API Features

Compare `openapi/openapi.json` endpoints against `specs/api-surface.md` and SDK implementations.

### Checklist

- [ ] All endpoints in OpenAPI spec listed in `specs/api-surface.md`
- [ ] All endpoints in `specs/api-surface.md` implemented in Rust SDK
- [ ] All endpoints in `specs/api-surface.md` implemented in Python SDK
- [ ] All endpoints in `specs/api-surface.md` implemented in TypeScript SDK
- [ ] New request/response types generated and integrated
- [ ] Tests added for new endpoints

## 4. Documentation

### docs.rs (Rust)

- [ ] All public types have doc comments
- [ ] All public methods have doc comments with examples
- [ ] Module-level docs explain purpose and usage
- [ ] `cargo doc --no-deps` produces clean output (no warnings)
- [ ] Examples in doc comments compile (`cargo test --doc`)

### Python

- [ ] All public classes/functions have docstrings
- [ ] Type hints on all public APIs

### TypeScript

- [ ] All public types/functions have JSDoc comments
- [ ] Examples in README are current

### READMEs

- [ ] `rust/README.md`: quick start is current, examples work
- [ ] `python/README.md`: quick start is current, examples work
- [ ] `typescript/README.md`: quick start is current, examples work
- [ ] Root `README.md`: links and overview are current

## 5. Spec-Code Alignment

Ensure specs match implementation and vice versa.

### Specs → Code

For each spec in `specs/`:
- [ ] `architecture.md`: structure matches actual file layout
- [ ] `api-surface.md`: endpoints match what SDKs implement
- [ ] `auth.md`: auth patterns match SDK auth modules
- [ ] `sse-streaming.md`: SSE behavior matches SDK streaming code
- [ ] `error-handling.md`: error types match SDK error modules
- [ ] `sdk-features.md`: features listed are implemented
- [ ] `cookbooks.md`: cookbook structure matches actual cookbooks
- [ ] `release-process.md`: release flow matches CI workflows

### Code → Specs

- [ ] Any SDK behavior not captured in specs is documented
- [ ] New features added since last review have spec coverage

## 6. Feature Parity Across Targets

All three SDKs (Rust, Python, TypeScript) must implement the same feature set.

### Comparison Matrix

| Feature | Rust | Python | TypeScript |
|---------|------|--------|------------|
| Client init (env + explicit) | | | |
| Agent CRUD | | | |
| Agent import/export | | | |
| Agent apply (upsert) | | | |
| Session CRUD | | | |
| Session cancel | | | |
| Message create/list | | | |
| Event list (polling) | | | |
| SSE streaming | | | |
| Capabilities list/get | | | |
| Image upload/get | | | |
| Session filesystem | | | |
| Error hierarchy | | | |
| Retry logic | | | |
| Timeout config | | | |
| Debug logging | | | |
| generate_agent_id | | | |
| Pagination support | | | |
| User-Agent header | | | |
| Resource cleanup | | | |

Fill with ✅ / ❌ / 🔧 (partial). Fix any ❌ items.

## 7. Cookbooks

### Runnable

Each cookbook must run successfully against a live server:

```bash
export EVERRUNS_API_KEY=...
export EVERRUNS_API_URL=http://localhost:9000

just run-cookbook-rust
just run-cookbook-python
just run-cookbook-typescript
```

### Compile Check

```bash
just check-cookbook    # all must pass
just lint-cookbook     # all must pass
```

### Cross-Target Coverage

All cookbooks must demonstrate the same scenarios across all languages. Compare:
- `cookbook/rust/src/main.rs`
- `cookbook/python/src/main.py`
- `cookbook/typescript/src/main.ts`

Ensure same features demonstrated. If one language has extra examples (e.g., `weather_tools`), add to other languages.

## 8. Public SDK Documentation

Verify https://github.com/everruns/everruns/blob/main/docs/features/sdk.mdx is current:

- [ ] Installation instructions match latest published versions
- [ ] Code examples work with current SDK API
- [ ] All SDK features are documented
- [ ] Links to SDK repos/docs are valid

If outdated, open a PR against `everruns/everruns` repo.

## 9. CI Health

- [ ] All CI workflows pass on main
- [ ] CI toolchain versions are current (Rust, Python, Node)
- [ ] CI caches are effective (not rebuilding from scratch)
- [ ] Dependabot or equivalent is configured (if desired)

## 10. Security

- [ ] No known vulnerabilities in dependencies (`cargo audit`, `pip audit`, `npm audit`)
- [ ] personal access tokens not committed in code or config
- [ ] `secrecy` crate usage correct in Rust SDK

## Running Maintenance

### Full Run

```bash
# 1. Branch
git checkout -b chore/maintenance-YYYY-MM

# 2. Dependencies
# Update each SDK per section 1

# 3. OpenAPI
# Sync per section 2

# 4. Run checks
just pre-pr
just check-cookbook
just lint-cookbook

# 5. Binary size (after any Rust dependency change)
cd rust && cargo bsize   # see "Binary Size (Rust)" above

# 6. Audit
cargo audit          # in rust/
uv run pip-audit     # in python/
npm audit            # in typescript/

# 7. Review each section above, fix issues

# 8. Commit and PR
git commit -m "chore: periodic maintenance"
```

### Quick Health Check

```bash
just pre-pr && just check-cookbook && just lint-cookbook
```
