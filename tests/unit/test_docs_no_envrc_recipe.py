"""D10: the MCP setup docs describe the launcher recipe, not the envrc-sourcing one."""

from __future__ import annotations

from pathlib import Path

import pytest

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
