from __future__ import annotations

import json
from pathlib import Path

import pytest

from _fl_int_helpers import build_fl_int_run_root, load_collect_module


def test_collect_input_bundle_is_deterministic_and_handles_optional_x(tmp_path: Path) -> None:
    module = load_collect_module()
    run_root = build_fl_int_run_root(tmp_path, include_x=False)
    out_root = tmp_path / "out"
    first = module.collect_input_bundle(run_root, out_root=out_root)
    second = module.collect_input_bundle(run_root, out_root=out_root)
    assert first == second
    assert first["schema_version"] == "FL_INT_INPUT_V1"
    assert first["available_phase_ids"] == ["C", "D", "R"]
    assert "X" not in first["phases"]
    payload_path = out_root / "FL_INT_INPUT.json"
    assert payload_path.exists()
    parsed = json.loads(payload_path.read_text(encoding="utf-8"))
    assert parsed == first


def test_collect_input_requires_d_c_r_norm_dirs(tmp_path: Path) -> None:
    module = load_collect_module()
    run_root = build_fl_int_run_root(tmp_path)
    missing_dir = run_root / "R_arbitration" / "norm"
    for child in list(missing_dir.iterdir()):
        child.unlink()
    missing_dir.rmdir()
    with pytest.raises(ValueError):
        module.collect_input_payload(run_root)
