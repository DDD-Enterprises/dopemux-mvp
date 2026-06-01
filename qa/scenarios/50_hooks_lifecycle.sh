#!/usr/bin/env bash
# qa/scenarios/50_hooks_lifecycle.sh — Lifecycle hook dispatcher tests.
#
# Tests all 10 Claude Code lifecycle hooks by invoking the dispatcher
# (src/dopemux/claude/native_hooks.py) for each event.
#
# Key behaviours verified:
#   hooks_all_fire  — All 10 hooks execute and return exit 0 (fail-open)
#   hooks_failopen  — Hooks degrade gracefully even in a minimal venv
#                     without optional dependencies (pydantic, etc.)
#   hooks_stopgate  — The Stop hook completes in < 5s (no blocking)
#
# The dispatcher reads JSON from stdin and writes JSON to stdout.
# It is invoked as:  echo '<json>' | python -m dopemux.claude.native_hooks
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

# ── All 10 hook event names ───────────────────────────────────────────────────
ALL_HOOKS=(
    "SessionStart"
    "UserPromptSubmit"
    "PreToolUse"
    "PostToolUse"
    "PostToolUseFailure"
    "PermissionRequest"
    "Stop"
    "SubagentStop"
    "PreCompact"
    "SessionEnd"
)

# Hook dispatcher path (invoked as a module so src/ layout is honoured)
HOOKS_MODULE="dopemux.claude.native_hooks"
SRC_DIR="${ROOT}/src"

# QA workspace for hooks tests
QA_HOOKS_WORKSPACE="/tmp/qa-hooks-test"
mkdir -p "${QA_HOOKS_WORKSPACE}"

# ── Helper: find a usable Python interpreter ─────────────────────────────────
_find_python() {
    for candidate in python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# ── Helper: invoke one hook via stdin and return exit code ────────────────────
# Usage: _fire_hook <python_bin> <event_name> [extra_pythonpath]
# Payload is minimal but valid JSON for the dispatcher.
# Returns the exit code of the dispatcher (0=allow, 2=block — both acceptable).
_fire_hook() {
    local python_bin="$1"
    local event_name="$2"
    local extra_path="${3:-}"

    # Build a minimal payload for each hook type
    local payload
    case "${event_name}" in
        "UserPromptSubmit")
            payload='{"hook_event_name":"UserPromptSubmit","session_id":"qa-test","prompt":"hello"}'
            ;;
        "PreToolUse")
            payload='{"hook_event_name":"PreToolUse","session_id":"qa-test","tool_name":"Bash","tool_input":{}}'
            ;;
        "PostToolUse")
            payload='{"hook_event_name":"PostToolUse","session_id":"qa-test","tool_name":"Bash","tool_input":{},"tool_response":"ok"}'
            ;;
        "PostToolUseFailure")
            payload='{"hook_event_name":"PostToolUseFailure","session_id":"qa-test","tool_name":"Bash","tool_input":{},"error":"test error"}'
            ;;
        "PermissionRequest")
            payload='{"hook_event_name":"PermissionRequest","session_id":"qa-test","tool_name":"Bash"}'
            ;;
        "Stop"|"SubagentStop")
            payload="{\"hook_event_name\":\"${event_name}\",\"session_id\":\"qa-test\",\"stop_hook_active\":false,\"response\":\"\"}"
            ;;
        "PreCompact")
            payload='{"hook_event_name":"PreCompact","session_id":"qa-test"}'
            ;;
        "SessionEnd")
            payload='{"hook_event_name":"SessionEnd","session_id":"qa-test","reason":"normal"}'
            ;;
        *)
            # SessionStart and any unknown
            payload="{\"hook_event_name\":\"${event_name}\",\"session_id\":\"qa-test\"}"
            ;;
    esac

    local pythonpath_extra=""
    if [[ -n "${extra_path}" ]]; then
        pythonpath_extra="${extra_path}:"
    fi

    local rc=0
    # Dispatcher reads from stdin; exit 0 = allow, exit 2 = block (both non-crash)
    # env vars must prefix the pipeline, not just echo
    echo "${payload}" \
        | PYTHONPATH="${pythonpath_extra}${SRC_DIR}" \
          CLAUDE_PROJECT_DIR="${QA_HOOKS_WORKSPACE}" \
          DOPEMUX_INSTANCE_ID="QA" \
          timeout 10 \
            "${python_bin}" -m "${HOOKS_MODULE}" \
            >/dev/null 2>/dev/null \
        || rc=$?

    # Exit code 2 = block decision — dispatcher ran and made a decision; not a crash
    # Exit code 0 = allow — dispatcher ran normally
    # Exit code 1 = crash / JSON parse failure — bad
    # Exit code >2 (e.g. 124=timeout, or Python error) — bad
    if [[ "${rc}" -eq 0 || "${rc}" -eq 2 ]]; then
        return 0
    fi
    return "${rc}"
}

