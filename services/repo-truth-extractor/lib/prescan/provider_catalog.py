from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from .models import PrescanConfig

try:
    from lib.spend_ledger import get_model_cost_rate
except Exception:  # pragma: no cover - optional in minimal test envs
    get_model_cost_rate = None

SANCTIONED_PROVIDERS = ("openai", "gemini", "xai", "openrouter")
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
    p = (provider or "").lower()
    m = (model_id or "").lower()
    if (
        m.startswith("gpt-5.4")
        or m.startswith("gpt-5.3")
        or m.startswith("gpt-5.2")
        or "claude-opus-4-6" in m
        or m.startswith("gemini-2.5-pro")
    ):
        return "premium_planning"
    if (
        "nano" in m
        or m.endswith("-mini")
        or "flash" in m
        or (p == "xai" and "fast" in m)
    ):
        return "cheap_structured"
    return "balanced_analysis"


def _pricing(provider: str, model_id: str) -> dict[str, Any]:
    fallback = {
        "input_1m_usd": 10.0,
        "output_1m_usd": 40.0,
        "pricing_authority": "fallback_default",
        "pricing_status": "UNPRICED_UNKNOWN",
        "pricing_confidence": "LOW",
    }
    if get_model_cost_rate is None:
        return fallback
    rate = get_model_cost_rate(provider=provider, model_id=model_id) or {}
    return {
        "input_1m_usd": float(rate.get("input_cost_per_1m_usd", 10.0)),
        "output_1m_usd": float(rate.get("output_cost_per_1m_usd", 40.0)),
        "pricing_authority": str(rate.get("pricing_source", "shared_spend_ledger_registry")),
        "pricing_status": str(rate.get("pricing_status", "UNPRICED_UNKNOWN")),
        "pricing_confidence": str(rate.get("pricing_confidence", "LOW")),
        "pricing_source_type": str(rate.get("pricing_source_type", "unknown")),
    }


def _load_runner_authority() -> tuple[dict[str, Any], dict[str, str]]:
    try:
        from run_extraction_v5 import ACTIVE_ROUTING_LADDERS, ROUTING_LADDERS
    except Exception:
        return {}, {}
    ladders = ACTIVE_ROUTING_LADDERS or ROUTING_LADDERS or {}
    provider_env: dict[str, str] = {}
    for tiers in ladders.values():
        for routes in tiers.values():
            for provider, _model_id, api_key_env in routes:
                provider_env.setdefault(provider, api_key_env)
    return ladders, provider_env


def build_provider_model_catalog(config: PrescanConfig) -> dict[str, Any]:
    ladders, provider_env = _load_runner_authority()
    routes_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for policy, tiers in (ladders or {}).items():
        for tier_name, routes in (tiers or {}).items():
            for provider, model_id, api_key_env in routes:
                provider = str(provider).lower()
                if provider not in SANCTIONED_PROVIDERS:
                    continue
                key = (provider, model_id)
                route = routes_by_key.setdefault(
                    key,
                    {
                        "provider": provider,
                        "model_id": model_id,
                        "api_key_env": api_key_env or provider_env.get(provider, ""),
                        "sources": [],
                    },
                )
                route["sources"].append({"policy": policy, "tier": tier_name})

    legacy_key = (config.provider, config.model)
    if config.provider in SANCTIONED_PROVIDERS and legacy_key not in routes_by_key:
        routes_by_key[legacy_key] = {
            "provider": config.provider,
            "model_id": config.model,
            "api_key_env": config.api_key_env,
            "sources": [{"policy": "legacy_prescan_config", "tier": "default"}],
        }

    routes = []
    for route in routes_by_key.values():
        env_name = route["api_key_env"]
        route["available"] = bool(env_name and os.environ.get(env_name))
        route["prescan_tier"] = classify_prescan_route(route["provider"], route["model_id"])
        route["pricing"] = _pricing(route["provider"], route["model_id"])
        routes.append(route)

    routes.sort(key=lambda r: (r["provider"], r["model_id"]))
    return {
        "generated_from": "run_extraction_v5 routing ladders + prescan config",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sanctioned_providers": list(SANCTIONED_PROVIDERS),
        "routes": routes,
    }


def _select_route_for_tier(
    routes: list[dict[str, Any]],
    required_tier: str,
) -> tuple[dict[str, Any] | None, str | None]:
    required_rank = PRESCAN_TIER_RANK[required_tier]
    eligible = [
        r
        for r in routes
        if PRESCAN_TIER_RANK.get(str(r.get("prescan_tier")), 0) >= required_rank
    ]
    if not eligible:
        return None, None
    eligible.sort(
        key=lambda r: (
            PRESCAN_TIER_RANK.get(str(r.get("prescan_tier")), 99),
            float(r.get("pricing", {}).get("input_1m_usd", 999.0)),
            float(r.get("pricing", {}).get("output_1m_usd", 999.0)),
        )
    )
    selected = eligible[0]
    selected_rank = PRESCAN_TIER_RANK.get(str(selected.get("prescan_tier")), 0)
    adjustment = "exact" if selected_rank == required_rank else "upgrade"
    return selected, adjustment


def build_prescan_routing_plan(
    config: PrescanConfig,
    catalog: dict[str, Any],
    passes: list[str] | None,
) -> dict[str, Any]:
    requested_passes = [p for p in (passes or []) if p in PRESCAN_PASS_REQUIREMENTS]
    routes = [r for r in catalog.get("routes", []) if r.get("available")]
    selected_routes: dict[str, Any] = {}
    candidate_routes: dict[str, list[dict[str, Any]]] = {}
    failures: list[dict[str, Any]] = []

    for pass_id in requested_passes:
        required_tier = PRESCAN_PASS_REQUIREMENTS[pass_id]
        required_rank = PRESCAN_TIER_RANK[required_tier]
        candidates = [
            r
            for r in routes
            if PRESCAN_TIER_RANK.get(str(r.get("prescan_tier")), 0) >= required_rank
        ]
        candidates.sort(
            key=lambda r: (
                PRESCAN_TIER_RANK.get(str(r.get("prescan_tier")), 99),
                float(r.get("pricing", {}).get("input_1m_usd", 999.0)),
            )
        )
        candidate_routes[pass_id] = [
            {
                "provider": r["provider"],
                "model_id": r["model_id"],
                "api_key_env": r["api_key_env"],
                "prescan_tier": r["prescan_tier"],
            }
            for r in candidates
        ]

        selected, adjustment = _select_route_for_tier(candidates, required_tier)
        if not selected:
            failures.append({"pass_id": pass_id, "required_tier": required_tier})
            continue
        selected_routes[pass_id] = {
            "provider": selected["provider"],
            "model_id": selected["model_id"],
            "api_key_env": selected["api_key_env"],
            "required_tier": required_tier,
            "selected_tier": selected["prescan_tier"],
            "tier_adjustment": adjustment,
            "legacy_route_changed": (
                selected["provider"] != config.provider or selected["model_id"] != config.model
            ),
            "pricing": selected.get("pricing", {}),
        }

    return {
        "status": "FAIL" if failures else "PASS",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "requested_passes": requested_passes,
        "selected_routes": selected_routes,
        "candidate_routes": candidate_routes,
        "failures": failures,
    }


def write_provider_catalog(output_dir: Path, catalog: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "provider_model_catalog.json"
    path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_routing_plan(output_dir: Path, routing_plan: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "prescan_routing_plan.json"
    path.write_text(json.dumps(routing_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
