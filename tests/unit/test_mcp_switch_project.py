"""Unit tests for `dopemux mcp switch-project` (Task 3c, D2).

Docker, run_cmd and the lifecycle are recording fakes; the lock dir is tmp.
"""

from __future__ import annotations

import subprocess
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import click
import pytest
from click.testing import CliRunner

from dopemux.commands import mcp_commands
from dopemux.mcp import docker_inspect as di
from dopemux.mcp import docker_runtime as dr
from dopemux.mcp import lifecycle as lc
from dopemux.mcp.runtime_state import resolve_identity_view


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv(
        "DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "rt" / "instances.json")
    )
    path = tmp_path / "proj"
    path.mkdir()
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    monkeypatch.setattr(
        mcp_commands, "_load_catalog", lambda *_a, **_k: {"version": 1, "servers": {}}
    )
    return path.resolve()


class Recorder:
    def __init__(self) -> None:
        self.commands: List[List[str]] = []
        self.lifecycle: List[Dict[str, Any]] = []


@pytest.fixture
def rec(monkeypatch) -> Recorder:
    recorder = Recorder()

    def run_cmd(cmd, **_kwargs):
        recorder.commands.append(list(cmd))
        return dr.RuntimeCommandResult(command=list(cmd), exit_code=0)

    def run_lifecycle(operation: str, **kwargs: Any):
        recorder.lifecycle.append({"operation": operation, **kwargs})
        return SimpleNamespace(
            exit_code=0, status="PASS", blocking_findings=[], services=[]
        )

    monkeypatch.setattr(dr, "run_cmd", run_cmd)
    monkeypatch.setattr(lc, "run_lifecycle", run_lifecycle)
    monkeypatch.setattr(lc, "_port_is_free", lambda port: True)
    return recorder


def _docker(monkeypatch, *containers: di.DockerContainerInfo) -> None:
    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **_k: di.DockerInspectResult(
            available=True, containers=list(containers)
        ),
    )


def _to(labels: Dict[str, str]) -> di.DockerContainerInfo:
    return di.DockerContainerInfo(
        id="0123456789ab",
        name="task-orchestrator-owner",
        ports=["127.0.0.1:7890->7890/tcp"],
        labels=labels,
        published_ports=[7890],
    )


def _labels(project_id: str, project_root: str) -> Dict[str, str]:
    return {
        "dopemux.managed": "true",
        "dopemux.service": "task-orchestrator",
        "dopemux.project_id": project_id,
        "dopemux.project_root": project_root,
    }


def _invoke(repo: Path, *extra: str):
    return CliRunner().invoke(
        mcp_commands.mcp, ["switch-project", "--repo", str(repo), *extra]
    )


def test_switch_project_noop_when_owned(repo: Path, rec: Recorder, monkeypatch):
    ident = resolve_identity_view(repo)
    _docker(monkeypatch, _to(_labels(ident.project_id or "", ident.project_root or "")))
    result = _invoke(repo, "--yes")
    assert result.exit_code == 0, result.output
    assert "already serves" in result.output
    assert rec.commands == []
    assert rec.lifecycle == []


def test_switch_project_stops_owner_and_starts_target_with_yes(
    repo: Path, rec: Recorder, tmp_path: Path, monkeypatch
):
    foreign = str(tmp_path / "other-project")
    _docker(monkeypatch, _to(_labels("other-project", foreign)))
    result = _invoke(repo, "--yes")
    assert result.exit_code == 0, result.output
    assert foreign in result.output
    assert rec.commands == [
        ["docker", "stop", "0123456789ab"],
        ["docker", "rm", "0123456789ab"],
    ]
    assert len(rec.lifecycle) == 1
    assert rec.lifecycle[0]["operation"] == "start"
    assert rec.lifecycle[0]["repo"] == repo
    assert rec.lifecycle[0]["services"] == ["task-orchestrator"]


def test_switch_project_refuses_unmanaged_listener(
    repo: Path, rec: Recorder, monkeypatch
):
    _docker(monkeypatch, _to({"dopemux.project_root": "/somewhere"}))
    unlabeled = _invoke(repo, "--yes")
    _docker(monkeypatch)
    monkeypatch.setattr(lc, "_port_is_free", lambda port: False)
    process = _invoke(repo, "--yes")  # something that is not a container holds 7890
    for result in (unlabeled, process):
        assert result.exit_code == 1, result.output
        assert "not a managed task-orchestrator container" in result.output
    assert rec.commands == []
    assert rec.lifecycle == []


# --- confirm outside the host-wide lock (fix round 1, finding B) ------------


class LockSpy:
    """Stands in for `reserved_port_lock`; records whether it is held."""

    def __init__(self) -> None:
        self.held = False
        self.entered = 0

    @contextmanager
    def __call__(self, port: int):
        assert not self.held, "reserved_port_lock taken twice"
        self.held = True
        self.entered += 1
        try:
            yield
        finally:
            self.held = False


