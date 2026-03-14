#!/usr/bin/env python3
"""Enforce kebab-case markdown filenames for active docs.

This pass is intentionally separate from placement hygiene:
- --check: fail if active docs filenames are not kebab-case.
- --apply: rename files to kebab-case and rewrite links/path references.
- --audit: write per-file filename audit JSON.
"""

from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import os
import re
import shutil
import sys
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml


DEFAULT_POLICY_PATH = "config/docs_hygiene/docs_placement_policy.yaml"
DEFAULT_AUDIT_PATH = "reports/docs-hygiene/filename_audit.json"


_PLACEMENT_MODULE_PATH = Path(__file__).resolve().parent / "check_docs_hygiene.py"
_PLACEMENT_SPEC = importlib.util.spec_from_file_location("check_docs_hygiene", _PLACEMENT_MODULE_PATH)
if not _PLACEMENT_SPEC or not _PLACEMENT_SPEC.loader:
    raise RuntimeError("Unable to import check_docs_hygiene module.")
_PLACEMENT_MODULE = importlib.util.module_from_spec(_PLACEMENT_SPEC)
sys.modules[_PLACEMENT_SPEC.name] = _PLACEMENT_MODULE
_PLACEMENT_SPEC.loader.exec_module(_PLACEMENT_MODULE)


@dataclass
class FilenameRecord:
    path: str
    zone: str
    status: str
    target_path: Optional[str]
    reason: str


def _normalize_relpath(path: str) -> str:
    return _PLACEMENT_MODULE._normalize_relpath(path)


def _repo_root() -> Path:
    return _PLACEMENT_MODULE._repo_root()


def _load_policy(policy_path: Path) -> Dict[str, Any]:
    policy = _PLACEMENT_MODULE._load_policy(policy_path=policy_path)
    policy.setdefault("filename_exemptions", [])
    return policy


def _slugify_stem(stem: str) -> str:
    # Normalize unicode then drop non-ascii for deterministic repo-safe names.
    translit_map = str.maketrans(
        {
            "ø": "o",
            "Ø": "o",
            "æ": "ae",
            "Æ": "ae",
            "å": "a",
            "Å": "a",
            "ö": "o",
            "Ö": "o",
            "ü": "u",
            "Ü": "u",
        }
    )
    normalized = unicodedata.normalize("NFKD", stem.translate(translit_map))
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.lower()
    ascii_only = ascii_only.replace("_", "-")
    ascii_only = re.sub(r"\s+", "-", ascii_only)
    ascii_only = re.sub(r"[^a-z0-9-]+", "-", ascii_only)
    ascii_only = re.sub(r"-{2,}", "-", ascii_only).strip("-")
    return ascii_only or "untitled"


def _is_exempt(rel_path: str, policy: Dict[str, Any]) -> bool:
    keepers = {_normalize_relpath(x) for x in policy.get("keep_docs_root_files", [])}
    if rel_path in keepers:
        return True
    for pattern in policy.get("filename_exemptions", []):
        if fnmatch.fnmatch(rel_path, str(pattern)):
            return True
    return False


def _zone_for_path(rel_path: str, policy: Dict[str, Any]) -> str:
    for quarantine_prefix in policy.get("quarantine_prefixes", []):
        if rel_path.startswith(_normalize_relpath(quarantine_prefix)):
            return "quarantine"
    return "active"


def classify_filename(rel_path: str, policy: Dict[str, Any]) -> FilenameRecord:
    rel_path = _normalize_relpath(rel_path)
    zone = _zone_for_path(rel_path=rel_path, policy=policy)
    if zone == "quarantine":
        return FilenameRecord(path=rel_path, zone=zone, status="quarantine", target_path=None, reason="quarantine")

    if _is_exempt(rel_path=rel_path, policy=policy):
        return FilenameRecord(path=rel_path, zone=zone, status="exempt", target_path=None, reason="exempt")

    file_name = Path(rel_path).name
    expected = f"{_slugify_stem(Path(file_name).stem)}.md"
    if file_name == expected:
        return FilenameRecord(path=rel_path, zone=zone, status="ok", target_path=None, reason="kebab-ok")

    target = _normalize_relpath(str(Path(rel_path).with_name(expected)))
    return FilenameRecord(path=rel_path, zone=zone, status="needs_rename", target_path=target, reason="kebab-required")


def iter_docs(repo_root: Path, docs_root: str, requested_paths: Optional[List[str]] = None) -> Iterable[Path]:
    if requested_paths:
        paths = []
        for p in requested_paths:
            path = repo_root / _normalize_relpath(p)
            if path.exists() and path.is_file() and path.suffix == ".md":
                paths.append(path)
        return sorted(paths)
    base = repo_root / _normalize_relpath(docs_root)
    if not base.exists():
        return []
    return sorted(base.rglob("*.md"))


