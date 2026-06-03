#!/usr/bin/env bash
# qa/scenarios/01_probe_entrypoints.sh — Probe all CLI commands via --help.
#
# Does NOT require the QA stack to be running — these are host CLI checks.
#
# Exit codes:
#   0  — always (PASS or FAIL encoded in result JSON)
#   1  — environment broken (dopemux not on PATH)

set -euo pipefail

# ── Locate repo root and source common library ────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QA_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT="$(cd "${QA_DIR}/.." && pwd)"

export ROOT
export RESULTS_DIR="${RESULTS_DIR:-${QA_DIR}/results}"
export RESULTS_FILE="${RESULTS_FILE:-${RESULTS_DIR}/results.jsonl}"
export QA_ENV_FILE="${QA_ENV_FILE:-${QA_DIR}/.env}"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-dopemux-qa}"
export RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "${RESULTS_DIR}"

# shellcheck source=../lib/qa_common.sh
source "${QA_DIR}/lib/qa_common.sh"

# ── Preflight: dopemux must be on PATH (or importable as python -m) ──────────
DOPEMUX_CMD=""
if command -v dopemux >/dev/null 2>&1; then
    DOPEMUX_CMD="dopemux"
elif python3 -m dopemux.cli --help >/dev/null 2>&1; then
    DOPEMUX_CMD="python3 -m dopemux.cli"
else
    scenario_start "probe_entrypoints"
    emit_result "probe_entrypoints" "NOT_RUN" \
        "dopemux not found on PATH and 'python3 -m dopemux.cli' failed — install dopemux first"
    exit 1
fi

log_info "dopemux command: ${DOPEMUX_CMD}"

# ── Begin scenario ────────────────────────────────────────────────────────────
scenario_start "probe_entrypoints"

FAILURES=()
COMMANDS_FOUND=()
COMMANDS_CHECKED=0

# ── Step 1: Run top-level --help, extract subcommands ─────────────────────────
log_info "Running: ${DOPEMUX_CMD} --help"
TOP_HELP=""
set +e
TOP_HELP="$(${DOPEMUX_CMD} --help 2>&1)"
TOP_HELP_RC=$?
set -e

if [[ ${TOP_HELP_RC} -ne 0 ]]; then
    emit_result "probe_entrypoints" "FAIL" \
        "'dopemux --help' exited ${TOP_HELP_RC}" \
        "{\"exit_code\":${TOP_HELP_RC}}"
    exit 0
fi

# Parse the Commands section — lines of the form "  <cmd>  <description>"
# We capture the first word of each indented line in the Commands block.
IN_COMMANDS=0
while IFS= read -r line; do
    if echo "$line" | grep -qE '^Commands:'; then
        IN_COMMANDS=1
        continue
    fi
    # A new section heading (no leading spaces, ends with colon) resets flag
    if echo "$line" | grep -qE '^[A-Za-z].*:$'; then
        IN_COMMANDS=0
        continue
    fi
    if [[ ${IN_COMMANDS} -eq 1 ]]; then
        # Lines in the commands block: "  cmd   description"
        cmd="$(echo "$line" | awk '{print $1}')"
        if [[ -n "$cmd" && "$cmd" != "--" ]]; then
            COMMANDS_FOUND+=("$cmd")
        fi
    fi
done <<< "${TOP_HELP}"

log_info "Commands found: ${#COMMANDS_FOUND[@]}"

if [[ ${#COMMANDS_FOUND[@]} -lt 5 ]]; then
    emit_result "probe_entrypoints" "FAIL" \
        "Expected >5 subcommands, found only ${#COMMANDS_FOUND[@]}" \
        "{\"commands_found\":${#COMMANDS_FOUND[@]},\"commands\":$(printf '%s\n' "${COMMANDS_FOUND[@]}" | jq -R . | jq -s .)}"
    exit 0
fi

# ── Step 2: Run --help for each discovered subcommand ─────────────────────────
for cmd in "${COMMANDS_FOUND[@]}"; do
    COMMANDS_CHECKED=$((COMMANDS_CHECKED + 1))
    log_info "Checking: dopemux ${cmd} --help"
    set +e
    OUTPUT="$(${DOPEMUX_CMD} "${cmd}" --help 2>&1)"
    CMD_RC=$?
    set -e

    if [[ ${CMD_RC} -ne 0 ]]; then
        log_error "FAIL: dopemux ${cmd} --help exited ${CMD_RC}"
        FAILURES+=("${cmd}:exit${CMD_RC}")
    elif [[ -z "${OUTPUT}" ]]; then
        log_warn "WARN: dopemux ${cmd} --help produced empty output"
        FAILURES+=("${cmd}:empty_output")
    else
        log_info "OK:   dopemux ${cmd} --help"
    fi
done

# ── Step 3: Build evidence JSON and emit result ───────────────────────────────
COMMANDS_COUNT="${#COMMANDS_FOUND[@]}"
FAILURES_COUNT="${#FAILURES[@]}"

# Build JSON array of failures
FAILURES_JSON="[]"
if [[ ${FAILURES_COUNT} -gt 0 ]]; then
    FAILURES_JSON="$(printf '%s\n' "${FAILURES[@]}" | jq -R . | jq -s .)"
fi

# Build JSON array of all commands found
COMMANDS_JSON="$(printf '%s\n' "${COMMANDS_FOUND[@]}" | jq -R . | jq -s .)"

EVIDENCE=$(printf \
    '{"commands_found":%d,"commands_checked":%d,"failure_count":%d,"failures":%s,"commands":%s}' \
    "${COMMANDS_COUNT}" \
    "${COMMANDS_CHECKED}" \
    "${FAILURES_COUNT}" \
    "${FAILURES_JSON}" \
    "${COMMANDS_JSON}")

if [[ ${FAILURES_COUNT} -eq 0 ]]; then
    emit_result "probe_entrypoints" "PASS" \
        "All ${COMMANDS_CHECKED}/${COMMANDS_COUNT} commands responded to --help with exit 0" \
        "${EVIDENCE}"
else
    emit_result "probe_entrypoints" "FAIL" \
        "${FAILURES_COUNT}/${COMMANDS_CHECKED} commands failed --help check" \
        "${EVIDENCE}"
fi
