#!/usr/bin/env bash
# Pre-push checks: fast local validation to catch CI failures early (~30s).
# Runs formatting, linting, and commit attribution checks.
# Usage: just pre-push (or: bash scripts/lib/pre-push.sh)

source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

FAILED=0
fail() { echo "   ❌ $1"; FAILED=1; }
pass() { echo "   ✅ $1"; }

echo "🔒 Running pre-push checks..."
echo ""

STEP=0
TOTAL=4

# 1. Rust formatting + clippy
STEP=$((STEP + 1))
echo "$STEP/$TOTAL Rust formatting & linting"
if [ -d "$PROJECT_ROOT/rust" ]; then
  if (cd "$PROJECT_ROOT/rust" && cargo fmt --check 2>/dev/null); then
    pass "cargo fmt"
  else
    fail "cargo fmt — run: cd rust && cargo fmt"
  fi
  if (cd "$PROJECT_ROOT/rust" && cargo clippy -- -D warnings 2>/dev/null); then
    pass "clippy"
  else
    fail "clippy — run: cd rust && cargo clippy --fix --allow-dirty"
  fi
else
  echo "   ⏭️  skipped (no rust/ directory)"
fi

# 2. Python linting
STEP=$((STEP + 1))
echo "$STEP/$TOTAL Python linting"
if [ -d "$PROJECT_ROOT/python" ]; then
  if (cd "$PROJECT_ROOT/python" && uv run ruff check . 2>/dev/null && uv run ruff format --check . 2>/dev/null); then
    pass "ruff check + format"
  else
    fail "ruff — run: cd python && uv run ruff format . && uv run ruff check --fix ."
  fi
else
  echo "   ⏭️  skipped (no python/ directory)"
fi

# 3. TypeScript linting
STEP=$((STEP + 1))
echo "$STEP/$TOTAL TypeScript linting"
if [ -d "$PROJECT_ROOT/typescript/node_modules" ]; then
  if (cd "$PROJECT_ROOT/typescript" && npm run lint 2>/dev/null); then
    pass "TS lint"
  else
    fail "TS lint — run: cd typescript && npm run lint"
  fi
else
  echo "   ⏭️  skipped (no node_modules)"
fi

# 4. Commit author attribution check
STEP=$((STEP + 1))
echo "$STEP/$TOTAL Commit author attribution"
if ! resolve_commit_git_identity; then
  fail "commit identity invalid — fix git config or set GIT_USER_NAME/GIT_USER_EMAIL to a real user"
elif OFFENDING_COMMIT="$(find_agent_like_outgoing_commit)"; then
  IFS=$'\t' read -r OFFENDING_SHA OFFENDING_NAME OFFENDING_EMAIL <<< "$OFFENDING_COMMIT"
  fail "outgoing commit $OFFENDING_SHA has agent-like author '$OFFENDING_NAME <$OFFENDING_EMAIL>'"
else
  pass "commit author ($RESOLVED_GIT_AUTHOR_SOURCE): $RESOLVED_GIT_AUTHOR_NAME <$RESOLVED_GIT_AUTHOR_EMAIL>"
fi

echo ""
if [ $FAILED -ne 0 ]; then
  echo "❌ Pre-push checks failed. Fix issues above."
  echo "   Auto-fix formatting: just fmt"
  exit 1
fi
echo "✅ All pre-push checks passed."
