from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .models import PrescanConfig

try:
    from ..spend_ledger import get_model_cost_rate
except Exception:  # pragma: no cover - defensive import seam
    get_model_cost_rate = None  # type: ignore[assignment]


SANCTIONED_PROVIDERS: tuple[str, ...] = (
    "openai",
    "gemini",
    "xai",
    "openrouter",
)

PROVIDER_API_KEY_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}

PRESCAN_TIER_RANK: dict[str, int] = {
    "cheap_structured": 1,
    "balanced_analysis": 2,
    "premium_planning": 3,
}

PRESCAN_PASS_REQUIREMENTS: dict[str, str] = {
    "dedup": "cheap_structured",
    "discover": "cheap_structured",
    "feasibility": "balanced_analysis",
    "optimize": "premium_planning",
}


def classify_prescan_route(provider: str, model_id: str) -> str:
    _ = provider
    token = str(model_id or "").strip().lower()

    premium_markers = (
        "gpt-5.4",
        "gpt-5.3-codex",
        "gpt-5.2",
        "claude-opus-4-6",
        "gemini-2.5-pro",
    )
    if any(marker in token for marker in premium_markers):
        return "premium_planning"

    cheap_markers = (
        "gpt-5-nano",
        "gpt-4.1-nano",
        "gpt-4o-mini",
        "gemini-2.5-flash",
        "gemini-3-flash",
        "grok-code-fast",
    )
    if any(marker in token for marker in cheap_markers):
        return "cheap_structured"

    return "balanced_analysis"


def _pricing(provider: str, model_id: str) -> dict[str, Any]:
    fallback_input = 10.0
    fallback_output = 40.0

    if get_model_cost_rate is None:
        return {
            "input_1m_usd": fallback_input,
            "output_1m_usd": fallback_output,
            "pricing_authority": "fallback_default",
            "pricing_status": "UNPRICED_UNKNOWN",
            "pricing_confidence": "UNKNOWN",
        }

    rate = get_model_cost_rate(provider=provider, model_id=model_id) or {}
    return {
        "input_1m_usd": float(rate.get("input_cost_per_1m_usd", fallback_input)),
        "output_1m_usd": float(rate.get("output_cost_per_1m_usd", fallback_output)),
        "pricing_authority": str(
            rate.get("pricing_source") or "shared_spend_ledger_registry"
        ),
        "pricing_status": str(rate.get("pricing_status") or "UNPRICED_UNKNOWN"),
        "pricing_confidence": str(rate.get("pricing_confidence") or "UNKNOWN"),
    }


def _load_runner_authority() -> tuple[
    dict[str, dict[str, list[tuple[str, str, str]]]], dict[str, str]
]:
    try:
        from run_extraction_v5 import ACTIVE_ROUTING_LADDERS, PROVIDER_API_KEY_ENV as KEY_ENV

        ladders = {
            policy: {tier: list(routes) for tier, routes in tiers.items()}
            for policy, tiers in (ACTIVE_ROUTING_LADDERS or {}).items()
        }
        provider_env = dict(KEY_ENV or {})
        return ladders, provider_env
    except Exception:
        return {}, dict(PROVIDER_API_KEY_ENV)


def build_provider_model_catalog(config: PrescanConfig) -> dict[str, Any]:
    ladders, provider_env = _load_runner_authority()
    routes_by_key: dict[tuple[str, str], dict[str, Any]] = {}

    for policy, tiers in (ladders or {}).items():
        for tier_name, route_defs in (tiers or {}).items():
            for provider, model_id, api_key_env in route_defs:
                if provider not in SANCTIONED_PROVIDERS:
                    continue

                key = (provider, model_id)
                route = routes_by_key.get(key)
                if route is None:
                    env_name = (
                        str(api_key_env or "").strip()
                        or provider_env.get(provider)
                        or PROVIDER_API_KEY_ENV.get(provider, "")
                    )
                    route = {
                        "provider": provider,
                        "model_id": model_id,
                        "api_key_env": env_name,
                        "available": bool(env_name and os.environ.get(env_name)),
                        "prescan_tier": classify_prescan_route(provider, model_id),
                        "pricing": _pricing(provider, model_id),
                        "sources": [],
                    }
                    routes_by_key[key] = route

                route["sources"].append(
                    {
                        "policy": policy,
                        "tier": tier_name,
                    }
                )

    if config.provider in SANCTIONED_PROVIDERS and config.model:
        key = (config.provider, config.model)
        if key not in routes_by_key:
            env_name = str(config.api_key_env or "").strip() or provider_env.get(
                config.provider, ""
            )
            routes_by_key[key] = {
                "provider": config.provider,
                "model_id": config.model,
                "api_key_env": env_name,
                "available": bool(env_name and os.environ.get(env_name)),
                "prescan_tier": classify_prescan_route(config.provider, config.model),
                "pricing": _pricing(config.provider, config.model),
                "sources": [],
            }
        routes_by_key[key]["sources"].append(
            {
                "policy": "legacy_prescan_config",
                "tier": "n/a",
            }
        )

    routes = list(routes_by_key.values())
    routes.sort(
        key=lambda item: (
            PRESCAN_TIER_RANK.get(str(item.get("prescan_tier")), 99),
            float(item.get("pricing", {}).get("input_1m_usd", 999.0)),
            float(item.get("pricing", {}).get("output_1m_usd", 999.0)),
            str(item.get("provider")),
            str(item.get("model_id")),
        )
    )

    return {
        "generated_from": "run_extraction_v5.ACTIVE_ROUTING_LADDERS",
        "sanctioned_providers": list(SANCTIONED_PROVIDERS),
        "routes": routes,
    }


