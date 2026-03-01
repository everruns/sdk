# Shipping

Defines the SDK "ship" workflow — the canonical process for delivering changes from branch to merged PR.

## Definition

"Ship" means: the change is **merged to main**. Not just "PR created" — merged. The full flow: implement with comprehensive test coverage (positive and negative paths), complete the Pre-PR Checklist, create PR, wait for CI green, squash-merge, confirm merge.

Shipping is not done until the PR is merged. This is NOT just "push and create PR". Shipping includes quality verification, artifact sync, smoke testing, AND the final merge.

## Phases

| Phase | Name | Purpose |
|-------|------|---------|
| 1 | Pre-flight | Branch validation, clean working tree |
| 2 | Test Coverage | Identify changed code paths, write/verify tests |
| 3 | Artifact Updates | Sync specs, docs, cookbooks, OpenAPI |
| 4 | Smoke Testing | End-to-end verification of affected SDKs |
| 5 | Code Simplification | Review for duplication, over-engineering, clarity |
| 6 | Security Review | OWASP Top 10, SDK-specific risks, fix vulnerabilities |
| 7 | Quality Gates | Rebase, lint, pre-pr checks |
| 8 | Push and PR | Push branch, create/update PR with template |
| 9 | CI and Merge | Poll CI, squash-merge when green |
| 10 | Post-merge | Report completion |

## Quality Core

Phases 2-6 are the quality core. They must NOT be skipped. The ship command enforces this by running all phases sequentially — there is no "fast ship" that bypasses tests, simplification, or security checks.

## Test Coverage Requirements

Every shipped change must have:

- **Positive tests** — happy path, valid inputs, expected behavior
- **Negative tests** — invalid inputs, error conditions, boundary cases
- **Per-language coverage** — changes in any SDK (Rust, Python, TypeScript) need corresponding tests in that language

## Code Simplification

Every shipped change must be reviewed for simplification opportunities:

- **Duplication** — repeated logic extracted into shared helpers
- **Over-engineering** — unnecessary abstractions, premature generalization, dead code removed
- **Clarity** — confusing names renamed, complex conditionals flattened
- **Consistency** — new code follows existing codebase patterns

Less code is better code. Simplify first, then re-run tests.

## Security Review

Every shipped change must be analyzed for security vulnerabilities:

- **OWASP Top 10** — injection, broken auth, sensitive data exposure, XXE, broken access control, misconfiguration, XSS, insecure dependencies, SSRF
- **SDK-specific risks** — API key redaction (secrecy crate / no log leaks), TLS verification enabled by default, graceful handling of malformed server responses

Fix vulnerabilities directly — do not just report them.

## Artifact Sync

When code changes affect behavior described in project artifacts, those artifacts must be updated as part of shipping:

- `specs/` — feature specifications
- `AGENTS.md` — development workflow docs
- `docs/` — user-facing documentation
- `openapi/openapi.json` — API surface definition
- `cookbook/` — example code

## Invocation

The `/ship` command (`.claude/commands/ship.md`) executes the full workflow. Usage:

```
/ship <description of what's being shipped>
```

The description scopes which tests, specs, and smoke tests are relevant.

For "fix and ship" requests: implement the fix first, then `/ship`.

## Constraints

- Never merge when CI is red
- Never skip the quality core (phases 2-4)
- Rebase conflicts require manual resolution — ship aborts
- Lint failures get one auto-fix attempt (`just fmt`), then abort
- PRs must use `.github/pull_request_template.md`
- PRs use squash-and-merge strategy
