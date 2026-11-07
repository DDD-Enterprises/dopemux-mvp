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
        product_root=(
            _product(tmp_path)
            if not (tmp_path / "product").exists()
            else tmp_path / "product"
        ),
        process_env={},
        port_is_free_fn=lambda p: True,
    )


def _active(paths) -> List[Dict[str, Any]]:
    return PortLeaseRegistry.load(paths.leases).active_leases()


def test_start_dry_run_without_envrc_allocates_leases_and_is_not_blocked(
    tmp_path, paths
):
    repo = _repo(tmp_path)
    result = _start(tmp_path, repo, paths)

    codes = {f["code"] for f in result.blocking_findings}
    assert (
        "ENVRC_MISSING" not in codes and "PORT_UNSET" not in codes
    ), result.blocking_findings
    assert result.status == "PLANNED", result.blocking_findings

    worktree_root = result.project_identity["worktree_root"]
    by_service = {}
    for lease in _active(paths):
        by_service.setdefault(lease["service"], []).append(lease)
        assert lease["worktree_root"] == worktree_root
    assert {"conport", "dope-memory"} <= set(by_service)
    # The planned services use the leased ports.
    leased_vars = {
        lease["port_var"]: lease["port"] for ls in by_service.values() for lease in ls
    }
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
        # The ConPort tenant probe: shared-store history present (legacy_shared); an
        # unanswered probe would refuse conport (final review R2).
        sql = kwargs.get("input") or ""
        if "DPMX_TABLES=" in sql:
            return SimpleNamespace(
                returncode=0, stdout="DPMX_TABLES=decisions\n", stderr=""
            )
        if "DPMX_COUNT=" in sql:
            return SimpleNamespace(returncode=0, stdout="DPMX_COUNT=3\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = _start(tmp_path, repo, paths, dry_run=False, cmd_runner=cmd_runner)

    assert (
        result.status in {"PASS", "UNKNOWN", "WARN"} or result.exit_code == 0
    ), result.to_dict()
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


def test_non_dry_run_lock_follows_registry_path_not_home(tmp_path, monkeypatch):
    """No env override: the lock sits beside the registry and HOME stays untouched."""
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("DOPEMUX_MCP_RUNTIME_REGISTRY", raising=False)
    monkeypatch.delenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", raising=False)
    reg = tmp_path / "reg" / "instances.json"
    repo = _repo(tmp_path)

    result = run_lifecycle(
        "start",
        repo=repo,
        services=["conport", "dope-memory"],
        catalog=_catalog(),
        dry_run=False,
        registry_path=reg,
        docker_runner=_docker_empty(),
        cmd_runner=lambda cmd, **kw: SimpleNamespace(
            returncode=0, stdout="", stderr=""
        ),
        product_root=_product(tmp_path),
        process_env={},
        port_is_free_fn=lambda p: True,
    )

    assert reg.exists(), result.to_dict()
    assert (reg.parent / "registry.lock").exists()
    assert not (home / ".dopemux").exists()


def test_resolve_ports_lease_identity_matches_init_allocation(tmp_path, monkeypatch):
    """`_resolve_ports` (start) and `_allocate_ports` (init) write identical lease docs."""
    from dopemux.commands import mcp_commands

    monkeypatch.setenv(
        "DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "rt" / "instances.json")
    )
    repo = _repo(tmp_path)
    identity = resolve_identity_view(repo)
    init_leases = tmp_path / "init" / "port-leases.json"
    start_leases = tmp_path / "start" / "port-leases.json"

    monkeypatch.setenv("DOPEMUX_MCP_PORT_LEASE_REGISTRY", str(init_leases))
    init_ports = mcp_commands._allocate_ports(
        identity.worktree_root,
        ["conport", "dope-memory"],
        _catalog(),
        project_root=identity.project_root,
        is_free_fn=lambda p: True,
    )
    start_ports = lc._resolve_ports(
        identity,
        ["conport", "dope-memory"],
        _catalog(),
        lease_path=start_leases,
        is_free_fn=lambda p: True,
    )

    assert start_ports == init_ports

    def docs(path):
        out = {}
        for lease in PortLeaseRegistry.load(path).active_leases():
            out[lease["port_var"]] = {
                k: lease.get(k)
                for k in (
                    "project_id",
                    "lease_id",
                    "worktree_root",
                    "instance_id",
                    "workspace_id",
                    "port",
                )
            }
        return out

    assert docs(start_leases) and docs(start_leases) == docs(init_leases)


# --- a lease held by another service's container (fix round 1, finding F) ---


def _seed_collision(paths, identity) -> int:
    """Lease conport, then add the dope-memory lease on CONPORT_HTTP_PORT the live run made."""
    from dopemux.mcp.port_allocator import build_role_requests

    ports = lc._resolve_ports(
        identity,
        ["conport"],
        _catalog(),
        lease_path=paths.leases,
        is_free_fn=lambda p: True,
    )
    collided = ports["CONPORT_HTTP_PORT"]
    reg = PortLeaseRegistry.load(paths.leases)
    sibling = next(
        L for L in reg.active_leases() if L["port_var"] == "CONPORT_HTTP_PORT"
    )
    role = build_role_requests(
        ["dope-memory"],
        _catalog(),
        worktree=identity.worktree_root,
        project_root=identity.project_root,
    )[0]
    reg.upsert_lease(
        {
            **sibling,
            "lease_id": "lease_collided_dope_memory",
            "service": "dope-memory",
            "port_role": role.port_role,
            "port_var": "DOPE_MEMORY_PORT",
        }
    )
    reg.save()
    return collided


def _conport_container(identity, port: int):
    from dopemux.mcp import docker_inspect as di

    return di.DockerContainerInfo(
        id="c0ffee000001",
        name="dopemux-dnh_crm-test-conport",
        ports=[f"127.0.0.1:{port}->3004/tcp"],
        labels={
            "dopemux.managed": "true",
            "dopemux.service": "conport",
            "dopemux.project_id": identity.project_id,
            "dopemux.project_root": identity.project_root,
        },
        published_ports=[port],
    )


def test_resolve_ports_releases_lease_held_by_another_services_container(
    tmp_path, paths
):
    from dopemux.mcp import docker_inspect as di

    repo = _repo(tmp_path)
    identity = resolve_identity_view(repo)
    collided = _seed_collision(paths, identity)
    docker = di.DockerInspectResult(
        available=True, containers=[_conport_container(identity, collided)]
    )
    got = lc._resolve_ports(
        identity,
        ["dope-memory"],
        _catalog(),
        lease_path=paths.leases,
        is_free_fn=lambda p: p != collided,
        docker=docker,
    )
    assert got["DOPE_MEMORY_PORT"] != collided
    leases = PortLeaseRegistry.load(paths.leases).leases()
    old = next(L for L in leases if L["lease_id"] == "lease_collided_dope_memory")
    assert old["status"] == "released"
    dm = [
        L for L in leases if L["service"] == "dope-memory" and L["status"] == "active"
    ]
    assert [int(L["port"]) for L in dm] == [got["DOPE_MEMORY_PORT"]]


@pytest.mark.parametrize("skip_doctor", [True, False])
def test_start_heals_colliding_lease_instead_of_port_collision(
    skip_doctor, tmp_path, paths, monkeypatch
):
    from dopemux.mcp import docker_inspect as di

    repo = _repo(tmp_path)
    identity = resolve_identity_view(repo)
    collided = _seed_collision(paths, identity)
    container = _conport_container(identity, collided)
    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **_k: di.DockerInspectResult(available=True, containers=[container]),
    )
    result = run_lifecycle(
        "start",
        repo=repo,
        services=["dope-memory"],
        catalog=_catalog(),
        dry_run=True,
        registry_path=paths.reg,
        product_root=_product(tmp_path),
        process_env={},
        skip_doctor=skip_doctor,
        port_is_free_fn=lambda p: p != collided,
    )
    codes = {f["code"] for f in result.blocking_findings}
    assert "DOCKER_CONTAINER_PORT_COLLISION" not in codes, result.blocking_findings
    assert result.status == "PLANNED", result.blocking_findings
    dm = next(s for s in result.services if s["service"] == "dope-memory")
    assert dm["ports"]["DOPE_MEMORY_PORT"] != collided
