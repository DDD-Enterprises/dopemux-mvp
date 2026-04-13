from __future__ import annotations

import json
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = SERVICE_ROOT / "prompts" / "prescan" / "registry.json"


def _load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def test_prescan_registry_lists_exactly_four_steps() -> None:
    data = _load_registry()
    assert len(data["steps"]) == 4
    expected = {"PRESCAN_DEDUP", "PRESCAN_DISCOVER", "PRESCAN_FEASIBILITY", "PRESCAN_OPTIMIZE"}
    assert set(data["steps"].keys()) == expected


def test_prescan_each_constant_name_exists_in_grok_passes() -> None:
    data = _load_registry()
    grok_path = SERVICE_ROOT / "lib" / "prescan" / "grok_passes.py"
    grok_text = grok_path.read_text(encoding="utf-8")
    for step_id, step in data["steps"].items():
        constant = step["constant_name"]
        assert constant in grok_text, (
            f"{step_id}: constant {constant} not found in grok_passes.py"
        )


def test_prescan_each_schema_exists_and_parses() -> None:
    data = _load_registry()
    base_dir = REGISTRY_PATH.parent
    for step_id, step in data["steps"].items():
        schema_path = base_dir / step["schema_path"]
        assert schema_path.exists(), f"{step_id}: schema missing at {schema_path}"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert "required" in schema, f"{step_id}: schema missing 'required' key"


def test_prescan_pass_system_prompts_keys_match_registry() -> None:
    data = _load_registry()
    grok_path = SERVICE_ROOT / "lib" / "prescan" / "grok_passes.py"
    grok_text = grok_path.read_text(encoding="utf-8")
    assert "PASS_SYSTEM_PROMPTS" in grok_text
    for step_id in data["steps"]:
        suffix = step_id.replace("PRESCAN_", "").lower()
        assert f'"{suffix}"' in grok_text, (
            f"PASS_SYSTEM_PROMPTS missing key '{suffix}' for {step_id}"
        )
