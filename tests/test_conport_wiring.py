import json
import stat

from dopemux.conport.wire_project import install_post_checkout_hook, wire_conport_project


def test_hook_installer_writes_portable_post_checkout(tmp_path):
    (tmp_path / ".git" / "hooks").mkdir(parents=True)

    hook_path = install_post_checkout_hook(tmp_path)

    assert hook_path.exists()
    assert hook_path.name == "post-checkout"
    assert hook_path.stat().st_mode & stat.S_IXUSR

    content = hook_path.read_text(encoding="utf-8")
    assert "git rev-parse --show-toplevel" in content
    assert "dopemux wire-conport" in content
    assert "scripts/wire_conport_project.py" not in content


def test_wire_conport_writes_required_claude_config(tmp_path):
    (tmp_path / ".git").mkdir()
    config_path = wire_conport_project(project=str(tmp_path), instance="main")

    assert config_path == tmp_path / ".claude" / "claude_config.json"
    assert config_path.exists()

    config = json.loads(config_path.read_text(encoding="utf-8"))
    conport = config["mcpServers"]["conport"]

    assert conport["type"] == "stdio"
    assert conport["command"] == "docker"
    assert conport["args"][0:2] == ["exec", "-i"]
    assert "mcp-conport" in conport["args"]
    assert conport["args"][-4:] == ["uvx", "--from", "context-portal-mcp", "conport-mcp"]
    assert "DOPEMUX_INSTANCE_ID" in conport["env"]
    assert "DOPEMUX_WORKSPACE_ID" in conport["env"]
    assert conport["env"]["DOPEMUX_INSTANCE_ID"] == "main"
    assert conport["env"]["DOPEMUX_WORKSPACE_ID"] == str(tmp_path)


def test_wire_conport_uses_explicit_project_over_workspace_env(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "/tmp/stale-workspace")

    config_path = wire_conport_project(project=str(tmp_path), instance="main")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    conport = config["mcpServers"]["conport"]

    assert conport["env"]["DOPEMUX_WORKSPACE_ID"] == str(tmp_path)


def test_wire_conport_still_allows_env_workspace_without_explicit_project(tmp_path, monkeypatch):
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ID", "/tmp/workspace-from-env")

    config_path = wire_conport_project(instance="main")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    conport = config["mcpServers"]["conport"]

    assert conport["env"]["DOPEMUX_WORKSPACE_ID"] == "/tmp/workspace-from-env"
