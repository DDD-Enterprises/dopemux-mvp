#!/usr/bin/env python3
"""
Generate a proposal to improve low-information titles in docs.

Heuristics:
- Flag titles like: Readme, README, Overview, Summary, Specification, Index
- Propose: "{Section/Folder} — {Slug Title}" where Section is derived from parent dirs
- Do not apply changes; write proposal to docs/TITLE_IMPROVEMENTS_PROPOSAL.md

Usage:
  python scripts/docs_titles_improve.py            # writes proposal file
  python scripts/docs_titles_improve.py --top 200  # limit items
"""
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from typing import List, Tuple

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
OUT = DOCS / "TITLE_IMPROVEMENTS_PROPOSAL.md"

GENERIC = {"readme", "overview", "summary", "specification", "index", "readme root", "readme copy"}


def parse_frontmatter(text: str):
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm = text[4:end]
            body = text[end + 5 :]
            data = {}
            for line in fm.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    data[k.strip()] = v.strip().strip("'\"")
            return data, body
    return {}, text


def slug_to_title(slug: str) -> str:
    s = slug.replace("-", " ").replace("_", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s.title() if s else "Document"


def section_from_path(p: Path) -> str:
    try:
        rel = p.relative_to(DOCS)
    except Exception:
        return "Docs"
    parts = list(rel.parts)
    if not parts:
        return "Docs"
    top = parts[0]
    mapping = {
        "01-tutorials": "Tutorial",
        "02-how-to": "How-to",
        "03-reference": "Reference",
        "04-explanation": "Explanation",
        "90-adr": "ADR",
        "91-rfc": "RFC",
        "92-runbooks": "Runbook",
        "94-architecture": "Architecture",
    }
    sec = mapping.get(top, top)
    # add component/context if present
    if len(parts) >= 2 and parts[1] not in {"assets", "historical"} and not parts[1].lower().endswith('.md'):
        sec += f" / {parts[1].replace('-', ' ').title()}"
    return sec


def collect_candidates(limit: int) -> List[Tuple[Path, str, str]]:
    items: List[Tuple[Path, str, str]] = []
    for p in DOCS.rglob("*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        fm, _ = parse_frontmatter(text)
        title = fm.get("title", "")
        if not title:
            continue
        tnorm = title.strip().lower()
        if tnorm in GENERIC:
            slug = p.stem
            sec = section_from_path(p)
            # Special cases for better readability
            if tnorm in {"readme", "readme root", "readme copy", "overview"}:
                # Turn into Overview
                # Use subsection for nested dirs
                proposed = sec.replace(" / ", " ") + " Overview" if " / " in sec else sec + " Overview"
            elif tnorm == "index":
                proposed = sec.replace(" / ", " ") + " Index" if " / " in sec else sec + " Index"
            elif tnorm == "summary":
                # e.g., Implementation Summary
                parent = p.parent.name.replace("-", " ").title()
                proposed = f"{parent} Summary" if parent else "Summary"
            elif tnorm == "specification":
                parent = p.parent.name.replace("-", " ").title()
                proposed = f"{parent} Specification" if parent else "Specification"
            else:
                base_title = slug_to_title(slug)
                proposed = f"{sec} — {base_title}"
            items.append((p, title, proposed))
        if limit and len(items) >= limit:
            break
    return items


def main():
    ap = argparse.ArgumentParser(description="Propose improved titles for docs")
    ap.add_argument("--top", type=int, default=200)
    args = ap.parse_args()

    items = collect_candidates(args.top)
    lines = [
        "---",
        "id: title-improvements-proposal",
        "title: Title Improvements Proposal",
        "type: reference",
        "owner: '@hu3mann'",
        "---\n",
        "Proposed improvements for low-information titles (Readme, Overview, Summary, Specification, Index).",
        "",
        "| Path | Current Title | Proposed Title |",
        "|------|---------------|----------------|",
    ]
    for p, cur, prop in items:
        rel = p.relative_to(DOCS)
        lines.append(f"| `{rel}` | {cur} | {prop} |")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote proposal with {len(items)} items to {OUT}")


if __name__ == "__main__":
    main()
