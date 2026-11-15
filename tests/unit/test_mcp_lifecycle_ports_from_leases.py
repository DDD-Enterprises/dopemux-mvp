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


# --- Task B7-2: envrc ports with no lease behind them are re-leased on start ----------

_LEASE_VARS = (
    "CONPORT_MCP_PORT",
    "CONPORT_HTTP_PORT",
    "CONPORT_INFO_PORT",
    "DOPE_MEMORY_PORT",
)


def _init_then_stop(tmp_path, paths):
    """`init` (allocator leases + an envrc naming them), then `stop` (leases released)."""
    from dopemux.commands import mcp_commands

    repo = _repo(tmp_path)
    identity = resolve_identity_view(repo)
    init_ports = mcp_commands._allocate_ports(
        identity.worktree_root,
        ["conport", "dope-memory"],
        _catalog(),
        project_root=identity.project_root,
        is_free_fn=lambda p: True,
    )
    (repo / ".envrc.dopemux-mcp").write_text(
        "".join(f"export {var}={init_ports[var]}\n" for var in _LEASE_VARS)
    )
    reg = PortLeaseRegistry.load(paths.leases)
    for lease in reg.active_leases():  # what a full `dopemux mcp stop` releases
        reg.mark_released(lease_id=str(lease["lease_id"]))
    reg.save()
    assert _active(paths) == []
    return repo, identity, {var: int(init_ports[var]) for var in _LEASE_VARS}


def _active_by_var(paths, worktree_root: str) -> Dict[str, int]:
    return {
        L["port_var"]: int(L["port"])
        for L in _active(paths)
        if L.get("worktree_root") == worktree_root
    }


def test_a_start_after_init_and_stop_re_leases_the_envrc_ports(tmp_path, paths):
    repo, identity, envrc_ports = _init_then_stop(tmp_path, paths)
    result = _start(tmp_path, repo, paths)
    assert not result.blocking_findings, result.blocking_findings
    assert _active_by_var(paths, identity.worktree_root) == envrc_ports
    planned = {v: p for s in result.services for v, p in s["ports"].items()}
    assert {v: planned[v] for v in _LEASE_VARS} == envrc_ports


def test_an_envrc_port_another_worktree_leased_is_replaced(tmp_path, paths):
    repo, identity, envrc_ports = _init_then_stop(tmp_path, paths)
    taken = envrc_ports["CONPORT_MCP_PORT"]
    reg = PortLeaseRegistry.load(paths.leases)
    reg.upsert_lease(
        {
            "lease_id": "lease_other_worktree",
            "service": "conport",
            "port": taken,
            "port_role": "sse",
            "port_var": "CONPORT_MCP_PORT",
            "worktree_root": str(tmp_path / "elsewhere"),
            "project_root": str(tmp_path / "elsewhere"),
            "project_id": "elsewhere",
            "worktree_hash": "ffff",
            "scope": "worktree",
            "status": "active",
        }
    )
    reg.save()
    result = _start(tmp_path, repo, paths)
    assert not result.blocking_findings, result.blocking_findings
    ours = _active_by_var(paths, identity.worktree_root)
    assert ours["CONPORT_MCP_PORT"] != taken
    conport = next(s for s in result.services if s["service"] == "conport")
    assert conport["ports"]["CONPORT_MCP_PORT"] == ours["CONPORT_MCP_PORT"]
    # the other ports were free and are leased exactly as the envrc names them
    assert {v: ours[v] for v in _LEASE_VARS if v != "CONPORT_MCP_PORT"} == {
        v: envrc_ports[v] for v in _LEASE_VARS if v != "CONPORT_MCP_PORT"
    }


def test_allocate_false_still_returns_the_envrc_ports_unleased(tmp_path, paths):
    repo, identity, envrc_ports = _init_then_stop(tmp_path, paths)
    ports = lc._resolve_ports(
        identity,
        ["conport", "dope-memory"],
        _catalog(),
        lease_path=paths.leases,
        env={var: str(port) for var, port in envrc_ports.items()},
        allocate=False,
        is_free_fn=lambda p: True,
    )
    assert {v: ports[v] for v in _LEASE_VARS} == envrc_ports
    assert _active(paths) == []  # status/doctor/stop never lease


