from __future__ import annotations

import json
from pathlib import Path

import yaml


def test_fl_int_prompt_files_registry_and_schemas_exist() -> None:
    root = Path(__file__).resolve().parents[3]
    prompt_root = root / "services" / "repo-truth-extractor" / "prompts" / "phase_fl_int"
    registry = json.loads((prompt_root / "registry.json").read_text(encoding="utf-8"))
    steps = registry["steps"]
    for step_id in ["F0", "F1", "F2", "F4", "L0", "L1", "L3", "L4"]:
        row = steps[step_id]
        prompt_path = prompt_root / row["prompt_path"]
        schema_path = prompt_root / row["schema_path"]
        assert prompt_path.exists()
        text = prompt_path.read_text(encoding="utf-8")
        assert "{{FL_INT_INPUT_JSON}}" in text
        assert "{{PRIOR_OUTPUTS_JSON}}" in text
        json.loads(schema_path.read_text(encoding="utf-8"))


def test_fl_int_artifact_registry_rows_are_present_and_bounded() -> None:
    root = Path(__file__).resolve().parents[3]
    artifacts_path = root / "services" / "repo-truth-extractor" / "promptsets" / "v4" / "artifacts.yaml"
    payload = yaml.safe_load(artifacts_path.read_text(encoding="utf-8"))
    rows = {(row["phase"], row["artifact_name"]): row for row in payload["artifacts"]}

    assert rows[("F", "DESIGN_CLAIMS_RAW.json")]["kind"] == "json_item_list"
    assert rows[("F", "DESIGN_CLAIMS_CLASSIFIED.json")]["kind"] == "json_item_list"
    assert rows[("F", "DESIGN_CONTRADICTIONS.json")]["kind"] == "json_item_list"
    assert rows[("F", "CANONICAL_DESIGN.md")]["kind"] == "markdown"
    assert rows[("L", "FEATURE_CANDIDATES_RAW.json")]["kind"] == "json_item_list"
    assert rows[("L", "FEATURE_CANDIDATES_NORMALIZED.json")]["kind"] == "json_item_list"
    assert rows[("L", "FEATURE_MERGE_LOG.json")]["kind"] == "json_item_list"
    assert rows[("L", "FEATURE_LEDGER_ROUTING.json")]["kind"] == "json_item_list"
    assert ("F", "CANONICAL_DESIGN_META.json") not in rows
    assert ("L", "MASTER_FEATURE_LEDGER.json") not in rows
