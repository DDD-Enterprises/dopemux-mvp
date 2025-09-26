#!/usr/bin/env python3
"""
Scan for high‑quality markdown docs outside docs/ and shortlist unique items.

Criteria (heuristic):
- Not under docs/
- Sufficient length (>= 300 words)
- Structured (>= 3 headings or has sections/code blocks)
- Not a duplicate of a docs/ page (exact or near‑duplicate by title/content)

Outputs:
- Prints a ranked shortlist to stdout
- Writes docs/EXTERNAL_DOCS_SHORTLIST.md (unless --no-write)

Usage:
  python scripts/external_docs_shortlist.py             # create shortlist file
  python scripts/external_docs_shortlist.py --no-write  # only print
  python scripts/external_docs_shortlist.py --top 50    # limit results
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
SHORTLIST_PATH = DOCS / "EXTERNAL_DOCS_SHORTLIST.md"

EXCLUDE_DIR_PATTERNS = [
    ".git", ".venv", "node_modules", "dist", "build", ".next", ".nuxt",
    ".pytest_cache", ".mypy_cache", ".worktrees",
]

LOW_VALUE_HINTS = [
    "checkpoint", "session", "log", "backup", "deleted", "manifest",
    "processing-artifacts", "tmp", ".DS_Store", "draft", "wip",
]


@dataclass
class DocInfo:
    path: Path
    title: str
    words: int
    headings: int
    code_blocks: int
    lists: int
    quality_score: float
    sha1: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def strip_frontmatter(text: str) -> str:
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            return text[end + 5 :]
    return text


def first_heading(text: str) -> str:
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()
    return ""


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def hash_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore").strip()).hexdigest()


def analyze_markdown(path: Path) -> Optional[DocInfo]:
    if path.suffix.lower() != ".md":
        return None
    text = read_text(path)
    if not text:
        return None
    body = strip_frontmatter(text)
    norm = normalize_whitespace(body)
    words = len(norm.split())
    if words < 300:
        return None

    headings = sum(1 for ln in body.splitlines() if ln.strip().startswith("#"))
    code_blocks = body.count("```") // 2
    lists = sum(1 for ln in body.splitlines() if re.match(r"^\s*[-*+]\s+", ln))
    title = first_heading(text) or path.stem.replace("-", " ").title()

    # Quality scoring heuristic
    score = 0.0
    score += min(words / 200.0, 20)  # cap contribution from length
    score += headings * 1.5
    score += code_blocks * 2.0
    score += min(lists * 0.5, 6)

    text_low = body.lower()
    if any(h in text_low for h in ["overview", "architecture", "implementation", "design", "api", "use cases", "background"]):
        score += 5
    if any(h in path.as_posix().lower() for h in LOW_VALUE_HINTS) or any(h in text_low for h in LOW_VALUE_HINTS):
        score -= 6

    sha1 = hash_text(norm)
    return DocInfo(path=path, title=title, words=words, headings=headings, code_blocks=code_blocks, lists=lists, quality_score=score, sha1=sha1)


def walk_markdown(base: Path) -> List[Path]:
    out: List[Path] = []
    for root, dirs, files in os.walk(base):
        # filter excluded dirs
        dirs[:] = [d for d in dirs if not any(pat in (Path(root) / d).as_posix() for pat in EXCLUDE_DIR_PATTERNS)]
        for fn in files:
            if fn.lower().endswith(".md"):
                out.append(Path(root) / fn)
    return out


def build_docs_index() -> Tuple[Dict[str, DocInfo], Dict[str, List[DocInfo]]]:
    """Index docs/ pages by sha1 and by normalized title."""
    sha_index: Dict[str, DocInfo] = {}
    title_index: Dict[str, List[DocInfo]] = {}
    for p in walk_markdown(DOCS):
        info = analyze_markdown(p)
        if not info:
            # include short docs for title dedupe only
            text = read_text(p)
            t = first_heading(text)
            if t:
                key = re.sub(r"\W+", " ", t.lower()).strip()
                title_index.setdefault(key, [])
            continue
        sha_index[info.sha1] = info
        key = re.sub(r"\W+", " ", info.title.lower()).strip()
        title_index.setdefault(key, []).append(info)
    return sha_index, title_index


def is_near_duplicate(candidate: DocInfo, title_index: Dict[str, List[DocInfo]]) -> bool:
    key = re.sub(r"\W+", " ", candidate.title.lower()).strip()
    matches = title_index.get(key) or []
    if not matches:
        return False
    # Compare similarity with best title match
    cand_text = normalize_whitespace(strip_frontmatter(read_text(candidate.path)))
    for ref in matches:
        ref_text = normalize_whitespace(strip_frontmatter(read_text(ref.path)))
        ratio = difflib.SequenceMatcher(a=cand_text, b=ref_text).ratio()
        if ratio >= 0.88:
            return True
    return False


def shortlist_external(top_n: int, no_write: bool) -> List[DocInfo]:
    sha_index, title_index = build_docs_index()
    results: List[DocInfo] = []
    for p in walk_markdown(REPO):
        # skip anything under docs/
        try:
            p.relative_to(DOCS)
            continue
        except ValueError:
            pass
        info = analyze_markdown(p)
        if not info:
            continue
        # skip by sha duplicate
        if info.sha1 in sha_index:
            continue
        # skip near duplicates by title/content
        if is_near_duplicate(info, title_index):
            continue
        results.append(info)

    # rank by quality score then words
    results.sort(key=lambda d: (d.quality_score, d.words), reverse=True)
    if top_n > 0:
        results = results[:top_n]

    if not no_write:
        lines = [
            "---",
            f"id: external-docs-shortlist",
            f"title: External Docs Shortlist",
            f"type: reference",
            f"owner: '@hu3mann'",
            "---\n",
            "This shortlist collects high-quality markdown documents found outside the main docs/ tree for review.",
            "",
            "Scoring heuristic favors length, structure (headings/code), and presence of sections like overview/architecture/implementation. Duplicates of docs/ content (exact or near by title/content) are excluded.",
            "",
            "| Score | Words | Headings | Code | Path | Title |",
            "|------:|------:|---------:|-----:|------|-------|",
        ]
        for d in results:
            rel = d.path.relative_to(REPO)
            lines.append(f"| {d.quality_score:.1f} | {d.words} | {d.headings} | {d.code_blocks} | `{rel}` | {d.title} |")
        SHORTLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        SHORTLIST_PATH.write_text("\n".join(lines), encoding="utf-8")
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="Shortlist external high-quality docs")
    ap.add_argument("--no-write", action="store_true", help="Do not write shortlist file")
    ap.add_argument("--top", type=int, default=50, help="Limit number of results (default 50)")
    args = ap.parse_args()

    results = shortlist_external(top_n=args.top, no_write=args.no_write)

    print(f"Found {len(results)} external high-quality unique docs.\n")
    for d in results:
        print(f"- {d.quality_score:.1f} | {d.words:4d}w | {d.headings:2d}h | {d.code_blocks:2d}c | {d.path.relative_to(REPO)} | {d.title}")
    if not args.no_write:
        print(f"\nShortlist written to: {SHORTLIST_PATH}")


if __name__ == "__main__":
    main()

