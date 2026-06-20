#!/usr/bin/env python3
"""Fail if .claude/commands reference deprecated memory backends."""

from __future__ import annotations

import re
import sys
from pathlib import Path

FORBIDDEN = re.compile(
    r"openmemory|memory_bank|\bmem0\b|/mcp memory\b|Claude-Context",
    re.IGNORECASE,
)

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = ROOT / ".claude" / "commands"


def main() -> int:
    violations: list[str] = []
    for path in sorted(COMMANDS.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), start=1):
            if "deprecated" in line.lower() or "do not use" in line.lower():
                continue
            if FORBIDDEN.search(line):
                rel = path.relative_to(ROOT)
                violations.append(f"{rel}:{i}: {line.strip()}")
    if violations:
        print("Deprecated memory backend references found:", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1
    print(f"OK: no forbidden memory refs in {COMMANDS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())