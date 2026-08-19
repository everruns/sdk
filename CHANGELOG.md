# Changelog

## [0.2.1] - 2026-08-19

### Highlights

- Rust SDK footprint trimmed for consumer binaries: leaner tokio/futures/reqwest feature sets, and TLS is now a Cargo feature (default `rustls-tls`, or `native-tls` for a much smaller binary).
- Rust SDK upgraded to reqwest 0.13.
- Dependency and security updates across all SDKs.
- Documentation polish: Everruns logo in the README, plainer punctuation in prose.

### What's Changed

* chore(rust): shrink SDK footprint in consumer binaries ([#110](https://github.com/everruns/sdk/pull/110)) by @chaliy
* chore(rust): upgrade to reqwest 0.13 ([#109](https://github.com/everruns/sdk/pull/109)) by @chaliy
* docs: replace em-dashes with plain punctuation in prose ([#108](https://github.com/everruns/sdk/pull/108)) by @chaliy
* docs: add Everruns logo ([#107](https://github.com/everruns/sdk/pull/107)) by @chaliy
* chore: update dependencies ([#106](https://github.com/everruns/sdk/pull/106)) by @chaliy
* chore: upgrade dependencies ([#105](https://github.com/everruns/sdk/pull/105)) by @chaliy

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.2.0...v0.2.1

## [0.2.0] - 2026-07-11

### Highlights

- Agents now own a harness: `harness_id` / `harness_name` on agent create and update across Rust, Python, and TypeScript SDKs (mutually exclusive; server defaults to `generic`). Adopts upstream EVE-686.
- Agent-first session creation: `agent_name` on session create (parallel to `agent_id`, mutually exclusive); a session created from an agent runs on the agent's harness.
- `parallel_tool_calls` on agent and session create/update; `harness_id` exposed on agent responses; `forked_from_session_id` / `forked_from_sequence` on session responses.
- Harnesses API across Rust, Python, and TypeScript SDKs: list/search/get/create/update/archive harnesses and list built-in examples — so callers can discover and manage the harness an agent or session references.
- Models API (read-only): list and get available models across all SDKs, for choosing an agent's `default_model_id`.
- Fixed (TypeScript): response objects for `Agent`, `Session`, `Harness`, `ModelWithProvider`, `CapabilityInfo`, `Budget`, `Connection`, and `Message` now expose their fields in snake_case matching the wire, so multi-word fields (e.g. `harness_id`, `system_prompt`, `created_at`, `provider_type`) resolve at runtime instead of being `undefined`. Rust and Python were already correct.
- Refreshed generated schemas from upstream OpenAPI.

### Breaking Changes

- **TypeScript response fields are now snake_case**: response objects (`Agent`, `Session`, `Harness`, `ModelWithProvider`, `CapabilityInfo`, `Budget`, `Connection`, `Message`, and related) now expose multi-word fields in snake_case, matching the wire. Previously these were typed camelCase but resolved to `undefined` at runtime. Update any code reading these fields.
  - Before: `agent.harnessId`, `session.systemPrompt`, `message.createdAt` (were `undefined`)
  - After: `agent.harness_id`, `session.system_prompt`, `message.created_at`
  - Rust and Python were already snake_case and are unaffected. TypeScript request models remain camelCase.

### What's Changed

* fix(typescript): snake_case response models ([#102](https://github.com/everruns/sdk/pull/102)) by @chaliy
* feat: add harnesses and models SDK APIs ([#101](https://github.com/everruns/sdk/pull/101)) by @chaliy
* feat: generate public SDK models from OpenAPI ([#100](https://github.com/everruns/sdk/pull/100)) by @chaliy
* feat: adopt agent harness ownership and agent-first sessions (EVE-686) ([#98](https://github.com/everruns/sdk/pull/98)) by @chaliy

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.10...v0.2.0

## [0.1.10] - 2026-06-19

### Highlights

- Workspaces and memories APIs across Rust, Python, and TypeScript SDKs
- Agent behavioral health-check endpoints (list, trigger, get) across all SDKs
- Agent analysis and guardrail helpers, plus session event-list filters
- Refreshed generated schemas, dependency/security updates, and documentation

### What's Changed

* chore(rust): add authors to crate metadata ([#96](https://github.com/everruns/sdk/pull/96)) by @chaliy
* ci: track everruns-server main HEAD again ([#95](https://github.com/everruns/sdk/pull/95)) by @chaliy
* docs(rust,python,typescript): fix invalid variable redeclaration in auth examples ([#94](https://github.com/everruns/sdk/pull/94)) by @chaliy
* docs(rust,python,typescript): document workspaces and memories APIs ([#93](https://github.com/everruns/sdk/pull/93)) by @chaliy
* feat: adopt agent health-checks, refresh deps ([#92](https://github.com/everruns/sdk/pull/92)) by @chaliy
* feat: adopt upstream workspace and memory APIs ([#91](https://github.com/everruns/sdk/pull/91)) by @chaliy
* feat: adopt upstream API refresh ([#90](https://github.com/everruns/sdk/pull/90)) by @chaliy
* fix(typescript): address code scanning alerts ([#89](https://github.com/everruns/sdk/pull/89)) by @chaliy

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.9...v0.1.10

## [0.1.9] - 2026-05-08

### Highlights

- Agent version APIs across Rust, Python, and TypeScript SDKs
- First-class org context support via `X-Org-Id` and `EVERRUNS_ORG_ID`
- Refreshed generated schemas, agent stats support, and maintenance updates

### What's Changed

* feat: adopt upstream agent versions ([#87](https://github.com/everruns/sdk/pull/87)) by @chaliy
* feat: add org context support across SDKs ([#86](https://github.com/everruns/sdk/pull/86)) by @chaliy
* chore(docs): add upstream adoption skill ([#85](https://github.com/everruns/sdk/pull/85)) by @chaliy
* chore(docs): make agent skills canonical ([#84](https://github.com/everruns/sdk/pull/84)) by @chaliy
* chore: periodic maintenance ([#83](https://github.com/everruns/sdk/pull/83)) by @chaliy

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.8...v0.1.9

## [0.1.8] - 2026-04-15

### Highlights

- Session export JSONL support across Rust, Python, and TypeScript SDKs
- `harness_name`, unique agent names, and upsert-by-name support across all SDKs
- Refreshed generated schemas, capability listing/import support, and maintenance updates

### What's Changed

* chore: periodic maintenance ([#80](https://github.com/everruns/sdk/pull/80)) by @chaliy
* feat(rust,python,typescript): unique agent names with upsert-by-name ([#79](https://github.com/everruns/sdk/pull/79)) by @chaliy
* feat(rust,python,typescript): support harness_name in session creation ([#78](https://github.com/everruns/sdk/pull/78)) by @chaliy
* feat(rust,python,typescript): add session export JSONL support ([#76](https://github.com/everruns/sdk/pull/76)) by @chaliy

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.7...v0.1.8

## [0.1.7] - 2026-04-05

### Highlights

- Budgets API support for managing resource budgets across all SDKs

### What's Changed

* feat(rust,python,typescript): add budgets API support ([#73](https://github.com/everruns/sdk/pull/73)) by @mchalyi

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.6...v0.1.7

## [0.1.6] - 2026-04-01

### Highlights

- Session secrets API for managing secrets within sessions
- Connections API for managing external service connections
- Dependency upgrades across all SDKs

### What's Changed

* feat(rust,python,typescript): add session secrets API ([#69](https://github.com/everruns/sdk/pull/69)) by @mchalyi
* feat(rust,python,typescript): add connections API ([#68](https://github.com/everruns/sdk/pull/68)) by @mchalyi
* chore(rust,python,typescript): upgrade dependencies across all SDKs ([#70](https://github.com/everruns/sdk/pull/70)) by @mchalyi

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.5...v0.1.6

## [0.1.5] - 2026-03-21

### Highlights

- Session filesystem client methods for file operations within sessions
- ListResponse pagination fields are now optional across all SDKs
- Git attribution helpers and pre-push checks for commit identity enforcement

### What's Changed

* fix(rust,python,typescript): make ListResponse pagination fields optional ([#64](https://github.com/everruns/sdk/pull/64)) by @mchalyi
* feat: add session filesystem client methods ([#62](https://github.com/everruns/sdk/pull/62)) by @mchalyi
* refactor: convert ship command to invocable skill ([#61](https://github.com/everruns/sdk/pull/61)) by @mchalyi
* feat(ci): add git attribution helpers and pre-push checks ([#59](https://github.com/everruns/sdk/pull/59)) by @mchalyi
* fix(ci): add --allow-dirty to cargo publish ([#58](https://github.com/everruns/sdk/pull/58)) by @mchalyi

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.4...v0.1.5

## [0.1.4] - 2026-03-14

### Highlights

- Session initial_files support for pre-populating session file systems
- Sync SDK with latest everruns API changes including optional harness_id
- Periodic maintenance with dependency updates and fixes

### What's Changed

* chore: periodic maintenance ([#56](https://github.com/everruns/sdk/pull/56))
* feat: add session initial_files support ([#54](https://github.com/everruns/sdk/pull/54))
* docs(docs): clarify latest-main workflow for worktrees ([#55](https://github.com/everruns/sdk/pull/55))
* fix(typescript): normalize repository.url in package.json ([#52](https://github.com/everruns/sdk/pull/52))
* fix(rust,python,typescript): make harness_id optional in session creation ([#53](https://github.com/everruns/sdk/pull/53))
* feat(rust,python,typescript): sync SDK with latest everruns API changes ([#50](https://github.com/everruns/sdk/pull/50))
* chore(docs): adopt everruns attribution standards ([#51](https://github.com/everruns/sdk/pull/51))
* feat(docs): adopt /ship command and shipping workflow ([#49](https://github.com/everruns/sdk/pull/49))

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.3...v0.1.4

## [0.1.3] - 2026-02-28

### Highlights

- Poll-level idle timeout for half-open SSE connections across all SDKs
- Harness support with optional agent parameter
- SSE read timeout and disconnect retry improvements

### What's Changed

* feat(rust,python,typescript): add harness support, make agent optional ([#37](https://github.com/everruns/sdk/pull/37))
* fix(typescript): use repeated keys for exclude param, add expansion tests ([#38](https://github.com/everruns/sdk/pull/38))
* refactor(rust): use structured enum for graceful disconnect signaling ([#39](https://github.com/everruns/sdk/pull/39))
* fix(rust,python,typescript): fix SSE disconnect retry, backoff reset, client reuse ([#40](https://github.com/everruns/sdk/pull/40))
* fix: add 60s SSE read timeout to detect stalled connections ([#42](https://github.com/everruns/sdk/pull/42))
* test: add read timeout tests and document decision rationale ([#43](https://github.com/everruns/sdk/pull/43))
* feat(rust,python,typescript): sync SDK with everruns/everruns#603 ([#45](https://github.com/everruns/sdk/pull/45))
* fix(rust): add poll-level idle timeout for half-open SSE connections ([#46](https://github.com/everruns/sdk/pull/46))
* fix(python,typescript): add poll-level idle timeout for half-open SSE connections ([#47](https://github.com/everruns/sdk/pull/47))

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.2...v0.1.3

## [0.1.2] - 2026-02-12

### Highlights

- Client tool call support across all SDKs
- Periodic maintenance: spec updates, dependency bumps, and fixes

### What's Changed

* feat(rust,python,typescript): add client tool call support ([#34](https://github.com/everruns/sdk/pull/34)) by @chaliy
* chore: periodic maintenance — spec, deps, fixes ([#35](https://github.com/everruns/sdk/pull/35)) by @chaliy

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.1...v0.1.2

## [0.1.1] - 2026-02-09

### Highlights

- Client-supplied agent IDs and `apply()` upsert support across all SDKs
- Agent capabilities, import/export functionality for Rust, Python, and TypeScript
- Rust output types are now serializable

### What's Changed

* feat(rust,python,typescript): client-supplied agent IDs and apply() upsert ([#31](https://github.com/everruns/sdk/pull/31)) by @chaliy
* chore(ci): adopt prep PR release process from bashkit ([#30](https://github.com/everruns/sdk/pull/30)) by @chaliy
* feat(rust,python,typescript): add capabilities, agent import/export ([#29](https://github.com/everruns/sdk/pull/29)) by @chaliy
* feat(rust): make all output types serializable ([#28](https://github.com/everruns/sdk/pull/28)) by @chaliy
* docs: use cargo add for Rust installation ([#27](https://github.com/everruns/sdk/pull/27)) by @chaliy
* fix(ci): add NPM_TOKEN for npm publish authentication ([#26](https://github.com/everruns/sdk/pull/26)) by @chaliy
* feat(ci): add workflow_dispatch trigger to publish workflow ([#25](https://github.com/everruns/sdk/pull/25)) by @chaliy
* feat(ci): use trusted publishing for npm and PyPI ([#24](https://github.com/everruns/sdk/pull/24)) by @chaliy

**Full Changelog**: https://github.com/everruns/sdk/compare/v0.1.0...v0.1.1

## [0.1.0] - 2026-01-29

### Highlights

- Initial release of Everruns SDKs for Rust, Python, and TypeScript
- SSE streaming with automatic reconnection support
- Cookbooks with working examples for all three languages

### What's Changed

* chore(ci): rename CRATES_IO_TOKEN secret to CARGO_REGISTRY_TOKEN ([#22](https://github.com/everruns/sdk/pull/22)) by @chaliy
* docs(rust): use cargo add for installation ([#21](https://github.com/everruns/sdk/pull/21)) by @chaliy
* feat(docs): enhance example output with more details ([#20](https://github.com/everruns/sdk/pull/20)) by @chaliy
* feat(cookbook): add Python and TypeScript cookbooks ([#19](https://github.com/everruns/sdk/pull/19)) by @chaliy
* fix: correct URL joining across all SDKs ([#18](https://github.com/everruns/sdk/pull/18)) by @chaliy
* feat(rust): add #[non_exhaustive] for future-proof structs ([#17](https://github.com/everruns/sdk/pull/17)) by @chaliy
* feat: implement SSE retry logic with automatic reconnection ([#16](https://github.com/everruns/sdk/pull/16)) by @chaliy
* docs: improve cloud env and PR checklist guidance ([#15](https://github.com/everruns/sdk/pull/15)) by @chaliy
* feat(docs): add cloud environment init script ([#14](https://github.com/everruns/sdk/pull/14)) by @chaliy
* feat: add api_key and api_url configuration to all SDKs ([#13](https://github.com/everruns/sdk/pull/13)) by @chaliy
* fix: simplify HTML responses in error messages ([#12](https://github.com/everruns/sdk/pull/12)) by @chaliy
* refactor: remove org parameter from API endpoints ([#11](https://github.com/everruns/sdk/pull/11)) by @chaliy
* docs(specs): add consolidated SDK features specification ([#10](https://github.com/everruns/sdk/pull/10)) by @chaliy
* docs: add comprehensive README with quick start examples ([#9](https://github.com/everruns/sdk/pull/9)) by @chaliy
* feat(ci): add job to run Rust cookbook with everruns-server ([#8](https://github.com/everruns/sdk/pull/8)) by @chaliy
* feat(cookbook): add Rust SDK cookbook with dad jokes example ([#7](https://github.com/everruns/sdk/pull/7)) by @chaliy
* fix(ci): resolve CI failures across all SDKs ([#6](https://github.com/everruns/sdk/pull/6)) by @chaliy
* chore: add publish prep files ([#5](https://github.com/everruns/sdk/pull/5)) by @chaliy
* feat(typescript): add TypeScript SDK implementation ([#4](https://github.com/everruns/sdk/pull/4)) by @chaliy
* feat(python): add Python SDK implementation ([#3](https://github.com/everruns/sdk/pull/3)) by @chaliy
* feat(rust): add Rust SDK implementation ([#2](https://github.com/everruns/sdk/pull/2)) by @chaliy

**Full Changelog**: https://github.com/everruns/sdk/commits/v0.1.0
