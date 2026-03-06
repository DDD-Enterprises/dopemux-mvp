from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _walk_object_nodes(node, path, violations):
    if isinstance(node, dict):
        if node.get("type") == "object" and node.get("additionalProperties") is not False:
            violations.append(".".join(path))
        for key, value in node.items():
            _walk_object_nodes(value, path + [str(key)], violations)
        return
    if isinstance(node, list):
        for idx, value in enumerate(node):
            _walk_object_nodes(value, path + [str(idx)], violations)


def test_all_json_managed_steps_emit_closed_object_schemas() -> None:
    root = Path(__file__).resolve().parents[3]
    phase_contract_map = _load_module(
        root / "services" / "repo-truth-extractor" / "lib" / "phase_contract_map.py",
        "phase_contract_map_for_schema_strictness",
    )
    structured_output_contracts = _load_module(
        root / "services" / "repo-truth-extractor" / "lib" / "structured_output_contracts.py",
        "structured_output_contracts_for_schema_strictness",
    )

    contract_map = phase_contract_map.compile_phase_contract_map()
    step_contracts = contract_map.get("steps", {})
    violations = []

    for step_id, step_contract in sorted(step_contracts.items()):
        if not structured_output_contracts.is_json_managed_step(step_contract):
            continue
        response_format, _ = structured_output_contracts.build_openai_response_format(step_contract)
        schema = response_format.get("json_schema", {}).get("schema", {})
        _walk_object_nodes(schema, [step_id], violations)

    assert violations == [], "OpenAI strict schema requires additionalProperties=false on every object: " + ", ".join(
        violations[:20]
    )
