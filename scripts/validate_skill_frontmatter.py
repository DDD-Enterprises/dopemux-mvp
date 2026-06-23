#!/usr/bin/env python3
"""Validate SKILL.md frontmatter in templates/skills."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "templates" / "skills"
REQUIRED = ("name", "description")
FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
FIELD = re.compile(r"^([a-zA-Z0-9_-]+):\s*(.+)$", re.MULTILINE)


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER.match(text)
    if not match:
        return {}
    body = match.group(1)
    out: dict[str, str] = {}
    for key, value in FIELD.findall(body):
        out[key] = value.strip().strip('"').strip("'")
    return out


def main() -> int:
    violations: list[str] = []
    for skill_md in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
        meta = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        missing = [k for k in REQUIRED if not meta.get(k)]
        if missing:
            rel = skill_md.relative_to(ROOT)
            violations.append(f"{rel}: missing {', '.join(missing)}")
    if violations:
        print("SKILL frontmatter violations:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1
    print(f"OK: {len(list(SKILLS_ROOT.glob('*/SKILL.md')))} skills have name+description frontmatter")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())