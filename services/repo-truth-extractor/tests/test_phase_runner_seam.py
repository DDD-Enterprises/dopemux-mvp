from __future__ import annotations

from extractor.phases.a import run_phase as run_extracted_phase_a
from extractor.phases.base import PhaseRunnerDeps
from extractor.phases.z import run_phase as run_extracted_phase_z
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import load_runner_module


def test_run_phase_a_delegates_to_extracted_impl(monkeypatch):
    runner = load_runner_module()
    sentinel = object()
    calls = {}

    monkeypatch.setattr(runner, "_phase_runner_deps", lambda: sentinel)

    def fake_impl(deps, dirs, cfg, ui=None):
        calls["args"] = (deps, dirs, cfg, ui)

    monkeypatch.setattr(runner, "extracted_run_phase_A", fake_impl)

    dirs = {"A": Path("/tmp/rte-phase-a")}
    cfg = object()
    ui = object()

    runner.run_phase_A(dirs, cfg, ui=ui)

    assert calls["args"] == (sentinel, dirs, cfg, ui)


def test_run_phase_z_delegates_to_extracted_impl(monkeypatch):
    runner = load_runner_module()
    sentinel = object()
    calls = {}

    monkeypatch.setattr(runner, "_phase_runner_deps", lambda: sentinel)

    def fake_impl(deps, dirs, cfg, ui=None):
        calls["args"] = (deps, dirs, cfg, ui)

    monkeypatch.setattr(runner, "extracted_run_phase_Z", fake_impl)

    dirs = {"Z": Path("/tmp/rte-phase-z")}
    cfg = object()
    ui = object()

    runner.run_phase_Z(dirs, cfg, ui=ui)

    assert calls["args"] == (sentinel, dirs, cfg, ui)


def test_phase_runner_deps_bind_existing_runner_helpers():
    runner = load_runner_module()

    deps = runner._phase_runner_deps()

    assert deps.repo_root == Path.cwd()
    assert deps.collector_cls is runner.Collector
    assert deps.merge_scan_excludes is runner._merge_scan_excludes
    assert deps.run_phase_inner is runner._run_phase_inner
    assert (
        deps.selected_execution_step_ids_for_phase
        is runner._selected_execution_step_ids_for_phase
    )
    assert deps.collect_phase_artifacts is runner.collect_phase_artifacts


def test_extracted_phase_a_uses_repo_scan_and_inner_runner():
    calls = {}

    class FakeCollector:
        def __init__(self, root, excludes):
            calls["collector"] = (root, excludes)

    def fake_merge_scan_excludes(base, repo):
        calls["merge"] = (list(base), list(repo))
        return list(base) + list(repo)

    def fake_run_phase_inner(phase, dirs, cfg, collector, targets, **kwargs):
        calls["inner"] = (phase, dirs, cfg, collector, targets, kwargs)

    deps = PhaseRunnerDeps(
        repo_root=Path("/tmp/rte-phase-runner-root"),
        repo_scan_excludes=("dist", ".pytest_cache"),
        collector_cls=FakeCollector,
        merge_scan_excludes=fake_merge_scan_excludes,
        run_phase_inner=fake_run_phase_inner,
        selected_execution_step_ids_for_phase=lambda cfg, phase: ["A0"],
        collect_phase_artifacts=lambda dirs, phases, kinds: [],
    )

    dirs = {"A": Path("/tmp/rte-phase-a")}
    cfg = object()
    ui = object()

    run_extracted_phase_a(deps, dirs, cfg, ui=ui)

    assert calls["merge"][0][:3] == [".git", "node_modules", "venv"]
    assert calls["merge"][1] == ["dist", ".pytest_cache"]
    assert calls["collector"] == (
        Path("/tmp/rte-phase-runner-root"),
        calls["merge"][0] + calls["merge"][1],
    )
    assert calls["inner"][0] == "A"
    assert calls["inner"][1] is dirs
    assert calls["inner"][2] is cfg
    assert isinstance(calls["inner"][3], FakeCollector)
    assert "AGENTS.md" in calls["inner"][4]
    assert calls["inner"][5]["ui"] is ui
    assert calls["inner"][5]["selected_step_ids"] == ["A0"]


def test_extracted_phase_z_collects_meta_inputs_before_inner_runner():
    calls = {}

    def fake_collect_phase_artifacts(dirs, phases, kinds):
        calls["collect"] = (dirs, list(phases), list(kinds))
        return [{"path": "/tmp/rte-phase-z/R/norm/OUT.json"}]

    def fake_run_phase_inner(phase, dirs, cfg, collector, targets, **kwargs):
        calls["inner"] = (phase, dirs, cfg, collector, targets, kwargs)

    deps = PhaseRunnerDeps(
        repo_root=Path("/tmp/rte-phase-runner-root"),
        repo_scan_excludes=(),
        collector_cls=object,
        merge_scan_excludes=lambda base, repo: list(base) + list(repo),
        run_phase_inner=fake_run_phase_inner,
        selected_execution_step_ids_for_phase=lambda cfg, phase: ["Z0"],
        collect_phase_artifacts=fake_collect_phase_artifacts,
    )

    dirs = {"Z": Path("/tmp/rte-phase-z")}
    cfg = object()
    ui = object()

    run_extracted_phase_z(deps, dirs, cfg, ui=ui)

    assert calls["collect"] == (dirs, ["R", "X", "T"], ["raw", "norm", "qa"])
    assert calls["inner"][0] == "Z"
    assert calls["inner"][1] is dirs
    assert calls["inner"][2] is cfg
    assert calls["inner"][3] is None
    assert calls["inner"][4] is None
    assert calls["inner"][5]["precollected_items"] == [
        {"path": "/tmp/rte-phase-z/R/norm/OUT.json"}
    ]
    assert calls["inner"][5]["ui"] is ui
    assert calls["inner"][5]["selected_step_ids"] == ["Z0"]
