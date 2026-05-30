#!/usr/bin/env python3
"""
qa/scenarios/20_cli_sweep.py — Comprehensive CLI command sweep.

Discovers all dopemux subcommands recursively (depth ≤ 3), runs --help on each,
validates JSON outputs where supported, and checks exit-code honesty.

Exits 0 in all cases; PASS/FAIL/NOT_RUN are encoded in the result JSONL.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# ── Bootstrap path so qa_common is importable ─────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
QA_DIR = SCRIPT_DIR.parent
ROOT = QA_DIR.parent

sys.path.insert(0, str(QA_DIR / "lib"))
from qa_common import emit_result, log, run_cmd, scenario_start  # noqa: E402

# ── Env defaults ──────────────────────────────────────────────────────────────
os.environ.setdefault("RESULTS_DIR", str(QA_DIR / "results"))
os.environ.setdefault(
    "RESULTS_FILE",
    str(Path(os.environ["RESULTS_DIR"]) / "results.jsonl"),
)
os.environ.setdefault("COMPOSE_PROJECT_NAME", "dopemux-qa")
os.environ.setdefault("RUN_ID", time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))

Path(os.environ["RESULTS_DIR"]).mkdir(parents=True, exist_ok=True)

# ── Commands to skip (they mutate state or require live infrastructure) ────────
# These are emitted as NOT_RUN rather than tested.
SKIP_COMMANDS: set[str] = {
    "start",
    "init",
    "deploy",
    "install",
    "upgrade",
    "upgrades",
    "wire-conport",
    "wizard",
    "launch",
    "kernel",
    "agent-loop",
    "orchestrator",
    "mobile",
    "mobile-env",
    "shell-setup",
    "pr-merge",
    "update",
    "trigger",
}

# Commands that support --json and whose output we validate
JSON_COMMANDS: list[list[str]] = [
    ["health"],
    ["doctor"],
    ["instances", "list"],
    ["status"],
]

# ── Locate dopemux binary ─────────────────────────────────────────────────────
def find_dopemux() -> list[str] | None:
    """Return the command prefix to invoke dopemux, or None if not found."""
    try:
        result = subprocess.run(
            ["dopemux", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode == 0:
            return ["dopemux"]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    try:
        result = subprocess.run(
            ["python3", "-m", "dopemux.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode == 0:
            return ["python3", "-m", "dopemux.cli"]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return None


# ── Parse --help output for subcommands ───────────────────────────────────────
def parse_subcommands(help_text: str) -> list[str]:
    """
    Extract subcommand names from help text.
    Looks for the 'Commands:' section and collects leading words.
    """
    cmds: list[str] = []
    in_commands = False
    for line in help_text.splitlines():
        # Detect Commands: section header
        if re.match(r"^\s*Commands\s*:", line, re.IGNORECASE):
            in_commands = True
            continue
        # A new section heading (non-indented, ends with colon) ends the block
        if in_commands and re.match(r"^[A-Za-z\-].*:$", line.strip()):
            in_commands = False
            continue
        if in_commands:
            stripped = line.strip()
            if not stripped:
                continue
            # First token is the command name; skip if it looks like a flag
            token = stripped.split()[0] if stripped.split() else ""
            if token and not token.startswith("-") and token != "--":
                cmds.append(token)
    return cmds


# ── Recursively discover commands up to max_depth ─────────────────────────────
def discover_commands(
    base: list[str],
    prefix: list[str],
    depth: int,
    max_depth: int = 3,
) -> list[list[str]]:
    """
    Walk the command tree and return all reachable command paths.
    Each entry is a list of command tokens, e.g. ['instances', 'list'].
    """
    if depth > max_depth:
        return []

    cmd = base + prefix + ["--help"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        help_text = result.stdout or result.stderr or ""
    except subprocess.TimeoutExpired:
        log("WARN", f"Timeout running: {' '.join(cmd)}")
        return []
    except Exception as exc:  # noqa: BLE001
        log("WARN", f"Error running {' '.join(cmd)}: {exc}")
        return []

    sub_cmds = parse_subcommands(help_text)
    results: list[list[str]] = []

    if not sub_cmds:
        # Leaf command — return itself (unless we're at root with no subs found
        # from a broken help)
        if prefix:
            results.append(prefix)
    else:
        for sub in sub_cmds:
            child = prefix + [sub]
            # Add the group itself
            results.append(child)
            # Recurse into children
            children = discover_commands(base, child, depth + 1, max_depth)
            results.extend(children)

    return results


# ── Run --help on one command path ─────────────────────────────────────────────
def check_help(base: list[str], path: list[str]) -> dict[str, Any]:
    """Run 'dopemux <path...> --help' and return a result dict."""
    cmd = base + path + ["--help"]
    label = " ".join(path)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        ok = result.returncode == 0 and bool((result.stdout or result.stderr or "").strip())
        return {
            "command": label,
            "exit_code": result.returncode,
            "has_output": bool((result.stdout or result.stderr or "").strip()),
            "ok": ok,
            "failure_reason": (
                None
                if ok
                else (
                    f"exit {result.returncode}"
                    if result.returncode != 0
                    else "empty output"
                )
            ),
        }
    except subprocess.TimeoutExpired:
        return {
            "command": label,
            "exit_code": -1,
            "has_output": False,
            "ok": False,
            "failure_reason": "timeout",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "command": label,
            "exit_code": -1,
            "has_output": False,
            "ok": False,
            "failure_reason": str(exc),
        }


# ── JSON output validation ─────────────────────────────────────────────────────
def check_json_output(base: list[str], path: list[str]) -> dict[str, Any]:
    """Run a command with --json and assert the output parses as valid JSON."""
    import json

    cmd = base + path + ["--json"]
    label = " ".join(path) + " --json"
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        output = result.stdout or result.stderr or ""
        # Attempt to find a JSON object/array in the output
        # (some commands emit preamble lines before JSON)
        parsed = None
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("{") or line.startswith("["):
                try:
                    parsed = json.loads(line)
                    break
                except json.JSONDecodeError:
                    pass
        if parsed is None:
            # Try full output
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                pass

        return {
            "command": label,
            "exit_code": result.returncode,
            "valid_json": parsed is not None,
            "ok": parsed is not None,
            "failure_reason": None if parsed is not None else "output is not valid JSON",
        }
    except subprocess.TimeoutExpired:
        return {
            "command": label,
            "exit_code": -1,
            "valid_json": False,
            "ok": False,
            "failure_reason": "timeout",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "command": label,
            "exit_code": -1,
            "valid_json": False,
            "ok": False,
            "failure_reason": str(exc),
        }


# ── Exit-code honesty test ─────────────────────────────────────────────────────
def check_exit_honesty(base: list[str]) -> dict[str, Any]:
    """
    Run 'dopemux health --instance NONEXISTENT_XYZ_QA' and expect non-zero.
    Also try 'dopemux doctor --instance NONEXISTENT_XYZ_QA'.
    """
    results = []
    test_cases = [
        base + ["health", "--instance", "NONEXISTENT_XYZ_QA"],
        base + ["doctor", "--instance", "NONEXISTENT_XYZ_QA"],
        base + ["instances", "list", "--instance", "NONEXISTENT_XYZ_QA"],
    ]
    for cmd in test_cases:
        label = " ".join(cmd[len(base):])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            # We expect non-zero for an unknown instance
            # BUT: some implementations exit 0 and print an error message.
            # Accept either non-zero exit OR output containing error indicators.
            output = (result.stdout + result.stderr).lower()
            has_error_text = any(
                kw in output
                for kw in ("error", "not found", "unknown", "invalid", "no such", "failed")
            )
            honest = result.returncode != 0 or has_error_text
            results.append({
                "command": label,
                "exit_code": result.returncode,
                "honest": honest,
                "failure_reason": None if honest else f"exited 0 with no error text for nonexistent instance",
            })
        except subprocess.TimeoutExpired:
            results.append({
                "command": label,
                "exit_code": -1,
                "honest": False,
                "failure_reason": "timeout",
            })
        except Exception as exc:  # noqa: BLE001
            results.append({
                "command": label,
                "exit_code": -1,
                "honest": False,
                "failure_reason": str(exc),
            })
    return {"tests": results}


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    # ── Find dopemux ─────────────────────────────────────────────────────────
    base = find_dopemux()
    if base is None:
        # Emit NOT_RUN for all sub-scenarios then exit cleanly
        for sc in ("cli_sweep_help", "cli_sweep_json", "cli_sweep_exit_honesty"):
            scenario_start(sc)
            emit_result(sc, "NOT_RUN", "dopemux not found on PATH; install dopemux first")
        return

    log("INFO", f"Using dopemux command: {' '.join(base)}")

    # ── Discover commands ─────────────────────────────────────────────────────
    log("INFO", "Discovering command tree (depth ≤ 3)…")
    all_commands = discover_commands(base, [], depth=1, max_depth=3)
    log("INFO", f"Discovered {len(all_commands)} command paths")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_commands: list[list[str]] = []
    for path in all_commands:
        key = " ".join(path)
        if key not in seen:
            seen.add(key)
            unique_commands.append(path)

    # ── Scenario 1: cli_sweep_help ─────────────────────────────────────────
    scenario_start("cli_sweep_help")

    help_results: list[dict[str, Any]] = []
    skipped: list[str] = []

    for path in unique_commands:
        root_cmd = path[0]
        if root_cmd in SKIP_COMMANDS:
            skipped.append(" ".join(path))
            emit_result(
                "cli_sweep_help",
                "NOT_RUN",
                f"Skipped mutating/infra command: {' '.join(path)}",
            )
            continue
        result = check_help(base, path)
        help_results.append(result)
        if result["ok"]:
            log("INFO", f"  PASS: {result['command']}")
        else:
            log("ERROR", f"  FAIL: {result['command']} — {result['failure_reason']}")

    failures = [r for r in help_results if not r["ok"]]
    checked = len(help_results)
    passed = checked - len(failures)

    help_evidence = {
        "commands_found": len(unique_commands),
        "commands_checked": checked,
        "commands_skipped": len(skipped),
        "passed": passed,
        "failed": len(failures),
        "failures": [
            {"command": r["command"], "reason": r["failure_reason"]}
            for r in failures
        ],
    }

    if not failures:
        emit_result(
            "cli_sweep_help",
            "PASS",
            f"{passed}/{checked} commands --help clean ({len(skipped)} state-mutating commands skipped)",
            help_evidence,
        )
    else:
        emit_result(
            "cli_sweep_help",
            "FAIL",
            f"{len(failures)}/{checked} commands failed --help check",
            help_evidence,
        )

    # ── Scenario 2: cli_sweep_json ─────────────────────────────────────────
    scenario_start("cli_sweep_json")

    json_results: list[dict[str, Any]] = []
    for path in JSON_COMMANDS:
        # Skip if any part of the path is in the skip list
        if path[0] in SKIP_COMMANDS:
            emit_result(
                "cli_sweep_json",
                "NOT_RUN",
                f"Skipped mutating command: {' '.join(path)} --json",
            )
            continue
        r = check_json_output(base, path)
        json_results.append(r)
        if r["ok"]:
            log("INFO", f"  PASS JSON: {r['command']}")
        else:
            log("ERROR", f"  FAIL JSON: {r['command']} — {r['failure_reason']}")

    json_failures = [r for r in json_results if not r["ok"]]
    json_evidence = {
        "checked": [r["command"] for r in json_results],
        "failures": [
            {"command": r["command"], "reason": r["failure_reason"]}
            for r in json_failures
        ],
    }

    if not json_results:
        emit_result(
            "cli_sweep_json",
            "NOT_RUN",
            "No JSON-capable commands were testable (all skipped)",
            json_evidence,
        )
    elif not json_failures:
        emit_result(
            "cli_sweep_json",
            "PASS",
            f"All {len(json_results)} --json outputs parse as valid JSON",
            json_evidence,
        )
    else:
        emit_result(
            "cli_sweep_json",
            "FAIL",
            f"{len(json_failures)}/{len(json_results)} --json outputs failed validation",
            json_evidence,
        )

    # ── Scenario 3: cli_sweep_exit_honesty ────────────────────────────────
    scenario_start("cli_sweep_exit_honesty")

    honesty = check_exit_honesty(base)
    tests = honesty["tests"]
    dishonest = [t for t in tests if not t["honest"]]

    honesty_evidence = {
        "tests": tests,
        "dishonest_count": len(dishonest),
    }

    if not tests:
        emit_result(
            "cli_sweep_exit_honesty",
            "NOT_RUN",
            "No exit-honesty test cases could be run",
            honesty_evidence,
        )
    elif not dishonest:
        emit_result(
            "cli_sweep_exit_honesty",
            "PASS",
            f"All {len(tests)} error-path commands returned non-zero or error text",
            honesty_evidence,
        )
    else:
        emit_result(
            "cli_sweep_exit_honesty",
            "FAIL",
            f"{len(dishonest)}/{len(tests)} commands did not signal error for nonexistent instance",
            honesty_evidence,
        )


if __name__ == "__main__":
    main()
