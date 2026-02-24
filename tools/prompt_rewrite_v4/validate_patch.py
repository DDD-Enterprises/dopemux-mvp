from __future__ import annotations

import argparse
import itertools
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional


HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
DIFF_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
DIFF_OLD_RE = re.compile(r"^--- a/(.+)$")


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reason: str


def count_lines(text: str) -> int:
    return 0 if not text else text.count("\n") + (0 if text.endswith("\n") else 1)


def is_unified_diff(text: str) -> bool:
    # Minimal structural check.
    return ("--- a/" in text) and ("+++ b/" in text) and ("@@ -" in text)


def parse_diff_target_paths(diff_text: str) -> Tuple[Optional[str], Optional[str]]:
    old_path = None
    new_path = None
    for line in diff_text.splitlines():
        m_old = DIFF_OLD_RE.match(line)
        if m_old:
            old_path = m_old.group(1)
        m_new = DIFF_FILE_RE.match(line)
        if m_new:
            new_path = m_new.group(1)
        if old_path and new_path:
            break
    return old_path, new_path


def build_heading_line_map(prompt_text: str) -> List[Tuple[int, str]]:
    """
    Returns list of (line_no_1based, heading_text) for markdown headings.
    We look for lines like: '# Heading' or '## Heading' etc.
    """
    out: List[Tuple[int, str]] = []
    for idx, line in enumerate(prompt_text.splitlines(), start=1):
        if line.startswith("#"):
            # normalize heading text
            stripped = line.lstrip("#").strip()
            if stripped:
                out.append((idx, stripped))
    return out


def section_bounds(prompt_text: str, section_name: str) -> Optional[Tuple[int, int]]:
    """
    Find 1-based inclusive bounds for the section body (lines after heading until before next heading).
    Returns (start_line, end_line) for the BODY ONLY (not including heading line).
    """
    headings = build_heading_line_map(prompt_text)
    # find exact match
    target_idx = None
    for i, (ln, name) in enumerate(headings):
        if name == section_name:
            target_idx = i
            break
    if target_idx is None:
        return None
    heading_line = headings[target_idx][0]
    body_start = heading_line + 1
    if target_idx + 1 < len(headings):
        next_heading_line = headings[target_idx + 1][0]
        body_end = next_heading_line - 1
    else:
        body_end = len(prompt_text.splitlines())
    if body_start > body_end:
        # empty body
        return (body_start, body_end)
    return (body_start, body_end)


def changed_line_numbers(diff_text: str) -> Tuple[List[int], List[int]]:
    """
    Return (changed_old_lines, changed_new_lines), 1-based line numbers for actual edits only.
    Context lines are ignored.
    """
    old_changed: List[int] = []
    new_changed: List[int] = []

    lines = diff_text.splitlines()
    i = 0
    while i < len(lines):
        m = HUNK_RE.match(lines[i])
        if not m:
            i += 1
            continue

        old_line = int(m.group(1))
        old_count = int(m.group(2) or "1")
        new_line = int(m.group(3))
        new_count = int(m.group(4) or "1")
        i += 1

        # Walk hunk body until next hunk header or next file header.
        while i < len(lines) and not HUNK_RE.match(lines[i]) and not DIFF_OLD_RE.match(lines[i]) and not DIFF_FILE_RE.match(lines[i]):
            line = lines[i]
            if not line:
                # Empty context line still advances both if it's context.
                old_line += 1
                new_line += 1
                i += 1
                continue

            if line.startswith("\\"):
                # "\ No newline at end of file" marker
                i += 1
                continue

            if line.startswith(" "):
                old_line += 1
                new_line += 1
            elif line.startswith("+") and not line.startswith("+++"):
                new_changed.append(new_line)
                new_line += 1
            elif line.startswith("-") and not line.startswith("---"):
                old_changed.append(old_line)
                old_line += 1
            else:
                # Unexpected line prefix; be conservative: treat as context.
                old_line += 1
                new_line += 1
            i += 1

    return old_changed, new_changed


def ranges_within(outer: Tuple[int, int], inner: Tuple[int, int]) -> bool:
    return inner[0] >= outer[0] and inner[1] <= outer[1]


def validate_patch(
    *,
    diff_text: str,
    expected_relpath: str,
    original_prompt_text: str,
    max_patch_lines: int,
) -> ValidationResult:
    if diff_text.strip() == "OUTPUT_LIMIT_REACHED":
        return ValidationResult(False, "Model reported OUTPUT_LIMIT_REACHED")

    if count_lines(diff_text) > max_patch_lines:
        return ValidationResult(False, f"Patch exceeds max_patch_lines={max_patch_lines}")

    if not is_unified_diff(diff_text):
        return ValidationResult(False, "Not a unified diff")

    old_path, new_path = parse_diff_target_paths(diff_text)
    if old_path != expected_relpath or new_path != expected_relpath:
        return ValidationResult(
            False,
            f"Diff targets do not match expected path. expected={expected_relpath} old={old_path} new={new_path}",
        )

    # Determine allowed section body bounds in the ORIGINAL file.
    ep_bounds = section_bounds(original_prompt_text, "Extraction Procedure")
    fm_bounds = section_bounds(original_prompt_text, "Failure Modes")
    if ep_bounds is None or fm_bounds is None:
        return ValidationResult(False, "Missing required section headings for bounds check")

    allowed = [ep_bounds, fm_bounds]

    old_changed, new_changed = changed_line_numbers(diff_text)

    # Validate actual changed lines only (ignore context).
    def in_allowed(line_no: int) -> bool:
        return any(a[0] <= line_no <= a[1] for a in allowed)

    for ln in old_changed:
        if not in_allowed(ln):
            return ValidationResult(False, f"Deleted line {ln} outside allowed sections. allowed={allowed}")

    for ln in new_changed:
        if not in_allowed(ln):
            return ValidationResult(False, f"Added line {ln} outside allowed sections. allowed={allowed}")

    return ValidationResult(True, "OK")


def cli() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff", required=True, help="Path to unified diff patch file")
    ap.add_argument("--expected-relpath", required=True, help="Expected repo-relative path the diff modifies")
    ap.add_argument("--original", required=True, help="Path to original prompt file (pre-patch)")
    ap.add_argument("--max-lines", type=int, default=350)
    args = ap.parse_args()

    diff_text = Path(args.diff).read_text(encoding="utf-8")
    orig_text = Path(args.original).read_text(encoding="utf-8")
    res = validate_patch(
        diff_text=diff_text,
        expected_relpath=args.expected_relpath,
        original_prompt_text=orig_text,
        max_patch_lines=args.max_lines,
    )
    print(("PASS: " if res.ok else "FAIL: ") + res.reason)
    raise SystemExit(0 if res.ok else 2)


if __name__ == "__main__":
    cli()