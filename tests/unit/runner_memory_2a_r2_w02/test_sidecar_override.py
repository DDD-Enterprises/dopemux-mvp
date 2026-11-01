"""docker_runtime: the ConPort sidecar gets its own auth mode and the read-only
hash-directory mount; W01's dope-memory lines are preserved."""

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


def _block(text: str, name: str) -> str:
    start = text.index(f"  {name}:\n")
    rest = text[start + 1 :]
    nxt = [i for i in (rest.find("\n  conport:\n"), rest.find("\n  dope-memory:\n"), rest.find("\nnetworks:")) if i > 0]
    return text[start : start + 1 + (min(nxt) if nxt else len(rest))]


@pytest.fixture()
def auth_dir(tmp_path):
    path = tmp_path / "auth"
    path.mkdir()
    return path


def test_should_render_the_conport_mode_and_a_readonly_directory_mount(auth_dir):
    block = _block(_override(conport_auth_mode="enforce", auth_dir=auth_dir), "conport")
    assert 'CONPORT_AUTH_MODE: "enforce"' in block
    assert 'CONPORT_AUTH_DIR: "/run/dopemux-auth"' in block
    assert f'- "{auth_dir.resolve()}:/run/dopemux-auth:ro"' in block
    assert "volumes:" in block
    # the pre-existing identity env is kept
    assert 'DOPEMUX_WORKSPACE_ID: "/w"' in block and "ports: !override" in block


def test_should_switch_each_server_separately(auth_dir):
    text = _override(auth_mode="enforce", conport_auth_mode="log", auth_dir=auth_dir)
    assert 'CONPORT_AUTH_MODE: "log"' in _block(text, "conport")
    assert 'DOPE_MEMORY_AUTH_MODE: "enforce"' in _block(text, "dope-memory")
    assert "DOPE_MEMORY_AUTH_MODE" not in _block(text, "conport")
    assert "CONPORT_AUTH_MODE" not in _block(text, "dope-memory")


def test_should_default_to_log_and_read_the_env_when_not_passed(auth_dir, monkeypatch):
    monkeypatch.delenv("CONPORT_AUTH_MODE", raising=False)
    assert 'CONPORT_AUTH_MODE: "log"' in _block(_override(auth_dir=auth_dir), "conport")
    monkeypatch.setenv("CONPORT_AUTH_MODE", "enforce")
    assert 'CONPORT_AUTH_MODE: "enforce"' in _block(_override(auth_dir=auth_dir), "conport")


def test_should_not_mount_a_missing_directory_but_still_send_the_mode(tmp_path):
    block = _block(_override(conport_auth_mode="log", auth_dir=tmp_path / "nope"), "conport")
    assert "dopemux-auth" not in block and "volumes:" not in block
    assert 'CONPORT_AUTH_MODE: "log"' in block


def test_should_reject_an_unknown_conport_mode():
    with pytest.raises(ValueError, match="conport auth mode"):
        _override(conport_auth_mode="permissive")


def test_should_preserve_the_dope_memory_changes(auth_dir):
    text = _override(auth_mode="enforce", auth_dir=auth_dir)
    memory = _block(text, "dope-memory")
    assert 'DOPE_MEMORY_AUTH_MODE: "enforce"' in memory
    assert 'DOPE_MEMORY_AUTH_DIR: "/run/dopemux-auth"' in memory
    assert f'- "{auth_dir.resolve()}:/run/dopemux-auth:ro"' in memory
    assert ":/data" in memory
    assert text.count("dopemux-auth:ro") == 2  # one mount per server, nothing else


def test_should_never_put_a_token_or_hash_in_the_override(auth_dir):
    (auth_dir / "memory-token-hashes.json").write_text('{"' + "a" * 64 + '": "runner:codex"}')
    text = _override(conport_auth_mode="enforce", auth_dir=auth_dir)
    assert "a" * 64 not in text and "runner:codex" not in text
    assert "bearer" not in text.lower() and "memory-token-hashes" not in text  # only the directory travels


def test_should_keep_generated_env_dropping_secret_keys():
    text = dr.generate_mcp_env({"CONPORT_HTTP_PORT": 3040, "CONPORT_AUTH_TOKEN": "x", "DB_PASSWORD": "y"})
    assert "CONPORT_AUTH_TOKEN" not in text and "DB_PASSWORD" not in text
    assert "CONPORT_HTTP_PORT=3040" in text
