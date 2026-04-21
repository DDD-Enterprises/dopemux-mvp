from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

from .models import PrescanConfig

try:
    from lib.spend_ledger import get_model_cost_rate
except Exception:  # pragma: no cover - defensive import fallback
    get_model_cost_rate = None


SANCTIONED_PROVIDERS = (
    "openai",
    "openrouter",
    "gemini",
    "xai",
    "mock",
)

PRESCAN_PASS_REQUIREMENTS = {
    "dedup": "cheap_structured",
    "discover": "cheap_structured",
    "feasibility": "balanced_analysis",
    "optimize": "premium_planning",
}

PRESCAN_TIER_RANK = {
    "cheap_structured": 1,
    "balanced_analysis": 2,
    "premium_planning": 3,
}


def classify_prescan_route(provider: str, model_id: str) -> str:
    """Classify route into prescan tier using provider/model heuristics."""
    model = (model_id or "").lower()

    premium_markers = (
        "gpt-5.4",
        "gpt-5.3",
        "gpt-5.2",
        "claude-opus",
        "gemini-2.5-pro",
    )
    if any(marker in model for marker in premium_markers):
        return "premium_planning"

    cheap_markers = (
        "nano",
        "mini",
        "flash",
        "grok-code-fast",
        "grok-4-1-fast",
        "gpt-4o-mini",
        "gpt-4.1-nano",
    )
    if any(marker in model for marker in cheap_markers):
        return "cheap_structured"

    return "balanced_analysis"


def _pricing(provider: str, model_id: str) -> dict[str, Any]:
    """Resolve pricing metadata from spend ledger, with safe defaults."""
    if get_model_cost_rate is None:
        return {
            "input_1m_usd": 10.0,
            "output_1m_usd": 40.0,
            "pricing_authority": "fallback_default",
            "pricing_status": "UNPRICED_UNKNOWN",
            "pricing_confidence": "UNKNOWN",
            "pricing_source_type": "unknown",
        }

    rate = get_model_cost_rate(provider=provider, model_id=model_id) or {}
    return {
        "input_1m_usd": float(rate.get("input_cost_per_1m_usd", 10.0)),
        "output_1m_usd": float(rate.get("output_cost_per_1m_usd", 40.0)),
        "pricing_authority": str(rate.get("pricing_source") or "shared_spend_ledger_registry"),
        "pricing_status": str(rate.get("pricing_status") or "UNPRICED_UNKNOWN"),
        "pricing_confidence": str(rate.get("pricing_confidence") or "UNKNOWN"),
        "pricing_source_type": str(rate.get("pricing_source_type") or "unknown"),
    }


def _load_runner_authority() -> tuple[dict[str, dict[str, list[tuple[str, str, str]]]], dict[str, str]]:
    """Load active routing ladders from run_extraction_v5 without hard dependency."""
    try:
        from run_extraction_v5 import ACTIVE_ROUTING_LADDERS  # type: ignore
    except Exception:
        return {}, {}

    ladders = ACTIVE_ROUTING_LADDERS or {}
    provider_env: dict[str, str] = {}
    for tiers in ladders.values():
        for routes in tiers.values():
            for provider, _model_id, api_key_env in routes:
                provider_env.setdefault(str(provider), str(api_key_env))

    return ladders, provider_env


