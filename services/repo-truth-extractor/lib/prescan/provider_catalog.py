from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import PrescanConfig

try:
    from lib.spend_ledger import get_model_cost_rate
except Exception:  # pragma: no cover - defensive import guard for optional runtime
    get_model_cost_rate = None


SANCTIONED_PROVIDERS = ("openai", "xai", "gemini", "openrouter", "mock")

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


def classify_prescan_route(provider: str, model_id: str) -> str:
    model = (model_id or "").lower()
    if any(
        token in model
        for token in ("gpt-5.4", "gpt-5.3", "gpt-5.2", "claude-opus", "gemini-2.5-pro")
    ):
        return "premium_planning"
    if any(
        token in model
        for token in (
            "nano",
            "mini",
            "flash",
            "grok-code-fast",
            "gpt-4.1-nano",
            "gpt-4o-mini",
        )
    ):
        return "cheap_structured"
    return "balanced_analysis"


def _pricing(provider: str, model_id: str) -> dict[str, Any]:
    fallback = {
        "input_1m_usd": 10.0,
        "output_1m_usd": 40.0,
        "pricing_authority": (
            "fallback_default"
            if get_model_cost_rate is None
            else "shared_spend_ledger_registry"
        ),
        "pricing_status": "UNPRICED_UNKNOWN",
        "pricing_confidence": "LOW",
    }

    if get_model_cost_rate is None:
        return fallback

    rate = get_model_cost_rate(provider=provider, model_id=model_id) or {}
    return {
        "input_1m_usd": float(
            rate.get("input_cost_per_1m_usd", fallback["input_1m_usd"])
        ),
        "output_1m_usd": float(
            rate.get("output_cost_per_1m_usd", fallback["output_1m_usd"])
        ),
        "pricing_authority": str(
            rate.get("pricing_source", fallback["pricing_authority"])
        ),
        "pricing_status": str(rate.get("pricing_status", fallback["pricing_status"])),
        "pricing_confidence": str(
            rate.get("pricing_confidence", fallback["pricing_confidence"])
        ),
    }


def _load_runner_authority() -> (
    tuple[dict[str, dict[str, list[tuple[str, str, str]]]], dict[str, str]]
):
    try:
        from run_extraction_v5 import ACTIVE_ROUTING_LADDERS, PROVIDER_API_KEY_ENV

        return dict(ACTIVE_ROUTING_LADDERS), dict(PROVIDER_API_KEY_ENV)
    except Exception:
        return {}, {}


def build_provider_model_catalog(config: PrescanConfig) -> dict[str, Any]:
    ladders, provider_env = _load_runner_authority()
    route_map: dict[tuple[str, str, str], dict[str, Any]] = {}

    for policy, tiers in ladders.items():
        for tier_name, candidates in (tiers or {}).items():
            for candidate in candidates:
                provider, model_id, api_key_env = candidate
                if provider not in SANCTIONED_PROVIDERS:
                    continue
                key = (provider, model_id, api_key_env)
                route = route_map.setdefault(
                    key,
                    {
                        "provider": provider,
                        "model_id": model_id,
                        "api_key_env": api_key_env,
                        "available": bool(os.environ.get(api_key_env, "")),
                        "prescan_tier": classify_prescan_route(provider, model_id),
                        "pricing": _pricing(provider, model_id),
                        "sources": [],
                    },
                )
                route["sources"].append({"policy": policy, "tier": tier_name})

    legacy_provider = str(config.provider)
    legacy_model = str(config.model)
    legacy_key_env = str(config.api_key_env)
    if legacy_provider in SANCTIONED_PROVIDERS:
        legacy_key = (legacy_provider, legacy_model, legacy_key_env)
        if legacy_key not in route_map:
            route_map[legacy_key] = {
                "provider": legacy_provider,
                "model_id": legacy_model,
                "api_key_env": legacy_key_env,
                "available": bool(os.environ.get(legacy_key_env, "")),
                "prescan_tier": classify_prescan_route(legacy_provider, legacy_model),
                "pricing": _pricing(legacy_provider, legacy_model),
                "sources": [{"policy": "legacy_prescan_config", "tier": "legacy"}],
            }
        else:
            route_map[legacy_key]["sources"].append(
                {"policy": "legacy_prescan_config", "tier": "legacy"}
            )

    routes = list(route_map.values())
    for route in routes:
        route["sources"].sort(key=lambda item: (item["policy"], item["tier"]))

    routes.sort(
        key=lambda item: (
            PRESCAN_TIER_RANK.get(str(item.get("prescan_tier")), 99),
            float(item.get("pricing", {}).get("input_1m_usd", 9999.0)),
            str(item.get("provider", "")),
            str(item.get("model_id", "")),
        )
    )

    return {
        "generated_from": "active_routing_ladders",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sanctioned_providers": list(SANCTIONED_PROVIDERS),
        "provider_env": provider_env,
        "routes": routes,
    }


