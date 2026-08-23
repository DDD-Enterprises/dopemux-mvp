#!/bin/bash
# ConPort multi-server supervisor (PID 1).
#
# Required children (all three must stay up):
#   INFO_PID  — info_server.py      (service discovery)
#   REST_PID  — enhanced_server.py  (HTTP data plane :3004)
#   PROXY_PID — server.py sse       (MCP protocol :3005)
#
# Contract (TP-CONPORT-PID1-SUPERVISION-001 / L3 clean candidate):
#   - Death of ANY required child => PID 1 kills siblings and exits nonzero.
#   - Docker `restart: unless-stopped` then recovers the container.
#   - Permanent failure is bounded: a failure counter (volume-backed when
#     CONPORT_SUPERVISION_STATE_DIR is set) trips into a terminal sleep state
#     that keeps healthcheck failing without exit-loop restart storms.
#   - This replaces third-party autoheal + docker.sock mounts.
#
# Do not replace bare `wait` with another silent multi-wait: that was the
# 2026-08-02 silent-outage root cause (REST dead 7h+, container "Up").

set -eu

STATE_DIR="${CONPORT_SUPERVISION_STATE_DIR:-/tmp/conport-supervision}"
MAX_FAILURES="${CONPORT_MAX_CHILD_FAILURES:-5}"
FAILURE_WINDOW_SECS="${CONPORT_FAILURE_WINDOW_SECS:-600}"
ALERT_MARKER="${STATE_DIR}/TERMINAL_ALERT"
FAIL_LOG="${STATE_DIR}/failures.log"
COUNT_FILE="${STATE_DIR}/failure_count"

mkdir -p "$STATE_DIR"

log() { echo "[conport-supervisor] $*"; }
now() { date +%s; }

# --- permanent-failure gate -----------------------------------------------
# failures.log lines: <unix_ts> <child_name> <exit_code>
prune_and_count_failures() {
    local cutoff now_ts count
    now_ts=$(now)
    cutoff=$((now_ts - FAILURE_WINDOW_SECS))
    if [ ! -f "$FAIL_LOG" ]; then
        echo 0
        return
    fi
    # Keep only in-window lines.
    awk -v c="$cutoff" '$1 >= c {print}' "$FAIL_LOG" > "${FAIL_LOG}.tmp" 2>/dev/null || true
    mv "${FAIL_LOG}.tmp" "$FAIL_LOG" 2>/dev/null || true
    count=$(wc -l < "$FAIL_LOG" | tr -d ' ')
    echo "${count:-0}"
}

record_failure() {
    local name="$1" code="$2"
    echo "$(now) ${name} ${code}" >> "$FAIL_LOG"
    prune_and_count_failures > "$COUNT_FILE"
}

enter_terminal_alert() {
    local count="$1"
    cat > "$ALERT_MARKER" <<EOF
status=TERMINAL_ALERT
reason=child_failure_budget_exhausted
failures_in_window=${count}
max_failures=${MAX_FAILURES}
window_secs=${FAILURE_WINDOW_SECS}
timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
    log "TERMINAL ALERT: ${count} child failures within ${FAILURE_WINDOW_SECS}s (max ${MAX_FAILURES})."
    log "Entering non-exit terminal sleep so restart:unless-stopped does not storm."
    log "Operator must clear ${ALERT_MARKER} / failures.log after repair."
    # Stay alive, fail healthchecks (no servers), do not exit.
    while true; do
        sleep 3600
    done
}

fail_count=$(prune_and_count_failures)
if [ -f "$ALERT_MARKER" ] || [ "$fail_count" -ge "$MAX_FAILURES" ]; then
    enter_terminal_alert "$fail_count"
fi

# --- start required children ----------------------------------------------
log "Starting ConPort required children (info, rest:3004, mcp:3005)..."

# Real advertised MCP/SSE port -- capture the container-level value (compose
# sets MCP_SERVER_PORT=3005) before overriding it below for the REST/info
# children. info_server's own MCP_SERVER_PORT is pinned to the REST port so
# INFO_PORT derives to 4004; without this it would advertise :3004/sse to
# clients when the actual SSE listener is on :3005.
MCP_ADVERTISED_PORT="${MCP_SERVER_PORT:-3005}"

# Pin ports explicitly. Container env may set MCP_SERVER_PORT=3005 for the
# MCP service; info_server derives INFO_PORT=MCP_SERVER_PORT+1000, so leaving
# the env inherited would bind info on 4005 while compose publishes 4004.
MCP_SERVER_PORT=3004 CONPORT_ADVERTISED_MCP_PORT="${MCP_ADVERTISED_PORT}" python info_server.py &
INFO_PID=$!
log "info_server.py pid=${INFO_PID} (info on 4004, advertises mcp on ${MCP_ADVERTISED_PORT})"

MCP_SERVER_PORT=3004 python enhanced_server.py &
REST_PID=$!
log "enhanced_server.py (REST) pid=${REST_PID}"

MCP_SERVER_PORT=3005 python server.py sse &
PROXY_PID=$!
log "server.py sse (MCP) pid=${PROXY_PID}"

CHILDREN="${INFO_PID} ${REST_PID} ${PROXY_PID}"

shutdown_siblings() {
    local keep="${1:-}"
    for pid in $CHILDREN; do
        if [ "$pid" = "$keep" ]; then
            continue
        fi
        if kill -0 "$pid" 2>/dev/null; then
            kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    # Brief grace, then KILL.
    sleep 1
    for pid in $CHILDREN; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -KILL "$pid" 2>/dev/null || true
        fi
    done
    # Reap zombies.
    wait 2>/dev/null || true
}

# Map pid -> name for logs / failure records.
child_name() {
    case "$1" in
        "$INFO_PID")  echo "info_server" ;;
        "$REST_PID")  echo "enhanced_server_rest" ;;
        "$PROXY_PID") echo "mcp_proxy_sse" ;;
        *)            echo "unknown" ;;
    esac
}

# --- supervise: any child exit => nonzero PID1 exit -----------------------
# wait -n returns when the first child exits. That is the supervision edge.
set +e
wait -n $CHILDREN
status=$?
set -e

# Identify which child(ren) are gone.
dead_name="unknown"
dead_code="$status"
for pid in $CHILDREN; do
    if ! kill -0 "$pid" 2>/dev/null; then
        dead_name=$(child_name "$pid")
        break
    fi
done

log "Required child died: name=${dead_name} wait_status=${dead_code}"
record_failure "$dead_name" "$dead_code"
shutdown_siblings

fail_count=$(prune_and_count_failures)
if [ "$fail_count" -ge "$MAX_FAILURES" ]; then
    # Next container start will enter terminal alert; exit nonzero this time
    # so Docker still records a failed attempt.
    log "Failure budget reached (${fail_count}/${MAX_FAILURES}); next start enters terminal alert."
fi

# Nonzero exit => Docker restart:unless-stopped recovers once.
exit 1
