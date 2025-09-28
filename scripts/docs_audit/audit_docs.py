#!/usr/bin/env python3
"""
Docs Audit CLI

Features (standard library only):
- Scan one or more roots for Markdown-like docs (.md, .mdx, .txt)
- Extract basic metadata (frontmatter presence, title, date, word count)
- Propose descriptive, date-in-title filenames (dry-run by default)
- Detect exact and near-duplicates using word shingles + Jaccard
- Generate JSON/CSV/Markdown reports for review
- Enforce minimal frontmatter (dry-run or apply)

Usage examples:
  python scripts/docs_audit/audit_docs.py scan --roots docs CCDOCS CHECKPOINT archive --out reports/docs-audit
  python scripts/docs_audit/audit_docs.py report --out reports/docs-audit
  python scripts/docs_audit/audit_docs.py plan-rename --out reports/docs-audit --template "{date} - {title}.md"
  python scripts/docs_audit/audit_docs.py enforce-frontmatter --out reports/docs-audit --apply

Notes:
- This tool does NOT move or delete files unless you pass an --apply flag on specific commands.
- Near-duplicate detection uses 5-word shingles with a Jaccard threshold (default 0.82).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


DOC_EXTS = {".md", ".mdx", ".txt"}
IGNORE_NAMES = {".ds_store", "thumbs.db"}
FRONTMATTER_BOUNDARY = re.compile(r"^---\s*$")
TITLE_H1_RE = re.compile(r"^\s*#\s+(.+?)\s*$")
FRONTMATTER_TITLE_RE = re.compile(r"^title:\s*(.+?)\s*$", re.IGNORECASE)
FRONTMATTER_DATE_RE = re.compile(r"^date:\s*(.+?)\s*$", re.IGNORECASE)


def _is_text_doc(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.name.lower() in IGNORE_NAMES:
        return False
    ext = path.suffix.lower()
    if ext in DOC_EXTS:
        return True
    # Treat extensionless small files as text, skip big/binary-ish files
    if ext == "":
        try:
            return path.stat().st_size < 512_000  # < 500 KB
        except Exception:
            return False
    return False


def _git_first_commit_date(path: Path) -> Optional[str]:
    """Return first commit date (YYYY-MM-DD) for file, or None if not in git."""
    try:
        # Use --diff-filter=A to find first addition commit
        out = subprocess.check_output([
            "git", "log", "--diff-filter=A", "--follow", "--format=%ad",
            "--date=short", "--", str(path)
        ], stderr=subprocess.DEVNULL, text=True)
        line = out.strip().splitlines()[-1] if out.strip() else ""
        if line:
            return line.strip()
    except Exception:
        pass
    # Fall back to last modified time
    try:
        ts = dt.datetime.fromtimestamp(path.stat().st_mtime)
        return ts.strftime("%Y-%m-%d")
    except Exception:
        return None


def _slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _split_frontmatter_and_body(text: str) -> Tuple[Optional[str], str]:
    """Return (frontmatter_text_or_None, body_text)."""
    lines = text.splitlines()
    if len(lines) >= 3 and FRONTMATTER_BOUNDARY.match(lines[0]):
        # find next boundary
        for i in range(1, len(lines)):
            if FRONTMATTER_BOUNDARY.match(lines[i]):
                fm = "\n".join(lines[1:i])
                body = "\n".join(lines[i+1:])
                return fm, body
    return None, text


def _parse_frontmatter_fields(frontmatter: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    title, date = None, None
    if not frontmatter:
        return title, date
    for line in frontmatter.splitlines():
        m_t = FRONTMATTER_TITLE_RE.match(line)
        if m_t:
            title = m_t.group(1).strip().strip('"')
            continue
        m_d = FRONTMATTER_DATE_RE.match(line)
        if m_d:
            date = m_d.group(1).strip().strip('"')
    return title, date


def _extract_title_from_body(body: str) -> Optional[str]:
    for line in body.splitlines():
        m = TITLE_H1_RE.match(line)
        if m:
            return m.group(1).strip()
    return None


def _normalize_md(text: str) -> str:
    # Drop frontmatter
    _, body = _split_frontmatter_and_body(text)
    # Remove code fences to reduce noise
    body = re.sub(r"```[\s\S]*?```", " ", body)
    # Remove inline code/backticks
    body = re.sub(r"`[^`]*`", " ", body)
    # Strip markdown syntax characters
    body = re.sub(r"[>*_#`~\[\]()+!=|{}]", " ", body)
    # Collapse whitespace
    body = re.sub(r"\s+", " ", body)
    return body.strip().lower()


def _word_shingles(text: str, k: int = 5) -> List[str]:
    words = [w for w in re.split(r"\W+", text) if w]
    if len(words) < k:
        return []
    return [" ".join(words[i:i+k]) for i in range(len(words)-k+1)]


def jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


@dataclass
class DocItem:
    path: str
    relpath: str
    ext: str
    has_frontmatter: bool
    fm_title: Optional[str]
    fm_date: Optional[str]
    h1_title: Optional[str]
    inferred_title: str
    inferred_date: Optional[str]
    word_count: int
    content_hash: str
    shingles: List[str]


def scan_roots(roots: List[Path], repo_root: Path) -> List[DocItem]:
    items: List[DocItem] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not _is_text_doc(path):
                continue
            try:
                text = _read_text(path)
            except Exception:
                text = ""
            fm_text, body = _split_frontmatter_and_body(text)
            has_fm = fm_text is not None
            fm_title, fm_date = _parse_frontmatter_fields(fm_text)
            h1_title = _extract_title_from_body(body)
            inferred_title = fm_title or h1_title or path.stem.replace("_", " ").replace("-", " ").strip()
            inferred_date = fm_date or _git_first_commit_date(path)
            norm = _normalize_md(text)
            wc = len(re.findall(r"\w+", norm))
            c_hash = hashlib.md5(norm.encode("utf-8", errors="ignore")).hexdigest()
            shingles = _word_shingles(norm, k=5)
            # Normalize to repo-relative path
            try:
                relp = str(path.resolve().relative_to(repo_root.resolve()))
            except Exception:
                # Fallback: best-effort string
                relp = str(path)
            items.append(DocItem(
                path=str(path),
                relpath=relp,
                ext=path.suffix.lower() or "",
                has_frontmatter=has_fm,
                fm_title=fm_title,
                fm_date=fm_date,
                h1_title=h1_title,
                inferred_title=inferred_title,
                inferred_date=inferred_date,
                word_count=wc,
                content_hash=c_hash,
                shingles=shingles,
            ))
    return items


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = sorted({k for r in rows for k in r.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def save_inventory(items: List[DocItem], out_dir: Path) -> None:
    write_json(out_dir / "inventory.json", [asdict(i) for i in items])
    # quick CSV for spreadsheet review
    rows = []
    for i in items:
        rows.append({
            "relpath": i.relpath,
            "has_frontmatter": str(i.has_frontmatter),
            "fm_title": i.fm_title or "",
            "fm_date": i.fm_date or "",
            "h1_title": i.h1_title or "",
            "inferred_title": i.inferred_title,
            "inferred_date": i.inferred_date or "",
            "word_count": str(i.word_count),
        })
    write_csv(out_dir / "inventory.csv", rows)


def detect_duplicates(items: List[DocItem], threshold: float = 0.82) -> Tuple[List[List[int]], List[Tuple[int,int,float]]]:
    # exact dup groups by content_hash
    by_hash: Dict[str, List[int]] = {}
    for idx, it in enumerate(items):
        by_hash.setdefault(it.content_hash, []).append(idx)
    groups: List[List[int]] = [g for g in by_hash.values() if len(g) > 1]

    # near duplicates via shingle Jaccard
    n = len(items)
    pairs: List[Tuple[int, int, float]] = []
    # simple union-find
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        si = items[i].shingles
        if not si:
            continue
        for j in range(i+1, n):
            sj = items[j].shingles
            if not sj:
                continue
            sim = jaccard(si, sj)
            if sim >= threshold:
                pairs.append((i, j, sim))
                union(i, j)

    # build clusters from union-find (only >1)
    clusters: Dict[int, List[int]] = {}
    for i in range(n):
        r = find(i)
        clusters.setdefault(r, []).append(i)
    near_groups = [g for g in clusters.values() if len(g) > 1]

    return (groups + near_groups), pairs


def make_report(items: List[DocItem], groups: List[List[int]], pairs: List[Tuple[int,int,float]]) -> str:
    total = len(items)
    missing_fm = sum(1 for i in items if not i.has_frontmatter)
    missing_date = sum(1 for i in items if not i.fm_date and not i.inferred_date)
    small_docs = sum(1 for i in items if i.word_count < 120)

    lines = []
    lines.append(f"# Docs Audit Summary ({dt.datetime.now().strftime('%Y-%m-%d %H:%M')})")
    lines.append("")
    lines.append(f"- Total docs scanned: {total}")
    lines.append(f"- Missing frontmatter: {missing_fm}")
    lines.append(f"- Missing date (frontmatter or inferred): {missing_date}")
    lines.append(f"- Likely weak (word_count<120): {small_docs}")
    lines.append(f"- Duplicate/near-duplicate groups: {len(groups)}")
    lines.append("")
    lines.append("## Top Missing Frontmatter (examples)")
    for i in items[:500]:
        if not i.has_frontmatter:
            lines.append(f"- {i.relpath} (wc={i.word_count}, title='{i.inferred_title[:60]}')")
    lines.append("")
    lines.append("## Duplicate/Near-Duplicate Groups")
    for gi, g in enumerate(groups, 1):
        lines.append(f"### Group {gi}")
        for idx in g:
            it = items[idx]
            lines.append(f"- {it.relpath} (wc={it.word_count}, title='{it.inferred_title[:70]}')")
        lines.append("")
    return "\n".join(lines)


def plan_renames(items: List[DocItem], template: str = "{date} - {title}.md") -> List[Dict[str,str]]:
    rows = []
    for it in items:
        # Compose title and date
        title = it.fm_title or it.h1_title or it.inferred_title
        date = it.fm_date or it.inferred_date or dt.datetime.now().strftime("%Y-%m-%d")
        # Normalize
        title_clean = re.sub(r"\s+", " ", title).strip()
        # Use slug for filename body; keep human title in frontmatter
        slug = _slugify(title_clean)[:100]
        # Build new filename from template
        ext = it.ext or ".md"
        filename = template.format(date=date, title=slug)
        if not filename.endswith(ext):
            filename = f"{filename}{ext}"
        new_rel = str(Path(it.relpath).with_name(filename))
        rows.append({
            "old_path": it.relpath,
            "new_path": new_rel,
            "title": title_clean,
            "date": date,
        })
    return rows


def apply_renames(repo_root: Path, plan_csv: Path) -> List[Tuple[str,str,str]]:
    """Return list of (old,new,status)"""
    results = []
    with plan_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            old_rel = row["old_path"].strip()
            new_rel = row["new_path"].strip()
            old_path = repo_root / old_rel
            new_path = repo_root / new_rel
            try:
                new_path.parent.mkdir(parents=True, exist_ok=True)
                if old_path.exists():
                    if old_path.resolve() == new_path.resolve():
                        results.append((old_rel, new_rel, "skipped (same)"))
                    else:
                        os.rename(old_path, new_path)
                        results.append((old_rel, new_rel, "renamed"))
                else:
                    results.append((old_rel, new_rel, "missing"))
            except Exception as e:
                results.append((old_rel, new_rel, f"error: {e}"))
    return results


def ensure_frontmatter(path: Path, title: str, date: str, dry_run: bool = True) -> bool:
    """Insert minimal frontmatter if missing. Return True if changed."""
    text = _read_text(path)
    fm_text, body = _split_frontmatter_and_body(text)
    if fm_text is not None:
        # Already has frontmatter; skip modification to avoid clobbering.
        return False
    fm = ["---", f"title: {title}", f"date: {date}", "tags: []", "status: draft", "summary: ''", "---", ""]
    new_text = "\n".join(fm) + body
    if dry_run:
        return True
    path.write_text(new_text, encoding="utf-8")
    return True


def cmd_scan(args):
    repo_root = Path.cwd()
    roots = [Path(r) for r in args.roots]
    items = scan_roots(roots, repo_root)
    out_dir = Path(args.out)
    save_inventory(items, out_dir)
    groups, pairs = detect_duplicates(items, threshold=args.dup_threshold)
    # Save pairs and groups
    write_json(out_dir / "duplicates_groups.json", groups)
    rows = []
    for i, j, s in pairs:
        rows.append({
            "a": items[i].relpath,
            "b": items[j].relpath,
            "similarity": f"{s:.4f}",
        })
    write_csv(out_dir / "duplicates_pairs.csv", rows)
    print(f"Scanned {len(items)} docs. Inventory and duplicates written to {out_dir}")


def cmd_report(args):
    out_dir = Path(args.out)
    inv_path = out_dir / "inventory.json"
    items = [DocItem(**d) for d in json.loads(inv_path.read_text(encoding="utf-8"))]
    groups = json.loads((out_dir / "duplicates_groups.json").read_text(encoding="utf-8")) if (out_dir / "duplicates_groups.json").exists() else []
    pairs_rows = []
    if (out_dir / "duplicates_pairs.csv").exists():
        with (out_dir / "duplicates_pairs.csv").open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            pairs_rows = [(i, j, float(s)) for i, j, s in []]
    report_md = make_report(items, groups, [])
    out = out_dir / "report.md"
    out.write_text(report_md, encoding="utf-8")
    print(f"Report written to {out}")


def cmd_plan_rename(args):
    out_dir = Path(args.out)
    inv_path = out_dir / "inventory.json"
    items = [DocItem(**d) for d in json.loads(inv_path.read_text(encoding="utf-8"))]
    rows = plan_renames(items, template=args.template)
    csv_path = out_dir / "rename_plan.csv"
    write_csv(csv_path, rows)
    print(f"Rename plan written to {csv_path} (dry-run; review before applying)")


def cmd_apply_rename(args):
    repo_root = Path.cwd()
    plan_csv = Path(args.plan)
    results = apply_renames(repo_root, plan_csv)
    out = plan_csv.parent / "rename_results.csv"
    rows = [{"old": a, "new": b, "status": s} for a, b, s in results]
    write_csv(out, rows)
    print(f"Apply-rename finished. Results at {out}")


def cmd_enforce_frontmatter(args):
    out_dir = Path(args.out)
    inv_path = out_dir / "inventory.json"
    items = [DocItem(**d) for d in json.loads(inv_path.read_text(encoding="utf-8"))]
    changed_rows = []
    for it in items:
        if it.has_frontmatter:
            continue
        title = it.fm_title or it.h1_title or it.inferred_title
        date = it.fm_date or it.inferred_date or dt.datetime.now().strftime("%Y-%m-%d")
        changed = ensure_frontmatter(Path(it.relpath), title=title, date=date, dry_run=(not args.apply))
        if changed:
            changed_rows.append({
                "path": it.relpath,
                "title": title,
                "date": date,
                "applied": str(bool(args.apply)),
            })
    write_csv(out_dir / ("frontmatter_applied.csv" if args.apply else "frontmatter_dryrun.csv"), changed_rows)
    print(("Applied" if args.apply else "Dry-run for") + f" frontmatter on {len(changed_rows)} files. See {out_dir}.")


def cmd_triage_template(args):
    out_dir = Path(args.out)
    inv_path = out_dir / "inventory.json"
    items = [DocItem(**d) for d in json.loads(inv_path.read_text(encoding="utf-8"))]
    groups = json.loads((out_dir / "duplicates_groups.json").read_text(encoding="utf-8")) if (out_dir / "duplicates_groups.json").exists() else []
    # Build index by relpath
    idx_by_rel = {it.relpath: i for i, it in enumerate(items)}
    # Map each index to a group id if present
    group_id_by_index: Dict[int, int] = {}
    for gi, grp in enumerate(groups, start=1):
        for idx in grp:
            group_id_by_index[idx] = gi
    rows = []
    for i, it in enumerate(items):
        rows.append({
            "relpath": it.relpath,
            "title": (it.fm_title or it.h1_title or it.inferred_title),
            "date": (it.fm_date or it.inferred_date or ""),
            "word_count": str(it.word_count),
            "dup_group": str(group_id_by_index.get(i, "")),
            "pile": "unassigned",  # hell_no | love_it | wow_forgot | not_sure
        })
    out_csv = out_dir / "triage_template.csv"
    write_csv(out_csv, rows)
    print(f"Triage template written to {out_csv}. Fill 'pile' column and save.")


def main():
    p = argparse.ArgumentParser(description="Docs Audit CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("scan", help="Scan roots for docs and build inventory + duplicates")
    ps.add_argument("--roots", nargs="+", default=["docs"], help="Root directories to scan")
    ps.add_argument("--out", default="reports/docs-audit", help="Output directory")
    ps.add_argument("--dup-threshold", type=float, default=0.82, help="Near-duplicate Jaccard threshold")
    ps.set_defaults(func=cmd_scan)

    pr = sub.add_parser("report", help="Generate Markdown summary report from inventory")
    pr.add_argument("--out", default="reports/docs-audit", help="Output directory")
    pr.set_defaults(func=cmd_report)

    pp = sub.add_parser("plan-rename", help="Create rename plan CSV with date-in-title")
    pp.add_argument("--out", default="reports/docs-audit", help="Output directory")
    pp.add_argument("--template", default="{date} - {title}.md", help="Filename template using {date} and {title} (slug)")
    pp.set_defaults(func=cmd_plan_rename)

    pa = sub.add_parser("apply-rename", help="Apply rename plan CSV")
    pa.add_argument("--plan", required=True, help="Path to rename_plan.csv")
    pa.set_defaults(func=cmd_apply_rename)

    pf = sub.add_parser("enforce-frontmatter", help="Add minimal frontmatter where missing")
    pf.add_argument("--out", default="reports/docs-audit", help="Output directory (reads inventory)")
    pf.add_argument("--apply", action="store_true", help="Write changes to files (default: dry-run)")
    pf.set_defaults(func=cmd_enforce_frontmatter)

    pt = sub.add_parser("triage-template", help="Create triage CSV with duplicate-group ids and empty 'pile'")
    pt.add_argument("--out", default="reports/docs-audit", help="Output directory")
    pt.set_defaults(func=cmd_triage_template)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
