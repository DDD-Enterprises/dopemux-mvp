import json

from click.testing import CliRunner

from dopemux.commands import mcp_commands


def _catalog():
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport"]},
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${CONPORT_MCP_PORT}/mcp",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "extra_port_vars": [
                    {"var": "CONPORT_HTTP_PORT", "base": 3004},
                    {"var": "CONPORT_INFO_PORT", "base": 4004},
                ],
                "requires_env": ["DOPEMUX_WORKSPACE_ID"],
            }
        },
    }


def test_mcp_init_keeps_matching_committed_template_and_writes_envrc(tmp_path, monkeypatch):
    catalog = _catalog()
    template = mcp_commands._build_local_mcp_json(["conport"], catalog)
    mcp_path = tmp_path / mcp_commands.PROJECT_MCP_FILENAME
    mcp_path.write_text(json.dumps(template, indent=2) + "\n")

    monkeypatch.setattr(mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(tmp_path))
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)

    result = CliRunner().invoke(mcp_commands.mcp_init_cmd, [])

    assert result.exit_code == 0, result.output
    assert json.loads(mcp_path.read_text()) == template
    envrc = (tmp_path / mcp_commands.ENVRC_FILENAME).read_text()
    assert "export CONPORT_MCP_PORT=" in envrc
    assert "export CONPORT_HTTP_PORT=" in envrc
    assert "export CONPORT_INFO_PORT=" in envrc


def test_mcp_add_appends_primary_and_extra_catalog_ports(tmp_path, monkeypatch):
    catalog = _catalog()
    (tmp_path / mcp_commands.PROJECT_MCP_FILENAME).write_text('{"mcpServers": {}}\n')

    monkeypatch.setattr(mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(tmp_path))
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)

    result = CliRunner().invoke(mcp_commands.mcp_add_cmd, ["conport"])

    assert result.exit_code == 0, result.output
    envrc = (tmp_path / mcp_commands.ENVRC_FILENAME).read_text()
    assert envrc.count("export CONPORT_MCP_PORT=") == 1
    assert envrc.count("export CONPORT_HTTP_PORT=") == 1
    assert envrc.count("export CONPORT_INFO_PORT=") == 1
