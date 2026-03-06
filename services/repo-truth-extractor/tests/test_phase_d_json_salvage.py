from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runner = _load_runner_module()


def test_extract_first_json_object_salvages_single_object_with_leading_and_trailing_text() -> None:
    raw_text = 'Here is the result:\n{"artifacts":[{"artifact_name":"OUT.json","payload":{"ok":true}}]}\nthanks'
    salvaged = runner.extract_first_json_object(raw_text)
    assert salvaged == '{"artifacts":[{"artifact_name":"OUT.json","payload":{"ok":true}}]}'
    parsed = runner.parse_json_from_response(raw_text)
    assert isinstance(parsed, dict)
    assert parsed["artifacts"][0]["artifact_name"] == "OUT.json"


def test_extract_first_json_object_rejects_multiple_top_level_objects() -> None:
    raw_text = 'preface {"a":1} spacer {"b":2}'
    assert runner.extract_first_json_object(raw_text) is None
    assert runner.parse_json_from_response(raw_text) is None


def test_extract_first_json_object_rejects_ambiguous_partial_json_noise() -> None:
    raw_text = 'preface {not-json} {"a":1} trailer {"b":2}'
    assert runner.extract_first_json_object(raw_text) is None
    assert runner.parse_json_from_response(raw_text) is None


def test_existing_single_fenced_json_behavior_remains_valid() -> None:
    raw_text = "notes\n```json\n" + json.dumps({"artifacts": [{"artifact_name": "OUT.json", "payload": {"ok": True}}]}) + "\n```\n"
    parsed = runner.parse_json_from_response(raw_text)
    assert isinstance(parsed, dict)
    assert parsed["artifacts"][0]["payload"]["ok"] is True