def test_the_launcher_cold_start_shape_re_leases_too(tmp_path, paths):
    """ensure_backend calls run_lifecycle("start", services=[svc],
    hold_instance_lock=False) with port vars scrubbed from the process env."""
    repo, identity, envrc_ports = _init_then_stop(tmp_path, paths)
    result = run_lifecycle(
        "start",
        repo=repo,
        services=["conport"],
        catalog=_catalog(),
        dry_run=False,
        registry_path=paths.reg,
        docker_runner=_docker_empty(),
        cmd_runner=lambda cmd, **kw: SimpleNamespace(
            returncode=0,
            stdout="DPMX_TABLES=decisions\nDPMX_COUNT=3\n" if kw.get("input") else "",
            stderr="",
        ),
        product_root=_product(tmp_path),
        process_env={},
        port_is_free_fn=lambda p: True,
        trust_env=False,
        hold_instance_lock=False,
    )
    assert result.exit_code == 0, result.to_dict()
    conport_vars = ("CONPORT_MCP_PORT", "CONPORT_HTTP_PORT", "CONPORT_INFO_PORT")
    assert _active_by_var(paths, identity.worktree_root) == {
        v: envrc_ports[v] for v in conport_vars
    }


def test_an_envrc_port_this_instances_own_container_publishes_is_adopted(
    tmp_path, paths
):
    """The leases are gone (a recovered lease file) but this worktree's own sidecar
    still publishes the envrc ports: they are leased as they are, not replaced."""
    from dopemux.mcp import docker_inspect as di

    repo, identity, envrc_ports = _init_then_stop(tmp_path, paths)
    conport_ports = [
        envrc_ports[v]
        for v in ("CONPORT_MCP_PORT", "CONPORT_HTTP_PORT", "CONPORT_INFO_PORT")
    ]
    own = di.DockerContainerInfo(
        id="c0ffee000002",
        name="dopemux-dnh-crm-own-conport",
        ports=[f"127.0.0.1:{p}->{p}/tcp" for p in conport_ports],
        labels={
            "dopemux.managed": "true",
            "dopemux.service": "conport",
            "dopemux.project_id": identity.project_id,
            "dopemux.worktree_hash": identity.worktree_hash,
        },
        published_ports=conport_ports,
    )
    busy = set(conport_ports)
    ports = lc._resolve_ports(
        identity,
        ["conport"],
        _catalog(),
        lease_path=paths.leases,
        env={var: str(port) for var, port in envrc_ports.items()},
        is_free_fn=lambda p: p not in busy,
        docker=di.DockerInspectResult(available=True, containers=[own]),
    )
    conport_vars = ("CONPORT_MCP_PORT", "CONPORT_HTTP_PORT", "CONPORT_INFO_PORT")
    assert {v: ports[v] for v in conport_vars} == {
        v: envrc_ports[v] for v in conport_vars
    }
    assert _active_by_var(paths, identity.worktree_root) == {
        v: envrc_ports[v] for v in conport_vars
    }


def test_a_port_another_worktrees_container_publishes_is_not_adopted(tmp_path, paths):
    """B7 micro round (a): only this worktree's own sidecar counts as free; another
    worktree's container publishing the preferred envrc port forces a fresh port."""
    from dopemux.mcp import docker_inspect as di

    repo, identity, envrc_ports = _init_then_stop(tmp_path, paths)
    taken = envrc_ports["CONPORT_MCP_PORT"]
    foreign = di.DockerContainerInfo(
        id="c0ffee000003",
        name="dopemux-dnh-crm-other-conport",
        ports=[f"127.0.0.1:{taken}->{taken}/tcp"],
        labels={
            "dopemux.managed": "true",
            "dopemux.service": "conport",
            "dopemux.project_id": identity.project_id,
            "dopemux.worktree_hash": "ffff",  # another worktree of the same project
        },
        published_ports=[taken],
    )
    ports = lc._resolve_ports(
        identity,
        ["conport"],
        _catalog(),
        lease_path=paths.leases,
        env={var: str(port) for var, port in envrc_ports.items()},
        is_free_fn=lambda p: p != taken,
        docker=di.DockerInspectResult(available=True, containers=[foreign]),
    )
    assert ports["CONPORT_MCP_PORT"] != taken
    ours = _active_by_var(paths, identity.worktree_root)
    assert ours["CONPORT_MCP_PORT"] == ports["CONPORT_MCP_PORT"]
    assert ours["CONPORT_HTTP_PORT"] == envrc_ports["CONPORT_HTTP_PORT"]


