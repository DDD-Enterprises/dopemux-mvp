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
                        "api_key_env": route.get("api_key_env"),
                        "service_tier": route.get("service_tier"),
                        "reasoning_effort": route.get("reasoning_effort"),
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
    # Plan B: the 6 BULK_CODE_HEAVY primary leads that carried grok-build-0.1 are
    # now the ${BULK_CODE_MODEL} placeholder (concrete model chosen per cost profile).
    assert "grok-build-0.1" not in model_ids
    # Increment 3: ${BULK_CODE_MODEL} now also drives the repair/sidefill leads of
    # the 6 BULK_CODE_HEAVY steps (6 primary + 6 repair + 6 sidefill = 18).
    assert model_ids.count("${BULK_CODE_MODEL}") == 18


def test_code_heavy_primary_leads_use_bulk_code_placeholder() -> None:
    # Plan B + Increment 3: BULK_CODE_HEAVY primary AND repair/sidefill leads use
    # the profile-agnostic placeholder.
    placeholders = [
        row for row in _model_map_routes() if row["model_id"] == "${BULK_CODE_MODEL}"
    ]
    assert {row["step_id"] for row in placeholders} == {
        "C1",
        "C5",
        "C6",
        "C7",
        "C10",
        "C11",
    }
    assert {row["route_role"] for row in placeholders} == {"primary", "repair", "sidefill"}
    assert {row["route_index"] for row in placeholders} == {0}
    assert {row["lane_class"] for row in placeholders} == {"BULK_CODE_HEAVY"}


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


def test_openai_routes_use_direct_latest_models_with_request_options() -> None:
    routes = _model_map_routes()

    assert not [
        row
        for row in routes
        if row["provider"] == "openrouter"
        and row["model_id"]
        in {"openai/gpt-5.4", "openai/gpt-5-mini", "openai/gpt-5.3-codex"}
    ]

    flex_routes = [
        row
        for row in routes
        if row["provider"] == "openai" and row["model_id"] == "gpt-5.5"
    ]
    # Plan B: counts reflect fallback routes only (leads converted to ${CELL};
    # 7 gpt-5.5 leads became placeholders: 171 -> 164). Codex 3361748519: the 7 AGG
    # primary tails moved from gpt-5.5 to a distinct gpt-5.3-codex fallback (so the
    # value-default SYNTH ladder keeps two distinct hops): 164 -> 157.
    assert len(flex_routes) == 157
    assert {row["api_key_env"] for row in flex_routes} == {"OPENAI_API_KEY"}
    assert {row["service_tier"] for row in flex_routes} == {"flex"}
    assert {row["reasoning_effort"] for row in flex_routes} == {None}

    codex_routes = [
        row
        for row in routes
        if row["provider"] == "openai" and row["model_id"] == "gpt-5.3-codex"
    ]
    # Plan B: 32 CE gpt-5.3-codex leads became ${CE_MODEL} (50 -> 18). Codex
    # 3361748519: the 11 CE primary middle gpt-5.3-codex routes were dropped when
    # the CE primary ladder was reshaped 3 -> 2 routes (lead = ${CE_MODEL}, fallback
    # = gpt-5.5); the 7 AGG steps each keep one gpt-5.3-codex (now the fallback):
    # 18 -> 7.
    assert len(codex_routes) == 7
    assert {row["api_key_env"] for row in codex_routes} == {"OPENAI_API_KEY"}
    assert {row["service_tier"] for row in codex_routes} == {None}
    assert {row["reasoning_effort"] for row in codex_routes} == {None}

    mini_routes = [
        row
        for row in routes
        if row["provider"] == "openai" and row["model_id"] == "gpt-5.4-mini"
    ]
    assert len(mini_routes) == 7
    assert {row["api_key_env"] for row in mini_routes} == {"OPENAI_API_KEY"}
    assert {row["service_tier"] for row in mini_routes} == {None}
    assert {row["reasoning_effort"] for row in mini_routes} == {None}


def test_grok_420_aliases_use_grok_43_with_explicit_reasoning_effort() -> None:
    routes = _model_map_routes()

    assert not [
        row
        for row in routes
        if row["provider"] == "xai"
        and row["model_id"]
        in {
            "grok-4.20-beta-0309-reasoning",
            "grok-4.20-beta-0309-non-reasoning",
        }
    ]

    grok_43 = [
        row
        for row in routes
        if row["provider"] == "xai" and row["model_id"] == "grok-4.3"
    ]
    # Plan B: 30 BULK_DOCS grok-4.3 leads (reasoning_effort=low) became
    # ${BULK_DOCS_MODEL} (260 -> 230; low 121 -> 91; none unchanged at 139).
    assert len(grok_43) == 230
    assert {
        effort: len([row for row in grok_43 if row["reasoning_effort"] == effort])
        for effort in {"low", "none"}
    } == {"low": 91, "none": 139}


def test_grok_4_3_none_routes_preserve_reasoning_effort_none() -> None:
    """Post-PR-685 fix invariant: the 139 YAML rows declaring
    ``reasoning_effort: none`` for xAI ``grok-4.3`` MUST forward
    ``reasoning_effort="none"`` to the xAI chat completions API.

    Per xAI's documented ``reasoning_effort`` enum
    (``none|low|medium|high``), ``"none"`` is the migration-recommended
    setting for non-reasoning workloads. The previous PR-685 fix used a
    global drop based on different source facts; this test now pins the
    corrected provider/model-aware preservation.

    The normalizer infers ``(provider, model_id)`` from the route dict itself
    when explicit kwargs are absent, so YAML rows that already carry
    ``provider: xai`` and ``model_id: grok-4.3`` trigger the allowlist match
    automatically.
    """
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "lib_route_options_regression",
        REPO_ROOT
        / "services"
        / "repo-truth-extractor"
        / "lib"
        / "route_options.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["lib_route_options_regression"] = module
    spec.loader.exec_module(module)

    rows = _model_map_routes()
    grok_43_none = [
        row
        for row in rows
        if row["provider"] == "xai"
        and row["model_id"] == "grok-4.3"
        and row["reasoning_effort"] == "none"
    ]
    assert len(grok_43_none) == 139
    for row in grok_43_none:
        normalized = module.normalize_route_request_options(row)
        assert normalized.get("reasoning_effort") == "none", (
            f"YAML row {row!r} must preserve reasoning_effort=none via "
            "dict-self-inference (xai/grok-4.3 is on the documented-enum "
            "allowlist)"
        )
