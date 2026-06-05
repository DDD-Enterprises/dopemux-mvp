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
  (f) Internal manifest inconsistency:
      - read_surface != commands with surface_class=read
      - read_only_tools != tools classified safe_read_only
  (g) A `read`-class command lists a NON-orchestrator tool that is not permitted by the
      manifest's read_command_nonorch_allowlist (fail-closed: catches a read command gaining a
      repo write such as Write/Edit or a bridge/memory write such as mcp__conport__log_decision,
      which the orchestrator-only check in (a) would otherwise miss). Bash handling: bare
      unscoped `Bash` is rejected (it can run mutating shell, e.g. `git commit`/`rm`); a scoped
      `Bash(<cmd>:*)` is allowed only when `<cmd>` is in bash_allowed_commands (read-only ops).

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
READ_COMMAND_NONORCH_TOOL_ALLOWLIST = {
    "Read",
    "Grep",
    "Glob",
    "LS",
    "mcp__conport__get_active_context",
}
READ_COMMAND_BASH_ALLOWLIST = {"git rev-parse"}


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


def nonorch_tools(tools: list[str]) -> set[str]:
    """The non-task-orchestrator entries in an allowed-tools list (full tool names)."""
    return {t for t in tools if not t.startswith(ORCH_PREFIX)}


def read_command_nonorch_violation(
    tool: str, allowlist: set[str], bash_allowed_commands: list[str]
) -> str | None:
    """Return a violation reason if `tool` is disallowed in a read command, else None.

    - A plain allowlisted tool (Read/Grep/… or an explicitly read-only MCP tool) is fine.
    - Bare unscoped `Bash` is rejected: it can run mutating shell (git commit / rm / touch).
    - A scoped `Bash(<cmd>:*)` is allowed only when `<cmd>` is in bash_allowed_commands
      (read-only operations). The command segment is the text before the first ':'.
    """
    if tool in allowlist:
        return None
    if tool == "Bash":
        return "bare unscoped 'Bash' (can run mutating shell); use a scoped read-only Bash pattern"
    if tool.startswith("Bash(") and tool.endswith(")"):
        inner = tool[len("Bash("):-1]
        cmd = inner.split(":", 1)[0].strip()
        if cmd in bash_allowed_commands:
            return None
        return f"scoped Bash command not in read-only allowlist: {cmd!r}"
    return "not in read-command non-orchestrator allowlist"


def run_validation(root: Path) -> tuple[list[str], list[str]]:
    """Core check. Returns (failures, per-command report lines). Pure: no exit, no print.

    Importable so tests can run it against a tampered tmp copy of the surface.
    """
    manifest = load_manifest(root)

    tool_table: dict = manifest.get("tools", {})
    read_only_tools: set[str] = set(manifest.get("read_only_tools", []))
    commands: dict = manifest.get("commands", {})
    declared_read_surface: set[str] = set(manifest.get("read_surface", []))
    nonorch_cfg: dict = manifest.get("read_command_nonorch_allowlist", {})
    nonorch_allowlist: set[str] = set(nonorch_cfg.get("tools", []))
    bash_allowed_commands: list[str] = list(nonorch_cfg.get("bash_allowed_commands", []))
    failures: list[str] = []

    # (f) internal manifest consistency: the non-orchestrator allowlist itself must stay safe.
    disallowed_allowlist = sorted(nonorch_allowlist - READ_COMMAND_NONORCH_TOOL_ALLOWLIST)
    if disallowed_allowlist:
        failures.append(
            "manifest: read_command_nonorch_allowlist.tools contains disallowed entry(ies) "
            f"{disallowed_allowlist}"
        )

    disallowed_bash = sorted(set(bash_allowed_commands) - READ_COMMAND_BASH_ALLOWLIST)
    if disallowed_bash:
        failures.append(
            "manifest: read_command_nonorch_allowlist.bash_allowed_commands contains disallowed "
            f"entry(ies) {disallowed_bash}"
        )

    cmd_dir = root / ".claude" / "commands" / "dx"
    if not cmd_dir.is_dir():
        _fail_setup(f"command dir not found: {cmd_dir}")
    files = {p.stem: p for p in sorted(cmd_dir.glob("*.md"))}

    lines: list[str] = []

    # (f) internal manifest consistency: read_surface == commands with surface_class=read
    read_class = {name for name, spec in commands.items() if spec.get("surface_class") == "read"}
    if read_class != declared_read_surface:
        failures.append(
            f"manifest: read_surface {sorted(declared_read_surface)} != read-class commands {sorted(read_class)}"
        )

    # (f) internal manifest consistency: read_only_tools must match safe_read_only classifications
    classified_read_only = {
        name for name, spec in tool_table.items() if spec.get("classification") == "safe_read_only"
    }
    if read_only_tools != classified_read_only:
        failures.append(
            "manifest: read_only_tools "
            f"{sorted(read_only_tools)} != safe_read_only tools {sorted(classified_read_only)}"
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

        all_tools = parse_frontmatter_allowed_tools(path)
        actual = orchestrator_tools(all_tools)
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

        # (a) read command must use only read-only orchestrator tools
        if klass == "read":
            non_read = {t for t in actual if t not in read_only_tools}
            if non_read:
                problems.append(f"read command lists non-read orchestrator tool(s): {sorted(non_read)}")

            # (g) read command's non-orchestrator tools must each be permitted (fail-closed)
            bad = {
                t: reason
                for t in nonorch_tools(all_tools)
                if (reason := read_command_nonorch_violation(t, nonorch_allowlist, bash_allowed_commands))
            }
            if bad:
                detail = "; ".join(f"{t} ({r})" for t, r in sorted(bad.items()))
                problems.append(f"read command lists disallowed non-orchestrator tool(s): {detail}")

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
