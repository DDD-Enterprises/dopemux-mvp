#!/usr/bin/env bash
set -euo pipefail

EXPECTED_PROJECT="${1:-}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Must be inside a git repo
git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
  echo "Refusing: not inside a git work tree: $REPO_ROOT" >&2
  exit 2
}

# Repo identity must exist
if [[ ! -f "$REPO_ROOT/.repo_id" ]]; then
  echo "Refusing: missing .repo_id in repo root: $REPO_ROOT" >&2
  exit 2
fi

# Parse project name
PROJECT_LINE="$(grep "project=" "$REPO_ROOT/.repo_id" -m 1 || true)"
PROJECT_NAME="${PROJECT_LINE#project=}"

if [[ -z "${PROJECT_NAME:-}" ]]; then
  echo "Refusing: .repo_id missing 'project=' line" >&2
  exit 2
fi

# If caller expects a specific project, enforce it
if [[ -n "$EXPECTED_PROJECT" && "$PROJECT_NAME" != "$EXPECTED_PROJECT" ]]; then
  echo "Refusing: repo_id mismatch. expected=$EXPECTED_PROJECT got=$PROJECT_NAME root=$REPO_ROOT" >&2
  exit 2
fi

# Optional: refuse if dirty unless explicitly allowed
if [[ "${ALLOW_DIRTY:-0}" != "1" ]]; then
  if [[ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]]; then
    echo "Refusing: repo is dirty (set ALLOW_DIRTY=1 to override): $REPO_ROOT" >&2
    git -C "$REPO_ROOT" status --porcelain >&2
    exit 2
  fi
fi

echo "OK: repo_preflight project=$PROJECT_NAME root=$REPO_ROOT" >&2
