"""Unit tests for reap-only cleanup (Task 5, D8/P-09).

Docker, clocks and registries are fakes under tmp_path; no real docker call is made
and nothing under ``~/.dopemux`` is read or written.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest
from click.testing import CliRunner

from dopemux.mcp import docker_inspect as di
from dopemux.mcp import docker_runtime as dr
from dopemux.mcp import reap
from dopemux.mcp.docker_inspect import DockerContainerInfo, DockerInspectResult
from dopemux.mcp.port_leases import PortLeaseRegistry
from dopemux.mcp.runtime_registry import RuntimeRegistry, build_instance_record

PROJECT_ID = "proj-1234abcd"
HASH = "abcd1234"
NOW = 1_000_000.0
IDLE = 1200.0


@pytest.fixture(autouse=True)
def _isolated(tmp_path: Path, monkeypatch):
    """Registries, leases, lock files and the kill-switch dir all live in tmp_path."""
    monkeypatch.setenv(
        "DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "runtime" / "instances.json")
    )
    monkeypatch.setenv(
        "DOPEMUX_MCP_PORT_LEASE_REGISTRY",
        str(tmp_path / "runtime" / "port-leases.json"),
    )
    monkeypatch.delenv("DOPEMUX_MCP_REAP", raising=False)


@pytest.fixture
def runtime(tmp_path: Path) -> Path:
    path = tmp_path / "runtime"
    path.mkdir()
    return path


def _container(
    cid: str,
    *,
    project_id: str = PROJECT_ID,
    worktree_hash: str = HASH,
    scope: Optional[str] = "worktree",
    managed: str = "true",
    service: str = "conport",
) -> DockerContainerInfo:
    labels: Dict[str, str] = {
        "dopemux.managed": managed,
        "dopemux.project_id": project_id,
        "dopemux.worktree_hash": worktree_hash,
        "dopemux.service": service,
    }
    if scope is not None:
        labels["dopemux.scope"] = scope
    return DockerContainerInfo(id=cid, name=f"c-{cid}", labels=labels)


def _record(
    worktree_root: Path,
    *,
    project_id: str = PROJECT_ID,
    worktree_hash: str = HASH,
    service: str = "conport",
    scope: str = "worktree",
) -> Dict[str, Any]:
    return build_instance_record(
        instance_id=f"proj-{worktree_hash}-{service}",
        project_id=project_id,
        workspace_id=str(worktree_root),
        project_root=str(worktree_root),
        worktree_root=str(worktree_root),
        worktree_hash=worktree_hash,
        project_hash="p" * 8,
        service=service,
        scope=scope,
        status="running",
        ports={"http": 3100},
        urls={},
        container_names=[f"c-{service}"],
        compose_project_name="dopemux-proj",
        labels={},
    )


def _registry(runtime: Path, worktree_root: Path, **kw: Any) -> RuntimeRegistry:
    reg = RuntimeRegistry.load(runtime / "instances.json", create_missing=True)
    reg.upsert_instance(_record(worktree_root, **kw))
    reg.save()
    return RuntimeRegistry.load(runtime / "instances.json")


def _rt_dir(runtime: Path, worktree_hash: str = HASH) -> Path:
    # project_slug(Path(project_root).name) for a worktree dir named "proj" is "proj"
    return runtime / f"proj-{worktree_hash}"


def _detached(rt: Path, *, ago: float) -> None:
    rt.mkdir(parents=True, exist_ok=True)
    marker = rt / "last_detach"
    marker.write_text("x\n", encoding="utf-8")
    os.utime(marker, (NOW - ago, NOW - ago))


def _plan(reg: RuntimeRegistry, containers: List[DockerContainerInfo], **kw: Any):
    return reap.plan_reap(
        registry=reg, containers=containers, now=NOW, idle_s=IDLE, **kw
    )


# --- attach / detach / live_attachments ------------------------------------------


def test_attach_writes_iso_timestamp_and_detach_records_last_detach(tmp_path: Path):
    rt = tmp_path / "rt"
    record = reap.attach(rt)
    assert record == rt / "attached" / str(os.getpid())
    text = record.read_text(encoding="utf-8").strip()
    assert text.endswith("Z") and "T" in text  # ISO-8601 UTC
    assert reap.live_attachments(rt) == 1
    reap.detach(record)
    assert not record.exists()
    assert (rt / "last_detach").is_file()
    reap.detach(record)  # idempotent
    assert reap.live_attachments(rt) == 0


def test_detach_does_not_recreate_a_removed_runtime_dir(tmp_path: Path):
    rt = tmp_path / "gone"
    record = reap.attach(rt)
    import shutil

    shutil.rmtree(rt)
    reap.detach(record)
    assert not rt.exists()


def test_live_attachments_prunes_dead_and_tolerates_plain_pid_content(tmp_path: Path):
    rt = tmp_path / "rt"
    attached = rt / "attached"
    attached.mkdir(parents=True)
    dead = subprocess.Popen(["true"])
    dead.wait()
    (attached / str(dead.pid)).write_text(
        f"{dead.pid}\n", encoding="utf-8"
    )  # Task 3c format
    (attached / str(os.getpid())).write_text(f"{os.getpid()}\n", encoding="utf-8")
    (attached / "not-a-pid").write_text("junk", encoding="utf-8")
    assert reap.live_attachments(rt, prune=False) == 1
    assert (attached / str(dead.pid)).exists()  # read-only count leaves it alone
    assert reap.live_attachments(rt) == 1
    assert not (attached / str(dead.pid)).exists()
    assert (attached / str(os.getpid())).exists()


# --- plan_reap -------------------------------------------------------------------


def test_plan_reap_skips_project_and_singleton_scope(tmp_path: Path, runtime: Path):
    missing = tmp_path / "removed" / "proj"
    reg = _registry(runtime, missing)
    containers = [
        _container("p1", scope="project"),
        _container("s1", scope="singleton"),
        _container("n1", scope=None),  # absent scope is unknown, never touched
        _container("u1", managed="false"),
        _container("x1", scope="worktree", project_id=""),  # missing a join label
    ]
    assert _plan(reg, containers) == []


def test_plan_reap_ignores_containers_of_a_pair_without_registry_entry(
    tmp_path: Path, runtime: Path
):
    reg = _registry(runtime, tmp_path / "removed" / "proj")
    got = _plan(reg, [_container("a1", worktree_hash="ffff0000")])
    assert all("a1" not in c.container_ids for c in got)  # never touched


def test_plan_reap_candidate_when_worktree_missing(tmp_path: Path, runtime: Path):
    missing = tmp_path / "removed" / "proj"
    reg = _registry(runtime, missing)
    got = _plan(reg, [_container("a1"), _container("a2", service="dope-memory")])
    assert len(got) == 1
    cand = got[0]
    assert (cand.project_id, cand.worktree_hash) == (PROJECT_ID, HASH)
    assert cand.worktree_root == str(missing)
    assert cand.runtime_dir == _rt_dir(runtime)
    assert sorted(cand.container_ids) == ["a1", "a2"]
    assert cand.reason == "worktree_missing"
    assert cand.services == ["conport", "dope-memory"]


def test_plan_reap_candidate_when_idle_and_detached(tmp_path: Path, runtime: Path):
    live = tmp_path / "wt" / "proj"
    live.mkdir(parents=True)
    reg = _registry(runtime, live)
    _detached(_rt_dir(runtime), ago=IDLE + 1)
    got = _plan(reg, [_container("a1")])
    assert [c.reason for c in got] == ["idle"]


def test_plan_reap_not_candidate_when_recently_detached(tmp_path: Path, runtime: Path):
    live = tmp_path / "wt" / "proj"
    live.mkdir(parents=True)
    reg = _registry(runtime, live)
    _detached(_rt_dir(runtime), ago=IDLE - 60)
    assert _plan(reg, [_container("a1")]) == []


def test_plan_reap_idle_without_last_detach_is_never_a_candidate(
    tmp_path: Path, runtime: Path
):
    live = tmp_path / "wt" / "proj"
    live.mkdir(parents=True)
    reg = _registry(runtime, live)
    _rt_dir(runtime).mkdir()  # runtime dir exists, nobody attached, no last_detach
    assert _plan(reg, [_container("a1")]) == []


def test_plan_reap_not_candidate_when_attached(tmp_path: Path, runtime: Path):
    missing = tmp_path / "removed" / "proj"
    reg = _registry(runtime, missing)
    attached = _rt_dir(runtime) / "attached"
    attached.mkdir(parents=True)
    (attached / str(os.getpid())).write_text("t\n", encoding="utf-8")
    assert _plan(reg, [_container("a1")]) == []


def test_plan_reap_stale_pid_counts_as_detached(tmp_path: Path, runtime: Path):
    missing = tmp_path / "removed" / "proj"
    reg = _registry(runtime, missing)
    dead = subprocess.Popen(["true"])
    dead.wait()
    attached = _rt_dir(runtime) / "attached"
    attached.mkdir(parents=True)
    (attached / str(dead.pid)).write_text(f"{dead.pid}\n", encoding="utf-8")
    got = _plan(reg, [_container("a1")])
    assert [c.reason for c in got] == ["worktree_missing"]
    assert (attached / str(dead.pid)).exists()  # planning is read-only


def test_plan_reap_with_corrupt_registry_is_empty(tmp_path: Path, runtime: Path):
    (runtime / "instances.json").write_text("{not json", encoding="utf-8")
    reg = RuntimeRegistry.load(runtime / "instances.json")
    assert reg.parse_status == "ERROR"
    assert _plan(reg, [_container("a1")]) == []


def test_plan_reap_treats_unreadable_worktree_as_present(tmp_path: Path, runtime: Path):
    reg = _registry(runtime, tmp_path / "removed" / "proj")

    def boom(path: Path) -> bool:
        raise PermissionError("denied")

    assert _plan(reg, [_container("a1")], exists=boom) == []


def test_plan_reap_refuses_unsafe_worktree_hash(tmp_path: Path, runtime: Path):
    reg = _registry(runtime, tmp_path / "removed" / "proj", worktree_hash="../escape")
    assert _plan(reg, [_container("a1", worktree_hash="../escape")]) == []


# --- apply_reap ------------------------------------------------------------------


class Recorder:
    def __init__(
        self, fail: Optional[set] = None, stderr: Optional[Dict[tuple, str]] = None
    ) -> None:
        self.calls: List[List[str]] = []
        self.kwargs: List[Dict[str, Any]] = []
        self.fail = fail or set()
        self.stderr = stderr or {}

    def __call__(self, cmd, **kwargs):
        cmd = list(cmd)
        self.calls.append(cmd)
        self.kwargs.append(kwargs)
        failed = tuple(cmd) in self.fail or tuple(cmd) in self.stderr
        return dr.RuntimeCommandResult(
            command=cmd,
            exit_code=1 if failed else 0,
            stderr=self.stderr.get(tuple(cmd), "boom") if failed else "",
        )


def _lease(
    worktree_root: Path, service: str, port: int, *, scope: str = "worktree"
) -> Dict[str, Any]:
    return {
        "lease_id": f"lease-{service}-{port}",
        "service": service,
        "port": port,
        "port_role": "http",
        "worktree_root": str(worktree_root),
        "project_id": PROJECT_ID,
        "scope": scope,
        "status": "active",
    }


def _setup_apply(tmp_path: Path, runtime: Path):
    missing = tmp_path / "removed" / "proj"
    reg = _registry(runtime, missing)
    rt = _rt_dir(runtime)
    rt.mkdir()
    (rt / "mcp.env").write_text("X=1\n", encoding="utf-8")
    leases = PortLeaseRegistry.load(runtime / "port-leases.json", create_missing=True)
    leases.upsert_lease(_lease(missing, "conport", 3100))
    leases.upsert_lease(_lease(missing, "dope-memory", 3101))
    leases.upsert_lease(_lease(missing, "task-orchestrator", 7890, scope="project"))
    leases.save()
    cands = _plan(reg, [_container("a1"), _container("a2", service="dope-memory")])
    assert len(cands) == 1
    return missing, cands


def test_apply_reap_stops_removes_releases_and_rmtree(tmp_path: Path, runtime: Path):
    missing, cands = _setup_apply(tmp_path, runtime)
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner)
    assert report.errors == []
    assert report.reaped == cands
    for cid in cands[0].container_ids:
        assert ["docker", "stop", cid] in runner.calls
        assert ["docker", "rm", cid] in runner.calls
        assert runner.calls.index(["docker", "stop", cid]) < runner.calls.index(
            ["docker", "rm", cid]
        )
    assert all("-f" not in c for c in runner.calls)
    leases = PortLeaseRegistry.load(runtime / "port-leases.json")
    status = {L["service"]: L["status"] for L in leases.leases()}
    assert status["conport"] == "released"
    assert status["dope-memory"] == "released"
    assert (
        status["task-orchestrator"] == "active"
    )  # project-scoped lease is not ours to release
    registry = RuntimeRegistry.load(runtime / "instances.json")
    assert [i["status"] for i in registry.instances()] == ["stopped"]
    assert not _rt_dir(runtime).exists()


def test_apply_reap_rechecks_attachment_under_lock(tmp_path: Path, runtime: Path):
    missing, cands = _setup_apply(tmp_path, runtime)
    reap.attach(_rt_dir(runtime))  # a launcher attaches between plan and apply
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner)
    assert report.reaped == []
    assert report.errors == []
    assert runner.calls == []
    assert _rt_dir(runtime).is_dir()
    leases = PortLeaseRegistry.load(runtime / "port-leases.json")
    assert {L["status"] for L in leases.leases()} == {"active"}


def test_apply_reap_keeps_state_when_a_container_fails_to_stop(
    tmp_path: Path, runtime: Path
):
    missing, cands = _setup_apply(tmp_path, runtime)
    runner = Recorder(fail={("docker", "stop", "a1")})
    report = reap.apply_reap(cands, runner=runner)
    assert report.reaped == []
    assert any("a1" in e for e in report.errors)
    assert [
        "docker",
        "rm",
        "a1",
    ] not in runner.calls  # never remove what failed to stop
    assert ["docker", "stop", "a2"] in runner.calls and [
        "docker",
        "rm",
        "a2",
    ] in runner.calls
    assert _rt_dir(runtime).is_dir()
    leases = PortLeaseRegistry.load(runtime / "port-leases.json")
    assert {L["status"] for L in leases.leases() if L["service"] == "conport"} == {
        "active"
    }
    registry = RuntimeRegistry.load(runtime / "instances.json")
    assert [i["status"] for i in registry.instances()] == ["running"]


def test_apply_reap_refuses_runtime_dir_outside_registry_dir(
    tmp_path: Path, runtime: Path
):
    missing, cands = _setup_apply(tmp_path, runtime)
    outside = tmp_path / "precious"
    outside.mkdir()
    bad = reap.ReapCandidate(
        project_id=PROJECT_ID,
        worktree_hash=HASH,
        worktree_root=str(missing),
        runtime_dir=outside,
        container_ids=["a1"],
        reason="worktree_missing",
    )
    runner = Recorder()
    report = reap.apply_reap([bad], runner=runner)
    assert report.reaped == []
    assert report.errors
    assert runner.calls == []
    assert outside.is_dir()


# --- maybe_reap ------------------------------------------------------------------


class FakeInspect:
    def __init__(self, containers: List[DockerContainerInfo]) -> None:
        self.containers = containers
        self.calls = 0

    def __call__(self, **kwargs: Any) -> DockerInspectResult:
        self.calls += 1
        return DockerInspectResult(available=True, containers=list(self.containers))


def test_maybe_reap_throttles(tmp_path: Path, runtime: Path):
    _setup_apply(tmp_path, runtime)
    inspect = FakeInspect([_container("a1")])
    state = tmp_path / "state" / "reap.last"
    runner = Recorder()
    clock = {"t": NOW}

    def call(throttle_s: float = 600):
        return reap.maybe_reap(
            throttle_s=throttle_s,
            state_file=state,
            now=lambda: clock["t"],
            inspector=inspect,
            runner=runner,
        )

    first = call()
    assert first is not None and len(first.reaped) == 1
    assert state.exists()
    os.utime(state, (NOW, NOW))
    clock["t"] = NOW + 599
    assert call() is None
    assert inspect.calls == 1
    clock["t"] = NOW + 601
    assert call() is not None
    assert inspect.calls == 2
    clock["t"] = NOW + 1
    assert call(throttle_s=0) is not None  # throttle_s=0 never skips


def test_maybe_reap_disabled_by_file(tmp_path: Path, runtime: Path):
    _setup_apply(tmp_path, runtime)
    (runtime / "reap.disabled").write_text("", encoding="utf-8")
    inspect = FakeInspect([_container("a1")])
    runner = Recorder()
    got = reap.maybe_reap(
        throttle_s=0,
        state_file=tmp_path / "s",
        now=lambda: NOW,
        inspector=inspect,
        runner=runner,
    )
    assert got is None
    assert inspect.calls == 0 and runner.calls == []
    assert not (tmp_path / "s").exists()
    assert _rt_dir(runtime).is_dir()


@pytest.mark.parametrize("value", ["0", "off", "false", "OFF", "False"])
def test_maybe_reap_disabled_by_env(
    tmp_path: Path, runtime: Path, monkeypatch, value: str
):
    _setup_apply(tmp_path, runtime)
    monkeypatch.setenv("DOPEMUX_MCP_REAP", value)
    inspect = FakeInspect([_container("a1")])
    runner = Recorder()
    got = reap.maybe_reap(
        throttle_s=0,
        state_file=tmp_path / "s",
        now=lambda: NOW,
        inspector=inspect,
        runner=runner,
    )
    assert got is None
    assert inspect.calls == 0 and runner.calls == []


def test_maybe_reap_skips_docker_when_registry_has_no_instances(
    tmp_path: Path, runtime: Path
):
    inspect = FakeInspect([_container("a1")])
    got = reap.maybe_reap(
        throttle_s=0,
        state_file=tmp_path / "s",
        now=lambda: NOW,
        inspector=inspect,
        runner=Recorder(),
    )
    assert got is not None and got.reaped == []
    assert inspect.calls == 0


def test_maybe_reap_docker_unavailable_reaps_nothing(tmp_path: Path, runtime: Path):
    _setup_apply(tmp_path, runtime)
    runner = Recorder()
    got = reap.maybe_reap(
        throttle_s=0,
        state_file=tmp_path / "s",
        now=lambda: NOW,
        inspector=lambda **kw: DockerInspectResult(available=False, error="no docker"),
        runner=runner,
    )
    assert got is not None and got.reaped == []
    assert runner.calls == []
    assert _rt_dir(runtime).is_dir()


# --- docker_inspect --------------------------------------------------------------


def test_inspect_all_managed_containers_lists_stopped_managed_containers():
    seen: List[List[str]] = []

    def runner(cmd, **kwargs):
        seen.append(list(cmd))
        row = {
            "ID": "abcdef0123456789",
            "Names": "c1",
            "Labels": "dopemux.managed=true,dopemux.scope=worktree",
            "Status": "Exited (0) 3 minutes ago",
        }
        return SimpleNamespace(returncode=0, stdout=json.dumps(row) + "\n", stderr="")

    result = di.inspect_all_managed_containers(runner=runner)
    assert seen == [
        [
            "docker",
            "ps",
            "-a",
            "--filter",
            "label=dopemux.managed=true",
            "--format",
            "{{json .}}",
        ]
    ]
    assert result.available and [c.id for c in result.containers] == ["abcdef012345"]


def test_inspect_all_managed_containers_reports_docker_failure():
    def runner(cmd, **kwargs):
        return SimpleNamespace(
            returncode=1, stdout="", stderr="Cannot connect to the Docker daemon"
        )

    result = di.inspect_all_managed_containers(runner=runner)
    assert not result.available and "Cannot connect" in (result.error or "")


# --- CLI -------------------------------------------------------------------------


def _cli():
    from dopemux.commands import mcp_commands

    return mcp_commands.mcp


def test_cli_dry_run_json_lists_candidates_and_changes_nothing(
    tmp_path: Path, runtime: Path, monkeypatch
):
    _setup_apply(tmp_path, runtime)
    monkeypatch.setattr(
        reap, "inspect_all_managed_containers", FakeInspect([_container("a1")])
    )
    boom = Recorder()
    monkeypatch.setattr(reap, "run_cmd", boom)
    result = CliRunner().invoke(_cli(), ["reap", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert [c["reason"] for c in payload["candidates"]] == ["worktree_missing"]
    assert payload["candidates"][0]["container_ids"] == ["a1"]
    assert boom.calls == []
    assert _rt_dir(runtime).is_dir()


def test_cli_apply_ignores_disable_file_but_warns(
    tmp_path: Path, runtime: Path, monkeypatch
):
    _setup_apply(tmp_path, runtime)
    (runtime / "reap.disabled").write_text("", encoding="utf-8")
    monkeypatch.setattr(
        reap, "inspect_all_managed_containers", FakeInspect([_container("a1")])
    )
    runner = Recorder()
    monkeypatch.setattr(reap, "run_cmd", runner)
    result = CliRunner().invoke(_cli(), ["reap", "--apply", "--json"])
    assert result.exit_code == 0, result.output
    assert "automatic reaping is disabled" in result.stderr
    payload = json.loads(result.stdout)  # the warning never pollutes the JSON channel
    assert payload["dry_run"] is False
    assert len(payload["reaped"]) == 1
    assert ["docker", "stop", "a1"] in runner.calls
    assert not _rt_dir(runtime).exists()


def test_cli_json_error_paths_print_a_json_object_and_exit_1(
    tmp_path: Path, runtime: Path, monkeypatch
):
    monkeypatch.setattr(
        reap,
        "inspect_all_managed_containers",
        lambda **kw: DockerInspectResult(available=False, error="no docker"),
    )
    result = CliRunner().invoke(_cli(), ["reap", "--json"])
    assert result.exit_code == 1
    assert "no docker" in json.loads(result.stdout)["error"]

    (runtime / "instances.json").write_text("{nope", encoding="utf-8")
    result = CliRunner().invoke(_cli(), ["reap", "--json"])
    assert result.exit_code == 1
    assert "unreadable" in json.loads(result.stdout)["error"]


def test_attach_creates_the_attached_dir_private(tmp_path: Path):
    import stat

    old = os.umask(0o022)
    try:
        record = reap.attach(tmp_path / "rt")
    finally:
        os.umask(old)
    assert stat.S_IMODE(record.parent.stat().st_mode) == 0o700


# --- fix round 1: services, state-only candidates, bounds, deadline --------------


def _two_services_registry(runtime: Path, wt: Path) -> RuntimeRegistry:
    """conport plus a worktree-scope task-orchestrator entry, as lifecycle.py writes it."""
    reg = RuntimeRegistry.load(runtime / "instances.json", create_missing=True)
    for svc in ("conport", "task-orchestrator"):
        reg.upsert_instance(_record(wt, service=svc))
    reg.save()
    return RuntimeRegistry.load(runtime / "instances.json")


def _to_container() -> DockerContainerInfo:
    # wrapper labels: scope=project and no worktree_hash
    return DockerContainerInfo(
        id="to1",
        name="t",
        labels={
            "dopemux.managed": "true",
            "dopemux.project_id": PROJECT_ID,
            "dopemux.scope": "project",
            "dopemux.service": "task-orchestrator",
        },
    )


def test_apply_reap_never_marks_the_reserved_orchestrator_stopped(
    tmp_path: Path, runtime: Path
):
    wt = tmp_path / "removed" / "proj"
    reg = _two_services_registry(runtime, wt)
    leases = PortLeaseRegistry.load(runtime / "port-leases.json", create_missing=True)
    leases.upsert_lease(_lease(wt, "conport", 3100))
    leases.upsert_lease(
        _lease(wt, "task-orchestrator", 7890)
    )  # worktree-scope lease row
    leases.save()
    cands = _plan(reg, [_container("side1"), _to_container()])
    assert [c.container_ids for c in cands] == [["side1"]]
    assert cands[0].services == ["conport"]
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner)
    assert report.errors == []
    assert [c[:2] for c in runner.calls] == [["docker", "stop"], ["docker", "rm"]]
    assert all("to1" not in c for c in runner.calls)
    status = {
        i["service"]: i["status"]
        for i in RuntimeRegistry.load(runtime / "instances.json").instances()
    }
    assert status == {"conport": "stopped", "task-orchestrator": "running"}
    lease_status = {
        L["service"]: L["status"]
        for L in PortLeaseRegistry.load(runtime / "port-leases.json").leases()
    }
    assert lease_status == {"conport": "released", "task-orchestrator": "active"}


def test_apply_reap_releases_only_leases_of_services_it_stopped(
    tmp_path: Path, runtime: Path
):
    missing, _ = _setup_apply(tmp_path, runtime)
    reg = RuntimeRegistry.load(runtime / "instances.json")
    cands = _plan(reg, [_container("a1")])  # only conport has a container left
    assert cands[0].services == ["conport"]
    reap.apply_reap(cands, runner=Recorder())
    leases = PortLeaseRegistry.load(runtime / "port-leases.json")
    assert {L["service"]: L["status"] for L in leases.leases()}[
        "dope-memory"
    ] == "active"
    # the next plan finishes the rest from state alone
    again = reap.plan_reap(
        registry=RuntimeRegistry.load(runtime / "instances.json"),
        containers=[],
        now=NOW,
        lease_registry=leases,
    )
    assert [c.state_only for c in again] == [True]


def test_state_only_candidate_finishes_a_reap_killed_after_docker_rm(
    tmp_path: Path, runtime: Path
):
    wt = tmp_path / "removed" / "proj"
    reg = _two_services_registry(runtime, wt)
    rt = _rt_dir(runtime)
    rt.mkdir()
    leases = PortLeaseRegistry.load(runtime / "port-leases.json", create_missing=True)
    leases.upsert_lease(_lease(wt, "conport", 3100))
    leases.upsert_lease(_lease(wt, "task-orchestrator", 7890))
    leases.save()
    kw = {"lease_registry": PortLeaseRegistry.load(runtime / "port-leases.json")}
    cands = _plan(reg, [], **kw)  # docker shows no container for the pair
    assert (
        len(cands) == 1
        and cands[0].state_only
        and cands[0].reason == "worktree_missing"
    )
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner)
    assert runner.calls == []  # no container is touched
    assert report.errors == [] and report.reaped == cands
    status = {
        i["service"]: i["status"]
        for i in RuntimeRegistry.load(runtime / "instances.json").instances()
    }
    assert status == {"conport": "stopped", "task-orchestrator": "running"}
    lease_status = {
        L["service"]: L["status"]
        for L in PortLeaseRegistry.load(runtime / "port-leases.json").leases()
    }
    assert lease_status == {"conport": "released", "task-orchestrator": "active"}
    assert not rt.exists()
    # idempotent: nothing left to do
    assert (
        _plan(
            RuntimeRegistry.load(runtime / "instances.json"),
            [],
            lease_registry=PortLeaseRegistry.load(runtime / "port-leases.json"),
        )
        == []
    )


def test_state_only_not_emitted_while_the_worktree_exists_or_a_launcher_is_attached(
    tmp_path: Path, runtime: Path
):
    live = tmp_path / "wt" / "proj"
    live.mkdir(parents=True)
    reg = _registry(runtime, live)
    assert _plan(reg, []) == []
    gone = _registry(runtime, tmp_path / "removed" / "proj", worktree_hash="beef0001")
    attached = _rt_dir(runtime, "beef0001") / "attached"
    attached.mkdir(parents=True)
    (attached / str(os.getpid())).write_text("t\n", encoding="utf-8")
    assert all(c.worktree_hash != "beef0001" for c in _plan(gone, []))


def test_stop_or_rm_no_such_container_counts_as_success(tmp_path: Path, runtime: Path):
    missing, cands = _setup_apply(tmp_path, runtime)
    gone = "Error response from daemon: No such container: x"
    runner = Recorder(
        stderr={("docker", "stop", "a1"): gone, ("docker", "rm", "a2"): gone}
    )
    report = reap.apply_reap(cands, runner=runner)
    assert report.errors == [] and report.reaped == cands
    assert ["docker", "rm", "a1"] in runner.calls  # still removed after a vanished stop
    assert not _rt_dir(runtime).exists()


def _many_pairs(tmp_path: Path, runtime: Path, n: int):
    reg = RuntimeRegistry.load(runtime / "instances.json", create_missing=True)
    containers = []
    for i in range(n):
        h = f"aa{i:06d}"
        reg.upsert_instance(_record(tmp_path / "removed" / f"proj{i}", worktree_hash=h))
        containers.append(_container(f"c{i}", worktree_hash=h))
        (runtime / f"proj{i}-{h}").mkdir()
    reg.save()
    return RuntimeRegistry.load(runtime / "instances.json"), containers


def test_apply_reap_bounds_stop_time_timeout_and_candidate_cap(
    tmp_path: Path, runtime: Path
):
    reg, containers = _many_pairs(tmp_path, runtime, 3)
    cands = _plan(reg, containers)
    assert len(cands) == 3
    runner = Recorder()
    report = reap.apply_reap(
        cands, runner=runner, max_candidates=1, stop_time_s=3, cmd_timeout_s=10.0
    )
    assert len(report.reaped) == 1
    assert [
        (c.container_ids, r) for c, r in zip(report.skipped, report.skip_reasons)
    ] == [
        (cands[1].container_ids, "cap"),
        (cands[2].container_ids, "cap"),
    ]
    assert runner.calls == [
        ["docker", "stop", "--time", "3", cands[0].container_ids[0]],
        ["docker", "rm", cands[0].container_ids[0]],
    ]
    assert all(k == {"timeout": 10.0} for k in runner.kwargs)


def test_maybe_reap_defaults_cap_three_and_bound_docker_calls(
    tmp_path: Path, runtime: Path
):
    reg, containers = _many_pairs(tmp_path, runtime, 4)
    runner = Recorder()
    got = reap.maybe_reap(
        throttle_s=0,
        state_file=tmp_path / "s",
        now=lambda: NOW,
        inspector=FakeInspect(containers),
        runner=runner,
    )
    assert got is not None and len(got.reaped) == 3
    assert [r for r in got.skip_reasons] == ["cap"]
    assert {tuple(c[:4]) for c in runner.calls if c[1] == "stop"} == {
        ("docker", "stop", "--time", "5")
    }
    assert all(k == {"timeout": 20.0} for k in runner.kwargs)


def test_deadline_skips_remaining_candidates(tmp_path: Path, runtime: Path):
    reg, containers = _many_pairs(tmp_path, runtime, 2)
    cands = _plan(reg, containers)
    clock = {"t": 0.0}

    class SlowRunner(Recorder):
        def __call__(self, cmd, **kwargs):
            clock["t"] += 60  # every docker call burns 60 s
            return super().__call__(cmd, **kwargs)

    runner = SlowRunner()
    report = reap.apply_reap(
        cands,
        runner=runner,
        cmd_timeout_s=10.0,
        deadline=100.0,
        clock=lambda: clock["t"],
    )
    # stop ends at 60 (60+10 <= 100) so rm runs; at 120 the second candidate is out of time
    assert [c[1] for c in runner.calls] == ["stop", "rm"]
    assert len(report.reaped) == 1
    assert report.skip_reasons == ["deadline"] and report.skipped == [cands[1]]
    assert report.to_dict()["skipped"][0]["skip_reason"] == "deadline"


def test_deadline_between_stop_and_rm_keeps_state_for_the_next_run(
    tmp_path: Path, runtime: Path
):
    missing, cands = _setup_apply(tmp_path, runtime)
    clock = {"t": 0.0}

    class SlowRunner(Recorder):
        def __call__(self, cmd, **kwargs):
            clock["t"] += 60
            return super().__call__(cmd, **kwargs)

    report = reap.apply_reap(
        cands,
        runner=SlowRunner(),
        cmd_timeout_s=10.0,
        deadline=100.0,
        clock=lambda: clock["t"],
    )
    assert report.reaped == [] and any("deadline" in e for e in report.errors)
    assert _rt_dir(runtime).is_dir()  # nothing released: containers may still exist


def test_maybe_reap_deadline_s_is_measured_from_the_call(tmp_path: Path, runtime: Path):
    reg, containers = _many_pairs(tmp_path, runtime, 2)
    clock = {"t": 1000.0}

    class SlowRunner(Recorder):
        def __call__(self, cmd, **kwargs):
            clock["t"] += 30
            return super().__call__(cmd, **kwargs)

    got = reap.maybe_reap(
        throttle_s=0,
        state_file=tmp_path / "s",
        now=lambda: NOW,
        inspector=FakeInspect(containers),
        runner=SlowRunner(),
        cmd_timeout_s=10.0,
        deadline_s=45,
        monotonic=lambda: clock["t"],
    )
    assert got is not None and len(got.reaped) == 1 and got.skip_reasons == ["deadline"]


# --- final review I2: a pruned dead record stamps last_detach (covers SIGKILL) -------


def _dead_record(rt: Path, *, mtime: float) -> Path:
    attached = rt / "attached"
    attached.mkdir(parents=True, exist_ok=True)
    dead = subprocess.Popen(["true"])
    dead.wait()
    record = attached / str(dead.pid)
    record.write_text("2026-11-06T00:00:00Z\n", encoding="utf-8")
    os.utime(record, (mtime, mtime))
    return record


def test_prune_stamps_last_detach_with_the_dead_record_mtime(tmp_path: Path):
    rt = tmp_path / "rt"
    record = _dead_record(rt, mtime=NOW - 300)
    assert reap.live_attachments(rt, prune=False) == 0
    assert not (rt / "last_detach").exists()  # a read-only count never writes
    assert reap.live_attachments(rt) == 0
    assert not record.exists()
    assert (rt / "last_detach").stat().st_mtime == NOW - 300


def test_prune_never_moves_a_newer_last_detach_back(tmp_path: Path):
    rt = tmp_path / "rt"
    _dead_record(rt, mtime=NOW - 300)
    _detached(rt, ago=10)  # a later clean detach
    reap.live_attachments(rt)
    assert (rt / "last_detach").stat().st_mtime == NOW - 10


def test_prune_advances_an_older_last_detach(tmp_path: Path):
    rt = tmp_path / "rt"
    _dead_record(rt, mtime=NOW - 300)
    _detached(rt, ago=5000)
    reap.live_attachments(rt)
    assert (rt / "last_detach").stat().st_mtime == NOW - 300


# --- final review P1 (N1): release a service's state once its containers are gone ----


def test_partial_reap_releases_the_services_whose_containers_are_gone(
    tmp_path: Path, runtime: Path
):
    missing, cands = _setup_apply(tmp_path, runtime)
    reg = RuntimeRegistry.load(runtime / "instances.json")
    reg.upsert_instance(_record(missing, service="dope-memory"))
    reg.save()
    cands = _plan(
        RuntimeRegistry.load(runtime / "instances.json"),
        [_container("a1"), _container("a2", service="dope-memory")],
    )
    runner = Recorder(
        fail={("docker", "stop", "a1")}
    )  # conport's container keeps running
    report = reap.apply_reap(cands, runner=runner)
    assert report.reaped == []
    assert any("a1" in e for e in report.errors)
    leases = {
        L["service"]: L["status"]
        for L in PortLeaseRegistry.load(runtime / "port-leases.json").leases()
    }
    assert leases["dope-memory"] == "released"  # a2 is gone: its state goes now
    assert leases["conport"] == "active"
    status = {
        i["service"]: i["status"]
        for i in RuntimeRegistry.load(runtime / "instances.json").instances()
    }
    assert status == {"conport": "running", "dope-memory": "stopped"}
    assert _rt_dir(runtime).is_dir()  # kept until every container is gone


# --- final review P1: `reap --json` keeps skip_reason ---------------------------------


def test_cli_apply_json_keeps_skip_reason(tmp_path: Path, runtime: Path, monkeypatch):
    _setup_apply(tmp_path, runtime)
    monkeypatch.setattr(
        reap, "inspect_all_managed_containers", FakeInspect([_container("a1")])
    )
    monkeypatch.setattr(reap, "run_cmd", Recorder())
    real_apply = reap.apply_reap

    def attach_then_apply(candidates, **kwargs):
        reap.attach(_rt_dir(runtime))  # a launcher attaches between plan and apply
        return real_apply(candidates, **kwargs)

    monkeypatch.setattr(reap, "apply_reap", attach_then_apply)
    result = CliRunner().invoke(_cli(), ["reap", "--apply", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert [s["skip_reason"] for s in payload["skipped"]] == ["attached"]


# --- final review P1: an entry with an empty service is owned by nobody: cleared ----


def test_state_only_reap_clears_entries_and_leases_without_a_service(
    tmp_path: Path, runtime: Path
):
    wt = tmp_path / "removed" / "proj"
    reg = _registry(runtime, wt, service="")
    leases = PortLeaseRegistry.load(runtime / "port-leases.json", create_missing=True)
    blank = _lease(wt, "", 3100)
    del blank["lease_id"]
    leases.upsert_lease(blank)
    leases.save()
    kw = {"lease_registry": PortLeaseRegistry.load(runtime / "port-leases.json")}
    cands = _plan(reg, [], **kw)
    assert [c.state_only for c in cands] == [True]
    report = reap.apply_reap(cands, runner=Recorder())
    assert report.errors == []
    statuses = [
        i["status"]
        for i in RuntimeRegistry.load(runtime / "instances.json").instances()
    ]
    assert statuses == ["stopped"]
    after = PortLeaseRegistry.load(runtime / "port-leases.json")
    assert [L["status"] for L in after.leases()] == ["released"]
    # nothing keeps the pair alive any more
    assert (
        _plan(
            RuntimeRegistry.load(runtime / "instances.json"), [], lease_registry=after
        )
        == []
    )


def test_reap_never_removes_images(tmp_path: Path, runtime: Path):
    # Images are shared by every worktree and project (final review I4).
    _missing, cands = _setup_apply(tmp_path, runtime)
    runner = Recorder()
    reap.apply_reap(cands, runner=runner)
    assert runner.calls
    assert all(c[:2] != ["docker", "rmi"] and "image" not in c for c in runner.calls)


# --- residual fix B2: the launcher reap really runs inside its 8 s deadline ------------
# Port of the re-review probe `rr2/t/test_rr2_launcher_reap_limits.py`: with
# cmd_timeout_s=10 reserved before every docker call and deadline_s=8, the launcher
# reap skipped every candidate ("deadline") yet still touched reap.last.


def test_launcher_limits_reap_one_candidate(tmp_path: Path, runtime: Path):
    from dopemux.mcp.launcher import LAUNCH_REAP_LIMITS

    _reg, containers = _many_pairs(tmp_path, runtime, 2)
    runner = Recorder()
    state = tmp_path / "s"
    got = reap.maybe_reap(
        throttle_s=600,
        state_file=state,
        now=lambda: NOW,
        inspector=FakeInspect(containers),
        runner=runner,
        **LAUNCH_REAP_LIMITS,
    )
    assert got is not None and len(got.reaped) == 1
    assert got.skip_reasons == ["cap"]  # one candidate per launcher, never "deadline"
    stops = [c for c in runner.calls if c[1] == "stop"]
    assert [c[:4] for c in stops] == [["docker", "stop", "--time", "2"]]
    assert runner.kwargs and all(0 < k["timeout"] <= 3.0 for k in runner.kwargs)
    assert state.exists()


def test_a_call_timeout_is_capped_at_the_time_left(tmp_path: Path, runtime: Path):
    reg, containers = _many_pairs(tmp_path, runtime, 1)
    cands = _plan(reg, containers)
    runner = Recorder()
    report = reap.apply_reap(
        cands, runner=runner, cmd_timeout_s=10.0, deadline=4.0, clock=lambda: 0.0
    )
    # 4 s are left: the candidate runs, each docker call gets at most those 4 s
    assert len(report.reaped) == 1 and report.skipped == []
    assert [k["timeout"] for k in runner.kwargs] == [4.0, 4.0]


class _Ticks:
    """A monotonic clock past any deadline after its first two readings (the
    deadline itself and the check before the docker inspection)."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self) -> float:
        self.calls += 1
        return 0.0 if self.calls <= 2 else 100.0


