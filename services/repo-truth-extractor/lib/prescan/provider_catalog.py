from __future__ import annotations

import importlib
import json
import os
from types import ModuleType
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
NO_LIVE_LANE = "NO_LIVE_LANE"


def _runner_module() -> ModuleType:
    return importlib.import_module("run_extraction_v5")


def _load_runner_authority() -> tuple[dict[str, dict[str, list[tuple[str, str, str]]]], dict[str, str]]:
    runner = _runner_module()
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
                provider, model_id, api_key_env = (
                    str(route[0]).strip().lower(),
                    str(route[1]).strip(),
                    str(route[2]).strip(),
                )
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
        status = "UNPRICED_UNKNOWN"
        confidence = "UNKNOWN"
        source_type = "inferred_estimated_fallback"
    else:
        rate = get_model_cost_rate(provider=provider, model_id=model_id)
        input_1m = rate.get("input_cost_per_1m_usd", 10.0)
        output_1m = rate.get("output_cost_per_1m_usd", 40.0)
        authority = str(rate.get("pricing_source") or "shared_spend_ledger_registry")
        status = str(rate.get("pricing_status") or "UNPRICED_UNKNOWN")
        confidence = str(rate.get("pricing_confidence") or "UNKNOWN")
        source_type = str(rate.get("pricing_source_type") or "unknown")
    return {
        "input_1m_usd": float(input_1m),
        "output_1m_usd": float(output_1m),
        "pricing_authority": authority,
        "pricing_status": status,
        "pricing_confidence": confidence,
        "pricing_source_type": source_type,
    }


def _route_transport(provider: str) -> str:
    if provider == "gemini":
        return "sdk"
    return "openai_sdk"


def _route_admissibility(provider: str) -> dict[str, Any]:
    transport = _route_transport(provider)
    if transport != "openai_sdk":
        return {
            "route_admissible": False,
            "route_admissibility_reason": f"unsupported_prescan_transport:{transport}",
        }
    return {
        "route_admissible": True,
        "route_admissibility_reason": "sanctioned_runtime_route",
    }


def _route_identity(provider: str, model_id: str) -> dict[str, Any]:
    normalized_provider = str(provider).strip().lower()
    normalized_model = str(model_id).strip()
    upstream_provider = normalized_provider
    if normalized_provider == "openrouter":
        prefix, sep, _rest = normalized_model.partition("/")
        if sep and prefix in {"anthropic", "gemini", "openai", "xai", "x-ai"}:
            upstream_provider = "xai" if prefix == "x-ai" else prefix
    dependency_class = "proxy" if normalized_provider == "openrouter" else "first_party"
    if normalized_provider in {"local", "lmstudio", "mock", "ollama", "vllm"}:
        dependency_class = "local"
    return {
        "dependency_class": dependency_class,
        "economic_surface": normalized_provider or "unknown",
        "upstream_provider": upstream_provider,
        "billing_independent_from_upstream": bool(
            normalized_provider == "openrouter" and upstream_provider != normalized_provider
        ),
        "execution_transport": _route_transport(normalized_provider),
    }


def build_provider_model_catalog(config: PrescanConfig) -> dict[str, Any]:
    seen: dict[tuple[str, str, str], dict[str, Any]] = {}
    for policy, ladder_tier, provider, model_id, api_key_env in _iter_runner_routes():
        key = (provider, model_id, api_key_env)
        credential_present = bool(os.environ.get(api_key_env, "").strip())
        entry = seen.setdefault(
            key,
            {
                "provider": provider,
                "model_id": model_id,
                "api_key_env": api_key_env,
                "available": credential_present,
                "credential_present": credential_present,
                "availability_reason": "credential_present" if credential_present else "missing_credential",
                "prescan_tier": classify_prescan_route(provider, model_id),
                "pricing": _pricing(provider, model_id),
                "sources": [],
                **_route_identity(provider, model_id),
                **_route_admissibility(provider),
            },
        )
        source = {"policy": policy, "ladder_tier": ladder_tier}
        if source not in entry["sources"]:
            entry["sources"].append(source)

    if config.provider in SANCTIONED_PROVIDERS and config.model and config.api_key_env:
        key = (config.provider, config.model, config.api_key_env)
        credential_present = bool(os.environ.get(config.api_key_env, "").strip())
        entry = seen.setdefault(
            key,
            {
                "provider": config.provider,
                "model_id": config.model,
                "api_key_env": config.api_key_env,
                "available": credential_present,
                "credential_present": credential_present,
                "availability_reason": "credential_present" if credential_present else "missing_credential",
                "prescan_tier": classify_prescan_route(config.provider, config.model),
                "pricing": _pricing(config.provider, config.model),
                "sources": [],
                **_route_identity(config.provider, config.model),
                **_route_admissibility(config.provider),
            },
        )
        if entry["route_admissible"]:
            entry["route_admissibility_reason"] = "legacy_prescan_config"
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