# --- Task F: doctor port findings are re-evaluated after allocation ----------------


def _foreign_conport_on_stale_envrc_port(tmp_path, paths, monkeypatch):
    """`init` then `stop`; another project's conport sidecar holds the envrc port.

    The doctor and the lifecycle both read docker through
    ``docker_inspect.inspect_running_containers``, so patching it feeds both.
    """
    from dopemux.mcp import docker_inspect as di

    repo, identity, envrc_ports = _init_then_stop(tmp_path, paths)
    taken = envrc_ports["CONPORT_MCP_PORT"]
    foreign = di.DockerContainerInfo(
        id="c0ffee000004",
        name="dopemux-other-project-conport",
        ports=[f"127.0.0.1:{taken}->3004/tcp"],
        labels={
            "dopemux.managed": "true",
            "dopemux.service": "conport",
            "dopemux.project_id": "another-project",
            "dopemux.worktree_hash": "eeee",
        },
        published_ports=[taken],
    )
    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **_k: di.DockerInspectResult(available=True, containers=[foreign]),
    )
    return repo, identity, taken


def _run(op, tmp_path, repo, paths, taken, is_free=None):
    product = tmp_path / "product"
    if not product.exists():
        product = _product(tmp_path)
    return run_lifecycle(
        op,
        repo=repo,
        services=["conport", "dope-memory"],
        catalog=_catalog(),
        dry_run=True,
        registry_path=paths.reg,
        docker_runner=_docker_empty(),
        product_root=product,
        process_env={},
        port_is_free_fn=is_free or (lambda p: p != taken),
    )


def test_start_after_init_and_stop_ignores_a_foreign_container_on_the_stale_port(
    tmp_path, paths, monkeypatch
):
    repo, identity, taken = _foreign_conport_on_stale_envrc_port(
        tmp_path, paths, monkeypatch
    )
    result = _run("start", tmp_path, repo, paths, taken)

    assert result.status != "BLOCKED", result.blocking_findings
    codes = {f["code"] for f in result.blocking_findings}
    assert "DOCKER_CONTAINER_WRONG_PROJECT" not in codes, result.blocking_findings
    conport = next(s for s in result.services if s["service"] == "conport")
    assert conport["ports"]["CONPORT_MCP_PORT"] != taken


def test_stop_does_not_re_evaluate_doctor_port_findings(tmp_path, paths, monkeypatch):
    """Control: only start/restart re-evaluate port findings; other ops are unchanged.

    A stop result's warnings are always empty, so the registry is made unreadable:
    REGISTRY_PARSE_ERROR makes ``_stop_blocking`` return every finding, and the
    doctor's container finding must still be among them.
    """
    repo, identity, taken = _foreign_conport_on_stale_envrc_port(
        tmp_path, paths, monkeypatch
    )
    paths.reg.parent.mkdir(parents=True, exist_ok=True)
    paths.reg.write_text("{not json")
    result = _run("stop", tmp_path, repo, paths, taken)

    assert result.operation == "stop"
    codes = {f["code"] for f in result.blocking_findings}
    assert "DOCKER_CONTAINER_WRONG_PROJECT" in codes, result.blocking_findings
    assert not [
        w for w in result.warnings if w.get("code") == "DOCTOR_PORT_FINDING_REEVALUATED"
    ]


def test_start_still_carries_a_port_independent_doctor_blocker(
    tmp_path, paths, monkeypatch
):
    """Control: a doctor blocker that does not depend on ports stays a blocker."""
    repo, identity, taken = _foreign_conport_on_stale_envrc_port(
        tmp_path, paths, monkeypatch
    )
    (repo / ".mcp.json").write_text("{not json")
    result = _run("start", tmp_path, repo, paths, taken)

    assert result.status == "BLOCKED"
    codes = {f["code"] for f in result.blocking_findings}
    assert "MCP_JSON_PARSE_ERROR" in codes, result.blocking_findings


