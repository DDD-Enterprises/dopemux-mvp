"""Unit tests for agent bootstrap doc generation."""

from __future__ import annotations

from pathlib import Path

from dopemux.mcp.agent_bootstrap import (
    BEGIN_MARKER,
    END_MARKER,
    apply_agent_bootstrap,
    bootstrap_section_body,
    plan_agent_bootstrap,
    verify_bootstrap_content,
    wrap_marked_section,
)


def test_create_new_doc(tmp_path: Path):
    repo = tmp_path / "r"
    repo.mkdir()
    plan = plan_agent_bootstrap(repo)
    assert plan.kind == "create"
    assert plan.reason == "AGENT_BOOTSTRAP_CREATED"
    apply_agent_bootstrap(plan)
    text = plan.path.read_text()
    assert BEGIN_MARKER in text
    assert END_MARKER in text
    assert verify_bootstrap_content(text) == []
    assert "dopemux mcp start" in text
    assert "dopemux mcp doctor" in text
    assert "Do not start this repo's MCP services by cd'ing into `dopemux-mvp`" in text
    assert "Authority" in text


def test_update_marked_section(tmp_path: Path):
    repo = tmp_path / "r"
    repo.mkdir()
    path = repo / ".claude" / "WORKTREE_MCP_SETUP.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "# Header kept\n\n"
        f"{BEGIN_MARKER}\nOLD CONTENT\n{END_MARKER}\n\n"
        "# Footer kept\n"
    )
    plan = plan_agent_bootstrap(repo)
    assert plan.kind == "update"
    apply_agent_bootstrap(plan)
    text = path.read_text()
    assert "# Header kept" in text
    assert "# Footer kept" in text
    assert "OLD CONTENT" not in text
    assert "dopemux mcp start" in text


def test_append_when_no_markers(tmp_path: Path):
    repo = tmp_path / "r"
    repo.mkdir()
    path = repo / ".claude" / "WORKTREE_MCP_SETUP.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Existing unrelated guide\n\nKeep me.\n")
    plan = plan_agent_bootstrap(repo)
    assert plan.kind == "append"
    apply_agent_bootstrap(plan)
    text = path.read_text()
    assert "Keep me." in text
    assert BEGIN_MARKER in text
    assert text.index("Keep me.") < text.index(BEGIN_MARKER)


def test_noop_when_identical(tmp_path: Path):
    repo = tmp_path / "r"
    repo.mkdir()
    plan = plan_agent_bootstrap(repo)
    apply_agent_bootstrap(plan)
    plan2 = plan_agent_bootstrap(repo)
    assert plan2.kind == "noop"
    mtime = plan.path.stat().st_mtime_ns
    apply_agent_bootstrap(plan2)
    assert plan.path.stat().st_mtime_ns == mtime


def test_body_contains_required_phrases():
    body = bootstrap_section_body()
    assert verify_bootstrap_content(wrap_marked_section(body)) == []
    assert "PORT_HASH_BUCKET_COLLISION_RISK" in body or "hash" in body.lower()
