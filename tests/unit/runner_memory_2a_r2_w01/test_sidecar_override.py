"""docker_runtime: the generated compose override carries the dope-memory auth
mode and a read-only auth-directory mount (dope-memory only)."""

from __future__ import annotations

from pathlib import Path

import pytest

from dopemux.mcp import docker_runtime as dr


def _override(**extra):
    labels = dr.build_labels(
        project_id="dnh",
        workspace_id="/w",
        project_root="/w",
        worktree_root="/w",
        project_hash="h",
        worktree_hash="8d6d",
        instance_id="dnh-8d6d-x",
        service="x",
        scope="worktree",
        transport="http",
    )
    return dr.generate_compose_override(
        services=["conport", "dope-memory"],
        identity={
            "DOPEMUX_INSTANCE_ID": "8d6d",
            "DOPEMUX_WORKSPACE_ID": "/w",
            "DOPE_MEMORY_WORKSPACE_ID": "w",
            "DOPE_MEMORY_INSTANCE_ID": "8d6d",
        },
        ports={"CONPORT_HTTP_PORT": 3040, "CONPORT_MCP_PORT": 3041,
               "CONPORT_INFO_PORT": 4040, "DOPE_MEMORY_PORT": 3060},
        container_names={"conport": "c-conport", "dope-memory": "c-mem"},
        labels_by_service={"conport": labels, "dope-memory": labels},
        memory_data_path=Path("/tmp/mem-data"),
        **extra,
    )


def _service_block(text: str, name: str) -> str:
    start = text.index(f"  {name}:\n")
    rest = text[start + 1 :]
    nxt = [i for i in (rest.find("\n  conport:\n"), rest.find("\n  dope-memory:\n"), rest.find("\nnetworks:")) if i > 0]
    return text[start : start + 1 + (min(nxt) if nxt else len(rest))]


def test_should_render_auth_mode_and_readonly_directory_mount(tmp_path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    block = _service_block(_override(auth_mode="enforce", auth_dir=auth_dir), "dope-memory")
    assert 'DOPE_MEMORY_AUTH_MODE: "enforce"' in block
    assert 'DOPE_MEMORY_AUTH_DIR: "/run/dopemux-auth"' in block
    assert f'- "{auth_dir.resolve()}:/run/dopemux-auth:ro"' in block
    assert ":/data" in block  # the data mount is preserved


def test_should_default_to_log_mode(tmp_path):
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    block = _service_block(_override(auth_dir=auth_dir), "dope-memory")
    assert 'DOPE_MEMORY_AUTH_MODE: "log"' in block


def test_should_read_mode_from_environment_when_not_passed(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPE_MEMORY_AUTH_MODE", "enforce")
    block = _service_block(_override(auth_dir=tmp_path), "dope-memory")
    assert 'DOPE_MEMORY_AUTH_MODE: "enforce"' in block


def test_should_not_render_mount_for_a_missing_directory(tmp_path):
    block = _service_block(_override(auth_mode="log", auth_dir=tmp_path / "nope"), "dope-memory")
    assert "dopemux-auth" not in block
    assert 'DOPE_MEMORY_AUTH_MODE: "log"' in block  # mode still travels


def test_should_keep_dope_memory_auth_settings_out_of_the_conport_service(tmp_path):
    # W02 (B06) gives ConPort its own CONPORT_AUTH_* env and mount; the
    # dope-memory settings must stay in the dope-memory block only.
    auth_dir = tmp_path / "auth"
    auth_dir.mkdir()
    text = _override(auth_mode="enforce", auth_dir=auth_dir)
    conport = _service_block(text, "conport")
    memory = _service_block(text, "dope-memory")
    assert "DOPE_MEMORY_AUTH" not in conport
    assert conport.count("dopemux-auth:ro") == 1
    assert memory.count("dopemux-auth:ro") == 1


def test_should_reject_an_unknown_mode():
    with pytest.raises(ValueError, match="auth mode"):
        _override(auth_mode="permissive")


def test_should_keep_dropping_token_and_password_keys_from_generated_env():
    text = dr.generate_mcp_env(
        {"DOPE_MEMORY_PORT": 3060, "SOME_TOKEN": "x", "DB_PASSWORD": "y", "DOPE_MEMORY_AUTH_MODE": "log"}
    )
    assert "SOME_TOKEN" not in text and "DB_PASSWORD" not in text
    assert "DOPE_MEMORY_PORT=3060" in text
