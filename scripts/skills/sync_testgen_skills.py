#!/usr/bin/env python3
"""Sync testgen skill templates into $CODEX_HOME/skills."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

SKILL_NAMES = ["testgen", "testgen-gemini", "testgen-copilot", "testgen-claude"]


def _default_codex_home() -> Path:
    value = os.environ.get("CODEX_HOME")
    if value:
        return Path(value)
    return Path.home() / ".codex"


def sync_skills(repo_root: Path, codex_home: Path, dry_run: bool = False) -> None:
    source_root = repo_root / "templates" / "skills"
    target_root = codex_home / "skills"

    for skill_name in SKILL_NAMES:
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
    parser = argparse.ArgumentParser(description="Sync testgen skill templates to $CODEX_HOME/skills")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--codex-home")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    codex_home = Path(args.codex_home).resolve() if args.codex_home else _default_codex_home().resolve()

    sync_skills(repo_root=repo_root, codex_home=codex_home, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