def build_records(repo_root: Path, policy: Dict[str, Any], requested_paths: Optional[List[str]] = None) -> List[FilenameRecord]:
    records: List[FilenameRecord] = []
    docs_root = _normalize_relpath(str(policy["docs_root"]))
    for path in iter_docs(repo_root=repo_root, docs_root=docs_root, requested_paths=requested_paths):
        try:
            rel = _normalize_relpath(str(path.relative_to(repo_root)))
            records.append(classify_filename(rel_path=rel, policy=policy))
        except ValueError:
            continue
    return records


def write_audit(path: Path, records: List[FilenameRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(record) for record in records]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _print_summary(records: List[FilenameRecord]) -> None:
    active = [r for r in records if r.zone == "active"]
    violations = [r for r in active if r.status == "needs_rename"]
    exempt = [r for r in active if r.status == "exempt"]
    quarantine = [r for r in records if r.zone == "quarantine"]
    print(
        "docs-filename-hygiene: "
        f"total={len(records)} active={len(active)} quarantine={len(quarantine)} "
        f"exempt={len(exempt)} violations={len(violations)}"
    )


def _next_available_target(
    desired_rel: str,
    occupied: set[str],
    source_paths: set[str],
    repo_root: Path,
) -> str:
    candidate = _normalize_relpath(desired_rel)
    candidate_path = repo_root / candidate
    if candidate not in occupied and (not candidate_path.exists() or candidate in source_paths):
        return candidate

    p = Path(candidate)
    stem = p.stem
    suffix = p.suffix
    parent = p.parent
    index = 2
    while True:
        alt = _normalize_relpath(str(parent / f"{stem}-{index}{suffix}"))
        alt_path = repo_root / alt
        if alt in occupied:
            index += 1
            continue
        if alt_path.exists() and alt not in source_paths:
            index += 1
            continue
        return alt


def _safe_move(repo_root: Path, src_rel: str, dst_rel: str) -> None:
    src = repo_root / src_rel
    dst = repo_root / dst_rel
    dst.parent.mkdir(parents=True, exist_ok=True)

    moved = _PLACEMENT_MODULE._git_mv(repo_root=repo_root, src=src, dst=dst)
    if moved:
        return
    shutil.move(str(src), str(dst))


def apply_renames(
    repo_root: Path,
    old_to_desired: Dict[str, str],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    old_to_final: Dict[str, str] = {}
    occupied: set[str] = set()
    source_paths = set(old_to_desired.keys())

    for old_rel in sorted(old_to_desired.keys()):
        desired = old_to_desired[old_rel]
        final_target = _next_available_target(
            desired_rel=desired,
            occupied=occupied,
            source_paths=source_paths,
            repo_root=repo_root,
        )
        old_to_final[old_rel] = final_target
        occupied.add(final_target)

    # Move in two phases via temp names to avoid cycles/case-only conflicts.
    temp_map: Dict[str, str] = {}
    index = 1
    for old_rel in sorted(old_to_final.keys()):
        src = repo_root / old_rel
        if not src.exists():
            continue
        temp_rel = _normalize_relpath(str(Path(old_rel).with_name(f".tmp-filename-rename-{index}.md")))
        while (repo_root / temp_rel).exists() or temp_rel in temp_map.values():
            index += 1
            temp_rel = _normalize_relpath(str(Path(old_rel).with_name(f".tmp-filename-rename-{index}.md")))
        _safe_move(repo_root=repo_root, src_rel=old_rel, dst_rel=temp_rel)
        temp_map[old_rel] = temp_rel
        index += 1

    moved_pairs: Dict[str, str] = {}
    for old_rel, temp_rel in temp_map.items():
        final_rel = old_to_final[old_rel]
        _safe_move(repo_root=repo_root, src_rel=temp_rel, dst_rel=final_rel)
        moved_pairs[old_rel] = final_rel

    return old_to_final, moved_pairs


def _rewrite_plain_path_refs(repo_root: Path, path_map: Dict[str, str]) -> int:
    text_exts = {
        ".md",
        ".py",
        ".sh",
        ".yaml",
        ".yml",
        ".toml",
        ".json",
        ".txt",
        ".ini",
        ".cfg",
    }
    ignore_prefixes = {
        ".git/",
        "htmlcov/",
        ".pytest_cache/",
        ".venv/",
        "node_modules/",
        "reports/docs-hygiene/",
    }
    replacements = sorted(path_map.items(), key=lambda x: len(x[0]), reverse=True)
    updated = 0

    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = _normalize_relpath(str(path.relative_to(repo_root)))
        if any(rel.startswith(prefix) for prefix in ignore_prefixes):
            continue
        if path.suffix.lower() not in text_exts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        new_text = text
        for old, new in replacements:
            if old in new_text:
                new_text = new_text.replace(old, new)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            updated += 1
    return updated


def run_audit(repo_root: Path, policy: Dict[str, Any], audit_path: Path, requested_paths: Optional[List[str]] = None) -> int:
    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    write_audit(path=audit_path, records=records)
    _print_summary(records)
    print(f"docs-filename-hygiene: wrote audit -> {audit_path}")
    return 0


def run_check(repo_root: Path, policy: Dict[str, Any], requested_paths: Optional[List[str]] = None) -> int:
    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    _print_summary(records)
    violations = [record for record in records if record.zone == "active" and record.status == "needs_rename"]
    if not violations:
        if requested_paths:
            print(f"docs-filename-hygiene: checked {len(records)} files, OK")
        else:
            print("docs-filename-hygiene: OK")
        return 0
    print("docs-filename-hygiene: FAILED")
    for idx, record in enumerate(violations, start=1):
        print(f"{idx}. {record.path}")
        print(f"   target: {record.target_path}")
        if idx >= 100:
            remaining = len(violations) - 100
            if remaining > 0:
                print(f"   ... and {remaining} more")
            break
    return 1


def run_apply(repo_root: Path, policy: Dict[str, Any], audit_path: Path, requested_paths: Optional[List[str]] = None) -> int:
    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    _print_summary(records)
    violations = [record for record in records if record.zone == "active" and record.status == "needs_rename"]
    if not violations:
        write_audit(path=audit_path, records=records)
        print("docs-filename-hygiene: no filename renames needed")
        return 0

    old_to_desired: Dict[str, str] = {}
    old_text_by_path: Dict[str, str] = {}
    for record in violations:
        if not record.target_path:
            continue
        old_to_desired[record.path] = record.target_path
        src = repo_root / record.path
        if src.exists():
            old_text_by_path[record.path] = src.read_text(encoding="utf-8", errors="replace")

    old_to_final, moved_pairs = apply_renames(repo_root=repo_root, old_to_desired=old_to_desired)

    if old_to_final:
        markdown_updates, docs_index_updates = _PLACEMENT_MODULE.rewrite_links_and_indices(
            repo_root=repo_root,
            moved_pairs=moved_pairs,
            move_map=old_to_final,
            old_text_by_path=old_text_by_path,
        )
    else:
        markdown_updates, docs_index_updates = 0, 0

    plain_ref_updates = _rewrite_plain_path_refs(repo_root=repo_root, path_map=old_to_final)

    final_records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    write_audit(path=audit_path, records=final_records)
    print(
        "docs-filename-hygiene: apply complete "
        f"(renamed={len(moved_pairs)} mapped={len(old_to_final)} "
        f"markdown_updates={markdown_updates} docs_index_updates={docs_index_updates} "
        f"plain_ref_updates={plain_ref_updates})"
    )
    remaining = [record for record in final_records if record.zone == "active" and record.status == "needs_rename"]
    if remaining:
        print(f"docs-filename-hygiene: WARNING remaining violations={len(remaining)}")
        return 1
    print("docs-filename-hygiene: apply finished cleanly")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and enforce docs filename kebab-case.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit", action="store_true", help="Write filename audit JSON and exit.")
    mode.add_argument("--check", action="store_true", help="Fail if any filename violates kebab-case.")
    mode.add_argument("--apply", action="store_true", help="Rename files and rewrite references.")
    parser.add_argument(
        "--policy",
        default=DEFAULT_POLICY_PATH,
        help=f"Placement policy path (default: {DEFAULT_POLICY_PATH})",
    )
    parser.add_argument(
        "--audit-out",
        default=DEFAULT_AUDIT_PATH,
        help=f"Audit artifact path (default: {DEFAULT_AUDIT_PATH})",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Accepted for CI/pre-commit parity; if not set, positional args are checked.",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Specific files to check (ignored if --all-files is set).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = _repo_root()
        policy_path = (repo_root / args.policy).resolve()
        policy = _load_policy(policy_path=policy_path)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"docs-filename-hygiene: error: {exc}", file=sys.stderr)
        return 2

    audit_path = (repo_root / args.audit_out).resolve()
    requested_paths = None if args.all_files else args.filenames

    if args.audit:
        return run_audit(repo_root=repo_root, policy=policy, audit_path=audit_path, requested_paths=requested_paths)
    if args.check:
        return run_check(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    if args.apply:
        return run_apply(repo_root=repo_root, policy=policy, audit_path=audit_path, requested_paths=requested_paths)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