def test_a_deadline_skip_of_everything_leaves_reap_last_untouched(
    tmp_path: Path, runtime: Path
):
    _reg, containers = _many_pairs(tmp_path, runtime, 1)
    state = tmp_path / "s"

    def run() -> Any:
        return reap.maybe_reap(
            throttle_s=600,
            state_file=state,
            now=lambda: NOW,
            inspector=FakeInspect(containers),
            runner=Recorder(),
            deadline_s=8.0,
            monotonic=_Ticks(),
        )

    got = run()
    assert got is not None and got.reaped == [] and got.skip_reasons == ["deadline"]
    assert not state.exists()  # the throttle is not consumed
    state.write_text("", encoding="utf-8")
    os.utime(state, (NOW - 5000, NOW - 5000))
    again = run()
    assert again is not None and again.skip_reasons == ["deadline"]
    assert state.stat().st_mtime == NOW - 5000


# --- audit F3: automatic reaps never wait on a held instance lock or a slow docker ----


def test_automatic_reap_skips_an_instance_whose_lock_is_held(
    tmp_path: Path, runtime: Path
):
    import time

    from dopemux.mcp.locks import instance_lock

    _reg, containers = _many_pairs(tmp_path, runtime, 1)
    rt = runtime / "proj0-aa000000"
    runner = Recorder()
    state = tmp_path / "s"
    deadline_s = 8.0
    with instance_lock(rt):  # a launcher is starting this instance right now
        started = time.monotonic()
        got = reap.maybe_reap(
            throttle_s=600,
            state_file=state,
            now=lambda: NOW,
            inspector=FakeInspect(containers),
            runner=runner,
            deadline_s=deadline_s,
        )
        elapsed = time.monotonic() - started
    assert elapsed < 1.0 < deadline_s  # did not wait for the lock
    assert got is not None and got.reaped == [] and got.skip_reasons == ["locked"]
    assert runner.calls == []
    assert not state.exists()  # nothing was attempted: the throttle is not consumed
    assert rt.is_dir()


