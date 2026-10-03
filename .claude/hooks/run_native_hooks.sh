#!/bin/sh
# Copilot hook PATH resolves python3 to the mise install, which has no
# pydantic. native_hooks.py then exits 1, and Copilot fail-closes preToolUse.
# Prefer the repo venv. Also export its site-packages so a resolved symlink
# to the base interpreter still imports pydantic.
set -eu

ROOT="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$ROOT" ] || [ ! -f "$ROOT/src/dopemux/claude/native_hooks.py" ]; then
  ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
fi
export CLAUDE_PROJECT_DIR="$ROOT"

PY="$ROOT/.venv/bin/python"
if [ ! -x "$PY" ]; then
  PY=$(command -v python3 || true)
fi
if [ -z "${PY}" ]; then
  echo "native hooks: no python interpreter" >&2
  exit 1
fi

for site in "$ROOT"/.venv/lib/python*/site-packages; do
  if [ -d "$site" ]; then
    if [ -n "${PYTHONPATH:-}" ]; then
      PYTHONPATH="$site:$PYTHONPATH"
    else
      PYTHONPATH="$site"
    fi
    export PYTHONPATH
    break
  fi
done

exec "$PY" "$ROOT/src/dopemux/claude/native_hooks.py"
