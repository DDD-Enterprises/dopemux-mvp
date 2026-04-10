from __future__ import annotations

import json
import importlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import PrescanConfig

try:
    from ..spend_ledger import get_model_cost_rate
except ImportError:  # pragma: no cover - fallback only when imported out of tree
    get_model_cost_rate = None

SANCTIONED_PROVIDERS = ("openai", "gemini", "xai", "openrouter")
PRESCAN_PASS_ORDER = ("dedup", "discover", "feasibility", "optimize")
PRESCAN_TIER_RANK = {
    "cheap_structured": 1,
    "balanced_analysis": 2,
    "premium_planning": 3,
}
PRESCAN_PASS_REQUIREMENTS = {
    "dedup": "cheap_structured",
    "discover": "cheap_structured",
    "feasibility": "balanced_analysis",
    "optimize": "premium_planning",
}


def _load_runner_authority() -> tuple[dict[str, dict[str, list[tuple[str, str, str]]]], dict[str, str]]:
    runner = importlib.import_module("run_extraction_v5")
    ladders = getattr(runner, "ACTIVE_ROUTING_LADDERS", {}) or {}
    provider_env = getattr(runner, "PROVIDER_API_KEY_ENV", {}) or {}
    return ladders, provider_env


def _iter_runner_routes() -> Iterable[tuple[str, str, str, str, str]]:
    ladders, _provider_env = _load_runner_authority()
    for policy, tiers in sorted(ladders.items()):
        if not isinstance(tiers, dict):
            continue
        for tier_name, routes in sorted(tiers.items()):
            if not isinstance(routes, list):
                continue
            for route in routes:
                if not isinstance(route, (list, tuple)) or len(route) != 3:
                    continue
                provider, model_id, api_key_env = (str(route[0]), str(route[1]), str(route[2]))
                if provider not in SANCTIONED_PROVIDERS or not model_id or not api_key_env:
                    continue
                yield policy, tier_name, provider, model_id, api_key_env


def classify_prescan_route(provider: str, model_id: str) -> str:
    token = str(model_id or "").strip().lower()
    provider_token = str(provider or "").strip().lower()
    if not token:
        return "balanced_analysis"
    premium_markers = (
        "claude-opus",
        "opus-4-6",
        "gpt-5.4",
        "gpt-5-pro",
        "gpt-5.3-codex",
        "gpt-5.2",
        "gpt-5.1-codex",
        "gemini-3.1-pro",
        "gemini-2.5-pro",
        "reasoning",
    )
    cheap_markers = (
        "gpt-5-nano",
        "gpt-4.1-nano",
        "gpt-4o-mini",
        "gemini-2.5-flash",
        "gemini-3-flash",
        "grok-code-fast",
        "fast-non-reasoning",
    )
    if any(marker in token for marker in premium_markers):
        return "premium_planning"
    if any(marker in token for marker in cheap_markers):
        return "cheap_structured"
    if provider_token == "gemini" and "flash" in token:
        return "cheap_structured"
    return "balanced_analysis"


def _pricing(provider: str, model_id: str) -> dict[str, Any]:
    if get_model_cost_rate is None:
        input_1m = 10.0
        output_1m = 40.0
        authority = "fallback_default"
    else:
        rate = get_model_cost_rate(provider=provider, model_id=model_id)
        input_1m = rate.get("input_cost_per_1m_usd", 10.0)
        output_1m = rate.get("output_cost_per_1m_usd", 40.0)
        authority = "shared_spend_ledger_registry"
    return {
        "input_1m_usd": float(input_1m),
        "output_1m_usd": float(output_1m),
        "pricing_authority": authority,
    }