def test_explicit_apply_still_waits_for_the_instance_lock(
    tmp_path: Path, runtime: Path
):
    import threading

    from dopemux.mcp.locks import instance_lock

    reg, containers = _many_pairs(tmp_path, runtime, 1)
    cands = _plan(reg, containers)
    rt = runtime / "proj0-aa000000"
    held = threading.Event()
    release = threading.Event()

    def holder() -> None:
        with instance_lock(rt):
            held.set()
            release.wait(5)

    thread = threading.Thread(target=holder)
    thread.start()
    held.wait(5)
    threading.Timer(0.3, release.set).start()
    report = reap.apply_reap(cands, runner=Recorder())  # the CLI path: blocking
    thread.join(5)
    assert len(report.reaped) == 1 and report.skipped == []


def test_a_docker_inspection_past_the_deadline_skips_the_run(
    tmp_path: Path, runtime: Path
):
    import time

    _reg, containers = _many_pairs(tmp_path, runtime, 1)
    seen: Dict[str, float] = {}

    def slow_docker(*, timeout: float) -> DockerInspectResult:
        seen["timeout"] = timeout
        time.sleep(timeout)  # docker hangs until the timeout kills it
        return DockerInspectResult(available=False, error="docker ps -a timed out")

    state = tmp_path / "s"
    runner = Recorder()
    started = time.monotonic()
    got = reap.maybe_reap(
        throttle_s=600,
        state_file=state,
        now=lambda: NOW,
        inspector=slow_docker,
        runner=runner,
        cmd_timeout_s=3.0,
        deadline_s=0.3,
    )
    elapsed = time.monotonic() - started
    assert seen["timeout"] <= 0.3  # min(cmd_timeout_s, time left)
    assert elapsed < 1.5
    assert got is not None and got.reaped == [] and got.skipped == []
    assert runner.calls == []
    assert not state.exists()  # the run was skipped: nothing touched


