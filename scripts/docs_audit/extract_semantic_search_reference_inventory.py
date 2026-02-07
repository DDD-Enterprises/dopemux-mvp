#!/usr/bin/env python3
"""
Build an active-reference inventory for semantic-search related symbols/paths.

Used to keep the semantic-search deprecation/migration backlog grounded in
tracked code/docs truth (excluding immutable archive docs).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


PATTERNS = [
    r"semantic_search_conport",
    r"semantic_search",
    r"semantic-search",
    r"/api/semantic-search",
    r"/api/adhd/semantic-search",
    r"/conport/semantic_search",
]

EXCLUDE_PREFIXES = (
    "docs/archive/",
    "docs/05-audit-reports/",
    "docs/06-research/",
)


def _classify_hit(line: str) -> str:
    if "/conport/semantic_search" in line:
        return "bridge_legacy_route_ref"
    if "/api/semantic-search" in line:
        return "legacy_endpoint_ref"
    if "/api/adhd/semantic-search" in line:
        return "adhd_endpoint_ref"
    if "semantic_search_conport" in line:
        return "conport_tool_ref"
    return "semantic_token"


def _scope_for_path(path: str) -> str:
    if path.startswith("docs/"):
        return "docs"
    if path.startswith("tests/") or "/test" in path:
        return "tests"
    return "code"


def _collect_records(
    tracked_paths: list[str],
    regex: re.Pattern[str],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for rel in tracked_paths:
        if rel.startswith(EXCLUDE_PREFIXES):
            continue
        file_path = Path(rel)
        if not file_path.exists() or file_path.is_dir():
            continue

        text = file_path.read_text(encoding="utf-8", errors="ignore")
        hits: list[dict[str, Any]] = []
        for idx, line in enumerate(text.splitlines(), start=1):
            if not regex.search(line):
                continue
            hits.append(
                {
                    "line": idx,
                    "kind": _classify_hit(line),
                    "text": line.strip()[:240],
                }
            )

        if hits:
            records.append(
                {
                    "path": rel,
                    "scope": _scope_for_path(rel),
                    "hit_count": len(hits),
                    "hits": hits,
                }
            )
    return records


def _summarize(records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "files_with_hits": len(records),
        "code_files": sum(1 for r in records if r["scope"] == "code"),
        "test_files": sum(1 for r in records if r["scope"] == "tests"),
        "doc_files": sum(1 for r in records if r["scope"] == "docs"),
        "bridge_legacy_route_ref_count": sum(
            1 for r in records for h in r["hits"] if h["kind"] == "bridge_legacy_route_ref"
        ),
        "legacy_endpoint_ref_count": sum(
            1 for r in records for h in r["hits"] if h["kind"] == "legacy_endpoint_ref"
        ),
        "adhd_endpoint_ref_count": sum(
            1 for r in records for h in r["hits"] if h["kind"] == "adhd_endpoint_ref"
        ),
        "conport_tool_ref_count": sum(
            1 for r in records for h in r["hits"] if h["kind"] == "conport_tool_ref"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract semantic-search reference inventory.")
    parser.add_argument(
        "--roots",
        nargs="+",
        default=["src", "services", "tests", "docs"],
        help="Tracked roots to scan via git ls-files.",
    )
    parser.add_argument(
        "--output-json",
        default="reports/strict_closure/semantic_search_reference_inventory_2026-02-07.json",
        help="Output artifact path.",
    )
    parser.add_argument(
        "--generated-at-utc",
        default="2026-02-07T00:00:00Z",
        help="Generation timestamp label used in artifact metadata.",
    )
    args = parser.parse_args()

    ls_cmd = ["git", "ls-files", *args.roots]
    tracked_paths = subprocess.check_output(ls_cmd, text=True).splitlines()
    regex = re.compile("|".join(PATTERNS))

    records = _collect_records(tracked_paths=tracked_paths, regex=regex)
    summary = _summarize(records)

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "artifact": str(output_path),
        "generated_at_utc": args.generated_at_utc,
        "scope": (
            "tracked files under src/services/tests/docs excluding "
            "docs/archive, docs/05-audit-reports, docs/06-research"
        ),
        "summary": summary,
        "records": records,
    }
    output_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Wrote: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
