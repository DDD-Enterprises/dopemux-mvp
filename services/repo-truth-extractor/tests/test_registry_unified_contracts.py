from __future__ import annotations

import json
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_POPULATIONS = {
    "SP": SERVICE_ROOT / "prompts" / "phase_s" / "registry.json",
    "FL_INT": SERVICE_ROOT / "prompts" / "phase_fl_int" / "registry.json",
    "S_INT": SERVICE_ROOT / "prompts" / "phase_s_int" / "registry.json",
}
REQUIRED_STEP_FIELDS = {"prompt_path", "outputs", "routing_tier", "max_hops"}


def _load_registry(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_registries_exist_and_parse() -> None:
    for name, path in REGISTRY_POPULATIONS.items():
        assert path.exists(), f"Registry missing: {name} at {path}"
        data = _load_registry(path)
        assert "steps" in data, f"Registry {name} missing 'steps' key"
        assert len(data["steps"]) > 0, f"Registry {name} has no steps"


def test_all_registries_have_required_fields() -> None:
    for name, path in REGISTRY_POPULATIONS.items():
        data = _load_registry(path)
        for step_id, step in data["steps"].items():
            for field in REQUIRED_STEP_FIELDS:
                assert field in step, f"{name}/{step_id} missing field: {field}"


def test_all_prompt_paths_resolve_to_existing_files() -> None:
    for name, path in REGISTRY_POPULATIONS.items():
        data = _load_registry(path)
        base_dir = path.parent
        for step_id, step in data["steps"].items():
            prompt_path = base_dir / step["prompt_path"]
            assert prompt_path.exists(), (
                f"{name}/{step_id}: prompt_path does not exist: {prompt_path}"
            )


def test_all_schema_paths_resolve_to_valid_json() -> None:
    for name, path in REGISTRY_POPULATIONS.items():
        data = _load_registry(path)
        base_dir = path.parent
        for step_id, step in data["steps"].items():
            schema_path_val = step.get("schema_path")
            if schema_path_val is None:
                continue
            schema_path = base_dir / schema_path_val
            assert schema_path.exists(), (
                f"{name}/{step_id}: schema_path does not exist: {schema_path}"
            )
            json.loads(schema_path.read_text(encoding="utf-8"))


def test_all_outputs_non_empty() -> None:
    for name, path in REGISTRY_POPULATIONS.items():
        data = _load_registry(path)
        for step_id, step in data["steps"].items():
            outputs = step.get("outputs", [])
            assert len(outputs) > 0, f"{name}/{step_id}: outputs is empty"


def test_zero_step_id_collisions_across_registries() -> None:
    all_step_ids: dict[str, str] = {}
    for name, path in REGISTRY_POPULATIONS.items():
        data = _load_registry(path)
        for step_id in data["steps"]:
            if step_id in all_step_ids:
                assert False, (
                    f"Step ID collision: {step_id} in both "
                    f"{all_step_ids[step_id]} and {name}"
                )
            all_step_ids[step_id] = name