# --- audit 2 F1: eligibility is re-evaluated under the instance lock ------------------


def _idle_candidate(tmp_path: Path, runtime: Path):
    """An idle pair: its worktree exists and its last launcher left 5000 s ago."""
    wt = tmp_path / "wt" / "proj"
    wt.mkdir(parents=True)
    reg = _registry(runtime, wt)
    _detached(_rt_dir(runtime), ago=5000)
    cands = _plan(reg, [_container("a1")])
    assert [c.reason for c in cands] == ["idle"]
    return wt, cands


def _registry_statuses(runtime: Path) -> List[str]:
    return [
        i["status"]
        for i in RuntimeRegistry.load(runtime / "instances.json").instances()
    ]


def test_a_detach_refreshed_after_planning_makes_the_candidate_stale(
    tmp_path: Path, runtime: Path
):
    _wt, cands = _idle_candidate(tmp_path, runtime)
    _detached(_rt_dir(runtime), ago=1)  # a launcher attached and left 1 s ago
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner, now=lambda: NOW, idle_s=IDLE)
    assert report.reaped == [] and report.skip_reasons == ["stale"]
    assert runner.calls == []  # no docker call
    assert _registry_statuses(runtime) == ["running"]  # no state change
    assert _rt_dir(runtime).is_dir()


