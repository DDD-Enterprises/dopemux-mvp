#!/usr/bin/env bash
# qa/scenarios/60_rte_routing_safety.sh — RTE dry-run safety gate tests.
#
# Verifies that the RTE (Runtime Extraction) subsystem refuses to make LLM calls
# unless DPMX_LIVE_OK=1 is explicitly set.  All three probe variants must exit
# non-zero OR print a "dry run / live execution disabled" message, and zero
# LLM spend must have occurred.
#
# Sub-results emitted:
#   rte_dryrun_gate      — bare scan, no flag, no env: refused / dry-run only
#   rte_execute_gate     — scan --execute WITHOUT DPMX_LIVE_OK=1: refused
#   rte_execute_gate_env — scan with DPMX_LIVE_OK=0 explicit: refused
#
# Exit codes:
#   0  — always (PASS / FAIL / NOT_RUN encoded in result JSON)

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

# ── Guard ─────────────────────────────────────────────────────────────────────
guard_qa_project

# ── Helper: locate dopemux binary ────────────────────────────────────────────
_find_dopemux() {
    if command -v dopemux >/dev/null 2>&1; then
        echo "dopemux"
        return 0
    fi
    if command -v python3 >/dev/null 2>&1 && \
       python3 -m dopemux.cli --help >/dev/null 2>&1; then
        echo "python3 -m dopemux.cli"
        return 0
    fi
    return 1
}

# ── Helper: detect whether a known RTE subcommand exists ─────────────────────
# Probes --help output for subcommands containing "rte" or "extract".
# Writes the discovered subcommand path to stdout (e.g. "rte scan").
_find_rte_cmd() {
    local base="$1"
    local help_out
    set +e
    help_out="$(${base} --help 2>&1)"
    set -e

    # Preferred: top-level "rte" group
    if echo "${help_out}" | grep -qE '^\s+rte\b'; then
        # Check if "rte scan" exists
        local rte_help
        set +e
        rte_help="$(${base} rte --help 2>&1)"
        set -e
        if echo "${rte_help}" | grep -qE '^\s+scan\b'; then
            echo "rte scan"
            return 0
        fi
        # Any other sub under rte
        local sub
        sub="$(echo "${rte_help}" | grep -E '^\s+[a-z]' | awk '{print $1}' | head -1 || true)"
        if [[ -n "${sub}" ]]; then
            echo "rte ${sub}"
            return 0
        fi
        echo "rte"
        return 0
    fi

    # Fallback: look for standalone "extract" or "extraction" subcommand
    for candidate in extract extraction run-extraction; do
        if echo "${help_out}" | grep -qE "^\s+${candidate}\b"; then
            echo "${candidate}"
            return 0
        fi
    done

    return 1  # not found
}

# ── Helper: check if output signals dry-run / refusal ────────────────────────
_output_signals_dryrun() {
    local output="$1"
    echo "${output}" | grep -qiE \
        'dry.?run|live.?execution.?disabled|not.?live|dpmx_live_ok|execute.*disabled|spend.*0|no.?llm.?call|safety.?gate|refused' \
        2>/dev/null
}

# ── Helper: detect spend > 0 in output or spend ledger ───────────────────────
# Looks for non-zero spend indicators in command output and in any spend log
# files written under ROOT (e.g. .dopemux/spend.log, logs/spend.jsonl).
_spend_detected() {
    local cmd_output="$1"

    # 1. Output contains a non-zero dollar / token spend mention
    if echo "${cmd_output}" | grep -qiE \
        'spend[^:]*:[[:space:]]*\$?[1-9]|tokens?[[:space:]]*used[^:]*:[[:space:]]*[1-9]|cost[^:]*:[[:space:]]*\$?[0-9]*\.[0-9]*[1-9]' \
        2>/dev/null; then
        return 0
    fi

    # 2. Spend ledger file shows a non-zero entry written since scenario start
    local spend_files
    spend_files="$(find "${ROOT}" -maxdepth 4 \
        \( -name 'spend.log' -o -name 'spend.jsonl' -o -name 'llm_spend.jsonl' \) \
        -newer "${_SPEND_MARKER_FILE}" 2>/dev/null | head -5 || true)"

    if [[ -n "${spend_files}" ]]; then
        while IFS= read -r f; do
            if [[ -f "${f}" ]] && \
               tail -5 "${f}" 2>/dev/null | grep -qiE '"(amount|usd|tokens)"[[:space:]]*:[[:space:]]*[1-9]'; then
                return 0
            fi
        done <<< "${spend_files}"
    fi

    return 1
}

