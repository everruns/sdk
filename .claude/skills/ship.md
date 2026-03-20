---
name: ship
description: Ship
user_invocable: true
---

# Ship

Run the full ship flow through to **merge on main**. Shipping is not done until the PR is merged.

This skill implements the complete "Shipping" definition and Pre-PR Checklist from AGENTS.md. When the user says "ship", "fix and ship", or "ship it", execute ALL 10 phases below — do NOT stop at PR creation. The final deliverable is a merged PR.

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

### Phase 5: Code Simplification

Review all changed code on this branch for opportunities to simplify:

1. **Read every changed file** — use `git diff origin/main...HEAD` to identify all modifications
2. **Check for duplication** — look for repeated logic that could be extracted into a shared helper
3. **Check for over-engineering** — unnecessary abstractions, premature generalization, unused parameters, dead code paths
4. **Check for clarity** — confusing names, overly complex conditionals, deeply nested logic that could be flattened
5. **Check for consistency** — ensure new code follows existing patterns and conventions in the codebase
6. **Simplify** — apply fixes directly. Less code is better code. If a helper is used once, inline it. If a name is unclear, rename it.
7. If changes were made, run `just test` to confirm nothing broke

### Phase 6: Security Review

Analyze all changed code for security vulnerabilities:

1. **Review every changed file** for OWASP Top 10 and common vulnerability patterns:
   - **Injection** — command injection, SQL injection, code injection in any string interpolation or shell calls
   - **Broken auth** — hardcoded secrets, credentials in logs, missing auth checks
   - **Sensitive data exposure** — API keys, tokens, or PII logged, leaked in errors, or stored insecurely
   - **XXE/deserialization** — unsafe parsing of XML, YAML, JSON, or pickle from untrusted sources
   - **Broken access control** — missing permission checks, IDOR, path traversal
   - **Security misconfiguration** — overly permissive defaults, debug modes, unnecessary features enabled
   - **XSS** — unsanitized user input in HTML/JS output
   - **Insecure dependencies** — known vulnerable versions, unnecessary dependencies
   - **SSRF** — user-controlled URLs used in server-side requests without validation
2. **Check for SDK-specific risks**:
   - API key handling: keys must use `secrecy`/redaction, never appear in logs or debug output
   - TLS verification: must not be disabled by default
   - Input validation at SDK boundaries: malformed server responses must not crash the SDK
3. **Fix any issues found** — do not just report them, fix them
4. If changes were made, run `just test` to confirm nothing broke

### Phase 7: Quality Gates

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

### Phase 8: Push and PR

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

### Phase 9: Wait for CI and Merge

- Check CI status with `gh pr checks --repo everruns/sdk` (poll every 30s, up to 15 minutes)
- If CI is green, merge with `gh pr merge --repo everruns/sdk --squash --auto`
- If CI fails, report the failing checks and stop
- **NEVER** merge when CI is red

### Phase 10: Post-merge

After successful merge:

- Report the merged PR URL
- Done

## Notes

- This is the canonical shipping workflow for the SDK repo.
- Phases 2-6 (tests, artifacts, smoke testing, simplification, security) are the quality core — do NOT skip them.
- The `$ARGUMENTS` context helps scope which tests, specs, and smoke tests are relevant.
- For "fix and ship" requests: implement the fix first, then run `/ship` to validate and merge.