def test_a_recently_dead_attach_record_makes_the_candidate_stale(
    tmp_path: Path, runtime: Path
):
    _wt, cands = _idle_candidate(tmp_path, runtime)
    _dead_record(_rt_dir(runtime), mtime=NOW - 1)  # pruning stamps last_detach NOW - 1
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner, now=lambda: NOW, idle_s=IDLE)
    assert report.skip_reasons == ["stale"] and runner.calls == []
    assert (_rt_dir(runtime) / "last_detach").stat().st_mtime == NOW - 1


def test_a_worktree_recreated_after_planning_makes_the_candidate_stale(
    tmp_path: Path, runtime: Path
):
    missing, cands = _setup_apply(tmp_path, runtime)
    assert [c.reason for c in cands] == ["worktree_missing"]
    missing.mkdir(parents=True)  # git worktree add at the same path, no launcher yet
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner, now=lambda: NOW, idle_s=IDLE)
    assert report.skip_reasons == ["stale"] and runner.calls == []
    leases = PortLeaseRegistry.load(runtime / "port-leases.json")
    assert {L["status"] for L in leases.leases()} == {"active"}


def test_a_genuinely_idle_candidate_is_still_reaped(tmp_path: Path, runtime: Path):
    _wt, cands = _idle_candidate(tmp_path, runtime)
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner, now=lambda: NOW, idle_s=IDLE)
    assert report.reaped == cands and report.skipped == []
    assert ["docker", "stop", "a1"] in runner.calls
    assert _registry_statuses(runtime) == ["stopped"]


