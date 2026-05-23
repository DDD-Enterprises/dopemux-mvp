from __future__ import annotations

import copy
import json
import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple


GENERIC_ITEM_VALUE_SCHEMA: Dict[str, Any] = {
    "anyOf": [
        {"type": "string"},
        {"type": "number"},
        {"type": "integer"},
        {"type": "boolean"},
        {
            "type": "array",
            "items": {
                "anyOf": [
                    {"type": "string"},
                    {"type": "number"},
                    {"type": "integer"},
                    {"type": "boolean"},
                    {"type": "null"},
                ]
            },
        },
        {"type": "null"},
    ]
}

STRUCTURED_OUTPUT_MODE_NONE = "none"
STRUCTURED_OUTPUT_MODE_JSON_OBJECT = "json_object"
STRUCTURED_OUTPUT_MODE_JSON_SCHEMA = "json_schema"
STRUCTURED_OUTPUT_MODES = {
    STRUCTURED_OUTPUT_MODE_NONE,
    STRUCTURED_OUTPUT_MODE_JSON_OBJECT,
    STRUCTURED_OUTPUT_MODE_JSON_SCHEMA,
}
ROUTE_REQUEST_OPTION_KEYS = ("service_tier", "reasoning_effort")

_XAI_STRIP_KEYWORDS: Set[str] = {
    "allOf",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
}
_GEMINI_ALLOWED_SCHEMA_KEYS: Set[str] = {
    "type",
    "format",
    "description",
    "nullable",
    "enum",
    "properties",
    "required",
    "propertyOrdering",
    "items",
    "minItems",
    "maxItems",
    "minimum",
    "maximum",
    "anyOf",
    "additionalProperties",
}


def normalize_structured_output_mode(value: Any) -> str:
    token = str(value or "").strip().lower()
    if token in STRUCTURED_OUTPUT_MODES:
        return token
    return STRUCTURED_OUTPUT_MODE_NONE


def route_structured_output_mode(
    route: Optional[Dict[str, Any]],
    *,
    step_contract: Optional[Dict[str, Any]] = None,
) -> str:
    if isinstance(route, dict):
        token = normalize_structured_output_mode(route.get("structured_output_mode"))
        if token != STRUCTURED_OUTPUT_MODE_NONE:
            return token
    if is_json_managed_step(step_contract):
        return STRUCTURED_OUTPUT_MODE_JSON_SCHEMA
    return STRUCTURED_OUTPUT_MODE_NONE


