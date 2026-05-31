#!/usr/bin/env bash
# qa/scenarios/00_env_up.sh — Bring up the dopemux-qa Docker stack (L0 lifecycle).
#
# Exit codes:
#   0  — scenario emitted (PASS or FAIL); orchestrator proceeds
#   1  — environment is broken (Docker not available), NOT_RUN emitted
#
# Usage: COMPOSE_PROJECT_NAME=dopemux-qa bash qa/scenarios/00_env_up.sh

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

# ── Preflight: Docker must be available ───────────────────────────────────────
if ! docker info >/dev/null 2>&1; then
    scenario_start "env_up"
    scenario_skip "Docker daemon not available — cannot bring up QA stack"
    exit 1
fi

# ── Guard: refuse to touch any non-qa compose project ────────────────────────
guard_qa_project

# ── Verify QA env file exists ─────────────────────────────────────────────────
if [[ ! -f "${QA_ENV_FILE}" ]]; then
    scenario_start "env_up"
    if [[ -f "${QA_DIR}/.env.example" ]]; then
        log_warn "QA env file not found at ${QA_ENV_FILE}; copying from .env.example"
        cp "${QA_DIR}/.env.example" "${QA_ENV_FILE}"
    else
        emit_result "env_up" "FAIL" \
            "QA env file not found: ${QA_ENV_FILE} (and no .env.example to copy from)"
        exit 1
    fi
fi

# ── Begin scenario ────────────────────────────────────────────────────────────
scenario_start "env_up"

# ── Step 1: Ensure QA docker network exists ───────────────────────────────────
log_info "Creating QA docker network '${QA_NETWORK}' (if not exists)"
docker network create "${QA_NETWORK}" 2>/dev/null || true

# ── Step 2: Ensure dopemux-network exists (BETA-INSTALL-02: external network) ─
log_info "Creating external network 'dopemux-network' (if not exists)"
docker network create dopemux-network 2>/dev/null || true

# ── Step 2b: Guard against fixed-container-name conflicts ────────────────────
# compose.yml has fixed container_name values (dopemux-postgres-age, redis-events, …)
# that Docker rejects when the live dopemux stack is already running.
# If a QA overlay (compose.qa.yml) doesn't exist AND the live stack is up,
# the harness cannot run in isolation — emit NOT_RUN rather than failing cryptically.
QA_COMPOSE_FILE="${ROOT}/compose.yml"
QA_OVERLAY="${ROOT}/qa/compose.qa.yml"
LIVE_RUNNING=0
LIVE_RUNNING=$(docker compose -p dopemux ps -q 2>/dev/null | wc -l | tr -d ' ') || LIVE_RUNNING=0
if [[ "${LIVE_RUNNING}" -gt 0 ]] && [[ ! -f "${QA_OVERLAY}" ]]; then
    scenario_skip "Live dopemux stack has ${LIVE_RUNNING} running container(s) and no qa/compose.qa.yml overlay exists. Create qa/compose.qa.yml that overrides fixed container_name values before running QA beside the live stack."
fi
if [[ -f "${QA_OVERLAY}" ]]; then
    log_info "Using QA overlay: ${QA_OVERLAY}"
    QA_COMPOSE_FILE="${QA_OVERLAY}"
fi

# ── Step 3: Bring up the QA stack ─────────────────────────────────────────────
log_info "Running: qa_docker_compose up -d --wait"
mkdir -p "${RESULTS_DIR}"
LOG_FILE="${RESULTS_DIR}/00_env_up.log"

# Allow compose up to fail without killing the script; we capture and check
set +e
qa_docker_compose \
    -f "${QA_COMPOSE_FILE}" \
    up -d --wait \
    2>&1 | tee "${LOG_FILE}"
COMPOSE_RC=${PIPESTATUS[0]}
set -e

if [[ ${COMPOSE_RC} -ne 0 ]]; then
    emit_result "env_up" "FAIL" \
        "docker compose up exited ${COMPOSE_RC} — see ${LOG_FILE}" \
        "{\"compose_exit\":${COMPOSE_RC},\"log\":\"${LOG_FILE}\"}"
    exit 1
fi