def test_a_stale_only_run_leaves_reap_last_untouched(
    tmp_path: Path, runtime: Path, monkeypatch
):
    wt = tmp_path / "wt" / "proj"
    wt.mkdir(parents=True)
    _registry(runtime, wt)
    _detached(_rt_dir(runtime), ago=5000)
    # A launcher killed 1 s ago, after planning (planning reads dead records since
    # cycle 2 B3): the prune under the lock stamps last_detach NOW - 1.
    real_apply = reap.apply_reap

    def killed_after_planning(candidates, **kwargs):
        _dead_record(_rt_dir(runtime), mtime=NOW - 1)
        return real_apply(candidates, **kwargs)

    monkeypatch.setattr(reap, "apply_reap", killed_after_planning)
    state = tmp_path / "s"
    got = reap.maybe_reap(
        throttle_s=600,
        state_file=state,
        now=lambda: NOW,
        idle_s=IDLE,
        inspector=FakeInspect([_container("a1")]),
        runner=Recorder(),
    )
    assert got is not None and got.skip_reasons == ["stale"]
    assert not state.exists()


# --- audit 2 F2: a busy registry lock never stalls an automatic reap -------------------


def test_automatic_reap_with_a_held_registry_lock_skips_finalization(
    tmp_path: Path, runtime: Path
):
    import time

    from dopemux.mcp.locks import registry_lock

    missing, _cands = _setup_apply(tmp_path, runtime)
    leases_before = (runtime / "port-leases.json").read_text()
    registry_before = (runtime / "instances.json").read_text()
    runner = Recorder()
    state = tmp_path / "s"
    with registry_lock(runtime / "instances.json"):  # e.g. a long lifecycle save
        started = time.monotonic()
        got = reap.maybe_reap(
            throttle_s=600,
            state_file=state,
            now=lambda: NOW,
            inspector=FakeInspect(
                [_container("a1"), _container("a2", service="dope-memory")]
            ),
            runner=runner,
            deadline_s=8.0,
        )
        elapsed = time.monotonic() - started
    assert elapsed < 4.0  # bounded wait (<= 2 s), never the whole deadline or forever
    assert (
        got is not None and got.reaped == [] and got.skip_reasons == ["registry_busy"]
    )
    stopped = {c[-1] for c in runner.calls if c[1] == "stop"}
    removed = {c[-1] for c in runner.calls if c[1] == "rm"}
    assert stopped == removed == {"a1", "a2"}  # containers handled as before
    assert (runtime / "port-leases.json").read_text() == leases_before
    assert (runtime / "instances.json").read_text() == registry_before
    assert _rt_dir(runtime).is_dir()  # kept: the next run finishes from state
    assert state.exists()  # docker calls were made: the throttle is consumed

    # the next run: no containers left, so a state-only candidate cleans the pair
    again = _plan(
        RuntimeRegistry.load(runtime / "instances.json"),
        [],
        lease_registry=PortLeaseRegistry.load(runtime / "port-leases.json"),
    )
    assert [c.state_only for c in again] == [True]
    report = reap.apply_reap(again, runner=Recorder(), blocking_locks=False)
    assert report.reaped == again and report.errors == []
    assert _registry_statuses(runtime) == ["stopped"]
    leases = PortLeaseRegistry.load(runtime / "port-leases.json")
    assert {L["service"]: L["status"] for L in leases.leases()}["conport"] == "released"
    assert not _rt_dir(runtime).exists()


def test_explicit_apply_still_waits_for_the_registry_lock(
    tmp_path: Path, runtime: Path
):
    import threading

    from dopemux.mcp.locks import registry_lock

    _missing, cands = _setup_apply(tmp_path, runtime)
    held = threading.Event()
    release = threading.Event()

    def holder() -> None:
        with registry_lock(runtime / "instances.json"):
            held.set()
            release.wait(5)

    thread = threading.Thread(target=holder)
    thread.start()
    held.wait(5)
    threading.Timer(0.3, release.set).start()
    report = reap.apply_reap(cands, runner=Recorder())  # the CLI path: blocking
    thread.join(5)
    assert report.reaped == cands and report.skipped == [] and report.errors == []
    assert _registry_statuses(runtime) == ["stopped"]


# --- cycle 2 B1 (codex F1): a failed state save keeps the runtime dir -------------------


