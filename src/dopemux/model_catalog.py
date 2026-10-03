"""Deterministic PAL projections derived from Dopemux routing/catalog data."""

from __future__ import annotations

import json
from typing import Any, Dict


PAL_CAPABILITY_FIELDS = {
    "aliases",
    "allow_code_generation",
    "context_window",
    "default_reasoning_effort",
    "description",
    "friendly_name",
    "intelligence_score",
    "max_image_size_mb",
    "max_output_tokens",
    "max_thinking_tokens",
    "model_name",
    "supports_extended_thinking",
    "supports_function_calling",
    "supports_images",
    "supports_json_mode",
    "supports_streaming",
    "supports_system_prompts",
    "supports_temperature",
    "use_openai_response_api",
}


def _enabled(entry: Dict[str, Any]) -> bool:
    return entry.get("enabled", True) is True


def _pal_entry(
    *,
    model_name: str,
    aliases: list[str],
    capabilities: Dict[str, Any],
    description: str,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "model_name": model_name,
        "aliases": sorted(set(aliases)),
        "friendly_name": model_name,
        "description": description,
    }
    for field in PAL_CAPABILITY_FIELDS - {
        "aliases",
        "description",
        "friendly_name",
        "model_name",
    }:
        if field in capabilities:
            entry[field] = capabilities[field]
    return entry


def _active_route_overrides(routing: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    providers = {
        provider["name"]: provider for provider in routing.get("providers", [])
    }
    overrides: Dict[str, Dict[str, Any]] = {}
    for model in routing.get("models", []):
        pal = model.get("pal")
        provider = providers.get(model.get("provider"), {})
        if not isinstance(pal, dict) or not _enabled(model) or not _enabled(provider):
            continue
        direct_name = pal.get("direct_model_name")
        if direct_name:
            overrides[str(direct_name)] = pal
    return overrides


def _description(model_name: str, pal: Dict[str, Any], projection: str) -> str:
    text = f"Dopemux-generated {projection} PAL catalog entry for {model_name}."
    if pal.get("thinking_mode") == "always_on":
        text += " Thinking always on; reasoning effort low/high/max."
    elif pal.get("thinking_mode") == "adaptive_always_on":
        text += " Adaptive thinking always on; manual disable/budget route unsupported."
    return text


def build_pal_manifest(
    routing: Dict[str, Any],
    cheaperinference_snapshot: Dict[str, Any],
    *,
    projection: str,
) -> Dict[str, Any]:
    """Build direct-CI or gateway PAL manifest from repo-owned catalog inputs."""
    if projection not in {"compatibility", "direct-ci", "gateway"}:
        raise ValueError(f"Unsupported PAL projection: {projection}")

    models: list[Dict[str, Any]] = []
    if projection in {"compatibility", "direct-ci"}:
        overrides = _active_route_overrides(routing)
        for observed in cheaperinference_snapshot.get("data", []):
            if observed.get("type") != "text" or not observed.get("id"):
                continue
            model_name = str(observed["id"])
            observed_capabilities = observed.get("capabilities") or {}
            pal = overrides.get(model_name, {})
            capabilities = {
                "supports_extended_thinking": bool(
                    observed_capabilities.get("reasoning", False)
                ),
                "supports_images": bool(observed_capabilities.get("vision", False)),
                "supports_streaming": bool(
                    observed_capabilities.get("streaming", False)
                ),
                "supports_function_calling": False,
                "supports_json_mode": False,
                "max_image_size_mb": (
                    40.0 if observed_capabilities.get("vision", False) else 0.0
                ),
            }
            capabilities.update(
                {
                    key: value
                    for key, value in pal.items()
                    if key in PAL_CAPABILITY_FIELDS
                }
            )
            models.append(
                _pal_entry(
                    model_name=model_name,
                    aliases=list(observed.get("aliases") or []),
                    capabilities=capabilities,
                    description=_description(model_name, pal, projection),
                )
            )
        if projection == "compatibility":
            by_name = {entry["model_name"]: entry for entry in models}
            for raw in routing.get("pal_compatibility_models", []):
                entry = {
                    key: deepcopy_value
                    for key, deepcopy_value in raw.items()
                    if key in PAL_CAPABILITY_FIELDS
                }
                if not entry.get("model_name"):
                    continue
                entry.setdefault("aliases", [])
                entry.setdefault("friendly_name", entry["model_name"])
                by_name[str(entry["model_name"])] = entry
            models = list(by_name.values())
    else:
        providers = {
            provider["name"]: provider for provider in routing.get("providers", [])
        }
        for model in routing.get("models", []):
            provider = providers.get(model.get("provider"), {})
            pal = model.get("pal")
            if not isinstance(pal, dict) or not _enabled(model) or not _enabled(provider):
                continue
            models.append(
                _pal_entry(
                    model_name=str(model["name"]),
                    aliases=list(pal.get("aliases") or []),
                    capabilities=pal,
                    description=_description(str(model["name"]), pal, projection),
                )
            )

    models.sort(key=lambda entry: entry["model_name"])
    return {
        "_README": {
            "authority": "Dopemux routing catalog",
            "generator": "scripts/generate_pal_model_manifest.py",
            "projection": projection,
        },
        "models": models,
    }


def render_pal_manifest(manifest: Dict[str, Any]) -> bytes:
    """Serialize manifest with stable ordering and newline."""
    return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
