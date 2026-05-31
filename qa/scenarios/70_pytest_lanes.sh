#!/usr/bin/env bash
# qa/scenarios/70_pytest_lanes.sh — Run the three pytest lanes and re-enable the
# disabled multi-instance test.
#
# Sub-results emitted:
#   pytest_unit                — tests/unit  (-n auto, json-report)
#   pytest_integration         — tests/integration (json-report)
#   pytest_multi_instance_reenable — tests/test_event_multi_instance.py (re-enabled temporarily)
#
# Skip/xfail clustering: if > 3 items in the same file are skipped/xfailed,
# it is flagged in evidence as a signal worth investigating.
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

# ── Helper: find a Python interpreter ────────────────────────────────────────
_find_python() {
    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# ── Helper: check pytest-json-report is available ────────────────────────────
_has_json_report() {
    local python_bin="$1"
    "${python_bin}" -m pytest --co -q --json-report --json-report-file=/dev/null \
        -p no:cacheprovider 2>&1 | grep -v "no tests ran" >/dev/null 2>&1
}

# ── Helper: parse json-report file into counts ───────────────────────────────
# Writes tab-separated: passed failed skipped xfailed to stdout
_parse_json_report() {
    local report_file="$1"
    if [[ ! -f "${report_file}" ]]; then
        echo "0 0 0 0"
        return
    fi
    if ! command -v jq >/dev/null 2>&1; then
        echo "0 0 0 0"
        return
    fi
    jq -r '[
        (.summary.passed  // 0),
        (.summary.failed  // 0),
        (.summary.skipped // 0),
        ((.summary.xfailed // 0) + (.summary.xpassed // 0))
    ] | @tsv' "${report_file}" 2>/dev/null || echo "0 0 0 0"
}

# ── Helper: find skip/xfail clusters from json-report ────────────────────────
# Returns a JSON array of objects {file, count} where count > threshold.
_find_skip_clusters() {
    local report_file="$1"
    local threshold="${2:-3}"
    if [[ ! -f "${report_file}" ]]; then
        echo "[]"
        return
    fi
    if ! command -v jq >/dev/null 2>&1; then
        echo "[]"
        return
    fi
    jq --argjson t "${threshold}" '
        [ .tests[]?
          | select(.outcome == "skipped" or .outcome == "xfailed" or .outcome == "xpassed")
          | .nodeid | split("::")[0]
        ]
        | sort
        | group_by(.)
        | map({file: .[0], count: length})
        | map(select(.count > $t))
    ' "${report_file}" 2>/dev/null || echo "[]"
}

# ── Helper: parse -v output into approximate counts (fallback) ────────────────
# Used when pytest-json-report is unavailable.
_parse_verbose_output() {
    local output="$1"
    local passed failed skipped xfailed
    passed="$(echo "${output}"  | grep -cE ' PASSED'  2>/dev/null || echo 0)"
    failed="$(echo "${output}"  | grep -cE ' FAILED'  2>/dev/null || echo 0)"
    skipped="$(echo "${output}" | grep -cE ' SKIPPED' 2>/dev/null || echo 0)"
    xfailed="$(echo "${output}" | grep -cE ' XFAILED| XPASSED' 2>/dev/null || echo 0)"
    # Try summary line as fallback: "5 passed, 1 failed, 2 skipped"
    local summary_line
    summary_line="$(echo "${output}" | grep -E '[0-9]+ passed' | tail -1 || true)"
    if [[ -n "${summary_line}" ]]; then
        local sp sf ss sx
        sp="$(echo "${summary_line}" | grep -oE '[0-9]+ passed'  | grep -oE '[0-9]+' || echo "${passed}")"
        sf="$(echo "${summary_line}" | grep -oE '[0-9]+ failed'  | grep -oE '[0-9]+' || echo "${failed}")"
        ss="$(echo "${summary_line}" | grep -oE '[0-9]+ skipped' | grep -oE '[0-9]+' || echo "${skipped}")"
        sx="$(echo "${summary_line}" | grep -oE '[0-9]+ x(failed|passed)' | grep -oE '[0-9]+' || echo "${xfailed}")"
        passed="${sp}"; failed="${sf}"; skipped="${ss}"; xfailed="${sx}"
    fi
    echo "${passed} ${failed} ${skipped} ${xfailed}"
}

# ── Helper: build evidence JSON from counts + clusters ───────────────────────
_counts_to_evidence() {
    local passed="$1" failed="$2" skipped="$3" xfailed="$4" clusters="${5:-[]}"
    printf '{"pass":%s,"fail":%s,"skip":%s,"xfail":%s,"skip_clusters":%s}' \
        "${passed}" "${failed}" "${skipped}" "${xfailed}" "${clusters}"
}

# ═══════════════════════════════════════════════════════════════════════════════
# Begin scenario
# ═══════════════════════════════════════════════════════════════════════════════
scenario_start "pytest_lanes"

# ── Preflight: find Python ────────────────────────────────────────────────────
PYTHON_BIN=""
if ! PYTHON_BIN="$(_find_python)"; then
    NOT_RUN_EV='{"reason":"no_python"}'
    emit_result "pytest_unit"                    "NOT_RUN" "No Python interpreter found on PATH" "${NOT_RUN_EV}"
    emit_result "pytest_integration"             "NOT_RUN" "No Python interpreter found on PATH" "${NOT_RUN_EV}"
    emit_result "pytest_multi_instance_reenable" "NOT_RUN" "No Python interpreter found on PATH" "${NOT_RUN_EV}"
    exit 0
fi
log_info "Python: ${PYTHON_BIN} ($(${PYTHON_BIN} --version 2>&1))"

# ── Preflight: check pytest installed ────────────────────────────────────────
PYTEST_VERSION=""
set +e
PYTEST_VERSION="$(${PYTHON_BIN} -m pytest --version 2>&1 | head -1)"
PYTEST_AVAILABLE=$?
set -e

if [[ ${PYTEST_AVAILABLE} -ne 0 ]]; then
    NOT_RUN_EV='{"reason":"pytest_not_installed"}'
    emit_result "pytest_unit"                    "NOT_RUN" "pytest not installed (python -m pytest --version failed)" "${NOT_RUN_EV}"
    emit_result "pytest_integration"             "NOT_RUN" "pytest not installed" "${NOT_RUN_EV}"
    emit_result "pytest_multi_instance_reenable" "NOT_RUN" "pytest not installed" "${NOT_RUN_EV}"
    exit 0
fi
log_info "pytest: ${PYTEST_VERSION}"

# ── Detect pytest-json-report availability ────────────────────────────────────
USE_JSON_REPORT=false
set +e
${PYTHON_BIN} -c "import pytest_jsonreport" >/dev/null 2>&1 && USE_JSON_REPORT=true
set -e
log_info "pytest-json-report available: ${USE_JSON_REPORT}"

# Change to ROOT so relative test paths work
cd "${ROOT}"

# ─────────────────────────────────────────────────────────────────────────────
# Lane 1: Unit tests  (tests/unit/)
# ─────────────────────────────────────────────────────────────────────────────
log_info "=== Lane 1: pytest unit ==="

UNIT_REPORT="${RESULTS_DIR}/pytest_unit.json"
UNIT_RC=0
UNIT_OUT=""

UNIT_DIR="tests/unit"
if [[ ! -d "${UNIT_DIR}" ]]; then
    emit_result "pytest_unit" "NOT_RUN" \
        "tests/unit directory not found at ${ROOT}/${UNIT_DIR}" \
        '{"reason":"no_test_dir"}'
else
    # Build pytest invocation
    UNIT_ARGS=("${PYTHON_BIN}" -m pytest "${UNIT_DIR}" -q --tb=short)
    if ${PYTHON_BIN} -c "import xdist" >/dev/null 2>&1; then
        UNIT_ARGS+=(-n auto)
    fi
    if [[ "${USE_JSON_REPORT}" == "true" ]]; then
        UNIT_ARGS+=(--json-report "--json-report-file=${UNIT_REPORT}")
    else
        UNIT_ARGS+=(-v)
    fi

    set +e
    UNIT_OUT="$("${UNIT_ARGS[@]}" 2>&1)"
    UNIT_RC=$?
    set -e

    log_info "Unit tests exit: ${UNIT_RC}"

    # Parse counts
    read -r U_PASS U_FAIL U_SKIP U_XFAIL <<< "$(
        if [[ "${USE_JSON_REPORT}" == "true" && -f "${UNIT_REPORT}" ]]; then
            _parse_json_report "${UNIT_REPORT}"
        else
            _parse_verbose_output "${UNIT_OUT}"
        fi
    )"
    U_CLUSTERS="$(
        if [[ "${USE_JSON_REPORT}" == "true" && -f "${UNIT_REPORT}" ]]; then
            _find_skip_clusters "${UNIT_REPORT}" 3
        else
            echo "[]"
        fi
    )"

    UNIT_EV="$(_counts_to_evidence "${U_PASS}" "${U_FAIL}" "${U_SKIP}" "${U_XFAIL}" "${U_CLUSTERS}")"

    if [[ ${UNIT_RC} -eq 0 ]]; then
        emit_result "pytest_unit" "PASS" \
            "Unit tests passed: ${U_PASS} passed, ${U_FAIL} failed, ${U_SKIP} skipped, ${U_XFAIL} xfail" \
            "${UNIT_EV}"
    else
        emit_result "pytest_unit" "FAIL" \
            "Unit tests failed (exit ${UNIT_RC}): ${U_PASS} passed, ${U_FAIL} failed, ${U_SKIP} skipped, ${U_XFAIL} xfail" \
            "${UNIT_EV}"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Lane 2: Integration tests  (tests/integration/)
# ─────────────────────────────────────────────────────────────────────────────
log_info "=== Lane 2: pytest integration ==="

INTEG_REPORT="${RESULTS_DIR}/pytest_integration.json"
INTEG_RC=0
INTEG_OUT=""

INTEG_DIR="tests/integration"
if [[ ! -d "${INTEG_DIR}" ]]; then
    emit_result "pytest_integration" "NOT_RUN" \
        "tests/integration directory not found at ${ROOT}/${INTEG_DIR}" \
        '{"reason":"no_test_dir"}'
else
    INTEG_ARGS=("${PYTHON_BIN}" -m pytest "${INTEG_DIR}" -q --tb=short)
    if [[ "${USE_JSON_REPORT}" == "true" ]]; then
        INTEG_ARGS+=(--json-report "--json-report-file=${INTEG_REPORT}")
    else
        INTEG_ARGS+=(-v)
    fi

    set +e
    INTEG_OUT="$("${INTEG_ARGS[@]}" 2>&1)"
    INTEG_RC=$?
    set -e

    log_info "Integration tests exit: ${INTEG_RC}"

    read -r I_PASS I_FAIL I_SKIP I_XFAIL <<< "$(
        if [[ "${USE_JSON_REPORT}" == "true" && -f "${INTEG_REPORT}" ]]; then
            _parse_json_report "${INTEG_REPORT}"
        else
            _parse_verbose_output "${INTEG_OUT}"
        fi
    )"
    I_CLUSTERS="$(
        if [[ "${USE_JSON_REPORT}" == "true" && -f "${INTEG_REPORT}" ]]; then
            _find_skip_clusters "${INTEG_REPORT}" 3
        else
            echo "[]"
        fi
    )"

    INTEG_EV="$(_counts_to_evidence "${I_PASS}" "${I_FAIL}" "${I_SKIP}" "${I_XFAIL}" "${I_CLUSTERS}")"

    if [[ ${INTEG_RC} -eq 0 ]]; then
        emit_result "pytest_integration" "PASS" \
            "Integration tests passed: ${I_PASS} passed, ${I_FAIL} failed, ${I_SKIP} skipped, ${I_XFAIL} xfail" \
            "${INTEG_EV}"
    else
        emit_result "pytest_integration" "FAIL" \
            "Integration tests failed (exit ${INTEG_RC}): ${I_PASS} passed, ${I_FAIL} failed, ${I_SKIP} skipped, ${I_XFAIL} xfail" \
            "${INTEG_EV}"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Lane 3: Re-enable disabled multi-instance test and run it
# File: tests/test_event_multi_instance.py.disabled
# ─────────────────────────────────────────────────────────────────────────────
log_info "=== Lane 3: pytest multi-instance re-enable ==="

MI_DISABLED_FILE="${ROOT}/tests/test_event_multi_instance.py.disabled"
MI_ENABLED_FILE="${ROOT}/tests/test_event_multi_instance.py"
MI_DID_RENAME=false

if [[ ! -f "${MI_DISABLED_FILE}" && ! -f "${MI_ENABLED_FILE}" ]]; then
    emit_result "pytest_multi_instance_reenable" "NOT_RUN" \
        "Neither tests/test_event_multi_instance.py nor .disabled found" \
        '{"reason":"file_not_found"}'
else
    # Rename .disabled → .py if needed
    if [[ -f "${MI_DISABLED_FILE}" && ! -f "${MI_ENABLED_FILE}" ]]; then
        log_info "Renaming ${MI_DISABLED_FILE} → ${MI_ENABLED_FILE}"
        cp "${MI_DISABLED_FILE}" "${MI_ENABLED_FILE}"
        MI_DID_RENAME=true
    fi

    MI_RC=0
    MI_OUT=""
    set +e
    MI_OUT="$(${PYTHON_BIN} -m pytest "${MI_ENABLED_FILE}" --tb=short -q 2>&1)"
    MI_RC=$?
    set -e

    log_info "Multi-instance test exit: ${MI_RC}"

    # Restore .disabled state (remove the copy we made)
    if [[ "${MI_DID_RENAME}" == "true" && -f "${MI_ENABLED_FILE}" ]]; then
        log_info "Restoring: removing ${MI_ENABLED_FILE} (keeping .disabled original)"
        rm -f "${MI_ENABLED_FILE}"
    fi

    read -r MI_PASS MI_FAIL MI_SKIP MI_XFAIL <<< "$(_parse_verbose_output "${MI_OUT}")"

    MI_EV=$(printf \
        '{"pass":%s,"fail":%s,"skip":%s,"xfail":%s,"was_disabled":%s,"restored_after_run":true}' \
        "${MI_PASS}" "${MI_FAIL}" "${MI_SKIP}" "${MI_XFAIL}" "${MI_DID_RENAME}")

    if [[ ${MI_RC} -eq 0 ]]; then
        emit_result "pytest_multi_instance_reenable" "PASS" \
            "Multi-instance test passed after re-enable (${MI_PASS} passed, ${MI_FAIL} failed)" \
            "${MI_EV}"
    else
        emit_result "pytest_multi_instance_reenable" "FAIL" \
            "Multi-instance test failed after re-enable (exit ${MI_RC}: ${MI_PASS} passed, ${MI_FAIL} failed)" \
            "${MI_EV}"
    fi
fi
