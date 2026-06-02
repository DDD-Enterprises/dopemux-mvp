#!/usr/bin/env python3
"""Validate active ADHD doctrine docs do not overclaim planned automation."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ACTIVE_DOCS = [
    ".claude/claude.md",
    ".claude/modules/shared/adhd-patterns.md",
    ".claude/modules/shared/superclaude-workflows.md",
    ".claude/modules/custom-commands.md",
    ".claude/modules/superclaude-integration.md",
    ".claude/commands/save.md",
    ".claude/commands/dx/implement.md",
]

FORBIDDEN_PHRASES = [
    "auto-save every 5min",
    "Auto-save every 5 minutes",
    "automatic break reminder",
    "automatic break reminders",
    "break reminder at 25",
    "Break reminder at 25",
    "forced break",
    "forces break at 90",
    "Mandatory Break",
    "mandatory break",
    "25min timer",
    "25-minute focus-block saves",
    "30-second auto-save cadence",
    "automates auto-save",
    "auto-saved.",
    "hyperfocus_force",
    "hyperfocus_warn",
]

REQUIRED_PHRASES = [
    "Observed runtime support",
    "Planned/specification behavior",
    "not proven wired",
]


def main() -> int:
    failures: list[str] = []
    combined = ""

    for rel_path in ACTIVE_DOCS:
        path = ROOT / rel_path
        text = path.read_text(encoding="utf-8")
        combined += text + "\n"
        for phrase in FORBIDDEN_PHRASES:
            if phrase in text:
                failures.append(f"{rel_path}: forbidden phrase {phrase!r}")

    for phrase in REQUIRED_PHRASES:
        if phrase not in combined:
            failures.append(f"missing required phrase {phrase!r}")

    if failures:
        print("ADHD doctrine validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("ADHD doctrine validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