def _offline_blocker(route: dict[str, Any], reason: str) -> dict[str, Any]:
    if reason == "online_llm_not_authorized":
        blocker = {
            "ready": False,
            "blocker_code": "ONLINE_LLM_NOT_AUTHORIZED",
            "blocker_class": "operator_policy",
            "remediation_class": "authorize_online_llm",
            "rerun_worthiness": "rerun_after_operator_authorization",
            "human_summary": "Online LLM execution was not authorized for prescan Stage 0 readiness probing.",
        }
        failure_type = "operator_policy"
    else:
        runner = _runner_module()
        blocker = runner.classify_provider_readiness_blocker(
            provider=str(route.get("provider") or ""),
            model_id=str(route.get("model_id") or ""),
            api_key_env=str(route.get("api_key_env") or ""),
            api_key_present=bool(route.get("credential_present")),
            status_code=None,
            failure_type="auth_missing" if reason == "missing_credential" else "unknown",
            provider_error_reason=reason,
        )
        failure_type = "auth_missing" if reason == "missing_credential" else "unknown"
    return {
        "provider": str(route.get("provider") or ""),
        "model_id": str(route.get("model_id") or ""),
        "api_key_env_name": str(route.get("api_key_env") or ""),
        "api_key_env_resolved": str(route.get("api_key_env") or ""),
        "api_key_present": bool(route.get("credential_present")),
        "transport": str(route.get("execution_transport") or ""),
        "status_code": None,
        "failure_type": failure_type,
        "provider_error_reason": reason,
        "provider_signature": f"{route.get('provider')}:{route.get('model_id')}",
        "ready": bool(blocker["ready"]),
        "readiness_blocker": blocker,
    }


def _build_probe_cfg() -> Any:
    runner = _runner_module()
    return runner.RunnerConfig(
        dry_run=True,
        max_files_docs=35,
        max_files_code=20,
        max_chars=650000,
        max_request_bytes=200000,
        file_truncate_chars=70000,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=True,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="default",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=1,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="cost",
        batch_mode=False,
        live_ok=False,
    )


