#!/usr/bin/env bash
# Portable hook for ConPort wiring after branch/worktree checkouts.

if ! command -v dopemux >/dev/null 2>&1; then
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
INSTANCE_ID="${DOPEMUX_INSTANCE_ID:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || basename "$REPO_ROOT")}"
if [ "$INSTANCE_ID" = "HEAD" ] || [ -z "$INSTANCE_ID" ]; then
  INSTANCE_ID="$(basename "$REPO_ROOT")"
fi

# Never block checkouts on wiring failures.
dopemux wire-conport --instance "$INSTANCE_ID" --project "$REPO_ROOT" >/dev/null 2>&1 || true
