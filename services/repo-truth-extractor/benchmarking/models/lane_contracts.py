from __future__ import annotations

from typing import Any

from ..storage.hashing import hash_json


def _route_signature_from_trace(route_trace: dict[str, Any], fallback_route_id: str) -> dict[str, list[str]]:
    step_route_counts = route_trace.get("step_route_counts")
    if isinstance(step_route_counts, dict) and step_route_counts:
        return {
            str(step_id): [str(item) for item in routes]
            for step_id, routes in sorted(step_route_counts.items())
            if isinstance(routes, list) and routes
        }
    route_hops = [str(item) for item in route_trace.get("route_hops", []) if str(item)]
    selected_route_id = str(route_trace.get("logical_route_id") or fallback_route_id)
    effective_route = route_hops or [selected_route_id]
    return {"effective_route": effective_route}


def build_runtime_route_attempt_payload(
    *,
    declared_route_id: str,
    route_trace: dict[str, Any],
    route_telemetry_refs: list[str],
    admissibility_status: str,
    admissibility_blocker_codes: list[str] | None = None,
    admissibility_notes: list[str] | None = None,
) -> dict[str, Any]:
    selected_identity = dict(route_trace.get("selected_route_identity") or {})
    selected_route_id = str(
        selected_identity.get("declared_route_id")
        or route_trace.get("logical_route_id")
        or declared_route_id
    )
    selected_identity.setdefault("declared_route_id", selected_route_id)
    effective_route_signature = _route_signature_from_trace(route_trace, selected_route_id)
    return {
        "declared_route_id": declared_route_id,
        "selected_route_id": selected_route_id,
        "selected_route_identity": selected_identity,
        "effective_route_signature": effective_route_signature,
        "effective_route_signature_hash": hash_json(effective_route_signature),
        "admissibility_status": admissibility_status,
        "admissibility_blocker_codes": list(admissibility_blocker_codes or []),
        "admissibility_notes": list(admissibility_notes or []),
        "route_telemetry_refs": list(route_telemetry_refs),
    }


def build_direct_model_attempt_payload(
    *,
    declared_provider_name: str,
    declared_model_key: str,
    selected_provider_name: str,
    selected_model_key: str,
    direct_request_ref: str,
    direct_response_ref: str,
    pricing_metrics: dict[str, float | int],
    latency_metrics: dict[str, float | int],
    validator_results_ref: str,
    retry_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "declared_provider_name": declared_provider_name,
        "declared_model_key": declared_model_key,
        "selected_provider_name": selected_provider_name,
        "selected_model_key": selected_model_key,
        "direct_request_ref": direct_request_ref,
        "direct_response_ref": direct_response_ref,
        "pricing_metrics": dict(pricing_metrics),
        "latency_metrics": dict(latency_metrics),
        "validator_results_ref": validator_results_ref,
        "retry_metadata": dict(retry_metadata or {}),
    }


def build_profile_synthesis_input_payload(
    *,
    profile_id: str,
    source_attempt_ids: list[str],
    source_rollup_ids: list[str],
    pricing_source_refs: list[str] | None = None,
    governance_source_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "profile_id": profile_id,
        "source_attempt_ids": list(source_attempt_ids),
        "source_rollup_ids": list(source_rollup_ids),
        "pricing_source_refs": list(pricing_source_refs or []),
        "governance_source_refs": list(governance_source_refs or []),
    }
