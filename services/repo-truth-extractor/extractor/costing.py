from __future__ import annotations

import threading
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import yaml

try:
    from lib.spend_ledger import (
        BASELINE_INPUT_COST_PER_1M_USD,
        BASELINE_OUTPUT_COST_PER_1M_USD,
        PRICING_VERSION,
        UNKNOWN_MODEL_POLICY,
    )
except ImportError:  # pragma: no cover - standalone fallback
    BASELINE_INPUT_COST_PER_1M_USD = 0.15
    BASELINE_OUTPUT_COST_PER_1M_USD = 0.60
    PRICING_VERSION = "baseline_v1"
    UNKNOWN_MODEL_POLICY = "baseline_v1_fallback"


@dataclass
class SpendTrackerState:
    run_root: Path
    run_id: str
    max_cost_usd: Decimal
    pricing_source: str
    pricing_sha256: str
    pricing_registry: Dict[str, Dict[str, Decimal]]
    total_cost_usd: Decimal
    cost_abort_triggered: bool
    abort_reason: Optional[str]
    entries: List[Dict[str, Any]]


class CostLimitExceededError(RuntimeError):
    def __init__(self, message: str, details: Dict[str, Any]) -> None:
        super().__init__(message)
        self.details = dict(details)


@dataclass(frozen=True)
class CostingDeps:
    selected_execution_step_ids_for_phase: Callable[[Any, str], Optional[list[str]]]
    collect_provider_routes: Callable[..., Dict[str, Dict[str, Any]]]
    load_pricing_registry: Callable[[], Tuple[Dict[str, Dict[str, Decimal]], str]]
    pricing_config_path: Path
    write_json: Callable[[Path, Dict[str, Any]], None]
    telemetry_path: Callable[[Path, str], Path]
    now_iso: Callable[[], str]
    pricing_surface_metadata: Callable[..., Dict[str, Any]]
    spend_ledger_filename: str


_SPEND_TRACKER_LOCK = threading.Lock()
_ACTIVE_SPEND_TRACKER: Optional[SpendTrackerState] = None