def test_a_re_evaluated_port_finding_is_recorded_as_an_info_warning(
    tmp_path, paths, monkeypatch
):
    """A successful start result carries no preflight warnings (pre-existing), so
    the entry is observed on a result that is blocked for another reason."""
    repo, identity, taken = _foreign_conport_on_stale_envrc_port(
        tmp_path, paths, monkeypatch
    )
    (repo / ".mcp.json").write_text("{not json")
    result = _run("start", tmp_path, repo, paths, taken)

    codes = {f["code"] for f in result.blocking_findings}
    assert "DOCKER_CONTAINER_WRONG_PROJECT" not in codes, result.blocking_findings
    reevaluated = [
        w for w in result.warnings if w.get("code") == "DOCTOR_PORT_FINDING_REEVALUATED"
    ]
    assert len(reevaluated) == 1, result.warnings
    assert reevaluated[0]["service"] == "conport"
    assert reevaluated[0]["severity"] == "INFO"
    assert "DOCKER_CONTAINER_WRONG_PROJECT" in reevaluated[0]["message"]


def _sibling_container(identity, port: int, **label_overrides):
    """A managed conport sidecar publishing ``port`` that is not this worktree's."""
    from dopemux.mcp import docker_inspect as di

    labels = {
        "dopemux.managed": "true",
        "dopemux.service": "conport",
        "dopemux.scope": "worktree",
        "dopemux.project_id": identity.project_id,
        "dopemux.worktree_hash": "ffff",
        "dopemux.workspace_id": "/elsewhere/sibling",
        "dopemux.worktree_root": "/elsewhere/sibling",
        "dopemux.project_root": "/elsewhere/sibling",
    }
    labels.update(label_overrides)
    labels = {k: v for k, v in labels.items() if v is not None}
    return di.DockerContainerInfo(
        id="c0ffee000005",
        name="dopemux-sibling-conport",
        ports=[f"127.0.0.1:{port}->3004/tcp"],
        labels=labels,
        published_ports=[port],
    )


def _patch_docker(monkeypatch, container):
    from dopemux.mcp import docker_inspect as di

    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **_k: di.DockerInspectResult(available=True, containers=[container]),
    )


def _blocked_by_port_collision(result):
    assert result.status == "BLOCKED", result.to_dict()
    codes = {f["code"] for f in result.blocking_findings}
    assert "DOCKER_CONTAINER_PORT_COLLISION" in codes, result.blocking_findings


def test_a_sibling_worktrees_container_on_the_port_our_lease_keeps_blocks(
    tmp_path, paths, monkeypatch
):
    repo = _repo(tmp_path)
    first = _start(tmp_path, repo, paths)
    conport = next(s for s in first.services if s["service"] == "conport")
    kept = conport["ports"]["CONPORT_MCP_PORT"]
    identity = resolve_identity_view(repo)
    _patch_docker(monkeypatch, _sibling_container(identity, kept))

    result = _run("start", tmp_path, repo, paths, kept, is_free=lambda p: True)

    _blocked_by_port_collision(result)


def test_a_sibling_worktrees_container_on_a_re_leased_stale_port_blocks(
    tmp_path, paths, monkeypatch
):
    repo, identity, envrc_ports = _init_then_stop(tmp_path, paths)
    taken = envrc_ports["CONPORT_MCP_PORT"]
    _patch_docker(monkeypatch, _sibling_container(identity, taken))

    # The connect probe misses the published port, so the same port is re-leased.
    result = _run("start", tmp_path, repo, paths, taken, is_free=lambda p: True)

    _blocked_by_port_collision(result)


def test_a_managed_container_without_project_id_of_another_root_blocks(
    tmp_path, paths, monkeypatch
):
    repo = _repo(tmp_path)
    first = _start(tmp_path, repo, paths)
    conport = next(s for s in first.services if s["service"] == "conport")
    kept = conport["ports"]["CONPORT_MCP_PORT"]
    identity = resolve_identity_view(repo)
    legacy = _sibling_container(
        identity,
        kept,
        **{
            "dopemux.project_id": None,
            "dopemux.worktree_hash": None,
            "dopemux.scope": None,
        },
    )
    _patch_docker(monkeypatch, legacy)

    result = _run("start", tmp_path, repo, paths, kept, is_free=lambda p: True)

    _blocked_by_port_collision(result)


