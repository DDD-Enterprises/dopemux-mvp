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
CONPORT_PORTS = {
    "CONPORT_MCP_PORT": 3105,
    "CONPORT_HTTP_PORT": 3104,
    "CONPORT_INFO_PORT": 4104,
}
TO_BACKEND = BackendSpec("http://127.0.0.1:7890/mcp", "http", "task-orchestrator")


def _managed_entry(name: str) -> Dict[str, Any]:
    return {
        "type": "stdio",
        "command": "${DOPEMUX_BIN:-dopemux}",
        "args": ["mcp", "launch", name],
    }


def _git_repo(tmp_path: Path, servers: Dict[str, Any] | None = None) -> Path:
    repo = tmp_path / "proj"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    if servers is None:
        servers = {name: _managed_entry(name) for name in CATALOG["servers"]}
    (repo / ".mcp.json").write_text(
        json.dumps({"mcpServers": servers}), encoding="utf-8"
    )
    return repo.resolve()


@pytest.fixture(autouse=True)
def _no_real_reap(monkeypatch):
    """`launch` reaps by default; keep these tests away from docker and real registries."""
    monkeypatch.setattr(launcher, "maybe_reap", lambda **kw: None)


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
        RuntimeRegistry,
        launcher._registry_file(target),
        lambda reg: reg.upsert_instance(record),
    )


def _started(service: str, ports: Dict[str, int], code: int = 0) -> SimpleNamespace:
    return SimpleNamespace(
        exit_code=code,
        blocking_findings=[],
        services=[
            {
                "service": service,
                "action": "started",
                "ports": dict(ports),
                "findings": [],
            }
        ],
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
        tmp_path,
        servers={"conport": {"type": "sse", "url": "http://localhost:3005/sse"}},
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


def test_ensure_backend_cold_path_starts_then_waits(
    tmp_path: Path, registry, no_image_build
):
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
        launcher.ensure_backend(
            target, wait_s=5, lifecycle=lifecycle, probe=lambda b: False
        )
    assert info.value.code == "LAUNCH_IMAGE_BUILDING"
    assert lifecycle.calls == []
    assert len(spawned) == 1
    expected = dr.compose_build_command(
        product=dr.product_root(),
        override_path=target.runtime_dir / "compose.build.yml",
        env_file=target.runtime_dir / "mcp.env",
        project_name=target.compose_project,
        services=["conport"],
    )
    assert spawned[0]["cmd"] == expected
    assert spawned[0]["start_new_session"] is True
    assert spawned[0]["log"] == str(target.runtime_dir / "build.log")
    # the build tags the one shared image
    image = dr.compose_image_name("conport", product=dr.product_root())
    assert f"image: {image}" in (target.runtime_dir / "compose.build.yml").read_text()
    assert (target.runtime_dir / "build.pid").read_text().strip() == "4242"


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
    assert (
        info.value.remedy
        == f"{foreign}; run dopemux mcp switch-project here to take it over"
    )
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
            target,
            docker=_docker_with(),
            lifecycle=lifecycle,
            port_is_free=lambda p: False,
        )
    for info in (container_case, process_case):
        assert info.value.code == "TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER"
        assert info.value.remedy == "run dopemux mcp doctor"
    assert lifecycle.calls == []


def test_ensure_orchestrator_free_starts(tmp_path: Path, registry):
    target = _target(tmp_path, "task-orchestrator")
    lifecycle = FakeLifecycle(
        _started("task-orchestrator", {"TASK_ORCHESTRATOR_HTTP_PORT": 7890})
    )
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
    monkeypatch.setattr(launcher, "_load_catalog", lambda *a, **k: CATALOG)
    seen: List[bool] = []
    attached_dir = (
        launcher.build_target(repo, "conport", catalog=CATALOG).runtime_dir / "attached"
    )

    def fake_proxy(backend: BackendSpec, **kw: Any) -> int:
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