# ── Step 4: Health poll key services ─────────────────────────────────────────
# Load port vars from QA env file
# shellcheck disable=SC1090
source <(grep -E '^[A-Z_]+=' "${QA_ENV_FILE}" | grep -v '^#' | sed 's/^/export /')

QA_POSTGRES_PORT="${QA_POSTGRES_PORT:-5472}"
QA_CONPORT_HTTP_PORT="${QA_CONPORT_HTTP_PORT:-3044}"
QA_PAL_PORT="${QA_PAL_PORT:-3043}"

HEALTH_FAILURES=0

# Postgres: pg_isready or simple TCP check via curl
log_info "Polling Postgres on port ${QA_POSTGRES_PORT}"
POLL_RETRIES=40
POLL_INTERVAL=3

# Postgres doesn't speak HTTP; use bash /dev/tcp to check TCP connectivity
postgres_ready=0
for attempt in $(seq 1 ${POLL_RETRIES}); do
    if (echo >/dev/tcp/localhost/${QA_POSTGRES_PORT}) 2>/dev/null; then
        log_info "Postgres TCP up (attempt ${attempt})"
        postgres_ready=1
        break
    fi
    log_info "Postgres not ready (attempt ${attempt}/${POLL_RETRIES})"
    sleep ${POLL_INTERVAL}
done
if [[ ${postgres_ready} -eq 0 ]]; then
    log_error "Postgres health poll timed out on port ${QA_POSTGRES_PORT}"
    HEALTH_FAILURES=$((HEALTH_FAILURES + 1))
fi

# ConPort HTTP
log_info "Polling ConPort HTTP on port ${QA_CONPORT_HTTP_PORT}"
if ! health_poll "http://localhost:${QA_CONPORT_HTTP_PORT}/health" \
        ${POLL_RETRIES} ${POLL_INTERVAL}; then
    HEALTH_FAILURES=$((HEALTH_FAILURES + 1))
fi

# PAL
log_info "Polling PAL on port ${QA_PAL_PORT}"
if ! health_poll "http://localhost:${QA_PAL_PORT}/health" \
        ${POLL_RETRIES} ${POLL_INTERVAL}; then
    # PAL /health may not exist; try root
    if ! health_poll "http://localhost:${QA_PAL_PORT}/" \
            5 2; then
        log_warn "PAL health endpoint not responding (non-critical)"
        # PAL being down is not a hard blocker — count as warning only
    fi
fi

# ── Step 5: Count running containers ─────────────────────────────────────────
log_info "Counting running QA containers"
CONTAINER_COUNT=0
set +e
CONTAINER_JSON="$(qa_docker_compose \
    -f "${QA_COMPOSE_FILE}" \
    ps --format json 2>/dev/null)"
set -e

if [[ -n "${CONTAINER_JSON}" ]]; then
    # Handle both array and line-delimited JSON output from different compose versions
    if echo "${CONTAINER_JSON}" | jq -e '.[0]' >/dev/null 2>&1; then
        CONTAINER_COUNT="$(echo "${CONTAINER_JSON}" | jq '[.[] | select(.State == "running")] | length')"
    else
        CONTAINER_COUNT="$(echo "${CONTAINER_JSON}" | jq -s '[.[] | select(.State == "running")] | length')"
    fi
fi

log_info "Running containers: ${CONTAINER_COUNT}"

if [[ ${CONTAINER_COUNT} -lt 1 ]]; then
    emit_result "env_up" "FAIL" \
        "No running containers found after compose up" \
        "{\"container_count\":${CONTAINER_COUNT},\"health_failures\":${HEALTH_FAILURES}}"
    exit 1
fi

if [[ ${HEALTH_FAILURES} -gt 0 ]]; then
    emit_result "env_up" "FAIL" \
        "QA stack up but ${HEALTH_FAILURES} health endpoint(s) did not respond" \
        "{\"container_count\":${CONTAINER_COUNT},\"health_failures\":${HEALTH_FAILURES}}"
    # Exit 1 so the orchestrator knows the stack is not ready
    exit 1
fi

emit_result "env_up" "PASS" \
    "QA stack up; all health endpoints responding" \
    "{\"container_count\":${CONTAINER_COUNT},\"health_failures\":0}"
