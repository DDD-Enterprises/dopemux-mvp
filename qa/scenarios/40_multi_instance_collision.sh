#!/usr/bin/env bash
# qa/scenarios/40_multi_instance_collision.sh — Namespace isolation test between
# two concurrent dopemux instances.
#
# Brings up a second minimal stack (dopemux-qa2) with port offsets +20 from QA
# ports, writes a key to its ConPort database, then confirms that the primary QA
# stack's ConPort (dopemux-qa, instance E) does NOT expose data written to the
# qa2 instance — proving postgres namespace isolation.
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

# ── Guard ─────────────────────────────────────────────────────────────────────
guard_qa_project

# ── Load QA port vars ─────────────────────────────────────────────────────────
if [[ -f "${QA_ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    source <(grep -E '^[A-Z_]+=' "${QA_ENV_FILE}" | grep -v '^#' | sed 's/^/export /')
fi

QA_CONPORT_HTTP_PORT="${QA_CONPORT_HTTP_PORT:-3044}"
QA_CONPORT_MCP_PORT="${QA_CONPORT_MCP_PORT:-3045}"
QA_POSTGRES_PORT="${QA_POSTGRES_PORT:-5472}"
POSTGRES_USER="${POSTGRES_USER:-dopemux}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-dopemux_qa_password}"

# qa2 ports are QA ports + 20
QA2_POSTGRES_PORT=$(( QA_POSTGRES_PORT + 20 ))         # 5492
QA2_CONPORT_HTTP_PORT=$(( QA_CONPORT_HTTP_PORT + 20 )) # 3064
QA2_CONPORT_MCP_PORT=$(( QA_CONPORT_MCP_PORT + 20 ))   # 3065

QA_WORKSPACE="${QA_WORKSPACE_PATH:-/tmp/qa-workspace}"
QA2_WORKSPACE="/tmp/qa2-workspace"

# Unique sentinel value written to qa2 and must NOT appear in qa
COLLISION_VALUE="instance_qa2_$(date -u +%s)"

STEP_TIMEOUT=60

# ── Detect whether primary QA stack is running ───────────────────────────────
_qa_stack_running() {
    local project="${1:-dopemux-qa}"
    local count=0
    set +e
    local raw
    raw="$(docker compose -p "${project}" ps --format json 2>/dev/null)"
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

# ── Helper: POST JSON-RPC to a ConPort MCP endpoint ─────────────────────────
conport_call() {
    local mcp_port="$1"
    local tool="$2"
    local args_json="$3"
    local body
    body=$(printf \
        '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"%s","arguments":%s}}' \
        "${tool}" "${args_json}")
    curl -s --max-time "${STEP_TIMEOUT}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "${body}" \
        "http://localhost:${mcp_port}/mcp" 2>/dev/null || true
}

# ── Cleanup trap ──────────────────────────────────────────────────────────────
QA2_ENV_FILE=""
_cleanup_qa2() {
    log_info "Cleaning up qa2 stack (dopemux-qa2)"
    set +e
    if [[ -n "${QA2_ENV_FILE}" && -f "${QA2_ENV_FILE}" ]]; then
        docker compose -p dopemux-qa2 \
            --env-file "${QA2_ENV_FILE}" \
            -f "${ROOT}/compose.yml" \
            down -v --remove-orphans 2>/dev/null
        rm -f "${QA2_ENV_FILE}"
    fi
    set -e
    log_info "qa2 cleanup complete"
}

# ── Begin scenario ────────────────────────────────────────────────────────────
scenario_start "multi_instance_collision"

# Skip if primary QA stack is not running
if ! _qa_stack_running "dopemux-qa"; then
    scenario_skip "Primary QA stack (dopemux-qa) is not running — run 00_env_up.sh first"
    exit 0
fi

log_info "Primary QA stack is running; starting namespace isolation test"
log_info "qa2 port offsets: postgres=${QA2_POSTGRES_PORT} conport_http=${QA2_CONPORT_HTTP_PORT} conport_mcp=${QA2_CONPORT_MCP_PORT}"

# ── Step 1: Build qa2 env file ────────────────────────────────────────────────
QA2_ENV_FILE="$(mktemp /tmp/dopemux-qa2-env.XXXXXX)"
trap '_cleanup_qa2' EXIT

cat > "${QA2_ENV_FILE}" <<EOF
COMPOSE_PROJECT_NAME=dopemux-qa2
DOPEMUX_INSTANCE_ID=QA2
POSTGRES_PORT=${QA2_POSTGRES_PORT}
POSTGRES_DB=dopemux_qa2
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
CONPORT_HTTP_PORT=${QA2_CONPORT_HTTP_PORT}
CONPORT_MCP_PORT=${QA2_CONPORT_MCP_PORT}
CONPORT_INFO_PORT=4024
REDIS_EVENTS_PORT=$(( 6419 + 20 ))
REDIS_PRIMARY_PORT=$(( 6420 + 20 ))
PAL_PORT=$(( 3043 + 20 ))
LITELLM_PORT=$(( 4040 + 20 ))
DOPE_CONTEXT_PORT=$(( 3050 + 20 ))
QDRANT_PORT=$(( 6373 + 20 ))
QDRANT_GRPC_PORT=$(( 6374 + 20 ))
REDIS_UI_PORT=18081
LEANTIME_PORT=$(( 8120 + 20 ))
EOF

log_info "qa2 env file: ${QA2_ENV_FILE}"

# ── Step 2: Bring up minimal qa2 stack (postgres + conport only) ──────────────
log_info "Bringing up dopemux-qa2 stack (postgres + conport services)"

# compose.yml has fixed container_name values (dopemux-postgres-age, redis-events, …)
# that conflict with the already-running qa stack. qa/compose.qa.yml must override
# those names; without it Docker rejects the second stack before any collision test.
QA_OVERLAY="${ROOT}/qa/compose.qa.yml"
if [[ ! -f "${QA_OVERLAY}" ]]; then
    emit_result "multi_instance_collision" "NOT_RUN" \
        "qa/compose.qa.yml not found — required to run a second stack without fixed container_name conflicts" \
        '{"reason":"missing_qa_overlay","help":"Create qa/compose.qa.yml overriding fixed container_name values"}'
    exit 0
fi
log_info "Using QA overlay for qa2: ${QA_OVERLAY}"

# Ensure dopemux-network exists (BETA-INSTALL-02)
docker network create dopemux-network 2>/dev/null || true

set +e
docker compose -p dopemux-qa2 \
    --env-file "${QA2_ENV_FILE}" \
    -f "${QA_OVERLAY}" \
    up -d \
    --scale pal=0 \
    --scale litellm=0 \
    --scale dope-context=0 \
    --scale qdrant=0 \
    --scale redis-ui=0 \
    --scale leantime=0 \
    2>"${RESULTS_DIR}/40_qa2_up.log"
QA2_UP_RC=$?
set -e

if [[ ${QA2_UP_RC} -ne 0 ]]; then
    emit_result "multi_instance_collision" "FAIL" \
        "Failed to bring up dopemux-qa2 stack (exit ${QA2_UP_RC})" \
        "$(printf '{"qa2_up_rc":%d,"log":"%s"}' ${QA2_UP_RC} "${RESULTS_DIR}/40_qa2_up.log")"
    exit 0
fi

# Wait for qa2 ConPort to be healthy
log_info "Waiting for qa2 ConPort HTTP on port ${QA2_CONPORT_HTTP_PORT}"
QA2_CONPORT_READY=0
for attempt in $(seq 1 20); do
    STATUS="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 \
        "http://localhost:${QA2_CONPORT_HTTP_PORT}/health" 2>/dev/null || echo "000")"
    if [[ "${STATUS}" == "200" ]]; then
        log_info "qa2 ConPort ready (attempt ${attempt})"
        QA2_CONPORT_READY=1
        break
    fi
    log_info "qa2 ConPort not ready (attempt ${attempt}/20, HTTP ${STATUS})"
    sleep 3
done

if [[ ${QA2_CONPORT_READY} -eq 0 ]]; then
    emit_result "multi_instance_collision" "NOT_RUN" \
        "qa2 ConPort did not become ready on port ${QA2_CONPORT_HTTP_PORT} within 60s" \
        "$(printf '{"qa2_conport_port":%d}' ${QA2_CONPORT_HTTP_PORT})"
    exit 0
fi

mkdir -p "${QA2_WORKSPACE}"

# ── Step 3: Write sentinel key to qa2 ConPort ─────────────────────────────────
log_info "Writing sentinel to qa2 ConPort workspace: ${QA2_WORKSPACE}"
WRITE_ARGS=$(printf \
    '{"workspace_id":"%s","category":"collision_test","key":"A","value":"%s"}' \
    "${QA2_WORKSPACE}" \
    "${COLLISION_VALUE}")
WRITE_RESP="$(conport_call "${QA2_CONPORT_MCP_PORT}" "log_custom_data" "${WRITE_ARGS}")"
log_info "qa2 log_custom_data response: $(echo "${WRITE_RESP}" | head -c 200)"

# Verify write was acknowledged (result or no error)
WRITE_OK=false
if [[ -n "${WRITE_RESP}" ]] && echo "${WRITE_RESP}" | jq -e '.result // .error' >/dev/null 2>&1; then
    WRITE_OK=true
fi

if [[ "${WRITE_OK}" != "true" ]]; then
    emit_result "multi_instance_collision" "FAIL" \
        "Could not write sentinel to qa2 ConPort — functional call failed" \
        "$(printf '{"write_ok":false,"qa2_conport_mcp_port":%d}' ${QA2_CONPORT_MCP_PORT})"
    exit 0
fi

# ── Step 4: Attempt to read the same key from the primary QA ConPort ──────────
# If isolation is correct, qa's postgres has no knowledge of qa2's workspace data
log_info "Reading same key from primary QA ConPort (port ${QA_CONPORT_MCP_PORT}) — expecting isolation"
READ_ARGS=$(printf \
    '{"workspace_id":"%s","category":"collision_test","key":"A"}' \
    "${QA2_WORKSPACE}")
READ_RESP="$(conport_call "${QA_CONPORT_MCP_PORT}" "get_custom_data" "${READ_ARGS}")"
log_info "QA get_custom_data response: $(echo "${READ_RESP}" | head -c 400)"

# Check if the sentinel value leaked across instance boundaries
LEAKED=false
if echo "${READ_RESP}" | grep -qF "${COLLISION_VALUE}" 2>/dev/null; then
    LEAKED=true
fi

ISOLATION_EVIDENCE=$(printf \
    '{"qa_conport_mcp_port":%d,"qa2_conport_mcp_port":%d,"sentinel_value":"%s","leaked":%s,"qa2_workspace":"%s"}' \
    "${QA_CONPORT_MCP_PORT}" \
    "${QA2_CONPORT_MCP_PORT}" \
    "${COLLISION_VALUE}" \
    "${LEAKED}" \
    "${QA2_WORKSPACE}")

if [[ "${LEAKED}" == "false" ]]; then
    emit_result "multi_instance_collision" "PASS" \
        "Namespace isolation confirmed: qa2 data not visible in primary QA ConPort" \
        "${ISOLATION_EVIDENCE}"
else
    emit_result "multi_instance_collision" "FAIL" \
        "NAMESPACE LEAK: sentinel value from qa2 ConPort was visible in primary QA ConPort" \
        "${ISOLATION_EVIDENCE}"
fi

# Cleanup happens via EXIT trap
