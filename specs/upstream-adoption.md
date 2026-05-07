# Upstream Adoption

Requirements for adopting changes from `everruns/everruns` into this SDK repo.

## Definition

Upstream adoption means the SDKs are brought back into agreement with the current Everruns product API and public documentation.

The deliverable is either:

- shipped SDK changes for obvious upstream deltas, merged to `main`
- a concrete proposal for non-obvious deltas, with enough detail to implement next
- both, when an upstream update has mixed obvious and ambiguous parts

## Sources Of Truth

- Upstream OpenAPI: `everruns/everruns:docs/api/openapi.json`
- Local OpenAPI mirror: `openapi/openapi.json`
- Local SDK requirements: `specs/`
- Local generated API types: language-specific generated code
- Public SDK docs and examples: root and per-language READMEs, `docs/`, `cookbook/`
- Upstream public SDK docs when relevant: `everruns/everruns:docs/features/sdk.mdx`

`openapi/openapi.json` is mirrored from upstream. Do not hand-edit it except to replace it with the current upstream file.

## Classification

### Obvious Changes

Implement and ship upstream changes when the SDK behavior is mechanically clear:

- new request/response fields generated from OpenAPI
- enum/schema changes with no ergonomic API design question
- endpoint changes matching an existing SDK resource pattern
- validation rule changes already stated in OpenAPI or upstream docs
- documentation updates that follow implemented SDK behavior
- cookbook updates that keep scenarios aligned across languages

### Non-Obvious Changes

Propose before implementing when the right SDK behavior is not clear:

- new product concepts that need naming or resource boundaries
- endpoints that do not fit existing client structure
- streaming, pagination, auth, retry, or error semantics not specified enough to code
- cross-language ergonomics where idiomatic APIs would diverge
- OpenAPI behavior that conflicts with local specs or implementation
- upstream docs that describe behavior missing from OpenAPI

Proposals must include the recommended SDK surface, impacted specs, target-language impact, migration scope, tests needed, and open questions.

## Requirements

### OpenAPI Sync

- Fetch the current upstream OpenAPI file from `https://raw.githubusercontent.com/everruns/everruns/main/docs/api/openapi.json`.
- Compare it to the local mirror before generating or coding.
- Regenerate types after any OpenAPI change with `just generate`.
- Treat generated diffs as inputs to implementation, not as complete adoption.

### Upstream Delta Analysis

- Inspect upstream changes relevant to API behavior, SDK docs, examples, auth, streaming, errors, and endpoint semantics.
- Use upstream commits, PRs, docs, and OpenAPI diffs as evidence.
- Distinguish product/API changes from internal server-only changes.
- Record ambiguous or conflicting findings instead of guessing.

### Spec Alignment

- Update `specs/` when behavior, API coverage, SDK architecture, auth, streaming, errors, shipping, or release expectations change.
- `specs/api-surface.md` must match the endpoints intentionally exposed by all SDK targets.
- Specs are requirements. Code should satisfy them or propose spec changes before implementation.

### Target Parity

- Rust, Python, and TypeScript SDKs must expose the same feature set unless a spec explicitly says otherwise.
- New endpoints, models, validations, errors, docs, and examples must be considered for every target.
- A change is incomplete if one target implements a public feature that the others do not.

### Documentation

- Update user-facing docs when public API usage changes.
- Update code docs when public classes, methods, functions, types, or modules change.
- Keep README and cookbook examples runnable and aligned across targets.
- If upstream public SDK docs are stale, include an upstream-docs follow-up or PR plan.

### Verification

- Add or update tests for implemented behavior, including positive and negative paths.
- Run target-specific checks for changed languages.
- Run cross-target checks when API parity, generated types, cookbooks, or shared specs change.
- Obvious changes are not done until they pass the repo shipping requirements and are merged.

## Shipping

Obvious adopted changes must use the normal shipping requirements in `specs/shipping.md` and the `/ship` skill.

Do not merge:

- red CI
- unreviewed generated diffs
- partial target implementations
- spec/code disagreements
- guessed behavior for non-obvious upstream changes
