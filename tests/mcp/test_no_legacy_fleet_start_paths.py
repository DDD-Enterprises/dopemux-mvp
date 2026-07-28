"""Guard test for design P-22 (legacy MCP fleet launch-path removal).

Acceptance criterion (claudedocs/mcp-fleet-multi-instance-design-2026-07-28.md
§9, packet P-22): "no path outside `dopemux mcp` can start fleet services."
Concretely: every `docker compose up` / `docker-compose up` invocation that
could launch a catalog service must live either under the canonical
`dopemux mcp` CLI, or in an explicitly-justified allowlist entry below.

This walks `git ls-files` (not the working tree) restricted to files that can
actually *execute* something — shell scripts, Python, PowerShell, and
Makefiles — since prose in docs/JSON/txt evidence dumps cannot start a
container. Every remaining hit must be covered by an allowlist entry with a
written justification, matching the P-22 AC's own CI-guard description.

See also: claudedocs/mcp-legacy-launch-path-worklist-2026-07-28.md (the file
sweep this packet's deletions were driven by).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Files that can actually launch something. Docs/JSON/txt evidence dumps are
# excluded by construction — they cannot execute a command.
_SCANNED_GLOBS = ("*.sh", "*.py", "*.ps1")
_SCANNED_BASENAMES = {"Makefile"}

_FLEET_START_RE = re.compile(
    r"docker[- ]compose(?:\s+-f\s+\S+)*\s+up\b"
)

# (path or path-prefix, justification). Prefixes match the path itself or
# anything under "<prefix>/". Every live hit found by the sweep below is
# accounted for here — see the packet report for the full evidence trail.
_ALLOWLIST: tuple[tuple[str, str], ...] = (
    # --- explicitly named in the P-22 task spec ---
    ("src/dopemux/mcp", "canonical MCP lifecycle implementation"),
    (
        "src/dopemux/commands/mcp_commands.py",
        "canonical `dopemux mcp` CLI command group (up/down/start/stop); "
        "the actual home of the reconciler + compose invocations — the P-22 "
        "spec named src/dopemux/mcp/** but the CLI commands live here",
    ),
    ("install.sh", "bootstrap installer, scoped by design"),
    (
        "scripts/mcp-wrappers/task-orchestrator-",
        "canonical task-orchestrator wrapper family "
        "(http-singleton / current-stdio / rollback-stdio)",
    ),
    (
        "scripts/mcp-wrappers/ensure-pal.sh",
        "off-compose pal-mcp-server ensure-script; load-bearing until "
        "design milestones M4/M5 bring it under `dopemux mcp` management",
    ),
    (
        "scripts/ensure_pal_stdio.sh",
        "off-compose pal-stdio ensure-script; load-bearing until design "
        "milestones M4/M5",
    ),
    ("qa/scenarios", "intentional compose-layer test harness, documented as exempt"),
    ("tests", "this guard test plus any test fixtures that embed the pattern"),
    # --- discovered during the sweep; not fleet-launch executions ---
    (
        "docker/mcp-servers-source",
        "vendored source tree (kept per P-22: 'keep all Dockerfiles and "
        "vendored source'), including the bundled pal-mcp-server "
        "subproject's own build/deploy tooling and a self-test script "
        "(verify-complete.sh) that greps the now-removed legacy script",
    ),
    (
        "examples",
        "demo/example scripts print illustrative commands in docstrings/"
        "print() calls; never executed",
    ),
    (
        "installers/leantime/install.py",
        "installer prints a manual 'Start: docker-compose up -d' suggestion "
        "on completion; not executed",
    ),
    (
        "scripts/cleanup.sh",
        "prints a manual restart suggestion on completion; not executed",
    ),
    (
        "scripts/compose_guard.py",
        "compose-guard tool's own help text about `docker compose up --scale`",
    ),
    (
        "scripts/consolidate_docker_networks.sh",
        "prints a manual restart suggestion on completion; not executed",
    ),
    (
        "scripts/deploy/deployment/launch-dopemux-minimal.sh",
        "tmux-pane help text telling the operator what to type manually; "
        "not executed",
    ),
    (
        "scripts/deploy/deployment/launch-dopemux-orchestrator.sh",
        "tmux-pane help text telling the operator what to type manually; "
        "not executed",
    ),
    (
        "scripts/deploy/migration/migrate_conport_to_age.sh",
        "one-time data-migration utility against a dedicated "
        "docker-compose.age.yml; not a fleet-launch path",
    ),
    (
        "scripts/deploy/setup/setup_dopemux.sh",
        "legacy unscoped full-stack launcher discovered by this guard; not "
        "in the P-22 worklist file list and no live caller was found — "
        "flagged for a follow-up packet rather than deleted unilaterally "
        "here (see task report)",
    ),
    (
        "scripts/dev/testing/validate-mcp-setup.sh",
        "prints a manual start suggestion on failure; not executed",
    ),
    (
        "scripts/generate-claude-config.py",
        "prints a manual start suggestion on failure; not executed",
    ),
    (
        "scripts/mcp-wrappers/conport-wrapper.sh",
        "prints a manual start suggestion on failure; not executed",
    ),
    (
        "scripts/mcp-wrappers/dope-context-wrapper.sh",
        "prints a manual start suggestion on failure; not executed",
    ),
    (
        "src/dopemux/mcp/agent_bootstrap.py",
        "covered by the src/dopemux/mcp prefix above; docstring mention only",
    ),
    (
        "src/dopemux/ui/theme.py",
        "UI hint string ('Fix: Run docker compose up db'); not executed",
    ),
    (
        "Makefile",
        "pre-existing pm-up / webhook_receiver targets invoke docker "
        "compose directly; outside the P-22 legacy-launch-path worklist "
        "file list — flagged for a follow-up packet rather than rewritten "
        "here (see task report)",
    ),
    (
        "docker/leantime/configure_bridge.sh",
        "pre-existing leantime-bridge --force-recreate call; outside the "
        "P-22 worklist file list — flagged for a follow-up packet (see "
        "task report)",
    ),
)


def _tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def _is_scanned(path: str) -> bool:
    name = Path(path).name
    if name in _SCANNED_BASENAMES:
        return True
    return any(Path(path).match(glob) for glob in _SCANNED_GLOBS)


def _is_allowlisted(path: str) -> str | None:
    for prefix, justification in _ALLOWLIST:
        if path == prefix or path.startswith(prefix.rstrip("/") + "/") or path.startswith(prefix):
            return justification
    return None


def test_no_legacy_fleet_start_paths_outside_allowlist():
    """Every `docker compose up` / `docker-compose up` hit in an executable
    file is either the canonical `dopemux mcp` path or an allowlisted,
    justified exception."""
    violations: list[str] = []

    for path in _tracked_files():
        if not _is_scanned(path):
            continue
        abs_path = REPO_ROOT / path
        if not abs_path.is_file():
            continue
        if _is_allowlisted(path):
            continue

        try:
            text = abs_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            if _FLEET_START_RE.search(line):
                violations.append(f"{path}:{lineno}: {line.strip()}")

    assert not violations, (
        "Found fleet-start command(s) outside `dopemux mcp` and outside the "
        "allowlist in tests/mcp/test_no_legacy_fleet_start_paths.py. Either "
        "route through `dopemux mcp up`/`dopemux mcp start`, or add a "
        "justified allowlist entry.\n\n" + "\n".join(violations)
    )


def test_allowlist_entries_are_all_tracked_paths_or_prefixes():
    """Sanity check: every allowlist entry should resolve to at least one
    tracked file, so stale entries get caught instead of silently rotting."""
    tracked = _tracked_files()
    stale: list[str] = []

    for prefix, _justification in _ALLOWLIST:
        if any(p == prefix or p.startswith(prefix.rstrip("/") + "/") or p.startswith(prefix) for p in tracked):
            continue
        stale.append(prefix)

    assert not stale, f"Allowlist entries with no matching tracked file: {stale}"