def test_another_projects_container_on_a_kept_port_is_not_called_same_project(
    tmp_path, paths, monkeypatch
):
    repo = _repo(tmp_path)
    first = _start(tmp_path, repo, paths)
    conport = next(s for s in first.services if s["service"] == "conport")
    kept = conport["ports"]["CONPORT_MCP_PORT"]
    identity = resolve_identity_view(repo)
    other = _sibling_container(identity, kept, **{"dopemux.project_id": "other-proj"})
    _patch_docker(monkeypatch, other)

    result = _run("start", tmp_path, repo, paths, kept, is_free=lambda p: True)

    assert result.status == "BLOCKED", result.to_dict()
    codes = {f["code"] for f in result.blocking_findings}
    assert "PORT_OWNED_BY_OTHER_PROJECT" in codes, result.blocking_findings
    assert not [
        f for f in result.blocking_findings if "same-project" in f.get("message", "")
    ]


def test_a_worktree_hash_without_a_scope_label_is_another_worktree(
    tmp_path, paths, monkeypatch
):
    repo = _repo(tmp_path)
    first = _start(tmp_path, repo, paths)
    conport = next(s for s in first.services if s["service"] == "conport")
    kept = conport["ports"]["CONPORT_MCP_PORT"]
    identity = resolve_identity_view(repo)
    unscoped = _sibling_container(identity, kept, **{"dopemux.scope": None})
    _patch_docker(monkeypatch, unscoped)

    result = _run("start", tmp_path, repo, paths, kept, is_free=lambda p: True)

    _blocked_by_port_collision(result)


# --- Task G: retained leases and the resolved port map are still validated ---------


def _retarget_lease(paths, port_var: str, port: int) -> None:
    reg = PortLeaseRegistry.load(paths.leases)
    lease = next(L for L in reg.active_leases() if L["port_var"] == port_var)
    reg.upsert_lease({**lease, "port": port})
    reg.save()


def _leased_start(tmp_path, paths):
    repo = _repo(tmp_path)
    first = _start(tmp_path, repo, paths)
    conport = next(s for s in first.services if s["service"] == "conport")
    return repo, conport["ports"]["CONPORT_MCP_PORT"]


def test_two_retained_leases_on_one_port_block(tmp_path, paths):
    repo, conport_port = _leased_start(tmp_path, paths)
    _retarget_lease(paths, "DOPE_MEMORY_PORT", conport_port)

    result = _run("start", tmp_path, repo, paths, conport_port, is_free=lambda p: True)

    assert result.status == "BLOCKED", result.to_dict()
    codes = {f["code"] for f in result.blocking_findings}
    assert "PORT_INTRA_CONFIG_COLLISION" in codes, result.blocking_findings


def test_a_retained_lease_on_the_reserved_orchestrator_port_blocks(tmp_path, paths):
    repo, _ = _leased_start(tmp_path, paths)
    _retarget_lease(paths, "CONPORT_MCP_PORT", 7890)

    result = _run("start", tmp_path, repo, paths, 7890, is_free=lambda p: True)

    assert result.status == "BLOCKED", result.to_dict()
    codes = {f["code"] for f in result.blocking_findings}
    assert "PORT_RESERVED_COLLISION" in codes, result.blocking_findings


def test_a_same_project_container_without_hash_or_scope_and_foreign_workspace_blocks(
    tmp_path, paths, monkeypatch
):
    repo, kept = _leased_start(tmp_path, paths)
    identity = resolve_identity_view(repo)
    leased = _active_by_var(paths, identity.worktree_root)
    (repo / ".envrc.dopemux-mcp").write_text(
        "".join(f"export {var}={port}\n" for var, port in leased.items())
    )
    legacy = _sibling_container(
        identity,
        kept,
        **{"dopemux.worktree_hash": None, "dopemux.scope": None},
    )
    _patch_docker(monkeypatch, legacy)

    result = _run("start", tmp_path, repo, paths, kept, is_free=lambda p: True)

    assert result.status == "BLOCKED", result.to_dict()


