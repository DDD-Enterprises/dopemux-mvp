"""Validate-first PRMS launcher regression. No real engine is invoked."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.dopemux_pr_merge_specialist.dopetask_packet_launcher import (
    DopetaskPacketLauncher,
    PACKET_ENGINE_MAP,
)


def _launcher(tmp_path: Path) -> DopetaskPacketLauncher:
    # No engine is called by the unknown-lane scenario.
    return DopetaskPacketLauncher(ops_engine=object(), bundle_root=tmp_path, strategy_library={})


def test_unmapped_packet_creates_no_output_directory(tmp_path: Path) -> None:
    launcher = _launcher(tmp_path)
    trace = launcher.launch("TP-PRMS-UNMAPPED-019", {})

    assert trace.success is False
    assert trace.engine_lane == "unknown"
    assert trace.bundle_path is None
    assert "Unknown engine lane" in (trace.error or "")
    assert list(tmp_path.iterdir()) == [], "Failed validation must not create an unknown/ artifact tree"


def test_bad_mapped_lane_creates_no_output_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(PACKET_ENGINE_MAP, "TP-PRMS-MALFORMED-019", "unsupported-lane")
    trace = _launcher(tmp_path).launch("TP-PRMS-MALFORMED-019", {})

    assert not trace.success
    assert trace.engine_lane == "unsupported-lane"
    assert "Unknown engine lane" in (trace.error or "")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ("tp_id", "lane", "method"),
    [
        ("TP-PRMS-052", "closed_loop", "_run_closed_loop"),
        ("TP-PRMS-053", "patch", "_run_patch"),
        ("TP-PRMS-054", "fusion", "_run_fusion"),
    ],
)
def test_valid_packets_reach_exact_engine_handler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tp_id: str, lane: str, method: str
) -> None:
    launcher = _launcher(tmp_path)
    seen: list[tuple] = []

    def fake_handler(packet_id: str, run_id: str, context: dict, output_dir: Path) -> str:
        seen.append((packet_id, run_id, context, output_dir))
        return str(output_dir / "fixture-proof.json")

    monkeypatch.setattr(launcher, method, fake_handler)
    context = {"fixture_only": True}
    trace = launcher.launch(tp_id, context)

    assert trace.success
    assert trace.engine_lane == lane
    assert trace.error is None
    assert trace.bundle_path == str(tmp_path / lane / trace.run_id / "fixture-proof.json")
    assert seen == [(tp_id, trace.run_id, context, tmp_path / lane / trace.run_id)]
    assert (tmp_path / lane / trace.run_id).is_dir()
