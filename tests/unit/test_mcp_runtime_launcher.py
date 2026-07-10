"""Tests for docker_runtime helpers (compose commands / artifacts)."""

from __future__ import annotations

from pathlib import Path

from dopemux.mcp import docker_runtime as dr


def test_compose_up_command_includes_override_and_no_deps(tmp_path: Path):
    product = tmp_path
    (product / "compose.yml").write_text("services: {}\n")
    override = tmp_path / "compose.override.yml"
    envf = tmp_path / "mcp.env"
    override.write_text("services: {}\n")
    envf.write_text("X=1\n")
    cmd = dr.compose_up_command(
        product=product,
        override_path=override,
        env_file=envf,
        project_name="dopemux_proj_abcd",
        services=["conport", "dope-memory"],
        no_deps=True,
    )
    assert cmd[:2] == ["docker", "compose"]
    assert "--no-deps" in cmd
    assert "conport" in cmd
    assert str(override) in cmd
    assert "dopemux_proj_abcd" in cmd


def test_write_runtime_artifacts_dry_run_no_files(tmp_path: Path):
    runtime = tmp_path / "rt"
    paths = dr.write_runtime_artifacts(
        runtime,
        env_text="A=1\n",
        override_text="services: {}\n",
        plan={"x": 1},
        dry_run=True,
    )
    assert "mcp.env" in paths
    assert not runtime.exists()


def test_write_runtime_artifacts_writes(tmp_path: Path):
    runtime = tmp_path / "rt"
    paths = dr.write_runtime_artifacts(
        runtime,
        env_text="CONPORT_MCP_PORT=3041\n",
        override_text="services:\n  conport: {}\n",
        plan={"services": ["conport"]},
        dry_run=False,
    )
    assert Path(paths["mcp.env"]).is_file()
    assert "3041" in Path(paths["mcp.env"]).read_text()
    assert Path(paths["compose.override.yml"]).is_file()


def test_mcp_env_skips_secrets():
    text = dr.generate_mcp_env(
        {
            "CONPORT_MCP_PORT": 3041,
            "OPENAI_API_KEY": "sk-secret",
            "DOPEMUX_WORKSPACE_ID": "/tmp/x",
        }
    )
    assert "3041" in text
    assert "OPENAI_API_KEY" not in text
    assert "DOPEMUX_WORKSPACE_ID" in text


def test_labels_required_keys():
    labels = dr.build_labels(
        project_id="p",
        workspace_id="/w",
        project_root="/p",
        worktree_root="/w",
        project_hash="h",
        worktree_hash="abcd",
        instance_id="p-abcd-conport",
        service="conport",
        scope="worktree",
        transport="sse",
    )
    assert labels["dopemux.managed"] == "true"
    assert labels["dopemux.created_by"] == "dopemux-mcp"
    assert labels["dopemux.service"] == "conport"
