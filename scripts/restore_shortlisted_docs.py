#!/usr/bin/env python3
"""
Restore shortlisted external docs (marked with XXX) into docs/ using Option A.

Reads docs/EXTERNAL_DOCS_SHORTLIST.md, finds rows with XXX, copies source files
into appropriate location under docs/ (01/02/03/04), normalizes filenames,
and ensures YAML frontmatter exists.

Usage:
  python scripts/restore_shortlisted_docs.py       # apply copies
  python scripts/restore_shortlisted_docs.py --dry # preview only
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
SHORTLIST = DOCS / "EXTERNAL_DOCS_SHORTLIST.md"


def slugify_filename(name: str) -> str:
    base, ext = os.path.splitext(name)
    base = base.strip().lower().replace("_", "-")
    base = re.sub(r"\s+", "-", base)
    base = re.sub(r"[^a-z0-9\-]", "-", base)
    base = re.sub(r"-+", "-", base).strip("-") or "untitled"
    return base + ".md"


def choose_target(src: Path) -> Path:
    name = src.name.lower()
    # Place based on keywords
    if any(k in name for k in ["getting-started", "quick-start", "setup", "deploy", "installation", "guide", "troubleshoot"]):
        base = DOCS / "02-how-to"
    elif any(k in name for k in ["api", "reference", "spec", "schema", "readme", "registry", "summary", "status"]):
        base = DOCS / "03-reference"
    elif "architecture" in name or any(k in name for k in ["overview", "design", "roadmap"]):
        base = DOCS / "04-explanation" / ("architecture" if "architecture" in name else "")
        base = base if base.suffix == "" else base.parent
    else:
        base = DOCS / "04-explanation"
    base.mkdir(parents=True, exist_ok=True)
    return base / slugify_filename(name)


def unique_destination(dst: Path, src: Path) -> Path:
    """Ensure destination path does not clobber an existing different file.
    If dst exists with different content, derive a unique name using parent slug
    and an incrementing suffix if needed.
    """
    if not dst.exists():
        return dst
    try:
        if dst.read_bytes() == src.read_bytes():
            return dst  # identical; ok to treat as same
    except Exception:
        pass
    base = dst.stem
    ext = dst.suffix
    parent_slug = re.sub(r"[^a-z0-9]+", "-", src.parent.name.lower()).strip("-") or "ext"
    candidate = dst.with_name(f"{parent_slug}-{base}{ext}")
    i = 2
    while candidate.exists():
        candidate = dst.with_name(f"{parent_slug}-{base}-{i}{ext}")
        i += 1
    return candidate


def parse_marked_paths(shortlist_path: Path) -> list[Path]:
    marked = []
    text = shortlist_path.read_text(encoding="utf-8", errors="ignore")
    for line in text.splitlines():
        if "XXX" not in line:
            continue
        m = re.search(r"`([^`]+)`", line)
        if m:
            p = REPO / m.group(1)
            if p.exists():
                marked.append(p)
    return marked


def ensure_frontmatter(path: Path) -> None:
    # Reuse docs_frontmatter_guard in fix mode for just this file
    try:
        subprocess.run(["python3", str(REPO / "scripts" / "docs_frontmatter_guard.py"), "--fix"], check=True)
    except Exception:
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Restore shortlisted external docs into docs/")
    ap.add_argument("--dry", action="store_true", help="Only print actions")
    args = ap.parse_args()

    if not SHORTLIST.exists():
        print("Shortlist not found:", SHORTLIST)
        raise SystemExit(1)

    sources = parse_marked_paths(SHORTLIST)
    if not sources:
        print("No XXX-marked items found in shortlist.")
        return

    print(f"Restoring {len(sources)} docs:")
    for src in sources:
        dst = choose_target(src)
        dst = unique_destination(dst, src)
        action = f"COPY {src.relative_to(REPO)} -> {dst.relative_to(REPO)}"
        if args.dry:
            print("-", action)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        ensure_frontmatter(dst)
        print("-", action)

    if not args.dry:
        print("\nDone. Consider updating mkdocs.yml navigation if needed.")


if __name__ == "__main__":
    main()