def build_provider_readiness_matrix(config: PrescanConfig, catalog: dict[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    blocked_codes: set[str] = set()
    allow_online = bool(getattr(config, "allow_online_llm", False))
    probe_cfg = _build_probe_cfg() if allow_online else None
    for route in catalog.get("routes", []):
        if not isinstance(route, dict) or not bool(route.get("route_admissible")):
            continue
        if not allow_online:
            provider_probe = _offline_blocker(route, "online_llm_not_authorized")
        elif not bool(route.get("credential_present")):
            provider_probe = _offline_blocker(route, "missing_credential")
        else:
            provider_probe = _runner_module().run_provider_doctor_probe(
                str(route.get("provider") or ""),
                str(route.get("model_id") or ""),
                str(route.get("api_key_env") or ""),
                probe_cfg,
            )
        blocker = dict(provider_probe.get("readiness_blocker") or {})
        if blocker.get("blocker_code") and blocker.get("blocker_code") != "READY":
            blocked_codes.add(str(blocker["blocker_code"]))
        rows.append(
            {
                "provider": str(route.get("provider") or ""),
                "model_id": str(route.get("model_id") or ""),
                "api_key_env": str(route.get("api_key_env") or ""),
                "dependency_class": str(route.get("dependency_class") or ""),
                "economic_surface": str(route.get("economic_surface") or ""),
                "execution_transport": str(route.get("execution_transport") or ""),
                "route_admissible": bool(route.get("route_admissible")),
                "ready": bool(provider_probe.get("ready")),
                "provider_probe": provider_probe,
                "exclusion_reason": None if provider_probe.get("ready") else str(blocker.get("blocker_code") or "unknown_readiness_block"),
            }
        )
    rows.sort(key=lambda item: (str(item["provider"]), str(item["model_id"]), str(item["api_key_env"])))
    return {
        "status": "PASS" if rows and any(row["ready"] for row in rows) else "FAIL",
        "routes": rows,
        "failed_blocker_codes": sorted(blocked_codes),
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


def _ready_routes(catalog: dict[str, Any], readiness: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[tuple[str, str, str], str]]:
    readiness_by_key = {
        (str(row.get("provider") or ""), str(row.get("model_id") or ""), str(row.get("api_key_env") or "")): row
        for row in readiness.get("routes", [])
        if isinstance(row, dict)
    }
    eligible: list[dict[str, Any]] = []
    exclusions: dict[tuple[str, str, str], str] = {}
    for route in catalog.get("routes", []):
        if not isinstance(route, dict):
            continue
        key = (str(route.get("provider") or ""), str(route.get("model_id") or ""), str(route.get("api_key_env") or ""))
        row = readiness_by_key.get(key)
        if route.get("route_admissible") is False:
            exclusions[key] = str(route.get("route_admissibility_reason") or "inadmissible")
        elif row is None:
            exclusions[key] = "missing_provider_readiness"
        elif not bool(row.get("ready")):
            exclusions[key] = str(row.get("exclusion_reason") or "provider_not_ready")
        else:
            eligible.append(route)
    return eligible, exclusions


def _candidate_fallbacks(primary: dict[str, Any] | None, routes: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if primary is None:
        return [], []
    selected = [primary]
    selected_classes = {str(primary.get("dependency_class") or "")}
    selected_surfaces = {str(primary.get("economic_surface") or "")}
    decisions: list[dict[str, Any]] = []
    for route in routes:
        if route is primary:
            continue
        dependency_class = str(route.get("dependency_class") or "")
        economic_surface = str(route.get("economic_surface") or "")
        decision = {
            "provider": str(route.get("provider") or ""),
            "model_id": str(route.get("model_id") or ""),
        }
        if dependency_class in selected_classes:
            decisions.append({**decision, "decision": "excluded", "reason": "shared_dependency_class"})
            continue
        if economic_surface in selected_surfaces:
            decisions.append({**decision, "decision": "excluded", "reason": "shared_economic_surface"})
            continue
        primary_provider = str(primary.get("provider") or "")
        route_provider = str(route.get("provider") or "")
        primary_billing_unconfirmed = primary_provider == "openrouter" and not bool(
            primary.get("billing_independent_from_upstream")
        )
        route_billing_unconfirmed = route_provider == "openrouter" and not bool(
            route.get("billing_independent_from_upstream")
        )
        if primary_billing_unconfirmed or route_billing_unconfirmed:
            decisions.append({**decision, "decision": "excluded", "reason": "billing_independence_unconfirmed"})
            continue
        selected.append(route)
        selected_classes.add(dependency_class)
        selected_surfaces.add(economic_surface)
        decisions.append({**decision, "decision": "admitted", "reason": "distinct_dependency_and_economic_surface"})
    return selected, decisions


def build_prescan_routing_plan(
    config: PrescanConfig,
    catalog: dict[str, Any],
    readiness: dict[str, Any] | list[str] | None = None,
    passes: list[str] | None = None,
) -> dict[str, Any]:
    compatibility_mode = not isinstance(readiness, dict)
    if compatibility_mode:
        if passes is None:
            passes = readiness if isinstance(readiness, list) else None
        readiness = {
            "status": "PASS",
            "routes": [
                {
                    "provider": str(route.get("provider") or ""),
                    "model_id": str(route.get("model_id") or ""),
                    "api_key_env": str(route.get("api_key_env") or ""),
                    "ready": bool(route.get("available", True)),
                    "exclusion_reason": None if bool(route.get("available", True)) else "missing_provider_readiness",
                }
                for route in catalog.get("routes", [])
                if isinstance(route, dict)
            ],
        }
    if readiness is None:
        readiness = {"status": "PASS", "routes": []}
    requested_passes = [pass_id for pass_id in (passes or []) if pass_id in PRESCAN_PASS_REQUIREMENTS]
    routes, exclusions = _ready_routes(catalog, readiness)
    selected_routes: dict[str, dict[str, Any]] = {}
    candidate_routes: dict[str, list[dict[str, Any]]] = {}
    fallback_decisions: dict[str, list[dict[str, Any]]] = {}
    failures: list[dict[str, Any]] = []
    for pass_id in requested_passes:
        required_tier = PRESCAN_PASS_REQUIREMENTS[pass_id]
        tier_routes = [
            route for route in routes
            if PRESCAN_TIER_RANK.get(str(route.get("prescan_tier")), 0) >= PRESCAN_TIER_RANK[required_tier]
        ]
        selected, adjustment = _select_route_for_tier(tier_routes, required_tier)
        if selected is None:
            failures.append(
                {
                    "pass_id": pass_id,
                    "required_tier": required_tier,
                    "reason": "no_executable_route_after_provider_readiness",
                    "excluded_routes": [
                        {"provider": p, "model_id": m, "api_key_env": k, "reason": reason}
                        for (p, m, k), reason in sorted(exclusions.items())
                    ],
                }
            )
            continue
        ordered = sorted(
            tier_routes,
            key=lambda row: (
                PRESCAN_TIER_RANK.get(str(row.get("prescan_tier")), 99),
                float(((row.get("pricing") or {}).get("input_1m_usd", 999.0))),
                float(((row.get("pricing") or {}).get("output_1m_usd", 999.0))),
                str(row.get("provider") or ""),
                str(row.get("model_id") or ""),
            ),
        )
        candidates, decisions = _candidate_fallbacks(selected, ordered)
        fallback_decisions[pass_id] = decisions
        candidate_routes[pass_id] = [
            {
                "provider": str(route.get("provider") or ""),
                "model_id": str(route.get("model_id") or ""),
                "api_key_env": str(route.get("api_key_env") or ""),
                "prescan_tier": str(route.get("prescan_tier") or ""),
                "dependency_class": str(route.get("dependency_class") or ""),
                "economic_surface": str(route.get("economic_surface") or ""),
                "execution_transport": str(route.get("execution_transport") or ""),
                "pricing": dict(route.get("pricing") or {}),
            }
            for route in candidates
        ]
        selected_routes[pass_id] = {
            "pass_id": pass_id,
            "required_tier": required_tier,
            "selected_tier": str(selected.get("prescan_tier")),
            "tier_adjustment": adjustment,
            "provider": str(selected.get("provider")),
            "model_id": str(selected.get("model_id")),
            "api_key_env": str(selected.get("api_key_env")),
            "dependency_class": str(selected.get("dependency_class") or ""),
            "economic_surface": str(selected.get("economic_surface") or ""),
            "selection_basis": "lowest_estimated_cost_within_allowed_tier_band_after_readiness",
            "pricing": dict(selected.get("pricing") or {}),
            "legacy_route_changed": bool(
                str(config.provider) != str(selected.get("provider"))
                or str(config.model) != str(selected.get("model_id"))
                or str(config.api_key_env) != str(selected.get("api_key_env"))
            ),
        }

    return {
        "requested_passes": requested_passes,
        "status": ("FAIL" if compatibility_mode and failures else NO_LIVE_LANE if failures else "PASS"),
        "halt_before_stage_1": bool(failures),
        "failures": failures,
        "candidate_routes": candidate_routes,
        "selected_routes": selected_routes,
        "fallback_decisions": fallback_decisions,
        "provider_readiness_status": str(readiness.get("status") or "UNKNOWN"),
    }


def write_provider_catalog(output_dir: Path, catalog: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "prescan_provider_model_catalog.json"
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), **catalog}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_provider_readiness(output_dir: Path, readiness: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "prescan_provider_readiness.json"
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), **readiness}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_routing_plan(output_dir: Path, plan: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "prescan_routing_plan.json"
    payload = {"generated_at": datetime.now(timezone.utc).isoformat(), **plan}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_no_live_lane_artifact(output_dir: Path, plan: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "prescan_no_live_lane.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": NO_LIVE_LANE,
        "halt_before_stage_1": True,
        "requested_passes": list(plan.get("requested_passes") or []),
        "failures": list(plan.get("failures") or []),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_live_lane_success_artifact(output_dir: Path, plan: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "prescan_live_lane_success.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "LIVE_LANE_READY",
        "halt_before_stage_1": False,
        "requested_passes": list(plan.get("requested_passes") or []),
        "provider_readiness_status": str(plan.get("provider_readiness_status") or "UNKNOWN"),
        "selected_routes": dict(plan.get("selected_routes") or {}),
        "candidate_routes": dict(plan.get("candidate_routes") or {}),
        "fallback_decisions": dict(plan.get("fallback_decisions") or {}),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
