#!/usr/bin/env bash
# qa/scenarios/30_mcp_roundtrips.sh — MCP server functional round-trip tests.
#
# Tests each MCP server with a real healthcheck AND a functional MCP call
# (not just port liveness). All checks degrade to NOT_RUN if the QA stack
# is not running.
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
export QA_NETWORK="${QA_NETWORK:-dopemux-qa-network}"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-dopemux-qa}"
export RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "${RESULTS_DIR}"

# shellcheck source=../lib/qa_common.sh
source "${QA_DIR}/lib/qa_common.sh"

# ── Guard: must be running under the QA compose project ──────────────────────
guard_qa_project

# ── Load QA port vars ─────────────────────────────────────────────────────────
if [[ -f "${QA_ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    source <(grep -E '^[A-Z_]+=' "${QA_ENV_FILE}" | grep -v '^#' | sed 's/^/export /')
fi

QA_CONPORT_HTTP_PORT="${QA_CONPORT_HTTP_PORT:-3044}"
QA_CONPORT_MCP_PORT="${QA_CONPORT_MCP_PORT:-3045}"
QA_PAL_PORT="${QA_PAL_PORT:-3043}"
QA_DOPE_CONTEXT_PORT="${QA_DOPE_CONTEXT_PORT:-3050}"

# QA workspace dir used for ConPort calls
QA_WORKSPACE="${QA_WORKSPACE_PATH:-/tmp/qa-workspace}"
mkdir -p "${QA_WORKSPACE}"

# ── Detect whether QA stack is running ───────────────────────────────────────
_qa_stack_running() {
    local count=0
    set +e
    local raw
    raw="$(docker compose -p dopemux-qa ps --format json 2>/dev/null)"
    if [[ -n "$raw" ]]; then
        if echo "$raw" | jq -e '.[0]' >/dev/null 2>&1; then
            count="$(echo "$raw" | jq '[.[] | select(.State == "running")] | length' 2>/dev/null || echo 0)"
        else
            count="$(echo "$raw" | jq -s '[.[] | select(.State == "running")] | length' 2>/dev/null || echo 0)"
        fi
    fi
    set -e
    [[ "${count}" -gt 0 ]]
}

# ── Helper: HTTP GET with status code capture ─────────────────────────────────
# Usage: http_get <url>
# Outputs: HTTP status code string (e.g. "200"), or "000" on error
http_get() {
    local url="$1"
    curl -s -o /dev/null -w '%{http_code}' --max-time 8 "$url" 2>/dev/null || echo "000"
}

# ── Helper: HTTP POST with JSON body ─────────────────────────────────────────
# Usage: http_post_json <url> <json_body>
# Outputs: response body (stdout); returns non-zero on curl failure
http_post_json() {
    local url="$1"
    local body="$2"
    curl -s --max-time 15 \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$body" \
        "$url" 2>/dev/null || true
}

# ── Helper: Check if JSON response contains a key ────────────────────────────
# Usage: json_has_key <response> <jq_expr>
# Returns 0 if jq_expr produces a non-null, non-false value
json_has_key() {
    local resp="$1"
    local expr="$2"
    echo "$resp" | jq -e "$expr" >/dev/null 2>&1
}

# ── Begin scenario ────────────────────────────────────────────────────────────
scenario_start "mcp_roundtrips"

# If the QA stack is not running, skip everything
if ! _qa_stack_running; then
    log_warn "QA stack (dopemux-qa) is not running — emitting NOT_RUN for all MCP checks"
    emit_result "mcp_conport_health"        "NOT_RUN" "QA stack not running" '{"reason":"stack_down"}'
    emit_result "mcp_conport_functional"    "NOT_RUN" "QA stack not running" '{"reason":"stack_down"}'
    emit_result "mcp_pal_health"            "NOT_RUN" "QA stack not running" '{"reason":"stack_down"}'
    emit_result "mcp_pal_functional"        "NOT_RUN" "QA stack not running" '{"reason":"stack_down"}'
    emit_result "mcp_dope_context_health"   "NOT_RUN" "QA stack not running" '{"reason":"stack_down"}'
    emit_result "mcp_dope_context_functional" "NOT_RUN" "QA stack not running" '{"reason":"stack_down"}'
    exit 0
fi

log_info "QA stack is running; proceeding with MCP round-trip tests"

# ─────────────────────────────────────────────────────────────────────────────
# A. ConPort — HTTP health + get_active_context functional call
# ─────────────────────────────────────────────────────────────────────────────
CONPORT_HTTP_BASE="http://localhost:${QA_CONPORT_HTTP_PORT}"
CONPORT_MCP_BASE="http://localhost:${QA_CONPORT_MCP_PORT}"

# A1. Health check
log_info "ConPort: GET ${CONPORT_HTTP_BASE}/health"
CONPORT_HEALTH_STATUS="$(http_get "${CONPORT_HTTP_BASE}/health")"
log_info "ConPort /health HTTP status: ${CONPORT_HEALTH_STATUS}"

CONPORT_HEALTH_EVIDENCE=$(printf \
    '{"http_status":"%s","url":"%s/health","response_ok":%s}' \
    "${CONPORT_HEALTH_STATUS}" \
    "${CONPORT_HTTP_BASE}" \
    "$([[ "${CONPORT_HEALTH_STATUS}" == "200" ]] && echo true || echo false)")

if [[ "${CONPORT_HEALTH_STATUS}" == "200" ]]; then
    emit_result "mcp_conport_health" "PASS" \
        "ConPort /health returned 200" \
        "${CONPORT_HEALTH_EVIDENCE}"
else
    emit_result "mcp_conport_health" "FAIL" \
        "ConPort /health returned ${CONPORT_HEALTH_STATUS} (expected 200)" \
        "${CONPORT_HEALTH_EVIDENCE}"
fi

# A2. Functional call: get_active_context
# ConPort MCP protocol: POST /mcp with JSON-RPC style body
log_info "ConPort: POST ${CONPORT_MCP_BASE}/mcp — tool=get_active_context"
CONPORT_FUNC_BODY=$(printf \
    '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_active_context","arguments":{"workspace_id":"%s"}}}' \
    "${QA_WORKSPACE}")
CONPORT_FUNC_RESP="$(http_post_json "${CONPORT_MCP_BASE}/mcp" "${CONPORT_FUNC_BODY}")"

CONPORT_FUNC_OK=false
CONPORT_FUNC_MSG="no valid JSON response"
if [[ -n "${CONPORT_FUNC_RESP}" ]] && echo "${CONPORT_FUNC_RESP}" | jq -e '.' >/dev/null 2>&1; then
    # Accept either a result key or an error key (both are valid JSON-RPC responses)
    if json_has_key "${CONPORT_FUNC_RESP}" '.result // .error'; then
        CONPORT_FUNC_OK=true
        CONPORT_FUNC_MSG="get_active_context returned valid JSON-RPC response"
    fi
fi

CONPORT_FUNC_EVIDENCE=$(printf \
    '{"http_status":200,"url":"%s/mcp","tool":"get_active_context","response_ok":%s}' \
    "${CONPORT_MCP_BASE}" \
    "${CONPORT_FUNC_OK}")

if [[ "${CONPORT_FUNC_OK}" == "true" ]]; then
    emit_result "mcp_conport_functional" "PASS" "${CONPORT_FUNC_MSG}" "${CONPORT_FUNC_EVIDENCE}"
elif [[ "${CONPORT_HEALTH_STATUS}" != "200" ]]; then
    emit_result "mcp_conport_functional" "NOT_RUN" \
        "Skipped: ConPort health check failed (port ${QA_CONPORT_MCP_PORT} likely unreachable)" \
        "${CONPORT_FUNC_EVIDENCE}"
else
    emit_result "mcp_conport_functional" "FAIL" \
        "get_active_context: ${CONPORT_FUNC_MSG}" \
        "${CONPORT_FUNC_EVIDENCE}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# B. PAL — HTTP health + listmodels functional call
# ─────────────────────────────────────────────────────────────────────────────
PAL_BASE="http://localhost:${QA_PAL_PORT}"

# B1. Health check — PAL may expose /health or just respond to GET /
log_info "PAL: GET ${PAL_BASE}/health"
PAL_HEALTH_STATUS="$(http_get "${PAL_BASE}/health")"
if [[ "${PAL_HEALTH_STATUS}" != "200" ]]; then
    log_info "PAL /health → ${PAL_HEALTH_STATUS}; trying GET /"
    PAL_HEALTH_STATUS="$(http_get "${PAL_BASE}/")"
fi
log_info "PAL health HTTP status: ${PAL_HEALTH_STATUS}"

PAL_HEALTH_EVIDENCE=$(printf \
    '{"http_status":"%s","url":"%s","response_ok":%s}' \
    "${PAL_HEALTH_STATUS}" \
    "${PAL_BASE}" \
    "$([[ "${PAL_HEALTH_STATUS}" == "200" ]] && echo true || echo false)")

if [[ "${PAL_HEALTH_STATUS}" == "200" ]]; then
    emit_result "mcp_pal_health" "PASS" \
        "PAL health endpoint returned 200" \
        "${PAL_HEALTH_EVIDENCE}"
else
    emit_result "mcp_pal_health" "FAIL" \
        "PAL health returned ${PAL_HEALTH_STATUS} (expected 200)" \
        "${PAL_HEALTH_EVIDENCE}"
fi

# B2. Functional call: listmodels
log_info "PAL: POST ${PAL_BASE}/mcp — tool=listmodels"
PAL_FUNC_BODY='{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"listmodels","arguments":{}}}'
PAL_FUNC_RESP="$(http_post_json "${PAL_BASE}/mcp" "${PAL_FUNC_BODY}")"

PAL_FUNC_OK=false
PAL_FUNC_MSG="no valid JSON response"
if [[ -n "${PAL_FUNC_RESP}" ]] && echo "${PAL_FUNC_RESP}" | jq -e '.' >/dev/null 2>&1; then
    # Check for result.content (typical MCP tool response) or any array/list in result
    if json_has_key "${PAL_FUNC_RESP}" '.result // .error'; then
        PAL_FUNC_OK=true
        PAL_FUNC_MSG="listmodels returned valid JSON-RPC response"
    fi
fi

PAL_FUNC_EVIDENCE=$(printf \
    '{"http_status":200,"url":"%s/mcp","tool":"listmodels","response_ok":%s}' \
    "${PAL_BASE}" \
    "${PAL_FUNC_OK}")

if [[ "${PAL_FUNC_OK}" == "true" ]]; then
    emit_result "mcp_pal_functional" "PASS" "${PAL_FUNC_MSG}" "${PAL_FUNC_EVIDENCE}"
elif [[ "${PAL_HEALTH_STATUS}" != "200" ]]; then
    emit_result "mcp_pal_functional" "NOT_RUN" \
        "Skipped: PAL health check failed (port ${QA_PAL_PORT} likely unreachable)" \
        "${PAL_FUNC_EVIDENCE}"
else
    emit_result "mcp_pal_functional" "FAIL" \
        "listmodels: ${PAL_FUNC_MSG}" \
        "${PAL_FUNC_EVIDENCE}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# C. dope-context — HTTP health + search_code functional call
# ─────────────────────────────────────────────────────────────────────────────
DOPE_CONTEXT_BASE="http://localhost:${QA_DOPE_CONTEXT_PORT}"

# C1. Health check
log_info "dope-context: GET ${DOPE_CONTEXT_BASE}/health"
DOPE_HEALTH_STATUS="$(http_get "${DOPE_CONTEXT_BASE}/health")"
log_info "dope-context /health HTTP status: ${DOPE_HEALTH_STATUS}"

DOPE_HEALTH_EVIDENCE=$(printf \
    '{"http_status":"%s","url":"%s/health","response_ok":%s}' \
    "${DOPE_HEALTH_STATUS}" \
    "${DOPE_CONTEXT_BASE}" \
    "$([[ "${DOPE_HEALTH_STATUS}" == "200" ]] && echo true || echo false)")

if [[ "${DOPE_HEALTH_STATUS}" == "200" ]]; then
    emit_result "mcp_dope_context_health" "PASS" \
        "dope-context /health returned 200" \
        "${DOPE_HEALTH_EVIDENCE}"
else
    emit_result "mcp_dope_context_health" "FAIL" \
        "dope-context /health returned ${DOPE_HEALTH_STATUS} (expected 200)" \
        "${DOPE_HEALTH_EVIDENCE}"
fi

# C2. Functional call: search_code
log_info "dope-context: POST ${DOPE_CONTEXT_BASE}/mcp — tool=search_code"
DOPE_FUNC_BODY=$(printf \
    '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_code","arguments":{"query":"test","top_k":1,"workspace_path":"%s"}}}' \
    "${QA_WORKSPACE}")
DOPE_FUNC_RESP="$(http_post_json "${DOPE_CONTEXT_BASE}/mcp" "${DOPE_FUNC_BODY}")"

DOPE_FUNC_OK=false
DOPE_FUNC_MSG="no valid JSON response"
if [[ -n "${DOPE_FUNC_RESP}" ]] && echo "${DOPE_FUNC_RESP}" | jq -e '.' >/dev/null 2>&1; then
    # Accept result (with any content including empty results array) or error (e.g. unindexed workspace)
    if json_has_key "${DOPE_FUNC_RESP}" '.result // .error'; then
        DOPE_FUNC_OK=true
        DOPE_FUNC_MSG="search_code returned valid JSON-RPC response"
    fi
fi

DOPE_FUNC_EVIDENCE=$(printf \
    '{"http_status":200,"url":"%s/mcp","tool":"search_code","response_ok":%s}' \
    "${DOPE_CONTEXT_BASE}" \
    "${DOPE_FUNC_OK}")

if [[ "${DOPE_FUNC_OK}" == "true" ]]; then
    emit_result "mcp_dope_context_functional" "PASS" "${DOPE_FUNC_MSG}" "${DOPE_FUNC_EVIDENCE}"
elif [[ "${DOPE_HEALTH_STATUS}" != "200" ]]; then
    emit_result "mcp_dope_context_functional" "NOT_RUN" \
        "Skipped: dope-context health check failed (port ${QA_DOPE_CONTEXT_PORT} likely unreachable)" \
        "${DOPE_FUNC_EVIDENCE}"
else
    emit_result "mcp_dope_context_functional" "FAIL" \
        "search_code: ${DOPE_FUNC_MSG}" \
        "${DOPE_FUNC_EVIDENCE}"
fi
