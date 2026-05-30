#!/usr/bin/env python3
"""
qa/scenarios/80_docs_drift.py — Extract commands/ports from key docs and verify
they resolve against the running QA environment.

Sub-results emitted:
    docs_commands_<docname>  — per-doc safe-command execution results
    docs_drift_overall       — aggregate PASS/FAIL

Docs checked (found by glob under ROOT):
    quickstart.md, cheat-sheet.md, troubleshooting.md

For each doc:
  - Extracts shell commands ($ prefix or bash/sh fenced blocks)
  - Filters to read-only commands: dopemux health/--help/doctor, curl http://
  - Runs each safe command with a 10s timeout
  - Checks extracted port numbers against known compose.yml port mapping

Exits 0 in all cases; PASS/FAIL/NOT_RUN are encoded in result JSONL.
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
from qa_common import emit_result, log, scenario_start  # noqa: E402

# ── Env defaults ──────────────────────────────────────────────────────────────
os.environ.setdefault("RESULTS_DIR", str(QA_DIR / "results"))
os.environ.setdefault(
    "RESULTS_FILE",
    str(Path(os.environ["RESULTS_DIR"]) / "results.jsonl"),
)
os.environ.setdefault("COMPOSE_PROJECT_NAME", "dopemux-qa")
os.environ.setdefault("RUN_ID", time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))

Path(os.environ["RESULTS_DIR"]).mkdir(parents=True, exist_ok=True)

# ── Known compose.yml port mapping (QA ports +40 from defaults) ──────────────
# Format: port_number -> service_description
KNOWN_PORTS: dict[int, str] = {
    # Default (live) ports
    5432:  "postgres (live)",
    6379:  "redis-events (live)",
    6380:  "redis-primary (live)",
    3004:  "conport-http (live)",
    3005:  "conport-mcp (live)",
    4004:  "conport-info (live)",
    3003:  "pal (live)",
    4000:  "litellm (live)",
    3010:  "dope-context (live)",
    6333:  "qdrant (live)",
    6334:  "qdrant-grpc (live)",
    8081:  "redis-ui (live)",
    8080:  "leantime (live)",
    # QA ports (+40)
    5472:  "postgres (qa)",
    6419:  "redis-events (qa)",
    6420:  "redis-primary (qa)",
    3044:  "conport-http (qa)",
    3045:  "conport-mcp (qa)",
    3043:  "pal (qa)",
    4040:  "litellm (qa)",
    3050:  "dope-context (qa)",
    6373:  "qdrant (qa)",
    6374:  "qdrant-grpc (qa)",
    8120:  "leantime (qa)",
    # Common instance ports derived from base 3000 + 30*n
    3000:  "instance-A",
    3030:  "instance-B",
    3060:  "instance-C",
    3090:  "instance-D",
    3120:  "instance-E",
    # Standard ports
    80:    "http",
    443:   "https",
    22:    "ssh",
}

# ── Docs to search for ────────────────────────────────────────────────────────
TARGET_DOCS = ["quickstart.md", "cheat-sheet.md", "troubleshooting.md"]

# ── Safe command prefixes (read-only, no state mutation) ─────────────────────
SAFE_COMMAND_PATTERNS: list[re.Pattern] = [
    re.compile(r"^dopemux\s+(health|--help|-h|doctor|instances\s+list|worktrees\s+list|mcp\s+list|cockpit\s+list|decisions|status)\b"),
    re.compile(r"^dopemux\s+--help\b"),
    re.compile(r"^curl\s+http://"),
    re.compile(r"^curl\s+-[a-zA-Z]*\s+http://"),
]


def find_docs() -> dict[str, Path]:
    """
    Search ROOT tree (max depth 4) for each target doc.
    Returns mapping name -> path for docs that are found.
    """
    found: dict[str, Path] = {}
    for target in TARGET_DOCS:
        matches = list(ROOT.rglob(target))
        # Prefer docs/ subtree; fall back to any match
        docs_matches = [p for p in matches if "docs" in str(p)]
        chosen = docs_matches[0] if docs_matches else (matches[0] if matches else None)
        if chosen:
            found[target] = chosen
            log("INFO", f"Found doc: {target} → {chosen.relative_to(ROOT)}")
        else:
            log("WARN", f"Doc not found: {target}")
    return found


def extract_shell_commands(text: str) -> list[str]:
    """
    Extract shell command candidates from markdown text.

    Strategies:
      1. Lines starting with '$ ' (shell prompt)
      2. Lines inside ```bash, ```sh, ```shell, ```console fenced blocks
    """
    commands: list[str] = []

    # Strategy 1: lines starting with '$ '
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("$ "):
            cmd = stripped[2:].strip()
            if cmd:
                commands.append(cmd)

    # Strategy 2: fenced code blocks
    fence_pattern = re.compile(
        r"```(?:bash|sh|shell|console|zsh)\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    for block in fence_pattern.findall(text):
        for line in block.splitlines():
            stripped = line.strip()
            # Skip blank lines, comments, variable assignments
            if not stripped or stripped.startswith("#") or "=" in stripped.split()[0] if stripped.split() else False:
                continue
            # Remove leading '$ ' if present inside fenced blocks
            if stripped.startswith("$ "):
                stripped = stripped[2:].strip()
            if stripped:
                commands.append(stripped)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for c in commands:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def is_safe_command(cmd: str) -> bool:
    """Return True if the command matches a known read-only safe pattern."""
    for pattern in SAFE_COMMAND_PATTERNS:
        if pattern.match(cmd):
            return True
    return False


def run_safe_command(cmd: str, timeout: int = 10) -> dict[str, Any]:
    """
    Run a safe command via shell and return a result dict.
    Always uses shell=True since commands may include flags/pipes.
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,           # noqa: S602
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "command": cmd,
            "exit_code": result.returncode,
            "ok": result.returncode == 0,
            "failure_reason": None if result.returncode == 0 else f"exit {result.returncode}",
        }
    except subprocess.TimeoutExpired:
        return {
            "command": cmd,
            "exit_code": -1,
            "ok": False,
            "failure_reason": f"timeout after {timeout}s",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "command": cmd,
            "exit_code": -1,
            "ok": False,
            "failure_reason": str(exc),
        }


