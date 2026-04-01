from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.dopemux_pr_merge_specialist.dopetask_adapter import DopetaskAdapter
from src.dopemux_pr_merge_specialist.dopetask_bundle_loader import DopetaskBundleLoader
from src.dopemux_pr_merge_specialist.dopetask_status_mapper import DopetaskStatusMapper


@pytest.fixture
def adapter(tmp_path: Path) -> DopetaskAdapter:
    loader = DopetaskBundleLoader(tmp_path)
    mapper = DopetaskStatusMapper()
    return DopetaskAdapter(loader, mapper)


def test_adapter_from_bundle_path(adapter: DopetaskAdapter, tmp_path: Path) -> None:
    bundle_path = tmp_path / "TP-1_PROOF_BUNDLE.json"
    bundle = {
        "tp_id": "1",
        "title": "Series adapter bundle",
        "status": "VALIDATED",
        "posture": "GO_SUPERVISED_ONLY",
        "summary": {
            "result": "Validated under supervision",
            "confidence": "HIGH",
            "risk": "LOW",
        },
        "acceptance_checks": [],
        "validation": {"outcome": "PASS", "gates": []},
        "artifacts": [],
        "manifest": {"generator": "test", "version": "1.0"},
    }
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    result = adapter.from_bundle_path(bundle_path)
    assert result.tp.id == "1"
    assert result.tp.status == "VALIDATED"
    assert result.posture.mode == "GO_SUPERVISED_ONLY"
    assert result.integration.adapter_status == "READY"
    assert "APPLY_FIX" in result.governance.allowed_actions


def test_adapter_from_tp_id(adapter: DopetaskAdapter, tmp_path: Path) -> None:
    bundle_path = tmp_path / "TP-2_PROOF_BUNDLE.json"
    bundle = {
        "tp_id": "2",
        "title": "Lookup by TP id",
        "status": "IN_PROGRESS",
        "posture": "HOLD",
        "summary": {
            "result": "Execution still running",
            "confidence": "MEDIUM",
            "risk": "MEDIUM",
        },
        "acceptance_checks": [],
        "validation": {"outcome": "PENDING", "gates": []},
        "artifacts": [],
        "manifest": {"generator": "test", "version": "1.0"},
    }
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")

    result = adapter.from_tp_id("2")
    assert result.tp.id == "2"
    assert result.tp.status == "IN_PROGRESS"
    assert result.posture.mode == "HOLD"