# ═══════════════════════════════════════════════════════════════════════════════
# Begin scenario
# ═══════════════════════════════════════════════════════════════════════════════
scenario_start "rte_routing_safety"

# Create a marker file timestamped at scenario start; spend detection uses
# -newer against this file so only logs written during this run are counted.
_SPEND_MARKER_FILE="${RESULTS_DIR}/60_rte_spend_marker_${RUN_ID:-$$}"
touch "${_SPEND_MARKER_FILE}"

# ── Preflight: locate dopemux ────────────────────────────────────────────────
DOPEMUX_BIN=""
if ! DOPEMUX_BIN="$(_find_dopemux)"; then
    NOT_RUN_EV='{"reason":"dopemux_not_found"}'
    emit_result "rte_dryrun_gate"      "NOT_RUN" "dopemux not found on PATH" "${NOT_RUN_EV}"
    emit_result "rte_execute_gate"     "NOT_RUN" "dopemux not found on PATH" "${NOT_RUN_EV}"
    emit_result "rte_execute_gate_env" "NOT_RUN" "dopemux not found on PATH" "${NOT_RUN_EV}"
    exit 0
fi
log_info "dopemux binary: ${DOPEMUX_BIN}"

# ── Preflight: probe --help to verify rte subcommand exists ──────────────────
RTE_SUBCMD=""
if ! RTE_SUBCMD="$(_find_rte_cmd "${DOPEMUX_BIN}")"; then
    NOT_RUN_EV='{"reason":"rte_subcommand_not_found"}'
    log_warn "No 'rte' (or equivalent) subcommand found in 'dopemux --help'"
    emit_result "rte_dryrun_gate"      "NOT_RUN" "rte subcommand not found in dopemux CLI" "${NOT_RUN_EV}"
    emit_result "rte_execute_gate"     "NOT_RUN" "rte subcommand not found in dopemux CLI" "${NOT_RUN_EV}"
    emit_result "rte_execute_gate_env" "NOT_RUN" "rte subcommand not found in dopemux CLI" "${NOT_RUN_EV}"
    exit 0
fi
log_info "RTE subcommand path: ${DOPEMUX_BIN} ${RTE_SUBCMD}"

# ─────────────────────────────────────────────────────────────────────────────
# Test 1: rte_dryrun_gate
# Run: dopemux rte scan  (no --execute, DPMX_LIVE_OK unset)
# Expect: exit non-zero  OR  output contains dry-run / live-disabled signal
# AND: no LLM spend detected
# ─────────────────────────────────────────────────────────────────────────────
log_info "=== Test 1: rte_dryrun_gate (no --execute, no DPMX_LIVE_OK) ==="

DRYRUN_RC=0
DRYRUN_OUT=""
set +e
DRYRUN_OUT="$(
    unset DPMX_LIVE_OK
    timeout 30 ${DOPEMUX_BIN} ${RTE_SUBCMD} 2>&1
)"
DRYRUN_RC=$?
set -e
log_info "exit code: ${DRYRUN_RC}, output head: $(echo "${DRYRUN_OUT}" | head -3 | tr '\n' '|')"

DRYRUN_REFUSED=false
DRYRUN_SIGNALS_SAFE=false
DRYRUN_SPEND=false

# Refused = non-zero exit
[[ ${DRYRUN_RC} -ne 0 ]] && DRYRUN_REFUSED=true

# Signals safety = output mentions dry-run or spend=0
_output_signals_dryrun "${DRYRUN_OUT}" && DRYRUN_SIGNALS_SAFE=true

# Spend detection
_spend_detected "${DRYRUN_OUT}" && DRYRUN_SPEND=true

DRYRUN_GATE_EV=$(printf \
    '{"exit_code":%d,"refused":%s,"signals_dryrun":%s,"spend_detected":%s}' \
    "${DRYRUN_RC}" \
    "${DRYRUN_REFUSED}" \
    "${DRYRUN_SIGNALS_SAFE}" \
    "${DRYRUN_SPEND}")

if [[ "${DRYRUN_SPEND}" == "true" ]]; then
    emit_result "rte_dryrun_gate" "FAIL" \
        "Spend detected during dry-run probe (exit ${DRYRUN_RC}) — LLM tokens consumed without DPMX_LIVE_OK=1" \
        "${DRYRUN_GATE_EV}"
elif [[ "${DRYRUN_REFUSED}" == "true" || "${DRYRUN_SIGNALS_SAFE}" == "true" ]]; then
    emit_result "rte_dryrun_gate" "PASS" \
        "Dry-run gate held: exit ${DRYRUN_RC}, spend_detected=false, signals_dryrun=${DRYRUN_SIGNALS_SAFE}" \
        "${DRYRUN_GATE_EV}"
