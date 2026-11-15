#!/usr/bin/env sh
# Shared dispatcher for Dopemux native lifecycle hooks across Claude Code and Codex.
#
# Resolution order (first match wins):
#   1. This checkout's src/dopemux/claude/native_hooks.py, run with this checkout's
#      .venv/bin/python, else the main checkout's .venv/bin/python (linked worktrees
#      carry no .venv of their own).
#   2. An installed `dopemux` (PATH, then ~/.local/bin): `dopemux native-hooks run`.
#   3. Nothing usable: warn on stderr and exit 0 so a missing interpreter never
#      blocks the session.
# The checkout is resolved from the current directory (Claude Code runs hooks with
# cwd = the session checkout), and an inherited CLAUDE_PROJECT_DIR is preserved.
set -eu
TOP="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
COMMON="$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
MAIN="$TOP"; [ -n "$COMMON" ] && MAIN="$(cd "$TOP" && cd "$(dirname "$COMMON")" 2>/dev/null && pwd)" || true
export CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$TOP}"
HOOK="$TOP/src/dopemux/claude/native_hooks.py"
if [ -f "$HOOK" ]; then
  for PY in "$TOP/.venv/bin/python" "$MAIN/.venv/bin/python"; do
    [ -x "$PY" ] && exec "$PY" "$HOOK"
  done
fi
for BIN in "$(command -v dopemux 2>/dev/null || true)" "$HOME/.local/bin/dopemux"; do
  [ -n "$BIN" ] && [ -x "$BIN" ] && exec "$BIN" native-hooks run
done
echo "native hooks: no interpreter found; skipping" >&2
exit 0
