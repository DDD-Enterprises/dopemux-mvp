#!/usr/bin/env bash
# qa/lib/qa_common.sh — Shared bash library for dopemux-qa scenario scripts
# Source this file at the top of every scenario script:
#   source "$(dirname "$0")/../lib/qa_common.sh"
#
# Expected env vars (set by runner or qa env):
#   ROOT, RUN_ID, RESULTS_DIR, RESULTS_FILE, QA_ENV_FILE, QA_NETWORK, COMPOSE_PROJECT_NAME

set -euo pipefail

# ── Color codes ────────────────────────────────────────────────────────────────
_QA_RESET='\033[0m'
_QA_RED='\033[0;31m'
_QA_YELLOW='\033[0;33m'
_QA_CYAN='\033[0;36m'
_QA_GREEN='\033[0;32m'

# ── Logging ────────────────────────────────────────────────────────────────────
log_info() {
    echo -e "${_QA_CYAN}[INFO ]${_QA_RESET} $(date -u +%H:%M:%S) $*" >&2
}

log_warn() {
    echo -e "${_QA_YELLOW}[WARN ]${_QA_RESET} $(date -u +%H:%M:%S) $*" >&2
}

log_error() {
    echo -e "${_QA_RED}[ERROR]${_QA_RESET} $(date -u +%H:%M:%S) $*" >&2
}

log_pass() {
    echo -e "${_QA_GREEN}[PASS ]${_QA_RESET} $(date -u +%H:%M:%S) $*" >&2
}

# ── Scenario state ─────────────────────────────────────────────────────────────
CURRENT_SCENARIO=""
_SCENARIO_START=0
SCENARIO_DONE=0

scenario_start() {
    local name="$1"
    CURRENT_SCENARIO="$name"
    _SCENARIO_START=$SECONDS
    SCENARIO_DONE=0
    log_info "=== scenario: $name ==="
}

scenario_skip() {
    local reason="${1:-skipped}"
    emit_result "$CURRENT_SCENARIO" "NOT_RUN" "$reason"
    SCENARIO_DONE=1
}

# ── Result emission ────────────────────────────────────────────────────────────
# emit_result scenario status message [evidence_json]
# Writes one JSON line atomically to $RESULTS_FILE.
emit_result() {
    local scenario="${1:-unknown}"
    local status="${2:-FAIL}"        # PASS | FAIL | NOT_RUN
    local message="${3:-}"
    local evidence="${4:-{}}"
    local timestamp
    timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    local duration_s=$(( SECONDS - _SCENARIO_START ))

    # Sanitise message for JSON (escape backslashes and double-quotes)
    local safe_msg
    safe_msg="$(printf '%s' "$message" | sed 's/\\/\\\\/g; s/"/\\"/g')"

    local line
    line=$(printf '{"scenario":"%s","status":"%s","message":"%s","evidence":%s,"timestamp":"%s","duration_s":%d}\n' \
        "$scenario" "$status" "$safe_msg" "$evidence" "$timestamp" "$duration_s")

    # Atomic append via temp file + mv (best-effort on NFS/overlayfs)
    local rf="${RESULTS_FILE:-/tmp/qa_results.jsonl}"
    local tmp
    tmp="$(mktemp "${rf}.XXXXXX")"
    echo "$line" > "$tmp"
    cat "$tmp" >> "$rf"
    rm -f "$tmp"

    case "$status" in
        PASS)    log_pass  "$scenario — $message" ;;
        FAIL)    log_error "$scenario — $message" ;;
        NOT_RUN) log_warn  "$scenario — NOT_RUN: $message" ;;
    esac
}

# ── Guard: must be running under the QA compose project ───────────────────────
guard_qa_project() {
    local project="${COMPOSE_PROJECT_NAME:-}"
    if [[ "$project" != "dopemux-qa" ]]; then
        log_error "COMPOSE_PROJECT_NAME='$project' — must be 'dopemux-qa'. Refusing to continue."
        exit 1
    fi
}

# ── docker compose wrapper scoped to QA project ───────────────────────────────
qa_docker_compose() {
    local env_file="${QA_ENV_FILE:-qa/.env}"
    docker compose -p dopemux-qa --env-file "$env_file" "$@"
}

# ── Require env vars ──────────────────────────────────────────────────────────
# require_env VAR1 VAR2 ...  — exits 1 if any var is unset or empty
require_env() {
    local missing=0
    for var in "$@"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required env var '$var' is unset or empty."
            missing=1
        fi
    done
    if [[ $missing -ne 0 ]]; then
        exit 1
    fi
}

# ── Health poll ───────────────────────────────────────────────────────────────
# health_poll url [retries=20] [interval_s=3]
# Returns 0 if HTTP 200 received within retries, 1 on timeout.
health_poll() {
    local url="$1"
    local retries="${2:-20}"
    local interval="${3:-3}"
    local attempt=0

    while (( attempt < retries )); do
        local code
        code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$url" 2>/dev/null || true)"
        if [[ "$code" == "200" ]]; then
            log_info "health_poll OK ($url) after $((attempt+1)) attempts"
            return 0
        fi
        log_info "health_poll $url → $code (attempt $((attempt+1))/$retries)"
        sleep "$interval"
        (( attempt++ )) || true
    done

    log_error "health_poll TIMEOUT: $url did not return 200 after $retries attempts"
    return 1
}

# ── assert_exit0 ───────────────────────────────────────────────────────────────
# assert_exit0 label cmd [args...]
# Runs cmd; emits FAIL and returns 1 if exit code is non-zero.
assert_exit0() {
    local label="$1"
    shift
    local output
    local rc=0
    output="$("$@" 2>&1)" || rc=$?
    if [[ $rc -ne 0 ]]; then
        emit_result "${CURRENT_SCENARIO:-unknown}" "FAIL" \
            "$label — exit $rc: $(echo "$output" | head -3 | tr '\n' ' ')"
        return 1
    fi
    log_info "assert_exit0 OK: $label"
    return 0
}

# ── assert_json ────────────────────────────────────────────────────────────────
# assert_json label file schema_key
# Uses jq to verify file has top-level key; emits FAIL if missing or jq fails.
assert_json() {
    local label="$1"
    local file="$2"
    local key="$3"

    if [[ ! -f "$file" ]]; then
        emit_result "${CURRENT_SCENARIO:-unknown}" "FAIL" \
            "$label — file not found: $file"
        return 1
    fi

    local val
    val="$(jq -e ".$key" "$file" 2>/dev/null)" || {
        emit_result "${CURRENT_SCENARIO:-unknown}" "FAIL" \
            "$label — key '.$key' missing or invalid JSON in $file"
        return 1
    }
    log_info "assert_json OK: $label (.$key = $val)"
    return 0
}

# ── Ensure results dir/file exist ─────────────────────────────────────────────
_qa_init_results() {
    local rf="${RESULTS_FILE:-/tmp/qa_results.jsonl}"
    local rd
    rd="$(dirname "$rf")"
    mkdir -p "$rd"
    touch "$rf"
}

_qa_init_results