def test_a_failed_state_save_keeps_the_runtime_dir_and_is_not_reaped(
    tmp_path: Path, runtime: Path, monkeypatch
):
    _missing, cands = _setup_apply(tmp_path, runtime)
    leases_before = (runtime / "port-leases.json").read_text()
    registry_before = (runtime / "instances.json").read_text()
    real_save = reap.save_states_locked
    monkeypatch.setattr(
        reap, "save_states_locked", lambda updates, wait_s=None: ["boom"]
    )
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner)
    assert report.reaped == []
    assert report.skipped == cands and report.skip_reasons == ["state_error"]
    assert any("boom" in e for e in report.errors)
    removed = {c[-1] for c in runner.calls if c[1] == "rm"}
    assert removed == {"a1", "a2"}  # the containers are gone
    assert _rt_dir(runtime).is_dir()  # the recovery artifacts stay
    assert (runtime / "port-leases.json").read_text() == leases_before
    assert (runtime / "instances.json").read_text() == registry_before

    # a later run finishes it from state alone (containers are gone, worktree too)
    monkeypatch.setattr(reap, "save_states_locked", real_save)
    again = _plan(
        RuntimeRegistry.load(runtime / "instances.json"),
        [],
        lease_registry=PortLeaseRegistry.load(runtime / "port-leases.json"),
    )
    assert [c.state_only for c in again] == [True]
    later = reap.apply_reap(again, runner=Recorder())
    assert later.reaped == again and later.errors == []
    assert _registry_statuses(runtime) == ["stopped"]
    assert not _rt_dir(runtime).exists()


def test_a_failed_state_save_in_separate_registry_dirs_keeps_the_runtime_dir(
    tmp_path: Path, runtime: Path, monkeypatch
):
    _missing, cands = _setup_apply(tmp_path, runtime)
    other = tmp_path / "elsewhere"
    other.mkdir()
    (runtime / "port-leases.json").rename(other / "port-leases.json")
    saves: List[str] = []

    def failing(cls, path, mutate, *, wait_s=None):
        saves.append(Path(path).name)
        return "boom" if Path(path).name == "port-leases.json" else None

    monkeypatch.setattr(reap, "save_state_locked", failing)
    report = reap.apply_reap(
        cands,
        runner=Recorder(),
        lease_path=other / "port-leases.json",
        registry_path=runtime / "instances.json",
    )
    assert saves == ["port-leases.json", "instances.json"]  # one lock each
    assert report.reaped == [] and report.skip_reasons == ["state_error"]
    assert any("boom" in e for e in report.errors)
    assert _rt_dir(runtime).is_dir()


def test_a_failed_state_save_after_a_partial_docker_failure_is_never_reaped(
    tmp_path: Path, runtime: Path, monkeypatch
):
    _missing, cands = _setup_apply(tmp_path, runtime)
    monkeypatch.setattr(
        reap, "save_states_locked", lambda updates, wait_s=None: ["boom"]
    )
    report = reap.apply_reap(cands, runner=Recorder(fail={("docker", "stop", "a1")}))
    assert report.reaped == [] and report.skipped == []
    assert any("a1" in e for e in report.errors) and any(
        "boom" in e for e in report.errors
    )
    assert _rt_dir(runtime).is_dir()


# --- cycle 2 B3 (Codex P2): a crashed launcher still lets the instance go idle ---------


def test_a_dead_attach_record_makes_an_idle_candidate_and_planning_writes_nothing(
    tmp_path: Path, runtime: Path, monkeypatch
):
    wt = tmp_path / "wt" / "proj"
    wt.mkdir(parents=True)
    reg = _registry(runtime, wt)
    rt = _rt_dir(runtime)
    record = _dead_record(rt, mtime=NOW - IDLE - 60)  # SIGKILLed: never detached
    assert not (rt / "last_detach").exists()
    cands = _plan(reg, [_container("a1")])
    assert [c.reason for c in cands] == ["idle"]
    assert record.exists()  # the dry run prunes nothing
    assert not (rt / "last_detach").exists()  # and stamps nothing
    assert sorted(p.name for p in (rt / "attached").iterdir()) == [record.name]

    seen: Dict[str, Any] = {}
    real_still_eligible = reap._still_eligible

    def spy(cand, **kw):
        seen["record"] = record.exists()
        seen["last_detach"] = (rt / "last_detach").stat().st_mtime
        return real_still_eligible(cand, **kw)

    monkeypatch.setattr(reap, "_still_eligible", spy)
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner, now=lambda: NOW, idle_s=IDLE)
    # under the lock the record was pruned and stamped last_detach before the re-check
    assert seen == {"record": False, "last_detach": NOW - IDLE - 60}
    assert report.reaped == cands and report.skipped == [] and report.errors == []
    assert ["docker", "stop", "a1"] in runner.calls
    assert _registry_statuses(runtime) == ["stopped"]
    assert not rt.exists()


def test_a_young_dead_attach_record_is_not_idle(tmp_path: Path, runtime: Path):
    wt = tmp_path / "wt" / "proj"
    wt.mkdir(parents=True)
    reg = _registry(runtime, wt)
    _dead_record(_rt_dir(runtime), mtime=NOW - IDLE + 60)
    assert _plan(reg, [_container("a1")]) == []


def test_a_last_detach_newer_than_the_dead_record_wins(tmp_path: Path, runtime: Path):
    wt = tmp_path / "wt" / "proj"
    wt.mkdir(parents=True)
    reg = _registry(runtime, wt)
    rt = _rt_dir(runtime)
    _dead_record(rt, mtime=NOW - IDLE - 60)
    _detached(rt, ago=10)  # a later launcher attached and left cleanly
    assert reap._effective_last_detach(rt) == NOW - 10
    assert _plan(reg, [_container("a1")]) == []


def test_effective_last_detach_reads_only_dead_numeric_records(tmp_path: Path):
    rt = tmp_path / "rt"
    assert reap._effective_last_detach(rt) is None  # nothing at all
    attached = rt / "attached"
    attached.mkdir(parents=True)
    junk = attached / "not-a-pid"
    junk.write_text("x", encoding="utf-8")
    os.utime(junk, (NOW - 9000, NOW - 9000))
    zero = attached / "0"
    zero.write_text("x", encoding="utf-8")
    os.utime(zero, (NOW - 8000, NOW - 8000))
    live = attached / str(os.getpid())
    live.write_text("x", encoding="utf-8")
    os.utime(live, (NOW - 7000, NOW - 7000))
    assert reap._effective_last_detach(rt) is None  # junk, zero and a live pid ignored
    dead = _dead_record(rt, mtime=NOW - 6000)
    assert reap._effective_last_detach(rt) == NOW - 6000
    _detached(rt, ago=6500)  # an older last_detach loses to the dead record
    assert reap._effective_last_detach(rt) == NOW - 6000
    assert dead.exists() and junk.exists()  # read-only


def test_effective_last_detach_of_an_unreadable_attached_dir_is_none(
    tmp_path: Path, monkeypatch
):
    rt = tmp_path / "rt"
    _detached(rt, ago=9000)
    (rt / "attached").mkdir()
    real_iterdir = Path.iterdir

    def unreadable(self):
        if self.name == "attached":
            raise PermissionError("denied")
        return real_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", unreadable)
    assert reap._effective_last_detach(rt) is None


# --- cycle 2 B4 (acceptance finding 2): a build-only launch's runtime dir -------------


def _empty_runtime_registry(runtime: Path) -> RuntimeRegistry:
    reg = RuntimeRegistry.load(runtime / "instances.json", create_missing=True)
    reg.save()
    loaded = RuntimeRegistry.load(runtime / "instances.json")
    assert loaded.parse_status == "OK" and loaded.instances() == []
    return loaded


def _marked_dir(
    runtime: Path,
    worktree_root: Path,
    *,
    worktree_hash: str = HASH,
    project_root: Optional[Path] = None,
    dir_name: Optional[str] = None,
    marker: Optional[Any] = None,
) -> Path:
    """A runtime dir as a refused build-only launch leaves it (no registry entry)."""
    rt = runtime / (dir_name or f"proj-{worktree_hash}")
    rt.mkdir(parents=True, exist_ok=True)
    (rt / "build.log").write_text("building\n", encoding="utf-8")
    (rt / "compose.build.yml").write_text("services: {}\n", encoding="utf-8")
    if marker is None:
        marker = {
            "project_id": PROJECT_ID,
            "worktree_hash": worktree_hash,
            "worktree_root": str(worktree_root),
            "project_root": str(project_root or worktree_root),
            "written_at": "2026-11-07T00:00:00Z",
        }
    text = marker if isinstance(marker, str) else json.dumps(marker)
    (rt / "instance.json").write_text(text, encoding="utf-8")
    return rt


