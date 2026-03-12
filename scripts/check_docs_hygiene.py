#!/usr/bin/env python3
"""Policy-driven documentation placement audit and enforcement.

This tool supports three modes:
1. ``--audit``: scan docs tree and emit per-file audit JSON.
2. ``--check``: fail if any active docs are outside canonical placement.
3. ``--apply``: move misplaced docs, rewrite markdown links, and update docs index refs.

The quarantine corpus is intentionally immutable and reported as ``zone=quarantine``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml


DEFAULT_POLICY_PATH = "config/docs_hygiene/docs_placement_policy.yaml"
DEFAULT_AUDIT_PATH = "reports/docs-hygiene/audit.json"

MARKDOWN_LINK_RE = re.compile(r"(\[[^\]]+\])\(([^)]+)\)")


@dataclass
class PlacementRecord:
    path: str
    zone: str
    status: str
    target_path: Optional[str]
    rule_id: str


def _normalize_relpath(path: str) -> str:
    normalized = path.replace("\\", "/")
    normalized = normalized.strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.strip("/")
    return normalized


def _repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Unable to determine git repository root.")
    return Path(result.stdout.strip())


def _load_policy(policy_path: Path) -> Dict[str, Any]:
    with policy_path.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle) or {}

    required = [
        "docs_root",
        "canonical_roots",
        "quarantine_prefixes",
        "keep_docs_root_files",
        "relocation_rules",
    ]
    missing = [key for key in required if key not in policy]
    if missing:
        raise ValueError(f"Policy missing required keys: {', '.join(missing)}")

    policy.setdefault("root_overrides", {})
    policy.setdefault("root_type_targets", {})
    policy.setdefault("root_token_rules", [])
    policy.setdefault("default_root_target_dir", "docs/04-explanation/root-relocated")
    policy.setdefault("unknown_top_level_fallback_dir", "docs/archive/unclassified-top-level")
    policy.setdefault("audit_output", DEFAULT_AUDIT_PATH)
    return policy


def _parse_frontmatter_type(path: Path) -> Optional[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    if not text.startswith("---\n"):
        return None

    end = text.find("\n---\n", 4)
    if end == -1:
        return None

    try:
        payload = yaml.safe_load(text[4:end]) or {}
    except Exception:
        return None

    if not isinstance(payload, dict):
        return None
    value = payload.get("type")
    return value if isinstance(value, str) else None


def _join_to_dir(target_dir: str, filename: str) -> str:
    return _normalize_relpath(f"{target_dir.rstrip('/')}/{filename}")


def _match_relocation_rule(rel_path: str, policy: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    for rule in policy.get("relocation_rules", []):
        src_prefix = str(rule.get("from", ""))
        dst_prefix = str(rule.get("to", ""))
        if not src_prefix or not dst_prefix or not rel_path.startswith(src_prefix):
            continue

        suffix = rel_path[len(src_prefix) :]
        mode = str(rule.get("mode", "prefix"))
        if mode == "project-subdir":
            parts = suffix.split("/", 1)
            project = parts[0] if parts and parts[0] else "misc"
            rest = parts[1] if len(parts) == 2 else ""
            target = _normalize_relpath(f"{dst_prefix.rstrip('/')}/{project}")
            if rest:
                target = _normalize_relpath(f"{target}/{rest}")
        else:
            target = _normalize_relpath(f"{dst_prefix}{suffix}")

        return target, str(rule.get("id", "rule-unknown"))
    return None, None


def _classify_root_doc(
    rel_path: str,
    frontmatter_type: Optional[str],
    policy: Dict[str, Any],
) -> PlacementRecord:
    filename = Path(rel_path).name
    keepers = {_normalize_relpath(x) for x in policy.get("keep_docs_root_files", [])}
    if rel_path in keepers:
        return PlacementRecord(
            path=rel_path,
            zone="active",
            status="ok",
            target_path=None,
            rule_id="root-keeper",
        )

    root_overrides = {
        _normalize_relpath(k): _normalize_relpath(v)
        for k, v in policy.get("root_overrides", {}).items()
    }
    if rel_path in root_overrides:
        return PlacementRecord(
            path=rel_path,
            zone="active",
            status="needs_relocation",
            target_path=root_overrides[rel_path],
            rule_id="root-override",
        )

    type_targets = {
        str(key): _normalize_relpath(value)
        for key, value in policy.get("root_type_targets", {}).items()
    }
    if frontmatter_type and frontmatter_type in type_targets:
        return PlacementRecord(
            path=rel_path,
            zone="active",
            status="needs_relocation",
            target_path=_join_to_dir(type_targets[frontmatter_type], filename),
            rule_id=f"root-type-{frontmatter_type}",
        )

    filename_lower = filename.lower()
    for token_rule in policy.get("root_token_rules", []):
        tokens = [str(t).lower() for t in token_rule.get("contains_any", [])]
        if any(token in filename_lower for token in tokens):
            target_dir = _normalize_relpath(str(token_rule.get("target_dir", "")).strip())
            if target_dir:
                return PlacementRecord(
                    path=rel_path,
                    zone="active",
                    status="needs_relocation",
                    target_path=_join_to_dir(target_dir, filename),
                    rule_id=str(token_rule.get("id", "root-token-rule")),
                )

    default_target_dir = _normalize_relpath(str(policy.get("default_root_target_dir", "")))
    return PlacementRecord(
        path=rel_path,
        zone="active",
        status="needs_relocation",
        target_path=_join_to_dir(default_target_dir, filename),
        rule_id="root-default-fallback",
    )


def classify_path(
    rel_path: str,
    frontmatter_type: Optional[str],
    policy: Dict[str, Any],
) -> PlacementRecord:
    rel_path = _normalize_relpath(rel_path)

    for quarantine_prefix in policy.get("quarantine_prefixes", []):
        if rel_path.startswith(_normalize_relpath(quarantine_prefix)):
            return PlacementRecord(
                path=rel_path,
                zone="quarantine",
                status="quarantine",
                target_path=None,
                rule_id="quarantine",
            )

    relocation_target, rule_id = _match_relocation_rule(rel_path, policy)
    if relocation_target:
        return PlacementRecord(
            path=rel_path,
            zone="active",
            status="needs_relocation",
            target_path=relocation_target,
            rule_id=rule_id or "relocation-rule",
        )

    docs_root = _normalize_relpath(str(policy.get("docs_root", "docs")))
    parts = Path(rel_path).parts
    if len(parts) == 2 and parts[0] == docs_root:
        return _classify_root_doc(rel_path=rel_path, frontmatter_type=frontmatter_type, policy=policy)

    if len(parts) < 3 or parts[0] != docs_root:
        return PlacementRecord(
            path=rel_path,
            zone="active",
            status="ok",
            target_path=None,
            rule_id="outside-docs-root",
        )

    top_level = parts[1]
    canonical = set(policy.get("canonical_roots", []))
    if top_level in canonical:
        return PlacementRecord(
            path=rel_path,
            zone="active",
            status="ok",
            target_path=None,
            rule_id="canonical",
        )

    suffix = rel_path[len(f"{docs_root}/{top_level}/") :]
    fallback_dir = _normalize_relpath(str(policy.get("unknown_top_level_fallback_dir", "")))
    target = _normalize_relpath(f"{fallback_dir}/{top_level}/{suffix}")
    return PlacementRecord(
        path=rel_path,
        zone="active",
        status="needs_relocation",
        target_path=target,
        rule_id="unknown-top-level-fallback",
    )


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


def build_records(repo_root: Path, policy: Dict[str, Any], requested_paths: Optional[List[str]] = None) -> List[PlacementRecord]:
    records: List[PlacementRecord] = []
    docs_root = _normalize_relpath(str(policy["docs_root"]))

    for path in iter_docs(repo_root=repo_root, docs_root=docs_root, requested_paths=requested_paths):
        try:
            rel = _normalize_relpath(str(path.relative_to(repo_root)))
            parts = Path(rel).parts
            fm_type = _parse_frontmatter_type(path) if len(parts) == 2 and parts[0] == docs_root else None
            records.append(classify_path(rel_path=rel, frontmatter_type=fm_type, policy=policy))
        except ValueError:
            continue

    return records


def write_audit(path: Path, records: List[PlacementRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(record) for record in records]
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _print_summary(records: List[PlacementRecord]) -> None:
    active = [record for record in records if record.zone == "active"]
    quarantine = [record for record in records if record.zone == "quarantine"]
    violations = [record for record in active if record.status == "needs_relocation"]
    print(
        "docs-hygiene: "
        f"total={len(records)} active={len(active)} quarantine={len(quarantine)} "
        f"violations={len(violations)}"
    )


def _files_identical(src: Path, dst: Path) -> bool:
    try:
        return src.read_bytes() == dst.read_bytes()
    except Exception:
        return False


def _collision_target(path: Path, index: int) -> Path:
    return path.with_name(f"{path.stem}__moved-{index}{path.suffix}")


def _git_mv(repo_root: Path, src: Path, dst: Path) -> bool:
    result = subprocess.run(
        ["git", "mv", str(src.relative_to(repo_root)), str(dst.relative_to(repo_root))],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def _move_file(repo_root: Path, src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if _git_mv(repo_root, src, dst):
        return
    shutil.move(str(src), str(dst))


def apply_moves(
    repo_root: Path,
    old_to_target: Dict[str, str],
) -> Tuple[Dict[str, str], Dict[str, str]]:
    old_to_actual: Dict[str, str] = {}
    moved_pairs: Dict[str, str] = {}
    used_targets: set[str] = set()

    for old_rel in sorted(old_to_target.keys()):
        src = repo_root / old_rel
        if not src.exists():
            continue

        requested = repo_root / old_to_target[old_rel]
        candidate = requested
        counter = 1
        dedupe = False
        while True:
            candidate_rel = _normalize_relpath(str(candidate.relative_to(repo_root)))
            if candidate_rel in used_targets:
                counter += 1
                candidate = _collision_target(requested, counter)
                continue

            if candidate.exists() and candidate != src:
                if _files_identical(src, candidate):
                    dedupe = True
                    break
                counter += 1
                candidate = _collision_target(requested, counter)
                continue
            break

        actual_rel = _normalize_relpath(str(candidate.relative_to(repo_root)))
        if dedupe:
            src.unlink()
            old_to_actual[old_rel] = actual_rel
            used_targets.add(actual_rel)
            continue

        if candidate != src:
            _move_file(repo_root, src, candidate)
            moved_pairs[old_rel] = actual_rel

        old_to_actual[old_rel] = actual_rel
        used_targets.add(actual_rel)

    return old_to_actual, moved_pairs


def _is_external_target(base: str) -> bool:
    return base.startswith(("http://", "https://", "mailto:", "tel:", "data:", "javascript:", "#"))


def _split_link_target(raw_target: str) -> Tuple[str, str, str, bool]:
    target = raw_target.strip()
    angle_wrapped = target.startswith("<") and target.endswith(">")
    inner = target[1:-1] if angle_wrapped else target

    suffix = ""
    if " " in inner:
        base, suffix_body = inner.split(" ", 1)
        suffix = " " + suffix_body
    else:
        base = inner

    fragment = ""
    if "#" in base:
        base, frag = base.split("#", 1)
        fragment = "#" + frag

    return base, fragment, suffix, angle_wrapped


def _resolve_link_target(repo_root: Path, source_rel: str, base: str) -> Optional[str]:
    source_dir = Path(source_rel).parent
    if base.startswith("/"):
        if not base.startswith("/docs/"):
            return None
        candidate = (repo_root / base.lstrip("/")).resolve()
    else:
        candidate = (repo_root / source_dir / base).resolve()
    try:
        return _normalize_relpath(str(candidate.relative_to(repo_root.resolve())))
    except ValueError:
        return None


def _relative_link(from_rel: str, to_rel: str) -> str:
    from_dir = Path(from_rel).parent
    rel = os.path.relpath(str(Path(to_rel)), str(from_dir)).replace("\\", "/")
    return rel if rel != "." else Path(to_rel).name


def rewrite_markdown_links(
    text: str,
    source_context_rel: str,
    source_output_rel: str,
    move_map: Dict[str, str],
    repo_root: Path,
    rebase_all_local_links: bool,
) -> Tuple[str, bool]:
    changed = False

    def replace(match: re.Match[str]) -> str:
        nonlocal changed
        label = match.group(1)
        raw_target = match.group(2)
        base, fragment, suffix, angle_wrapped = _split_link_target(raw_target)
        if not base or _is_external_target(base):
            return match.group(0)

        resolved = _resolve_link_target(repo_root=repo_root, source_rel=source_context_rel, base=base)
        if not resolved:
            return match.group(0)

        mapped = move_map.get(resolved, resolved)
        if not rebase_all_local_links and mapped == resolved:
            return match.group(0)

        rewritten_base = _relative_link(from_rel=source_output_rel, to_rel=mapped)
        rewritten_target = f"{rewritten_base}{fragment}{suffix}"
        if angle_wrapped:
            rewritten_target = f"<{rewritten_target}>"

        if rewritten_target != raw_target:
            changed = True
            return f"{label}({rewritten_target})"
        return match.group(0)

    rewritten = MARKDOWN_LINK_RE.sub(replace, text)
    return rewritten, changed


def _rewrite_docs_index(repo_root: Path, move_map: Dict[str, str]) -> bool:
    docs_index = repo_root / "docs/docs_index.yaml"
    if not docs_index.exists():
        return False

    data = yaml.safe_load(docs_index.read_text(encoding="utf-8"))
    changed = False

    def walk(value: Any) -> Any:
        nonlocal changed
        if isinstance(value, dict):
            return {k: walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, str):
            normalized = _normalize_relpath(value)
            if normalized in move_map:
                changed = True
                return move_map[normalized]
        return value

    new_data = walk(data)
    if not changed:
        return False

    docs_index.write_text(
        yaml.safe_dump(new_data, sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )
    return True


def rewrite_links_and_indices(
    repo_root: Path,
    moved_pairs: Dict[str, str],
    move_map: Dict[str, str],
    old_text_by_path: Dict[str, str],
) -> Tuple[int, int]:
    updated_markdown = 0
    moved_targets = set(moved_pairs.values())

    for old_rel, new_rel in moved_pairs.items():
        target_path = repo_root / new_rel
        if not target_path.exists():
            continue
        text = old_text_by_path.get(old_rel, target_path.read_text(encoding="utf-8", errors="replace"))
        rewritten, changed = rewrite_markdown_links(
            text=text,
            source_context_rel=old_rel,
            source_output_rel=new_rel,
            move_map=move_map,
            repo_root=repo_root,
            rebase_all_local_links=True,
        )
        if changed:
            target_path.write_text(rewritten, encoding="utf-8")
            updated_markdown += 1

    for path in sorted(repo_root.rglob("*.md")):
        rel = _normalize_relpath(str(path.relative_to(repo_root)))
        if rel in moved_targets:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rewritten, changed = rewrite_markdown_links(
            text=text,
            source_context_rel=rel,
            source_output_rel=rel,
            move_map=move_map,
            repo_root=repo_root,
            rebase_all_local_links=False,
        )
        if changed:
            path.write_text(rewritten, encoding="utf-8")
            updated_markdown += 1

    updated_index = 1 if _rewrite_docs_index(repo_root=repo_root, move_map=move_map) else 0
    return updated_markdown, updated_index


def run_audit(repo_root: Path, policy: Dict[str, Any], audit_path: Path, requested_paths: Optional[List[str]] = None) -> int:
    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    write_audit(path=audit_path, records=records)
    _print_summary(records)
    print(f"docs-hygiene: wrote audit -> {audit_path}")
    return 0


def run_check(repo_root: Path, policy: Dict[str, Any], requested_paths: Optional[List[str]] = None) -> int:
    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    _print_summary(records)
    violations = [record for record in records if record.zone == "active" and record.status == "needs_relocation"]
    if not violations:
        if requested_paths:
            print(f"docs-hygiene: checked {len(records)} files, OK")
        else:
            print("docs-hygiene: OK")
        return 0

    print("docs-hygiene: FAILED")
    for index, record in enumerate(violations, start=1):
        print(f"{index}. {record.path}")
        print(f"   rule: {record.rule_id}")
        if record.target_path:
            print(f"   target: {record.target_path}")
        if index >= 100:
            remaining = len(violations) - 100
            if remaining > 0:
                print(f"   ... and {remaining} more")
            break
    return 1


def run_apply(repo_root: Path, policy: Dict[str, Any], audit_path: Path, requested_paths: Optional[List[str]] = None) -> int:
    records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    violations = [record for record in records if record.zone == "active" and record.status == "needs_relocation"]
    _print_summary(records)
    if not violations:
        write_audit(path=audit_path, records=records)
        print("docs-hygiene: no relocation needed")
        return 0

    old_to_target: Dict[str, str] = {}
    old_text_by_path: Dict[str, str] = {}
    for record in violations:
        if not record.target_path:
            continue
        old_to_target[record.path] = record.target_path
        src = repo_root / record.path
        if src.exists():
            old_text_by_path[record.path] = src.read_text(encoding="utf-8", errors="replace")

    old_to_actual, moved_pairs = apply_moves(repo_root=repo_root, old_to_target=old_to_target)
    if old_to_actual:
        updated_markdown, updated_index = rewrite_links_and_indices(
            repo_root=repo_root,
            moved_pairs=moved_pairs,
            move_map=old_to_actual,
            old_text_by_path=old_text_by_path,
        )
    else:
        updated_markdown, updated_index = 0, 0

    final_records = build_records(repo_root=repo_root, policy=policy, requested_paths=requested_paths)
    write_audit(path=audit_path, records=final_records)
    print(
        "docs-hygiene: apply complete "
        f"(moved={len(moved_pairs)} mapped={len(old_to_actual)} "
        f"markdown_updates={updated_markdown} docs_index_updates={updated_index})"
    )
    remaining = [record for record in final_records if record.zone == "active" and record.status == "needs_relocation"]
    if remaining:
        print(f"docs-hygiene: WARNING remaining violations={len(remaining)}")
        return 1
    print("docs-hygiene: apply finished cleanly")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit and enforce docs placement hygiene.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audit", action="store_true", help="Write per-file audit JSON and exit.")
    mode.add_argument("--check", action="store_true", help="Fail if any file needs relocation.")
    mode.add_argument("--apply", action="store_true", help="Apply relocation and link/index rewrites.")
    parser.add_argument(
        "--policy",
        default=DEFAULT_POLICY_PATH,
        help=f"Placement policy path (default: {DEFAULT_POLICY_PATH})",
    )
    parser.add_argument(
        "--audit-out",
        default=None,
        help=f"Audit artifact path (default from policy or {DEFAULT_AUDIT_PATH})",
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
        print(f"docs-hygiene: error: {exc}", file=sys.stderr)
        return 2

    audit_out = args.audit_out or str(policy.get("audit_output", DEFAULT_AUDIT_PATH))
    audit_path = (repo_root / audit_out).resolve()
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
