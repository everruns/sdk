#!/usr/bin/env bash
# Common functions for dev scripts
# Adapted from everruns/everruns for consistent attribution enforcement.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"

# Load .env file if it exists
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Check if a command is available, exit with hint if not
require_command() {
  local cmd="$1"
  local hint="$2"

  if ! command -v "$cmd" &> /dev/null; then
    echo "❌ $cmd not installed. $hint"
    exit 1
  fi
}

# --- Git identity helpers ---

GIT_AGENT_IDENTITY_PATTERN="(claude|cursor|copilot|github-actions|bot|ai-agent|openai|anthropic|gpt)"

git_identity_looks_agent_like() {
  local value="${1:-}"

  if [ -z "$value" ]; then
    return 1
  fi

  printf '%s\n' "$value" | grep -iEq "$GIT_AGENT_IDENTITY_PATTERN"
}

# Resolve the commit identity to use.
# Prefer existing human git config. If git config is agent-like or incomplete,
# fall back to GIT_USER_NAME/GIT_USER_EMAIL and reject agent-like values there too.
resolve_commit_git_identity() {
  local current_name current_email
  current_name="$(git config user.name 2>/dev/null || true)"
  current_email="$(git config user.email 2>/dev/null || true)"

  RESOLVED_GIT_AUTHOR_NAME=""
  RESOLVED_GIT_AUTHOR_EMAIL=""
  RESOLVED_GIT_AUTHOR_SOURCE=""

  if [ -n "$current_name" ] && [ -n "$current_email" ] && \
    ! git_identity_looks_agent_like "$current_name" && \
    ! git_identity_looks_agent_like "$current_email"; then
    RESOLVED_GIT_AUTHOR_NAME="$current_name"
    RESOLVED_GIT_AUTHOR_EMAIL="$current_email"
    RESOLVED_GIT_AUTHOR_SOURCE="git"
  else
    if [ -z "${GIT_USER_NAME:-}" ] || [ -z "${GIT_USER_EMAIL:-}" ]; then
      echo "git commit identity is missing or agent-like; set GIT_USER_NAME and GIT_USER_EMAIL to a real user before committing" >&2
      return 1
    fi

    RESOLVED_GIT_AUTHOR_NAME="$GIT_USER_NAME"
    RESOLVED_GIT_AUTHOR_EMAIL="$GIT_USER_EMAIL"
    RESOLVED_GIT_AUTHOR_SOURCE="env"
  fi

  if git_identity_looks_agent_like "$RESOLVED_GIT_AUTHOR_NAME" || \
    git_identity_looks_agent_like "$RESOLVED_GIT_AUTHOR_EMAIL"; then
    echo "resolved git commit identity looks agent-like: '$RESOLVED_GIT_AUTHOR_NAME <$RESOLVED_GIT_AUTHOR_EMAIL>'" >&2
    return 1
  fi
}

configure_commit_git_identity_if_needed() {
  resolve_commit_git_identity || return 1
  git config user.name "$RESOLVED_GIT_AUTHOR_NAME"
  git config user.email "$RESOLVED_GIT_AUTHOR_EMAIL"
}

git_outgoing_commit_range() {
  if git rev-parse --verify -q '@{upstream}' >/dev/null 2>&1; then
    printf '%s\n' '@{upstream}..HEAD'
    return 0
  fi

  if git rev-parse --verify -q 'origin/main' >/dev/null 2>&1; then
    printf '%s\n' 'origin/main..HEAD'
    return 0
  fi

  return 1
}

find_agent_like_outgoing_commit() {
  local range sha name email tmpfile

  if ! range="$(git_outgoing_commit_range)"; then
    return 1
  fi

  tmpfile="$(mktemp)"
  trap "rm -f '$tmpfile'" RETURN

  git log --format='%H%x09%an%x09%ae' "$range" > "$tmpfile"

  while IFS=$'\t' read -r sha name email; do
    [ -n "$sha" ] || continue

    if git_identity_looks_agent_like "$name" || git_identity_looks_agent_like "$email"; then
      printf '%s\t%s\t%s\n' "$sha" "$name" "$email"
      return 0
    fi
  done < "$tmpfile"

  return 1
}
