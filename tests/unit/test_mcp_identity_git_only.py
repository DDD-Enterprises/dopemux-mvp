"""Identity comes from git only; ambient DOPEMUX_* env is ignored unless --trust-env."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict

import pytest
from click.testing import CliRunner

from dopemux.commands import mcp_commands
from dopemux.mcp.lifecycle import resolve_target_repo, run_lifecycle
from dopemux.mcp.port_diagnostics import instance_id_for_path
from dopemux.mcp.project_identity import resolve_project_identity
from dopemux.mcp.runtime_state import resolve_identity_view
from dopemux.worktree_commands import get_repo_root

_AMBIENT_VARS = (
    "DOPEMUX_WORKSPACE_ROOT",
    "DOPEMUX_PROJECT_ROOT",
    "DOPEMUX_INSTANCE_ID",
    "DOPEMUX_WORKSPACE_ID",
    "TASK_ORCHESTRATOR_PROJECT_ROOT",
)


@pytest.fixture(autouse=True)
def _clean_ambient_env(monkeypatch):
    for name in _AMBIENT_VARS:
        monkeypatch.delenv(name, raising=False)


def _git_init(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True, capture_output=True)
    (path / "README").write_text("x\n")
    subprocess.run(["git", "add", "README"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


def _foreign_env(foreign: Path) -> Dict[str, str]:
    return {
        "DOPEMUX_WORKSPACE_ROOT": str(foreign),
        "DOPEMUX_PROJECT_ROOT": str(foreign),
        "DOPEMUX_INSTANCE_ID": "dcd6",
        "DOPEMUX_WORKSPACE_ID": str(foreign),
        "TASK_ORCHESTRATOR_PROJECT_ROOT": str(foreign),
    }


@pytest.fixture
def repos(tmp_path):
    main = (tmp_path / "main").resolve()
    foreign = (tmp_path / "foreign").resolve()
    _git_init(main)
    _git_init(foreign)
    linked = (tmp_path / "linked").resolve()
    subprocess.run(["git", "worktree", "add", str(linked)], cwd=main, check=True, capture_output=True)
    return SimpleNamespace(main=main, foreign=foreign, linked=linked)


def test_identity_view_ignores_ambient_env_for_linked_worktree(repos):
    view = resolve_identity_view(repos.linked, envrc_values=_foreign_env(repos.foreign))

    assert view.project_root == str(repos.main)
    assert view.worktree_root == str(repos.linked)
    assert view.instance_id == instance_id_for_path(repos.linked)
    assert view.workspace_id == str(repos.linked)
    assert not any("forced identity" in e for e in view.evidence)


def test_identity_view_trust_env_keeps_override(repos):
    view = resolve_identity_view(
        repos.linked, envrc_values=_foreign_env(repos.foreign), trust_env=True
    )

    assert view.project_root == str(repos.foreign)


def test_identity_stable_across_symlinked_path(repos, tmp_path):
    link = tmp_path / "link"
    os.symlink(repos.main, link)

    real_view = resolve_identity_view(repos.main)
    link_view = resolve_identity_view(link)

    assert real_view.project_id == link_view.project_id
    assert real_view.instance_id == link_view.instance_id


def test_resolve_project_identity_none_env_is_empty(repos, monkeypatch):
    monkeypatch.setenv("DOPEMUX_PROJECT_ROOT", str(repos.foreign))

    identity = resolve_project_identity(cwd=repos.main)

    assert identity.project_root == repos.main


def test_get_repo_root_prefers_git_over_env(repos, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(repos.foreign))
    monkeypatch.setenv("DOPEMUX_PROJECT_ROOT", str(repos.foreign))
    monkeypatch.chdir(repos.linked)

    assert Path(get_repo_root(fallback_cwd=False)).resolve() == repos.linked


def test_get_repo_root_trust_env_restores_precedence(repos, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(repos.foreign))
    monkeypatch.chdir(repos.linked)

    assert Path(get_repo_root(fallback_cwd=False, trust_env=True)).resolve() == repos.foreign


def test_resolve_target_repo_uses_git_toplevel_from_subdir(repos):
    sub = repos.linked / "a" / "b"
    sub.mkdir(parents=True)

    assert resolve_target_repo(None, cwd=sub) == repos.linked


def _catalog() -> Dict[str, Any]:
    return {
        "version": 1,
        "defaults": {"per_worktree": ["dope-memory"]},
        "servers": {
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
                "management_model": "compose-service",
            }
        },
    }


def _docker_empty():
    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner


def test_run_lifecycle_dry_run_identity_matches_clean_shell(repos, tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(tmp_path / "leases.json"))
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "runtime.json"))
    product = tmp_path / "product"
    (product / "scripts" / "mcp-wrappers").mkdir(parents=True)
    (product / "compose.yml").write_text("services: {}\n")

    def _run(process_env, tag):
        return run_lifecycle(
            "start",
            repo=repos.linked,
            catalog=_catalog(),
            dry_run=True,
            process_env=process_env,
            docker_runner=_docker_empty(),
            registry_path=tmp_path / tag / "instances.json",
            product_root=product,
        )

    polluted = _run(_foreign_env(repos.foreign), "polluted")
    clean = _run({}, "clean")

    assert polluted.project_identity == clean.project_identity
    assert polluted.project_identity["project_root"] == str(repos.main)
    assert polluted.project_identity["worktree_root"] == str(repos.linked)


@pytest.fixture
def init_env(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(tmp_path / "leases.json"))
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "runtime.json"))
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: _catalog())
    monkeypatch.setattr(mcp_commands, "_catalog_path", lambda: None)


def test_init_repo_option_targets_given_checkout_not_env(repos, init_env, monkeypatch):
    for name, value in _foreign_env(repos.foreign).items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(repos.foreign)

    result = CliRunner().invoke(mcp_commands.mcp, ["init", "--repo", str(repos.main)])

    assert result.exit_code == 0, result.output
    assert (repos.main / ".mcp.json").exists()
    assert (repos.main / ".envrc.dopemux-mcp").exists()
    assert not (repos.foreign / ".mcp.json").exists()
    assert not (repos.foreign / ".envrc.dopemux-mcp").exists()
    envrc = (repos.main / ".envrc.dopemux-mcp").read_text()
    assert f"DOPEMUX_PROJECT_ROOT={repos.main}" in envrc


def test_init_force_preserves_conport_db_keys(repos, init_env):
    envrc = repos.main / ".envrc.dopemux-mcp"
    envrc.write_text("export CONPORT_DB_NAME=x\nexport CONPORT_DB_USER=tenant\n")

    result = CliRunner().invoke(
        mcp_commands.mcp, ["init", "--force", "--repo", str(repos.main)]
    )

    assert result.exit_code == 0, result.output
    text = envrc.read_text()
    assert "export CONPORT_DB_NAME=x" in text
    assert "export CONPORT_DB_USER=tenant" in text
