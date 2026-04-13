from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import load_runner_module


def test_write_step_metrics_snapshot_delegates_to_reporting_impl(monkeypatch):
    runner = load_runner_module()
    sentinel = {"status": "ok"}
    calls = {}

    monkeypatch.setattr(runner, "_telemetry_writer_deps", lambda: "telemetry-deps")

    def fake_impl(deps, run_root, phase, step_id, metrics):
        calls["args"] = (deps, run_root, phase, step_id, metrics)
        return sentinel

    monkeypatch.setattr(runner, "reporting_write_step_metrics_snapshot", fake_impl)

    result = runner.write_step_metrics_snapshot(
        Path("/tmp/rte-reporting-seam"),
        "D",
        "D1",
        {"count": 1},
    )

    assert result is sentinel
    assert calls["args"] == (
        "telemetry-deps",
        Path("/tmp/rte-reporting-seam"),
        "D",
        "D1",
        {"count": 1},
    )


def test_write_run_manifest_delegates_to_reporting_impl(monkeypatch, tmp_path):
    runner = load_runner_module()
    sentinel = {"blocked_promptset": False}
    calls = {}

    monkeypatch.setattr(runner, "_reporting_deps", lambda: "reporting-deps")

    def fake_impl(deps, root, dirs, run_id, args, run_context, phases):
        calls["args"] = (deps, root, dirs, run_id, args, run_context, phases)
        return sentinel

    monkeypatch.setattr(runner, "reporting_write_run_manifest", fake_impl)

    args = argparse.Namespace(phase="D", dry_run=True)
    run_context = runner.RunContext(
        run_id="reporting-seam",
        source="explicit",
        latest_file=tmp_path / "LATEST_RUN_ID",
        latest_written=False,
    )
    dirs = {"root": tmp_path / "runs" / "reporting-seam"}

    result = runner.write_run_manifest(
        tmp_path,
        dirs,
        "reporting-seam",
        args,
        run_context,
        ["D"],
    )

    assert result is sentinel
    assert calls["args"] == (
        "reporting-deps",
        tmp_path,
        dirs,
        "reporting-seam",
        args,
        run_context,
        ["D"],
    )