def _select_route_for_tier(
    routes: list[dict[str, Any]], required_tier: str
) -> tuple[dict[str, Any] | None, str | None]:
    if not routes:
        return None, None

    required_rank = PRESCAN_TIER_RANK[required_tier]
    eligible = [
        route
        for route in routes
        if PRESCAN_TIER_RANK.get(str(route.get("prescan_tier")), 0) >= required_rank
    ]
    if not eligible:
        return None, None

    exact = [
        route
        for route in eligible
        if PRESCAN_TIER_RANK.get(str(route.get("prescan_tier")), 0) == required_rank
    ]
    pool = exact or eligible
    adjustment = "exact" if exact else "upgrade"

    selected = min(
        pool,
        key=lambda item: (
            float(item.get("pricing", {}).get("input_1m_usd", 9999.0)),
            str(item.get("provider", "")),
            str(item.get("model_id", "")),
        ),
    )
    return selected, adjustment


def build_prescan_routing_plan(
    config: PrescanConfig,
    catalog: dict[str, Any],
    passes: list[str] | None,
) -> dict[str, Any]:
    requested_passes = [
        pass_id for pass_id in (passes or []) if pass_id in PRESCAN_PASS_REQUIREMENTS
    ]
    available_routes = [
        route for route in catalog.get("routes", []) if route.get("available")
    ]

    selected_routes: dict[str, dict[str, Any]] = {}
    candidate_routes: dict[str, list[dict[str, Any]]] = {}
    failures: list[dict[str, Any]] = []

    for pass_id in requested_passes:
        required_tier = PRESCAN_PASS_REQUIREMENTS[pass_id]
        required_rank = PRESCAN_TIER_RANK[required_tier]
        candidates = [
            route
            for route in available_routes
            if PRESCAN_TIER_RANK.get(str(route.get("prescan_tier")), 0) >= required_rank
        ]
        candidates.sort(
            key=lambda item: (
                PRESCAN_TIER_RANK.get(str(item.get("prescan_tier")), 99),
                float(item.get("pricing", {}).get("input_1m_usd", 9999.0)),
                str(item.get("provider", "")),
                str(item.get("model_id", "")),
            )
        )
        candidate_routes[pass_id] = [
            {
                "provider": candidate["provider"],
                "model_id": candidate["model_id"],
                "api_key_env": candidate["api_key_env"],
                "tier": candidate["prescan_tier"],
            }
            for candidate in candidates
        ]

        selected, adjustment = _select_route_for_tier(candidates, required_tier)
        if selected is None:
            failures.append(
                {
                    "pass_id": pass_id,
                    "required_tier": required_tier,
                    "reason": "no_eligible_available_route",
                }
            )
            continue

        selected_routes[pass_id] = {
            "pass_id": pass_id,
            "required_tier": required_tier,
            "selected_tier": selected["prescan_tier"],
            "adjustment": adjustment,
            "provider": selected["provider"],
            "model_id": selected["model_id"],
            "api_key_env": selected["api_key_env"],
            "pricing": selected.get("pricing", {}),
            "legacy_route_changed": (
                selected["provider"] != config.provider
                or selected["model_id"] != config.model
                or selected["api_key_env"] != config.api_key_env
            ),
        }

    return {
        "status": "FAIL" if failures else "PASS",
        "requested_passes": requested_passes,
        "selected_routes": selected_routes,
        "candidate_routes": candidate_routes,
        "failures": failures,
    }


def write_provider_catalog(output_dir: Path, catalog: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "provider_catalog.json"
    path.write_text(
        json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path


def write_routing_plan(output_dir: Path, routing_plan: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "prescan_routing_plan.json"
    path.write_text(
        json.dumps(routing_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path
