"""
qa/lib/qa_common.py — Shared Python library for dopemux-qa scenario scripts.

Import at the top of Python scenario scripts:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
    from qa_common import emit_result, run_cmd, assert_exit0, health_poll, log

Expected env vars (set by runner or qa env):
    ROOT, RUN_ID, RESULTS_DIR, RESULTS_FILE, QA_ENV_FILE, QA_NETWORK,
    COMPOSE_PROJECT_NAME
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Color codes ────────────────────────────────────────────────────────────────
_RESET  = "\033[0m"
_RED    = "\033[0;31m"
_YELLOW = "\033[0;33m"
_CYAN   = "\033[0;36m"
_GREEN  = "\033[0;32m"

# ── Module-level scenario state ────────────────────────────────────────────────
_current_scenario: str = "unknown"
_scenario_start: float = time.monotonic()


def scenario_start(name: str) -> None:
    """Set current scenario name and reset start time."""
    global _current_scenario, _scenario_start
    _current_scenario = name
    _scenario_start = time.monotonic()
    log("INFO", f"=== scenario: {name} ===")


# ── Logging ────────────────────────────────────────────────────────────────────
def log(level: str, msg: str) -> None:
    """Write a colored log line to stderr."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    colors = {
        "INFO":  _CYAN,
        "WARN":  _YELLOW,
        "ERROR": _RED,
        "PASS":  _GREEN,
    }
    color = colors.get(level.upper(), _RESET)
    tag = f"{level.upper()[:5]:5s}"
    print(f"{color}[{tag}]{_RESET} {ts} {msg}", file=sys.stderr)


# ── Results file resolution ────────────────────────────────────────────────────
def get_results_file() -> Path:
    """Return the Path for results output (from RESULTS_FILE env or default)."""
    rf = os.environ.get("RESULTS_FILE")
    if rf:
        return Path(rf)
    return Path("results") / "default" / "results.jsonl"


# ── Result emission ────────────────────────────────────────────────────────────
def emit_result(
    scenario: str,
    status: str,
    message: str,
    evidence: dict[str, Any] | None = None,
    results_file: Path | str | None = None,
) -> None:
    """
    Write one JSON result line atomically to the results file.

    status must be one of: PASS | FAIL | NOT_RUN
    """
    if evidence is None:
        evidence = {}

    rf = Path(results_file) if results_file else get_results_file()
    rf.parent.mkdir(parents=True, exist_ok=True)

    duration_s = round(time.monotonic() - _scenario_start, 3)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    record = {
        "scenario":   scenario,
        "status":     status,
        "message":    message,
        "evidence":   evidence,
        "timestamp":  timestamp,
        "duration_s": duration_s,
    }
    line = json.dumps(record, separators=(",", ":")) + "\n"

    # Atomic append via temp file
    try:
        fd, tmp_path = tempfile.mkstemp(dir=rf.parent, prefix=rf.name + ".")
        try:
            with os.fdopen(fd, "w") as f:
                f.write(line)
            with open(rf, "a") as out, open(tmp_path, "r") as inp:
                out.write(inp.read())
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    except OSError:
        # Fallback: direct append
        with open(rf, "a") as f:
            f.write(line)

    _log_result(status, scenario, message)


def _log_result(status: str, scenario: str, message: str) -> None:
    level_map = {"PASS": "PASS", "FAIL": "ERROR", "NOT_RUN": "WARN"}
    log(level_map.get(status, "INFO"), f"{scenario} — {message}")


