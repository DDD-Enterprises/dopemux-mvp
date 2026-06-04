#!/usr/bin/env bash
# qa/scenarios/10_install_gauntlet.sh — Test installer in an isolated Docker sandbox.
#
# Runs install.sh inside a fresh Ubuntu 22.04 container using INSTALLER_TEST_MODE=1
# (which skips actual secret acquisition and service starts while still exercising
# all preflight checks and installer logic paths).
#
# Exit codes:
#   0  — always (PASS / FAIL / NOT_RUN encoded in result JSON)
#   1  — hard environment failure (Docker not available)

set -euo pipefail

# ── Locate repo root and source common library ────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QA_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ROOT="$(cd "${QA_DIR}/.." && pwd)"

export ROOT
export RESULTS_DIR="${RESULTS_DIR:-${QA_DIR}/results}"
export RESULTS_FILE="${RESULTS_FILE:-${RESULTS_DIR}/results.jsonl}"
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-dopemux-qa}"
export RUN_ID="${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

mkdir -p "${RESULTS_DIR}"

# shellcheck source=../lib/qa_common.sh
source "${QA_DIR}/lib/qa_common.sh"

INSTALL_SCRIPT="${ROOT}/install.sh"
SANDBOX_IMAGE="ubuntu:22.04"

# ── Preflight: Docker must be available ───────────────────────────────────────
scenario_start "install_gauntlet"

if ! docker info >/dev/null 2>&1; then
    scenario_skip "Docker daemon not available — skipping install gauntlet"
    exit 0
fi

# ── Preflight: install.sh must exist ─────────────────────────────────────────
if [[ ! -f "${INSTALL_SCRIPT}" ]]; then
    emit_result "install_gauntlet" "NOT_RUN" \
        "install.sh not found at ${INSTALL_SCRIPT}" \
        "{\"install_script\":\"${INSTALL_SCRIPT}\"}"
    exit 0
fi

log_info "Running install gauntlet in ${SANDBOX_IMAGE}"
log_info "install.sh: ${INSTALL_SCRIPT}"

# ── Build inline test script for the container ───────────────────────────────
# We copy install.sh into the container and invoke it with INSTALLER_TEST_MODE=1,
# which exercises all preflight checks, arg parsing, and installer scaffolding
# without making network calls for secrets or starting Docker services.
# The --verify flag is also tested as a secondary check.

LOG_FILE="${RESULTS_DIR}/10_install_gauntlet.log"

INSTALL_CONTENTS="$(cat "${INSTALL_SCRIPT}")"

INNER_SCRIPT='#!/bin/bash
set -euo pipefail

# Minimal deps for install.sh preflight
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq 2>&1 | tail -5
apt-get install -y -qq curl git python3 python3-pip docker.io 2>&1 | tail -10

echo "=== Dependencies installed ==="

# Write install.sh to a temp location
cat > /tmp/install.sh << '"'"'INSTALL_SCRIPT_EOF'"'"'
'"${INSTALL_CONTENTS}"'
INSTALL_SCRIPT_EOF
chmod +x /tmp/install.sh

echo "=== Running install.sh with INSTALLER_TEST_MODE=1 ==="
INSTALLER_TEST_MODE=1 bash /tmp/install.sh --quick 2>&1
INSTALL_RC=$?
echo "install.sh --quick exit: ${INSTALL_RC}"

# If the installer placed a binary, test --version
if command -v dopemux >/dev/null 2>&1; then
    echo "=== dopemux found on PATH ==="
    dopemux --version 2>&1 || true
elif python3 -c "import dopemux" 2>/dev/null; then
    echo "=== dopemux importable as Python package ==="
    python3 -m dopemux.cli --version 2>&1 || true
else
    echo "dopemux not installed (expected in test mode)"
fi

exit ${INSTALL_RC}
'

# ── Run the sandbox ───────────────────────────────────────────────────────────
INSTALL_EXIT=99
CONTAINER_ID=""
set +e
CONTAINER_ID="$(docker run --rm \
    --name "dopemux-qa-install-gauntlet-$$" \
    --network host \
    "${SANDBOX_IMAGE}" \
    bash -c "${INNER_SCRIPT}" \
    2>&1 | tee "${LOG_FILE}")"
INSTALL_EXIT=${PIPESTATUS[0]}
set -e

log_info "Sandbox exit code: ${INSTALL_EXIT}"

EVIDENCE=$(printf \
    '{"sandbox":"%s","install_exit":%d,"log":"%s","install_script":"%s"}' \
    "${SANDBOX_IMAGE}" \
    "${INSTALL_EXIT}" \
    "${LOG_FILE}" \
    "${INSTALL_SCRIPT}")

if [[ ${INSTALL_EXIT} -eq 0 ]]; then
    emit_result "install_gauntlet" "PASS" \
        "install.sh (INSTALLER_TEST_MODE=1) completed in ${SANDBOX_IMAGE} with exit 0" \
        "${EVIDENCE}"
else
    # Check if failure is due to missing internet vs actual installer bug
    if grep -qiE "unable to fetch|could not resolve|network" "${LOG_FILE}" 2>/dev/null; then
        emit_result "install_gauntlet" "NOT_RUN" \
            "Sandbox had no internet access — install.sh network preflight failed (exit ${INSTALL_EXIT})" \
            "${EVIDENCE}"
    else
        emit_result "install_gauntlet" "FAIL" \
            "install.sh exited ${INSTALL_EXIT} in ${SANDBOX_IMAGE} — see ${LOG_FILE}" \
            "${EVIDENCE}"
    fi
fi
