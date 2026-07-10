"""Unit tests for fleet init/doctor (TP-DMX-MCP-RUNTIME-003)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from dopemux.mcp import fleet as fl


def _catalog() -> Dict[str, Any]:
    return {
        "version": 1,
        "defaults": {"per_worktree": ["conport"]},
        "servers": {
            "conport": {
                "scope": "per-worktree",
                "transport": "sse",
                "url_template": "http://localhost:${CONPORT_MCP_PORT}/sse",
                "port_var": "CONPORT_MCP_PORT",
                "default_port_base": 3005,
                "management_model": "compose-service",
            }
        },
    }


def _render(name: str, spec: Dict[str, Any]) -> Dict[str, Any]:
    return {"type": spec["transport"], "url": spec.get("url_template") or spec.get("url")}


def _alloc(worktree, names, catalog, *, project_root=None):
    return {"CONPORT_MCP_PORT": 3015}


def _exports(worktree, project_root):
    return {
        "DOPEMUX_WORKSPACE_ID": worktree,
        "DOPEMUX_WORKSPACE_ROOT": worktree,
        "DOPEMUX_PROJECT_ROOT": project_root,
        "TASK_ORCHESTRATOR_PROJECT_ROOT": project_root,
        "DOPEMUX_INSTANCE_ID": "ffff",
        "DOPE_MEMORY_WORKSPACE_ID": Path(worktree).name,
        "DOPE_MEMORY_INSTANCE_ID": "ffff",
        "WORKSPACE_ID": worktree,
    }


def _git_init(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=path, check=True, capture_output=True)
    (path / "README").write_text("x\n")
    subprocess.run(["git", "add", "README"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


def _git_worktree(main: Path, wt: Path, branch: str) -> None:
    subprocess.run(
        ["git", "worktree", "add", "-b", branch, str(wt)],
        cwd=main,
        check=True,
        capture_output=True,
    )


def test_fleet_init_dry_run_multi(tmp_path: Path):
    main = tmp_path / "main"
    _git_init(main)
    wt = tmp_path / "wt-a"
    _git_worktree(main, wt, "feature-a")

    report = fl.fleet_init(
        main,
        [main, wt],
        _catalog(),
        dry_run=True,
        apply=False,
        allocate_ports_fn=_alloc,
        project_env_exports_fn=_exports,
        render_local_fn=_render,
        global_claude_path=tmp_path / "no-global.json",
    )
    assert report.operation == "fleet-init"
    assert report.dry_run is True
    assert len(report.worktrees) == 2
    # dry-run must not write
    assert not (main / ".mcp.json").exists()
    assert not (wt / ".mcp.json").exists()
    assert report.counts["failed"] == 0


def test_fleet_init_apply(tmp_path: Path):
    main = tmp_path / "main"
    _git_init(main)
    wt = tmp_path / "wt-b"
    _git_worktree(main, wt, "feature-b")

    report = fl.fleet_init(
        main,
        [main, wt],
        _catalog(),
        dry_run=False,
        apply=True,
        allocate_ports_fn=_alloc,
        project_env_exports_fn=_exports,
        render_local_fn=_render,
        global_claude_path=tmp_path / "no-global.json",
    )
    assert (main / ".mcp.json").is_file()
    assert (wt / ".mcp.json").is_file()
    assert report.counts["failed"] == 0
    assert report.counts["repaired"] + report.counts["initialized"] >= 1


def test_fleet_wrong_repo_blocked(tmp_path: Path):
    a = tmp_path / "repo-a"
    b = tmp_path / "repo-b"
    _git_init(a)
    _git_init(b)

    report = fl.fleet_init(
        a,
        [b],
        _catalog(),
        dry_run=True,
        allocate_ports_fn=_alloc,
        project_env_exports_fn=_exports,
        render_local_fn=_render,
        global_claude_path=tmp_path / "no-global.json",
    )
    assert report.counts["failed"] == 1
    assert report.worktrees[0].code == "FLEET_WORKTREE_INVALID"
    assert report.status == "FAIL"


def test_fleet_invalid_path(tmp_path: Path):
    main = tmp_path / "main"
    _git_init(main)
    report = fl.fleet_init(
        main,
        [tmp_path / "does-not-exist"],
        _catalog(),
        dry_run=True,
        allocate_ports_fn=_alloc,
        project_env_exports_fn=_exports,
        render_local_fn=_render,
    )
    assert report.counts["failed"] >= 1


def test_fleet_doctor_aggregates(tmp_path: Path):
    main = tmp_path / "main"
    _git_init(main)

    def fake_doctor(path, **kwargs):
        m = MagicMock()
        m.status = "PASS_WITH_WARNINGS"
        m.findings = [MagicMock(code="TRANSPORT_MISMATCH")]
        return m

    report = fl.fleet_doctor(
        main,
        [main],
        _catalog(),
        skip_docker=True,
        run_doctor_fn=fake_doctor,
    )
    assert report.operation == "fleet-doctor"
    assert report.counts["warn"] == 1
    assert report.worktrees[0]["top_findings"] == ["TRANSPORT_MISMATCH"]
    assert report.status == "PASS_WITH_WARNINGS"


def test_fleet_doctor_json_shape(tmp_path: Path):
    main = tmp_path / "main"
    _git_init(main)

    def fake_doctor(path, **kwargs):
        return {"status": "PASS", "findings": []}

    report = fl.fleet_doctor(main, [main], _catalog(), run_doctor_fn=fake_doctor)
    d = json.loads(report.to_json())
    assert d["schema_version"] == "1.0"
    assert "counts" in d
    assert d["counts"]["pass"] == 1