# ── run_cmd ────────────────────────────────────────────────────────────────────
def run_cmd(
    args: list[str],
    timeout: int = 30,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a subprocess and return CompletedProcess.
    Raises subprocess.CalledProcessError if check=True and rc != 0.
    """
    kwargs: dict[str, Any] = {
        "timeout": timeout,
        "check":   check,
    }
    if capture:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
        kwargs["text"]   = True

    return subprocess.run(args, **kwargs)  # noqa: S603


# ── assert_exit0 ───────────────────────────────────────────────────────────────
def assert_exit0(
    label: str,
    args: list[str],
    timeout: int = 30,
    scenario: str | None = None,
) -> bool:
    """
    Run command; emit FAIL result if exit code is non-zero.
    Returns True on success, False on failure.
    """
    sc = scenario or _current_scenario
    try:
        result = run_cmd(args, timeout=timeout, check=False, capture=True)
        if result.returncode != 0:
            snippet = (result.stdout or result.stderr or "")[:300].replace("\n", " ")
            emit_result(sc, "FAIL", f"{label} — exit {result.returncode}: {snippet}")
            return False
        log("INFO", f"assert_exit0 OK: {label}")
        return True
    except subprocess.TimeoutExpired:
        emit_result(sc, "FAIL", f"{label} — timed out after {timeout}s")
        return False
    except Exception as exc:  # noqa: BLE001
        emit_result(sc, "FAIL", f"{label} — exception: {exc}")
        return False


# ── assert_json_schema ─────────────────────────────────────────────────────────
def assert_json_schema(
    label: str,
    data: dict[str, Any],
    required_keys: list[str],
    scenario: str | None = None,
) -> bool:
    """
    Verify all required_keys are present in data dict.
    Emits FAIL result if any are missing.
    Returns True if all present.
    """
    sc = scenario or _current_scenario
    missing = [k for k in required_keys if k not in data]
    if missing:
        emit_result(sc, "FAIL", f"{label} — missing keys: {missing}")
        return False
    log("INFO", f"assert_json_schema OK: {label}")
    return True


# ── health_poll ────────────────────────────────────────────────────────────────
def health_poll(url: str, retries: int = 20, interval: int = 3) -> bool:
    """
    Poll url until HTTP 200 or retries exhausted.
    Returns True if healthy, False on timeout.
    """
    import urllib.error
    import urllib.request

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310
                if resp.status == 200:
                    log("INFO", f"health_poll OK ({url}) after {attempt} attempt(s)")
                    return True
                log("INFO", f"health_poll {url} → {resp.status} (attempt {attempt}/{retries})")
        except Exception as exc:  # noqa: BLE001
            log("INFO", f"health_poll {url} → error: {exc} (attempt {attempt}/{retries})")
        if attempt < retries:
            time.sleep(interval)

    log("ERROR", f"health_poll TIMEOUT: {url} did not return 200 after {retries} attempts")
    return False


# ── Guard: QA compose project ─────────────────────────────────────────────────
def guard_qa_project() -> None:
    """Abort if COMPOSE_PROJECT_NAME is not 'dopemux-qa'."""
    project = os.environ.get("COMPOSE_PROJECT_NAME", "")
    if project != "dopemux-qa":
        log("ERROR", f"COMPOSE_PROJECT_NAME='{project}' — must be 'dopemux-qa'. Refusing to continue.")
        sys.exit(1)


# ── require_env ────────────────────────────────────────────────────────────────
def require_env(*vars_: str) -> None:
    """Exit 1 if any of the named environment variables are unset or empty."""
    missing = [v for v in vars_ if not os.environ.get(v)]
    if missing:
        for v in missing:
            log("ERROR", f"Required env var '{v}' is unset or empty.")
        sys.exit(1)


# ── CLI entrypoint ────────────────────────────────────────────────────────────
def synthesize_report(results_dir: str) -> None:
    """Read results.jsonl from *results_dir* and write report.md."""
    import json as _json
    from pathlib import Path as _Path

    rdir = _Path(results_dir)
    rdir.mkdir(parents=True, exist_ok=True)
    jsonl_path = rdir / "results.jsonl"
    report_path = rdir / "report.md"

    if not jsonl_path.exists():
        log("WARN", f"No results.jsonl found at {jsonl_path} — writing empty report.")
        report_path.write_text("# QA Run Report\n\n_No results recorded._\n")
        return

    rows: list[dict] = []
    for line in jsonl_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(_json.loads(line))
        except _json.JSONDecodeError:
            continue

    counts: dict[str, int] = {"PASS": 0, "FAIL": 0, "NOT_RUN": 0}
    for r in rows:
        status = r.get("status", "").upper()
        counts[status] = counts.get(status, 0) + 1

    total = len(rows)
    lines = [
        "# QA Run Report",
        "",
        f"**Results dir:** `{results_dir}`  ",
        f"**Total:** {total}  "
        f"| ✅ PASS: {counts.get('PASS', 0)}"
        f"  ❌ FAIL: {counts.get('FAIL', 0)}"
        f"  ⏭ NOT_RUN: {counts.get('NOT_RUN', 0)}",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Status | Message |",
        "|----------|--------|---------|",
    ]
    for r in rows:
        scenario = r.get("scenario", "?")
        status = r.get("status", "?")
        message = r.get("message", "")[:120].replace("|", "\\|")
        icon = {"PASS": "✅", "FAIL": "❌", "NOT_RUN": "⏭"}.get(status.upper(), "❓")
        lines.append(f"| `{scenario}` | {icon} {status} | {message} |")

    lines += ["", "---", "_Generated by qa/lib/qa_common.py synthesize_report_", ""]
    report_path.write_text("\n".join(lines))
    log("INFO", f"Report written to {report_path}")


if __name__ == "__main__":
    import argparse as _argparse

    parser = _argparse.ArgumentParser(description="qa_common CLI helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sr = sub.add_parser("synthesize_report", help="Generate report.md from results.jsonl")
    sr.add_argument("results_dir", help="Path to results/<run-id>/ directory")

    ub = sub.add_parser("update_baseline", help="Update baseline.json from a results dir")
    ub.add_argument("results_dir")
    ub.add_argument("baseline_file")

    args = parser.parse_args()

    if args.cmd == "synthesize_report":
        synthesize_report(args.results_dir)
    elif args.cmd == "update_baseline":
        log("INFO", f"update_baseline: {args.results_dir} → {args.baseline_file} (stub)")
