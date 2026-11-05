"""Unit tests for `dopemux mcp switch-project` (Task 3c, D2).

Docker, run_cmd and the lifecycle are recording fakes; the lock dir is tmp.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest
from click.testing import CliRunner

from dopemux.commands import mcp_commands
from dopemux.mcp import docker_inspect as di
from dopemux.mcp import docker_runtime as dr
from dopemux.mcp import lifecycle as lc
from dopemux.mcp.runtime_state import resolve_identity_view


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("DOPEMUX_MCP_RUNTIME_REGISTRY", str(tmp_path / "rt" / "instances.json"))
    path = tmp_path / "proj"
    path.mkdir()
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    monkeypatch.setattr(mcp_commands, "_load_catalog", lambda: {"version": 1, "servers": {}})
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
        return SimpleNamespace(exit_code=0, status="PASS", blocking_findings=[], services=[])

    monkeypatch.setattr(dr, "run_cmd", run_cmd)
    monkeypatch.setattr(lc, "run_lifecycle", run_lifecycle)
    monkeypatch.setattr(lc, "_port_is_free", lambda port: True)
    return recorder


def _docker(monkeypatch, *containers: di.DockerContainerInfo) -> None:
    monkeypatch.setattr(
        di,
        "inspect_running_containers",
        lambda **_k: di.DockerInspectResult(available=True, containers=list(containers)),
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
    return CliRunner().invoke(mcp_commands.mcp, ["switch-project", "--repo", str(repo), *extra])


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


def test_switch_project_refuses_unmanaged_listener(repo: Path, rec: Recorder, monkeypatch):
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
