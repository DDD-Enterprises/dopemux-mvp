from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from .resolve import coldstart_report

# Fixed group order as specified in TP-TO-CANON-005
_GROUP_ORDER = [
    "active_root_in_progress",
    "repo_pr_proof_observed",
    "explicit_blocked",
    "operator_gate",
    "queue_only_supervisor_required",
    "queue_only",
]

_GROUP_LABELS = {
    "active_root_in_progress": "Active Root — In Progress",
    "repo_pr_proof_observed": "Repo PR Proof Observed",
    "explicit_blocked": "Explicit Blocked",
    "operator_gate": "Operator Gate",
    "queue_only_supervisor_required": "Queue Only — Supervisor Required",
    "queue_only": "Queue Only",
}


def _evidence_cell(evidence: dict[str, Any]) -> str:
    """Render evidence dict as a deterministic string. Fixed key order: pr, proof_exists, proof_json, role, status_label."""
    parts = []
    if "pr" in evidence:
        parts.append(f"pr={evidence['pr']}")
    if "proof_exists" in evidence:
        parts.append(f"proof_exists={evidence['proof_exists']}")
    if "proof_json" in evidence:
        parts.append(f"proof_json={evidence['proof_json']}")
    if "role" in evidence:
        parts.append(f"role={evidence['role']}")
    if "status_label" in evidence:
        parts.append(f"status_label={evidence['status_label']}")
    return "; ".join(parts) if parts else ""


def render_markdown(coldstart: dict) -> str:
    """Render a coldstart reconciliation dict as a deterministic Markdown report.

    Takes the dict produced by the offline JSON (or build_coldstart_report).
    Does NOT call any live DB function. Output is byte-stable across re-runs
    provided the input dict is identical (no wall-clock timestamps, no randomness).
    """
    pit = coldstart["point_in_time"]
    valid_as_of = pit["valid_as_of_utc"]
    basis = pit["basis"]
    counts = coldstart.get("classification_counts", {})
    items = coldstart.get("items", [])
    schema_version = coldstart.get("schema_version", "")
    root_decision = coldstart.get("root_decision", "")
    active_db_slug = coldstart.get("active_db_slug", "")

    # Group items by classification
    groups: dict[str, list[dict]] = {g: [] for g in _GROUP_ORDER}
    for item in items:
        cls = item.get("classification", "")
        if cls in groups:
            groups[cls].append(item)
    # Sort each group by title for deterministic ordering
    for cls in _GROUP_ORDER:
        groups[cls].sort(key=lambda x: x.get("title", ""))

    lines: list[str] = []

    # Frontmatter — static, no wall-clock dates
    lines.append("---")
    lines.append("id: coldstart-reconciliation-20260622")
    lines.append("title: Coldstart Reconciliation 20260622")
    lines.append("type: reference")
    lines.append("owner: '@hu3mann'")
    lines.append("author: '@hu3mann'")
    lines.append("date: '2026-06-22'")
    lines.append("last_review: '2026-06-22'")
    lines.append("next_review: '2026-09-20'")
    lines.append(
        "prelude: Coldstart reconciliation decision report for the DMX-COLDSTART"
        " task-packet series as of 2026-06-22."
    )
    lines.append("---")
    lines.append("")

    # Title and intro
    lines.append("# Coldstart Reconciliation — 2026-06-22")
    lines.append("")
    lines.append(
        "Offline point-in-time classification of all DMX-COLDSTART work items. "
        "This report is generated from the committed reconciliation JSON and is "
        "presentation-only — no live database access, no status mutations."
    )
    lines.append("")

    # Point-in-time banner — verbatim from input dict
    lines.append("## Point-in-Time Provenance")
    lines.append("")
    lines.append(f"**valid_as_of_utc**: `{valid_as_of}`")
    lines.append("")
    lines.append(f"**basis**: {basis}")
    lines.append("")
    lines.append(f"**schema_version**: `{schema_version}`")
    lines.append("")
    lines.append(f"**active_db_slug**: `{active_db_slug}`")
    lines.append("")
    lines.append(f"**root_decision**: `{root_decision}`")
    lines.append("")

    # Per-group tables
    lines.append("## Item Classifications")
    lines.append("")
    for cls in _GROUP_ORDER:
        group_items = groups[cls]
        label = _GROUP_LABELS.get(cls, cls)
        lines.append(f"### {label}")
        lines.append("")
        if not group_items:
            lines.append("_No items in this classification._")
            lines.append("")
            continue
        # Table header
        lines.append("| Title | Role | Decision | Status Label | Evidence |")
        lines.append("|-------|------|----------|--------------|----------|")
        for item in group_items:
            title = item.get("title", "")
            role = item.get("role", "") or ""
            decision = item.get("decision", "") or ""
            status_label = item.get("status_label", "") or ""
            evidence = item.get("evidence", {})
            evidence_str = _evidence_cell(evidence)
            lines.append(
                f"| {title} | {role} | {decision} | {status_label} | {evidence_str} |"
            )
        lines.append("")

    # Counts summary — read from classification_counts, fixed group order
    lines.append("## Classification Counts")
    lines.append("")
    lines.append("| Classification | Count |")
    lines.append("|----------------|-------|")
    for cls in _GROUP_ORDER:
        count = counts.get(cls, 0)
        lines.append(f"| {cls} | {count} |")
    lines.append("")
    total = sum(counts.values())
    lines.append(f"**Total items**: {total}")
    lines.append("")

    return "\n".join(lines)


def build_coldstart_report(conn: sqlite3.Connection, repo_root: Path) -> dict[str, Any]:
    return coldstart_report(conn, repo_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Render a coldstart reconciliation JSON as a deterministic Markdown report."
        )
    )
    parser.add_argument(
        "--from-json",
        required=True,
        type=Path,
        metavar="PATH",
        help="path to COLDSTART_RECONCILIATION.json (read-only)",
    )
    parser.add_argument(
        "--emit-md",
        required=True,
        type=Path,
        metavar="PATH",
        help="output path for the generated Markdown report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        coldstart = json.loads(args.from_json.read_text(encoding="utf-8"))
    except OSError as exc:
        parser.error(f"cannot read --from-json {args.from_json}: {exc}")
    except json.JSONDecodeError as exc:
        parser.error(f"invalid JSON in --from-json {args.from_json}: {exc}")
    md = render_markdown(coldstart)
    args.emit_md.parent.mkdir(parents=True, exist_ok=True)
    args.emit_md.write_text(md, encoding="utf-8")
    print(f"wrote {args.emit_md}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
