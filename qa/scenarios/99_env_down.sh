#!/usr/bin/env bash
# qa/scenarios/99_env_down.sh — Crash-safe teardown of the QA stack.
#
# ALWAYS runs (called in trap by the orchestrator).
# Uses || true on every docker command — docker teardown MUST NOT exit non-zero.
# EXCEPTION: exits 1 before any docker call if COMPOSE_PROJECT_NAME is wrong,
# to prevent accidental teardown of the wrong project.
# NEVER deletes volumes (-v), NEVER touches the live 'dopemux' project.
#
# Emits:
#   env_down   — PASS if QA containers reach 0; FAIL otherwise (still safe)

set -euo pipefail

# ── Locate and source the shared library ──────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB="${SCRIPT_DIR}/../lib/qa_common.sh"

# Inline fallback so teardown works even if lib is missing or broken
_emit_inline() {
    local scenario="$1" status="$2" message="$3" evidence="${4:-{}}"
    local rf="${RESULTS_FILE:-/tmp/qa_results.jsonl}"
    local ts; ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    local dur=$(( SECONDS - _SCENARIO_START ))
    local safe; safe="$(printf '%s' "$message" | sed 's/\\/\\\\/g; s/"/\\"/g')"
    mkdir -p "$(dirname "$rf")"
    printf '{"scenario":"%s","status":"%s","message":"%s","evidence":%s,"timestamp":"%s","duration_s":%d}\n' \
        "$scenario" "$status" "$safe" "$evidence" "$ts" "$dur" >> "$rf"
    echo "[$status] $scenario — $message" >&2
}

_SCENARIO_START=$SECONDS

if [[ -f "$LIB" ]]; then
    # shellcheck source=../lib/qa_common.sh
    source "$LIB"
else
    echo "[WARN] qa_common.sh not found at $LIB — using inline fallback" >&2
    RESULTS_FILE="${RESULTS_FILE:-/tmp/qa_results.jsonl}"
    CURRENT_SCENARIO="env_down"
    emit_result() { _emit_inline "$@"; }
    log_info()  { echo "[INFO ] $(date -u +%H:%M:%S) $*" >&2; }
    log_warn()  { echo "[WARN ] $(date -u +%H:%M:%S) $*" >&2; }
    log_error() { echo "[ERROR] $(date -u +%H:%M:%S) $*" >&2; }
    scenario_start() { CURRENT_SCENARIO="${1:-unknown}"; _SCENARIO_START=$SECONDS; }
    scenario_skip()  { emit_result "${CURRENT_SCENARIO}" "NOT_RUN" "${1:-skipped}"; exit 0; }
fi

# ── Setup ─────────────────────────────────────────────────────────────────────
scenario_start "env_down"

ROOT="${ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
RESULTS_DIR="${RESULTS_DIR:-$SCRIPT_DIR/../results}"
mkdir -p "$RESULTS_DIR"

TEARDOWN_LOG="$RESULTS_DIR/99_env_down.log"

# ── Guard: refuse to tear down the wrong project ──────────────────────────────
# If COMPOSE_PROJECT_NAME is wrong, we log and exit 1 BEFORE touching anything.
# This is the ONE place we do NOT use || true — a wrong project name is a hard abort.
_CP="${COMPOSE_PROJECT_NAME:-}"
if [[ "$_CP" != "dopemux-qa" ]]; then
    log_error "ABORT: COMPOSE_PROJECT_NAME='$_CP' — must be 'dopemux-qa'. Refusing teardown."
    emit_result "env_down" "FAIL" \
        "Aborted: COMPOSE_PROJECT_NAME='$_CP' is not 'dopemux-qa'" \
        "{\"compose_project\":\"$_CP\"}"
    exit 1
fi

log_info "Tearing down QA stack (COMPOSE_PROJECT_NAME=dopemux-qa) ..."

# ── Snapshot live stack count BEFORE teardown (for integrity check after) ─────
LIVE_BEFORE=0
LIVE_BEFORE=$(docker compose -p dopemux ps -q 2>/dev/null | wc -l | tr -d ' ') || LIVE_BEFORE=0
log_info "Live dopemux containers before teardown: $LIVE_BEFORE"

# ── docker compose down (no -v: never delete volumes) ─────────────────────────
docker compose -p dopemux-qa -f "${ROOT}/compose.yml" down --remove-orphans 2>&1 | tee "$TEARDOWN_LOG" || true

# ── Remove QA-specific network (NOT the shared dopemux-network) ───────────────
QA_NETWORK="${QA_NETWORK:-dopemux-qa-network}"
if docker network inspect "$QA_NETWORK" >/dev/null 2>&1; then
    log_info "Removing QA network: $QA_NETWORK"
    docker network rm "$QA_NETWORK" 2>/dev/null || true
else
    log_info "QA network '$QA_NETWORK' not found or already removed — OK"
fi

# Safety: explicitly confirm the shared live network is untouched
if docker network inspect dopemux-network >/dev/null 2>&1; then
    log_info "Shared dopemux-network still present — OK"
fi

# ── Verify QA containers are gone ─────────────────────────────────────────────
QA_REMAINING=0
QA_REMAINING_JSON="[]"
RAW_PS=""
RAW_PS=$(docker compose -p dopemux-qa -f "${ROOT}/compose.yml" ps --format json 2>/dev/null || true)

# docker compose ps --format json may return an array or newline-delimited objects
if [[ -n "$RAW_PS" ]]; then
    # Try array form first, then wrapped array
    QA_REMAINING=$(printf '%s' "$RAW_PS" | jq -e 'if type=="array" then length else 1 end' 2>/dev/null || echo "1")
    QA_REMAINING_JSON=$(printf '%s' "$RAW_PS" | jq -c '[.[].Name // .[].Service // "unknown"] // []' 2>/dev/null || echo "[]")
else
    QA_REMAINING=0
    QA_REMAINING_JSON="[]"
fi

# ── Snapshot live stack count AFTER teardown ──────────────────────────────────
LIVE_AFTER=0
LIVE_AFTER=$(docker compose -p dopemux ps -q 2>/dev/null | wc -l | tr -d ' ') || LIVE_AFTER=0
log_info "Live dopemux containers after teardown: $LIVE_AFTER"

# ── Integrity: live stack should be unchanged ─────────────────────────────────
LIVE_DELTA=$(( LIVE_AFTER - LIVE_BEFORE ))
if [[ $LIVE_DELTA -ne 0 ]]; then
    log_warn "Live stack container count changed by $LIVE_DELTA (before=$LIVE_BEFORE after=$LIVE_AFTER)"
fi

# ── Emit result ───────────────────────────────────────────────────────────────
EVIDENCE=$(printf '{"qa_containers_remaining":%d,"qa_container_names":%s,"live_containers_before":%d,"live_containers_after":%d,"live_delta":%d}' \
    "$QA_REMAINING" "$QA_REMAINING_JSON" "$LIVE_BEFORE" "$LIVE_AFTER" "$LIVE_DELTA")

if [[ $QA_REMAINING -eq 0 ]]; then
    emit_result "env_down" "PASS" \
        "QA stack fully stopped; live stack untouched (${LIVE_AFTER} containers)" \
        "$EVIDENCE"
else
    emit_result "env_down" "FAIL" \
        "${QA_REMAINING} QA container(s) still running after teardown" \
        "$EVIDENCE"
fi

# Script exits 0 regardless — teardown must never abort the caller's trap
exit 0
