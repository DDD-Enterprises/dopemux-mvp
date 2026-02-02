#!/usr/bin/env bash
# Post-worktree setup hook for Dopemux ConPort wiring
# Usage: copy to .git/hooks/post-checkout (or run manually per worktree)

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

# Detect instance id: prefer env, fallback to branch name
INSTANCE_ID="${DOPEMUX_INSTANCE_ID:-}"
if [ -z "$INSTANCE_ID" ]; then
  if git rev-parse --abbrev-ref HEAD >/dev/null 2>&1; then
    INSTANCE_ID="$(git rev-parse --abbrev-ref HEAD | tr -cs '[:alnum:]_.-' '-')"
  else
    INSTANCE_ID="main"
  fi
fi

echo "🔧 Wiring ConPort for instance: $INSTANCE_ID"
python3 "$ROOT_DIR/scripts/wire_conport_project.py" --instance "$INSTANCE_ID"
echo "✅ Project ConPort wired (.claude/claude_config.json)"