def build_provider_model_catalog(config: PrescanConfig) -> dict[str, Any]:
    """Build deduplicated provider/model route catalog from active ladders."""
    ladders, provider_env = _load_runner_authority()
    route_index: dict[tuple[str, str], dict[str, Any]] = {}

    for policy, tiers in ladders.items():
        for tier_name, routes in tiers.items():
            for provider, model_id, api_key_env in routes:
                provider = str(provider)
                model_id = str(model_id)
                api_key_env = str(api_key_env)
                if provider not in SANCTIONED_PROVIDERS:
                    continue

                key = (provider, model_id)
                route = route_index.get(key)
                if route is None:
                    route = {
                        "provider": provider,
                        "model_id": model_id,
                        "api_key_env": provider_env.get(provider, api_key_env),
                        "sources": [],
                    }
                    route_index[key] = route

                source = {"policy": str(policy), "tier": str(tier_name)}
                if source not in route["sources"]:
                    route["sources"].append(source)

    legacy_provider = str(config.provider)
    legacy_model = str(config.model)
    if legacy_provider in SANCTIONED_PROVIDERS and legacy_model:
        key = (legacy_provider, legacy_model)
        route = route_index.get(key)
        if route is None:
            route = {
                "provider": legacy_provider,
                "model_id": legacy_model,
                "api_key_env": str(config.api_key_env),
                "sources": [],
            }
            route_index[key] = route
        legacy_source = {"policy": "legacy_prescan_config", "tier": "legacy"}
        if legacy_source not in route["sources"]:
            route["sources"].append(legacy_source)

    routes: list[dict[str, Any]] = []
    for route in route_index.values():
        provider = str(route["provider"])
        model_id = str(route["model_id"])
        api_key_env = str(route["api_key_env"])
        finalized = {
            **route,
            "available": bool(os.environ.get(api_key_env)),
            "prescan_tier": classify_prescan_route(provider, model_id),
            "pricing": _pricing(provider, model_id),
        }
        routes.append(finalized)

    routes.sort(key=lambda r: (str(r["provider"]), str(r["model_id"])))

    return {
        "generated_from": "run_extraction_v5.ACTIVE_ROUTING_LADDERS",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sanctioned_providers": list(SANCTIONED_PROVIDERS),
        "routes": routes,
    }


def _select_route_for_tier(
    routes: list[dict[str, Any]], required_tier: str
) -> tuple[dict[str, Any] | None, str | None]:
    required_rank = PRESCAN_TIER_RANK[required_tier]
    eligible = [
        r
        for r in routes
        if PRESCAN_TIER_RANK.get(str(r.get("prescan_tier")), 0) >= required_rank
    ]
    if not eligible:
        return None, None

    exact = [r for r in eligible if str(r.get("prescan_tier")) == required_tier]
    pool = exact or eligible
    chosen = min(
        pool,
        key=lambda r: (
            float((r.get("pricing") or {}).get("input_1m_usd", 999.0)),
            float((r.get("pricing") or {}).get("output_1m_usd", 999.0)),
        ),
    )
    return chosen, "exact" if exact else "upgrade"


def build_prescan_routing_plan(
    config: PrescanConfig,
    catalog: dict[str, Any],
    passes: list[str] | None,
) -> dict[str, Any]:
    requested_passes = [p for p in (passes or []) if p in PRESCAN_PASS_REQUIREMENTS]
    routes = [r for r in catalog.get("routes", []) if r.get("available")]
    selected_routes: dict[str, dict[str, Any]] = {}
    candidate_routes: dict[str, list[dict[str, Any]]] = {}
    failures: list[dict[str, str]] = []

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
                float((r.get("pricing") or {}).get("input_1m_usd", 999.0)),
                float((r.get("pricing") or {}).get("output_1m_usd", 999.0)),
            )
        )

        candidate_routes[pass_id] = [
            {
                "provider": r["provider"],
                "model_id": r["model_id"],
                "api_key_env": r["api_key_env"],
                "tier": r["prescan_tier"],
            }
            for r in candidates
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

        selected_routes[pass_id] = {
            "provider": selected["provider"],
            "model_id": selected["model_id"],
            "api_key_env": selected["api_key_env"],
            "required_tier": required_tier,
            "selected_tier": selected["prescan_tier"],
            "tier_adjustment": adjustment,
            "pricing": selected.get("pricing", {}),
            "legacy_route_changed": (
                str(selected["provider"]) != str(config.provider)
                or str(selected["model_id"]) != str(config.model)
                or str(selected["api_key_env"]) != str(config.api_key_env)
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
    path = output_dir / "provider_model_catalog.json"
    path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n")
    return path


def write_routing_plan(output_dir: Path, routing_plan: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "routing_plan.json"
    path.write_text(json.dumps(routing_plan, indent=2, sort_keys=True) + "\n")
    return path