else
    emit_result "rte_dryrun_gate" "FAIL" \
        "Gate did not hold: exited 0 with no dry-run signal and no spend detected — behavior ambiguous" \
        "${DRYRUN_GATE_EV}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Test 2: rte_execute_gate
# Run: dopemux rte scan --execute  WITHOUT DPMX_LIVE_OK=1
# Expect: exit non-zero (hard refusal)
# ─────────────────────────────────────────────────────────────────────────────
log_info "=== Test 2: rte_execute_gate (--execute, no DPMX_LIVE_OK) ==="

EXEC_RC=0
EXEC_OUT=""
set +e
EXEC_OUT="$(
    unset DPMX_LIVE_OK
    timeout 30 ${DOPEMUX_BIN} ${RTE_SUBCMD} --execute --allow-legacy-v3-scan 2>&1
)"
EXEC_RC=$?
set -e
log_info "exit code: ${EXEC_RC}, output head: $(echo "${EXEC_OUT}" | head -3 | tr '\n' '|')"

EXEC_REFUSED=false
[[ ${EXEC_RC} -ne 0 ]] && EXEC_REFUSED=true
# Also accept exit 0 that explicitly signals refusal in output
_output_signals_dryrun "${EXEC_OUT}" && EXEC_REFUSED=true

EXEC_SPEND=false
_spend_detected "${EXEC_OUT}" && EXEC_SPEND=true

EXEC_GATE_EV=$(printf \
    '{"exit_code":%d,"refused":%s,"spend_detected":%s}' \
    "${EXEC_RC}" \
    "${EXEC_REFUSED}" \
    "${EXEC_SPEND}")

if [[ "${EXEC_SPEND}" == "true" ]]; then
    emit_result "rte_execute_gate" "FAIL" \
        "Spend detected during --execute without DPMX_LIVE_OK=1 — gate did not hold" \
        "${EXEC_GATE_EV}"
elif [[ "${EXEC_REFUSED}" == "true" ]]; then
    emit_result "rte_execute_gate" "PASS" \
        "--execute refused without DPMX_LIVE_OK=1 (exit ${EXEC_RC}, spend=0)" \
        "${EXEC_GATE_EV}"
else
    emit_result "rte_execute_gate" "FAIL" \
        "--execute accepted without DPMX_LIVE_OK=1 (exit 0, no refusal signal) — safety gate missing" \
        "${EXEC_GATE_EV}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Test 3: rte_execute_gate_env
# Run: dopemux rte scan with DPMX_LIVE_OK=0 set explicitly
# Expect: exit non-zero (same as unset)
# ─────────────────────────────────────────────────────────────────────────────
log_info "=== Test 3: rte_execute_gate_env (DPMX_LIVE_OK=0 explicit) ==="

ENV0_RC=0
ENV0_OUT=""
set +e
ENV0_OUT="$(
    DPMX_LIVE_OK=0 timeout 30 ${DOPEMUX_BIN} ${RTE_SUBCMD} --execute --allow-legacy-v3-scan 2>&1
)"
ENV0_RC=$?
set -e
log_info "exit code: ${ENV0_RC}, output head: $(echo "${ENV0_OUT}" | head -3 | tr '\n' '|')"

ENV0_REFUSED=false
[[ ${ENV0_RC} -ne 0 ]] && ENV0_REFUSED=true
_output_signals_dryrun "${ENV0_OUT}" && ENV0_REFUSED=true

ENV0_SPEND=false
_spend_detected "${ENV0_OUT}" && ENV0_SPEND=true

ENV0_GATE_EV=$(printf \
    '{"exit_code":%d,"refused":%s,"spend_detected":%s,"dpmx_live_ok_value":"0"}' \
    "${ENV0_RC}" \
    "${ENV0_REFUSED}" \
    "${ENV0_SPEND}")

if [[ "${ENV0_SPEND}" == "true" ]]; then
    emit_result "rte_execute_gate_env" "FAIL" \
        "Spend detected when DPMX_LIVE_OK=0 — gate did not hold" \
        "${ENV0_GATE_EV}"
elif [[ "${ENV0_REFUSED}" == "true" ]]; then
    emit_result "rte_execute_gate_env" "PASS" \
        "--execute refused when DPMX_LIVE_OK=0 (exit ${ENV0_RC}, spend=0)" \
        "${ENV0_GATE_EV}"
else
    emit_result "rte_execute_gate_env" "FAIL" \
        "--execute accepted when DPMX_LIVE_OK=0 (exit 0, no refusal signal) — falsy env var not respected" \
        "${ENV0_GATE_EV}"
fi
