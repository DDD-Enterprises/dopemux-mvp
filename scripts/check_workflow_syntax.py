#!/usr/bin/env python3
"""Validate GitHub Actions workflow files for defects CI itself cannot catch.

TP-RTE-TRUTH-R0-009.

This guard must live in pre-commit, NOT in a CI job: both defects it detects
prevent the workflow file from being accepted at all, so GitHub runs zero jobs
and any CI-side check is never reached. On PR #1136 this presented as a check
list that looked largely green while all 14 required gates were simply absent.

Two defect classes, both observed in production on branch
claude/rte-truth-program:

  EXPR-ESCAPE (fatal) -- a backslash-escaped quote inside a ``${{ }}``
      expression. Actions expression literals are single-quoted and escape an
      embedded quote by DOUBLING it (''); backslash escaping is a parse error
      that invalidates the entire file. Introduced when shell escaping leaks
      out of a heredoc during authoring.

  ORPHAN-ARG -- inside a ``run:`` block scalar, a continuation-looking line
      (``--flag ...``) whose predecessor lacks a trailing backslash. The shell
      then executes the flag line as its own command, which exits 127 under the
      Actions default ``bash -e -o pipefail``. The job can never go green, and
      the flags silently never reach the intended command.

Neither is detectable by grepping for the inserted text -- the check that let
both defects through in the first place.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - guard degrades rather than blocking commits
    yaml = None

EXPRESSION = re.compile(r"\$\{\{.*?\}\}", re.DOTALL)
RUN_KEY = re.compile(r"^(\s*)(?:-\s+)?run:\s*[|>][-+]?\s*$")
FLAG_LINE = re.compile(r"^\s*--\S")

Finding = Tuple[str, int, str]


def _check_expression_escapes(text: str) -> List[Finding]:
    findings: List[Finding] = []
    for match in EXPRESSION.finditer(text):
        if "\\'" in match.group(0) or '\\"' in match.group(0):
            line_no = text.count("\n", 0, match.start()) + 1
            snippet = " ".join(match.group(0).split())[:90]
            findings.append(
                (
                    "EXPR-ESCAPE",
                    line_no,
                    f"backslash-escaped quote in Actions expression: {snippet}\n"
                    f"    Actions escapes a quote by doubling it ('') -- a backslash "
                    f"invalidates the whole workflow file.",
                )
            )
    return findings


def _check_orphan_args(text: str) -> List[Finding]:
    """Flag --flag lines inside `run:` blocks whose predecessor lacks a `\\`."""
    findings: List[Finding] = []
    lines = text.splitlines()
    in_block = False
    block_indent = 0

    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip())

        run_match = RUN_KEY.match(raw)
        if run_match:
            in_block = True
            block_indent = len(run_match.group(1))
            continue

        if in_block and stripped and indent <= block_indent:
            in_block = False  # dedented out of the block scalar

        if not in_block or not FLAG_LINE.match(raw):
            continue

        # Walk back to the previous meaningful line within the same block.
        prev = ""
        for back in range(idx - 1, -1, -1):
            candidate = lines[back].rstrip()
            if candidate.strip() and not candidate.strip().startswith("#"):
                prev = candidate
                break

        if not prev or prev.endswith(("\\", "|", "&&", "||", "(")):
            continue

        findings.append(
            (
                "ORPHAN-ARG",
                idx + 1,
                f"{stripped[:70]}\n"
                f"    Previous line does not end with '\\', so the shell runs this "
                f"as its own command (exit 127 under `bash -e`) and the flags never "
                f"reach the intended command.",
            )
        )
    return findings


def check_file(path: Path) -> List[Finding]:
    text = path.read_text(encoding="utf-8")
    findings = _check_expression_escapes(text) + _check_orphan_args(text)
    if yaml is not None:
        try:
            yaml.safe_load(text)
        except yaml.YAMLError as exc:  # pragma: no cover - exercised by malformed input
            findings.append(("YAML-ERROR", 0, str(exc).replace("\n", " ")[:200]))
    return findings


def main(argv: List[str]) -> int:
    paths = [Path(a) for a in argv[1:]]
    if not paths:
        paths = sorted(Path(".github/workflows").glob("*.y*ml"))

    total = 0
    for path in paths:
        if not path.is_file():
            continue
        for kind, line_no, detail in check_file(path):
            total += 1
            location = f"{path}:{line_no}" if line_no else str(path)
            print(f"❌ {kind} {location}\n    {detail}", file=sys.stderr)

    if total:
        print(
            f"\n{total} workflow defect(s). These prevent GitHub from running ANY job, "
            f"so CI cannot report them -- that is why this guard runs pre-commit.",
            file=sys.stderr,
        )
        return 1

    print(f"✅ workflow syntax guard passed ({len(paths)} file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
