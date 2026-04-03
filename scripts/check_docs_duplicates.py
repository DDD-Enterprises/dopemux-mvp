#!/usr/bin/env python3
"""Detect and remediate suffixed duplicate docs files.

This pass targets active docs files ending in configured duplicate suffixes.

- ``--check``: fail if duplicate-suffix files remain in the active docs tree.
- ``--apply``: archive duplicate copies and rename orphaned suffix files.
- ``--audit``: write per-file audit JSON.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_POLICY_PATH = "config/docs_hygiene/docs_placement_policy.yaml"
DEFAULT_AUDIT_PATH = "reports/docs-hygiene/duplicates_audit.json"


_PLACEMENT_MODULE_PATH = Path(__file__).resolve().parent / "check_docs_hygiene.py"
_PLACEMENT_SPEC = importlib.util.spec_from_file_location("check_docs_hygiene", _PLACEMENT_MODULE_PATH)
if not _PLACEMENT_SPEC or not _PLACEMENT_SPEC.loader:
    raise RuntimeError("Unable to import check_docs_hygiene module.")
_PLACEMENT_MODULE = importlib.util.module_from_spec(_PLACEMENT_SPEC)
sys.modules[_PLACEMENT_SPEC.name] = _PLACEMENT_MODULE
_PLACEMENT_SPEC.loader.exec_module(_PLACEMENT_MODULE)


@dataclass
class DuplicateRecord:
    path: str
    zone: str
    status: str
    base_path: Optional[str]
    target_path: Optional[str]
    reason: str
    similarity: Optional[float]


def _normalize_relpath(path: str) -> str:
    return _PLACEMENT_MODULE._normalize_relpath(path)


def _repo_root() -> Path:
    return _PLACEMENT_MODULE._repo_root()


def _load_policy(policy_path: Path) -> Dict[str, Any]:
    policy = _PLACEMENT_MODULE._load_policy(policy_path=policy_path)
    dupes = policy.setdefault("duplicate_suffixes", {})
    dupes.setdefault("suffixes", ["-2", "-3"])
    dupes.setdefault("similarity_threshold", 0.95)
    dupes.setdefault("archive_dir", "docs/archive/deduped-suffixes")
    dupes.setdefault("exclude_prefixes", ["docs/archive/", "docs/04-explanation/history/sourceFiles/"])
    return policy


def _iter_candidate_paths(
    repo_root: Path,
    policy: Dict[str, Any],
    requested_paths: Optional[List[str]] = None,
) -> Iterable[Path]:
    docs_root = _normalize_relpath(str(policy["docs_root"]))
    suffixes = tuple(str(value) for value in policy["duplicate_suffixes"]["suffixes"])
    exclude_prefixes = {_normalize_relpath(p) for p in policy["duplicate_suffixes"]["exclude_prefixes"]}

    if requested_paths:
        candidates: List[Path] = []
        for raw in requested_paths:
            path = repo_root / _normalize_relpath(raw)
            if not path.exists() or not path.is_file() or path.suffix != ".md":
                continue
            rel = _normalize_relpath(str(path.relative_to(repo_root)))
            if any(rel.startswith(prefix) for prefix in exclude_prefixes):
                continue
            stem = path.stem
            if any(stem.endswith(suffix) for suffix in suffixes):
                candidates.append(path)
        return sorted(candidates)

    base = repo_root / docs_root
    if not base.exists():
        return []

    matches: List[Path] = []
    for path in sorted(base.rglob("*.md")):
        rel = _normalize_relpath(str(path.relative_to(repo_root)))
        if any(rel.startswith(prefix) for prefix in exclude_prefixes):
            continue
        if any(path.stem.endswith(suffix) for suffix in suffixes):
            matches.append(path)
    return matches


def _strip_duplicate_suffix(path: Path, suffixes: List[str]) -> Optional[Path]:
    for suffix in sorted(suffixes, key=len, reverse=True):
        if path.stem.endswith(suffix):
            base_stem = path.stem[: -len(suffix)]
            if not base_stem:
                return None
            return path.with_name(f"{base_stem}{path.suffix}")
    return None


def _similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    return SequenceMatcher(None, a.strip(), b.strip()).ratio()


def classify_duplicate(rel_path: str, repo_root: Path, policy: Dict[str, Any]) -> DuplicateRecord:
    rel_path = _normalize_relpath(rel_path)
    path = repo_root / rel_path
    suffixes = [str(value) for value in policy["duplicate_suffixes"]["suffixes"]]
    threshold = float(policy["duplicate_suffixes"]["similarity_threshold"])
    archive_dir = _normalize_relpath(str(policy["duplicate_suffixes"]["archive_dir"]))

    base_candidate = _strip_duplicate_suffix(Path(rel_path), suffixes)
    if base_candidate is None:
        return DuplicateRecord(
            path=rel_path,
            zone="active",
            status="ok",
            base_path=None,
            target_path=None,
            reason="not-a-duplicate-suffix",
            similarity=None,
        )

    base_rel = _normalize_relpath(str(base_candidate))
    base_path = repo_root / base_rel
    archive_target = _normalize_relpath(f"{archive_dir}/{Path(rel_path).relative_to(policy['docs_root'])}")

    if not base_path.exists():
        return DuplicateRecord(
            path=rel_path,
            zone="active",
            status="rename_orphan",
            base_path=base_rel,
            target_path=base_rel,
            reason="base-missing-strip-suffix",
            similarity=None,
        )

    source_text = path.read_text(encoding="utf-8", errors="replace")
    base_text = base_path.read_text(encoding="utf-8", errors="replace")
    score = _similarity(source_text, base_text)
    if score >= threshold:
        return DuplicateRecord(
            path=rel_path,
            zone="active",
            status="archive_duplicate",
            base_path=base_rel,
            target_path=archive_target,
            reason="base-exists-near-identical",
            similarity=round(score, 4),
        )

    return DuplicateRecord(
        path=rel_path,
        zone="active",
        status="manual_review",
        base_path=base_rel,
        target_path=None,
        reason="base-exists-content-differs",
        similarity=round(score, 4),
    )


def build_records(
    repo_root: Path,
    policy: Dict[str, Any],
    requested_paths: Optional[List[str]] = None,
) -> List[DuplicateRecord]:
    records: List[DuplicateRecord] = []
    for path in _iter_candidate_paths(repo_root=repo_root, policy=policy, requested_paths=requested_paths):
        rel = _normalize_relpath(str(path.relative_to(repo_root)))
        records.append(classify_duplicate(rel_path=rel, repo_root=repo_root, policy=policy))
    return records


def write_audit(path: Path, records: List[DuplicateRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(record) for record in records]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _print_summary(records: List[DuplicateRecord]) -> None:
    archive = sum(1 for record in records if record.status == "archive_duplicate")
    rename = sum(1 for record in records if record.status == "rename_orphan")
    manual = sum(1 for record in records if record.status == "manual_review")
    print(
        "docs-duplicates: "
        f"total={len(records)} archive={archive} rename={rename} manual_review={manual}"
    )


def run_audit(
    repo_root: Path,
    policy: Dict[str, Any],
    audit_path: Path,
    requested_paths: Optional[List[str]] = None,
) -> int:
    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    write_audit(path=audit_path, records=records)
    _print_summary(records)
    print(f"docs-duplicates: wrote audit -> {audit_path}")
    return 0


def run_check(repo_root: Path, policy: Dict[str, Any], requested_paths: Optional[List[str]] = None) -> int:
    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    _print_summary(records)
    violations = [record for record in records if record.status in {"archive_duplicate", "rename_orphan", "manual_review"}]
    if not violations:
        print("docs-duplicates: OK")
        return 0

    print("docs-duplicates: FAILED")
    for idx, record in enumerate(violations, start=1):
        print(f"{idx}. {record.path}")
        print(f"   status: {record.status}")
        print(f"   reason: {record.reason}")
        if record.base_path:
            print(f"   base: {record.base_path}")
        if record.target_path:
            print(f"   target: {record.target_path}")
        if record.similarity is not None:
            print(f"   similarity: {record.similarity:.4f}")
        if idx >= 100:
            remaining = len(violations) - 100
            if remaining > 0:
                print(f"   ... and {remaining} more")
            break
    return 1


def run_apply(
    repo_root: Path,
    policy: Dict[str, Any],
    audit_path: Path,
    requested_paths: Optional[List[str]] = None,
) -> int:
    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    _print_summary(records)

    actionable = [record for record in records if record.status in {"archive_duplicate", "rename_orphan"}]
    if not actionable:
        write_audit(path=audit_path, records=records)
        print("docs-duplicates: no duplicate remediation needed")
        remaining = [record for record in records if record.status == "manual_review"]
        return 1 if remaining else 0

    old_to_target: Dict[str, str] = {}
    old_text_by_path: Dict[str, str] = {}
    link_target_map: Dict[str, str] = {}
    for record in actionable:
        if not record.target_path:
            continue
        old_to_target[record.path] = record.target_path
        old_text_by_path[record.path] = (repo_root / record.path).read_text(encoding="utf-8", errors="replace")
        if record.status == "archive_duplicate" and record.base_path:
            link_target_map[record.path] = record.base_path

    old_to_actual, moved_pairs = _PLACEMENT_MODULE.apply_moves(repo_root=repo_root, old_to_target=old_to_target)
    for old_rel, actual_rel in old_to_actual.items():
        link_target_map.setdefault(old_rel, actual_rel)

    markdown_updates, docs_index_updates = _PLACEMENT_MODULE.rewrite_links_and_indices(
        repo_root=repo_root,
        moved_pairs=moved_pairs,
        move_map=link_target_map,
        old_text_by_path=old_text_by_path,
    )

    final_records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    write_audit(path=audit_path, records=final_records)
    print(
        "docs-duplicates: apply complete "
        f"(moved={len(moved_pairs)} mapped={len(old_to_actual)} "
        f"markdown_updates={markdown_updates} docs_index_updates={docs_index_updates})"
    )

    remaining = [record for record in final_records if record.status in {"archive_duplicate", "rename_orphan", "manual_review"}]
    if remaining:
        print(f"docs-duplicates: WARNING remaining_violations={len(remaining)}")
        return 1
    print("docs-duplicates: apply finished cleanly")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and enforce duplicate docs suffix hygiene.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit", action="store_true", help="Write duplicate audit JSON and exit.")
    mode.add_argument("--check", action="store_true", help="Fail if duplicate-suffix files remain active.")
    mode.add_argument("--apply", action="store_true", help="Archive duplicates and rename orphan suffix files.")
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
    parser.add_argument("filenames", nargs="*", help="Specific files to check (ignored if --all-files is set).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = _repo_root()
        policy_path = (repo_root / args.policy).resolve()
        policy = _load_policy(policy_path=policy_path)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"docs-duplicates: error: {exc}", file=sys.stderr)
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