@pytest.fixture
def lock_spy(monkeypatch) -> LockSpy:
    from dopemux.mcp import locks

    spy = LockSpy()
    monkeypatch.setattr(locks, "reserved_port_lock", spy)
    return spy


def _foreign(tmp_path: Path, cid: str = "0123456789ab") -> di.DockerContainerInfo:
    owner = _to(_labels("other-project", str(tmp_path / "other-project")))
    owner.id = cid
    return owner


def _docker_sequence(monkeypatch, *snapshots) -> List[int]:
    calls: List[int] = []

    def inspect(**_k):
        calls.append(1)
        containers = snapshots[min(len(calls), len(snapshots)) - 1]
        return di.DockerInspectResult(available=True, containers=list(containers))

    monkeypatch.setattr(di, "inspect_running_containers", inspect)
    return calls


def test_switch_project_confirms_outside_the_reserved_lock(
    repo: Path, rec: Recorder, lock_spy: LockSpy, tmp_path: Path, monkeypatch
):
    _docker_sequence(monkeypatch, [_foreign(tmp_path)])
    asked: List[bool] = []

    def confirm(*_a, **_k):
        asked.append(lock_spy.held)
        return True

    monkeypatch.setattr(click, "confirm", confirm)
    under_lock: List[bool] = []
    record_cmd = dr.run_cmd

    def run_cmd(cmd, **kwargs):
        under_lock.append(lock_spy.held)
        return record_cmd(cmd, **kwargs)

    monkeypatch.setattr(dr, "run_cmd", run_cmd)
    result = _invoke(repo)
    assert result.exit_code == 0, result.output
    assert asked == [False]  # the prompt never holds the host-wide lock
    assert rec.commands == [
        ["docker", "stop", "0123456789ab"],
        ["docker", "rm", "0123456789ab"],
    ]
    assert under_lock == [True, True]
    assert len(rec.lifecycle) == 1


def test_switch_project_decline_changes_nothing(
    repo: Path, rec: Recorder, lock_spy: LockSpy, tmp_path: Path, monkeypatch
):
    _docker_sequence(monkeypatch, [_foreign(tmp_path)])
    result = CliRunner().invoke(
        mcp_commands.mcp, ["switch-project", "--repo", str(repo)], input="n\n"
    )
    assert result.exit_code == 1
    assert rec.commands == []
    assert rec.lifecycle == []
    assert lock_spy.entered == 0


@pytest.mark.parametrize("change", ["other_container", "was_free"])
def test_switch_project_refuses_when_owner_changed_after_confirm(
    change: str,
    repo: Path,
    rec: Recorder,
    lock_spy: LockSpy,
    tmp_path: Path,
    monkeypatch,
):
    if change == "other_container":
        _docker_sequence(
            monkeypatch, [_foreign(tmp_path)], [_foreign(tmp_path, "fedcba987654")]
        )
    else:
        _docker_sequence(monkeypatch, [], [_foreign(tmp_path)])
    result = _invoke(repo, "--yes")
    assert result.exit_code == 1, result.output
    assert "changed" in result.output
    assert rec.commands == []
    assert rec.lifecycle == []


# --- final review M4: the stopped owner's registry entry is marked stopped -----------


def test_switch_project_marks_the_old_owners_entry_stopped(
    repo: Path, rec: Recorder, tmp_path: Path, monkeypatch
):
    from dopemux.mcp.locks import locked_reload_and_save
    from dopemux.mcp.runtime_registry import (
        RuntimeRegistry,
        build_instance_record,
        default_registry_path,
    )

    def entry(project_id: str, service: str, root: str) -> Dict[str, Any]:
        return build_instance_record(
            instance_id=f"{project_id}-{service}",
            project_id=project_id,
            workspace_id=root,
            project_root=root,
            worktree_root=root,
            worktree_hash="beef0003",
            project_hash="p" * 8,
            service=service,
            scope="project" if service == "task-orchestrator" else "worktree",
            status="running",
            ports={},
            urls={},
            container_names=[
                "task-orchestrator-owner" if service == "task-orchestrator" else "c"
            ],
            compose_project_name="x",
            labels={},
        )

    foreign_root = str(tmp_path / "other-project")
    records = [
        entry("other-project", "task-orchestrator", foreign_root),
        entry("other-project", "conport", foreign_root),
    ]
    reg_path = default_registry_path()
    locked_reload_and_save(
        RuntimeRegistry, reg_path, lambda r: [r.upsert_instance(x) for x in records]
    )
    _docker(monkeypatch, _to(_labels("other-project", foreign_root)))

    result = _invoke(repo, "--yes")

    assert result.exit_code == 0, result.output
    status = {
        i["instance_id"]: i["status"]
        for i in RuntimeRegistry.load(reg_path).instances()
    }
    assert status == {
        "other-project-task-orchestrator": "stopped",
        "other-project-conport": "running",  # only the orchestrator that was stopped
    }