def build_provider_model_catalog(config: PrescanConfig) -> dict[str, Any]:
    seen: dict[tuple[str, str, str], dict[str, Any]] = {}
    for policy, ladder_tier, provider, model_id, api_key_env in _iter_runner_routes():
        key = (provider, model_id, api_key_env)
        entry = seen.setdefault(
            key,
            {
                "provider": provider,
                "model_id": model_id,
                "api_key_env": api_key_env,
                "available": bool(os.environ.get(api_key_env, "").strip()),
                "availability_reason": (
                    "credential_present"
                    if os.environ.get(api_key_env, "").strip()
                    else "missing_credential"
                ),
                "prescan_tier": classify_prescan_route(provider, model_id),
                "pricing": _pricing(provider, model_id),
                "sources": [],
                "execution_transport": "openai_sdk_compatible",
            },
        )
        source = {"policy": policy, "ladder_tier": ladder_tier}
        if source not in entry["sources"]:
            entry["sources"].append(source)

    if config.provider in SANCTIONED_PROVIDERS and config.model and config.api_key_env:
        key = (config.provider, config.model, config.api_key_env)
        entry = seen.setdefault(
            key,
            {
                "provider": config.provider,
                "model_id": config.model,
                "api_key_env": config.api_key_env,
                "available": bool(os.environ.get(config.api_key_env, "").strip()),
                "availability_reason": (
                    "credential_present"
                    if os.environ.get(config.api_key_env, "").strip()
                    else "missing_credential"
                ),
                "prescan_tier": classify_prescan_route(config.provider, config.model),
                "pricing": _pricing(config.provider, config.model),
                "sources": [],
                "execution_transport": "openai_sdk_compatible",
            },
        )
        source = {"policy": "legacy_prescan_config", "ladder_tier": "legacy_default"}
        if source not in entry["sources"]:
            entry["sources"].append(source)

    rows = []
    for provider, model_id, api_key_env in sorted(seen):
        row = dict(seen[(provider, model_id, api_key_env)])
        row["sources"] = sorted(
            row["sources"],
            key=lambda item: (str(item.get("policy")), str(item.get("ladder_tier"))),
        )
        rows.append(row)
    return {
        "generated_from": "run_extraction_v5.ACTIVE_ROUTING_LADDERS",
        "sanctioned_providers": list(SANCTIONED_PROVIDERS),
        "routes": rows,
    }


def _select_route_for_tier(
    routes: list[dict[str, Any]],
    required_tier: str,
) -> tuple[dict[str, Any] | None, str | None]:
    required_rank = PRESCAN_TIER_RANK[required_tier]
    eligible = [
        route
        for route in routes
        if PRESCAN_TIER_RANK.get(str(route.get("prescan_tier")), 0) >= required_rank
    ]
    if not eligible:
        return None, None
    eligible.sort(
        key=lambda row: (
            PRESCAN_TIER_RANK.get(str(row.get("prescan_tier")), 99),
            float(((row.get("pricing") or {}).get("input_1m_usd", 999.0))),
            float(((row.get("pricing") or {}).get("output_1m_usd", 999.0))),
            str(row.get("provider") or ""),
            str(row.get("model_id") or ""),
        )
    )
    selected = eligible[0]
    selected_tier = str(selected.get("prescan_tier"))
    adjustment = "exact" if selected_tier == required_tier else "upgrade"
    return selected, adjustment


def build_prescan_routing_plan(
    config: PrescanConfig,
    catalog: dict[str, Any],
    passes: list[str] | None,
) -> dict[str, Any]:
    requested_passes = [
        pass_id for pass_id in (passes or []) if pass_id in PRESCAN_PASS_REQUIREMENTS
    ]
    routes = [
        row
        for row in catalog.get("routes", [])
        if isinstance(row, dict) and bool(row.get("available"))
    ]
    selected_routes: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    for pass_id in requested_passes:
        required_tier = PRESCAN_PASS_REQUIREMENTS[pass_id]
        selected, adjustment = _select_route_for_tier(routes, required_tier)
        if selected is None:
            failures.append(
                {
                    "pass_id": pass_id,
                    "required_tier": required_tier,
                    "reason": "no_available_route_for_required_tier_or_higher",
                }
            )
            continue
        route = {
            "pass_id": pass_id,
            "required_tier": required_tier,
            "selected_tier": str(selected.get("prescan_tier")),
            "tier_adjustment": adjustment,
            "provider": str(selected.get("provider")),
            "model_id": str(selected.get("model_id")),
            "api_key_env": str(selected.get("api_key_env")),
            "selection_basis": "lowest_estimated_cost_within_allowed_tier_band",
            "pricing": dict(selected.get("pricing") or {}),
            "legacy_route_changed": bool(
                str(config.provider) != str(selected.get("provider"))
                or str(config.model) != str(selected.get("model_id"))
                or str(config.api_key_env) != str(selected.get("api_key_env"))
            ),
        }
        selected_routes[pass_id] = route

    return {
        "requested_passes": requested_passes,
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "selected_routes": selected_routes,
    }


def write_provider_catalog(output_dir: Path, catalog: dict[str, Any]) -> Path:
    path = output_dir / "prescan_provider_model_catalog.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **catalog,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_routing_plan(output_dir: Path, plan: dict[str, Any]) -> Path:
    path = output_dir / "prescan_routing_plan.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **plan,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
