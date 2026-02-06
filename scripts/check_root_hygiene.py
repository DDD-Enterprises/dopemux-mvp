#!/usr/bin/env python3
"""Enforce repository root hygiene.

This check is intentionally strict about what can live at repo root.
Use it from pre-commit (changed paths) and CI (--all-files).
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

DEFAULT_POLICY_PATH = "config/repo_hygiene/root_hygiene_policy.json"


def _run_git(repo_root: Path, args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", *args],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _detect_repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("Could not determine git repo root")
    return Path(result.stdout.strip())


def _match_any(value: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(value, pattern) for pattern in patterns)


def _normalize_path(path: str, repo_root: Path) -> str | None:
    if not path:
        return None

    raw = Path(path)
    if raw.is_absolute():
        try:
            rel = raw.relative_to(repo_root)
        except ValueError:
            return None
    else:
        rel = raw

    normalized = rel.as_posix().strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.strip("/")
    if not normalized or normalized.startswith(".git/"):
        return None
    return normalized


def _load_policy(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        policy = json.load(handle)

    required = ["allowed_root_dirs", "allowed_root_files"]
    missing = [key for key in required if key not in policy]
    if missing:
        raise ValueError(f"Policy missing required keys: {', '.join(missing)}")

    policy.setdefault("legacy_root_files", [])
    policy.setdefault("blocked_root_file_patterns", [])
    policy.setdefault("blocked_root_dir_patterns", [])
    policy.setdefault("destination_hints", [])
    return policy


def _collect_candidate_paths(
    repo_root: Path,
    cli_paths: list[str],
    all_files: bool,
    include_untracked: bool,
) -> list[str]:
    if cli_paths:
        normalized = [_normalize_path(path, repo_root) for path in cli_paths]
        return sorted({path for path in normalized if path})

    if all_files:
        tracked = _run_git(repo_root, ["ls-files"])
        candidates = list(tracked)
        if include_untracked:
            untracked = _run_git(repo_root, ["ls-files", "--others", "--exclude-standard"])
            candidates.extend(untracked)
        normalized = [_normalize_path(path, repo_root) for path in candidates]
        return sorted({path for path in normalized if path})

    staged = _run_git(repo_root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
    if staged:
        normalized = [_normalize_path(path, repo_root) for path in staged]
        return sorted({path for path in normalized if path})

    changed = _run_git(repo_root, ["diff", "--name-only", "--diff-filter=ACMR"])
    normalized = [_normalize_path(path, repo_root) for path in changed]
    return sorted({path for path in normalized if path})


def _destination_hint(path: str, policy: dict[str, Any]) -> str:
    basename = Path(path).name
    for rule in policy.get("destination_hints", []):
        patterns = rule.get("patterns", [])
        if not isinstance(patterns, list):
            continue
        if any(fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(path, pattern) for pattern in patterns):
            destination = str(rule.get("destination", "tmp/"))
            purpose = str(rule.get("purpose", "")).strip()
            if purpose:
                return f"{destination} ({purpose})"
            return destination
    return "tmp/"


def _is_allowed_root_file(name: str, policy: dict[str, Any]) -> bool:
    allowed = list(policy.get("allowed_root_files", [])) + list(policy.get("legacy_root_files", []))
    return _match_any(name, allowed)


def _is_allowed_root_dir(name: str, policy: dict[str, Any]) -> bool:
    return _match_any(name, list(policy.get("allowed_root_dirs", [])))


def _evaluate(paths: list[str], policy: dict[str, Any]) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []

    for path in paths:
        parts = Path(path).parts
        if not parts:
            continue

        top = parts[0]
        is_root_file = len(parts) == 1

        if is_root_file:
            if _is_allowed_root_file(top, policy):
                continue

            reason = "root files must be explicitly allowlisted"
            if _match_any(top, list(policy.get("blocked_root_file_patterns", []))):
                reason = "matches a blocked root-file pattern"

            violations.append(
                {
                    "path": path,
                    "reason": reason,
                    "hint": _destination_hint(path, policy),
                }
            )
            continue

        if _match_any(top, list(policy.get("blocked_root_dir_patterns", []))):
            violations.append(
                {
                    "path": path,
                    "reason": "writes to a blocked top-level artifact directory",
                    "hint": _destination_hint(path, policy),
                }
            )
            continue

        if not _is_allowed_root_dir(top, policy):
            violations.append(
                {
                    "path": path,
                    "reason": f"top-level directory '{top}' is not allowlisted",
                    "hint": _destination_hint(path, policy),
                }
            )

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Check repository root hygiene.")
    parser.add_argument("paths", nargs="*", help="Optional paths to validate.")
    parser.add_argument(
        "--policy",
        default=DEFAULT_POLICY_PATH,
        help=f"Policy file path (default: {DEFAULT_POLICY_PATH}).",
    )
    parser.add_argument(
        "--all-files",
        action="store_true",
        help="Validate all tracked files in the repository.",
    )
    parser.add_argument(
        "--include-untracked",
        action="store_true",
        help="When used with --all-files, also validate untracked non-ignored files.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress success output.",
    )
    args = parser.parse_args()

    try:
        repo_root = _detect_repo_root()
        policy_path = (repo_root / args.policy).resolve()
        policy = _load_policy(policy_path)
        paths = _collect_candidate_paths(
            repo_root=repo_root,
            cli_paths=args.paths,
            all_files=args.all_files,
            include_untracked=args.include_untracked,
        )
    except Exception as exc:  # pylint: disable=broad-except
        print(f"root-hygiene: error: {exc}", file=sys.stderr)
        return 2

    if not paths:
        if not args.quiet:
            print("root-hygiene: no candidate files to check")
        return 0

    violations = _evaluate(paths, policy)

    if not violations:
        if not args.quiet:
            print(f"root-hygiene: OK ({len(paths)} paths checked)")
        return 0

    print("root-hygiene: FAILED")
    print(f"Policy: {policy_path}")
    for index, violation in enumerate(violations, start=1):
        print(f"{index}. {violation['path']}")
        print(f"   reason: {violation['reason']}")
        print(f"   suggested destination: {violation['hint']}")

    print(
        "Move files to the suggested destination, or explicitly update "
        "config/repo_hygiene/root_hygiene_policy.json when the new root entry is intentional."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
