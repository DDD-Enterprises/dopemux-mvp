#!/usr/bin/env sh
# Shared dispatcher for Dopemux native lifecycle hooks across Claude Code and Codex.
# Resolves the repository root, prefers .venv/bin/python, injects site-packages,
# and executes native_hooks.py.
set -eu

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [ ! -d "$ROOT" ]; then
  ROOT="$(pwd)"
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
