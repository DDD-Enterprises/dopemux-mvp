#!/usr/bin/env bash
set -euo pipefail

RUN_ID="${RUN_ID:-run-$(date -u +'%Y%m%d-%H%M%S')}"
RUN_MODE="${RUN_MODE:-dry-run}"
TP_ID="${TP_ID:-UNKNOWN-TP}"
PREFLIGHT_SKIP_GIT_CLEAN="${PREFLIGHT_SKIP_GIT_CLEAN:-0}"
PREFLIGHT_LEDGER_PATH="${PREFLIGHT_LEDGER_PATH:-config/preflight/ledger.json}"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

FAILURES=()
SKIPPED=()

log() {
  printf '[preflight] %s\n' "$*"
}

record_failure() {
  FAILURES+=("$1")
}

record_skip() {
  SKIPPED+=("$1")
}

json_array() {
  if [[ "$#" -eq 0 ]]; then
    printf '[]'
  else
    printf '%s\n' "$@" | jq -R . | jq -s .
  fi
}

next_manifest_path() {
  local candidate=".runs/${1}.manifest.json"
  local idx=1
  while [[ -e "$candidate" ]]; do
    candidate=".runs/${1}.${idx}.manifest.json"
    idx=$((idx + 1))
  done
  printf '%s\n' "$candidate"
}

python_syntax_check() {
  python - <<'PY'
from pathlib import Path
import ast

paths = []
for base in ("src", "tests"):
    root = Path(base)
    if root.exists():
        paths.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)

for path in sorted(paths):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

print(f"syntax-ok files={len(paths)}")
PY
}

run_smoke_tests() {
  local pytest_args=(tests/unit/test_extract_local_smoke.py)
  if [[ -d tests/smoke ]]; then
    pytest_args=(tests/smoke)
  fi

  if command -v uv >/dev/null 2>&1; then
    uv run --frozen --extra test pytest -q --no-cov "${pytest_args[@]}" || return 1
    uv run --frozen --extra test python - <<'PY'
from pathlib import Path
import ast

paths = []
for base in ("src", "tests"):
    root = Path(base)
    if root.exists():
        paths.extend(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)

for path in sorted(paths):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

print(f"syntax-ok files={len(paths)}")
PY
    return $?
  fi

  if command -v python >/dev/null 2>&1; then
    python -m pytest -q --no-cov "${pytest_args[@]}" || return 1
    python_syntax_check
    return $?
  fi

  return 1
}

mkdir -p .runs
MANIFEST_PATH="$(next_manifest_path "$RUN_ID")"

log "check: run-mode"
case "$RUN_MODE" in
  dry-run|enforce)
    log "OK: run mode ${RUN_MODE}"
    ;;
  *)
    log "FAIL: invalid RUN_MODE=${RUN_MODE}"
    record_failure "run-mode"
    ;;
esac

log "check: jq-present"
if command -v jq >/dev/null 2>&1; then
  log "OK: jq present"
else
  log "FAIL: jq missing"
  record_failure "jq-present"
fi

log "check: git-clean"
if [[ "$PREFLIGHT_SKIP_GIT_CLEAN" == "1" ]]; then
  log "SKIP: git clean disabled for hook context"
  record_skip "git-clean"
elif [[ -n "$(git status --porcelain)" ]]; then
  log "FAIL: worktree not clean"
  record_failure "git-clean"
else
  log "OK: worktree clean"
fi

log "check: ledger-present"
if [[ -f "$PREFLIGHT_LEDGER_PATH" ]]; then
  log "OK: ledger present"
else
  log "FAIL: missing ${PREFLIGHT_LEDGER_PATH}"
  record_failure "ledger-present"
fi

log "check: ledger-json"
if [[ -f "$PREFLIGHT_LEDGER_PATH" ]]; then
  if jq -e . "$PREFLIGHT_LEDGER_PATH" >/dev/null; then
    log "OK: ledger JSON valid"
  else
    log "FAIL: ledger JSON invalid"
    record_failure "ledger-json"
  fi
else
  log "SKIP: ledger JSON validation requires ${PREFLIGHT_LEDGER_PATH}"
  record_skip "ledger-json"
fi

log "check: diff-whitespace"
if git diff --check && git diff --cached --check; then
  log "OK: diff whitespace clean"
else
  log "FAIL: diff whitespace check failed"
  record_failure "diff-whitespace"
fi

log "check: smoke-tests"
if run_smoke_tests; then
  log "OK: smoke checks passed"
else
  log "FAIL: smoke checks failed"
  record_failure "smoke-tests"
fi

STATUS="PASS"
if [[ "${#FAILURES[@]}" -gt 0 ]]; then
  STATUS="FAIL"
fi

if ! command -v jq >/dev/null 2>&1; then
  log "manifest not written: jq missing"
  if [[ "$RUN_MODE" == "enforce" ]]; then
    exit 1
  fi
  exit 0
fi

failures_json="$(json_array "${FAILURES[@]}")"
skipped_json="$(json_array "${SKIPPED[@]}")"
repo_url="$(git config --get remote.origin.url || true)"
repo_url="${repo_url:-UNKNOWN}"
branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
branch="${branch:-UNKNOWN}"
commit="$(git rev-parse HEAD 2>/dev/null || true)"
commit="${commit:-UNKNOWN}"

jq -n \
  --arg manifest_version "1.0" \
  --arg run_id "$RUN_ID" \
  --arg tp_id "$TP_ID" \
  --arg run_mode "$RUN_MODE" \
  --arg status "$STATUS" \
  --argjson failures "$failures_json" \
  --argjson skipped "$skipped_json" \
  --arg repo "$repo_url" \
  --arg branch "$branch" \
  --arg commit "$commit" \
  --arg manifest_path "$MANIFEST_PATH" \
  --arg timestamp_utc "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  '{
    manifest_version: $manifest_version,
    run_id: $run_id,
    tp_id: $tp_id,
    run_mode: $run_mode,
    status: $status,
    failures: $failures,
    skipped: $skipped,
    repo: $repo,
    branch: $branch,
    commit: $commit,
    manifest_path: $manifest_path,
    timestamp_utc: $timestamp_utc
  }' > "$MANIFEST_PATH"

log "manifest written: ${MANIFEST_PATH}"

if [[ "${#FAILURES[@]}" -gt 0 ]] && [[ "$RUN_MODE" == "enforce" ]]; then
  exit 1
fi