def test_launch_reaps_after_attach_and_before_ensure_backend(
    tmp_path: Path, monkeypatch, registry
):
    repo = _git_repo(tmp_path / "x")
    monkeypatch.chdir(repo)
    monkeypatch.setattr(launcher, "_load_catalog", lambda *a, **k: CATALOG)
    attached_dir = (
        launcher.build_target(repo, "conport", catalog=CATALOG).runtime_dir / "attached"
    )
    order: List[str] = []
    limits: List[dict] = []

    def fake_reap(**kwargs) -> None:
        order.append(f"reap attached={(attached_dir / str(os.getpid())).is_file()}")
        limits.append(kwargs)

    def fake_ensure(target, **kw):
        order.append("ensure_backend")
        return BackendSpec("u", "sse", "conport")

    monkeypatch.setattr(launcher, "maybe_reap", fake_reap)
    monkeypatch.setattr(launcher, "ensure_backend", fake_ensure)
    monkeypatch.setattr(launcher, "run_proxy", lambda backend, **kw: 0)
    assert launcher.launch("conport", env={}) == 0
    assert order == ["reap attached=True", "ensure_backend"]
    # launcher-style bounds: it runs inside Claude's connect budget
    assert limits == [
        {
            "max_candidates": 1,
            "stop_time_s": 3,
            "cmd_timeout_s": 10.0,
            "deadline_s": 8.0,
        }
    ]


def test_launch_attaches_under_the_instance_lock_and_releases_it_before_reaping(
    tmp_path: Path, monkeypatch, registry
):
    import contextlib

    repo = _git_repo(tmp_path / "x")
    monkeypatch.chdir(repo)
    monkeypatch.setattr(launcher, "_load_catalog", lambda *a, **k: CATALOG)
    events: List[str] = []
    held = {"now": False}

    @contextlib.contextmanager
    def spy_lock(runtime_dir):
        events.append("lock")
        held["now"] = True
        try:
            yield
        finally:
            held["now"] = False
            events.append("unlock")

    real_attach = launcher.attach

    def spy_attach(runtime_dir):
        events.append(f"attach(held={held['now']})")
        return real_attach(runtime_dir)

    monkeypatch.setattr(launcher, "instance_lock", spy_lock)
    monkeypatch.setattr(launcher, "attach", spy_attach)
    monkeypatch.setattr(
        launcher, "maybe_reap", lambda **kw: events.append(f"reap(held={held['now']})")
    )
    monkeypatch.setattr(
        launcher,
        "ensure_backend",
        lambda target, **kw: events.append("ensure")
        or BackendSpec("u", "sse", "conport"),
    )
    monkeypatch.setattr(launcher, "run_proxy", lambda backend, **kw: 0)
    assert launcher.launch("conport", env={}) == 0
    assert events == [
        "lock",
        "attach(held=True)",
        "unlock",
        "reap(held=False)",
        "ensure",
    ]


def test_reap_failure_never_refuses_a_launch(
    tmp_path: Path, monkeypatch, registry, capsys
):
    repo = _git_repo(tmp_path / "x")
    monkeypatch.chdir(repo)
    monkeypatch.setattr(launcher, "_load_catalog", lambda *a, **k: CATALOG)

    def boom(**kwargs) -> None:
        raise RuntimeError("docker exploded")

    monkeypatch.setattr(launcher, "maybe_reap", boom)
    monkeypatch.setattr(
        launcher,
        "ensure_backend",
        lambda target, **kw: BackendSpec("u", "sse", "conport"),
    )
    monkeypatch.setattr(launcher, "run_proxy", lambda backend, **kw: 0)
    assert launcher.launch("conport", env={}) == 0
    assert "reap skipped: docker exploded" in capsys.readouterr().err