def test_split_deferred_doctor_keeps_everything_when_docker_is_unavailable():
    from dopemux.mcp import docker_inspect as di

    finding = {
        "code": "DOCKER_CONTAINER_WRONG_PROJECT",
        "service": "conport",
        "evidence": ["some-container"],
    }
    down = di.DockerInspectResult(available=False, error="no docker")
    kept, dropped = lc._split_deferred_doctor(
        [finding], down, {"CONPORT_MCP_PORT": 3005}
    )
    assert kept == [finding] and dropped == []


def test_split_deferred_doctor_drops_only_findings_off_the_resolved_ports():
    from dopemux.mcp import docker_inspect as di

    def container(name, port):
        return di.DockerContainerInfo(
            id=name, name=name, ports=[], labels={}, published_ports=[port]
        )

    on_port = {"code": "DOCKER_CONTAINER_WRONG_PROJECT", "evidence": ["on-resolved"]}
    off_port = {"code": "DOCKER_CONTAINER_WRONG_PROJECT", "evidence": ["on-stale"]}
    gone = {"code": "DOCKER_CONTAINER_PORT_COLLISION", "evidence": ["not-running"]}
    docker = di.DockerInspectResult(
        available=True,
        containers=[container("on-resolved", 3005), container("on-stale", 3040)],
    )
    kept, dropped = lc._split_deferred_doctor(
        [on_port, off_port, gone], docker, {"CONPORT_MCP_PORT": 3005}
    )
    assert kept == [on_port]
    assert dropped == [off_port, gone]


def test_a_container_bearing_our_expected_name_with_foreign_labels_blocks(
    tmp_path, paths, monkeypatch
):
    """Probe 26: a moved worktree's leftover, off the resolved ports, same name."""
    from dopemux.mcp import docker_runtime as dr

    repo, kept = _leased_start(tmp_path, paths)
    identity = resolve_identity_view(repo)
    expected = dr.container_name_for(
        dr.project_slug(Path(identity.project_root).name),
        identity.worktree_hash,
        "conport",
    )
    leftover = _sibling_container(
        identity,
        3999,
        **{"dopemux.worktree_hash": None, "dopemux.scope": None},
    )
    leftover.name = expected
    _patch_docker(monkeypatch, leftover)

    result = _run("start", tmp_path, repo, paths, kept, is_free=lambda p: True)

    assert result.status == "BLOCKED", result.to_dict()
    codes = {f["code"] for f in result.blocking_findings}
    assert "DOCKER_CONTAINER_WRONG_PROJECT" in codes, result.blocking_findings


@pytest.mark.parametrize("evidence", [{"evidence": []}, {}])
def test_split_deferred_doctor_keeps_a_finding_without_a_container_name(evidence):
    from dopemux.mcp import docker_inspect as di

    finding = {"code": "DOCKER_CONTAINER_WRONG_PROJECT", **evidence}
    docker = di.DockerInspectResult(available=True, containers=[])
    kept, dropped = lc._split_deferred_doctor(
        [finding], docker, {"CONPORT_MCP_PORT": 3005}, ["dopemux-x-conport"]
    )
    assert kept == [finding] and dropped == []


def test_split_deferred_doctor_keeps_a_finding_bearing_an_expected_name():
    from dopemux.mcp import docker_inspect as di

    def container(name, port):
        return di.DockerContainerInfo(
            id=name, name=name, ports=[], labels={}, published_ports=[port]
        )

    ours = {"code": "DOCKER_CONTAINER_WRONG_PROJECT", "evidence": ["dopemux-x-conport"]}
    other = {"code": "DOCKER_CONTAINER_WRONG_PROJECT", "evidence": ["unrelated"]}
    docker = di.DockerInspectResult(
        available=True,
        containers=[container("dopemux-x-conport", 3999), container("unrelated", 3998)],
    )
    kept, dropped = lc._split_deferred_doctor(
        [ours, other], docker, {"CONPORT_MCP_PORT": 3005}, ["dopemux-x-conport"]
    )
    assert kept == [ours]
    assert dropped == [other]
