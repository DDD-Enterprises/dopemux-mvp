#!/usr/bin/env python3
"""Sync repository skill templates into $CODEX_HOME/skills."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from typing import Dict, Iterable, List

FAMILIES: Dict[str, List[str]] = {
    "testgen": ["testgen", "testgen-gemini", "testgen-copilot", "testgen-claude"],
    "pr-docgen-sync": [
        "pr-docgen-sync",
        "pr-docgen-sync-gemini",
        "pr-docgen-sync-copilot",
        "pr-docgen-sync-claude",
    ],
    "workflow-kit": [
        "brief-drafter",
        "task-breakdown",
        "code-researcher",
        "research-reviewer",
        "implementation-planner",
        "plan-reviewer",
        "code-implementer",
        "quality-refactorer",
    ],
}


def _default_codex_home() -> Path:
    value = os.environ.get("CODEX_HOME")
    if value:
        return Path(value)
    return Path.home() / ".codex"


def _resolve_skill_names(families: Iterable[str]) -> List[str]:
    selected: List[str] = []
    for family in families:
        if family == "all":
            for names in FAMILIES.values():
                for name in names:
                    if name not in selected:
                        selected.append(name)
            continue

        if family not in FAMILIES:
            allowed = ", ".join(sorted([*FAMILIES.keys(), "all"]))
            raise ValueError(f"Unknown family '{family}'. Allowed: {allowed}")

        for name in FAMILIES[family]:
            if name not in selected:
                selected.append(name)
    return selected


def sync_skills(repo_root: Path, codex_home: Path, skill_names: Iterable[str], dry_run: bool = False) -> None:
    source_root = repo_root / "templates" / "skills"
    target_root = codex_home / "skills"

    for skill_name in skill_names:
        src = source_root / skill_name
        dst = target_root / skill_name
        if not src.exists():
            raise FileNotFoundError(f"Source skill not found: {src}")

        if dry_run:
            print(f"[dry-run] sync {src} -> {dst}")
            continue

        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)

        if not (dst / "SKILL.md").exists():
            raise RuntimeError(f"Synced skill missing SKILL.md: {dst}")

        print(f"synced {skill_name} -> {dst}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync repository skill templates to $CODEX_HOME/skills")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--codex-home")
    parser.add_argument(
        "--family",
        action="append",
        default=[],
        help="Skill family to sync (repeatable): testgen, pr-docgen-sync, workflow-kit, all",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    families = args.family or ["all"]
    skill_names = _resolve_skill_names(families)
    repo_root = Path(args.repo_root).resolve()
    codex_home = Path(args.codex_home).resolve() if args.codex_home else _default_codex_home().resolve()

    sync_skills(repo_root=repo_root, codex_home=codex_home, skill_names=skill_names, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
