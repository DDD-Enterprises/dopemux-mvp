#!/usr/bin/env python3
"""Sync packaged personas from the canonical authoring surface.

Canonical source:  .claude/personas/*.agent.md   (authored, runtime-primary)
Packaged subset:   src/dopemux/personas/*.agent.md (wheel data, dopemux init fallback)

The packaged subset is a GENERATED artifact. Never hand-edit files under
src/dopemux/personas/ — edit the canonical file and run this script.

Usage:
    python scripts/sync_personas.py          # apply: canonical -> packaged
    python scripts/sync_personas.py --check  # verify only, non-zero on drift
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIR = REPO_ROOT / ".claude" / "personas"
PACKAGED_DIR = REPO_ROOT / "src" / "dopemux" / "personas"

# Declared packaged subset (persona stems, without .agent.md). This list is the
# single source of truth for which personas ship in the wheel as the
# `dopemux init` fallback set (instruction_manager._get_packaged_personas_dir).
PACKAGED_PERSONAS = [
    "devops-expert",
    "janitor",
    "principal-software-engineer",
    "se-security-reviewer",
    "se-system-architecture-reviewer",
    "task-planner",
    "task-researcher",
    "wg-code-sentinel",
    "workflow-executor",
    "workflow-manager",
]


def collect_drift() -> list[str]:
    """Return a sorted list of drift findings; empty means in sync."""
    problems: list[str] = []

    for stem in PACKAGED_PERSONAS:
        canonical = CANONICAL_DIR / f"{stem}.agent.md"
        packaged = PACKAGED_DIR / f"{stem}.agent.md"
        if not canonical.is_file():
            problems.append(f"MISSING_CANONICAL: {canonical.relative_to(REPO_ROOT)}")
            continue
        if not packaged.is_file():
            problems.append(f"MISSING_PACKAGED: {packaged.relative_to(REPO_ROOT)}")
            continue
        if canonical.read_bytes() != packaged.read_bytes():
            problems.append(f"DRIFT: {packaged.relative_to(REPO_ROOT)} != {canonical.relative_to(REPO_ROOT)}")

    declared = {f"{stem}.agent.md" for stem in PACKAGED_PERSONAS}
    for extra in sorted(PACKAGED_DIR.glob("*.agent.md")):
        if extra.name not in declared:
            problems.append(f"UNDECLARED_PACKAGED: {extra.relative_to(REPO_ROOT)}")

    return sorted(problems)


def apply_sync() -> list[str]:
    """Copy canonical -> packaged for the declared subset. Fail-closed."""
    actions: list[str] = []
    for stem in PACKAGED_PERSONAS:
        canonical = CANONICAL_DIR / f"{stem}.agent.md"
        packaged = PACKAGED_DIR / f"{stem}.agent.md"
        if not canonical.is_file():
            raise FileNotFoundError(f"canonical persona missing: {canonical}")
        content = canonical.read_bytes()
        if not packaged.is_file() or packaged.read_bytes() != content:
            packaged.write_bytes(content)
            actions.append(f"synced: {stem}.agent.md")
        else:
            actions.append(f"ok: {stem}.agent.md")
    return actions


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify only; exit 1 on drift")
    args = parser.parse_args()

    if not CANONICAL_DIR.is_dir():
        print(f"FATAL: canonical personas dir missing: {CANONICAL_DIR}", file=sys.stderr)
        return 2
    if not PACKAGED_DIR.is_dir():
        print(f"FATAL: packaged personas dir missing: {PACKAGED_DIR}", file=sys.stderr)
        return 2

    if args.check:
        problems = collect_drift()
        if problems:
            for problem in problems:
                print(problem, file=sys.stderr)
            return 1
        print(f"IN SYNC: {len(PACKAGED_PERSONAS)} packaged personas match canonical")
        return 0

    try:
        actions = apply_sync()
    except FileNotFoundError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 2
    for action in actions:
        print(action)
    problems = collect_drift()
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
