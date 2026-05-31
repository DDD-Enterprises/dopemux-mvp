#!/usr/bin/env bash
# qa/scenarios/90_tui_renders.sh — L2 perceptual: TUI render quality checks
# Prefers deterministic/headless renders; never requires a live PTY.
#
# Sub-scenarios emitted:
#   tui_cockpit_audit     — dopemux cockpit --audit --output <file>
#   tui_cockpit_plain     — dopemux cockpit --plain (text fallback)
#   tui_dashboard_demo    — dopemux dashboard --demo OR python module entrypoint
#   tui_svg_snapshot      — Textual export_screenshot() SVG
#   tui_golden_diff       — diff against baseline/snapshots/ (NOT_RUN if no golden)
#   tui_ui_dashboard_build — ui-dashboard npm build (NOT_RUN if no package.json)
#   tui_renders_overall   — PASS if ≥2 sub-steps PASS, FAIL otherwise

set -euo pipefail

# ── Locate and source the shared library ──────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB="${SCRIPT_DIR}/../lib/qa_common.sh"
if [[ -f "$LIB" ]]; then
    # shellcheck source=../lib/qa_common.sh
    source "$LIB"
else
    # Minimal fallback so the script can still emit results
    echo "[WARN] qa_common.sh not found at $LIB — using inline fallback" >&2
    RESULTS_FILE="${RESULTS_FILE:-/tmp/qa_results.jsonl}"
    mkdir -p "$(dirname "$RESULTS_FILE")"
    touch "$RESULTS_FILE"
    CURRENT_SCENARIO="tui_renders"
    _SCENARIO_START=$SECONDS
    emit_result() {
        local scenario="$1" status="$2" message="$3" evidence="${4:-{}}"
        local ts; ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
        local dur=$(( SECONDS - _SCENARIO_START ))
        local safe; safe="$(printf '%s' "$message" | sed 's/\\/\\\\/g; s/"/\\"/g')"
        printf '{"scenario":"%s","status":"%s","message":"%s","evidence":%s,"timestamp":"%s","duration_s":%d}\n' \
            "$scenario" "$status" "$safe" "$evidence" "$ts" "$dur" >> "$RESULTS_FILE"
    }
    log_info()  { echo "[INFO ] $(date -u +%H:%M:%S) $*" >&2; }
    log_warn()  { echo "[WARN ] $(date -u +%H:%M:%S) $*" >&2; }
    log_error() { echo "[ERROR] $(date -u +%H:%M:%S) $*" >&2; }
    scenario_start() { CURRENT_SCENARIO="${1:-unknown}"; _SCENARIO_START=$SECONDS; }
    scenario_skip()  { emit_result "${CURRENT_SCENARIO}" "NOT_RUN" "${1:-skipped}"; exit 0; }
fi

# ── Setup ─────────────────────────────────────────────────────────────────────
scenario_start "tui_renders"

ROOT="${ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
RESULTS_DIR="${RESULTS_DIR:-$SCRIPT_DIR/../results}"
SNAPSHOTS_DIR="${SCRIPT_DIR}/../baseline/snapshots"
mkdir -p "$RESULTS_DIR" "$SNAPSHOTS_DIR"

PASS_COUNT=0

# ── Helper: increment pass counter ───────────────────────────────────────────
_sub_pass() { PASS_COUNT=$(( PASS_COUNT + 1 )); }

# ── Step A: cockpit --audit ───────────────────────────────────────────────────
{
    AUDIT_OUT="$RESULTS_DIR/cockpit_audit.json"
    rc=0
    dopemux cockpit --audit --output "$AUDIT_OUT" >"$RESULTS_DIR/cockpit_audit.stdout" 2>&1 || rc=$?
    if [[ $rc -eq 0 && -f "$AUDIT_OUT" ]] && jq -e . "$AUDIT_OUT" >/dev/null 2>&1; then
        emit_result "tui_cockpit_audit" "PASS" \
            "cockpit --audit exited 0 and produced valid JSON" \
            "{\"output_file\":\"cockpit_audit.json\"}"
        _sub_pass
    else
        emit_result "tui_cockpit_audit" "FAIL" \
            "cockpit --audit failed (rc=$rc) or output invalid JSON" \
            "{\"rc\":$rc}"
    fi
} || true

# ── Step B: cockpit --plain ───────────────────────────────────────────────────
{
    PLAIN_OUT="$RESULTS_DIR/cockpit_plain.txt"
    rc=0
    dopemux cockpit --plain >"$PLAIN_OUT" 2>&1 || rc=$?
    local_size=0
    [[ -f "$PLAIN_OUT" ]] && local_size=$(wc -c < "$PLAIN_OUT" | tr -d ' ')
    if [[ $rc -eq 0 && ${local_size:-0} -gt 0 ]]; then
        emit_result "tui_cockpit_plain" "PASS" \
            "cockpit --plain exited 0 and produced ${local_size} bytes" \
            "{\"bytes\":$local_size}"
        _sub_pass
    else
        emit_result "tui_cockpit_plain" "FAIL" \
            "cockpit --plain failed (rc=$rc) or empty output (${local_size} bytes)" \
            "{\"rc\":$rc,\"bytes\":${local_size:-0}}"
    fi
} || true