def _quantize_usd(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _pricing_key(provider: str, model_id: str) -> str:
    return f"{str(provider).strip().lower()}/{str(model_id).strip()}"


def load_pricing_registry(path: Path) -> Tuple[Dict[str, Dict[str, Decimal]], str]:
    if not path.exists():
        raise RuntimeError(f"Pricing config missing: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Pricing config must decode to an object: {path}")
    models = payload.get("models")
    if not isinstance(models, dict) or not models:
        raise RuntimeError(f"Pricing config missing models map: {path}")
    registry: Dict[str, Dict[str, Decimal]] = {}
    for key, row in models.items():
        if not isinstance(row, dict):
            raise RuntimeError(f"Pricing entry must be an object for {key}")
        if row.get("input_cost_per_m") is None or row.get("output_cost_per_m") is None:
            continue
        try:
            input_cost = Decimal(str(row["input_cost_per_m"]))
            output_cost = Decimal(str(row["output_cost_per_m"]))
        except Exception as exc:
            raise RuntimeError(f"Invalid pricing entry for {key}") from exc
        if input_cost < 0 or output_cost < 0:
            raise RuntimeError(f"Negative pricing entry for {key}")
        registry[str(key).strip().lower()] = {
            "input_cost_per_m": input_cost,
            "output_cost_per_m": output_cost,
        }
    from lib.promptgen.hashing import sha256_text

    return registry, sha256_text(path.read_text(encoding="utf-8"))


def extract_usage_summary(
    provider: str,
    response_obj: Any,
    response_json: Optional[Dict[str, Any]],
) -> Optional[Dict[str, int]]:
    if provider == "gemini":
        usage = getattr(response_obj, "usage_metadata", None)
        if usage is None and isinstance(response_json, dict):
            usage = response_json.get("usage_metadata")
        prompt_tokens = getattr(usage, "prompt_token_count", None)
        completion_tokens = getattr(usage, "candidates_token_count", None)
        total_tokens = getattr(usage, "total_token_count", None)
        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_token_count", prompt_tokens)
            completion_tokens = usage.get("candidates_token_count", completion_tokens)
            total_tokens = usage.get("total_token_count", total_tokens)
    else:
        usage = (
            response_json.get("usage")
            if isinstance(response_json, dict)
            else getattr(response_obj, "usage", None)
        )
        prompt_tokens = getattr(usage, "prompt_tokens", None)
        completion_tokens = getattr(usage, "completion_tokens", None)
        total_tokens = getattr(usage, "total_tokens", None)
        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
            completion_tokens = usage.get("completion_tokens", completion_tokens)
            total_tokens = usage.get("total_tokens", total_tokens)

    def _to_int(value: Any) -> Optional[int]:
        try:
            if value is None or value == "":
                return None
            return int(value)
        except Exception:
            return None

    prompt_value = _to_int(prompt_tokens)
    completion_value = _to_int(completion_tokens)
    total_value = _to_int(total_tokens)
    if prompt_value is None and completion_value is None and total_value is None:
        return None
    if total_value is None and prompt_value is not None and completion_value is not None:
        total_value = prompt_value + completion_value
    return {
        "prompt_tokens": int(prompt_value or 0),
        "completion_tokens": int(completion_value or 0),
        "total_tokens": int(total_value or 0),
    }


def estimate_usage_cost_usd(
    *,
    provider: str,
    model_id: str,
    usage: Dict[str, int],
    pricing_registry: Dict[str, Dict[str, Decimal]],
) -> Decimal:
    key = _pricing_key(provider, model_id)
    pricing = pricing_registry.get(key)
    if pricing is None:
        raise RuntimeError(f"Missing pricing for route {key}")
    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    input_cost = (Decimal(prompt_tokens) / Decimal(1_000_000)) * pricing["input_cost_per_m"]
    output_cost = (Decimal(completion_tokens) / Decimal(1_000_000)) * pricing["output_cost_per_m"]
    return _quantize_usd(input_cost + output_cost)


def get_active_spend_tracker() -> Optional[SpendTrackerState]:
    with _SPEND_TRACKER_LOCK:
        return _ACTIVE_SPEND_TRACKER


def is_spend_tracker_aborted() -> bool:
    state = get_active_spend_tracker()
    return bool(state is not None and state.cost_abort_triggered)


def _write_spend_ledger_snapshot(
    deps: CostingDeps,
    state: SpendTrackerState,
) -> Dict[str, Any]:
    totals_by_provider: Dict[str, Decimal] = {}
    totals_by_model: Dict[str, Decimal] = {}
    totals_by_phase: Dict[str, Decimal] = {}
    totals_by_step: Dict[str, Decimal] = {}
    for row in state.entries:
        cost = Decimal(str(row.get("cost_usd", "0")))
        provider = str(row.get("provider") or "")
        model_id = str(row.get("model_id") or "")
        phase = str(row.get("phase") or "")
        step_id = str(row.get("step_id") or "")
        if provider:
            totals_by_provider[provider] = totals_by_provider.get(provider, Decimal("0")) + cost
        if provider and model_id:
            model_key = f"{provider}/{model_id}"
            totals_by_model[model_key] = totals_by_model.get(model_key, Decimal("0")) + cost
        if phase:
            totals_by_phase[phase] = totals_by_phase.get(phase, Decimal("0")) + cost
        if phase and step_id:
            step_key = f"{phase}:{step_id}"
            totals_by_step[step_key] = totals_by_step.get(step_key, Decimal("0")) + cost
    payload = {
        "generated_at": deps.now_iso(),
        "run_id": state.run_id,
        "pricing_source": state.pricing_source,
        "pricing_sha256": state.pricing_sha256,
        "max_cost_usd": float(state.max_cost_usd),
        "total_cost_usd": float(_quantize_usd(state.total_cost_usd)),
        "cost_abort_triggered": state.cost_abort_triggered,
        "abort_reason": state.abort_reason,
        "entries_total": len(state.entries),
        "totals_by_provider_usd": {
            key: float(_quantize_usd(value))
            for key, value in sorted(totals_by_provider.items())
        },
        "totals_by_model_usd": {
            key: float(_quantize_usd(value))
            for key, value in sorted(totals_by_model.items())
        },
        "totals_by_phase_usd": {
            key: float(_quantize_usd(value))
            for key, value in sorted(totals_by_phase.items())
        },
        "totals_by_step_usd": {
            key: float(_quantize_usd(value))
            for key, value in sorted(totals_by_step.items())
        },
        "entries": list(state.entries),
    }
    deps.write_json(deps.telemetry_path(state.run_root, deps.spend_ledger_filename), payload)
    return payload


def reset_spend_tracker() -> None:
    global _ACTIVE_SPEND_TRACKER
    with _SPEND_TRACKER_LOCK:
        _ACTIVE_SPEND_TRACKER = None


def initialize_spend_tracker(
    *,
    deps: CostingDeps,
    run_root: Path,
    run_id: str,
    cfg: Any,
    phases: Sequence[str],
) -> Optional[Dict[str, Any]]:
    global _ACTIVE_SPEND_TRACKER
    if cfg.max_cost_usd is None:
        reset_spend_tracker()
        return None
    if cfg.partition_workers != 1:
        raise RuntimeError("--max-cost-usd requires --partition-workers 1 for deterministic enforcement.")
    selected_step_ids_by_phase = {
        phase: selected_ids
        for phase in phases
        if (selected_ids := deps.selected_execution_step_ids_for_phase(cfg, phase)) is not None
    }
    pricing_registry, pricing_sha = deps.load_pricing_registry()
    routes = deps.collect_provider_routes(
        phases=phases,
        routing_policy=cfg.routing_policy,
        selected_step_ids_by_phase=selected_step_ids_by_phase or None,
        cost_profile=cfg.cost_profile,
    )
    missing = sorted(
        _pricing_key(route["provider"], route["model_id"])
        for route in routes.values()
        if _pricing_key(route["provider"], route["model_id"]) not in pricing_registry
    )
    if missing:
        raise RuntimeError(
            "Pricing config missing route coverage for active target: "
            + ", ".join(missing)
        )
    state = SpendTrackerState(
        run_root=run_root,
        run_id=run_id,
        max_cost_usd=_quantize_usd(Decimal(str(cfg.max_cost_usd))),
        pricing_source=str(deps.pricing_config_path.resolve()),
        pricing_sha256=pricing_sha,
        pricing_registry=pricing_registry,
        total_cost_usd=Decimal("0"),
        cost_abort_triggered=False,
        abort_reason=None,
        entries=[],
    )
    with _SPEND_TRACKER_LOCK:
        _ACTIVE_SPEND_TRACKER = state
        return _write_spend_ledger_snapshot(deps, state)


def record_request_cost(
    *,
    deps: CostingDeps,
    meta: Dict[str, Any],
    phase: str,
    step_id: str,
    partition_id: str,
    provider: str,
    model_id: str,
) -> Dict[str, Any]:
    if not isinstance(meta, dict):
        return meta
    if meta.get("spend_ledger_recorded"):
        return meta
    if meta.get("failure_type") == "cost_aborted":
        return meta
    with _SPEND_TRACKER_LOCK:
        state = _ACTIVE_SPEND_TRACKER
        if state is None:
            return meta
        if state.cost_abort_triggered:
            updated = dict(meta)
            updated["spend_ledger_recorded"] = False
            updated["cost_cap"] = {
                "max_cost_usd": float(state.max_cost_usd),
                "total_cost_usd": float(_quantize_usd(state.total_cost_usd)),
                "cost_abort_triggered": True,
                "abort_reason": state.abort_reason,
            }
            updated["failure_type"] = "cost_aborted"
            updated["provider_error_reason"] = state.abort_reason
            return updated
        response_summary = meta.get("response_summary")
        usage = (
            dict(response_summary.get("usage"))
            if isinstance(response_summary, dict)
            and isinstance(response_summary.get("usage"), dict)
            else None
        )
        if usage is None:
            state.cost_abort_triggered = True
            state.abort_reason = "cost_cap_usage_unavailable"
            _write_spend_ledger_snapshot(deps, state)
            updated = dict(meta)
            updated["spend_ledger_recorded"] = False
            updated["cost_cap"] = {
                "max_cost_usd": float(state.max_cost_usd),
                "total_cost_usd": float(_quantize_usd(state.total_cost_usd)),
                "cost_abort_triggered": True,
                "abort_reason": state.abort_reason,
            }
            updated["failure_type"] = "cost_aborted"
            updated["provider_error_reason"] = state.abort_reason
            return updated
        cost_usd = estimate_usage_cost_usd(
            provider=provider,
            model_id=model_id,
            usage=usage,
            pricing_registry=state.pricing_registry,
        )
        state.total_cost_usd = _quantize_usd(state.total_cost_usd + cost_usd)
        pricing_meta = deps.pricing_surface_metadata(
            provider=provider,
            model_id=model_id,
            api_key_env=(
                str(
                    meta.get("api_key_env")
                    or meta.get("api_key_env_resolved")
                    or meta.get("api_key_env_requested")
                    or ""
                )
                or None
            ),
            route_identity=meta,
            endpoint_effective=(
                str(meta.get("endpoint_effective"))
                if meta.get("endpoint_effective") is not None
                else None
            ),
            transport=(
                str(meta.get("transport"))
                if meta.get("transport") is not None
                else None
            ),
            provider_signature=(
                str(meta.get("provider_signature"))
                if meta.get("provider_signature") is not None
                else None
            ),
            route_fingerprint_hash=(
                str(meta.get("route_fingerprint_hash"))
                if meta.get("route_fingerprint_hash") is not None
                else None
            ),
        )
        event = {
            "sequence": len(state.entries) + 1,
            "recorded_at": deps.now_iso(),
            "phase": phase,
            "step_id": step_id,
            "partition_id": partition_id,
            "provider": provider,
            "model_id": model_id,
            "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
            "cost_usd": float(cost_usd),
            "total_cost_usd_after_event": float(_quantize_usd(state.total_cost_usd)),
            **pricing_meta,
        }
        state.entries.append(event)
        if state.total_cost_usd > state.max_cost_usd:
            state.cost_abort_triggered = True
            state.abort_reason = (
                f"cost_cap_exceeded total_cost_usd={float(_quantize_usd(state.total_cost_usd))} "
                f"max_cost_usd={float(state.max_cost_usd)}"
            )
        _write_spend_ledger_snapshot(deps, state)
        updated = dict(meta)
        updated["spend_ledger_recorded"] = True
        updated["cost_event"] = dict(event)
        updated["cost_cap"] = {
            "max_cost_usd": float(state.max_cost_usd),
            "total_cost_usd": float(_quantize_usd(state.total_cost_usd)),
            "cost_abort_triggered": state.cost_abort_triggered,
            "abort_reason": state.abort_reason,
        }
        if state.cost_abort_triggered:
            updated["failure_type"] = "cost_aborted"
            updated["provider_error_reason"] = state.abort_reason
        return updated
