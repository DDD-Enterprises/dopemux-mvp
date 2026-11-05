"""Lifecycle resolves ports from the lease registry when no envrc exists (D2, D7)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from dopemux.mcp import lifecycle as lc
from dopemux.mcp.lifecycle import run_lifecycle
from dopemux.mcp.port_leases import PortLeaseRegistry
from dopemux.mcp.runtime_registry import RuntimeRegistry
from dopemux.mcp.runtime_state import resolve_identity_view


def _catalog() -> Dict[str, Any]:
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport", "dope-memory", "task-orchestrator"]},
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "extra_port_vars": [
                    {"var": "CONPORT_HTTP_PORT", "base": 3004},
                    {"var": "CONPORT_INFO_PORT", "base": 4004},
                ],
            },
            "dope-memory": {
                "scope": "per-worktree",
                "transport": "http",
                "url_template": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
                "port_var": "DOPE_MEMORY_PORT",
                "default_port_base": 3020,
            },
            "task-orchestrator": {
                "scope": "per-worktree",
                "state_scope": "per-repo",
                "transport": "http",
                "management_model": "wrapper-singleton",
                "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
                "default_port_base": 7890,
            },
        },
    }


def _repo(tmp_path: Path, *, envrc: str | None = None) -> Path:
    repo = tmp_path / "dNh_CRM"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    (repo / ".mcp.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "conport": {
                        "type": "sse",
                        "url": "http://localhost:${CONPORT_MCP_PORT:-3005}/sse",
                    },
                    "dope-memory": {
                        "type": "http",
                        "url": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
                    },
                }
            }
        )
    )
    if envrc is not None:
        (repo / ".envrc.dopemux-mcp").write_text(envrc)
    return repo


def _docker_empty():
    def runner(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    return runner


def _product(tmp_path: Path) -> Path:
    product = tmp_path / "product"
    product.mkdir()
    (product / "compose.yml").write_text("services: {}\n")
    (product / "scripts" / "mcp-wrappers").mkdir(parents=True)
    (
        product / "scripts" / "mcp-wrappers" / "task-orchestrator-http-singleton.sh"
    ).write_text("#!/bin/bash\n")
    return product


@pytest.fixture
def paths(tmp_path: Path, monkeypatch) -> SimpleNamespace:
    reg = tmp_path / "reg" / "instances.json"
    leases = tmp_path / "reg" / "port-leases.json"
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(reg))
    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(leases))
    return SimpleNamespace(reg=reg, leases=leases)


def _start(tmp_path: Path, repo: Path, paths, *, dry_run: bool = True, cmd_runner=None):
    return run_lifecycle(
        "start",
        repo=repo,
        services=["conport", "dope-memory"],
        catalog=_catalog(),
        dry_run=dry_run,
        registry_path=paths.reg,
        docker_runner=_docker_empty(),
        cmd_runner=cmd_runner,
        product_root=_product(tmp_path) if not (tmp_path / "product").exists() else tmp_path / "product",
        process_env={},
        port_is_free_fn=lambda p: True,
    )


def _active(paths) -> List[Dict[str, Any]]:
    return PortLeaseRegistry.load(paths.leases).active_leases()


def test_start_dry_run_without_envrc_allocates_leases_and_is_not_blocked(tmp_path, paths):
    repo = _repo(tmp_path)
    result = _start(tmp_path, repo, paths)

    codes = {f["code"] for f in result.blocking_findings}
    assert "ENVRC_MISSING" not in codes and "PORT_UNSET" not in codes, result.blocking_findings
    assert result.status == "PLANNED", result.blocking_findings

    worktree_root = result.project_identity["worktree_root"]
    by_service = {}
    for lease in _active(paths):
        by_service.setdefault(lease["service"], []).append(lease)
        assert lease["worktree_root"] == worktree_root
    assert {"conport", "dope-memory"} <= set(by_service)
    # The planned services use the leased ports.
    leased_vars = {l["port_var"]: l["port"] for ls in by_service.values() for l in ls}
    conport = next(s for s in result.services if s["service"] == "conport")
    assert conport["ports"]["CONPORT_MCP_PORT"] == leased_vars["CONPORT_MCP_PORT"]
    # Dry run still must not create the instance registry.
    assert not paths.reg.exists()


def test_start_reuses_existing_active_leases(tmp_path, paths):
    repo = _repo(tmp_path)
    first = _start(tmp_path, repo, paths)
    leases_before = _active(paths)
    assert len(leases_before) == 4  # 3 conport roles + dope-memory
    second = _start(tmp_path, repo, paths)

    def ports(r):
        return {s["service"]: s["ports"] for s in r.services}

    assert ports(first) and ports(first) == ports(second)
    assert _active(paths) == leases_before
    assert len(_active(paths)) == len(leases_before)


def test_envrc_ports_still_win_when_present_and_leased(tmp_path, paths):
    repo = _repo(tmp_path)
    # First pass has no envrc and allocates; then the envrc names those same ports.
    first = _start(tmp_path, repo, paths)
    leased = {s["service"]: s["ports"] for s in first.services}
    assert leased and not first.blocking_findings
    cp = leased["conport"]
    envrc = (
        f"export CONPORT_HTTP_PORT={cp['CONPORT_HTTP_PORT']}\n"
        f"export CONPORT_MCP_PORT={cp['CONPORT_MCP_PORT']}\n"
        f"export CONPORT_INFO_PORT={cp['CONPORT_INFO_PORT']}\n"
        f"export DOPE_MEMORY_PORT={leased['dope-memory']['DOPE_MEMORY_PORT']}\n"
    )
    (repo / ".envrc.dopemux-mcp").write_text(envrc)
    before = _active(paths)

    second = _start(tmp_path, repo, paths)

    assert {s["service"]: s["ports"] for s in second.services} == leased
    assert _active(paths) == before
    assert "ENVRC_MISSING" not in {w["code"] for w in second.warnings}
    assert not second.blocking_findings, second.blocking_findings


def test_final_registry_save_reloads_under_lock(tmp_path, paths):
    repo = _repo(tmp_path)
    foreign = {
        "instance_id": "other-proj-beef-conport",
        "project_id": "other-proj",
        "service": "conport",
        "status": "running",
    }

    def cmd_runner(cmd, **kwargs):
        cmd = list(cmd)
        if "up" in cmd:
            # A concurrent start in another process lands its record after we loaded.
            paths.reg.parent.mkdir(parents=True, exist_ok=True)
            doc = {"schema_version": "1.0", "updated_at": "x", "instances": [foreign]}
            paths.reg.write_text(json.dumps(doc))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = _start(tmp_path, repo, paths, dry_run=False, cmd_runner=cmd_runner)

    assert result.status in {"PASS", "UNKNOWN", "WARN"} or result.exit_code == 0, result.to_dict()
    ids = {i["instance_id"] for i in RuntimeRegistry.load(paths.reg).instances()}
    assert "other-proj-beef-conport" in ids
    assert any(i.endswith("-conport") and i != "other-proj-beef-conport" for i in ids)


def test_envrc_missing_is_info_and_not_blocking(tmp_path, paths):
    assert "ENVRC_MISSING" not in lc.BLOCKING_FINDING_CODES
    repo = _repo(tmp_path)
    result = run_lifecycle(
        "status",
        repo=repo,
        services=["conport", "dope-memory"],
        catalog=_catalog(),
        registry_path=paths.reg,
        docker_runner=_docker_empty(),
        process_env={},
        port_is_free_fn=lambda p: True,
    )
    assert "ENVRC_MISSING" not in {f["code"] for f in result.blocking_findings}
    missing = [w for w in result.warnings if w["code"] == "ENVRC_MISSING"]
    assert missing and missing[0]["severity"] == "INFO"
    # status never allocates leases
    assert not paths.leases.exists()


def test_runtime_dir_for_matches_original_expression(tmp_path, paths):
    repo = _repo(tmp_path)
    identity = resolve_identity_view(repo)
    got = lc.runtime_dir_for(identity, registry_path=paths.reg)
    slug = lc.dr.project_slug(Path(identity.project_root).name)
    assert got == paths.reg.parent / f"{slug}-{identity.worktree_hash}"
    assert lc.runtime_dir_for(identity) == (
        Path(paths.reg).parent / f"{slug}-{identity.worktree_hash}"
    )


def test_resolve_ports_returns_catalog_port_var_keys(tmp_path, paths):
    repo = _repo(tmp_path)
    identity = resolve_identity_view(repo)
    ports = lc._resolve_ports(
        identity,
        ["conport", "dope-memory"],
        _catalog(),
        lease_path=paths.leases,
        is_free_fn=lambda p: True,
    )
    assert set(ports) == {
        "CONPORT_MCP_PORT",
        "CONPORT_HTTP_PORT",
        "CONPORT_INFO_PORT",
        "DOPE_MEMORY_PORT",
    }
    assert all(isinstance(v, int) for v in ports.values())
