# Changelog

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
