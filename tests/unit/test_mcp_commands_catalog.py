import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import click
import pytest
import yaml
from click.testing import CliRunner

from dopemux.commands import mcp_commands
from dopemux.mcp.project_identity import resolve_project_identity


def _identity(path):
    return SimpleNamespace(project_root=path)


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
    monkeypatch.setattr(mcp_commands, "resolve_project_identity", lambda **_: _identity(tmp_path))

    result = CliRunner().invoke(mcp_commands.mcp_init_cmd, [])

    assert result.exit_code == 0, result.output
    assert json.loads(mcp_path.read_text()) == template
    envrc = (tmp_path / mcp_commands.ENVRC_FILENAME).read_text()
    assert f"export DOPEMUX_PROJECT_ROOT={tmp_path}" in envrc
    assert f"export TASK_ORCHESTRATOR_PROJECT_ROOT={tmp_path}" in envrc
    assert "export CONPORT_MCP_PORT=" in envrc
    assert "export CONPORT_HTTP_PORT=" in envrc
    assert "export CONPORT_INFO_PORT=" in envrc


def test_committed_mcp_json_matches_root_catalog_defaults():
    repo_root = Path(__file__).resolve().parents[2]
    catalog = yaml.safe_load((repo_root / "mcp_catalog.yaml").read_text())
    defaults = catalog.get("defaults", {}).get("per_worktree", [])

    expected = mcp_commands._build_local_mcp_json(defaults, catalog)
    actual = json.loads((repo_root / ".mcp.json").read_text())

    assert actual == expected


def test_mcp_add_appends_primary_and_extra_catalog_ports(tmp_path, monkeypatch):
    catalog = _catalog()
    (tmp_path / mcp_commands.PROJECT_MCP_FILENAME).write_text('{"mcpServers": {}}\n')

    monkeypatch.setattr(mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(tmp_path))
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(mcp_commands, "resolve_project_identity", lambda **_: _identity(tmp_path))

    result = CliRunner().invoke(mcp_commands.mcp_add_cmd, ["conport"])

    assert result.exit_code == 0, result.output
    envrc = (tmp_path / mcp_commands.ENVRC_FILENAME).read_text()
    assert "export TASK_ORCHESTRATOR_PROJECT_ROOT=" in envrc
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


def test_project_identity_is_shared_across_linked_worktrees(tmp_path):
    repo = tmp_path / "repo"
    linked = tmp_path / "repo-linked"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / "README.md").write_text("test\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test User",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-m",
            "init",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "worktree", "add", str(linked)], cwd=repo, check=True, capture_output=True)

    main_identity = resolve_project_identity(cwd=repo, env={})
    linked_identity = resolve_project_identity(cwd=linked, env={})

    assert main_identity.project_root == repo.resolve()
    assert linked_identity.project_root == repo.resolve()
    assert main_identity.project_id == linked_identity.project_id
    assert linked_identity.worktree_root == linked.resolve()


def test_project_identity_allows_explicit_project_root_outside_git(tmp_path):
    identity = resolve_project_identity(
        cwd=tmp_path,
        env={"TASK_ORCHESTRATOR_PROJECT_ROOT": str(tmp_path)},
    )

    assert identity.project_root == tmp_path.resolve()
    assert identity.worktree_root == tmp_path.resolve()
    assert identity.git_common_dir is None


def test_load_catalog_falls_back_to_bundled_default(tmp_path, monkeypatch):
    monkeypatch.delenv(mcp_commands.CATALOG_ENV_VAR, raising=False)
    monkeypatch.setattr(mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(tmp_path))

    catalog = mcp_commands._load_catalog()

    task_orchestrator = catalog["servers"]["task-orchestrator"]
    assert task_orchestrator["transport"] == "stdio"
    assert task_orchestrator["state_scope"] == "per-repo"
    assert task_orchestrator["doctor_args"] == ["--print-resolution"]


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
    monkeypatch.setattr(mcp_commands, "resolve_project_identity", lambda **_: _identity(tmp_path))
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


def test_doctor_runs_relative_stdio_resolution_from_repo_root(tmp_path, monkeypatch):
    wrapper_dir = tmp_path / "scripts" / "mcp-wrappers"
    wrapper_dir.mkdir(parents=True)
    doctor_script = wrapper_dir / "doctor.sh"
    doctor_script.write_text("#!/usr/bin/env bash\nprintf 'state_id=test-state\\n'\n")
    doctor_script.chmod(0o755)
    relative_command = "scripts/mcp-wrappers/doctor.sh"
    (tmp_path / mcp_commands.PROJECT_MCP_FILENAME).write_text(json.dumps({
        "mcpServers": {
            "task-orchestrator": {"type": "stdio", "command": relative_command, "args": []},
        }
    }, indent=2) + "\n")
    (tmp_path / mcp_commands.ENVRC_FILENAME).write_text("")
    catalog = {
        "version": 1,
        "servers": {
            "task-orchestrator": {
                "scope": "per-worktree",
                "state_scope": "per-repo",
                "transport": "stdio",
                "command": relative_command,
                "doctor_args": ["--print-resolution"],
                "requires_env": ["TASK_ORCHESTRATOR_PROJECT_ROOT"],
            },
        },
    }

    monkeypatch.setattr(mcp_commands, "get_repo_root", lambda fallback_cwd=False: str(tmp_path))
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: catalog)
    monkeypatch.setattr(mcp_commands, "resolve_project_identity", lambda **_: _identity(tmp_path))
    monkeypatch.delenv("TASK_ORCHESTRATOR_PROJECT_ROOT", raising=False)
    subdir = tmp_path / "nested"
    subdir.mkdir()
    monkeypatch.chdir(subdir)

    result = CliRunner().invoke(mcp_commands.mcp_doctor_cmd, [])

    assert result.exit_code == 0, result.output
    assert "state_id=test-state" in result.output
    assert "nothing listening" not in result.output
