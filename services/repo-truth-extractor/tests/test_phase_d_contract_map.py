from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_contract_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "lib" / "phase_contract_map.py"
    spec = importlib.util.spec_from_file_location("phase_contract_map", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_compile_phase_contract_map_includes_d0_d1_lane_and_artifacts() -> None:
    module = _load_contract_module()
    payload = module.compile_phase_contract_map()
    assert payload["version"] == "PHASE_CONTRACT_MAP_V2"
    assert payload["scope"] == "json_managed_only"
    assert payload["policy"]["no_auto_transport_flips"] is True
    steps = payload["steps"]
    assert "D:D0" in steps
    assert "D:D1" in steps

    d0 = steps["D:D0"]
    assert d0["expected_artifacts"] == [
        "DOC_INVENTORY.json",
        "DOC_PARTITIONS.json",
        "DOC_TODO_QUEUE.json",
    ]
    assert d0["lane"]["lane_class"] == "CE"
    assert d0["lane"]["strict_schema_required"] is True
    assert d0["lane"]["primary_routes"][0]["provider"] == "openrouter"
    assert d0["lane"]["primary_routes"][0]["model_id"] == "openai/gpt-5.3-codex"
    assert d0["lane"]["sidefill_enabled"] is True

    d1 = steps["D:D1"]
    assert d1["expected_artifacts"] == [
        "DOC_INDEX.partX.json",
        "DOC_CONTRACT_CLAIMS.partX.json",
        "DOC_BOUNDARIES.partX.json",
        "DOC_SUPERSESSION.partX.json",
        "CAP_NOTICES.partX.json",
    ]
    cap_meta = d1["artifacts"]["CAP_NOTICES.partX.json"]
    assert cap_meta["canonical_schema_id"] == "CAP_NOTICES@v1"
    assert "id" in cap_meta["required_fields"]
    assert "path" in cap_meta["required_fields"]
    assert "line_range" in cap_meta["required_fields"]
    assert "evidence" in cap_meta["prompt_required_item_fields"]
    assert d1["lane"]["lane_class"] == "CE"
    assert d1["lane"]["primary_routes"][0]["strict_json_schema"] is True
    assert d1["lane"]["primary_routes"][0]["strict_passthrough_verified"] is True
    assert d1["scope"]["json_managed"] is True
    assert d1["scope"]["mixed_step"] is False


def test_write_phase_contract_map_persists_run_scoped_artifact(tmp_path: Path) -> None:
    module = _load_contract_module()
    out_path = module.write_phase_contract_map(tmp_path, "run_contract_map_test")
    assert out_path.name == "PHASE_CONTRACT_MAP.json"
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run_contract_map_test"
    assert payload["version"] == "PHASE_CONTRACT_MAP_V2"
    assert "D:D0" in payload["steps"]
    assert "D:D1" in payload["steps"]


def test_contract_map_scope_matches_repo_truth_json_steps_exactly() -> None:
    module = _load_contract_module()
    payload = module.compile_phase_contract_map()
    observed = set(payload["steps"].keys())

    repo_truth = json.loads(Path(module.REPO_TRUTH_MAP_PATH).read_text(encoding="utf-8"))
    expected = set()
    for row in repo_truth.get("steps", []):
        if not isinstance(row, dict):
            continue
        phase = str(row.get("phase") or "").strip().upper()
        step = str(row.get("step") or row.get("step_id") or "").strip().upper()
        prompt_declared = row.get("prompt_declared") if isinstance(row.get("prompt_declared"), dict) else {}
        artifacts = prompt_declared.get("expected_artifacts")
        if not isinstance(artifacts, list):
            continue
        if any(str(name).strip().endswith(".json") for name in artifacts):
            expected.add(f"{phase}:{step}")
    assert observed == expected


def test_unknown_lane_step_guard_rejects_phantom_steps() -> None:
    module = _load_contract_module()
    with pytest.raises(ValueError, match="outside repo_truth_map JSON scope"):
        module._assert_lane_map_matches_scope(  # type: ignore[attr-defined]
            {("A", "A0"): {}, ("A", "A11"): {}},
            {("A", "A0"): {}},
        )


def test_mixed_steps_keep_json_contract_and_markdown_bypass_metadata() -> None:
    module = _load_contract_module()
    payload = module.compile_phase_contract_map()
    t9 = payload["steps"]["T:T9"]
    z9 = payload["steps"]["Z:Z9"]
    for row in (t9, z9):
        assert row["lane"]["lane_class"] == "AGG"
        assert row["scope"]["json_managed"] is True
        assert row["scope"]["mixed_step"] is True
        assert row["scope"]["markdown_bypassed"] is True
