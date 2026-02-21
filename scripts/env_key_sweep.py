#!/usr/bin/env python3
"""Sweep .env-style files for provider key ambiguity without exposing secrets."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

TARGET_KEYS = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY")
ENV_PATTERN = re.compile(r"^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$")
IGNORED_DIRS = {
    ".git",
    "docs/archive",
    "_audit_out",
    "reports",
    "extraction/runs",
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "quarantine",
}
GOOGLE_KEY_COMPAT_PATHS = {"docker/mcp-servers/.env"}


@dataclass
class KeyRef:
    line: int
    value_state: str


@dataclass
class FileFinding:
    path: Path
    keys: Dict[str, KeyRef]


def _is_ignored(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    for ignored in IGNORED_DIRS:
        if rel == ignored or rel.startswith(f"{ignored}/"):
            return True
    return False


def _iter_env_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or _is_ignored(path, root):
            continue
        name = path.name
        if name == ".env" or name.startswith(".env.") or name.endswith(".env") or name.endswith(".env.example") or name.endswith(".env.template"):
            yield path


def _value_state(raw_value: str) -> str:
    value = raw_value.strip().strip('"').strip("'")
    return "set" if bool(value) else "empty"


def sweep(root: Path) -> List[FileFinding]:
    findings: List[FileFinding] = []
    for env_file in sorted(_iter_env_files(root)):
        keys: Dict[str, KeyRef] = {}
        for idx, line in enumerate(env_file.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            match = ENV_PATTERN.match(line)
            if not match:
                continue
            key, raw_value = match.groups()
            if key in TARGET_KEYS:
                keys[key] = KeyRef(line=idx, value_state=_value_state(raw_value))
        if keys:
            findings.append(FileFinding(path=env_file, keys=keys))
    return findings


def summarize(findings: List[FileFinding], root: Path) -> Tuple[str, int]:
    lines: List[str] = []
    deprecated_count = 0
    deprecated_actionable_count = 0
    dual_count = 0

    lines.append("Provider key sweep (.env files)")
    lines.append(f"Root: {root}")
    lines.append(f"Files with provider keys: {len(findings)}")

    for finding in findings:
        rel = finding.path.relative_to(root)
        key_parts = [f"{k}@{v.line}({v.value_state})" for k, v in sorted(finding.keys.items())]
        lines.append(f"- {rel}: " + ", ".join(key_parts))

        has_google = "GOOGLE_API_KEY" in finding.keys
        has_gemini = "GEMINI_API_KEY" in finding.keys
        rel_str = rel.as_posix()
        if has_google:
            deprecated_count += 1
            is_backup = "backup" in rel_str.lower()
            is_compat = rel_str in GOOGLE_KEY_COMPAT_PATHS
            if not (is_backup or is_compat):
                deprecated_actionable_count += 1
        if has_google and has_gemini:
            dual_count += 1

    lines.append("")
    lines.append("Policy")
    lines.append("- Canonical Gemini key: GEMINI_API_KEY")
    lines.append("- Deprecated in Dopemux-managed env files: GOOGLE_API_KEY")
    lines.append(f"- Files using deprecated GOOGLE_API_KEY (all): {deprecated_count}")
    lines.append(f"- Files using deprecated GOOGLE_API_KEY (actionable): {deprecated_actionable_count}")
    lines.append(f"- Files defining both GEMINI_API_KEY and GOOGLE_API_KEY: {dual_count}")

    exit_code = 1 if deprecated_actionable_count > 0 else 0
    return "\n".join(lines), exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Sweep .env-style files for provider key ambiguity.")
    parser.add_argument("--root", default=".", help="Repository root (default: current directory)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    findings = sweep(root)
    report, exit_code = summarize(findings, root)
    print(report)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
