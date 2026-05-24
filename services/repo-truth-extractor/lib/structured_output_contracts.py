from __future__ import annotations

import copy
import hashlib
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
    """Return normalized route rows for the given stage.

    Each row contains: provider, model_id, api_key_env, structured_output_mode,
    strict_json_schema, strict_passthrough_verified, service_tier, and optional
    context_window.

    service_tier is copied through from the raw row when present (string token
    like "default" / "flex" / "priority" / "auto") and defaults to None when
    absent. Callers that don't consume service_tier are unaffected.

    E8 (v3 awareness): if the step_contract carries v3-only fields under
    ``lane.tags`` (and optionally ``lane.tag_definitions``), the function
    applies tag-driven routing deltas defensively after the v2-shape route
    list is materialized — preserving the critical-safety invariant when
    ``lane.impact_class`` is structural or security_sensitive. Callers that
    do not propagate these fields see unchanged behavior.
    """
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
        raw_service_tier = row.get("service_tier")
        service_tier = (
            str(raw_service_tier).strip()
            if isinstance(raw_service_tier, str) and str(raw_service_tier).strip()
            else None
        )
        normalized = {
            "provider": provider,
            "model_id": model_id,
            "api_key_env": api_key_env,
            "structured_output_mode": route_structured_output_mode(
                row,
                step_contract=step_contract,
            ),
            "strict_json_schema": bool(row.get("strict_json_schema", False)),
            "strict_passthrough_verified": bool(row.get("strict_passthrough_verified", False)),
            "service_tier": service_tier,
        }
        context_window = _route_context_window(row)
        if context_window is not None:
            normalized["context_window"] = context_window
        out.append(normalized)

    # E8 v3 tag-delta hook: activates ONLY when the caller has propagated
    # BOTH `lane.tags` (non-empty list) AND `lane.tag_definitions` (mapping)
    # into the step_contract. Requiring both fields makes activation explicit
    # and prevents silent partial behavior.
    tags = lane.get("tags")
    tag_definitions = lane.get("tag_definitions")
    if (
        isinstance(tags, list) and tags
        and isinstance(tag_definitions, dict) and tag_definitions
    ):
        impact_class = lane.get("impact_class")
        out = apply_tag_routing_delta(
            out,
            tags=tags,
            tag_definitions=tag_definitions,
            impact_class=str(impact_class).strip().lower() if isinstance(impact_class, str) else None,
        )
    return out