def extract_ports(text: str) -> list[int]:
    """
    Extract port numbers from text.
    Matches patterns like: :3004, port 5432, PORT=3003, localhost:8080, 0.0.0.0:6379
    """
    ports: set[int] = set()
    patterns = [
        re.compile(r":(\d{2,5})\b"),          # :NNNN
        re.compile(r"\bport\s+(\d{2,5})\b", re.IGNORECASE),
        re.compile(r"\bPORT[=_](\d{2,5})\b"),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            try:
                port = int(match.group(1))
                if 80 <= port <= 65535:
                    ports.add(port)
            except ValueError:
                pass
    return sorted(ports)


def check_doc(doc_name: str, doc_path: Path) -> tuple[str, str, dict[str, Any]]:
    """
    Process one doc file.

    Returns (scenario_name, status, evidence).
    """
    scenario_name = f"docs_commands_{doc_name.replace('.', '_').replace('-', '_')}"
    log("INFO", f"Processing doc: {doc_name} ({doc_path})")

    try:
        text = doc_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return scenario_name, "FAIL", {"error": str(exc), "doc": str(doc_path)}

    # Extract and filter commands
    all_commands = extract_shell_commands(text)
    safe_commands = [c for c in all_commands if is_safe_command(c)]
    unsafe_commands = [c for c in all_commands if not is_safe_command(c)]

    log("INFO", f"  Commands found: {len(all_commands)} total, {len(safe_commands)} safe, {len(unsafe_commands)} skipped")

    # Run safe commands
    cmd_results: list[dict[str, Any]] = []
    for cmd in safe_commands:
        log("INFO", f"  Running: {cmd}")
        r = run_safe_command(cmd)
        cmd_results.append(r)
        if r["ok"]:
            log("INFO", f"    exit 0 OK")
        else:
            log("ERROR", f"    FAIL: {r['failure_reason']}")

    failed_commands = [r for r in cmd_results if not r["ok"]]

    # Extract and check ports
    ports_found = extract_ports(text)
    ports_unknown = [p for p in ports_found if p not in KNOWN_PORTS]
    log("INFO", f"  Ports found: {ports_found}, unknown: {ports_unknown}")

    evidence: dict[str, Any] = {
        "doc": str(doc_path.relative_to(ROOT)),
        "commands_found": len(all_commands),
        "commands_safe": len(safe_commands),
        "commands_skipped_unsafe": len(unsafe_commands),
        "commands_checked": len(cmd_results),
        "commands_failed": [
            {"command": r["command"], "reason": r["failure_reason"]}
            for r in failed_commands
        ],
        "ports_found": ports_found,
        "ports_known": [p for p in ports_found if p in KNOWN_PORTS],
        "ports_unknown": ports_unknown,
    }

    if not cmd_results and not ports_found:
        return scenario_name, "NOT_RUN", {**evidence, "reason": "no_safe_commands_or_ports_found"}

    if failed_commands or ports_unknown:
        status = "FAIL"
    else:
        status = "PASS"

    return scenario_name, status, evidence


def main() -> None:
    scenario_start("docs_drift")

    # ── Find target docs ───────────────────────────────────────────────────────
    docs = find_docs()

    all_statuses: list[str] = []
    not_found: list[str] = []

    for target in TARGET_DOCS:
        if target not in docs:
            not_found.append(target)
            scenario_name = f"docs_commands_{target.replace('.', '_').replace('-', '_')}"
            emit_result(
                scenario_name,
                "NOT_RUN",
                f"Doc not found: {target} (searched under {ROOT})",
                {"doc": target, "reason": "file_not_found"},
            )
            all_statuses.append("NOT_RUN")
            continue

        sc_name, status, evidence = check_doc(target, docs[target])

        msg_parts = []
        if evidence.get("commands_checked", 0) > 0:
            n_fail = len(evidence.get("commands_failed", []))
            n_ok = evidence["commands_checked"] - n_fail
            msg_parts.append(f"commands: {n_ok}/{evidence['commands_checked']} OK")
        if evidence.get("ports_unknown"):
            msg_parts.append(f"unknown ports: {evidence['ports_unknown']}")
        if not msg_parts:
            msg_parts.append("no safe commands or ports found")

        emit_result(sc_name, status, "; ".join(msg_parts), evidence)
        all_statuses.append(status)

    # ── Aggregate result ───────────────────────────────────────────────────────
    if all(s == "NOT_RUN" for s in all_statuses):
        overall_status = "NOT_RUN"
        overall_msg = f"All target docs not found: {not_found}"
    elif any(s == "FAIL" for s in all_statuses):
        overall_status = "FAIL"
        fail_docs = [
            t for t, s in zip(TARGET_DOCS, all_statuses) if s == "FAIL"
        ]
        overall_msg = f"Docs with failures: {fail_docs}"
    else:
        overall_status = "PASS"
        found_docs = [t for t in TARGET_DOCS if t in docs]
        overall_msg = (
            f"All checked docs clean "
            f"({len(found_docs)} found, {len(not_found)} not found)"
        )

    emit_result(
        "docs_drift_overall",
        overall_status,
        overall_msg,
        {
            "docs_found": list(docs.keys()),
            "docs_not_found": not_found,
            "per_doc_statuses": dict(zip(TARGET_DOCS, all_statuses)),
        },
    )


if __name__ == "__main__":
    main()
