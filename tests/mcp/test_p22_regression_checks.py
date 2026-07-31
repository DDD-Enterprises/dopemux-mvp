"""Supervisor-mandated regression checks for the PR #1150 MUST_FIX repairs.

Four checks from the supervisor re-verdict (2026-07-28):
1. No active installation doc references a deleted installation entrypoint —
   every `scripts/*.sh` / `./install.sh`-style path referenced by the active
   install tutorials must exist in the repo.
2. The MCP health-probe hook recommends the repo-aware `dopemux mcp start`,
   never bare `dopemux mcp up` (whose no-``--repo`` branch is legacy
   cwd-compose and fails outside the primary checkout).
3. The surviving installer does not silently skip its advertised Docker
   stage — `scripts/deploy/setup/install-mcp-servers.sh` must not reference
   the deleted `install-docker-mcp-servers.sh` and must direct users to the
   dopemux CLI instead.
4. Active agent/runbook docs do not promote deprecated authority or raw
   fleet startup: `.github/copilot-instructions.md` must name
   `mcp_catalog.yaml` as the MCP authority, and the PM recovery runbook must
   not recommend `scripts/start.sh`, blanket name-filtered `docker rm -f`,
   or raw compose-up restarts.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_INSTALL_DOCS = [
    "docs/01-tutorials/installation.md",
    "docs/01-tutorials/installation-2.md",
    "docs/01-tutorials/installation-3.md",
    "INSTALL.md",
    "QUICK_START.md",
    "README.md",
]

_SCRIPT_REF_RE = re.compile(r"(?:\./)?(scripts/[A-Za-z0-9_./-]+\.sh|install\.sh)\b")


def test_active_install_docs_reference_only_existing_entrypoints():
    """Every script path an active install doc tells the user to run must exist."""
    missing: list[str] = []
    for rel in _INSTALL_DOCS:
        doc = REPO_ROOT / rel
        if not doc.is_file():
            continue
        for match in _SCRIPT_REF_RE.finditer(doc.read_text(encoding="utf-8", errors="replace")):
            script = match.group(1)
            if not (REPO_ROOT / script).is_file():
                missing.append(f"{rel} -> {script}")
    assert not missing, (
        "Active installation docs reference deleted/nonexistent entrypoints "
        "(restore a compatibility shim or update the doc): " + "; ".join(sorted(set(missing)))
    )


def test_health_probe_hook_recommends_repo_aware_mcp_start():
    """The hook's generic remediation must be `dopemux mcp start`, not bare `mcp up`."""
    hook = (REPO_ROOT / ".claude/hooks/mcp_health_probe.py").read_text(encoding="utf-8")
    assert "dopemux mcp start" in hook, "hook lost the repo-aware `mcp start` remediation"
    assert "dopemux mcp up" not in hook, (
        "hook recommends bare `dopemux mcp up`; its no-`--repo` branch is legacy "
        "cwd-compose and fails in worktrees/external repos (PR #1150 MUST_FIX P2)"
    )


def test_surviving_installer_does_not_silently_skip_docker_stage():
    """install-mcp-servers.sh must not call the deleted Docker installer."""
    installer = (REPO_ROOT / "scripts/deploy/setup/install-mcp-servers.sh").read_text(
        encoding="utf-8"
    )
    assert "install-docker-mcp-servers.sh" not in installer, (
        "installer still references the deleted install-docker-mcp-servers.sh — "
        "its Docker stage would silently no-op (PR #1150 MUST_FIX A3)"
    )
    assert "dopemux mcp" in installer, (
        "installer's Docker MCP stage must direct users to the dopemux CLI"
    )


def test_agent_and_runbook_docs_do_not_promote_deprecated_paths():
    """Copilot instructions carry catalog authority; recovery runbook is safe."""
    copilot = (REPO_ROOT / ".github/copilot-instructions.md").read_text(encoding="utf-8")
    assert "mcp_catalog.yaml" in copilot, (
        ".github/copilot-instructions.md must name mcp_catalog.yaml as the MCP "
        "authority (ADR-MCPINT-001; PR #1150 MUST_FIX A4)"
    )

    runbook = (
        REPO_ROOT / "docs/02-how-to/operations/pm-plane-runtime-recovery.md"
    ).read_text(encoding="utf-8")
    assert "scripts/start.sh" not in runbook, (
        "recovery runbook recommends the deleted scripts/start.sh (MUST_FIX A5)"
    )
    assert 'docker rm -f $(docker ps -aq --filter "name=task-orchestrator")' not in runbook, (
        "recovery runbook recommends blanket name-filtered force-removal, which "
        "destroys OTHER projects' task-orchestrator singletons (MUST_FIX A5)"
    )
    assert not re.search(r"docker[- ]compose[^\n]*\bup\b", runbook), (
        "recovery runbook still recommends raw compose-up restarts (MUST_FIX A5)"
    )