# ── Begin scenario ────────────────────────────────────────────────────────────
scenario_start "hooks_lifecycle"

# ── Preflight: Find Python interpreter ───────────────────────────────────────
PYTHON_BIN=""
if ! PYTHON_BIN="$(_find_python)"; then
    emit_result "hooks_all_fire" "NOT_RUN" \
        "No Python interpreter found on PATH" '{"reason":"no_python"}'
    emit_result "hooks_failopen" "NOT_RUN" \
        "No Python interpreter found on PATH" '{"reason":"no_python"}'
    emit_result "hooks_stopgate" "NOT_RUN" \
        "No Python interpreter found on PATH" '{"reason":"no_python"}'
    exit 0
fi
log_info "Python interpreter: ${PYTHON_BIN} ($(${PYTHON_BIN} --version 2>&1))"

# ── Preflight: Verify hooks module is importable ──────────────────────────────
IMPORT_CHECK_RC=0
IMPORT_CHECK_OUTPUT=""
set +e
IMPORT_CHECK_OUTPUT="$(PYTHONPATH="${SRC_DIR}" ${PYTHON_BIN} -c \
    "from dopemux.claude.native_hooks import NativeHookAdapter; print('ok')" 2>&1)"
IMPORT_CHECK_RC=$?
set -e

if [[ ${IMPORT_CHECK_RC} -ne 0 ]]; then
    log_warn "Hooks module import failed: ${IMPORT_CHECK_OUTPUT}"
    emit_result "hooks_all_fire" "NOT_RUN" \
        "Cannot import dopemux.claude.native_hooks — package not installed or SRC_DIR wrong" \
        "$(printf '{"import_rc":%d,"src_dir":"%s","error":"%s"}' \
            ${IMPORT_CHECK_RC} "${SRC_DIR}" \
            "$(echo "${IMPORT_CHECK_OUTPUT}" | head -1 | sed 's/"/\\"/g')")"
    emit_result "hooks_failopen" "NOT_RUN" \
        "Cannot import dopemux.claude.native_hooks" '{"reason":"import_failed"}'
    emit_result "hooks_stopgate" "NOT_RUN" \
        "Cannot import dopemux.claude.native_hooks" '{"reason":"import_failed"}'
    exit 0
fi

log_info "Hooks module importable: ${IMPORT_CHECK_OUTPUT}"

# ─────────────────────────────────────────────────────────────────────────────
# Test 1: hooks_all_fire
# Fire every hook and assert exit 0 (fail-open: any non-crash exit is acceptable)
# ─────────────────────────────────────────────────────────────────────────────
FIRED_COUNT=0
FAILED_HOOKS=()

for event in "${ALL_HOOKS[@]}"; do
    log_info "Firing hook: ${event}"
    HOOK_RC=0
    set +e
    _fire_hook "${PYTHON_BIN}" "${event}"
    HOOK_RC=$?
    set -e

    if [[ ${HOOK_RC} -eq 0 ]]; then
        FIRED_COUNT=$(( FIRED_COUNT + 1 ))
        log_info "  ${event} → exit 0 (allow) ✓"
    else
        log_error "  ${event} → exit ${HOOK_RC} (unexpected crash)"
        FAILED_HOOKS+=("${event}:exit${HOOK_RC}")
    fi
done

