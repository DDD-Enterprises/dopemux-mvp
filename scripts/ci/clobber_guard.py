#!/usr/bin/env python3
"""Clobber guard — fail delete-heavy / code+test co-deletion / stale-clobber PRs.

Motivated by the #1025 incident: a "UI" PR deleted the entire MCP runtime stack
(27,676 lines across 137 files, including the modules' own unit tests) off main
with **green CI** — because when code AND its tests are deleted together, nothing
fails. Green CI is not evidence of no-regression when the safety net is removed
alongside the code.

This guard compares a base ref (default ``origin/main``) against HEAD through the
branch merge-base and raises three independent violations:

  1. LARGE_DELETION            — deleted lines/files exceed thresholds
  2. SOURCE_AND_TEST_CODELETION — at least one non-test source file AND at least
                                  one test file are both deleted (the #1025 signature)
  3. STALE_CLOBBER             — a deleted file was modified on the base branch
                                  AFTER the branch's merge-base (i.e. the PR is
                                  removing work that is newer than the branch)

Any violation exits 1, UNLESS ``--allow-intentional`` is passed (wired to the
``intentional-deletion`` PR label), which downgrades violations to warnings and
exits 0. This keeps legitimate large refactors unblocked while forcing an
explicit, auditable acknowledgement.

Exit codes: 0 = ok (or warnings only under override), 1 = violation, 2 = git/usage error.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

# --- classification ---------------------------------------------------------

# A path is a "test file" if it lives under a tests dir or matches a test naming
# convention (Python + JS/TS). conftest.py counts (it is test scaffolding).
_TEST_DIR = re.compile(r"(^|/)(tests?|__tests__)(/|$)")
_TEST_NAME = re.compile(
    r"(^|/)(test_[^/]+\.py|[^/]+_test\.py|conftest\.py|[^/]+\.(test|spec)\.(t|j)sx?)$"
)

# A path is "source" if it is code we care about protecting (not docs/proof/config).
_SOURCE_EXT = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".rb", ".sh")


def is_test_file(path: str) -> bool:
    return bool(_TEST_DIR.search(path) or _TEST_NAME.search(path))


def is_source_file(path: str) -> bool:
    return path.endswith(_SOURCE_EXT) and not is_test_file(path)


# --- pure evaluation --------------------------------------------------------


@dataclass(frozen=True)
class Config:
    max_deleted_lines: int = 1500
    max_deleted_files: int = 15


@dataclass
class Result:
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 1 if self.violations else 0


def evaluate(
    deleted_files: list[str],
    deleted_lines: int,
    stale_deleted: list[str],
    *,
    allow_intentional: bool,
    config: Config = Config(),
) -> Result:
    """Apply the three rules to already-collected diff facts (pure, testable).

    ``deleted_files`` are the paths deleted by the PR; ``deleted_lines`` is the
    total lines removed across the whole diff; ``stale_deleted`` are deleted
    paths that were also modified on base after the merge-base. When
    ``allow_intentional`` is set, findings are emitted as warnings, not violations.
    """
    findings: list[str] = []

    n_files = len(deleted_files)
    if deleted_lines > config.max_deleted_lines or n_files > config.max_deleted_files:
        findings.append(
            f"LARGE_DELETION: {deleted_lines} lines / {n_files} files deleted "
            f"(limits: {config.max_deleted_lines} lines, {config.max_deleted_files} files)."
        )

    deleted_tests = [p for p in deleted_files if is_test_file(p)]
    deleted_sources = [p for p in deleted_files if is_source_file(p)]
    if deleted_tests and deleted_sources:
        findings.append(
            "SOURCE_AND_TEST_CODELETION: this PR deletes source AND its tests "
            f"together ({len(deleted_sources)} source, {len(deleted_tests)} test "
            "files) — CI can stay green because the safety net is removed with the "
            "code. Examples: "
            + ", ".join(sorted(deleted_sources)[:3] + sorted(deleted_tests)[:3])
        )

    if stale_deleted:
        findings.append(
            "STALE_CLOBBER: this PR deletes files that were modified on the base "
            "branch AFTER this branch diverged — it is likely removing newer work "
            "(stale-branch clobber). Files: " + ", ".join(sorted(stale_deleted)[:8])
        )

    result = Result()
    if allow_intentional:
        result.warnings = findings
    else:
        result.violations = findings
    return result


# --- git layer --------------------------------------------------------------


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def collect_facts(base: str, head: str) -> tuple[list[str], int, list[str]]:
    """Collect (deleted_files, deleted_lines, stale_deleted) from git."""
    merge_base = _git("merge-base", base, head).strip()

    deleted_files = [
        line
        for line in _git(
            "diff", "--diff-filter=D", "--name-only", merge_base, head
        ).splitlines()
        if line.strip()
    ]

    deleted_lines = 0
    for row in _git("diff", "--numstat", merge_base, head).splitlines():
        parts = row.split("\t")
        if len(parts) == 3 and parts[1].isdigit():
            deleted_lines += int(parts[1])  # numstat col 2 = deletions

    # Stale-clobber: a deleted file that base touched after the merge-base.
    stale_deleted = []
    for path in deleted_files:
        log = _git("log", "--oneline", f"{merge_base}..{base}", "--", path)
        if log.strip():
            stale_deleted.append(path)

    return deleted_files, deleted_lines, stale_deleted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Guard against delete-heavy / clobber PRs.")
    parser.add_argument("--base", default=None, help="Base ref (default: origin/$GITHUB_BASE_REF or origin/main).")
    parser.add_argument("--head", default="HEAD", help="Head ref (default: HEAD).")
    parser.add_argument(
        "--allow-intentional",
        action="store_true",
        help="Downgrade violations to warnings (wire to the 'intentional-deletion' label).",
    )
    parser.add_argument("--max-deleted-lines", type=int, default=Config.max_deleted_lines)
    parser.add_argument("--max-deleted-files", type=int, default=Config.max_deleted_files)
    args = parser.parse_args(argv)

    base = args.base
    if not base:
        ref = os.getenv("GITHUB_BASE_REF")
        base = f"origin/{ref}" if ref else "origin/main"

    try:
        deleted_files, deleted_lines, stale_deleted = collect_facts(base, args.head)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    result = evaluate(
        deleted_files,
        deleted_lines,
        stale_deleted,
        allow_intentional=args.allow_intentional,
        config=Config(args.max_deleted_lines, args.max_deleted_files),
    )

    for w in result.warnings:
        print(f"::warning:: [clobber-guard] {w}")
    for v in result.violations:
        print(f"::error:: [clobber-guard] {v}")

    if result.violations:
        print(
            "\nclobber-guard FAILED. If these deletions are intentional, add the "
            "'intentional-deletion' label to this PR (a human must confirm the "
            "removal is deliberate), then re-run.",
            file=sys.stderr,
        )
        return 1
    if result.warnings:
        print("clobber-guard: violations acknowledged via 'intentional-deletion' label (warnings only).")
    else:
        print("clobber-guard: OK — no clobber signature detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
