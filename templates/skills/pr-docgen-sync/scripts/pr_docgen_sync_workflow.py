#!/usr/bin/env python3
"""Deterministic workflow helper for the pr-docgen-sync skill."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import yaml


CANONICAL_INDEXES: List[str] = [
    "docs/docs_index.yaml",
    "docs/00-MASTER-INDEX.md",
    "docs/INDEX.md",
    "docs/01-tutorials/overview.md",
    "docs/02-how-to/overview.md",
    "docs/03-reference/overview.md",
    "docs/04-explanation/overview.md",
    "docs/03-reference/documentation-catalog.md",
]

DEFAULT_LEDGER_PATH = "docs/planes/pm/task-orchestrator-leantime-followups.md"
DEFAULT_LAYOUT_REPORT_PATH = "reports/docs-hygiene/pr-docgen-sync-layout-findings.json"

INSTRUCTION_PATH_CANDIDATES: Dict[str, Tuple[str, ...]] = {
    "codex": (
        "docs/03-reference/instructions/CODEX.md",
        "docs/instructions/codex-2.md",
    ),
    "claude": (
        "docs/03-reference/instructions/CLAUDE.md",
        "docs/instructions/claude-2.md",
    ),
    "gemini": (
        "docs/03-reference/instructions/GEMINI.md",
        "docs/GEMINI.md",
        "docs/instructions/GEMINI.md",
    ),
}


SUBSYSTEM_RULES: List[Dict[str, Any]] = [
    {
        "name": "runtime-compose",
        "prefixes": (
            "compose.yml",
            "scripts/start.sh",
            "scripts/smoke_",
            "scripts/deploy/",
            "tools/smoke_",
            "tools/ports_health_audit.py",
            "services/registry.yaml",
        ),
        "globs": ("docker-compose*.yml",),
        "audiences": ("developer", "devops", "product", "user"),
        "targets": (
            "README.md",
            "INSTALL.md",
            "CHANGELOG.md",
            "docs/02-how-to/DOCKER_SETUP.md",
            "docs/03-reference/ports-and-registry-truth.md",
            "docs/03-reference/service-env-contract.md",
            "docs/03-reference/services/server-registry-2.md",
            "docs/03-reference/services/performance-baseline-2.md",
        ),
        "system_hubs": (),
        "user_workflow_signal": True,
        "architecture_policy_signal": True,
    },
    {
        "name": "task-orchestrator",
        "prefixes": (
            "services/task-orchestrator/",
            "docs/03-reference/services/task-orchestrator.md",
            "docs/02-how-to/operations/workflow-idea-epic-lifecycle.md",
            "docs/02-how-to/integrations/leantime-integration-guide.md",
        ),
        "globs": ("*task-orchestrator*", "*leantime*"),
        "audiences": ("developer", "devops", "product", "user"),
        "targets": (
            "CHANGELOG.md",
            "docs/03-reference/services/task-orchestrator.md",
            "docs/02-how-to/integrations/leantime-integration-guide.md",
            "docs/02-how-to/operations/workflow-idea-epic-lifecycle.md",
            "docs/planes/pm/task-orchestrator-leantime-followups.md",
            "docs/planes/pm/hub-3.md",
        ),
        "system_hubs": (),
        "user_workflow_signal": True,
        "architecture_policy_signal": True,
    },
    {
        "name": "adhd-engine",
        "prefixes": (
            "services/adhd_engine/",
            "services/adhd-engine/",
            "src/dopemux/adhd",
        ),
        "globs": ("*adhd*", "*serena*"),
        "audiences": ("developer", "product", "user"),
        "targets": (
            "CHANGELOG.md",
            "README.md",
            "docs/03-reference/adhd-engine-api.md",
            "docs/04-explanation/architecture/adhd-architecture-diagram.md",
            "docs/04-explanation/dopemux-overview.md",
            "services/adhd_engine/README.md",
        ),
        "system_hubs": ("docs/03-reference/systems/adhd-intelligence/overview.md",),
        "user_workflow_signal": True,
        "architecture_policy_signal": False,
    },
    {
        "name": "llm-instructions",
        "prefixes": (
            "AGENTS.md",
            "docs/03-reference/instructions/",
            "docs/instructions/",
            ".github/copilot-instructions.md",
            "docker/.claude/",
            "services/.claude/",
            "GEMINI.md",
            "docs/",
        ),
        "globs": (
            "*claude.md",
            "*CLAUDE.md",
            "*copilot*",
            "*gemini*",
            "*GEMINI*",
            "*AGENTS.md",
            "*instructions*",
        ),
        "audiences": ("developer", "product"),
        "targets": (),
        "system_hubs": (),
        "user_workflow_signal": False,
        "architecture_policy_signal": True,
    },
    {
        "name": "architecture-and-planning",
        "prefixes": (
            "docs/90-adr/",
            "docs/91-rfc/",
            "services/dopecon-bridge/",
            "src/dopemux/event_bus.py",
            "docs/04-explanation/architecture/",
        ),
        "globs": ("*adr*", "*rfc*", "*architecture*"),
        "audiences": ("developer", "devops", "product"),
        "targets": (
            "CHANGELOG.md",
            "README.md",
            "docs/04-explanation/dopemux-overview.md",
            "docs/04-explanation/architecture/adhd-architecture-diagram.md",
            "docs/planes/pm/hub-3.md",
        ),
        "system_hubs": (
            "docs/systems/dopecon-bridge/readme-3.md",
            "docs/systems/production/readme-3.md",
        ),
        "user_workflow_signal": False,
        "architecture_policy_signal": True,
    },
]


USER_WORKFLOW_HINTS: Sequence[str] = (
    "src/dopemux/cli.py",
    "README.md",
    "INSTALL.md",
    "QUICK_START.md",
    "ui-dashboard/",
    "ui-dashboard-backend/",
    "docs/01-tutorials/",
    "docs/02-how-to/",
)

ARCHITECTURE_POLICY_HINTS: Sequence[str] = (
    "compose.yml",
    "services/registry.yaml",
    "docs/90-adr/",
    "docs/91-rfc/",
    "docs/04-explanation/architecture/",
    "docs/planes/pm/",
)


def _run_git(repo_root: Path, args: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _ensure_baseline(repo_root: Path, baseline: str) -> None:
    proc = _run_git(repo_root, ["rev-parse", "--verify", baseline.split("...", 1)[0]])
    if proc.returncode != 0:
        raise RuntimeError(f"Baseline ref is not valid: {baseline}")


def _parse_name_status_line(line: str) -> Tuple[str, str]:
    parts = line.split("\t")
    if not parts:
        return "", ""
    status = parts[0].strip()
    path = parts[-1].strip()
    return status, path


def list_changed_files(repo_root: Path, baseline: str) -> List[Dict[str, str]]:
    proc = _run_git(repo_root, ["diff", "--name-status", baseline])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"Unable to diff baseline {baseline}")

    rows: List[Dict[str, str]] = []
    for raw in proc.stdout.splitlines():
        if not raw.strip():
            continue
        status, path = _parse_name_status_line(raw)
        if path:
            rows.append({"status": status, "path": path})
    return rows


def _match_rule(path: str, rule: Dict[str, Any]) -> bool:
    if any(path.startswith(prefix) for prefix in rule["prefixes"]):
        return True
    return any(fnmatch.fnmatch(path, pattern) for pattern in rule["globs"])


def _is_doc_file(path: str) -> bool:
    return path.endswith(".md")


def _is_active_doc(path: str) -> bool:
    if not path.startswith("docs/"):
        return False
    if path.startswith("docs/archive/"):
        return False
    if path.startswith("docs/04-explanation/history/"):
        return False
    return path.endswith(".md")


def _parse_frontmatter_type(file_path: Path) -> str | None:
    if not file_path.exists() or file_path.suffix.lower() != ".md":
        return None
    # Frontmatter is expected to be at the beginning and typically small.
    # Reading only the first 16KB avoids loading massive files into memory.
    try:
        with file_path.open("r", encoding="utf-8", errors="replace") as f:
            text = f.read(16384)
    except Exception:
        return None

    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end == -1:
        return None
    try:
        data = yaml.safe_load(text[4:end])
    except Exception:
        return None
    if isinstance(data, dict) and isinstance(data.get("type"), str):
        return data["type"].strip()
    return None


def _infer_doc_type(path: str) -> str:
    if path.startswith("docs/01-tutorials/"):
        return "tutorial"
    if path.startswith("docs/02-how-to/"):
        return "how-to"
    if path.startswith("docs/03-reference/") or path.startswith("docs/05-audit-reports/"):
        return "reference"
    if path.startswith("docs/90-adr/"):
        return "adr"
    if path.startswith("docs/91-rfc/"):
        return "rfc"
    if path.startswith("docs/92-runbooks/"):
        return "runbook"
    return "explanation"


def _has_any_prefix(paths: Iterable[str], prefixes: Sequence[str]) -> bool:
    for path in paths:
        for prefix in prefixes:
            if path.startswith(prefix):
                return True
    return False


def _has_any_hint(paths: Iterable[str], hints: Sequence[str]) -> bool:
    for path in paths:
        for hint in hints:
            if hint in path or path.startswith(hint):
                return True
    return False


def _select_existing_path(repo_root: Path, candidates: Sequence[str]) -> str:
    for candidate in candidates:
        if (repo_root / candidate).exists():
            return candidate
    return candidates[0]


def _resolve_instruction_targets(repo_root: Path) -> List[str]:
    resolved = [
        "AGENTS.md",
        _select_existing_path(repo_root, INSTRUCTION_PATH_CANDIDATES["codex"]),
        _select_existing_path(repo_root, INSTRUCTION_PATH_CANDIDATES["claude"]),
        _select_existing_path(repo_root, INSTRUCTION_PATH_CANDIDATES["gemini"]),
        "GEMINI.md",
        ".github/copilot-instructions.md",
        "docker/.claude/claude.md",
        "services/.claude/claude.md",
        "CHANGELOG.md",
        "README.md",
    ]
    return sorted(set(resolved))


def build_impact(changed: List[Dict[str, str]], repo_root: Path) -> Dict[str, Any]:
    changed_paths = [row["path"] for row in changed]
    subsystem_hits: Dict[str, List[str]] = {}
    audiences: set[str] = set()
    doc_targets: set[str] = set(CANONICAL_INDEXES)
    system_hubs: set[str] = set()
    user_workflow_changed = _has_any_hint(changed_paths, USER_WORKFLOW_HINTS)
    architecture_policy_changed = _has_any_hint(changed_paths, ARCHITECTURE_POLICY_HINTS)

    for rule in SUBSYSTEM_RULES:
        hit_files = [path for path in changed_paths if _match_rule(path, rule)]
        if not hit_files:
            continue
        subsystem_hits[rule["name"]] = sorted(hit_files)
        audiences.update(rule["audiences"])
        if rule["name"] == "llm-instructions":
            doc_targets.update(_resolve_instruction_targets(repo_root))
        else:
            doc_targets.update(rule["targets"])
        system_hubs.update(rule["system_hubs"])
        user_workflow_changed = user_workflow_changed or bool(rule["user_workflow_signal"])
        architecture_policy_changed = architecture_policy_changed or bool(rule["architecture_policy_signal"])

    if any(not _is_doc_file(path) for path in changed_paths):
        doc_targets.update(("README.md", "CHANGELOG.md"))

    if _has_any_prefix(changed_paths, ("services/task-orchestrator/", "docs/planes/pm/", "docs/02-how-to/integrations/")):
        doc_targets.add("docs/planes/pm/hub-3.md")

    doc_targets.update(system_hubs)

    required_types = ["reference", "how-to", "explanation"]
    if user_workflow_changed:
        required_types.append("tutorial")
    if architecture_policy_changed:
        required_types.extend(["adr", "rfc"])

    changed_doc_types: set[str] = set()
    for row in changed:
        path = row["path"]
        if not _is_active_doc(path):
            continue
        doc_type = _parse_frontmatter_type(repo_root / path) or _infer_doc_type(path)
        changed_doc_types.add(doc_type)

    rationale = {
        "reference": "Technical surface changed and needs up-to-date contracts/specs.",
        "how-to": "Operational usage/deployment behavior may change with code/runtime updates.",
        "explanation": "Conceptual architecture/behavior context must remain aligned to implementation.",
        "tutorial": "User workflow or UX-facing behavior changed.",
        "adr": "Architecture/policy boundary change detected.",
        "rfc": "Design proposal/transition boundary change detected.",
    }

    matrix = []
    blocking: List[str] = []
    for doc_type in required_types:
        covered = doc_type in changed_doc_types
        matrix.append(
            {
                "doc_type": doc_type,
                "required": True,
                "rationale": rationale.get(doc_type, "Required by policy."),
                "satisfied_by_changed_docs": covered,
            }
        )
        if not covered:
            blocking.append(f"Required doc type '{doc_type}' has no changed active document in baseline range")

    index_checklist = []
    changed_set = {row["path"] for row in changed}
    for target in sorted(doc_targets):
        if target in CANONICAL_INDEXES:
            reason = "Active canonical index/list"
        elif target == "docs/planes/pm/hub-3.md":
            reason = "PM hub impacted by task-orchestrator/leantime surface"
        elif target.startswith("docs/systems/"):
            reason = "Impacted subsystem hub"
        else:
            reason = "Impacted documentation target"
        index_checklist.append(
            {
                "path": target,
                "required": target in CANONICAL_INDEXES or target == "docs/planes/pm/hub-3.md" or target.startswith("docs/systems/"),
                "reason": reason,
                "updated_in_baseline": target in changed_set,
            }
        )

    for item in index_checklist:
        if item["required"] and not item["updated_in_baseline"]:
            blocking.append(f"Required index/hub target not updated in baseline range: {item['path']}")

    return {
        "subsystems": subsystem_hits,
        "audiences": sorted(audiences),
        "changed_paths": changed_paths,
        "doc_targets": sorted(doc_targets),
        "required_doc_types": required_types,
        "doc_type_coverage_matrix": matrix,
        "index_reconciliation_checklist": index_checklist,
        "blocking_findings": blocking,
    }


def _expected_prefixes_for_type(doc_type: str) -> Sequence[str]:
    if doc_type == "tutorial":
        return ("docs/01-tutorials/",)
    if doc_type == "how-to":
        return ("docs/02-how-to/",)
    if doc_type == "reference":
        return (
            "docs/03-reference/",
            "docs/05-audit-reports/",
            "docs/systems/",
            "docs/planes/",
            "docs/spec/",
        )
    if doc_type == "explanation":
        return (
            "docs/04-explanation/",
            "docs/planes/",
            "docs/03-reference/instructions/",
            "docs/instructions/",
            "docs/00-MASTER-INDEX.md",
            "docs/INDEX.md",
            "docs/03-reference/documentation-catalog.md",
            "docs/03-reference/overview.md",
            "docs/01-tutorials/overview.md",
            "docs/02-how-to/overview.md",
        )
    if doc_type == "adr":
        return ("docs/90-adr/",)
    if doc_type == "rfc":
        return ("docs/91-rfc/",)
    if doc_type == "runbook":
        return ("docs/92-runbooks/",)
    if doc_type == "pattern":
        return ("docs/03-reference/", "docs/04-explanation/")
    if doc_type == "caveat":
        return ("docs/03-reference/", "docs/04-explanation/")
    return ("docs/",)


def _path_matches_prefixes(path: str, prefixes: Sequence[str]) -> bool:
    for prefix in prefixes:
        if prefix.endswith(".md"):
            if path == prefix:
                return True
        elif path.startswith(prefix):
            return True
    return False


def audit_layout(repo_root: Path, changed: List[Dict[str, str]]) -> Dict[str, Any]:
    changed_docs = {row["path"] for row in changed if _is_active_doc(row["path"])}
    issues = []

    for path in sorted(repo_root.glob("docs/**/*.md")):
        rel = path.relative_to(repo_root).as_posix()
        if rel.startswith("docs/archive/"):
            continue
        if rel.startswith("docs/04-explanation/history/"):
            continue

        doc_type = _parse_frontmatter_type(path) or _infer_doc_type(rel)
        expected_prefixes = _expected_prefixes_for_type(doc_type)

        if _path_matches_prefixes(rel, expected_prefixes):
            continue

        issues.append(
            {
                "path": rel,
                "doc_type": doc_type,
                "expected_prefixes": list(expected_prefixes),
                "touched_or_new": rel in changed_docs,
            }
        )

    touched = [issue for issue in issues if issue["touched_or_new"]]
    existing = [issue for issue in issues if not issue["touched_or_new"]]

    return {
        "touched_or_new_misplacements": touched,
        "existing_misplacements": existing,
        "blocking": bool(touched),
    }


def write_layout_report(
    repo_root: Path,
    baseline: str,
    layout: Dict[str, Any],
    report_path: str,
    write_report: bool,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "path": report_path,
        "written": False,
        "existing_misplacements": len(layout["existing_misplacements"]),
        "touched_or_new_misplacements": len(layout["touched_or_new_misplacements"]),
    }

    if not write_report:
        return result

    now = dt.datetime.now(dt.timezone.utc).isoformat()
    payload = {
        "generated_at": now,
        "baseline": baseline,
        "existing_misplacements": layout["existing_misplacements"],
        "touched_or_new_misplacements": layout["touched_or_new_misplacements"],
    }

    report_file = repo_root / report_path
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["written"] = True
    return result


def append_layout_followups(
    repo_root: Path,
    ledger_path: str,
    layout: Dict[str, Any],
    layout_report: Dict[str, Any],
    write_ledger: bool,
) -> Dict[str, Any]:
    result = {
        "ledger_written": False,
        "entries": 0,
        "retry_after_utc": None,
    }

    if not write_ledger:
        return result

    existing = layout["existing_misplacements"]
    if not existing:
        return result

    now = dt.datetime.now(dt.timezone.utc)
    retry_after = (now + dt.timedelta(hours=24)).isoformat()
    lines = [
        "## Layout Audit Follow-up",
        f"- Timestamp: `{now.isoformat()}`",
        f"- Existing unrelated misplacements: `{len(existing)}`",
        f"- Findings report: `{layout_report['path']}`",
        f"- Retry after UTC: `{retry_after}`",
    ]
    for issue in existing[:5]:
        lines.append(
            "- Pending remediation: "
            f"`{issue['path']}` type=`{issue['doc_type']}` expected_prefixes=`{','.join(issue['expected_prefixes'])}`"
        )
    if len(existing) > 5:
        lines.append(f"- Additional misplacements not listed inline: `{len(existing) - 5}`")

    _append_ledger_entry(repo_root / ledger_path, lines)
    result["ledger_written"] = True
    result["entries"] = len(existing)
    result["retry_after_utc"] = retry_after
    return result


def _http_json_request(url: str, payload: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"raw": body}


def _http_get_json(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"raw": body}


def _extract_ticket_ids_from_ledger(ledger_text: str) -> List[str]:
    ids = sorted({token for token in set(ledger_text.replace("`", " ").split()) if token.startswith("PM-") and token.count("-") >= 2})
    return [token.strip(".,:;()[]{}") for token in ids]


def _append_ledger_entry(ledger_path: Path, lines: Sequence[str]) -> None:
    block = "\n".join(lines).rstrip() + "\n"
    if not ledger_path.exists():
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(block, encoding="utf-8")
        return

    current = ledger_path.read_text(encoding="utf-8", errors="replace")
    if not current.endswith("\n"):
        current += "\n"
    current += "\n" + block
    ledger_path.write_text(current, encoding="utf-8")


def sync_tickets(
    repo_root: Path,
    baseline: str,
    mode: str,
    task_orchestrator_url: str,
    ticket_ids: Sequence[str],
    ledger_path: str,
    write_ledger: bool,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "mode": mode,
        "task_orchestrator_url": task_orchestrator_url,
        "health": "skipped",
        "tickets": [],
        "ledger_path": ledger_path,
        "ledger_written": False,
        "pending_sync_entries": [],
        "errors": [],
        "blocking": False,
    }

    if mode == "off":
        return result

    ledger_file = repo_root / ledger_path
    resolved_tickets = list(ticket_ids)
    if not resolved_tickets and ledger_file.exists():
        resolved_tickets = _extract_ticket_ids_from_ledger(ledger_file.read_text(encoding="utf-8", errors="replace"))

    result["ticket_ids"] = resolved_tickets

    health_url = f"{task_orchestrator_url.rstrip('/')}/health"
    healthy = False
    try:
        health_payload = _http_get_json(health_url)
        status = str(health_payload.get("status", "")).lower()
        healthy = status in {"healthy", "ok", "degraded"}
        result["health"] = status or "unknown"
        result["health_payload"] = health_payload
    except Exception as exc:
        result["health"] = "unreachable"
        result["errors"].append(f"health probe failed: {exc}")

    now_dt = dt.datetime.now(dt.timezone.utc)
    now = now_dt.isoformat()
    retry_after = (now_dt + dt.timedelta(hours=24)).isoformat()

    if healthy and resolved_tickets:
        for ticket_id in resolved_tickets:
            payload = {
                "operation": "update_progress",
                "source_plane": "pm",
                "priority": 3,
                "data": {
                    "progress": {
                        "task_id": ticket_id,
                        "status": "in_progress",
                        "note": "PR docgen sync progress update",
                        "baseline": baseline,
                        "updated_at": now,
                    }
                },
            }
            try:
                response = _http_json_request(
                    f"{task_orchestrator_url.rstrip('/')}/api/coordination/operations",
                    payload,
                )
                success = bool(response.get("success", False))
                result["tickets"].append(
                    {
                        "ticket_id": ticket_id,
                        "live_sync_attempted": True,
                        "live_sync_success": success,
                        "response": response,
                    }
                )
                if not success:
                    result["errors"].append(f"live sync returned unsuccessful response for {ticket_id}")
                    result["pending_sync_entries"].append(
                        {
                            "ticket_id": ticket_id,
                            "reason": "live sync returned unsuccessful response",
                            "retry_after_utc": retry_after,
                        }
                    )
            except Exception as exc:
                result["tickets"].append(
                    {
                        "ticket_id": ticket_id,
                        "live_sync_attempted": True,
                        "live_sync_success": False,
                        "error": str(exc),
                    }
                )
                result["errors"].append(f"live sync failed for {ticket_id}: {exc}")
                result["pending_sync_entries"].append(
                    {
                        "ticket_id": ticket_id,
                        "reason": f"live sync failed: {exc}",
                        "retry_after_utc": retry_after,
                    }
                )
    elif resolved_tickets:
        for ticket_id in resolved_tickets:
            result["tickets"].append(
                {
                    "ticket_id": ticket_id,
                    "live_sync_attempted": False,
                    "live_sync_success": False,
                    "reason": "task-orchestrator unavailable",
                }
            )
            result["pending_sync_entries"].append(
                {
                    "ticket_id": ticket_id,
                    "reason": "task-orchestrator unavailable",
                    "retry_after_utc": retry_after,
                }
            )
    else:
        result["pending_sync_entries"].append(
            {
                "ticket_id": None,
                "reason": "missing ticket identifiers",
                "retry_after_utc": retry_after,
            }
        )

    ledger_lines = [
        "## Progress Sync Log",
        f"- Timestamp: `{now}`",
        f"- Baseline: `{baseline}`",
        f"- Mode: `{mode}`",
    ]
    if resolved_tickets:
        for ticket in result["tickets"]:
            status = "live-sync-ok" if ticket.get("live_sync_success") else "ledger-fallback"
            reason = ticket.get("reason") or ticket.get("error") or "n/a"
            if status == "live-sync-ok":
                ledger_lines.append(f"- Ticket `{ticket['ticket_id']}`: `{status}`")
            else:
                ledger_lines.append(
                    f"- Ticket `{ticket['ticket_id']}`: `{status}` reason=`{reason}` retry_after_utc=`{retry_after}`"
                )
    else:
        ledger_lines.append(
            f"- No ticket IDs discovered; pending-sync reason=`missing ticket identifiers` retry_after_utc=`{retry_after}`."
        )

    if write_ledger:
        _append_ledger_entry(ledger_file, ledger_lines)
        result["ledger_written"] = True

    if mode == "required":
        all_ok = healthy and resolved_tickets and all(ticket.get("live_sync_success") for ticket in result["tickets"])
        if not all_ok:
            result["blocking"] = True
            result["errors"].append("required live ticket sync failed")

    return result


def render_markdown(report: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# PR Docgen Sync Report")
    lines.append("")
    lines.append(f"Baseline: `{report['baseline']}`")
    lines.append(f"Changed files: `{len(report['changed_files'])}`")
    lines.append("")

    lines.append("## Impact Map")
    for name, files in sorted(report["impact_map"]["subsystems"].items()):
        lines.append(f"- `{name}`")
        for path in files:
            lines.append(f"  - `{path}`")
    lines.append(f"- Audiences: {', '.join(report['impact_map']['audiences']) or 'none'}")
    lines.append("")

    lines.append("## Doc Type Coverage Matrix")
    for row in report["doc_type_coverage_matrix"]:
        status = "ok" if row["satisfied_by_changed_docs"] else "missing"
        lines.append(f"- `{row['doc_type']}`: `{status}` ({row['rationale']})")
    lines.append("")

    lines.append("## Index Reconciliation Checklist")
    for row in report["index_reconciliation_checklist"]:
        mark = "x" if row["updated_in_baseline"] else " "
        req = "required" if row["required"] else "recommended"
        lines.append(f"- [{mark}] `{row['path']}` ({req}; {row['reason']})")
    lines.append("")

    lines.append("## Layout Audit")
    lines.append(f"- Touched/new misplacements: `{len(report['layout_audit']['touched_or_new_misplacements'])}`")
    lines.append(f"- Existing misplacements: `{len(report['layout_audit']['existing_misplacements'])}`")
    lines.append("")

    lines.append("## Ticket Sync Results")
    ticket_sync = report["ticket_sync_results"]
    lines.append(f"- Mode: `{ticket_sync['mode']}`")
    lines.append(f"- Health: `{ticket_sync['health']}`")
    lines.append(f"- Ledger written: `{ticket_sync['ledger_written']}`")
    for item in ticket_sync.get("tickets", []):
        lines.append(
            f"- `{item['ticket_id']}`: live_attempted=`{item.get('live_sync_attempted')}` live_success=`{item.get('live_sync_success')}`"
        )
    for pending in ticket_sync.get("pending_sync_entries", []):
        lines.append(
            "- pending-sync: "
            f"ticket=`{pending.get('ticket_id')}` reason=`{pending.get('reason')}` "
            f"retry_after_utc=`{pending.get('retry_after_utc')}`"
        )
    if ticket_sync.get("errors"):
        for err in ticket_sync["errors"]:
            lines.append(f"- error: {err}")
    lines.append("")

    lines.append("## Blocking Findings")
    if report["blocking_findings"]:
        for finding in report["blocking_findings"]:
            lines.append(f"- {finding}")
    else:
        lines.append("- none")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--baseline", default="main...HEAD")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--sync-tickets", choices=("best-effort", "required", "off"), default="best-effort")
    parser.add_argument("--task-orchestrator-url", default="http://localhost:8000")
    parser.add_argument("--ticket-id", action="append", default=[])
    parser.add_argument("--ledger-path", default=DEFAULT_LEDGER_PATH)
    parser.add_argument("--no-ledger-write", action="store_true")
    parser.add_argument("--layout-report-path", default=DEFAULT_LAYOUT_REPORT_PATH)
    parser.add_argument("--no-layout-report-write", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()

    try:
        _ensure_baseline(repo_root, args.baseline)
        changed = list_changed_files(repo_root, args.baseline)
        impact = build_impact(changed, repo_root)
        layout = audit_layout(repo_root, changed)
        layout_report = write_layout_report(
            repo_root=repo_root,
            baseline=args.baseline,
            layout=layout,
            report_path=args.layout_report_path,
            write_report=not args.no_layout_report_write,
        )

        ticket_sync = sync_tickets(
            repo_root=repo_root,
            baseline=args.baseline,
            mode=args.sync_tickets,
            task_orchestrator_url=args.task_orchestrator_url,
            ticket_ids=args.ticket_id,
            ledger_path=args.ledger_path,
            write_ledger=not args.no_ledger_write,
        )
        layout_followups = append_layout_followups(
            repo_root=repo_root,
            ledger_path=args.ledger_path,
            layout=layout,
            layout_report=layout_report,
            write_ledger=not args.no_ledger_write,
        )

        blocking = list(impact["blocking_findings"])
        if layout["blocking"]:
            blocking.append("Touched/new docs contain placement issues that violate Diataxis layout policy")
        if ticket_sync.get("blocking"):
            blocking.append("Required ticket sync failed")

        report = {
            "baseline": args.baseline,
            "changed_files": changed,
            "impact_map": {
                "subsystems": impact["subsystems"],
                "audiences": impact["audiences"],
                "doc_targets": impact["doc_targets"],
                "required_doc_types": impact["required_doc_types"],
            },
            "doc_type_coverage_matrix": impact["doc_type_coverage_matrix"],
            "index_reconciliation_checklist": impact["index_reconciliation_checklist"],
            "layout_audit": layout,
            "layout_report": layout_report,
            "layout_followup_ledger": layout_followups,
            "ticket_sync_results": ticket_sync,
            "blocking_findings": blocking,
        }

        if args.format == "json":
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(render_markdown(report), end="")

        return 2 if blocking else 0
    except Exception as exc:  # pragma: no cover - CLI guard
        print(json.dumps({"status": "error", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