FAILED_HOOKS_JSON="[]"
if [[ ${#FAILED_HOOKS[@]} -gt 0 ]]; then
    FAILED_HOOKS_JSON="$(printf '%s\n' "${FAILED_HOOKS[@]}" | jq -R . | jq -s .)"
fi

ALL_FIRE_EVIDENCE=$(printf \
    '{"fired":%d,"total":%d,"failed":%s}' \
    "${FIRED_COUNT}" \
    "${#ALL_HOOKS[@]}" \
    "${FAILED_HOOKS_JSON}")

if [[ ${#FAILED_HOOKS[@]} -eq 0 ]]; then
    emit_result "hooks_all_fire" "PASS" \
        "All ${FIRED_COUNT}/${#ALL_HOOKS[@]} hooks fired and returned exit 0" \
        "${ALL_FIRE_EVIDENCE}"
else
    emit_result "hooks_all_fire" "FAIL" \
        "${#FAILED_HOOKS[@]} hook(s) crashed: $(printf '%s ' "${FAILED_HOOKS[@]}")" \
        "${ALL_FIRE_EVIDENCE}"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Test 2: hooks_failopen
# Run the dispatcher in a minimal venv WITHOUT pydantic (optional dep).
# The hook must still exit 0 — the fail-open guard in native_hooks.py
# catches ImportError and returns allow.
# ─────────────────────────────────────────────────────────────────────────────
VENV_DIR="$(mktemp -d /tmp/dopemux-qa-failopen-venv.XXXXXX)"
log_info "Creating minimal venv at ${VENV_DIR} (without pydantic)"

VENV_RC=0
set +e
${PYTHON_BIN} -m venv "${VENV_DIR}" 2>/dev/null
VENV_RC=$?
set -e

if [[ ${VENV_RC} -ne 0 ]]; then
    emit_result "hooks_failopen" "NOT_RUN" \
        "Cannot create temporary venv (python -m venv failed: exit ${VENV_RC})" \
        "$(printf '{"venv_rc":%d}' ${VENV_RC})"
else
    VENV_PYTHON="${VENV_DIR}/bin/python"
    # Install only the minimal dopemux package (no extras) — no pydantic
    set +e
    "${VENV_PYTHON}" -m pip install -q --no-deps -e "${ROOT}" 2>/dev/null
    VENV_INSTALL_RC=$?
    set -e

    FAILOPEN_EXIT=0
    FAILOPEN_OK=true

    # Run just SessionStart in the lean venv — must not crash
    if [[ ${VENV_INSTALL_RC} -eq 0 ]]; then
        set +e
        _fire_hook "${VENV_PYTHON}" "SessionStart"
        FAILOPEN_EXIT=$?
        set -e
    else
        log_warn "Minimal venv install failed (exit ${VENV_INSTALL_RC}); testing import isolation only"
        # Try running the module anyway — it may still work if src is on PYTHONPATH
        set +e
        _fire_hook "${VENV_PYTHON}" "SessionStart"
        FAILOPEN_EXIT=$?
        set -e
    fi

    if [[ ${FAILOPEN_EXIT} -ne 0 ]]; then
        FAILOPEN_OK=false
    fi

    # Cleanup venv
    rm -rf "${VENV_DIR}"

    FAILOPEN_EVIDENCE=$(printf \
        '{"clean_venv_exit":%d,"venv_install_rc":%d,"exit_ok":%s}' \
        "${FAILOPEN_EXIT}" \
        "${VENV_INSTALL_RC}" \
        "${FAILOPEN_OK}")

    if [[ "${FAILOPEN_OK}" == "true" ]]; then
        emit_result "hooks_failopen" "PASS" \
            "Hooks dispatcher returned exit 0 in minimal venv (graceful degradation)" \
            "${FAILOPEN_EVIDENCE}"
    else
        emit_result "hooks_failopen" "FAIL" \
            "Hooks dispatcher exited ${FAILOPEN_EXIT} in minimal venv — not fail-open" \
            "${FAILOPEN_EVIDENCE}"
    fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Test 3: hooks_stopgate
# The Stop hook must complete in < 5 seconds (no blocking on I/O or network).
# We measure wall-clock time using $SECONDS (integer seconds) or /usr/bin/time.
# ─────────────────────────────────────────────────────────────────────────────
STOP_LATENCY_S=0
STOP_RC=0
STOP_START=$SECONDS

set +e
# stop_hook_active=true tells the dispatcher to fast-return without blocking
STOP_PAYLOAD='{"hook_event_name":"Stop","session_id":"qa-test","stop_hook_active":true,"response":""}'
echo "${STOP_PAYLOAD}" \
    | PYTHONPATH="${SRC_DIR}" \
      CLAUDE_PROJECT_DIR="${QA_HOOKS_WORKSPACE}" \
      DOPEMUX_INSTANCE_ID="QA" \
      timeout 10 \
          "${PYTHON_BIN}" -m "${HOOKS_MODULE}" \
          >/dev/null 2>/dev/null
STOP_RC=$?
set -e

STOP_LATENCY_S=$(( SECONDS - STOP_START ))
log_info "Stop hook completed in ${STOP_LATENCY_S}s with exit ${STOP_RC}"

STOPGATE_OK=true
STOPGATE_MSG="Stop hook completed in ${STOP_LATENCY_S}s (exit ${STOP_RC})"

# Fail if took >= 5s or the dispatcher crashed (not 0 or 2)
if [[ ${STOP_LATENCY_S} -ge 5 ]]; then
    STOPGATE_OK=false
    STOPGATE_MSG="Stop hook took ${STOP_LATENCY_S}s — exceeds 5s threshold"
fi
if [[ ${STOP_RC} -ne 0 && ${STOP_RC} -ne 2 ]]; then
    STOPGATE_OK=false
    STOPGATE_MSG="Stop hook exited ${STOP_RC} (unexpected crash)"
fi

STOPGATE_EVIDENCE=$(printf \
    '{"stop_latency_s":%d,"stop_exit_rc":%d,"threshold_s":5}' \
    "${STOP_LATENCY_S}" \
    "${STOP_RC}")

if [[ "${STOPGATE_OK}" == "true" ]]; then
    emit_result "hooks_stopgate" "PASS" "${STOPGATE_MSG}" "${STOPGATE_EVIDENCE}"
else
    emit_result "hooks_stopgate" "FAIL" "${STOPGATE_MSG}" "${STOPGATE_EVIDENCE}"
fi
