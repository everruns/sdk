---
name: adopt-upstream
description: Adopt upstream Everruns changes into the SDK. Use when asked to sync or pull changes from everruns/everruns, update the OpenAPI spec, analyze upstream API/docs changes, implement obvious SDK updates across Rust, Python, and TypeScript, propose ambiguous changes, and ship adopted changes.
user_invocable: true
---

# Adopt Upstream

Adopt current `everruns/everruns` API and docs changes into this SDK repo.

Requirements live in `specs/upstream-adoption.md`. Use that spec as authority. This skill describes expected outcomes, not a rigid workflow.

## Arguments

- `$ARGUMENTS` - Optional scope, date range, upstream PR/commit, feature area, or "ship" intent.

## Goals

### Current Base

Work from latest `origin/main`. In a worktree, fetch `origin/main`, create or use a branch based on it, and rebase before shipping.

### Upstream Understanding

Build enough evidence to know what changed upstream:

- refresh `openapi/openapi.json` from upstream
- inspect the OpenAPI diff
- inspect recent upstream commits/PRs/docs relevant to SDK behavior
- compare findings with local `specs/`, generated types, SDK clients, tests, docs, and cookbooks

Do not treat OpenAPI generation as the whole job. It only exposes part of the delta.

### Decision Quality

Classify each upstream delta:

- **Obvious**: SDK behavior follows existing patterns or explicit specs. Implement it.
- **Non-obvious**: semantics, naming, target parity, or user ergonomics need a decision. Propose it.

For non-obvious changes, produce a proposal with:

- recommended SDK surface
- spec updates needed
- Rust/Python/TypeScript impact
- tests and docs needed
- open questions or upstream gaps

### Complete Adoption

For obvious changes, make the SDK whole:

- update specs first or with code when requirements changed
- regenerate types after OpenAPI changes
- implement public client behavior in every target
- add/update positive and negative tests
- update user docs, code docs, and cookbooks when public behavior changed
- keep examples equivalent across Rust, Python, and TypeScript

No target should be left behind unless a spec explicitly excludes it.

### Shipment

If the user asked to ship, or the obvious change is ready to ship, use `/ship` after implementation. Shipping means merged to `main`; PR creation alone is not done.

If mixed obvious and non-obvious changes exist, ship the obvious safe subset only when it is independently coherent. Leave the rest as a proposal.

## Output

Report:

- upstream sources inspected
- OpenAPI/spec/code/docs changes made
- target parity status
- tests/checks run
- shipped PR/merge status, or proposal status with blockers