def test_launch_env_default_is_resolved_at_call_time(tmp_path: Path, monkeypatch):
    import inspect

    # A default of os.environ would render every variable (secrets included) in
    # help(), pydoc and inspect.signature.
    assert inspect.signature(launcher.launch).parameters["env"].default is None

    repo = _git_repo(tmp_path)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(launcher, "_load_catalog", lambda *a, **k: CATALOG)
    monkeypatch.setenv(launcher.WAIT_ENV, "7")
    seen: Dict[str, Any] = {}

    def fake_ensure(target, **kw):
        seen.update(kw)
        return BackendSpec("u", "sse", "conport")

    monkeypatch.setattr(launcher, "ensure_backend", fake_ensure)
    monkeypatch.setattr(launcher, "run_proxy", lambda backend, **kw: 0)
    assert launcher.launch("conport") == 0
    assert seen["wait_s"] == 7.0
    assert seen["env"][launcher.WAIT_ENV] == "7"


# --- reconnect guard (final review C1) --------------------------------------------


def _sidecar_container(target: launcher.LaunchTarget, port: int, **overrides: str):
    labels = {
        "dopemux.managed": "true",
        "dopemux.project_id": target.identity.project_id or "",
        "dopemux.worktree_hash": target.identity.worktree_hash or "",
        "dopemux.service": target.service,
        "dopemux.scope": "worktree",
    }
    labels.update(overrides)
    return di.DockerContainerInfo(
        id="cafe0001", name="sidecar-now-on-port", labels=labels, published_ports=[port]
    )


def test_orchestrator_reconnect_guard_reproves_the_owner(tmp_path: Path, registry):
    from dopemux.mcp.stdio_proxy import ProxyRefused

    target = _target(tmp_path, "task-orchestrator")
    ours = {
        "dopemux.managed": "true",
        "dopemux.service": "task-orchestrator",
        "dopemux.project_id": target.identity.project_id,
        "dopemux.project_root": target.identity.project_root,
    }
    foreign = str(tmp_path / "elsewhere" / "project-b")
    theirs = {
        **ours,
        "dopemux.project_id": "project-b",
        "dopemux.project_root": foreign,
    }

    def guard(docker, free=True):
        return launcher.reconnect_guard(
            target, TO_BACKEND, docker=docker, port_is_free=lambda p: free
        )

    guard(_docker_with(_to_container(ours)))()  # still ours: passes
    guard(_docker_with())()  # nothing on :7890 yet: passes, the connect retries
    with pytest.raises(ProxyRefused) as wrong:
        guard(_docker_with(_to_container(theirs)))()
    assert wrong.value.code == "TASK_ORCHESTRATOR_START_BLOCKED_WRONG_PROJECT"
    assert wrong.value.remedy.startswith(foreign)
    with pytest.raises(ProxyRefused) as unknown:
        guard(_docker_with(), free=False)()  # a non-container listener
    assert unknown.value.code == "TASK_ORCHESTRATOR_START_BLOCKED_UNKNOWN_OWNER"


@pytest.mark.parametrize(
    "overrides",
    [
        {"dopemux.worktree_hash": "ffff0000"},
        {"dopemux.project_id": "someone-else"},
        {"dopemux.managed": "false"},
    ],
)
def test_sidecar_reconnect_guard_refuses_another_owner(
    tmp_path: Path, registry, overrides
):
    from dopemux.mcp.stdio_proxy import ProxyRefused

    target = _target(tmp_path, "conport")
    backend = BackendSpec("http://localhost:3105/sse", "sse", "conport")
    ok = launcher.reconnect_guard(
        target, backend, docker=_docker_with(_sidecar_container(target, 3105))
    )
    ok()
    bad = launcher.reconnect_guard(
        target,
        backend,
        docker=_docker_with(_sidecar_container(target, 3105, **overrides)),
    )
    with pytest.raises(ProxyRefused) as info:
        bad()
    assert info.value.code == "LAUNCH_BACKEND_OWNER_CHANGED"


