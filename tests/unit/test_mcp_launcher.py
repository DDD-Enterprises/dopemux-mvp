"""Unit tests for `dopemux mcp launch` (Task 3c, D2/D4/D7).

Lifecycle, probe, docker, clock and sleep are injected fakes; registries and
lock files live under tmp_path. No real docker call is made.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from dopemux.mcp import docker_inspect as di
from dopemux.mcp import docker_runtime as dr
from dopemux.mcp import launcher
from dopemux.mcp.launcher import LaunchError
from dopemux.mcp.locks import locked_reload_and_save
from dopemux.mcp.runtime_registry import RuntimeRegistry, build_instance_record
from dopemux.mcp.stdio_proxy import BackendSpec

CATALOG: Dict[str, Any] = {
    "version": 1,
    "servers": {
        "conport": {
            "scope": "per-worktree",
            "transport": "sse",
            "client": "launcher",
            "management_model": "compose-service",
            "docker_compose_service": "conport",
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
            "client": "launcher",
            "management_model": "compose-service",
            "docker_compose_service": "dope-memory",
            "url_template": "http://localhost:${DOPE_MEMORY_PORT:-3020}/mcp",
            "port_var": "DOPE_MEMORY_PORT",
            "default_port_base": 3020,
        },
        "task-orchestrator": {
            "scope": "per-worktree",
            "transport": "http",
            "client": "launcher",
            "management_model": "wrapper-singleton",
            "reserved_port": 7890,
            "url_template": "http://127.0.0.1:${TASK_ORCHESTRATOR_HTTP_PORT:-7890}/mcp",
            "port_var": "TASK_ORCHESTRATOR_HTTP_PORT",
            "default_port_base": 7890,
        },
    },
}
CONPORT_PORTS = {"CONPORT_MCP_PORT": 3105, "CONPORT_HTTP_PORT": 3104, "CONPORT_INFO_PORT": 4104}
TO_BACKEND = BackendSpec("http://127.0.0.1:7890/mcp", "http", "task-orchestrator")


def _managed_entry(name: str) -> Dict[str, Any]:
    return {"type": "stdio", "command": "${DOPEMUX_BIN:-dopemux}", "args": ["mcp", "launch", name]}


def _git_repo(tmp_path: Path, servers: Dict[str, Any] | None = None) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    if servers is None:
        servers = {name: _managed_entry(name) for name in CATALOG["servers"]}
    (repo / ".mcp.json").write_text(json.dumps({"mcpServers": servers}), encoding="utf-8")
    return repo.resolve()


@pytest.fixture
def registry(tmp_path: Path, monkeypatch) -> Path:
    path = tmp_path / "runtime" / "instances.json"
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(path))
    return path


@pytest.fixture
def no_image_build(monkeypatch):
    monkeypatch.setattr(dr, "docker_image_exists", lambda *a, **k: True)


def _target(tmp_path: Path, service: str = "conport") -> launcher.LaunchTarget:
    return launcher.build_target(_git_repo(tmp_path), service, catalog=CATALOG)


def _write_running_record(target: launcher.LaunchTarget, ports: Dict[str, int]) -> None:
    ident = target.identity
    record = build_instance_record(
        instance_id=f"test-{ident.worktree_hash}-{target.service}",
        project_id=ident.project_id or "",
        workspace_id=ident.workspace_id or "",
        project_root=ident.project_root or "",
        worktree_root=ident.worktree_root or "",
        worktree_hash=ident.worktree_hash or "",
        project_hash=ident.project_hash or "",
        service=target.service,
        scope="worktree",
        status="running",
        ports=dict(ports),
        urls={},
        container_names=[f"c-{target.service}"],
        compose_project_name=target.compose_project,
        labels={},
    )
    locked_reload_and_save(
        RuntimeRegistry, launcher._registry_file(target), lambda reg: reg.upsert_instance(record)
    )


def _started(service: str, ports: Dict[str, int], code: int = 0) -> SimpleNamespace:
    return SimpleNamespace(
        exit_code=code,
        blocking_findings=[],
        services=[{"service": service, "action": "started", "ports": dict(ports), "findings": []}],
    )


class FakeLifecycle:
    def __init__(self, result: Any = None, on_call=None) -> None:
        self.calls: List[Dict[str, Any]] = []
        self.result = result
        self.on_call = on_call

    def __call__(self, operation: str, **kwargs: Any) -> Any:
        self.calls.append({"operation": operation, **kwargs})
        if self.on_call is not None:
            return self.on_call(operation, **kwargs)
        return self.result


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: List[float] = []

    def clock(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def _sequence_probe(*answers: bool):
    remaining = list(answers)

    def probe(_backend: BackendSpec) -> bool:
        return remaining.pop(0) if remaining else answers[-1]

    return probe


class DockerSpy:
    """Wrap subprocess.Popen; record every `docker ...` argv, run the rest."""

    def __init__(self, real) -> None:
        self.real = real
        self.calls: List[List[str]] = []

    def __call__(self, args, *a, **kw):
        argv = [str(x) for x in (args if isinstance(args, (list, tuple)) else [args])]
        if argv and Path(argv[0]).name == "docker":
            self.calls.append(argv)
            raise AssertionError(f"unexpected docker call: {argv}")
        return self.real(args, *a, **kw)


@pytest.fixture
def docker_spy(monkeypatch) -> DockerSpy:
    spy = DockerSpy(subprocess.Popen)
    monkeypatch.setattr(subprocess, "Popen", spy)
    recorded: List[str] = []

    def no_inspect(*_a, **_k):
        recorded.append("inspect")
        raise AssertionError("unexpected docker inspect")

    monkeypatch.setattr(di, "inspect_running_containers", no_inspect)
    monkeypatch.setattr(launcher, "inspect_running_containers", no_inspect)
    spy.inspects = recorded  # type: ignore[attr-defined]
    return spy


# --- root resolution -------------------------------------------------------


def test_resolve_launch_root_from_subdirectory(tmp_path: Path):
    repo = _git_repo(tmp_path)
    sub = repo / "pkg" / "deep"
    sub.mkdir(parents=True)
    assert launcher.resolve_launch_root(None, cwd=sub, service="conport") == repo
    assert launcher.resolve_launch_root(sub, cwd=tmp_path, service="conport") == repo


def test_launch_refuses_outside_git_without_docker(
    tmp_path: Path, monkeypatch, capsys, docker_spy, registry
):
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.chdir(plain)
    code = launcher.launch("conport", env={}, registry_path=registry)
    err = capsys.readouterr().err
    assert code == 3
    assert err.startswith("LAUNCH_ROOT_NOT_GIT: ")
    assert docker_spy.calls == []
    assert docker_spy.inspects == []  # type: ignore[attr-defined]


def test_launch_refuses_unmanaged_mcp_json(
    tmp_path: Path, monkeypatch, capsys, docker_spy, registry
):
    repo = _git_repo(
        tmp_path, servers={"conport": {"type": "sse", "url": "http://localhost:3005/sse"}}
    )
    monkeypatch.chdir(repo)
    code = launcher.launch("conport", env={}, registry_path=registry)
    err = capsys.readouterr().err
    assert code == 3
    assert err.startswith("LAUNCH_MCP_JSON_NOT_MANAGED: ")
    assert docker_spy.calls == []
    assert docker_spy.inspects == []  # type: ignore[attr-defined]


# --- ensure_backend --------------------------------------------------------


def test_ensure_backend_warm_path_skips_lifecycle(tmp_path: Path, registry):
    target = _target(tmp_path)
    _write_running_record(target, CONPORT_PORTS)
    lifecycle = FakeLifecycle()
    backend = launcher.ensure_backend(
        target, wait_s=5, lifecycle=lifecycle, probe=lambda b: True
    )
    assert backend == BackendSpec("http://localhost:3105/sse", "sse", "conport")
    assert lifecycle.calls == []


def test_ensure_backend_cold_path_starts_then_waits(tmp_path: Path, registry, no_image_build):
    target = _target(tmp_path)
    lifecycle = FakeLifecycle(_started("conport", CONPORT_PORTS))
    clock = FakeClock()
    backend = launcher.ensure_backend(
        target,
        wait_s=5,
        lifecycle=lifecycle,
        probe=_sequence_probe(False, False, True),
        clock=clock.clock,
        sleep=clock.sleep,
    )
    assert backend == BackendSpec("http://localhost:3105/sse", "sse", "conport")
    assert len(lifecycle.calls) == 1
    call = lifecycle.calls[0]
    assert call["operation"] == "start"
    assert call["repo"] == target.root
    assert call["services"] == ["conport"]
    assert call["trust_env"] is False
    assert clock.sleeps == [0.5, 0.5]


def test_ensure_backend_wait_exceeded(tmp_path: Path, registry, no_image_build):
    target = _target(tmp_path)
    clock = FakeClock()
    with pytest.raises(LaunchError) as info:
        launcher.ensure_backend(
            target,
            wait_s=1.0,
            lifecycle=FakeLifecycle(_started("conport", CONPORT_PORTS)),
            probe=lambda b: False,
            clock=clock.clock,
            sleep=clock.sleep,
        )
    assert info.value.code == "LAUNCH_WAIT_EXCEEDED"
    assert info.value.remedy == "run /mcp reconnect all"


def test_ensure_backend_image_missing_spawns_build_and_exits(
    tmp_path: Path, registry, monkeypatch
):
    target = _target(tmp_path)
    monkeypatch.setattr(dr, "docker_image_exists", lambda *a, **k: False)
    spawned: List[Dict[str, Any]] = []

    def fake_popen(cmd, **kwargs):
        spawned.append({"cmd": cmd, "log": kwargs["stdout"].name, **kwargs})
        return SimpleNamespace(pid=4242)

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    lifecycle = FakeLifecycle(_started("conport", CONPORT_PORTS))
    with pytest.raises(LaunchError) as info:
        launcher.ensure_backend(target, wait_s=5, lifecycle=lifecycle, probe=lambda b: False)
    assert info.value.code == "LAUNCH_IMAGE_BUILDING"
    assert lifecycle.calls == []
    assert len(spawned) == 1
    expected = dr.compose_build_command(
        product=dr.product_root(),
        override_path=target.runtime_dir / "compose.override.yml",
        env_file=target.runtime_dir / "mcp.env",
        project_name=target.compose_project,
        services=["conport"],
    )
    assert spawned[0]["cmd"] == expected
    assert spawned[0]["start_new_session"] is True
    assert spawned[0]["log"] == str(target.runtime_dir / "build.log")


def test_two_launchers_one_start(tmp_path: Path, registry, no_image_build):
    target = _target(tmp_path)
    started = threading.Event()
    counter_lock = threading.Lock()
    counter = {"n": 0}

    def start(operation: str, **_kwargs: Any) -> Any:
        with counter_lock:
            counter["n"] += 1
        threading.Event().wait(0.2)  # a start takes a while; the other launcher queues
        _write_running_record(target, CONPORT_PORTS)
        started.set()
        return _started("conport", CONPORT_PORTS)

    results: List[Any] = []

    def run() -> None:
        results.append(
            launcher.ensure_backend(
                target,
                wait_s=5,
                lifecycle=FakeLifecycle(on_call=start),
                probe=lambda b: started.is_set(),
            )
        )

    threads = [threading.Thread(target=run) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert counter["n"] == 1
    assert len(results) == 2


# --- ensure_orchestrator ---------------------------------------------------


def _docker_with(*containers: di.DockerContainerInfo):
    return lambda: di.DockerInspectResult(available=True, containers=list(containers))


def _to_container(labels: Dict[str, str]) -> di.DockerContainerInfo:
    return di.DockerContainerInfo(
        id="abc123def456",
        name="task-orchestrator-owner",
        ports=["127.0.0.1:7890->7890/tcp"],
        labels=labels,
        published_ports=[7890],
    )


def test_ensure_orchestrator_ok_forwards(tmp_path: Path, registry):
    target = _target(tmp_path, "task-orchestrator")
    labels = {
        "dopemux.managed": "true",
        "dopemux.service": "task-orchestrator",
        "dopemux.project_id": target.identity.project_id,
        "dopemux.project_root": target.identity.project_root,
    }
    lifecycle = FakeLifecycle()
    backend = launcher.ensure_orchestrator(
        target, docker=_docker_with(_to_container(labels)), lifecycle=lifecycle
    )
    assert backend == TO_BACKEND
    assert lifecycle.calls == []


def test_ensure_orchestrator_wrong_project_refuses(tmp_path: Path, registry):
    target = _target(tmp_path, "task-orchestrator")
    foreign = str(tmp_path / "elsewhere" / "other-project")
    labels = {
        "dopemux.managed": "true",
        "dopemux.service": "task-orchestrator",
        "dopemux.project_id": "other-project",
        "dopemux.project_root": foreign,
    }
    lifecycle = FakeLifecycle()
    with pytest.raises(LaunchError) as info:
        launcher.ensure_orchestrator(
            target, docker=_docker_with(_to_container(labels)), lifecycle=lifecycle
        )
    assert info.value.code == "TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT"
    assert info.value.remedy == f"{foreign}; run dopemux mcp switch-project here to take it over"
    assert lifecycle.calls == []


def test_ensure_orchestrator_unlabelled_refuses(tmp_path: Path, registry):
    target = _target(tmp_path, "task-orchestrator")
    lifecycle = FakeLifecycle()
    with pytest.raises(LaunchError) as container_case:
        launcher.ensure_orchestrator(
            target, docker=_docker_with(_to_container({})), lifecycle=lifecycle
        )
    with pytest.raises(LaunchError) as process_case:  # a non-container listener on 7890
        launcher.ensure_orchestrator(
            target, docker=_docker_with(), lifecycle=lifecycle, port_is_free=lambda p: False
        )
    for info in (container_case, process_case):
        assert info.value.code == "TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER"
        assert info.value.remedy == "run dopemux mcp doctor"
    assert lifecycle.calls == []


def test_ensure_orchestrator_free_starts(tmp_path: Path, registry):
    target = _target(tmp_path, "task-orchestrator")
    lifecycle = FakeLifecycle(_started("task-orchestrator", {"TASK_ORCHESTRATOR_HTTP_PORT": 7890}))
    backend = launcher.ensure_orchestrator(
        target,
        docker=_docker_with(),
        lifecycle=lifecycle,
        probe=lambda b: True,
        port_is_free=lambda p: True,
    )
    assert backend == TO_BACKEND
    assert len(lifecycle.calls) == 1
    assert lifecycle.calls[0]["services"] == ["task-orchestrator"]
    assert lifecycle.calls[0]["trust_env"] is False


# --- attach / detach -------------------------------------------------------


def test_attach_record_written_and_removed(tmp_path: Path, monkeypatch, registry):
    record = launcher.attach(tmp_path / "rt")
    assert record == tmp_path / "rt" / "attached" / str(os.getpid())
    assert record.is_file()
    launcher.detach(record)
    assert not record.exists()
    launcher.detach(record)  # idempotent

    # Through launch: present while proxying, removed afterwards, also on refusal.
    repo = _git_repo(tmp_path / "x")
    monkeypatch.chdir(repo)
    monkeypatch.setattr(launcher, "_load_catalog", lambda: CATALOG)
    seen: List[bool] = []
    attached_dir = launcher.build_target(repo, "conport", catalog=CATALOG).runtime_dir / "attached"

    def fake_proxy(backend: BackendSpec) -> int:
        seen.append((attached_dir / str(os.getpid())).is_file())
        return 0

    monkeypatch.setattr(launcher, "run_proxy", fake_proxy)
    warm = BackendSpec("u", "sse", "conport")
    monkeypatch.setattr(launcher, "ensure_backend", lambda target, **kw: warm)
    assert launcher.launch("conport", env={}) == 0
    assert seen == [True]
    assert list(attached_dir.iterdir()) == []

    def refuse(target, **kw):
        raise LaunchError("LAUNCH_WAIT_EXCEEDED", "run /mcp reconnect all")

    monkeypatch.setattr(launcher, "ensure_backend", refuse)
    assert launcher.launch("conport", env={}) == 3
    assert list(attached_dir.iterdir()) == []
