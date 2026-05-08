import json

import click
import pytest
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


def _singleton_catalog():
    return {
        "version": 1,
        "defaults": {"per_worktree": []},
        "servers": {
            "exa": {
                # No catalog description — lets us verify user descriptions are preserved
                # by sync-globals when the catalog is silent.
                "scope": "singleton",
                "transport": "http",
                "url": "https://exa.example/mcp",
                "requires_env": ["EXA_API_KEY"],
            },
            "gpt-researcher": {
                "scope": "singleton",
                "transport": "http",
                "url": "http://localhost:3009/mcp",
            },
        },
    }


def test_allocate_ports_raises_on_cross_server_collision():
    """Two per-worktree servers whose default_port_base land on the same hash slot must error."""
    catalog = {
        "version": 1,
        "servers": {
            "alpha": {
                "scope": "per-worktree",
                "transport": "http",
                "port_var": "ALPHA_PORT",
                "default_port_base": 4000,
            },
            "beta": {
                "scope": "per-worktree",
                "transport": "http",
                "port_var": "BETA_PORT",
                # Collides with alpha because both use the same hash offset
                # against the same base. _allocate_ports must reject this.
                "default_port_base": 4000,
            },
        },
    }

    with pytest.raises(click.ClickException) as excinfo:
        mcp_commands._allocate_ports("/tmp/wt-collide", ["alpha", "beta"], catalog)

    msg = str(excinfo.value.message)
    assert "Internal port collision" in msg
    assert "alpha" in msg
    assert "beta" in msg


def test_sync_globals_dry_run_reports_additions_without_writing(tmp_path, monkeypatch):
    """Default invocation (no --apply) must not touch ~/.claude.json."""
    catalog = _singleton_catalog()
    global_path = tmp_path / ".claude.json"
    global_path.write_text(json.dumps({"mcpServers": {}}, indent=2) + "\n")
    original_bytes = global_path.read_bytes()

    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(mcp_commands, "_claude_global_path", lambda: global_path)

    result = CliRunner().invoke(mcp_commands.mcp_sync_globals_cmd, [])

    assert result.exit_code == 0, result.output
    assert "+ exa" in result.output
    assert "+ gpt-researcher" in result.output
    assert "Dry-run only" in result.output
    assert global_path.read_bytes() == original_bytes


def test_sync_globals_apply_writes_backup_and_preserves_user_description(tmp_path, monkeypatch):
    """--apply writes a timestamped backup, syncs functional fields, keeps user-set descriptions."""
    catalog = _singleton_catalog()
    global_path = tmp_path / ".claude.json"
    global_path.write_text(json.dumps({
        "mcpServers": {
            "exa": {
                "type": "http",
                "url": "https://exa.example/mcp",
                "description": "User's customized description",
                "env": {"EXA_API_KEY": "${EXA_API_KEY:-}"},
            }
        }
    }, indent=2) + "\n")

    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(mcp_commands, "_claude_global_path", lambda: global_path)

    result = CliRunner().invoke(mcp_commands.mcp_sync_globals_cmd, ["--apply"])

    assert result.exit_code == 0, result.output
    written = json.loads(global_path.read_text())["mcpServers"]
    assert "gpt-researcher" in written            # newly added
    assert written["exa"]["description"] == "User's customized description"
    backups = list(tmp_path.glob(".claude.json.backup-*"))
    assert len(backups) == 1


def test_sync_globals_keeps_extra_entries_without_prune(tmp_path, monkeypatch):
    """Without --prune, entries in ~/.claude.json that aren't in the catalog are kept."""
    catalog = _singleton_catalog()
    global_path = tmp_path / ".claude.json"
    global_path.write_text(json.dumps({
        "mcpServers": {
            "legacy-server": {"type": "http", "url": "https://legacy.example/mcp"},
        }
    }, indent=2) + "\n")

    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(mcp_commands, "_claude_global_path", lambda: global_path)

    result = CliRunner().invoke(mcp_commands.mcp_sync_globals_cmd, ["--apply"])

    assert result.exit_code == 0, result.output
    written = json.loads(global_path.read_text())["mcpServers"]
    assert "legacy-server" in written
    assert "exa" in written


def test_sync_globals_prune_removes_unknown_entries(tmp_path, monkeypatch):
    catalog = _singleton_catalog()
    global_path = tmp_path / ".claude.json"
    global_path.write_text(json.dumps({
        "mcpServers": {
            "legacy-server": {"type": "http", "url": "https://legacy.example/mcp"},
        }
    }, indent=2) + "\n")

    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(mcp_commands, "_claude_global_path", lambda: global_path)

    result = CliRunner().invoke(mcp_commands.mcp_sync_globals_cmd, ["--apply", "--prune"])

    assert result.exit_code == 0, result.output
    written = json.loads(global_path.read_text())["mcpServers"]
    assert "legacy-server" not in written
    assert "exa" in written


def test_doctor_aggregates_problems_and_exits_nonzero(tmp_path, monkeypatch):
    """`doctor` reports every issue it finds and exits 1 if any are present."""
    catalog = {
        "version": 1,
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "requires_env": ["DOPEMUX_WORKSPACE_ID"],
            },
            "ghost": {
                # Declared in local .mcp.json but absent from catalog
                "scope": "per-worktree",
                "transport": "http",
            },
        },
    }
    # Catalog deliberately omits "ghost" — local declaration must surface as a problem.
    catalog["servers"].pop("ghost")

    (tmp_path / mcp_commands.PROJECT_MCP_FILENAME).write_text(json.dumps({
        "mcpServers": {
            "conport": {"type": "sse", "url": "http://localhost:3005/mcp"},
            "ghost": {"type": "http", "url": "http://localhost:9999/mcp"},
        }
    }, indent=2) + "\n")
    # No mcp_commands.ENVRC_FILENAME (.envrc.dopemux-mcp) file → that's a separate problem.

    monkeypatch.setattr(mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(tmp_path))
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    # Ensure required env is unset and port appears unreachable.
    monkeypatch.delenv("DOPEMUX_WORKSPACE_ID", raising=False)
    monkeypatch.delenv("CONPORT_MCP_PORT", raising=False)

    result = CliRunner().invoke(mcp_commands.mcp_doctor_cmd, [])

    assert result.exit_code == 1, result.output
    # Doctor reports multiple problems in a single run (envrc missing + ghost server +
    # missing required env + missing port var). Assert each surfaces, ignoring the
    # logger's line-wrapping of long absolute paths.
    assert "issue(s) found" in result.output
    assert ".envrc" in result.output
    assert "ghost" in result.output
    assert "DOPEMUX_WORKSPACE_ID" in result.output
    assert "CONPORT_MCP_PORT" in result.output