def test_sidecar_reconnect_guard_free_port_passes_and_foreign_listener_refuses(
    tmp_path: Path, registry
):
    from dopemux.mcp.stdio_proxy import ProxyRefused

    target = _target(tmp_path, "dope-memory")
    backend = BackendSpec("http://localhost:3120/mcp", "http", "dope-memory")
    launcher.reconnect_guard(
        target, backend, docker=_docker_with(), port_is_free=lambda p: True
    )()
    with pytest.raises(ProxyRefused) as info:
        launcher.reconnect_guard(
            target, backend, docker=_docker_with(), port_is_free=lambda p: False
        )()
    assert info.value.code == "LAUNCH_BACKEND_OWNER_CHANGED"


def test_launch_hands_the_proxy_a_reconnect_guard(
    tmp_path: Path, monkeypatch, registry
):
    repo = _git_repo(tmp_path / "x")
    monkeypatch.chdir(repo)
    monkeypatch.setattr(launcher, "_load_catalog", lambda *a, **k: CATALOG)
    backend = BackendSpec("http://localhost:3105/sse", "sse", "conport")
    monkeypatch.setattr(launcher, "ensure_backend", lambda target, **kw: backend)
    seen: Dict[str, Any] = {}

    def fake_proxy(spec: BackendSpec, **kwargs: Any) -> int:
        seen["backend"] = spec
        seen.update(kwargs)
        return 0

    monkeypatch.setattr(launcher, "run_proxy", fake_proxy)
    assert launcher.launch("conport", env={}) == 0
    assert seen["backend"] == backend
    assert callable(seen["reconnect_guard"])


# --- M1: OSError never escapes as a traceback --------------------------------------


@pytest.mark.parametrize("where", ["attach", "instance_lock"])
def test_launch_maps_os_errors_to_a_refusal(
    tmp_path: Path, monkeypatch, registry, capsys, where
):
    repo = _git_repo(tmp_path / "x")
    monkeypatch.chdir(repo)
    monkeypatch.setattr(launcher, "_load_catalog", lambda *a, **k: CATALOG)

    def boom(*_a: Any, **_k: Any) -> Any:
        if where == "attach":
            raise OSError(28, "No space left on device", "/rt/attached/1")
        raise OSError("could not acquire a stable lock on /rt/launch.lock")

    monkeypatch.setattr(launcher, where, boom)
    assert launcher.launch("conport", env={}) == 3
    err = capsys.readouterr().err
    assert err.startswith("LAUNCH_IO_ERROR: ")
    assert "Traceback" not in err


# --- M5: --root drives the catalog lookup ----------------------------------------


def test_launch_root_selects_the_repo_local_catalog(
    tmp_path: Path, monkeypatch, registry
):
    import yaml

    other = _git_repo(tmp_path / "other")
    marker = {"version": 1, "servers": {"conport": {"marker": "from-root"}}}
    (other / "mcp_catalog.yaml").write_text(yaml.safe_dump(marker), encoding="utf-8")
    elsewhere = _git_repo(tmp_path / "cwd-repo")
    monkeypatch.chdir(elsewhere)
    monkeypatch.delenv("DOPEMUX_MCP_CATALOG", raising=False)
    seen: Dict[str, Any] = {}

    def capture(root: Path, service: str, *, catalog, registry_path=None):
        seen["root"] = root
        seen["catalog"] = catalog
        raise LaunchError("LAUNCH_SERVICE_UNKNOWN", "stop here")

    monkeypatch.setattr(launcher, "build_target", capture)
    assert launcher.launch("conport", root=other, env={}) == 3
    assert seen["root"] == other
    assert seen["catalog"]["servers"]["conport"] == {"marker": "from-root"}


# --- I2: a launcher killed by SIGTERM/SIGHUP still detaches -------------------------
# Port of the reviewer's scratch probe `detach_probe.py`: before the fix the
# signal killed the process without running `finally`, so no `last_detach`.

_SIGNAL_CHILD = r"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import anyio
from mcp import ClientSession, types
from mcp.server.lowlevel import Server
from mcp.shared.memory import create_client_server_memory_streams

from dopemux.mcp import launcher, stdio_proxy

