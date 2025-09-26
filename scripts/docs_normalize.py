#!/usr/bin/env python3
"""
Normalize documentation filenames and categorize within docs/ (Option A).

Actions:
- Enforce lower-kebab-case .md filenames (spaces/underscores -> hyphens)
- Keep numeric section folders as-is (01..04, 90..99)
- Prefer single source of truth for components under docs/03-reference/components/
- Heuristic moves from docs/ root or misc folders into:
  * 01-tutorials, 02-how-to, 03-reference, 04-explanation
- Skips ADR/RFC/Runbook/C4/arc42 structure except filename normalization

Usage:
  Dry run: python scripts/docs_normalize.py
  Apply:   python scripts/docs_normalize.py --apply

Notes:
- Only operates within the docs/ directory.
- Tries `git mv` when possible, falls back to shutil.move.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"


SECTION_DIRS = {
    "01-tutorials": DOCS / "01-tutorials",
    "02-how-to": DOCS / "02-how-to",
    "03-reference": DOCS / "03-reference",
    "04-explanation": DOCS / "04-explanation",
    # preserved specialized sections
    "90-adr": DOCS / "90-adr",
    "91-rfc": DOCS / "91-rfc",
    "92-runbooks": DOCS / "92-runbooks",
    "94-architecture": DOCS / "94-architecture",
}

COMPONENTS_DIR = SECTION_DIRS["03-reference"] / "components"


def ensure_dirs():
    for p in SECTION_DIRS.values():
        p.mkdir(parents=True, exist_ok=True)
    COMPONENTS_DIR.mkdir(parents=True, exist_ok=True)


def slugify_filename(name: str) -> str:
    base, ext = os.path.splitext(name)
    base = base.strip().lower()
    base = base.replace("_", "-")
    base = re.sub(r"\s+", "-", base)
    base = re.sub(r"[^a-z0-9\-]", "-", base)
    base = re.sub(r"-+", "-", base).strip("-")
    if not base:
        base = "untitled"
    ext = ".md" if ext.lower() != ".md" else ".md"
    return base + ext


def is_markdown(p: Path) -> bool:
    return p.is_file() and p.suffix.lower() == ".md"


def is_in_any_section(p: Path) -> bool:
    try:
        rel = p.relative_to(DOCS)
    except ValueError:
        return False
    parts = rel.parts
    return parts and parts[0] in SECTION_DIRS


def target_for_misc(p: Path) -> Optional[Path]:
    """Heuristically place docs under a primary section.
    Only used for files directly under docs/ or under non-section folders.
    """
    rel = p.relative_to(DOCS)
    name = rel.name.lower()
    # Keep index/readme at root
    if name in {"readme.md", "index.md"}:
        return p

    # Heuristics by keywords
    if any(k in name for k in ["install", "setup", "how-to", "guide", "troubleshoot"]):
        return SECTION_DIRS["02-how-to"] / slugify_filename(name)
    if any(k in name for k in ["tutorial", "getting-started", "user-guide", "user_guide"]):
        return SECTION_DIRS["01-tutorials"] / slugify_filename(name)
    if any(k in name for k in ["api", "reference", "spec", "schema", "mcp", "tools", "inventory", "status"]):
        return SECTION_DIRS["03-reference"] / slugify_filename(name)
    if any(k in name for k in ["architecture", "design", "overview", "summary", "explanation"]):
        # Route architecture-* to architecture/ subdir
        subdir = SECTION_DIRS["04-explanation"] / "architecture" if "architecture" in name else SECTION_DIRS["04-explanation"]
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / slugify_filename(name)
    # Default to explanation
    return SECTION_DIRS["04-explanation"] / slugify_filename(name)


def try_git_mv(src: Path, dst: Path) -> bool:
    try:
        subprocess.run(["git", "mv", str(src), str(dst)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception:
        return False


def move_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not try_git_mv(src, dst):
        shutil.move(str(src), str(dst))


@dataclass
class PlanItem:
    src: Path
    dst: Path
    action: str  # RENAME | MOVE | MOVE+RENAME | NONE


def build_plan() -> List[PlanItem]:
    plan: List[PlanItem] = []
    for root, _, files in os.walk(DOCS):
        root_path = Path(root)
        for fn in files:
            if not fn.lower().endswith('.md'):
                continue
            src = root_path / fn
            # Skip templates and historical/import artifacts
            rel_str = str(src.relative_to(DOCS))
            if "/templates/" in rel_str:
                continue

            new_name = slugify_filename(fn)
            dst = src
            action = "NONE"

            if is_in_any_section(src):
                # Keep section, normalize filename only
                if new_name != fn:
                    dst = src.with_name(new_name)
                    action = "RENAME"
            else:
                # Place into a section via heuristic
                target = target_for_misc(src)
                if target and target != src:
                    # If only name changes within same folder, call rename; otherwise move+rename
                    action = "MOVE" if target.parent == src.parent and target.name == new_name else "MOVE+RENAME"
                    dst = target
                elif new_name != fn:
                    dst = src.with_name(new_name)
                    action = "RENAME"

            if action != "NONE" and dst != src:
                plan.append(PlanItem(src=src, dst=dst, action=action))
    return plan


def main() -> None:
    ap = argparse.ArgumentParser(description="Normalize docs filenames and categorize within docs/")
    ap.add_argument("--apply", action="store_true", help="Apply planned moves/renames")
    args = ap.parse_args()

    ensure_dirs()
    plan = build_plan()

    print("Proposed documentation normalization plan:\n")
    for it in plan:
        print(f"[{it.action}] {it.src.relative_to(REPO_ROOT)} -> {it.dst.relative_to(REPO_ROOT)}")

    if not args.apply:
        print(f"\nDry run only. Items: {len(plan)}. Use --apply to make changes.")
        return

    print("\nApplying changes...")
    for it in plan:
        move_file(it.src, it.dst)
        print(f"  {it.action}: {it.src.relative_to(REPO_ROOT)} -> {it.dst.relative_to(REPO_ROOT)}")

    print("\nNormalization complete.")


if __name__ == "__main__":
    main()

