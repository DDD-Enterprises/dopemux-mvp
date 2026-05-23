from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[5]
MODEL_MAP = (
    REPO_ROOT
    / "services"
    / "repo-truth-extractor"
    / "promptsets"
    / "v4"
    / "model_map.yaml"
)
PROOF_DIR = REPO_ROOT / "proof" / "repo-truth-extractor" / "audit-2026-05-22"
PROPOSED_CHANGES = (
    PROOF_DIR / "TP-RTE-FINAL-AUDIT-MODEL-REFRESH-004_PROPOSED_CHANGES.json"
)
PROOF = PROOF_DIR / "TP-RTE-FINAL-AUDIT-MODEL-REFRESH-004_PROOF.json"

ROLE_KEYS = {
    "primary_routes": "primary",
    "repair_routes": "repair",
    "sidefill_routes": "sidefill",
}


def _route_rows(data: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    candidates: list[tuple[str, dict[str, Any]]] = []
    if isinstance(data, dict):
        raw_steps = data.get("steps")
        if isinstance(raw_steps, list):
            for step in raw_steps:
                if isinstance(step, dict):
                    candidates.append((str(step.get("step_id") or ""), step))
        elif isinstance(raw_steps, dict):
            for step_id, step in raw_steps.items():
                if isinstance(step, dict):
                    candidates.append((str(step_id), step))

    for step_id, spec in candidates:
        for route_key, role in ROLE_KEYS.items():
            routes = spec.get(route_key)
            if not isinstance(routes, list):
                continue
            for index, route in enumerate(routes):
                if not isinstance(route, dict):
                    continue
                rows.append(
                    {
                        "step_id": step_id,
                        "route_role": role,
                        "route_index": index,
                        "provider": route.get("provider"),
                        "model_id": route.get("model_id"),
                        "lane_class": spec.get("lane_class"),
                    }
                )
    return rows


def _model_map_routes() -> list[dict[str, Any]]:
    data = yaml.safe_load(MODEL_MAP.read_text(encoding="utf-8"))
    return _route_rows(data)


def test_retired_grok_code_fast_route_is_removed_from_model_map() -> None:
    model_ids = [row["model_id"] for row in _model_map_routes()]
    assert "grok-code-fast-1" not in model_ids
    assert model_ids.count("grok-build-0.1") == 6


def test_grok_build_replacement_is_limited_to_code_heavy_primary_routes() -> None:
    replacements = [
        row for row in _model_map_routes() if row["model_id"] == "grok-build-0.1"
    ]
    assert {row["step_id"] for row in replacements} == {
        "C1",
        "C5",
        "C6",
        "C7",
        "C10",
        "C11",
    }
    assert {row["route_role"] for row in replacements} == {"primary"}
    assert {row["route_index"] for row in replacements} == {0}
    assert {row["provider"] for row in replacements} == {"xai"}
    assert {row["lane_class"] for row in replacements} == {"BULK_CODE_HEAVY"}


def test_proposed_changes_are_structured_and_supported_for_implemented_routes() -> None:
    changes = json.loads(PROPOSED_CHANGES.read_text(encoding="utf-8"))
    assert isinstance(changes, list)
    implemented = [change for change in changes if change["decision"] == "IMPLEMENT"]
    assert len(implemented) == 6
    for change in implemented:
        assert change["old_model_id"] == "grok-code-fast-1"
        assert change["new_model_id"] == "grok-build-0.1"
        assert change["required_runtime_fields"] == []
        assert change["runtime_fields_supported"] is True


def test_unsupported_structured_field_migrations_are_deferred_in_proof() -> None:
    proof = json.loads(PROOF.read_text(encoding="utf-8"))
    deferred = proof["deferred_changes"]
    reasons = json.dumps(deferred, sort_keys=True)
    assert "DEFERRED_STRUCTURED_FIELD_UNSUPPORTED" in reasons
    assert "reasoning_effort" in reasons
    assert "service_tier" in reasons