# ── Step C: dashboard --demo ──────────────────────────────────────────────────
{
    DEMO_OUT="$RESULTS_DIR/dashboard_demo.html"
    rc=0
    # Try CLI first; fall back to module entrypoint
    if dopemux dashboard --demo --output "$DEMO_OUT" >"$RESULTS_DIR/dashboard_demo.stdout" 2>&1; then
        rc=0
    elif python3 -c "
from dopemux.ui.dashboard import main
main(['--demo'])
" >"$DEMO_OUT" 2>&1; then
        rc=0
    else
        rc=1
    fi
    if [[ $rc -eq 0 ]]; then
        emit_result "tui_dashboard_demo" "PASS" \
            "dashboard --demo exited 0" "{}"
        _sub_pass
    else
        emit_result "tui_dashboard_demo" "FAIL" \
            "dashboard --demo unavailable (both CLI and module entrypoint failed)" "{}"
    fi
} || true

# ── Step D: Textual SVG snapshot ──────────────────────────────────────────────
{
    SVG_OUT="$RESULTS_DIR/tui_snapshot.svg"
    rc=0
    python3 - "$SVG_OUT" <<'PYEOF' 2>/dev/null || rc=$?
import sys, os
out_path = sys.argv[1]
try:
    from dopemux.tui.app import DopemuxApp
    app = DopemuxApp()
    svg = app.export_screenshot()
    with open(out_path, "w") as f:
        f.write(svg)
    print("ok")
except Exception as e:
    # Try alternate import paths
    try:
        from dopemux.app import DopemuxApp
        app = DopemuxApp()
        svg = app.export_screenshot()
        with open(out_path, "w") as f:
            f.write(svg)
        print("ok")
    except Exception as e2:
        print(f"svg_failed: {e2}", file=sys.stderr)
        sys.exit(1)
PYEOF
    svg_size=0
    [[ -f "$SVG_OUT" ]] && svg_size=$(wc -c < "$SVG_OUT" | tr -d ' ')
    if [[ $rc -eq 0 && ${svg_size:-0} -gt 100 ]]; then
        emit_result "tui_svg_snapshot" "PASS" \
            "Textual export_screenshot produced ${svg_size}-byte SVG" \
            "{\"bytes\":$svg_size,\"file\":\"tui_snapshot.svg\"}"
        _sub_pass
    else
        emit_result "tui_svg_snapshot" "FAIL" \
            "SVG snapshot failed (rc=$rc, bytes=${svg_size:-0})" \
            "{\"rc\":$rc,\"bytes\":${svg_size:-0}}"
    fi
} || true

# ── Step E: golden diff ───────────────────────────────────────────────────────
{
    CURRENT_SVG="$RESULTS_DIR/tui_snapshot.svg"
    GOLDEN_SVG="$SNAPSHOTS_DIR/tui_snapshot_golden.svg"
    if [[ ! -f "$GOLDEN_SVG" ]]; then
        emit_result "tui_golden_diff" "NOT_RUN" \
            "No golden snapshot exists yet in baseline/snapshots/; baseline update is a separate flow" "{}"
    elif [[ ! -f "$CURRENT_SVG" ]]; then
        emit_result "tui_golden_diff" "NOT_RUN" \
            "Current SVG snapshot was not produced (step D failed); cannot diff" "{}"
    else
        diff_out="$RESULTS_DIR/tui_golden_diff.txt"
        rc=0
        diff "$GOLDEN_SVG" "$CURRENT_SVG" >"$diff_out" 2>&1 || rc=$?
        if [[ $rc -eq 0 ]]; then
            emit_result "tui_golden_diff" "PASS" \
                "Current SVG matches golden snapshot exactly" "{}"
            _sub_pass
        else
            diff_lines=$(wc -l < "$diff_out" | tr -d ' ')
            emit_result "tui_golden_diff" "FAIL" \
                "SVG differs from golden (${diff_lines} diff lines); review $diff_out" \
                "{\"diff_lines\":$diff_lines}"
        fi
    fi
} || true

# ── Step F: ui-dashboard npm build (BETA-UI-01: build may be broken) ──────────
{
    PKG_JSON="${ROOT}/ui-dashboard/package.json"
    if [[ ! -f "$PKG_JSON" ]]; then
        emit_result "tui_ui_dashboard_build" "NOT_RUN" \
            "ui-dashboard/package.json not found; BETA-UI-01 unresolved or directory absent" "{}"
    else
        rc=0
        BUILD_LOG="$RESULTS_DIR/ui_dashboard_build.log"
        npm run build --prefix "${ROOT}/ui-dashboard" >"$BUILD_LOG" 2>&1 || rc=$?
        if [[ $rc -eq 0 ]]; then
            emit_result "tui_ui_dashboard_build" "PASS" \
                "ui-dashboard npm build succeeded" "{}"
            _sub_pass
        else
            emit_result "tui_ui_dashboard_build" "FAIL" \
                "ui-dashboard npm build failed (rc=$rc); see ui_dashboard_build.log" \
                "{\"rc\":$rc}"
        fi
    fi
} || true

# ── Overall rollup ────────────────────────────────────────────────────────────
if [[ $PASS_COUNT -ge 2 ]]; then
    emit_result "tui_renders_overall" "PASS" \
        "${PASS_COUNT} sub-steps PASSED (threshold: 2)" \
        "{\"pass_count\":$PASS_COUNT}"
else
    emit_result "tui_renders_overall" "FAIL" \
        "Only ${PASS_COUNT} sub-steps PASSED (threshold: 2)" \
        "{\"pass_count\":$PASS_COUNT}"
fi
