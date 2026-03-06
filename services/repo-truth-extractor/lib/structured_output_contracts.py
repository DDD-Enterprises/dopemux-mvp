from __future__ import annotations

import copy
import json
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


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
        out.append(
            {
                "provider": provider,
                "model_id": model_id,
                "api_key_env": api_key_env,
                "strict_json_schema": bool(row.get("strict_json_schema", False)),
                "strict_passthrough_verified": bool(row.get("strict_passthrough_verified", False)),
            }
        )
    return out


def route_for_contract(step_contract: Optional[Dict[str, Any]]) -> Optional[Tuple[str, str, str]]:
    rows = route_entries_for_stage(step_contract, "primary")
    if not rows:
        return None
    row = rows[0]
    return (str(row["provider"]), str(row["model_id"]), str(row["api_key_env"]))


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
        attempts.append(
            {
                "provider": provider,
                "model_id": str(route["model_id"]),
                "api_key_env": str(route["api_key_env"]),
                "transport": transport,
                "strict_json_schema": bool(route.get("strict_json_schema", False)),
                "strict_passthrough_verified": bool(route.get("strict_passthrough_verified", False)),
                "strict_capable": strict_capable,
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
    return {
        "type": "object",
        "required": required_keys,
        "properties": properties,
        "additionalProperties": False,
    }


def build_openai_response_format(
    step_contract: Dict[str, Any],
    artifact_names: Optional[Iterable[str]] = None,
    schema_name_suffix: str = "draft",
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
    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "strict": True,
            "schema": schema,
        },
    }
    meta = {
        "schema": schema_name,
        "schema_name": schema_name,
        "schema_version": "v1",
        "strict": True,
        "contract_lane": contract_lane(step_contract),
        "schema_ids": schema_names,
        "artifact_names": ordered_artifacts,
    }
    return response_format, meta


def empty_payload_for_artifact(artifact_meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema": str(artifact_meta.get("canonical_schema_id") or ""),
        "items": [],
    }


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
        observed_schema_id = str(payload_copy.get("schema") or "").strip()
        if observed_schema_id and observed_schema_id != canonical_schema_id and observed_schema_id.lower() == canonical_schema_id.lower():
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
                if item.get(key) in (None, "", []):
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


def merge_artifacts_by_name(
    artifacts: List[Dict[str, Any]],
    updates: List[Dict[str, Any]],
    step_contract: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
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
        merged[artifact_name] = copy.deepcopy(row)
    if not isinstance(step_contract, dict):
        return [merged[name] for name in sorted(merged.keys())]
    order = artifact_order(step_contract)
    rows = [merged[name] for name in order if name in merged]
    extra = [merged[name] for name in sorted(merged.keys()) if name not in set(order)]
    return rows + extra


def dump_response_format_json(response_format: Dict[str, Any]) -> str:
    return json.dumps(response_format, indent=2, sort_keys=True, ensure_ascii=True)