def _build_pid(rt: Path, pid: int, *, age: float = 10.0) -> None:
    pid_file = rt / "build-conport.pid"
    pid_file.write_text(f"{pid}\n", encoding="utf-8")
    os.utime(pid_file, (NOW - age, NOW - age))


def _dead_pid() -> int:
    dead = subprocess.Popen(["true"])
    dead.wait()
    return dead.pid


def test_a_marked_dir_of_a_removed_worktree_is_a_dir_only_candidate(
    tmp_path: Path, runtime: Path
):
    reg = _empty_runtime_registry(runtime)
    missing = tmp_path / "removed" / "proj"
    rt = _marked_dir(runtime, missing)
    _build_pid(rt, _dead_pid())  # the build finished: no longer live
    cands = _plan(reg, [])
    assert len(cands) == 1
    cand = cands[0]
    assert cand.runtime_dir == rt and cand.reason == "worktree_missing"
    assert cand.state_only and cand.dir_only
    assert (cand.project_id, cand.worktree_hash) == (PROJECT_ID, HASH)
    assert cand.worktree_root == str(missing)
    assert cand.to_dict()["dir_only"] is True and cand.to_dict()["state_only"] is True
    assert (rt / "instance.json").exists() and (rt / "build.log").exists()  # dry run

    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner, now=lambda: NOW, idle_s=IDLE)
    assert runner.calls == []  # no container: no docker call at all
    assert report.reaped == cands and report.errors == [] and report.skipped == []
    assert not rt.exists()
    assert _plan(RuntimeRegistry.load(runtime / "instances.json"), []) == []


def test_a_marked_dir_with_a_live_build_is_not_a_candidate(
    tmp_path: Path, runtime: Path
):
    reg = _empty_runtime_registry(runtime)
    rt = _marked_dir(runtime, tmp_path / "removed" / "proj")
    _build_pid(rt, os.getpid())  # alive and young: the build may still write here
    assert _plan(reg, []) == []
    # older than the build budget: stale, as the launcher treats it
    _build_pid(rt, os.getpid(), age=dr.build_timeout_secs() + 60)
    assert [c.dir_only for c in _plan(reg, [])] == [True]


def test_a_marked_dir_that_is_not_ours_is_ignored(tmp_path: Path, runtime: Path):
    reg = _empty_runtime_registry(runtime)
    missing = tmp_path / "removed" / "proj"
    # project_root names another slug: runtime_dir_for_paths would not be this dir
    _marked_dir(runtime, missing, project_root=tmp_path / "removed" / "other")
    # hash in the marker differs from the dir name
    _marked_dir(runtime, missing, worktree_hash="beef0001", dir_name="proj-beef0002")
    assert _plan(reg, []) == []


def test_a_marked_dir_of_an_existing_worktree_is_never_reaped_as_idle(
    tmp_path: Path, runtime: Path
):
    reg = _empty_runtime_registry(runtime)
    live = tmp_path / "wt" / "proj"
    live.mkdir(parents=True)
    rt = _marked_dir(runtime, live)
    _detached(rt, ago=IDLE * 10)  # idle for a long time: still not a candidate
    assert _plan(reg, []) == []


def test_runtime_dirs_without_a_good_marker_are_ignored(tmp_path: Path, runtime: Path):
    reg = _empty_runtime_registry(runtime)
    missing = tmp_path / "removed" / "proj"
    legacy = runtime / "dopemux-mvp-2271"  # no marker at all
    legacy.mkdir()
    (legacy / "build.log").write_text("x\n", encoding="utf-8")
    _marked_dir(runtime, missing, worktree_hash="beef0001", marker="{not json")
    _marked_dir(
        runtime,
        missing,
        worktree_hash="beef0002",
        marker={
            "project_id": PROJECT_ID,
            "worktree_hash": "beef0002",
        },  # fields missing
    )
    _marked_dir(
        runtime,
        missing,
        dir_name="proj-..",
        marker={
            "project_id": PROJECT_ID,
            "worktree_hash": "..",  # unsafe hash
            "worktree_root": str(missing),
            "project_root": str(missing),
        },
    )
    assert _plan(reg, []) == []
    assert legacy.is_dir()


def test_a_marked_dir_with_a_registry_entry_or_container_is_not_dir_only(
    tmp_path: Path, runtime: Path
):
    missing = tmp_path / "removed" / "proj"
    reg = _registry(runtime, missing)  # the registry knows the pair
    _marked_dir(runtime, missing)
    cands = _plan(reg, [])
    assert [(c.state_only, c.dir_only) for c in cands] == [(True, False)]  # once
    (runtime / "instances.json").unlink()
    reg_empty = _empty_runtime_registry(runtime)
    assert [c.dir_only for c in _plan(reg_empty, [])] == [True]
    # a managed container of the pair (any scope) keeps it out of the dir-only source
    assert _plan(reg_empty, [_container("p1", scope="project")]) == []


def test_a_marked_dir_with_a_live_attachment_is_not_a_candidate(
    tmp_path: Path, runtime: Path
):
    reg = _empty_runtime_registry(runtime)
    rt = _marked_dir(runtime, tmp_path / "removed" / "proj")
    reap.attach(rt)
    assert _plan(reg, []) == []


def test_a_dir_only_candidate_is_rechecked_under_the_lock(
    tmp_path: Path, runtime: Path
):
    reg = _empty_runtime_registry(runtime)
    missing = tmp_path / "removed" / "proj"
    rt = _marked_dir(runtime, missing)
    cands = _plan(reg, [])
    assert [c.dir_only for c in cands] == [True]
    # a build started after planning: kept
    _build_pid(rt, os.getpid())
    report = reap.apply_reap(cands, runner=Recorder(), now=lambda: NOW, idle_s=IDLE)
    assert report.skip_reasons == ["stale"] and rt.is_dir()
    (rt / "build-conport.pid").unlink()
    # the worktree is back and has been idle for long: never reaped on idle
    missing.mkdir(parents=True)
    _detached(rt, ago=IDLE * 10)
    report = reap.apply_reap(cands, runner=Recorder(), now=lambda: NOW, idle_s=IDLE)
    assert report.skip_reasons == ["stale"] and rt.is_dir()


# --- cycle 2 fix round 1 (review minors M3, M6, M7) -----------------------------------


def test_a_corrupt_lease_file_is_a_state_error_with_the_registry_still_saved(
    tmp_path: Path, runtime: Path
):
    """The real partial outcome: each registry is saved on its own, no rollback."""
    missing, cands = _setup_apply(tmp_path, runtime)
    lease_file = runtime / "port-leases.json"
    lease_file.write_text("{not json", encoding="utf-8")
    runner = Recorder()
    report = reap.apply_reap(cands, runner=runner)
    assert report.reaped == [] and report.skip_reasons == ["state_error"]
    assert any("unreadable; left as is" in e for e in report.errors)
    assert {c[-1] for c in runner.calls if c[1] == "rm"} == {"a1", "a2"}
    assert _registry_statuses(runtime) == ["stopped"]  # this save succeeded
    assert lease_file.read_text(encoding="utf-8") == "{not json"  # left for a person
    assert _rt_dir(runtime).is_dir()  # kept
    # the next run retries from state (worktree gone, dir left) and fails the same way
    again = _plan(RuntimeRegistry.load(runtime / "instances.json"), [])
    assert [c.state_only for c in again] == [True]
    second = reap.apply_reap(again, runner=Recorder())
    assert second.skip_reasons == ["state_error"] and _rt_dir(runtime).is_dir()
    # once the lease file is readable again, a later run finishes it
    lease_file.unlink()
    fixed = PortLeaseRegistry.load(lease_file, create_missing=True)
    fixed.save()
    third = reap.apply_reap(again, runner=Recorder())
    assert third.reaped == again and not _rt_dir(runtime).exists()


def test_non_ascii_digits_are_never_parsed_as_pids(tmp_path: Path):
    rt = tmp_path / "rt"
    attached = rt / "attached"
    attached.mkdir(parents=True)
    (attached / "²").write_text("x", encoding="utf-8")  # "²".isdigit() is True
    assert reap.live_attachments(rt, prune=False) == 0
    assert reap.live_attachments(rt) == 0
    assert reap._effective_last_detach(rt) is None
    (rt / "build-conport.pid").write_text("²\n", encoding="utf-8")
    assert reap._live_build(rt, NOW) is False


def test_a_marker_with_a_relative_worktree_root_is_ignored(
    tmp_path: Path, runtime: Path
):
    reg = _empty_runtime_registry(runtime)
    _marked_dir(
        runtime,
        Path("removed/proj"),  # relative: would be judged against the cwd
        project_root=tmp_path / "removed" / "proj",
    )
    assert _plan(reg, []) == []