def _select_route_for_tier(
    routes: list[dict[str, Any]], required_tier: str
) -> tuple[dict[str, Any] | None, str | None]:
    required_rank = PRESCAN_TIER_RANK.get(required_tier)
    if required_rank is None:
        return None, None

    eligible = [
        route
        for route in routes
        if PRESCAN_TIER_RANK.get(str(route.get("prescan_tier")), 0) >= required_rank
    ]
    if not eligible:
        return None, None

    eligible.sort(
        key=lambda item: (
            PRESCAN_TIER_RANK.get(str(item.get("prescan_tier")), 99),
            float(item.get("pricing", {}).get("input_1m_usd", 999.0)),
            float(item.get("pricing", {}).get("output_1m_usd", 999.0)),
            str(item.get("provider")),
            str(item.get("model_id")),
        )
    )
    selected = eligible[0]
    selected_tier = str(selected.get("prescan_tier") or "")
    adjustment = "exact" if selected_tier == required_tier else "upgrade"
    return selected, adjustment


def build_prescan_routing_plan(
    config: PrescanConfig,
    catalog: dict[str, Any],
    passes: list[str] | None,
) -> dict[str, Any]:
    requested_passes = [p for p in (passes or []) if p in PRESCAN_PASS_REQUIREMENTS]
    available_routes = [r for r in catalog.get("routes", []) if r.get("available")]

    selected_routes: dict[str, Any] = {}
    candidate_routes: dict[str, list[dict[str, Any]]] = {}
    failures: list[dict[str, Any]] = []

    for pass_id in requested_passes:
        required_tier = PRESCAN_PASS_REQUIREMENTS[pass_id]
        required_rank = PRESCAN_TIER_RANK[required_tier]
        candidates = [
            r
            for r in available_routes
            if PRESCAN_TIER_RANK.get(str(r.get("prescan_tier")), 0) >= required_rank
        ]
        candidates.sort(
            key=lambda item: (
                PRESCAN_TIER_RANK.get(str(item.get("prescan_tier")), 99),
                float(item.get("pricing", {}).get("input_1m_usd", 999.0)),
                float(item.get("pricing", {}).get("output_1m_usd", 999.0)),
            )
        )

        candidate_routes[pass_id] = [
            {
                "provider": c["provider"],
                "model_id": c["model_id"],
                "api_key_env": c["api_key_env"],
                "tier": c.get("prescan_tier"),
            }
            for c in candidates
        ]

        selected, adjustment = _select_route_for_tier(candidates, required_tier)
        if selected is None:
            failures.append(
                {
                    "pass_id": pass_id,
                    "required_tier": required_tier,
                    "reason": "no_available_route_for_required_tier",
                }
            )
            continue

        selected_tier = str(selected.get("prescan_tier") or "")
        selected_routes[pass_id] = {
            "required_tier": required_tier,
            "selected_tier": selected_tier,
            "provider": selected["provider"],
            "model_id": selected["model_id"],
            "api_key_env": selected["api_key_env"],
            "pricing": dict(selected.get("pricing") or {}),
            "tier_adjustment": adjustment,
            "legacy_route_changed": (
                selected.get("provider") != config.provider
                or selected.get("model_id") != config.model
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
    path = output_dir / "provider_model_catalog.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_routing_plan(output_dir: Path, routing_plan: dict[str, Any]) -> Path:
    path = output_dir / "prescan_routing_plan.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(routing_plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return path