def is_json_managed_step(step_contract: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(step_contract, dict):
        return False
    scope = step_contract.get("scope") if isinstance(step_contract.get("scope"), dict) else {}
    if "json_managed" in scope:
        return bool(scope.get("json_managed"))
    return bool(step_contract.get("expected_artifacts"))


def is_strict_contract_step(step_contract: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(step_contract, dict):
        return False
    lane = step_contract.get("lane") if isinstance(step_contract.get("lane"), dict) else {}
    return bool(
        lane.get("strict_schema_required_primary")
        if "strict_schema_required_primary" in lane
        else lane.get("strict_schema_required")
    )


def contract_lane(step_contract: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(step_contract, dict):
        return None
    lane = step_contract.get("lane") if isinstance(step_contract.get("lane"), dict) else {}
    token = str(lane.get("lane_class") or lane.get("lane") or "").strip()
    return token or None


def repair_mode(step_contract: Optional[Dict[str, Any]]) -> str:
    if not isinstance(step_contract, dict):
        return "targeted_only"
    lane = step_contract.get("lane") if isinstance(step_contract.get("lane"), dict) else {}
    token = str(lane.get("repair_mode") or "").strip()
    return token or "targeted_only"


def sidefill_enabled(step_contract: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(step_contract, dict):
        return False
    lane = step_contract.get("lane") if isinstance(step_contract.get("lane"), dict) else {}
    return bool(lane.get("sidefill_enabled", False))


def plural_expected_json_artifacts(step_contract: Optional[Dict[str, Any]]) -> bool:
    if not isinstance(step_contract, dict):
        return False
    if "plural_expected_json_artifacts" in step_contract:
        return bool(step_contract.get("plural_expected_json_artifacts"))
    expected = list(step_contract.get("expected_artifacts") or [])
    return len(expected) >= 2


def route_entries_for_stage(
    step_contract: Optional[Dict[str, Any]],
    stage: str,
) -> List[Dict[str, Any]]:
    if not isinstance(step_contract, dict):
        return []
    lane = step_contract.get("lane") if isinstance(step_contract.get("lane"), dict) else {}
    key = {
        "primary": "primary_routes",
        "repair": "repair_routes",
        "sidefill": "sidefill_routes",
    }.get(str(stage or "").strip().lower())
    if not key:
        return []
    rows = lane.get(key)
    if not isinstance(rows, list):
        return []
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider") or "").strip().lower()
        model_id = str(row.get("model_id") or "").strip()
        api_key_env = str(row.get("api_key_env") or "").strip()
        if not (provider and model_id and api_key_env):
            continue
        parsed = {
            "provider": provider,
            "model_id": model_id,
            "api_key_env": api_key_env,
            "structured_output_mode": route_structured_output_mode(
                row,
                step_contract=step_contract,
            ),
            "strict_json_schema": bool(row.get("strict_json_schema", False)),
            "strict_passthrough_verified": bool(row.get("strict_passthrough_verified", False)),
        }
        for option_key in ROUTE_REQUEST_OPTION_KEYS:
            option_value = str(row.get(option_key) or "").strip()
            if option_value:
                parsed[option_key] = option_value
        out.append(parsed)
    return out


def route_for_contract(step_contract: Optional[Dict[str, Any]]) -> Optional[Tuple[str, str, str]]:
    rows = route_entries_for_stage(step_contract, "primary")
    if not rows:
        return None
    row = rows[0]
    return (str(row["provider"]), str(row["model_id"]), str(row["api_key_env"]))


def route_entry_by_identity(
    routes: Iterable[Dict[str, Any]],
    *,
    provider: str,
    model_id: str,
    api_key_env: str,
) -> Optional[Dict[str, Any]]:
    for row in routes:
        if not isinstance(row, dict):
            continue
        if (
            str(row.get("provider") or "") == str(provider)
            and str(row.get("model_id") or "") == str(model_id)
            and str(row.get("api_key_env") or "") == str(api_key_env)
        ):
            return dict(row)
    return None


def strict_capability_reason(
    route: Optional[Dict[str, Any]],
    transport: Optional[str],
) -> Optional[str]:
    if not isinstance(route, dict):
        return "route_missing"
    if not bool(route.get("strict_json_schema", False)):
        return "strict_json_schema_disabled"
    provider = str(route.get("provider") or "").strip().lower()
    transport_mode = str(transport or "").strip().lower()
    if provider == "openrouter" and not bool(route.get("strict_passthrough_verified", False)):
        return "openrouter_strict_passthrough_unverified"
    if provider in {"openai", "openrouter", "xai"}:
        if transport_mode in {"openai_sdk", "openai_compat_http"}:
            return None
        return f"transport_not_strict_capable:{transport_mode or 'unknown'}"
    return f"provider_not_strict_capable:{provider or 'unknown'}"


def is_strict_capable_route(route: Optional[Dict[str, Any]], transport: Optional[str]) -> bool:
    return strict_capability_reason(route, transport) is None


def schema_capability_reason(
    route: Optional[Dict[str, Any]],
    transport: Optional[str],
) -> Optional[str]:
    if not isinstance(route, dict):
        return "route_missing"
    mode = route_structured_output_mode(route)
    if mode == STRUCTURED_OUTPUT_MODE_NONE:
        return "structured_output_disabled"
    provider = str(route.get("provider") or "").strip().lower()
    transport_mode = str(transport or "").strip().lower()
    if mode == STRUCTURED_OUTPUT_MODE_JSON_OBJECT:
        if provider == "gemini":
            return None
        if provider in {"openai", "openrouter", "xai"} and transport_mode in {
            "openai_sdk",
            "openai_compat_http",
        }:
            return None
        return f"provider_not_json_object_capable:{provider or 'unknown'}"
    if provider == "gemini":
        return None
    if provider == "openrouter":
        return None if transport_mode in {"openai_sdk", "openai_compat_http"} else f"transport_not_schema_capable:{transport_mode or 'unknown'}"
    if provider in {"openai", "xai"}:
        return None if transport_mode in {"openai_sdk", "openai_compat_http"} else f"transport_not_schema_capable:{transport_mode or 'unknown'}"
    return f"provider_not_schema_capable:{provider or 'unknown'}"


def is_schema_capable_route(route: Optional[Dict[str, Any]], transport: Optional[str]) -> bool:
    return schema_capability_reason(route, transport) is None


def resolve_stage_route(
    *,
    step_contract: Optional[Dict[str, Any]],
    stage: str,
    transport_for_provider: Callable[[str], str],
    strict_required: bool,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    routes = route_entries_for_stage(step_contract, stage)
    attempts: List[Dict[str, Any]] = []
    for route in routes:
        provider = str(route["provider"])
        transport = transport_for_provider(provider)
        reason = strict_capability_reason(route, transport)
        strict_capable = reason is None
        schema_reason = schema_capability_reason(route, transport)
        schema_capable = schema_reason is None
        attempts.append(
            {
                "provider": provider,
                "model_id": str(route["model_id"]),
                # Deliberately omit api_key_env to avoid exposing authentication-related
                # environment identifiers in any logged or serialized strict-route metadata.
                "structured_output_mode": route_structured_output_mode(route, step_contract=step_contract),
                "transport": transport,
                "strict_json_schema": bool(route.get("strict_json_schema", False)),
                "strict_passthrough_verified": bool(route.get("strict_passthrough_verified", False)),
                "strict_capable": strict_capable,
                "schema_capable": schema_capable,
                "schema_reason": schema_reason,
                "reason": reason,
            }
        )
        if strict_required:
            if strict_capable:
                return route, attempts
            continue
        return route, attempts
    return None, attempts


def artifact_order(step_contract: Dict[str, Any], artifact_names: Optional[Iterable[str]] = None) -> List[str]:
    base = list(step_contract.get("artifact_order") or step_contract.get("expected_artifacts") or [])
    if artifact_names is None:
        return base
    wanted = {str(name).strip() for name in artifact_names if str(name).strip()}
    return [name for name in base if name in wanted]


def artifact_contract(step_contract: Dict[str, Any], artifact_name: str) -> Dict[str, Any]:
    artifacts = step_contract.get("artifacts") if isinstance(step_contract.get("artifacts"), dict) else {}
    row = artifacts.get(artifact_name)
    return dict(row) if isinstance(row, dict) else {}


def _generic_item_schema(artifact_meta: Dict[str, Any]) -> Dict[str, Any]:
    runner_required = set(artifact_meta.get("required_fields") or [])
    prompt_required = set(artifact_meta.get("prompt_required_item_fields") or [])
    required_keys = sorted(runner_required | prompt_required)
    properties: Dict[str, Any] = {
        "id": {"type": "string"},
        "path": {"type": "string"},
        "line_range": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2,
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "line_range": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                    "excerpt": {"type": "string"},
                },
                "required": ["path", "line_range", "excerpt"],
                "additionalProperties": False,
            },
        },
    }
    for key in required_keys:
        properties.setdefault(key, GENERIC_ITEM_VALUE_SCHEMA)
    # OpenAI strict mode requires every property in 'required'
    all_required = sorted(properties.keys())
    return {
        "type": "object",
        "required": all_required,
        "properties": properties,
        "additionalProperties": False,
    }


def build_json_schema_response_format(
    *,
    schema: Dict[str, Any],
    schema_name: str,
    strict: bool,
    contract_lane_name: Optional[str],
    schema_names: Optional[Iterable[str]] = None,
    artifact_names: Optional[Iterable[str]] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "strict": bool(strict),
            "schema": schema,
        },
    }
    meta = {
        "schema": schema_name,
        "schema_name": schema_name,
        "schema_version": "v1",
        "strict": bool(strict),
        "contract_lane": contract_lane_name,
        "schema_ids": list(schema_names or []),
        "artifact_names": list(artifact_names or []),
    }
    return response_format, meta


def build_openai_response_format(
    step_contract: Dict[str, Any],
    artifact_names: Optional[Iterable[str]] = None,
    schema_name_suffix: str = "draft",
    *,
    strict: bool = True,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    ordered_artifacts = artifact_order(step_contract, artifact_names)
    any_of_rows: List[Dict[str, Any]] = []
    schema_names: List[str] = []
    for artifact_name in ordered_artifacts:
        artifact_meta = artifact_contract(step_contract, artifact_name)
        schema_id = str(artifact_meta.get("canonical_schema_id") or "")
        schema_names.append(schema_id)
        payload_schema: Dict[str, Any] = {
            "type": "object",
            "properties": {
                "schema": {"type": "string", "const": schema_id},
                "items": {"type": "array", "items": _generic_item_schema(artifact_meta)},
            },
            "required": ["schema", "items"],
            "additionalProperties": False,
        }
        any_of_rows.append(
            {
                "type": "object",
                "properties": {
                    "artifact_name": {"type": "string", "const": artifact_name},
                    "payload": payload_schema,
                },
                "required": ["artifact_name", "payload"],
                "additionalProperties": False,
            }
        )

    schema_name = (
        f"{step_contract['phase']}_{step_contract['step_id']}_{schema_name_suffix}".lower().replace(".", "_")
    )
    schema = {
        "type": "object",
        "properties": {
            "artifacts": {
                "type": "array",
                "items": {"anyOf": any_of_rows},
                "minItems": len(ordered_artifacts),
                "maxItems": len(ordered_artifacts),
            }
        },
        "required": ["artifacts"],
        "additionalProperties": False,
    }
    return build_json_schema_response_format(
        schema=schema,
        schema_name=schema_name,
        strict=bool(strict),
        contract_lane_name=contract_lane(step_contract),
        schema_names=schema_names,
        artifact_names=ordered_artifacts,
    )


def _rewrite_const_to_enum(value: Any) -> Any:
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, child in value.items():
            if key == "const":
                out["enum"] = [child]
            else:
                out[key] = _rewrite_const_to_enum(child)
        return out
    if isinstance(value, list):
        return [_rewrite_const_to_enum(item) for item in value]
    return value


def _strip_schema_keywords(value: Any, stripped: Set[str]) -> Any:
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, child in value.items():
            if key in stripped:
                continue
            out[key] = _strip_schema_keywords(child, stripped)
        return out
    if isinstance(value, list):
        return [_strip_schema_keywords(item, stripped) for item in value]
    return value


def _filter_gemini_schema(value: Any) -> Any:
    if isinstance(value, dict):
        out: Dict[str, Any] = {}
        for key, child in value.items():
            if key == "const":
                out["enum"] = [child]
                continue
            if key not in _GEMINI_ALLOWED_SCHEMA_KEYS:
                continue
            if key == "properties" and isinstance(child, dict):
                out[key] = {
                    str(prop): _filter_gemini_schema(prop_schema)
                    for prop, prop_schema in child.items()
                    if isinstance(prop_schema, dict)
                }
                continue
            out[key] = _filter_gemini_schema(child)
        return out
    if isinstance(value, list):
        return [_filter_gemini_schema(item) for item in value]
    return value


def provider_schema_variant(
    provider: str,
    model_id: str,
) -> str:
    normalized_provider = str(provider or "").strip().lower()
    normalized_model_id = str(model_id or "").strip().lower()
    if normalized_provider == "xai":
        return "xai_relaxed"
    if normalized_provider == "gemini":
        return "gemini_relaxed"
    if normalized_provider == "openrouter":
        if normalized_model_id.startswith("x-ai/"):
            return "xai_relaxed"
        if normalized_model_id.startswith("google/") or normalized_model_id.startswith(
            "gemini"
        ):
            return "gemini_relaxed"
        return "canonical"
    return "canonical"


def provider_schema_variant_label(
    provider: str,
    model_id: str,
) -> str:
    normalized_provider = str(provider or "").strip().lower()
    normalized_model_id = str(model_id or "").strip().lower()
    if normalized_provider == "xai":
        return "xai_relaxed_direct"
    if normalized_provider == "gemini":
        return "gemini_relaxed_direct"
    if normalized_provider == "openrouter":
        if normalized_model_id.startswith("x-ai/"):
            return "openrouter_proxy_xai_relaxed"
        if normalized_model_id.startswith("google/") or normalized_model_id.startswith(
            "gemini"
        ):
            return "openrouter_proxy_gemini_relaxed"
        return "openrouter_proxy_canonical"
    if normalized_provider == "openai":
        return "canonical_direct"
    return "unknown"


def adapt_canonical_schema_for_variant(
    schema: Dict[str, Any],
    *,
    variant: str,
    model_id: Optional[str] = None,
) -> Dict[str, Any]:
    canonical = copy.deepcopy(schema)
    if variant == "canonical":
        return canonical
    if variant == "xai_relaxed":
        return _strip_schema_keywords(_rewrite_const_to_enum(canonical), _XAI_STRIP_KEYWORDS)
    if variant == "gemini_relaxed":
        adapted = _filter_gemini_schema(canonical)
        normalized_model = str(model_id or "").strip().lower()
        if normalized_model.startswith("gemini-2.0") and isinstance(adapted, dict):
            properties = adapted.get("properties")
            if isinstance(properties, dict) and properties and "propertyOrdering" not in adapted:
                adapted["propertyOrdering"] = list(properties.keys())
        return adapted
    return canonical


def build_provider_structured_output(
    *,
    route: Optional[Dict[str, Any]],
    transport: Optional[str],
    schema: Optional[Dict[str, Any]] = None,
    schema_name: Optional[str] = None,
    strict: Optional[bool] = None,
    contract_lane_name: Optional[str] = None,
    schema_ids: Optional[Iterable[str]] = None,
    artifact_names: Optional[Iterable[str]] = None,
    mode: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    effective_mode = (
        normalize_structured_output_mode(mode)
        if mode is not None
        else route_structured_output_mode(route)
    )
    provider = str((route or {}).get("provider") or "").strip().lower()
    model_id = str((route or {}).get("model_id") or "").strip()
    variant_label = provider_schema_variant_label(provider, model_id)
    if effective_mode == STRUCTURED_OUTPUT_MODE_NONE:
        return None, {
            "enabled": False,
            "structured_output_mode_requested": STRUCTURED_OUTPUT_MODE_NONE,
            "structured_output_mode_effective": STRUCTURED_OUTPUT_MODE_NONE,
            "schema": None,
            "schema_name": None,
            "schema_version": None,
            "schema_variant": None,
            "provider_schema_variant": variant_label,
            "strict": bool(strict),
            "contract_lane": contract_lane_name,
            "transport_mode": None,
        }
    if effective_mode == STRUCTURED_OUTPUT_MODE_JSON_OBJECT:
        return {"type": "json_object"}, {
            "enabled": True,
            "structured_output_mode_requested": effective_mode,
            "structured_output_mode_effective": effective_mode,
            "schema": None,
            "schema_name": None,
            "schema_version": None,
            "schema_variant": None,
            "provider_schema_variant": variant_label,
            "strict": False,
            "contract_lane": contract_lane_name,
            "transport_mode": (
                "response_mime_type"
                if provider == "gemini" and str(transport or "").strip().lower() != "openai_compat_http"
                else "response_format_json_object"
            ),
        }
    if not isinstance(schema, dict) or not str(schema_name or "").strip():
        raise ValueError("json_schema mode requires schema and schema_name")
    variant = provider_schema_variant(provider, model_id)
    effective_schema = adapt_canonical_schema_for_variant(
        schema,
        variant=variant,
        model_id=model_id,
    )
    strict_flag = bool(strict)
    response_format, meta = build_json_schema_response_format(
        schema=effective_schema,
        schema_name=str(schema_name),
        strict=strict_flag,
        contract_lane_name=contract_lane_name,
        schema_names=schema_ids,
        artifact_names=artifact_names,
    )
    meta.update(
        {
            "enabled": True,
            "structured_output_mode_requested": effective_mode,
            "structured_output_mode_effective": effective_mode,
            "schema_variant": variant,
            "schema_variant_behavior": variant,
            "provider_schema_variant": variant_label,
            "transport_mode": (
                "response_json_schema"
                if provider == "gemini" and str(transport or "").strip().lower() != "openai_compat_http"
                else "response_format_json_schema"
            ),
        }
    )
    return response_format, meta


def build_provider_step_contract_output(
    *,
    route: Optional[Dict[str, Any]],
    transport: Optional[str],
    step_contract: Dict[str, Any],
    artifact_names: Optional[Iterable[str]] = None,
    schema_name_suffix: str = "draft",
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    effective_mode = route_structured_output_mode(route, step_contract=step_contract)
    if effective_mode == STRUCTURED_OUTPUT_MODE_NONE:
        return build_provider_structured_output(
            route=route,
            transport=transport,
            mode=effective_mode,
            contract_lane_name=contract_lane(step_contract),
        )
    if effective_mode == STRUCTURED_OUTPUT_MODE_JSON_OBJECT:
        return build_provider_structured_output(
            route=route,
            transport=transport,
            mode=effective_mode,
            contract_lane_name=contract_lane(step_contract),
        )
    canonical_response_format, canonical_meta = build_openai_response_format(
        step_contract,
        artifact_names=artifact_names,
        schema_name_suffix=schema_name_suffix,
        strict=bool((route or {}).get("strict_json_schema", False)),
    )
    json_schema = canonical_response_format.get("json_schema")
    schema = json_schema.get("schema") if isinstance(json_schema, dict) else None
    schema_name = json_schema.get("name") if isinstance(json_schema, dict) else None
    return build_provider_structured_output(
        route=route,
        transport=transport,
        schema=schema if isinstance(schema, dict) else None,
        schema_name=str(schema_name or ""),
        strict=bool(canonical_meta.get("strict")),
        contract_lane_name=contract_lane(step_contract),
        schema_ids=canonical_meta.get("schema_ids"),
        artifact_names=canonical_meta.get("artifact_names"),
        mode=effective_mode,
    )


def empty_payload_for_artifact(artifact_meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema": str(artifact_meta.get("canonical_schema_id") or ""),
        "items": [],
    }


def _normalize_line_range_value(value: Any) -> Any:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple) and len(value) == 2 and all(
        isinstance(part, int) for part in value
    ):
        return [int(value[0]), int(value[1])]
    if not isinstance(value, str):
        return value
    match = re.fullmatch(r"\s*(\d+)\s*[-:]\s*(\d+)\s*", value)
    if not match:
        return value
    start = int(match.group(1))
    end = int(match.group(2))
    if start <= 0 or end < start:
        return value
    return [start, end]


def _normalize_evidence_line_ranges(payload_copy: Dict[str, Any]) -> None:
    items = payload_copy.get("items")
    if not isinstance(items, list):
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        item["line_range"] = _normalize_line_range_value(item.get("line_range"))
        evidence_rows = item.get("evidence")
        if not isinstance(evidence_rows, list):
            continue
        for evidence in evidence_rows:
            if not isinstance(evidence, dict):
                continue
            evidence["line_range"] = _normalize_line_range_value(
                evidence.get("line_range")
            )


def canonicalize_artifacts(
    artifacts: List[Dict[str, Any]],
    step_contract: Optional[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    if not isinstance(step_contract, dict):
        return artifacts, []
    normalized: List[Dict[str, Any]] = []
    schema_normalizations: List[Dict[str, str]] = []
    by_artifact = step_contract.get("artifacts") if isinstance(step_contract.get("artifacts"), dict) else {}
    order = artifact_order(step_contract)
    order_index = {name: idx for idx, name in enumerate(order)}
    for row in artifacts:
        if not isinstance(row, dict):
            continue
        artifact_name = str(row.get("artifact_name") or "").strip()
        if artifact_name not in by_artifact:
            continue
        artifact_meta = by_artifact[artifact_name]
        payload = row.get("payload")
        if not isinstance(payload, dict):
            normalized.append({"artifact_name": artifact_name, "payload": payload})
            continue
        payload_copy = copy.deepcopy(payload)
        canonical_schema_id = str(artifact_meta.get("canonical_schema_id") or "")
        schema_aliases = {
            str(alias).strip().lower()
            for alias in artifact_meta.get("schema_aliases") or []
            if str(alias).strip()
        }
        if canonical_schema_id:
            schema_aliases.add(canonical_schema_id.lower())
        observed_schema_id = str(payload_copy.get("schema") or "").strip()
        if (
            observed_schema_id
            and observed_schema_id != canonical_schema_id
            and observed_schema_id.lower() in schema_aliases
        ):
            schema_normalizations.append(
                {
                    "artifact_name": artifact_name,
                    "from": observed_schema_id,
                    "to": canonical_schema_id,
                }
            )
            payload_copy["schema"] = canonical_schema_id
        elif not observed_schema_id and canonical_schema_id:
            payload_copy["schema"] = canonical_schema_id
        _normalize_evidence_line_ranges(payload_copy)
        normalized.append({"artifact_name": artifact_name, "payload": payload_copy})
    normalized.sort(key=lambda row: order_index.get(str(row.get("artifact_name") or ""), 9999))
    return normalized, schema_normalizations


def describe_contract_failure(
    artifacts: List[Dict[str, Any]],
    step_contract: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not isinstance(step_contract, dict):
        return None
    order = artifact_order(step_contract)
    observed = {
        str(row.get("artifact_name") or "").strip()
        for row in artifacts
        if isinstance(row, dict) and str(row.get("artifact_name") or "").strip()
    }
    missing = [name for name in order if name not in observed]
    if missing:
        return {
            "artifact_name": missing[0],
            "item_index": None,
            "item_id": None,
            "item_path": None,
            "failure_reason": f"missing_expected_artifacts:{','.join(missing)}",
            "missing_key": None,
            "constraint": "artifact_presence",
        }

    for row in artifacts:
        if not isinstance(row, dict):
            continue
        artifact_name = str(row.get("artifact_name") or "").strip()
        artifact_meta = artifact_contract(step_contract, artifact_name)
        payload = row.get("payload")
        if not isinstance(payload, dict):
            return {
                "artifact_name": artifact_name,
                "item_index": None,
                "item_id": None,
                "item_path": None,
                "failure_reason": "contract_payload_not_object",
                "missing_key": None,
                "constraint": "payload_object",
            }
        canonical_schema_id = str(artifact_meta.get("canonical_schema_id") or "")
        observed_schema_id = str(payload.get("schema") or "").strip()
        if not observed_schema_id:
            return {
                "artifact_name": artifact_name,
                "item_index": None,
                "item_id": None,
                "item_path": None,
                "failure_reason": "contract_missing_key:schema",
                "missing_key": "schema",
                "constraint": canonical_schema_id,
            }
        if canonical_schema_id and observed_schema_id.lower() != canonical_schema_id.lower():
            return {
                "artifact_name": artifact_name,
                "item_index": None,
                "item_id": None,
                "item_path": None,
                "failure_reason": "contract_schema_id_mismatch",
                "missing_key": None,
                "constraint": canonical_schema_id,
            }
        items = payload.get("items")
        if not isinstance(items, list):
            return {
                "artifact_name": artifact_name,
                "item_index": None,
                "item_id": None,
                "item_path": None,
                "failure_reason": "contract_items_not_list",
                "missing_key": "items",
                "constraint": "list",
            }
        required_keys = sorted(
            set(artifact_meta.get("required_fields") or []) | set(artifact_meta.get("prompt_required_item_fields") or [])
        )
        allow_empty_arrays = set(artifact_meta.get("allow_empty_array_fields") or [])
        for item_index, item in enumerate(items):
            if not isinstance(item, dict):
                return {
                    "artifact_name": artifact_name,
                    "item_index": item_index,
                    "item_id": None,
                    "item_path": None,
                    "failure_reason": "schema_item_not_object",
                    "missing_key": None,
                    "constraint": "item_object",
                }
            item_id = str(item.get("id") or "").strip() or None
            item_path = str(item.get("path") or "").strip() or None
            for key in required_keys:
                if key not in item:
                    reason = f"schema_missing_key:{key}" if key in {"id", "path", "line_range"} else f"contract_missing_key:{key}"
                    return {
                        "artifact_name": artifact_name,
                        "item_index": item_index,
                        "item_id": item_id,
                        "item_path": item_path,
                        "failure_reason": reason,
                        "missing_key": key,
                        "constraint": None,
                    }
                val = item.get(key)
                empty_vals: tuple = (None, "") if key in allow_empty_arrays else (None, "", [])
                if val in empty_vals:
                    reason = f"schema_empty_key:{key}" if key in {"id", "path", "line_range"} else f"contract_empty_key:{key}"
                    return {
                        "artifact_name": artifact_name,
                        "item_index": item_index,
                        "item_id": item_id,
                        "item_path": item_path,
                        "failure_reason": reason,
                        "missing_key": key,
                        "constraint": "non_empty",
                    }
            line_range = item.get("line_range")
            if not (
                isinstance(line_range, list)
                and len(line_range) == 2
                and all(isinstance(value, int) for value in line_range)
                and int(line_range[0]) > 0
                and int(line_range[1]) >= int(line_range[0])
            ):
                return {
                    "artifact_name": artifact_name,
                    "item_index": item_index,
                    "item_id": item_id,
                    "item_path": item_path,
                    "failure_reason": "schema_invalid_line_range",
                    "missing_key": "line_range",
                    "constraint": "line_range",
                }
    return None


def artifacts_pass_contract_gate(
    artifacts: List[Dict[str, Any]],
    step_contract: Optional[Dict[str, Any]],
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    failure = describe_contract_failure(artifacts, step_contract)
    if failure:
        return False, str(failure.get("failure_reason") or "contract_gate_failure"), failure
    return True, None, None


def normalize_required_array_fields(
    items: List[Dict[str, Any]],
    artifact_meta: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Normalize None/""/missing required array fields to [] for fields in allow_empty_array_fields.

    Returns (normalized_items, coercions_applied). Each coercion entry has keys:
    item_id, field, from_type, to_type.
    """
    allow_empty = set(artifact_meta.get("allow_empty_array_fields") or [])
    if not allow_empty:
        return items, []
    normalized: List[Dict[str, Any]] = []
    coercions: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        item_copy = dict(item)
        for field in sorted(allow_empty):
            if field not in item_copy:
                from_type = "missing"
                item_copy[field] = []
                coercions.append({"item_id": str(item.get("id") or ""), "field": field, "from_type": from_type, "to_type": "list"})
            elif item_copy[field] is None or item_copy[field] == "":
                from_type = type(item_copy[field]).__name__
                item_copy[field] = []
                coercions.append({"item_id": str(item.get("id") or ""), "field": field, "from_type": from_type, "to_type": "list"})
        normalized.append(item_copy)
    return normalized, coercions


def _is_scalar_conflict_candidate(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _artifact_item_scalar_conflicts(
    artifact_name: str,
    existing_row: Dict[str, Any],
    updated_row: Dict[str, Any],
) -> List[Dict[str, Any]]:
    existing_payload = (
        existing_row.get("payload") if isinstance(existing_row.get("payload"), dict) else {}
    )
    updated_payload = (
        updated_row.get("payload") if isinstance(updated_row.get("payload"), dict) else {}
    )
    existing_items = (
        existing_payload.get("items") if isinstance(existing_payload.get("items"), list) else None
    )
    updated_items = (
        updated_payload.get("items") if isinstance(updated_payload.get("items"), list) else None
    )
    if not isinstance(existing_items, list) or not isinstance(updated_items, list):
        return []

    existing_by_id = {
        str(item.get("id") or ""): item
        for item in existing_items
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    updated_by_id = {
        str(item.get("id") or ""): item
        for item in updated_items
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }

    conflicts: List[Dict[str, Any]] = []
    for item_id in sorted(set(existing_by_id.keys()) & set(updated_by_id.keys())):
        existing_item = existing_by_id[item_id]
        updated_item = updated_by_id[item_id]
        shared_fields = sorted(set(existing_item.keys()) & set(updated_item.keys()))
        for field in shared_fields:
            if field == "id":
                continue
            before = existing_item.get(field)
            after = updated_item.get(field)
            if not (_is_scalar_conflict_candidate(before) and _is_scalar_conflict_candidate(after)):
                continue
            if before == after:
                continue
            conflicts.append(
                {
                    "artifact_name": artifact_name,
                    "item_id": item_id,
                    "field": field,
                    "existing_value": before,
                    "updated_value": after,
                }
            )
    return conflicts


def merge_artifacts_by_name(
    artifacts: List[Dict[str, Any]],
    updates: List[Dict[str, Any]],
    step_contract: Optional[Dict[str, Any]],
    *,
    return_conflicts: bool = False,
) -> Any:
    merged: Dict[str, Dict[str, Any]] = {}
    conflicts: List[Dict[str, Any]] = []
    for row in artifacts:
        if not isinstance(row, dict):
            continue
        artifact_name = str(row.get("artifact_name") or "").strip()
        if not artifact_name:
            continue
        merged[artifact_name] = copy.deepcopy(row)
    for row in updates:
        if not isinstance(row, dict):
            continue
        artifact_name = str(row.get("artifact_name") or "").strip()
        if not artifact_name:
            continue
        if artifact_name in merged:
            conflicts.extend(
                _artifact_item_scalar_conflicts(artifact_name, merged[artifact_name], row)
            )
        merged[artifact_name] = copy.deepcopy(row)
    if not isinstance(step_contract, dict):
        rows = [merged[name] for name in sorted(merged.keys())]
        return (rows, conflicts) if return_conflicts else rows
    order = artifact_order(step_contract)
    rows = [merged[name] for name in order if name in merged]
    extra = [merged[name] for name in sorted(merged.keys()) if name not in set(order)]
    merged_rows = rows + extra
    return (merged_rows, conflicts) if return_conflicts else merged_rows


def dump_response_format_json(response_format: Dict[str, Any]) -> str:
    return json.dumps(response_format, indent=2, sort_keys=True, ensure_ascii=True)