def apply_tag_routing_delta(
    routes: List[Dict[str, Any]],
    *,
    tags: List[str],
    tag_definitions: Optional[Dict[str, Any]] = None,
    impact_class: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Apply v3 tag-driven routing deltas to a route list.

    Each tag's ``routing_delta`` (as authored in v3 ``tag_definitions``) is
    interpreted defensively:

    * ``filter_provider``               → drop routes whose provider does
                                          not match.
    * ``filter_supports_json_schema_strict`` → drop routes where
                                          ``strict_json_schema`` is false.
    * ``filter_route_context_window_min`` → drop routes whose context_window
                                          is absent or below the minimum.
                                          Optional ``fallback_routes`` are
                                          explicit replacement candidates
                                          used only when the current route
                                          list has no satisfying route.
    * ``temperature_override``         → no-op at the route-list layer;
                                          downstream callers consume the
                                          tag via the step_contract.
    * ``route_allowlist`` (sequence)   → keep only routes whose
                                          provider-qualified identity or
                                          ``model_id`` matches one of the
                                          glob-like patterns (``*`` only).

    Critical-safety invariants for structural/security_sensitive steps:
      (1) If a non-empty candidate list would drop every strict-capable
          route while the pre-state had one, skip that delta.
      (2) If a hard filter produces zero candidates, fail closed with the
          empty list rather than silently keeping routes that violate the tag
          unless an explicit context-window fallback route satisfies the
          active filter.
    """
    if not routes:
        return list(routes)
    deltas: List[Dict[str, Any]] = []
    if isinstance(tag_definitions, dict):
        for tag in tags:
            entry = tag_definitions.get(tag)
            if not isinstance(entry, dict):
                continue
            delta = entry.get("routing_delta")
            if isinstance(delta, dict):
                deltas.append(delta)
    if not deltas:
        return list(routes)

    critical = impact_class in ("structural", "security_sensitive")

    def _retains_strict_capable(candidate: List[Dict[str, Any]]) -> bool:
        return any(bool(r.get("strict_json_schema")) for r in candidate)

    out: List[Dict[str, Any]] = list(routes)
    for delta in deltas:
        filtered = list(out)
        prov = delta.get("filter_provider")
        if isinstance(prov, str) and prov:
            filtered = [r for r in filtered if str(r.get("provider", "")).lower() == prov.lower()]
        if delta.get("filter_supports_json_schema_strict") is True:
            filtered = [r for r in filtered if bool(r.get("strict_json_schema"))]
        context_window_min = _positive_int(delta.get("filter_route_context_window_min"))
        if context_window_min is not None:
            filtered = [
                r
                for r in filtered
                if (_route_context_window(r) or 0) >= context_window_min
            ]
            if not filtered:
                filtered = [
                    r
                    for r in _normalized_fallback_routes(delta.get("fallback_routes"))
                    if (_route_context_window(r) or 0) >= context_window_min
                ]
        allowlist = delta.get("route_allowlist")
        if isinstance(allowlist, list) and allowlist:
            filtered = [
                r for r in filtered
                if any(
                    _route_matches_pattern(candidate, pat)
                    for candidate in _route_allowlist_candidates(r)
                    for pat in allowlist
                    if isinstance(pat, str)
                )
            ]
        # Critical-safety: if the candidate would drop all strict-capable
        # routes AND the step is structural/security_sensitive, refuse the
        # delta application (keep prior state). Empty filtered lists are
        # different: hard filters must fail closed rather than preserving
        # routes that violate tag intent.
        if filtered and critical and not _retains_strict_capable(filtered) and _retains_strict_capable(out):
            continue
        out = filtered
    return out


def _positive_int(value: Any) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _route_context_window(route: Dict[str, Any]) -> Optional[int]:
    for key in ("context_window", "context_window_tokens"):
        parsed = _positive_int(route.get(key))
        if parsed is not None:
            return parsed
    return None


def _normalized_fallback_routes(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        return []
    rows: List[Dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict):
            continue
        provider = str(row.get("provider") or "").strip().lower()
        model_id = str(row.get("model_id") or "").strip()
        api_key_env = str(row.get("api_key_env") or "").strip()
        if not (provider and model_id and api_key_env):
            continue
        strict_json_schema = bool(row.get("strict_json_schema", False))
        raw_mode = normalize_structured_output_mode(row.get("structured_output_mode"))
        structured_output_mode = raw_mode
        if raw_mode == STRUCTURED_OUTPUT_MODE_NONE and strict_json_schema:
            structured_output_mode = STRUCTURED_OUTPUT_MODE_JSON_SCHEMA
        raw_service_tier = row.get("service_tier")
        normalized = {
            "provider": provider,
            "model_id": model_id,
            "api_key_env": api_key_env,
            "structured_output_mode": structured_output_mode,
            "strict_json_schema": strict_json_schema,
            "strict_passthrough_verified": bool(row.get("strict_passthrough_verified", False)),
            "service_tier": (
                str(raw_service_tier).strip()
                if isinstance(raw_service_tier, str) and str(raw_service_tier).strip()
                else None
            ),
        }
        context_window = _route_context_window(row)
        if context_window is not None:
            normalized["context_window"] = context_window
        rows.append(normalized)
    return rows


def _route_allowlist_candidates(route: Dict[str, Any]) -> List[str]:
    model_id = str(route.get("model_id", "")).strip()
    provider = str(route.get("provider", "")).strip()
    candidates = []
    if model_id:
        candidates.append(model_id)
    if provider and model_id:
        candidates.append(f"{provider}/{model_id}")
    return candidates


def _route_matches_pattern(model_id: str, pattern: str) -> bool:
    """Match a model_id against an allowlist glob (only ``*`` wildcard)."""
    if not pattern:
        return False
    if "*" not in pattern:
        return model_id == pattern
    parts = pattern.split("*")
    cursor = 0
    if not pattern.startswith("*") and not model_id.startswith(parts[0]):
        return False
    if not pattern.endswith("*") and not model_id.endswith(parts[-1]):
        return False
    for part in parts:
        if not part:
            continue
        idx = model_id.find(part, cursor)
        if idx < 0:
            return False
        cursor = idx + len(part)
    return True


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


_CACHE_STRATEGIES: Set[str] = {"auto", "cache_control_explicit", "none"}
_ANTHROPIC_CACHE_MARKER_LIMIT: int = 4
ANTHROPIC_TOOL_USE_UNWIRED_REASON = "anthropic_tool_use_transport_unwired"


def _is_anthropic_cache_target(provider: str, model_id: str) -> bool:
    if provider == "anthropic":
        return True
    if provider == "openrouter" and model_id.startswith("anthropic/"):
        return True
    return False


def _is_anthropic_tool_use_target(provider: str, model_id: str) -> bool:
    if provider == "anthropic":
        return True
    if provider == "openrouter" and model_id.startswith("anthropic/"):
        return True
    return False


def _is_openai_cache_target(provider: str, model_id: str) -> bool:
    if provider == "openai":
        return True
    # OpenRouter routes that are NOT anthropic/gemini/xai pass through to OpenAI-compatible providers.
    if provider == "openrouter" and not (
        model_id.startswith("anthropic/")
        or model_id.startswith("google/")
        or model_id.startswith("gemini")
        or model_id.startswith("x-ai/")
    ):
        return True
    return False


def prompt_caching_directives_for_provider(
    provider: str,
    model_id: str,
    *,
    prompt_text_lengths: Optional[Iterable[int]] = None,
    cache_strategy: str = "auto",
    auto_cache_enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    """Return provider-appropriate prompt-cache directives.

    Anthropic (direct or via OpenRouter `anthropic/*`) gets `cache_control_markers`
    capped at 4 (Anthropic API limit). OpenAI-compatible routes get a stable
    `prompt_cache_key` derived from a deterministic hash of provider + model +
    prefix-length structure. Gemini gets a `cached_content_name` only under
    explicit opt-in (`cache_strategy='cache_control_explicit'`); under the default
    `'auto'` strategy Gemini relies on its implicit cache and no directive is
    emitted.

    Behavior matrix:
      * `cache_strategy='none'`            → always applied=False, strategy='none'
      * `cache_strategy='auto'` + `auto_cache_enabled` falsy → applied=False
      * `cache_strategy='auto'` + `auto_cache_enabled=True`  → emit per provider
      * `cache_strategy='cache_control_explicit'`             → emit per provider
        (Gemini honors this; other providers treat it like enabled-auto.)

    The returned dict shape is stable: every key is always present. The function
    is pure (no IO, no provider calls) and deterministic for fixed inputs.
    """
    normalized_provider = str(provider or "").strip().lower()
    normalized_model = str(model_id or "").strip().lower()
    none_result: Dict[str, Any] = {
        "cache_control_markers": [],
        "prompt_cache_key": None,
        "cached_content_name": None,
        "applied": False,
        "strategy": "none",
    }
    strategy = str(cache_strategy or "").strip().lower()
    if strategy not in _CACHE_STRATEGIES:
        return dict(none_result)
    if strategy == "none":
        return dict(none_result)
    if strategy == "auto" and not bool(auto_cache_enabled):
        return dict(none_result)

    lengths_list: List[int] = []
    if prompt_text_lengths is not None:
        for raw_len in prompt_text_lengths:
            try:
                parsed = int(raw_len)
            except (TypeError, ValueError):
                continue
            if parsed <= 0:
                continue
            lengths_list.append(parsed)

    if _is_anthropic_cache_target(normalized_provider, normalized_model):
        if lengths_list:
            # Anthropic best practice (per packet S4): cache_control on the LAST
            # ~K message blocks of the stable prefix — i.e. the blocks closest
            # to the mutable tail (typically the final user query). Markers act
            # as cache breakpoints meaning "everything up to and including this
            # block is cacheable"; placing them at the end of the stable prefix
            # maximizes the cache hit rate. Cap at the Anthropic API limit of 4.
            count = min(_ANTHROPIC_CACHE_MARKER_LIMIT, max(1, len(lengths_list) - 1))
            # Index window: [start, start+count) where start leaves the final
            # block (the mutable tail) unmarked when there's more than one block.
            start = max(0, len(lengths_list) - 1 - count)
        else:
            # No prefix structure provided: mark a single ephemeral checkpoint
            # at block_index 0 so callers still benefit from the system prefix
            # being cached.
            count = 1
            start = 0
        markers = [
            {"type": "ephemeral", "block_index": start + offset}
            for offset in range(count)
        ]
        return {
            "cache_control_markers": markers,
            "prompt_cache_key": None,
            "cached_content_name": None,
            "applied": True,
            "strategy": strategy,
        }

    if _is_openai_cache_target(normalized_provider, normalized_model):
        seed_parts = [normalized_provider, normalized_model]
        if lengths_list:
            seed_parts.append(",".join(str(length) for length in lengths_list))
        cache_key = hashlib.sha256(":".join(seed_parts).encode("utf-8")).hexdigest()[:32]
        return {
            "cache_control_markers": [],
            "prompt_cache_key": cache_key,
            "cached_content_name": None,
            "applied": True,
            "strategy": strategy,
        }

    if normalized_provider == "gemini" or (
        normalized_provider == "openrouter"
        and (normalized_model.startswith("google/") or normalized_model.startswith("gemini"))
    ):
        if strategy != "cache_control_explicit":
            # Implicit cache is automatic; no per-request directive is needed.
            return dict(none_result)
        return {
            "cache_control_markers": [],
            "prompt_cache_key": None,
            "cached_content_name": f"cached/{normalized_model}/explicit",
            "applied": True,
            "strategy": strategy,
        }

    # Unknown provider — fail closed: emit no directive rather than guess.
    return dict(none_result)


def strict_capability_reason(
    route: Optional[Dict[str, Any]],
    transport: Optional[str],
) -> Optional[str]:
    if not isinstance(route, dict):
        return "route_missing"
    if not bool(route.get("strict_json_schema", False)):
        return "strict_json_schema_disabled"
    provider = str(route.get("provider") or "").strip().lower()
    model_id = str(route.get("model_id") or "").strip().lower()
    transport_mode = str(transport or "").strip().lower()
    if provider == "openrouter" and not bool(route.get("strict_passthrough_verified", False)):
        return "openrouter_strict_passthrough_unverified"
    if (
        route_structured_output_mode(route) == STRUCTURED_OUTPUT_MODE_JSON_SCHEMA
        and _is_anthropic_tool_use_target(provider, model_id)
    ):
        return ANTHROPIC_TOOL_USE_UNWIRED_REASON
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
    model_id = str(route.get("model_id") or "").strip().lower()
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
    if _is_anthropic_tool_use_target(provider, model_id):
        return ANTHROPIC_TOOL_USE_UNWIRED_REASON
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
    if normalized_provider == "anthropic":
        return "anthropic_tool_use"
    if normalized_provider == "openrouter":
        if normalized_model_id.startswith("x-ai/"):
            return "xai_relaxed"
        if normalized_model_id.startswith("google/") or normalized_model_id.startswith(
            "gemini"
        ):
            return "gemini_relaxed"
        if normalized_model_id.startswith("anthropic/"):
            return "anthropic_tool_use"
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
    if normalized_provider == "anthropic":
        return "anthropic_tool_use_direct"
    if normalized_provider == "openrouter":
        if normalized_model_id.startswith("x-ai/"):
            return "openrouter_proxy_xai_relaxed"
        if normalized_model_id.startswith("google/") or normalized_model_id.startswith(
            "gemini"
        ):
            return "openrouter_proxy_gemini_relaxed"
        if normalized_model_id.startswith("anthropic/"):
            return "openrouter_proxy_anthropic_tool_use"
        return "openrouter_proxy_canonical"
    if normalized_provider == "openai":
        return "canonical_direct"
    return "unknown"


def adapt_canonical_schema_for_variant(
    schema: Dict[str, Any],
    *,
    variant: str,
    model_id: Optional[str] = None,
    schema_name: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """Adapt a canonical JSON Schema for a specific provider variant.

    For the legacy three variants (`canonical`, `xai_relaxed`, `gemini_relaxed`)
    the return shape is the JSON Schema dict (possibly with provider-specific
    keyword rewrites or stripping).

    For `anthropic_tool_use` the return shape is an Anthropic tool definition
    dict: `{name, description, input_schema}`. Callers must therefore inspect
    the returned shape based on variant (the top-level keys differ).
    `schema_name` is required when `variant == 'anthropic_tool_use'`; missing
    or blank names raise `ValueError`. A stable fallback name of
    `'emit_canonical'` is used only if sanitizing a non-empty schema_name strips
    every character. The function never mutates `schema`.
    """
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
    if variant == "anthropic_tool_use":
        # schema_name is required for tool_use: the tool definition must be
        # named so the model knows which tool to invoke. Fail closed rather
        # than silently substituting a default that risks tool-choice collisions
        # across schemas.
        if not str(schema_name or "").strip():
            raise ValueError(
                "anthropic_tool_use variant requires non-empty schema_name"
            )
        # Anthropic tool_use input_schema must be a top-level object schema.
        # The canonical schemas this module produces are already top-level
        # `{"type": "object", ...}` so the input_schema is canonical verbatim;
        # we only defensively coerce when an external caller supplies something
        # else (e.g. an `anyOf` root) by wrapping it under `properties._root_`.
        if isinstance(canonical, dict) and canonical.get("type") == "object":
            input_schema = canonical
        else:
            # Guard against non-dict canonical (type hints say dict but be defensive):
            # the `_root_` property must itself be a valid JSON Schema dict.
            root_schema = canonical if isinstance(canonical, dict) else {"type": "string"}
            input_schema = {
                "type": "object",
                "properties": {"_root_": root_schema},
                "required": ["_root_"],
                "additionalProperties": False,
            }
        raw_name = str(schema_name).strip()
        # Anthropic tool names must match ^[a-zA-Z0-9_-]{1,64}$. Strip disallowed
        # chars then cap to 60 so we have room for an 'emit_' prefix.
        safe_name = re.sub(r"[^A-Za-z0-9_-]", "_", raw_name)[:60] or "emit_canonical"
        # Prefix check is case-insensitive so callers that pass 'EMIT_X' or
        # 'Emit_x' don't get double-prefixed to 'emit_EMIT_X'.
        tool_name = (
            safe_name if safe_name.lower().startswith("emit_") else f"emit_{safe_name}"
        )
        tool_name = tool_name[:64]
        # Description goes into the model's tool definition. Collapse whitespace
        # and truncate to keep the description single-line and bounded — defense
        # against accidentally embedding multi-line config noise or unbounded names.
        if isinstance(description, str) and str(description).strip():
            tool_description = re.sub(r"\s+", " ", str(description).strip())[:240]
        else:
            safe_raw_name_for_desc = re.sub(r"\s+", " ", raw_name)[:120]
            tool_description = (
                f"Emit the {safe_raw_name_for_desc} structured artifact."
            )
        return {
            "name": tool_name,
            "description": tool_description,
            "input_schema": input_schema,
        }
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
    allow_anthropic_tool_use_payload: bool = False,
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """Build a provider-appropriate structured-output payload + meta.

    For OpenAI / OpenRouter / xAI / Gemini routes the first tuple element is a
    standard OpenAI-style `response_format` dict (`{"type": "json_schema", ...}`
    or `{"type": "json_object"}`) or `None` when structured output is disabled.

    Anthropic / OpenRouter+anthropic routes use a non-response_format payload
    shape (`tools` + `tool_choice`). E3 keeps that branch default-off because
    current runtime callers still serialize the first tuple element under
    `response_format`. Only callers that already know how to put those fields
    at the wire-request top level may pass `allow_anthropic_tool_use_payload=True`.
    """
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

    if variant == "anthropic_tool_use":
        if not allow_anthropic_tool_use_payload:
            raise ValueError(
                "anthropic_tool_use payload not wired for current response_format callers"
            )
        # Anthropic tool_use doesn't use OpenAI/Gemini's `response_format` field.
        # Instead the request carries `tools=[...]` + `tool_choice={"type":"tool","name":...}`.
        # Return that shape only after an explicit caller opt-in and tag the meta
        # so a wired runtime can route it correctly.
        tool_def = adapt_canonical_schema_for_variant(
            schema,
            variant=variant,
            model_id=model_id,
            schema_name=str(schema_name),
        )
        anthropic_payload = {
            "tools": [tool_def],
            "tool_choice": {"type": "tool", "name": tool_def["name"]},
        }
        meta = {
            "enabled": True,
            "structured_output_mode_requested": effective_mode,
            "structured_output_mode_effective": effective_mode,
            "schema": str(schema_name),
            "schema_name": str(schema_name),
            "schema_version": "v1",
            "strict": bool(strict),
            "contract_lane": contract_lane_name,
            "schema_ids": list(schema_ids or []),
            "artifact_names": list(artifact_names or []),
            "schema_variant": variant,
            "schema_variant_behavior": variant,
            "provider_schema_variant": variant_label,
            "transport_mode": "anthropic_tool_use",
            "anthropic_tool_use_payload": anthropic_payload,
        }
        return anthropic_payload, meta

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
