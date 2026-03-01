# Ship

Run the full ship flow: verify quality, ensure test coverage, update artifacts, then push, create PR, and merge when CI is green.

This command implements the complete "Shipping" definition and Pre-PR Checklist from AGENTS.md. When the user says "ship" or "fix and ship", execute ALL phases below — not just the push/merge steps.

## Arguments

- `$ARGUMENTS` - Optional: description of what is being shipped (used for PR title/body context and to scope the quality checks)

## Instructions

### Phase 1: Pre-flight

1. Confirm we're NOT on `main` or `master`
2. Confirm there are no uncommitted changes (`git diff --quiet && git diff --cached --quiet`)
3. If uncommitted changes exist, stop and tell the user

### Phase 2: Test Coverage

Review the changes on this branch (use `git diff origin/main...HEAD` and `git log origin/main..HEAD`) and ensure comprehensive test coverage:

1. **Identify all changed code paths** — every new/modified function, module, class, endpoint
2. **Verify existing tests cover the changes** — run `just test` and check for failures
3. **Write missing tests** for any uncovered code paths:
   - **Positive tests**: happy path, valid inputs, expected behavior
   - **Negative tests**: invalid inputs, error conditions, boundary cases
   - **Per-language tests**: ensure changes in any SDK (rust, python, typescript) have corresponding tests
4. **Run all tests** to confirm green: `just test`
5. If any test fails, fix the code or test until green

### Phase 3: Artifact Updates

Review the changes and update project artifacts where applicable. Skip items that aren't affected.

1. **Specs** (`specs/`): if the change adds/modifies behavior covered by a spec, update the relevant spec file to stay in sync
2. **AGENTS.md**: if the change adds new specs, commands, or modifies development workflows — update the relevant section
3. **Documentation** (`docs/`): if the change affects user-facing APIs or features — update the relevant docs
4. **OpenAPI spec**: if API surface was modified, update `openapi/openapi.json`
5. **Cookbooks** (`cookbook/`): if APIs changed in a way that affects examples — update cookbook code

### Phase 4: Smoke Testing

Verify impacted functionality works end-to-end:

1. **Rust SDK**: `cd rust && cargo build && cargo test`
2. **Python SDK**: `cd python && uv sync --all-extras && uv run pytest`
3. **TypeScript SDK**: `cd typescript && npm ci && npm test`
4. **Cookbooks**: if SDK APIs changed, run `just check-cookbook` to verify examples still compile

Only test languages/cookbooks affected by the changes, not all.

If smoke testing reveals issues, fix them and loop back to Phase 2 (tests must still pass).

### Phase 5: Quality Gates

```bash
git fetch origin main && git rebase origin/main
```

- If rebase fails with conflicts, abort and tell the user to resolve manually

```bash
just lint
```

- If it fails, run `just fmt` to auto-fix, then retry once
- If still failing, stop and report

```bash
just pre-pr
```

- If it fails, stop and report the failures

### Phase 6: Push and PR

```bash
git push -u origin <current-branch>
```

Check for existing PR:

```bash
gh pr view --repo everruns/sdk --json url 2>/dev/null
```

If no PR exists, create one using the PR template (`.github/pull_request_template.md`):

- **Title**: conventional commit style from the branch commits
- **Body**: fill in the PR template sections (Summary, Test Plan, Checklist) based on the actual changes. Include what tests were added/verified.
- Use `gh pr create --repo everruns/sdk --head <branch-name>`

If a PR already exists, update it if needed and report its URL.

### Phase 7: Wait for CI and Merge

- Check CI status with `gh pr checks --repo everruns/sdk` (poll every 30s, up to 15 minutes)
- If CI is green, merge with `gh pr merge --repo everruns/sdk --squash --auto`
- If CI fails, report the failing checks and stop
- **NEVER** merge when CI is red

### Phase 8: Post-merge

After successful merge:

- Report the merged PR URL
- Done

## Notes

- This is the canonical shipping workflow for the SDK repo.
- Phases 2-4 (tests, artifacts, smoke testing) are the quality core — do NOT skip them.
- The `$ARGUMENTS` context helps scope which tests, specs, and smoke tests are relevant.
- For "fix and ship" requests: implement the fix first, then run `/ship` to validate and merge.
