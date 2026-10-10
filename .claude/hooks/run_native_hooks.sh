#!/usr/bin/env sh
# Claude Code dispatcher for Dopemux native lifecycle hooks (Codex inlines its own
# copy in .codex/hooks.json; this script is not shared with it).
#
# Root: the hook cwd's git toplevel (or pwd). If that tree has no native_hooks.py,
# fall back to the CLAUDE_PROJECT_DIR the harness passed in.
# Interpreter, first executable wins: $ROOT/.venv, the main checkout's .venv (a
# linked worktree usually has none), then python3. site-packages is injected from
# the selected venv only.
# Failure policy: native_hooks.py exits 0 (allow) or 2 (deliberate block); both are
# passed through. Any other result (crash, import error, no interpreter) on
# PreToolUse is converted to exit 2 (fail closed) because Claude Code treats exit 1
# as non-blocking and would run the tool unenforced. Every other event keeps the
# non-blocking exit code. DOPEMUX_HOOKS_FAIL_OPEN=1 disables the conversion.
set -eu

INCOMING_DIR="${CLAUDE_PROJECT_DIR:-}"
HOOK_REL="src/dopemux/claude/native_hooks.py"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [ ! -d "$ROOT" ]; then
  ROOT="$(pwd)"
fi
if [ ! -f "$ROOT/$HOOK_REL" ] && [ -n "$INCOMING_DIR" ] && [ -f "$INCOMING_DIR/$HOOK_REL" ]; then
  ROOT="$INCOMING_DIR"
fi
export CLAUDE_PROJECT_DIR="$ROOT"

PY=""
VENV=""
if [ -x "$ROOT/.venv/bin/python" ]; then
  PY="$ROOT/.venv/bin/python"
  VENV="$ROOT/.venv"
else
  COMMON="$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  if [ -n "$COMMON" ]; then
    MAIN="$(dirname "$COMMON")"
    if [ -x "$MAIN/.venv/bin/python" ]; then
      PY="$MAIN/.venv/bin/python"
      VENV="$MAIN/.venv"
    fi
  fi
fi
if [ -z "$PY" ]; then
  PY="$(command -v python3 || true)"
fi

if [ -n "$VENV" ]; then
  for site in "$VENV"/lib/python*/site-packages; do
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
fi

PAYLOAD="$(cat)"

rc=0
if [ -z "$PY" ]; then
  echo "native hooks: no python interpreter" >&2
  rc=1
else
  printf '%s' "$PAYLOAD" | "$PY" "$ROOT/$HOOK_REL" || rc=$?
fi

if [ "$rc" -eq 0 ] || [ "$rc" -eq 2 ]; then
  exit "$rc"
fi

if [ "${DOPEMUX_HOOKS_FAIL_OPEN:-}" = "1" ]; then
  exit "$rc"
fi

event=""
if [ -n "$PY" ]; then
  event="$(printf '%s' "$PAYLOAD" | "$PY" -I -c \
    'import json, sys; print(json.load(sys.stdin).get("hook_event_name", ""))' \
    2>/dev/null || true)"
fi
if [ -z "$event" ]; then
  case "$PAYLOAD" in
    *'"hook_event_name":"PreToolUse"'* | *'"hook_event_name": "PreToolUse"'*) event="PreToolUse" ;;
  esac
fi

if [ "$event" = "PreToolUse" ]; then
  echo "Dopemux PreToolUse enforcement hook could not run (exit code $rc, interpreter: ${PY:-none}); this tool call was blocked (fail-closed). Repair by creating or repairing the repo .venv (for example run 'uv sync'). The operator override DOPEMUX_HOOKS_FAIL_OPEN=1, set in the environment that launches Claude Code, restores non-blocking behaviour." >&2
  exit 2
fi
exit "$rc"