rt = Path(sys.argv[1])
target = launcher.LaunchTarget(
    root=rt, identity=SimpleNamespace(), service="conport", spec={},
    runtime_dir=rt, compose_project="x",
)
launcher.resolve_launch_root = lambda *a, **k: rt
launcher._load_catalog = lambda *a, **k: {}
launcher.build_target = lambda *a, **k: target
launcher.maybe_reap = lambda **k: None
launcher.ensure_backend = lambda *a, **k: stdio_proxy.BackendSpec("u", "sse", "conport")


@asynccontextmanager
async def factory(**client_kwargs):
    server = Server("held")
    async with create_client_server_memory_streams() as (c, s):
        async with anyio.create_task_group() as tg:
            opts = server.create_initialization_options()
            tg.start_soon(lambda: server.run(s[0], s[1], opts))
            async with ClientSession(c[0], c[1], **client_kwargs) as session:
                (rt / "proxy-up").write_text("1")
                yield session
            tg.cancel_scope.cancel()


real_run_proxy = stdio_proxy.run_proxy
launcher.run_proxy = lambda backend, **kw: real_run_proxy(backend, session_factory=factory)
sys.exit(launcher.launch("conport", env={}))
"""


@pytest.mark.parametrize("signame,code", [("SIGTERM", 143), ("SIGHUP", 129)])
def test_launcher_killed_by_signal_still_detaches(
    tmp_path: Path, signame: str, code: int
):
    import signal
    import sys
    import time

    rt = tmp_path / "rt"
    rt.mkdir()
    env = dict(
        os.environ,
        DOPEMUX_MCP_RUNTIME_REGISTRY=str(tmp_path / "reg" / "instances.json"),
    )
    child = subprocess.Popen(
        [sys.executable, "-c", _SIGNAL_CHILD, str(rt)],
        stdin=subprocess.PIPE,  # held open: the proxy keeps serving
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        deadline = time.monotonic() + 30
        while not (rt / "proxy-up").exists():
            assert child.poll() is None, (
                child.stderr.read().decode() if child.stderr else ""
            )
            assert time.monotonic() < deadline, "child never reached the proxy"
            time.sleep(0.05)
        assert (rt / "attached" / str(child.pid)).is_file()
        child.send_signal(getattr(signal, signame))
        assert child.wait(timeout=20) == code
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
        for pipe in (child.stdin, child.stdout, child.stderr):
            if pipe is not None:
                pipe.close()
    assert (rt / "last_detach").is_file()
    assert not (rt / "attached" / str(child.pid)).exists()


# --- I4: one shared image per service; one build at a time ---------------------------


def _linked_worktree(repo: Path, where: Path) -> Path:
    git = [
        "git",
        "-C",
        str(repo),
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@example.com",
    ]
    subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "init"], check=True)
    subprocess.run([*git, "worktree", "add", "-q", str(where)], check=True)
    return where.resolve()


def test_image_name_is_shared_by_worktrees_and_projects(
    tmp_path: Path, registry, monkeypatch
):
    repo = _git_repo(tmp_path / "one")
    sibling = _linked_worktree(repo, tmp_path / "one-wt")
    (sibling / ".mcp.json").write_text(
        (repo / ".mcp.json").read_text(), encoding="utf-8"
    )
    other = _git_repo(tmp_path / "two")
    asked: List[str] = []

    def exists(image: str, **_kw: Any) -> bool:
        asked.append(image)
        return True

    monkeypatch.setattr(dr, "docker_image_exists", exists)
    targets = [
        launcher.build_target(r, "conport", catalog=CATALOG)
        for r in (repo, sibling, other)
    ]
    assert len({t.compose_project for t in targets}) == 3  # three compose projects ...
    for target in targets:
        launcher._build_image_if_missing(target)
    assert len(asked) == 3 and len(set(asked)) == 1  # ... one image
    assert asked[0] == dr.compose_image_name("conport", product=dr.product_root())


def test_second_launch_during_a_live_build_spawns_nothing(
    tmp_path: Path, registry, monkeypatch, capsys
):
    target = _target(tmp_path)
    monkeypatch.setattr(dr, "docker_image_exists", lambda *a, **k: False)
    spawned: List[Any] = []

    def fake_popen(cmd, **kwargs):
        spawned.append(cmd)
        return SimpleNamespace(pid=os.getpid())  # alive for the whole test

    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    for _ in range(2):
        with pytest.raises(LaunchError) as info:
            launcher._build_image_if_missing(target)
        assert info.value.code == "LAUNCH_IMAGE_BUILDING"
    assert len(spawned) == 1
    err = capsys.readouterr().err
    assert "still building" in err and str(target.runtime_dir / "build.log") in err


def test_a_stale_build_pid_file_is_replaced(tmp_path: Path, registry, monkeypatch):
    target = _target(tmp_path)
    target.runtime_dir.mkdir(parents=True, exist_ok=True)
    dead = subprocess.Popen(["true"])
    dead.wait()
    (target.runtime_dir / "build.pid").write_text(f"{dead.pid}\n", encoding="utf-8")
    monkeypatch.setattr(dr, "docker_image_exists", lambda *a, **k: False)
    spawned: List[Any] = []
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda cmd, **kw: spawned.append(cmd) or SimpleNamespace(pid=4243),
    )
    with pytest.raises(LaunchError):
        launcher._build_image_if_missing(target)
    assert len(spawned) == 1
    assert (target.runtime_dir / "build.pid").read_text().strip() == "4243"


# --- M3: a record without the port never resolves to the template default ---------


def test_find_backend_ignores_a_running_record_without_its_port(
    tmp_path: Path, registry
):
    target = _target(tmp_path)
    _write_running_record(target, {"CONPORT_HTTP_PORT": 3104})  # no CONPORT_MCP_PORT
    assert launcher.find_backend(target) is None  # not http://localhost:3005/sse


def test_start_result_without_the_port_refuses(
    tmp_path: Path, registry, no_image_build
):
    target = _target(tmp_path)
    lifecycle = FakeLifecycle(_started("conport", {"CONPORT_HTTP_PORT": 3104}))
    with pytest.raises(LaunchError) as info:
        launcher.ensure_backend(
            target, wait_s=5, lifecycle=lifecycle, probe=lambda b: True
        )
    assert info.value.code == "LAUNCH_BACKEND_PORT_UNKNOWN"
    assert "CONPORT_MCP_PORT" in info.value.remedy


# --- P1: SDK INFO lines (httpx/mcp) stay out of a launcher's stderr ------------------


def test_launch_quiets_sdk_info_logs_while_probing(
    tmp_path: Path, monkeypatch, registry, caplog
):
    import logging

    repo = _git_repo(tmp_path / "x")
    monkeypatch.chdir(repo)
    monkeypatch.setattr(launcher, "_load_catalog", lambda *a, **k: CATALOG)

    def probing_ensure(target, **kw):  # what probe_backend's SDK session logs
        logging.getLogger("httpx").info("HTTP Request: POST http://localhost:3105/mcp")
        logging.getLogger("mcp.client.streamable_http").info("Received session ID: x")
        logging.getLogger("httpx").warning("a real problem")
        return BackendSpec("http://localhost:3105/sse", "sse", "conport")

    monkeypatch.setattr(launcher, "ensure_backend", probing_ensure)
    monkeypatch.setattr(launcher, "run_proxy", lambda backend, **kw: 0)
    before = {n: logging.getLogger(n).level for n in ("httpx", "httpcore", "mcp")}
    with caplog.at_level(logging.INFO):
        assert launcher.launch("conport", env={}) == 0
    messages = [r.getMessage() for r in caplog.records]
    assert "a real problem" in messages
    assert not [m for m in messages if "HTTP Request" in m or "session ID" in m]
    assert {
        n: logging.getLogger(n).level for n in before
    } == before  # restored afterwards
