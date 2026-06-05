#!/usr/bin/env python3
"""Validate the /dx: command surface against the task-orchestrator surface manifest.

Read-only by construction: this script only *inspects* files. It never calls the
task-orchestrator MCP, never mutates workflow or repo state, and takes no network
or execution action. It is the mechanical enforcement for TP-DMX-ORCH-CS-P1.

Authority: `.taskorchestrator/surface_manifest.json` is the independent contract.
Each `.claude/commands/dx/<name>.md` must conform to its manifest entry. The manifest
is hand-authored (NOT generated from frontmatter), so a command that drifts — e.g. a
read command that gains a write tool — is detectable against an external source of truth.

Failure conditions (each -> non-zero exit):
  (a) A `read`-class command lists any orchestrator tool that is not `safe_read_only`.
  (b) A command lists an orchestrator tool absent from the manifest's tool table.
  (c) A command's orchestrator-tool set drifts from the manifest's expected set.
  (d) A command file exists with no manifest entry (uncatalogued surface).
  (e) The manifest references a command with no corresponding file (stale manifest).
  (f) Internal manifest inconsistency (read_surface != commands with surface_class=read).

Usage:
  python scripts/validate_dx_surface.py            # validate; print PASS/FAIL summary
  python scripts/validate_dx_surface.py --quiet    # only print the final verdict line
Exit code 0 = conforms, 1 = drift/violation, 2 = setup error (missing files/deps).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ORCH_PREFIX = "mcp__task-orchestrator__"


def repo_root() -> Path:
    # This script lives at <root>/scripts/validate_dx_surface.py
    return Path(__file__).resolve().parents[1]


def _fail_setup(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    print(f"SETUP ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def load_manifest(root: Path) -> dict:
    path = root / ".taskorchestrator" / "surface_manifest.json"
    if not path.is_file():
        _fail_setup(f"manifest not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive
        _fail_setup(f"manifest is not valid JSON: {exc}")


def parse_frontmatter_allowed_tools(md_path: Path) -> list[str]:
    """Return the `allowed-tools` list from a command file's YAML frontmatter."""
    try:
        import yaml  # PyYAML; present in the repo toolchain
    except ImportError:  # pragma: no cover - environment guard
        _fail_setup("PyYAML is required (pip install pyyaml)")

    text = md_path.read_text()
    if not text.startswith("---"):
        _fail_setup(f"{md_path.name}: missing frontmatter")
    # Frontmatter is the block between the first two '---' fences.
    parts = text.split("---", 2)
    if len(parts) < 3:
        _fail_setup(f"{md_path.name}: unterminated frontmatter")
    front = yaml.safe_load(parts[1]) or {}
    tools = front.get("allowed-tools", [])
    if not isinstance(tools, list):
        _fail_setup(f"{md_path.name}: allowed-tools is not a list")
    return [str(t) for t in tools]


def orchestrator_tools(tools: list[str]) -> set[str]:
    """Short names of the task-orchestrator tools in an allowed-tools list."""
    return {t[len(ORCH_PREFIX):] for t in tools if t.startswith(ORCH_PREFIX)}


def run_validation(root: Path) -> tuple[list[str], list[str]]:
    """Core check. Returns (failures, per-command report lines). Pure: no exit, no print.

    Importable so tests can run it against a tampered tmp copy of the surface.
    """
    manifest = load_manifest(root)

    tool_table: dict = manifest.get("tools", {})
    read_only_tools: set[str] = set(manifest.get("read_only_tools", []))
    commands: dict = manifest.get("commands", {})
    declared_read_surface: set[str] = set(manifest.get("read_surface", []))

    cmd_dir = root / ".claude" / "commands" / "dx"
    if not cmd_dir.is_dir():
        _fail_setup(f"command dir not found: {cmd_dir}")
    files = {p.stem: p for p in sorted(cmd_dir.glob("*.md"))}

    failures: list[str] = []
    lines: list[str] = []

    # (f) internal manifest consistency: read_surface == commands with surface_class=read
    read_class = {name for name, spec in commands.items() if spec.get("surface_class") == "read"}
    if read_class != declared_read_surface:
        failures.append(
            f"manifest: read_surface {sorted(declared_read_surface)} != read-class commands {sorted(read_class)}"
        )

    # (e) manifest entries must have files
    for name in sorted(commands):
        if name not in files:
            failures.append(f"manifest references command '{name}' but {cmd_dir}/{name}.md is missing")

    # (a)-(d) per-file checks
    for name, path in files.items():
        spec = commands.get(name)
        if spec is None:
            failures.append(f"{name}: command file present but not catalogued in manifest")
            lines.append(f"  FAIL {name}: uncatalogued")
            continue

        actual = orchestrator_tools(parse_frontmatter_allowed_tools(path))
        expected = set(spec.get("orchestrator_tools", []))
        klass = spec.get("surface_class", "?")
        problems: list[str] = []

        # (b) unknown tools
        unknown = {t for t in actual if t not in tool_table}
        if unknown:
            problems.append(f"unknown orchestrator tool(s): {sorted(unknown)}")

        # (c) drift vs manifest
        if actual != expected:
            problems.append(f"orchestrator-tool drift: frontmatter={sorted(actual)} manifest={sorted(expected)}")

        # (a) read command must use only read-only tools
        if klass == "read":
            non_read = {t for t in actual if t not in read_only_tools}
            if non_read:
                problems.append(f"read command lists non-read tool(s): {sorted(non_read)}")

        if problems:
            failures.extend(f"{name}: {p}" for p in problems)
            lines.append(f"  FAIL {name} [{klass}]: " + "; ".join(problems))
        else:
            lines.append(f"  ok   {name} [{klass}]: {sorted(actual) or '—'}")

    return failures, lines


def main(argv: list[str]) -> int:
    quiet = "--quiet" in argv
    root = repo_root()
    if "--root" in argv:
        root = Path(argv[argv.index("--root") + 1]).resolve()

    manifest = load_manifest(root)
    commands: dict = manifest.get("commands", {})
    declared_read_surface = manifest.get("read_surface", [])
    read_class = [n for n, s in commands.items() if s.get("surface_class") == "read"]
    n_files = len(list((root / ".claude" / "commands" / "dx").glob("*.md")))

    failures, lines = run_validation(root)

    if not quiet:
        print("dx surface validation — .claude/commands/dx/ vs .taskorchestrator/surface_manifest.json")
        print(f"  tools catalogued: {len(manifest.get('tools', {}))} | "
              f"read-only: {len(manifest.get('read_only_tools', []))} | commands: {n_files}")
        for line in lines:
            print(line)

    if failures:
        print(f"\nFAIL: {len(failures)} surface violation(s):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"\nPASS: {n_files} commands conform to the surface manifest "
          f"({len(declared_read_surface)} read-surface, "
          f"{len(read_class)} read / "
          f"{sum(1 for s in commands.values() if s.get('surface_class') == 'write')} write / "
          f"{sum(1 for s in commands.values() if s.get('surface_class') == 'composite')} composite).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
