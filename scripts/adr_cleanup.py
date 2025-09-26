#!/usr/bin/env python3
"""
ADR cleanup utility: standardize filenames and consolidate ADR documents into docs/90-adr.

- Detect ADR markdown files across the repo (primarily under docs/)
- Normalize filenames to: adr-XXXX-slug.md (lowercase, zero-padded number)
- Move into docs/90-adr/
- Skip historical/imported/archive trees by default to avoid duplication

Usage:
  Dry run (default):
    python scripts/adr_cleanup.py

  Apply changes:
    python scripts/adr_cleanup.py --apply

Options:
  --include-historical   Also process docs/HISTORICAL and docs/DMPX IMPORT trees
  --include-archive      Also process archive/ trees
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
ADR_DIR = DOCS_DIR / "90-adr"


def slugify(text: str) -> str:
    text = text.strip().lower()
    # Replace non-word with hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled"


def rg_paths(pattern: str, base: Path, globs: Optional[List[str]] = None) -> List[Path]:
    args = ["rg", "-n", "-S", pattern, str(base)]
    if globs:
        for g in globs:
            args.extend(["-g", g])
    try:
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        paths: Set[Path] = set()
        for line in proc.stdout.splitlines():
            p = Path(line.split(":", 1)[0])
            if p.suffix.lower() == ".md" and p.exists():
                paths.add(p)
        return sorted(paths)
    except FileNotFoundError:
        # Fallback to manual walk
        results: List[Path] = []
        for p in base.rglob("*.md"):
            try:
                if re.search(pattern, p.read_text(encoding="utf-8", errors="ignore")):
                    results.append(p)
            except Exception:
                continue
        return results


def read_first_header(p: Path) -> Optional[str]:
    try:
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip().startswith("#"):
                    return line.strip().lstrip("#").strip()
    except Exception:
        return None
    return None


def extract_adr_number_and_title(p: Path) -> Tuple[Optional[int], Optional[str]]:
    name = p.name
    # Try filename patterns
    m = re.search(r"(?i)\badr[-_ ]?(\d{1,4})\b", name)
    if m:
        num = int(m.group(1))
        # Title from remainder of filename
        tail = re.sub(r"(?i)\badr[-_ ]?\d{1,4}[-_ ]?", "", name)
        title = tail.rsplit(".", 1)[0]
        title = title.replace("_", " ").replace("-", " ").strip()
        return num, title or None

    # Try header line
    header = read_first_header(p) or ""
    mh = re.search(r"(?i)^adr[- ]?(\d{1,4})[:\- ]+(.+)$", header)
    if mh:
        num = int(mh.group(1))
        title = mh.group(2).strip()
        return num, title or None

    # If header like "ADR: Title"
    mh2 = re.search(r"(?i)^adr[:\- ]+(.+)$", header)
    if mh2:
        return None, mh2.group(1).strip()

    # Fallback: plain title
    if header:
        return None, header

    return None, None


def list_existing_ids(adr_dir: Path) -> Set[int]:
    ids: Set[int] = set()
    for p in adr_dir.glob("adr-*.md"):
        m = re.search(r"adr-(\d{1,4})-", p.name)
        if m:
            ids.add(int(m.group(1)))
    return ids


def next_available_id(used: Set[int]) -> int:
    i = 1
    while i in used:
        i += 1
    return i


@dataclass
class PlanItem:
    src: Path
    dst: Path
    reason: str
    assigned_id: Optional[int] = None


def find_adr_candidates(include_historical: bool, include_archive: bool) -> List[Path]:
    candidates: Set[Path] = set()
    if not DOCS_DIR.exists():
        return []

    # Walk docs and pick likely ADRs
    for p in DOCS_DIR.rglob("*.md"):
        rel = p.relative_to(REPO_ROOT)
        rel_str = str(rel)
        if p.is_dir():
            continue
        # Skip target dir and templates
        if str(ADR_DIR) in str(p.parent):
            continue
        if "/templates/" in rel_str:
            continue
        # Skip historical by default
        if not include_historical and (
            "/HISTORICAL/" in rel_str or "/DMPX IMPORT/" in rel_str
        ):
            continue

        # Heuristics: path segment contains adr/adrs or filename starts with ADR-
        if re.search(r"/(adr|adrs)/", rel_str, re.I) or re.search(r"/(adr|ADR)-", rel_str):
            candidates.add(p)
            continue
        # Or header contains ADR
        header = read_first_header(p) or ""
        if re.search(r"(?i)^adr", header):
            candidates.add(p)

    # Optionally include archive
    if include_archive:
        for p in (REPO_ROOT / "archive").rglob("*.md"):
            rel = str(p.relative_to(REPO_ROOT))
            if "/adrs/" in rel or re.search(r"\bADR-\d+", p.name, re.I):
                candidates.add(p)

    return sorted(candidates)


def build_plan(include_historical: bool, include_archive: bool) -> Tuple[List[PlanItem], List[str]]:
    errors: List[str] = []
    plan: List[PlanItem] = []
    used_ids = list_existing_ids(ADR_DIR)
    all_used = set(used_ids)

    for src in find_adr_candidates(include_historical, include_archive):
        num, title = extract_adr_number_and_title(src)
        assigned = num
        reason = ""

        if num is None:
            assigned = next_available_id(all_used)
            reason = "no id; assigning next available"
        elif num in all_used:
            # If there's already an adr-XXXX in target, attempt content compare
            existing = list(ADR_DIR.glob(f"adr-{num:04d}-*.md"))
            if existing:
                try:
                    src_txt = src.read_text(encoding="utf-8", errors="ignore").strip()
                    ex_txt = existing[0].read_text(encoding="utf-8", errors="ignore").strip()
                    if src_txt == ex_txt:
                        # Duplicate; we will treat as redundant (skip move)
                        reason = f"duplicate of {existing[0].name}; skipping"
                        # Represent as no-op by setting dst to src
                        plan.append(PlanItem(src=src, dst=src, reason=reason, assigned_id=num))
                        continue
                    else:
                        # Different content – assign a new ID
                        assigned = next_available_id(all_used)
                        reason = f"id {num:04d} occupied; new id assigned"
                except Exception:
                    assigned = next_available_id(all_used)
                    reason = f"id {num:04d} occupied; new id assigned"
        else:
            reason = "kept original id"

        all_used.add(int(assigned))

        # Determine slug
        if not title:
            # fallback from filename parts
            base = src.stem
            base = re.sub(r"(?i)^adr[-_ ]?\d{1,4}[-_ ]?", "", base)
            title = base or "untitled"
        slug = slugify(title)

        dst = ADR_DIR / f"adr-{int(assigned):04d}-{slug}.md"
        plan.append(PlanItem(src=src, dst=dst, reason=reason, assigned_id=int(assigned)))

    return plan, errors


def ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)


def move_file(item: PlanItem) -> None:
    if item.src == item.dst:
        return
    ensure_dir(item.dst)
    try:
        # Prefer git mv when possible for history
        subprocess.run(["git", "mv", str(item.src), str(item.dst)], check=True)
    except Exception:
        shutil.move(str(item.src), str(item.dst))


def main() -> None:
    ap = argparse.ArgumentParser(description="Normalize and consolidate ADR docs")
    ap.add_argument("--apply", action="store_true", help="Apply moves/renames")
    ap.add_argument("--include-historical", action="store_true", help="Include docs/HISTORICAL and docs/DMPX IMPORT trees")
    ap.add_argument("--include-archive", action="store_true", help="Include archive/ trees")
    args = ap.parse_args()

    plan, errors = build_plan(args.include_historical, args.include_archive)

    if errors:
        print("Errors:")
        for e in errors:
            print(f"  - {e}")
        print()

    print("Proposed ADR normalization plan:\n")
    for it in plan:
        rel_src = it.src.relative_to(REPO_ROOT)
        rel_dst = it.dst.relative_to(REPO_ROOT)
        status = "SKIP" if it.src == it.dst else "MOVE"
        print(f"[{status}] {rel_src} -> {rel_dst} :: {it.reason}")

    if not args.apply:
        print("\nDry run only. Use --apply to perform moves.")
        return

    # Apply
    print("\nApplying moves...")
    for it in plan:
        if it.src == it.dst:
            continue
        move_file(it)
        print(f"  moved {it.src.relative_to(REPO_ROOT)} -> {it.dst.relative_to(REPO_ROOT)}")

    print("\nADR cleanup complete.")


if __name__ == "__main__":
    main()

