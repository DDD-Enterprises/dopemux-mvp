#!/usr/bin/env bash
# Launch OpenCode against a free-tier Zen/OpenRouter model inside an isolated,
# public-origin/main-only worktree with a scrubbed environment and a hardened
# permission profile (.opencode/free-lane/config.jsonc).
#
# Rationale: free models may retain/train on submitted data, so this lane only
# ever sees content already public on origin/main — never unmerged branches,
# .env values, tokens, or local secrets. See .opencode/free-lane/config.jsonc
# for the permission policy this enforces.
#
# Usage:
#   scripts/opencode/free-lane.sh [-n NAME] [-m MODEL] [--force] [-- opencode-args...]
#
#   -n NAME    worktree/branch suffix (default: date-based timestamp)
#   -m MODEL   override the default model (opencode/laguna-s-2.1-free)
#   --force    skip the pre-flight secret scan (not recommended)
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
CONFIG_PATH="${REPO_ROOT}/.opencode/free-lane/config.jsonc"
MODEL=""
NAME=""
FORCE=0
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n) NAME="$2"; shift 2 ;;
    -m) MODEL="$2"; shift 2 ;;
    --force) FORCE=1; shift ;;
    --) shift; EXTRA_ARGS=("$@"); break ;;
    *) EXTRA_ARGS+=("$1"); shift ;;
  esac
done

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "error: missing $CONFIG_PATH" >&2
  exit 1
fi

if [[ -z "$NAME" ]]; then
  NAME="$(date +%Y%m%d_%H%M%S)"
fi

WORKTREE_DIR="${REPO_ROOT}/.worktrees/free-lane-${NAME}"
BRANCH="free-lane/${NAME}"

echo "==> Fetching origin/main"
git -C "$REPO_ROOT" fetch origin main --quiet

if [[ -d "$WORKTREE_DIR" ]]; then
  echo "==> Reusing existing worktree: $WORKTREE_DIR"
else
  echo "==> Creating worktree off origin/main: $WORKTREE_DIR ($BRANCH)"
  git -C "$REPO_ROOT" worktree add -b "$BRANCH" "$WORKTREE_DIR" origin/main
fi

if [[ "$FORCE" -eq 0 ]]; then
  echo "==> Pre-flight secret scan"
  SCANNED=0

  if command -v gitleaks >/dev/null 2>&1; then
    SCANNED=1
    # `dir` scans working-tree content only (fast) — what the model actually
    # sees. `detect` walks full git history by default, which is both slow
    # on this repo and irrelevant: secrets purged from history never reach
    # the free model.
    gitleaks dir "$WORKTREE_DIR" --no-banner || {
      echo "error: gitleaks found potential secrets — aborting. Use --force to override." >&2
      exit 1
    }
  fi

  if command -v trufflehog >/dev/null 2>&1; then
    SCANNED=1
    TRUFFLEHOG_OUT="$(trufflehog filesystem "$WORKTREE_DIR" --only-verified --fail 2>&1)" || {
      echo "$TRUFFLEHOG_OUT" >&2
      echo "error: trufflehog found verified secrets — aborting. Use --force to override." >&2
      exit 1
    }
  fi

  if [[ "$SCANNED" -eq 0 ]]; then
    echo "    (gitleaks/trufflehog not installed — falling back to a coarse grep; install one for a real scan)"
    if grep -RInE '(AKIA[0-9A-Z]{16}|ghp_[0-9A-Za-z]{36}|sk-[A-Za-z0-9]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' \
        --exclude-dir=.git "$WORKTREE_DIR" 2>/dev/null; then
      echo "error: possible secret pattern found above — aborting. Use --force to override." >&2
      exit 1
    fi
  fi
fi

MODEL="${MODEL:-opencode/laguna-s-2.1-free}"

echo "==> Launching OpenCode"
echo "    worktree: $WORKTREE_DIR"
echo "    branch:   $BRANCH"
echo "    model:    $MODEL"
echo "    config:   $CONFIG_PATH (share disabled, MCP/webfetch/websearch/push/commit denied)"
echo "    env:      scrubbed (only HOME/PATH/TERM/LANG preserved)"

cd "$WORKTREE_DIR"
exec env -i \
  HOME="$HOME" \
  PATH="$PATH" \
  TERM="$TERM" \
  LANG="${LANG:-en_US.UTF-8}" \
  OPENCODE_CONFIG="$CONFIG_PATH" \
  opencode -m "$MODEL" "${EXTRA_ARGS[@]}"
