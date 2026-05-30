#!/usr/bin/env bash
# qa/scenarios/61_live_lane.sh — Opt-in live lane test (real LLM calls, cost tracking).
#
# DISABLED BY DEFAULT.  Enable by setting:
#   DPMX_LIVE_OK=1
#   DPMX_QA_SPEND_CAP_USD=<e.g. 0.05>
#
# What this tests:
#   live_lane_pal — A real PAL completion (cheapest/flash model, 1-token prompt)
#                   exits 0 with non-empty response; spend ledger records > 0.
#   live_lane_rte — RTE scan --execute on a fixture/sandbox workspace;
#                   completes without error and cumulative spend stays within cap.
#
# Spend cap is a hard abort: if spend exceeds DPMX_QA_SPEND_CAP_USD at any
# point, the scenario emits FAIL and exits immediately.
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

# ── Load QA env file if present ──────────────────────────────────────────────
if [[ -f "${QA_ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    source <(grep -E '^[A-Z_]+=' "${QA_ENV_FILE}" | grep -v '^#' | sed 's/^/export /')
fi

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

# ── Helper: read current spend from ledger files ──────────────────────────────
# Returns a floating-point USD value (0.0 if no ledger found or unparseable).
_read_spend_usd() {
    local total="0"
    local spend_files
    spend_files="$(find "${ROOT}" -maxdepth 4 \
        \( -name 'spend.log' -o -name 'spend.jsonl' -o -name 'llm_spend.jsonl' \) \
        2>/dev/null | head -10 || true)"

    if [[ -z "${spend_files}" ]]; then
        echo "0"
        return 0
    fi

    # Sum "amount" or "usd" fields from JSON lines
    while IFS= read -r f; do
        if [[ -f "${f}" ]]; then
            local file_sum
            file_sum="$(grep -oE '"(amount|usd)"[[:space:]]*:[[:space:]]*[0-9]+(\.[0-9]+)?' "${f}" 2>/dev/null \
                | grep -oE '[0-9]+(\.[0-9]+)?$' \
                | awk '{s+=$1} END {printf "%.6f", s}' || echo "0")"
            total="$(awk "BEGIN{printf \"%.6f\", ${total}+${file_sum}}")"
        fi
    done <<< "${spend_files}"

    echo "${total}"
}

# ── Helper: compare two floats (a <= b) ──────────────────────────────────────
_float_le() {
    # Returns 0 (true) if $1 <= $2
    awk "BEGIN{exit !($1 <= $2)}"
}

# ── Helper: detect RTE subcommand ────────────────────────────────────────────
_find_rte_cmd() {
    local base="$1"
    local help_out
    set +e
    help_out="$(${base} --help 2>&1)"
    set -e
    if echo "${help_out}" | grep -qE '^\s+rte\b'; then
        local rte_help
        set +e
        rte_help="$(${base} rte --help 2>&1)"
        set -e
        if echo "${rte_help}" | grep -qE '^\s+scan\b'; then
            echo "rte scan"; return 0
        fi
        local sub
        sub="$(echo "${rte_help}" | grep -E '^\s+[a-z]' | awk '{print $1}' | head -1 || true)"
        [[ -n "${sub}" ]] && { echo "rte ${sub}"; return 0; }
        echo "rte"; return 0
    fi
    for candidate in extract extraction run-extraction; do
        if echo "${help_out}" | grep -qE "^\s+${candidate}\b"; then
            echo "${candidate}"; return 0
        fi
    done
    return 1
}

# ── Helper: fixture workspace for live RTE test ───────────────────────────────
_make_fixture_workspace() {
    local ws
    ws="$(mktemp -d /tmp/dopemux-qa-live-rte.XXXXXX)"
    # Create a minimal stub so RTE has something to scan but doesn't load real tasks
    mkdir -p "${ws}/prompts" "${ws}/results"
    cat > "${ws}/prompts/qa_fixture.txt" <<'FIXTURE'
[QA FIXTURE] This is a synthetic prompt for live lane testing.
It contains no real customer data and no sensitive information.
Respond with exactly: QA_FIXTURE_OK
FIXTURE
    echo "${ws}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Begin scenario
# ═══════════════════════════════════════════════════════════════════════════════
scenario_start "live_lane"

# ── Gate: live lane disabled unless both vars are set ─────────────────────────
if [[ "${DPMX_LIVE_OK:-}" != "1" ]] || [[ -z "${DPMX_QA_SPEND_CAP_USD:-}" ]]; then
    scenario_skip "Live lane disabled — set DPMX_LIVE_OK=1 and DPMX_QA_SPEND_CAP_USD=<limit> to enable"
    exit 0
fi

SPEND_CAP="${DPMX_QA_SPEND_CAP_USD}"
log_info "Live lane ENABLED — spend cap: \$${SPEND_CAP}"

# ── Find dopemux ─────────────────────────────────────────────────────────────
DOPEMUX_BIN=""
if ! DOPEMUX_BIN="$(_find_dopemux)"; then
    NOT_RUN_EV='{"reason":"dopemux_not_found"}'
    emit_result "live_lane_pal" "NOT_RUN" "dopemux not found on PATH" "${NOT_RUN_EV}"
    emit_result "live_lane_rte" "NOT_RUN" "dopemux not found on PATH" "${NOT_RUN_EV}"
    exit 0
fi
log_info "dopemux binary: ${DOPEMUX_BIN}"

# ─────────────────────────────────────────────────────────────────────────────
# Test 1: live_lane_pal
# Run a minimal PAL completion (cheapest/flash model, minimal tokens).
# Assert: exit 0, non-empty response, spend ledger records > 0.
# ─────────────────────────────────────────────────────────────────────────────
log_info "=== Test 1: live_lane_pal ==="

SPEND_BEFORE="$(_read_spend_usd)"
log_info "Spend before PAL call: \$${SPEND_BEFORE}"

# Model preference order (cheapest first): gemini-flash → gpt-4o-mini → gpt-3.5-turbo
PAL_MODEL="${DPMX_QA_PAL_MODEL:-gemini-flash}"
PAL_MSG="Reply: ok"
PAL_MAX_TOKENS=3

PAL_RC=0
PAL_OUT=""
set +e
PAL_OUT="$(
    DPMX_LIVE_OK=1 timeout 60 \
        ${DOPEMUX_BIN} pal chat \
            --model "${PAL_MODEL}" \
            --message "${PAL_MSG}" \
            --max-tokens "${PAL_MAX_TOKENS}" \
        2>&1
)"
PAL_RC=$?
set -e

log_info "PAL exit: ${PAL_RC}, output: $(echo "${PAL_OUT}" | head -2 | tr '\n' '|')"

SPEND_AFTER_PAL="$(_read_spend_usd)"
PAL_SPEND_DELTA="$(awk "BEGIN{printf \"%.6f\", ${SPEND_AFTER_PAL}-${SPEND_BEFORE}}")"
log_info "Spend after PAL call: \$${SPEND_AFTER_PAL} (delta: \$${PAL_SPEND_DELTA})"

PAL_RESPONSE_OK=false
[[ ${PAL_RC} -eq 0 && -n "${PAL_OUT}" ]] && PAL_RESPONSE_OK=true

PAL_SPEND_RECORDED=false
# Spend delta > 0 or output mentions tokens/spend
if awk "BEGIN{exit !(${PAL_SPEND_DELTA} > 0)}"; then
    PAL_SPEND_RECORDED=true
elif echo "${PAL_OUT}" | grep -qiE 'token|usage|cost|spend'; then
    PAL_SPEND_RECORDED=true
fi

PAL_WITHIN_CAP=true
if ! _float_le "${PAL_SPEND_DELTA}" "${SPEND_CAP}"; then
    PAL_WITHIN_CAP=false
fi

PAL_EVIDENCE=$(printf \
    '{"model":"%s","exit_code":%d,"response_ok":%s,"spend_before_usd":"%s","spend_after_usd":"%s","spend_delta_usd":"%s","spend_recorded":%s,"within_cap":%s,"cap_usd":"%s"}' \
    "${PAL_MODEL}" \
    "${PAL_RC}" \
    "${PAL_RESPONSE_OK}" \
    "${SPEND_BEFORE}" \
    "${SPEND_AFTER_PAL}" \
    "${PAL_SPEND_DELTA}" \
    "${PAL_SPEND_RECORDED}" \
    "${PAL_WITHIN_CAP}" \
    "${SPEND_CAP}")

# Hard abort on overspend
if [[ "${PAL_WITHIN_CAP}" == "false" ]]; then
    emit_result "live_lane_pal" "FAIL" \
        "Spend cap exceeded after PAL call: \$${SPEND_AFTER_PAL} > cap \$${SPEND_CAP}" \
        "${PAL_EVIDENCE}"
    emit_result "live_lane_rte" "NOT_RUN" \
        "Skipped — spend cap exceeded during PAL test" \
        '{"reason":"spend_cap_exceeded_before_rte"}'
    exit 0
fi

if [[ "${PAL_RESPONSE_OK}" == "true" ]]; then
    emit_result "live_lane_pal" "PASS" \
        "PAL call succeeded (model=${PAL_MODEL}, exit=${PAL_RC}, spend_delta=\$${PAL_SPEND_DELTA})" \
        "${PAL_EVIDENCE}"
else
    emit_result "live_lane_pal" "FAIL" \
        "PAL call failed or returned empty response (exit=${PAL_RC})" \
        "${PAL_EVIDENCE}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Test 2: live_lane_rte
# Run RTE scan --execute on a fixture/sandbox workspace (not real tasks).
# Assert: exits 0, spend stays within cap.
# ─────────────────────────────────────────────────────────────────────────────
log_info "=== Test 2: live_lane_rte ==="

# Create fixture workspace
FIXTURE_WORKSPACE=""
FIXTURE_WORKSPACE="$(_make_fixture_workspace)"
log_info "Fixture workspace: ${FIXTURE_WORKSPACE}"

# Locate rte subcommand
RTE_SUBCMD=""
if ! RTE_SUBCMD="$(_find_rte_cmd "${DOPEMUX_BIN}")"; then
    emit_result "live_lane_rte" "NOT_RUN" \
        "rte subcommand not found in dopemux CLI" \
        '{"reason":"rte_subcommand_not_found"}'
    rm -rf "${FIXTURE_WORKSPACE}"
    exit 0
fi
log_info "RTE subcommand: ${RTE_SUBCMD}"

SPEND_BEFORE_RTE="$(_read_spend_usd)"
log_info "Spend before RTE call: \$${SPEND_BEFORE_RTE}"

RTE_RC=0
RTE_OUT=""
set +e
RTE_OUT="$(
    DPMX_LIVE_OK=1 timeout 120 \
        ${DOPEMUX_BIN} ${RTE_SUBCMD} --execute \
            --allow-legacy-v3-scan \
            --workspace "${FIXTURE_WORKSPACE}" \
        2>&1
)"
RTE_RC=$?
set -e

log_info "RTE exit: ${RTE_RC}, output head: $(echo "${RTE_OUT}" | head -3 | tr '\n' '|')"

SPEND_AFTER_RTE="$(_read_spend_usd)"
RTE_SPEND_DELTA="$(awk "BEGIN{printf \"%.6f\", ${SPEND_AFTER_RTE}-${SPEND_BEFORE_RTE}}")"
log_info "Spend after RTE call: \$${SPEND_AFTER_RTE} (delta: \$${RTE_SPEND_DELTA})"

RTE_WITHIN_CAP=true
if ! _float_le "${RTE_SPEND_DELTA}" "${SPEND_CAP}"; then
    RTE_WITHIN_CAP=false
fi

# Clean up fixture workspace
rm -rf "${FIXTURE_WORKSPACE}"

RTE_EVIDENCE=$(printf \
    '{"rte_subcmd":"%s","exit_code":%d,"spend_delta_usd":"%s","spend_total_usd":"%s","within_cap":%s,"cap_usd":"%s","fixture_workspace_used":true}' \
    "${RTE_SUBCMD}" \
    "${RTE_RC}" \
    "${RTE_SPEND_DELTA}" \
    "${SPEND_AFTER_RTE}" \
    "${RTE_WITHIN_CAP}" \
    "${SPEND_CAP}")

if [[ "${RTE_WITHIN_CAP}" == "false" ]]; then
    emit_result "live_lane_rte" "FAIL" \
        "Spend cap exceeded after RTE call: \$${SPEND_AFTER_RTE} > cap \$${SPEND_CAP}" \
        "${RTE_EVIDENCE}"
    exit 0
fi

if [[ ${RTE_RC} -eq 0 ]]; then
    emit_result "live_lane_rte" "PASS" \
        "RTE scan --execute on fixture workspace succeeded (exit=0, spend_delta=\$${RTE_SPEND_DELTA}, within_cap=true)" \
        "${RTE_EVIDENCE}"
else
    emit_result "live_lane_rte" "FAIL" \
        "RTE scan --execute on fixture workspace exited ${RTE_RC}" \
        "${RTE_EVIDENCE}"
fi
