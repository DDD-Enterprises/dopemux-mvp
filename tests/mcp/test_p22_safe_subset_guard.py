"""P-22 SAFE-SUBSET guard (legacy MCP fleet launch-path removal).

WHAT THIS PROVES (narrowed claim — supervisor re-verdict on PR #1150): the
legacy launch paths deleted by the P-22 safe subset stay deleted, and no NEW
single-line `docker compose ... up` / `docker-compose ... up` invocation
appears in executable files outside an explicitly-justified allowlist.

WHAT THIS DOES **NOT** PROVE: repo-wide launch-path exclusivity. This test is
NOT evidence that "no path outside `dopemux mcp` can start fleet services" —
known launch paths survive the safe subset and are enumerated below with
packet IDs so this disclosure cannot silently rot:

  SURVIVING PATHS (packet ID · classification):
  - P22-F1 · OPERATOR-DESTRUCTIVE, allowlisted: `scripts/compose_nuke.sh`
    (down + labeled rm -f + network recreate + up --force-recreate; a
    deliberate destructive-recovery tool with no `dopemux mcp` equivalent).
  - P22-F2 · STRUCTURAL-BYPASS, regex-invisible: `src/dopemux/cli.py::
    _start_mcp_servers_with_progress` (the `dopemux init` default startup
    flow) builds its compose command as a Python list — see
    `_KNOWN_STRUCTURAL_GAPS` and the NOTE block in cli.py.
  - P22-F3 · PRE-EXISTING, allowlisted with justification: Makefile
    `pm-up`/webhook targets, `docker/leantime/configure_bridge.sh`,
    `scripts/deploy/setup/setup_dopemux.sh` (out-of-worklist, flagged for
    their own packet, not rewritten under the safe subset).

Mechanics: walks `git ls-files` (not the working tree) restricted to files
that can actually *execute* something — shell scripts, Python, PowerShell,
and Makefiles — since prose in docs/JSON/txt evidence dumps cannot start a
container. Every remaining hit must be covered by an allowlist entry with a
written justification.

See also: claudedocs/mcp-legacy-launch-path-worklist-2026-07-28.md (the file
sweep the deletions were driven by) and PR #1150 embedded-audit findings
A1/A2 (proof/pr_merge/embedded-audit/pr-1150/AUDITOR_REPORT.md).
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

# The previous regex (`docker[- ]compose(?:\s+-f\s+\S+)*\s+up\b`) only
# tolerated repeated `-f <file>` flags between `compose` and `up`, so any
# invocation that reordered or added flags -- e.g. `-p <project> -f <file>
# --profile <name> up` -- silently evaded detection (PR #1150 embedded-audit
# finding A1). The widened pattern below tolerates *arbitrary* flags between
# `compose` and `up`, so flag reordering cannot evade detection.
#
# `_UP_BOUNDARY` uses a lookahead `(?=[^\w-]|$)` instead of `\b` so that `up`
# embedded in a longer token (e.g. `docker compose logs -f up-service`) is
# not mistaken for the `up` subcommand: a plain `\b` would treat the boundary
# between `up` and the following `-` as a word boundary and false-positive
# on `up-service`; excluding `-` from the boundary class keeps `up-service`,
# `up-grade`, etc. from matching.
_UP_BOUNDARY = r"(?=[^\w-]|$)"
_FLEET_START_RE = re.compile(
    r"docker[- ]compose(?:\s+(?!up" + _UP_BOUNDARY + r")\S+)*\s+up" + _UP_BOUNDARY
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
    # --- discovered by the widened A1 regex (previously invisible to the "
    # narrower -f-only pattern) ---
    (
        "scripts/compose_nuke.sh",
        "deliberate operator-only destructive-recovery tool (down + "
        "labeled rm -f + network recreate + up --force-recreate) with no "
        "`dopemux mcp` equivalent; not a routine launch path",
    ),
    (
        "scripts/cleanup_compose.sh",
        "prints a manual restart suggestion "
        "('docker compose -p dopemux -f compose.yml up -d --remove-orphans "
        "--force-recreate') on completion, mirroring scripts/cleanup.sh; "
        "not executed -- every docker compose invocation this script "
        "actually runs is a `down`",
    ),
)

# Structural gaps this guard test cannot see: code paths that build a
# `docker compose ... up` invocation programmatically (e.g. as a Python
# list passed to subprocess) rather than as a contiguous source line. The
# line-based regex scan above is blind to these by construction, so they
# are disclosed here instead of silently omitted (PR #1150 embedded-audit
# finding A2). Each entry is `(\"<file>::<function>\", \"<justification>\")`;
# see test_known_structural_gaps_still_point_at_real_code below, which
# keeps this disclosure from rotting as the code moves.
_KNOWN_STRUCTURAL_GAPS: tuple[tuple[str, str], ...] = (
    (
        "src/dopemux/cli.py::_start_mcp_servers_with_progress",
        "docker compose up cmd is built as a Python list, not a "
        "contiguous line — invisible to this regex scan; tracked P-22 "
        "follow-up, see comment in cli.py",
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


def test_p22_safe_subset_no_unallowlisted_compose_up():
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
        "allowlist in tests/mcp/test_p22_safe_subset_guard.py. Either "
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


def test_fleet_start_regex_catches_flag_reordering_evasion():
    """PR #1150 embedded-audit finding A1: the old regex only tolerated
    repeated `-f <file>` flags between `compose` and `up`, so any
    invocation using other flags (most commonly `-p <project>`) evaded
    detection entirely. Assert the widened regex catches these."""
    positive_cases = [
        "docker compose -p dopemux -f compose.yml up -d --remove-orphans",
        'docker compose -p "$PROJECT" -f compose.yml up -d --remove-orphans --force-recreate',
    ]
    for line in positive_cases:
        assert _FLEET_START_RE.search(line), f"expected a match for: {line!r}"


def test_fleet_start_regex_does_not_false_positive_on_non_up_invocations():
    """The widened regex must still not fire on invocations that don't
    actually run `up` — including near-misses where `up` is a substring
    of a different token, not the `up` subcommand itself."""
    negative_cases = [
        "docker compose logs -f up-service",
        "docker compose down",
        "docker compose up-grade",
        "docker-compose up-and-running -d",
    ]
    for line in negative_cases:
        assert not _FLEET_START_RE.search(line), f"unexpected match for: {line!r}"


def test_known_structural_gaps_still_point_at_real_code():
    """Each _KNOWN_STRUCTURAL_GAPS entry names a `file.py::function_name`
    that the regex scan structurally cannot see. Parse the file and assert
    the function still exists there, so this disclosure can't silently rot
    (e.g. after a rename or move) without the guard test noticing."""
    import ast

    for entry, _justification in _KNOWN_STRUCTURAL_GAPS:
        file_part, sep, func_part = entry.partition("::")
        assert sep, f"malformed _KNOWN_STRUCTURAL_GAPS entry (no '::'): {entry!r}"

        abs_path = REPO_ROOT / file_part
        assert abs_path.is_file(), f"{file_part} does not exist"

        tree = ast.parse(abs_path.read_text(encoding="utf-8"), filename=file_part)
        func_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        assert func_part in func_names, (
            f"{func_part} not found as a top-level or nested function in "
            f"{file_part}"
        )
