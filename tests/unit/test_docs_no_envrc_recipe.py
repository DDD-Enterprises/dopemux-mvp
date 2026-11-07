"""D10: the MCP setup docs describe the launcher recipe, not the envrc-sourcing one."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

REPO = Path(__file__).resolve().parents[2]
RETIRED = "source .envrc.dopemux-mcp"
DOCS = (
    "AGENTS.md",
    ".claude/CLAUDE.md",
    "docs/02-how-to/mcp-setup-other-repos.md",
)
HINT_SOURCES = (
    "src/dopemux/mcp/lifecycle.py",
    "src/dopemux/mcp/agent_bootstrap.py",
)


@pytest.mark.parametrize("rel", DOCS)
def test_doc_has_no_envrc_sourcing_recipe(rel: str) -> None:
    text = (REPO / rel).read_text(encoding="utf-8")
    hits = [n for n, line in enumerate(text.splitlines(), 1) if RETIRED in line]
    assert not hits, f"{rel} still tells the reader to `{RETIRED}` (lines {hits})"


@pytest.mark.parametrize("rel", HINT_SOURCES)
def test_hint_sources_do_not_recommend_sourcing(rel: str) -> None:
    text = (REPO / rel).read_text(encoding="utf-8")
    assert RETIRED not in text, f"{rel} still recommends `{RETIRED}`"


def test_worktree_setup_guide_is_retired() -> None:
    assert not (REPO / ".claude" / "WORKTREE_MCP_SETUP.md").exists()


def test_how_to_documents_the_one_command_recipe() -> None:
    text = (REPO / "docs/02-how-to/mcp-setup-other-repos.md").read_text(encoding="utf-8")
    for needle in (
        "dopemux mcp init --repo",
        "dopemux mcp launch",
        "dopemux mcp switch-project",
        "dopemux mcp reap",
        "DOPEMUX_BIN",
        "--trust-env",
        "/mcp reconnect all",
    ):
        assert needle in text, f"how-to is missing `{needle}`"


# --- fix round 1: no stale envrc/"per worktree" hints in generated output -------------


def test_init_next_steps_do_not_tell_the_user_to_source_the_env_file(tmp_path, monkeypatch) -> None:
    """Runs the real `mcp init` (sidecar step faked out) and checks the rendered "Next:" lines."""
    from dopemux.commands import mcp_commands

    repo = tmp_path / "proj"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "rt" / "instances.json"))
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(tmp_path / "rt" / "port-leases.json"))
    monkeypatch.setattr(mcp_commands, "_init_sidecars", lambda *a, **k: True)

    result = CliRunner().invoke(mcp_commands.mcp, ["init", "--repo", str(repo)])

    assert result.exit_code == 0, result.output
    assert "Next:" in result.output
    assert "source" not in result.output.split("Next:", 1)[1]
    assert "direnv" not in result.output.split("Next:", 1)[1]
    assert ".mcp.json" in result.output.split("Next:", 1)[1]
    assert "dopemux mcp doctor --repo" in result.output.split("Next:", 1)[1]
    header = (repo / ".envrc.dopemux-mcp").read_text(encoding="utf-8").splitlines()[0]
    assert "Do not edit by hand" not in header
    assert "no dopemux command reads this file" in "\n".join(
        (repo / ".envrc.dopemux-mcp").read_text(encoding="utf-8").splitlines()[:3]
    )


def test_config_repair_next_actions_do_not_source_the_env_file(tmp_path) -> None:
    from dopemux.mcp.config_repair import plan_repair

    repo = tmp_path / "proj"
    repo.mkdir()
    catalog = {
        "version": 1,
        "defaults": {"per_worktree": ["conport"]},
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
            }
        },
    }
    plan = plan_repair(
        repo,
        catalog,
        dry_run=True,
        allocate_ports_fn=lambda *a, **k: {"CONPORT_MCP_PORT": 3015},
        project_env_exports_fn=lambda worktree, project_root: {},
        render_local_fn=lambda name, spec: {"type": spec.get("transport", "http")},
        global_claude_path=repo / "no-global-claude.json",
    )
    assert plan.next_actions
    assert not [a for a in plan.next_actions if "envrc" in a or a.startswith("source")]
    assert any(a.startswith("dopemux mcp doctor --repo") for a in plan.next_actions)


def test_agent_bootstrap_does_not_call_init_per_worktree() -> None:
    from dopemux.mcp.agent_bootstrap import bootstrap_section_body

    body = bootstrap_section_body()
    assert "once per worktree" not in body
    assert "never per worktree" in body


# Files that legitimately name the file: the generator/consumer of the per-repo agent note
# (repair-config writes it into target repos) and the how-to that describes that output.
_BOOTSTRAP_NAME_ALLOWED = {
    "src/dopemux/mcp/agent_bootstrap.py",
    "scripts/proofs/run_dnh_mcp_e2e.py",
    "docs/02-how-to/mcp-setup-other-repos.md",
}
_HISTORICAL_DOC_PREFIXES = (
    "docs/archive/",
    "docs/planes/",
    "docs/03-reference/planes/",
    "docs/05-audit-reports/",
    "docs/90-adr/",
)


def test_no_live_reference_to_the_retired_worktree_setup_guide() -> None:
    needle = "WORKTREE_MCP_SETUP.md"
    hits = []
    for top in ("src", "scripts", ".claude/modules", "docs"):
        for path in sorted((REPO / top).rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".md", ".sh", ".yaml", ".yml", ".toml"}:
                continue
            rel = path.relative_to(REPO).as_posix()
            if rel in _BOOTSTRAP_NAME_ALLOWED or rel.startswith(_HISTORICAL_DOC_PREFIXES):
                continue
            if needle in path.read_text(encoding="utf-8", errors="ignore"):
                hits.append(rel)
    assert not hits, f"still reference the deleted guide: {hits}"
