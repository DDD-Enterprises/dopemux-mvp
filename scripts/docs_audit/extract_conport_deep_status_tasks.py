#!/usr/bin/env python3
"""
Extract TODO/BLOCKED task claims from ConPort import bundles and compare them
against active master fix docs.

This is used to pull missed implementation work from historical ConPort SQLite
exports, including structured custom_data payloads that contain status fields.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


TASK_STATUS_SET = {"TODO", "BLOCKED"}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"`+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9\s:|._/-]", "", text)
    return text.strip()


def _task_type(description: str) -> str:
    if re.match(r"^day\s+\d+", description, flags=re.IGNORECASE):
        return "DAY_PLAN"
    if re.match(r"^week\s+\d+", description, flags=re.IGNORECASE):
        return "WEEK_PLAN"
    if re.match(r"^epic(\s+\d+)?", description, flags=re.IGNORECASE):
        return "EPIC"
    if re.match(r"^\d+\.\d+\.\d+", description):
        return "NUMERIC_3"
    if re.match(r"^task\s+\d+\.\d+", description, flags=re.IGNORECASE):
        return "TASK_PLAN"
    return "OTHER"


def _safe_json_loads(raw: Any) -> Any:
    value: Any = raw
    for _ in range(4):
        if not isinstance(value, str):
            return value
        text = value.strip()
        if not text:
            return value
        if text[0] not in "[{\"":
            return value
        try:
            value = json.loads(text)
        except Exception:
            return value
    return value


def _iter_status_nodes(obj: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], dict[str, Any]]]:
    if isinstance(obj, dict):
        status = obj.get("status")
        if isinstance(status, str) and status.upper() in TASK_STATUS_SET:
            yield path, obj
        for key, value in obj.items():
            yield from _iter_status_nodes(value, path + (str(key),))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            yield from _iter_status_nodes(value, path + (str(idx),))


def _prettify_path_token(token: str) -> str:
    token = token.replace("_", " ").strip()
    token = re.sub(r"\s+", " ", token)
    return token


def _description_from_status_node(path: tuple[str, ...], node: dict[str, Any], custom_key: str) -> str:
    for key in ("description", "task", "title", "name", "summary"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    criteria = node.get("criteria")
    criteria_hint = ""
    if isinstance(criteria, list) and criteria:
        first = criteria[0]
        if isinstance(first, str) and first.strip():
            criteria_hint = f" | Criteria: {first.strip()}"

    if path:
        leaf = _prettify_path_token(path[-1])
    else:
        leaf = _prettify_path_token(custom_key)
    return f"{leaf}{criteria_hint}".strip()


@dataclass
class Record:
    description: str
    status: str
    status_set: list[str]
    priority_hint: str
    task_type: str
    identity_token: str
    covered_in_master_docs: bool
    bundle_hits: list[str]
    bundle_paths: list[str]
    first_timestamp: str | None
    last_timestamp: str | None
    source_kinds: list[str]
    source_locations: list[str]
    already_in_full_coverage: bool


def _priority_hint(description: str, status: str) -> str:
    if status == "BLOCKED":
        return "BLOCKED"
    m = re.search(r"\((P[0-3])\)", description, flags=re.IGNORECASE)
    if m:
        return m.group(1).upper()
    m = re.search(r"\b(P[0-3])\b", description, flags=re.IGNORECASE)
    if m:
        return m.group(1).upper()
    return "UNSPECIFIED"


def _coverage_aliases(description: str) -> list[str]:
    aliases = {description.strip()}
    first_segment = description.split("|", 1)[0].strip()
    if first_segment:
        aliases.add(first_segment)

    blocked_trimmed = re.split(r"\s+-\s+BLOCKED[:\s-]*", first_segment, maxsplit=1, flags=re.IGNORECASE)[0].strip()
    if blocked_trimmed:
        aliases.add(blocked_trimmed)

    numbered = re.sub(r"^\s*(?:day|week|task|epic)\s+\d+[:\s-]*", "", blocked_trimmed, flags=re.IGNORECASE).strip()
    numbered = re.sub(r"^\s*\d+\.\d+\.\d+\s*[:\s-]*", "", numbered).strip()
    if numbered:
        aliases.add(numbered)

    return [a for a in aliases if a]


def _is_covered(doc_text_norm: str, description: str) -> bool:
    for alias in _coverage_aliases(description):
        normalized = _normalize(alias)
        if not normalized:
            continue
        if normalized in doc_text_norm:
            return True
        words = [w for w in normalized.split() if len(w) > 3 and w not in {"with", "from", "that", "this"}]
        if len(words) >= 4:
            fingerprint = " ".join(words[:8])
            if fingerprint in doc_text_norm:
                return True
    return False


def _load_full_coverage_identities(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    records = data.get("all_records", [])
    out: set[str] = set()
    for rec in records:
        if isinstance(rec, dict):
            desc = rec.get("description")
            if isinstance(desc, str) and desc.strip():
                out.add(_normalize(desc))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Deep ConPort TODO/BLOCKED extraction against master docs.")
    parser.add_argument(
        "--bundle-glob",
        default="reports/conport_sqlite_exports/**/import_bundles/*_conport_import_bundle.json",
        help="Glob pattern for ConPort import bundle JSON files.",
    )
    parser.add_argument(
        "--docs",
        nargs="+",
        default=[
            "docs/05-audit-reports/CONPORT_MASTER_TODO_MISS_MATRIX_2026-02-06.md",
            "docs/05-audit-reports/CONPORT_UNDERREPRESENTED_EXECUTION_PACKET_2026-02-06.md",
            "docs/05-audit-reports/FINAL_STATE_FEATURE_BASELINE_AND_EXECUTION_PLAN_2026-02-06.md",
            "docs/05-audit-reports/LEANTIME_BRIDGE_READINESS_2026-02-06.md",
        ],
        help="Master docs checked for explicit coverage.",
    )
    parser.add_argument(
        "--full-coverage-json",
        default="reports/strict_closure/conport_full_todo_coverage_2026-02-06.json",
        help="Existing full coverage artifact used for de-dup tracking.",
    )
    parser.add_argument(
        "--output-json",
        default="reports/strict_closure/conport_deep_status_task_extract_2026-02-06.json",
        help="Output artifact path.",
    )
    args = parser.parse_args()

    bundle_paths = sorted(Path(".").glob(args.bundle_glob))
    if not bundle_paths:
        raise SystemExit(f"No bundles found for glob: {args.bundle_glob}")

    docs_checked: list[str] = []
    doc_texts: list[str] = []
    for doc in args.docs:
        p = Path(doc)
        if p.exists():
            docs_checked.append(doc)
            doc_texts.append(p.read_text(encoding="utf-8", errors="ignore"))

    docs_text_norm = _normalize("\n".join(doc_texts))
    full_coverage_identities = _load_full_coverage_identities(Path(args.full_coverage_json))

    aggregate: dict[str, dict[str, Any]] = {}
    raw_record_count = 0
    source_kind_counts = defaultdict(int)

    for bundle_path in bundle_paths:
        data = json.loads(bundle_path.read_text(encoding="utf-8"))
        metadata = data.get("metadata", {})
        source_db = metadata.get("source_db_path")
        timestamp_hint = metadata.get("export_timestamp")
        bundle_ref = str(bundle_path)

        for entry in data.get("progress_entries", []):
            if not isinstance(entry, dict):
                continue
            status = str(entry.get("status", "")).upper()
            description = entry.get("description")
            if status not in TASK_STATUS_SET or not isinstance(description, str) or not description.strip():
                continue
            raw_record_count += 1
            source_kind_counts["progress_entries"] += 1
            identity = _normalize(description)
            row = aggregate.setdefault(
                identity,
                {
                    "description": description.strip(),
                    "status_set": set(),
                    "bundle_hits": set(),
                    "bundle_paths": set(),
                    "first_timestamp": timestamp_hint,
                    "last_timestamp": timestamp_hint,
                    "source_kinds": set(),
                    "source_locations": set(),
                },
            )
            row["status_set"].add(status)
            row["bundle_hits"].add(str(source_db or "unknown"))
            row["bundle_paths"].add(bundle_ref)
            row["source_kinds"].add("progress_entries")
            row["source_locations"].add(f"{bundle_ref}::progress_entries")
            row["last_timestamp"] = timestamp_hint

        for custom in data.get("custom_data", []):
            if not isinstance(custom, dict):
                continue
            raw_value = custom.get("value")
            parsed = _safe_json_loads(raw_value)
            if isinstance(parsed, str):
                continue
            custom_key = str(custom.get("key", "custom_data"))
            custom_category = str(custom.get("category", "custom_data"))

            for path, node in _iter_status_nodes(parsed):
                status = str(node.get("status", "")).upper()
                if status not in TASK_STATUS_SET:
                    continue
                description = _description_from_status_node(path, node, custom_key)
                if not description:
                    continue

                raw_record_count += 1
                source_kind_counts["custom_data"] += 1
                identity = _normalize(description)
                row = aggregate.setdefault(
                    identity,
                    {
                        "description": description,
                        "status_set": set(),
                        "bundle_hits": set(),
                        "bundle_paths": set(),
                        "first_timestamp": timestamp_hint,
                        "last_timestamp": timestamp_hint,
                        "source_kinds": set(),
                        "source_locations": set(),
                    },
                )
                row["status_set"].add(status)
                row["bundle_hits"].add(str(source_db or "unknown"))
                row["bundle_paths"].add(bundle_ref)
                row["source_kinds"].add("custom_data")
                row["source_locations"].add(
                    f"{bundle_ref}::custom_data::{custom_category}::{custom_key}::{'.'.join(path)}"
                )
                row["last_timestamp"] = timestamp_hint

    records: list[Record] = []
    for identity, row in aggregate.items():
        status_set_sorted = sorted(row["status_set"])
        status = "BLOCKED" if "BLOCKED" in status_set_sorted else status_set_sorted[0]
        description = row["description"]
        covered = _is_covered(docs_text_norm, description)
        records.append(
            Record(
                description=description,
                status=status,
                status_set=status_set_sorted,
                priority_hint=_priority_hint(description, status),
                task_type=_task_type(description),
                identity_token=identity,
                covered_in_master_docs=covered,
                bundle_hits=sorted(row["bundle_hits"]),
                bundle_paths=sorted(row["bundle_paths"]),
                first_timestamp=row["first_timestamp"],
                last_timestamp=row["last_timestamp"],
                source_kinds=sorted(row["source_kinds"]),
                source_locations=sorted(row["source_locations"]),
                already_in_full_coverage=identity in full_coverage_identities,
            )
        )

    def _sort_key(rec: Record) -> tuple[int, int, str]:
        return (
            0 if rec.priority_hint == "BLOCKED" else 1 if rec.priority_hint == "P0" else 2 if rec.priority_hint == "P1" else 3,
            -len(rec.bundle_hits),
            rec.description.lower(),
        )

    records.sort(key=_sort_key)

    uncovered = [r for r in records if not r.covered_in_master_docs]
    new_vs_full = [r for r in records if not r.already_in_full_coverage]
    new_uncovered_vs_full = [r for r in new_vs_full if not r.covered_in_master_docs]

    task_breakdown = defaultdict(int)
    for rec in records:
        task_breakdown[rec.task_type] += 1

    output = {
        "generated_at_utc": __import__("datetime").datetime.now(__import__("datetime").UTC).replace(microsecond=0).isoformat(),
        "source_bundles": [str(p) for p in bundle_paths],
        "docs_checked": docs_checked,
        "full_coverage_reference": args.full_coverage_json,
        "summary": {
            "raw_records_scanned": raw_record_count,
            "source_kind_counts": dict(source_kind_counts),
            "unique_status_items": len(records),
            "covered_in_master_docs": len(records) - len(uncovered),
            "uncovered_in_master_docs": len(uncovered),
            "already_in_full_coverage": len(records) - len(new_vs_full),
            "new_vs_full_coverage": len(new_vs_full),
            "new_uncovered_vs_full_coverage": len(new_uncovered_vs_full),
            "task_type_breakdown": dict(sorted(task_breakdown.items())),
        },
        "new_uncovered_top_100": [r.__dict__ for r in new_uncovered_vs_full[:100]],
        "uncovered_top_100": [r.__dict__ for r in uncovered[:100]],
        "all_records": [r.__dict__ for r in records],
    }

    out_path = Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(
        "summary:",
        json.dumps(
            {
                "unique_status_items": output["summary"]["unique_status_items"],
                "uncovered_in_master_docs": output["summary"]["uncovered_in_master_docs"],
                "new_uncovered_vs_full_coverage": output["summary"]["new_uncovered_vs_full_coverage"],
            }
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
