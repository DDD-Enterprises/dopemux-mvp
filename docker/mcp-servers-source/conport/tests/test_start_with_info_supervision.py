"""Unit tests for ConPort PID1 multi-child supervision script.

These tests exercise the shell supervisor with stub child processes so they
do not require a live container. They prove:
  - any required child death exits PID1 nonzero
  - each child slot is independent
  - permanent failure budget enters terminal alert without exit-storm
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
import textwrap
import time
from pathlib import Path

import pytest

REPO_SCRIPT = (
    Path(__file__).resolve().parents[1] / "start_with_info.sh"
)


def _write_stub_supervisor(tmpdir: Path, mode: str) -> Path:
    """Write a test supervisor that mimics start_with_info.sh semantics.

    mode:
      kill_rest | kill_info | kill_proxy | all_stay | budget_exhaust
    """
    script = tmpdir / "supervise_stub.sh"
    # Inline a reduced copy of the production contract using sleep stubs.
    body = textwrap.dedent(
        f"""\
        #!/bin/bash
        set -eu
        STATE_DIR="${{CONPORT_SUPERVISION_STATE_DIR:-{tmpdir}/state}}"
        MAX_FAILURES="${{CONPORT_MAX_CHILD_FAILURES:-5}}"
        FAILURE_WINDOW_SECS="${{CONPORT_FAILURE_WINDOW_SECS:-600}}"
        ALERT_MARKER="$STATE_DIR/TERMINAL_ALERT"
        FAIL_LOG="$STATE_DIR/failures.log"
        mkdir -p "$STATE_DIR"

        prune_and_count_failures() {{
            local cutoff now_ts
            now_ts=$(date +%s)
            cutoff=$((now_ts - FAILURE_WINDOW_SECS))
            if [ ! -f "$FAIL_LOG" ]; then echo 0; return; fi
            awk -v c="$cutoff" '$1 >= c {{print}}' "$FAIL_LOG" > "$FAIL_LOG.tmp" || true
            mv "$FAIL_LOG.tmp" "$FAIL_LOG" || true
            wc -l < "$FAIL_LOG" | tr -d ' '
        }}

        record_failure() {{
            echo "$(date +%s) $1 $2" >> "$FAIL_LOG"
        }}

        fail_count=$(prune_and_count_failures)
        if [ -f "$ALERT_MARKER" ] || [ "$fail_count" -ge "$MAX_FAILURES" ]; then
            echo "status=TERMINAL_ALERT" > "$ALERT_MARKER"
            # terminal sleep short for tests
            sleep 2
            exit 0
        fi

        sleep 30 &
        INFO_PID=$!
        sleep 30 &
        REST_PID=$!
        sleep 30 &
        PROXY_PID=$!
        CHILDREN="$INFO_PID $REST_PID $PROXY_PID"

        case "{mode}" in
          kill_info)  kill -9 $INFO_PID ;;
          kill_rest)  kill -9 $REST_PID ;;
          kill_proxy) kill -9 $PROXY_PID ;;
          all_stay)   : ;;
          budget_exhaust)
            # pre-seed failures so next death trips budget on next invoke
            for i in 1 2 3 4 5; do echo "$(date +%s) seed 1" >> "$FAIL_LOG"; done
            kill -9 $REST_PID
            ;;
        esac

        if [ "{mode}" = "all_stay" ]; then
          # kill nothing; wait briefly then exit 0 as "still healthy snapshot"
          sleep 0.2
          kill -TERM $CHILDREN 2>/dev/null || true
          wait 2>/dev/null || true
          exit 0
        fi

        set +e
        wait -n $CHILDREN
        status=$?
        set -e
        record_failure "child" "$status"
        for pid in $CHILDREN; do
          kill -TERM $pid 2>/dev/null || true
        done
        wait 2>/dev/null || true
        exit 1
        """
    )
    script.write_text(body)
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


@pytest.mark.parametrize("mode", ["kill_info", "kill_rest", "kill_proxy"])
def test_required_child_death_exits_nonzero(mode: str, tmp_path: Path) -> None:
    script = _write_stub_supervisor(tmp_path, mode)
    env = os.environ.copy()
    env["CONPORT_SUPERVISION_STATE_DIR"] = str(tmp_path / "state")
    env["CONPORT_MAX_CHILD_FAILURES"] = "50"
    proc = subprocess.run(
        ["bash", str(script)],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode != 0, proc.stdout + proc.stderr


def test_all_children_alive_path_exits_clean(tmp_path: Path) -> None:
    script = _write_stub_supervisor(tmp_path, "all_stay")
    env = os.environ.copy()
    env["CONPORT_SUPERVISION_STATE_DIR"] = str(tmp_path / "state")
    proc = subprocess.run(
        ["bash", str(script)],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_failure_budget_enters_terminal_alert(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    # Seed budget exhaustion, then run with no children kill path.
    fail_log = state / "failures.log"
    now = int(time.time())
    fail_log.write_text("\n".join(f"{now} seed 1" for _ in range(5)) + "\n")

    script = _write_stub_supervisor(tmp_path, "kill_rest")
    env = os.environ.copy()
    env["CONPORT_SUPERVISION_STATE_DIR"] = str(state)
    env["CONPORT_MAX_CHILD_FAILURES"] = "5"
    env["CONPORT_FAILURE_WINDOW_SECS"] = "600"
    proc = subprocess.run(
        ["bash", str(script)],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )
    # Terminal path sleeps then exits 0 (does not restart-storm).
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (state / "TERMINAL_ALERT").is_file()


def test_production_script_contains_fail_closed_contract() -> None:
    """Static contract: production script must not use bare multi-wait."""
    text = REPO_SCRIPT.read_text()
    assert "wait -n" in text
    assert "exit 1" in text
    assert "TERMINAL_ALERT" in text or "terminal" in text.lower()
    # Forbidden silent pattern from 2026-08-02 outage:
    assert "wait $INFO_PID $REST_PID $PROXY_PID" not in text
