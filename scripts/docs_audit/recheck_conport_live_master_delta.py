#!/usr/bin/env python3
"""
Compare the latest live ConPort progress backlog export against:
1) a previous export snapshot, and
2) the active ConPort master todo/miss matrix document.

Purpose:
- detect net-new live TODO/BLOCKED-style descriptions,
- identify whether new rows are already represented in master docs,
- emit a strict-closure JSON artifact for audit traceability.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any


def _normalize(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _canonical(text: str) -> str:
    text = _normalize(text)
    text = text.split("|", 1)[0].strip()
    text = re.sub(r"\([^\)]*hours?[^\)]*\)", "", text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _build_report(
    previous_rows: list[dict[str, str]],
    current_rows: list[dict[str, str]],
    master_doc_text: str,
    previous_csv: Path,
    current_csv: Path,
    master_doc: Path,
    artifact_path: Path,
) -> dict[str, Any]:
    master_doc_norm = _normalize(master_doc_text)
    master_doc_canonical = _canonical(master_doc_text)

    previous_descriptions = {
        _normalize(row.get("description", ""))
        for row in previous_rows
        if _normalize(row.get("description", ""))
    }

    current_unique: dict[str, dict[str, str]] = {}
    for row in current_rows:
        description_norm = _normalize(row.get("description", ""))
        if not description_norm:
            continue
        current_unique[description_norm] = row

    new_rows = [
        row
        for description_norm, row in current_unique.items()
        if description_norm not in previous_descriptions
    ]

    checked_new_rows: list[dict[str, Any]] = []
    for row in sorted(new_rows, key=lambda r: r.get("created_at", ""), reverse=True):
        description = (row.get("description") or "").strip()
        checked_new_rows.append(
            {
                "workspace_id": row.get("workspace_id"),
                "status": row.get("status"),
                "description": description,
                "created_at": row.get("created_at"),
                "updated_at": row.get("updated_at"),
                "present_in_master_exact": _normalize(description) in master_doc_norm,
                "present_in_master_canonical": _canonical(description) in master_doc_canonical,
            }
        )

    missing_exact = [row for row in checked_new_rows if not row["present_in_master_exact"]]
    missing_canonical = [row for row in checked_new_rows if not row["present_in_master_canonical"]]

    return {
        "artifact": str(artifact_path),
        "source_previous": str(previous_csv),
        "source_current": str(current_csv),
        "source_master_doc": str(master_doc),
        "summary": {
            "previous_rows": len(previous_rows),
            "current_rows": len(current_rows),
            "new_descriptions_since_previous": len(checked_new_rows),
            "new_missing_in_master_exact": len(missing_exact),
            "new_missing_in_master_canonical": len(missing_canonical),
        },
        "new_rows": checked_new_rows,
        "new_missing_exact": missing_exact,
        "new_missing_canonical": missing_canonical,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Recheck live ConPort backlog delta against master docs.")
    parser.add_argument(
        "--previous-csv",
        default="reports/strict_closure/conport_live_progress_backlog_2026-02-06.csv",
        help="Previous live export snapshot.",
    )
    parser.add_argument(
        "--current-csv",
        default="reports/strict_closure/conport_live_progress_backlog_2026-02-07.csv",
        help="Current live export snapshot.",
    )
    parser.add_argument(
        "--master-doc",
        default="docs/05-audit-reports/CONPORT_MASTER_TODO_MISS_MATRIX_2026-02-06.md",
        help="Master matrix document used for coverage checks.",
    )
    parser.add_argument(
        "--output-json",
        default="reports/strict_closure/conport_live_backlog_delta_2026-02-07.json",
        help="Output artifact path.",
    )
    args = parser.parse_args()

    previous_csv = Path(args.previous_csv)
    current_csv = Path(args.current_csv)
    master_doc = Path(args.master_doc)
    output_json = Path(args.output_json)

    if not current_csv.exists():
        raise SystemExit(f"Current CSV not found: {current_csv}")
    if not master_doc.exists():
        raise SystemExit(f"Master doc not found: {master_doc}")

    previous_rows = _load_csv_rows(previous_csv)
    current_rows = _load_csv_rows(current_csv)
    master_doc_text = master_doc.read_text(encoding="utf-8", errors="ignore")

    report = _build_report(
        previous_rows=previous_rows,
        current_rows=current_rows,
        master_doc_text=master_doc_text,
        previous_csv=previous_csv,
        current_csv=current_csv,
        master_doc=master_doc,
        artifact_path=output_json,
    )

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    print(f"Wrote: {output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
