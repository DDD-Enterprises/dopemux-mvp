import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# TP-RTE-TRUTH-R2-001 (F-10 / F-11): this module used to keep its OWN
# hardcoded $0.15/$0.60 baseline registry, silently overwritten by
# benchmarking.pricing.catalog when importable and silently KEPT (fail-open)
# whenever that import or load failed — meaning a broken catalog reprices
# every model, including a true $5/$30 model, at 33-50x under cost while
# still reporting itself "priced" (match_type exact, unknown_model False).
# That entire fail-open path is deleted. There is now exactly ONE pricing
# authority for this whole service: extractor.costing.load_pricing_registry
# (reads config/pricing.yaml directly, raises on any load problem — fail
# closed, never a silent reprice) + extractor.costing.resolve_model_rate
# (the same candidate-matching lookup E3's accounting already used). SpendLedger
# below is a thin, backward-compatible façade over that authority.
# --------------------------------------------------------------------------
PRICING_VERSION = "baseline_v1"
UNKNOWN_MODEL_POLICY = "baseline_v1_fallback"
BASELINE_INPUT_COST_PER_1M_USD = 0.15
BASELINE_OUTPUT_COST_PER_1M_USD = 0.60

from extractor.costing import (  # noqa: E402
    compute_optimized_cost,
    load_pricing_registry_cached,
    make_projected_cost_check,
    resolve_model_rate,
)
from rte_config import PRICING_CONFIG_PATH  # noqa: E402

try:
    from lib.pricing_surface import pricing_surface_metadata
except ImportError:  # pragma: no cover - direct file imports in legacy tests
    import importlib.util

    _pricing_surface_path = Path(__file__).with_name("pricing_surface.py")
    _pricing_surface_spec = importlib.util.spec_from_file_location(
        "repo_truth_pricing_surface", _pricing_surface_path
    )
    if _pricing_surface_spec is None or _pricing_surface_spec.loader is None:
        raise
    _pricing_surface_module = importlib.util.module_from_spec(_pricing_surface_spec)
    _pricing_surface_spec.loader.exec_module(_pricing_surface_module)
    pricing_surface_metadata = _pricing_surface_module.pricing_surface_metadata


@dataclass
class ProviderSpend:
    provider: str
    usage_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


@dataclass
class ModelSpend:
    provider: str
    model_id: str
    pricing_key: str
    pricing_source: str
    requested_provider: str = "unknown"
    requested_model_id: str = ""
    provider_route_kind: str = "unknown"
    upstream_provider: str = "unknown"
    economic_surface: str = "unknown"
    api_key_env: str | None = None
    endpoint_effective: str | None = None
    transport: str | None = None
    provider_signature: str | None = None
    route_fingerprint_hash: str | None = None
    pricing_authority: str = "unknown"
    pricing_surface: str = "unknown"
    pricing_surface_source: str = "static_request_route_metadata"
    pricing_live_validation_status: str = "UNKNOWN"
    direct_provider_billing_inherited: bool | None = None
    pricing_version: str = PRICING_VERSION
    unknown_model: bool = False
    usage_count: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    input_cost_per_1m_usd: float = BASELINE_INPUT_COST_PER_1M_USD
    output_cost_per_1m_usd: float = BASELINE_OUTPUT_COST_PER_1M_USD


@dataclass
class PhaseSpend:
    phase: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    models: Dict[str, ModelSpend] = field(default_factory=dict)
    providers: Dict[str, ProviderSpend] = field(default_factory=dict)


@dataclass
class SpendLedgerRecord:
    run_id: str
    global_max_cost_usd: float | None = None
    pricing_version: str = PRICING_VERSION
    unknown_model_policy: str = UNKNOWN_MODEL_POLICY
    phases: Dict[str, PhaseSpend] = field(default_factory=dict)
    models: Dict[str, ModelSpend] = field(default_factory=dict)
    providers: Dict[str, ProviderSpend] = field(default_factory=dict)
    total_cost_usd: float = 0.0
    unknown_model_events: int = 0
    fallback_usage_count: int = 0


def _safe_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except Exception:
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except Exception:
        return 0.0


MODEL_SURFACE_FIELDS = (
    "requested_provider",
    "requested_model_id",
    "provider_route_kind",
    "upstream_provider",
    "economic_surface",
    "api_key_env",
    "endpoint_effective",
    "transport",
    "provider_signature",
    "route_fingerprint_hash",
    "pricing_authority",
    "pricing_surface",
    "pricing_surface_source",
    "pricing_live_validation_status",
    "direct_provider_billing_inherited",
)


def _model_surface_from_payload(model_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: model_data.get(key)
        for key in MODEL_SURFACE_FIELDS
        if key in model_data
    }


def get_model_cost_rate(
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
    route: Optional[str] = None,
) -> Dict[str, Any]:
    """Backward-compatible façade over the single pricing authority.

    Loads config/pricing.yaml through extractor.costing.load_pricing_registry_cached
    (raises RuntimeError on any catalog problem — fail closed, F-10 fix) and
    resolves the route through extractor.costing.resolve_model_rate (the same
    candidate-matching lookup E3's accounting uses). Callers that relied on
    this function's exact return shape (lib/prescan/cost_estimator.py,
    benchmarking/direct_model/spend.py, lib/prescan/provider_catalog.py's
    mocked tests) keep working unchanged.

    Raises RuntimeError if the pricing catalog itself cannot be loaded. Does
    NOT raise for an unknown model — that returns unknown_model=True with
    UNPRICED status and a $0.00 rate (no fabricated number); callers that
    need "unknown model + cap set -> raise" apply that policy themselves
    (see SpendLedger.price_usage below).
    """
    pricing_registry, _pricing_sha = load_pricing_registry_cached(PRICING_CONFIG_PATH)
    resolved = resolve_model_rate(pricing_registry, provider, model_id, route)
    surface = pricing_surface_metadata(
        provider=resolved["provider"],
        model_id=resolved["model_id"],
        route=route,
    )
    return {
        **resolved,
        **surface,
        "pricing_version": PRICING_VERSION,
    }


class SpendLedger:
    def __init__(self, run_dir: Path, run_id: str, max_cost_usd: float | None = None):
        self.ledger_path = run_dir / "spend_ledger.json"
        self.record = SpendLedgerRecord(
            run_id=run_id,
            global_max_cost_usd=max_cost_usd,
        )
        self._lock = threading.Lock()
        self._load()

    def _provider_from_payload(self, provider_name: str, provider_data: Dict[str, Any]) -> ProviderSpend:
        return ProviderSpend(
            provider=provider_name,
            usage_count=_safe_int(provider_data.get("usage_count", 0)),
            input_tokens=_safe_int(provider_data.get("input_tokens", 0)),
            output_tokens=_safe_int(provider_data.get("output_tokens", 0)),
            estimated_cost_usd=_safe_float(provider_data.get("estimated_cost_usd", 0.0)),
        )

    def _phase_from_payload(self, phase_name: str, phase_data: Dict[str, Any]) -> PhaseSpend:
        phase_spend = PhaseSpend(
            phase=phase_name,
            input_tokens=_safe_int(phase_data.get("input_tokens", 0)),
            output_tokens=_safe_int(phase_data.get("output_tokens", 0)),
            estimated_cost_usd=_safe_float(phase_data.get("estimated_cost_usd", 0.0)),
        )
        models = phase_data.get("models")
        if isinstance(models, dict):
            for model_key, model_data in models.items():
                if not isinstance(model_data, dict):
                    continue
                phase_spend.models[str(model_key)] = ModelSpend(
                    provider=str(model_data.get("provider") or ""),
                    model_id=str(model_data.get("model_id") or ""),
                    pricing_key=str(model_data.get("pricing_key") or model_key),
                    pricing_source=str(model_data.get("pricing_source") or "legacy_load"),
                    **_model_surface_from_payload(model_data),
                    pricing_version=str(
                        model_data.get("pricing_version") or self.record.pricing_version
                    ),
                    unknown_model=bool(model_data.get("unknown_model", False)),
                    usage_count=_safe_int(model_data.get("usage_count", 0)),
                    input_tokens=_safe_int(model_data.get("input_tokens", 0)),
                    output_tokens=_safe_int(model_data.get("output_tokens", 0)),
                    estimated_cost_usd=_safe_float(
                        model_data.get("estimated_cost_usd", 0.0)
                    ),
                    input_cost_per_1m_usd=_safe_float(
                        model_data.get(
                            "input_cost_per_1m_usd", BASELINE_INPUT_COST_PER_1M_USD
                        )
                    ),
                    output_cost_per_1m_usd=_safe_float(
                        model_data.get(
                            "output_cost_per_1m_usd", BASELINE_OUTPUT_COST_PER_1M_USD
                        )
                    ),
                )
        providers = phase_data.get("providers")
        if isinstance(providers, dict):
            for provider_name, provider_data in providers.items():
                if not isinstance(provider_data, dict):
                    continue
                phase_spend.providers[str(provider_name)] = self._provider_from_payload(
                    str(provider_name), provider_data
                )
        return phase_spend

    def _models_from_payload(self, payload: Dict[str, Any]) -> Dict[str, ModelSpend]:
        loaded: Dict[str, ModelSpend] = {}
        for model_key, model_data in payload.items():
            if not isinstance(model_data, dict):
                continue
            loaded[str(model_key)] = ModelSpend(
                provider=str(model_data.get("provider") or ""),
                model_id=str(model_data.get("model_id") or ""),
                pricing_key=str(model_data.get("pricing_key") or model_key),
                pricing_source=str(model_data.get("pricing_source") or "legacy_load"),
                **_model_surface_from_payload(model_data),
                pricing_version=str(
                    model_data.get("pricing_version") or self.record.pricing_version
                ),
                unknown_model=bool(model_data.get("unknown_model", False)),
                usage_count=_safe_int(model_data.get("usage_count", 0)),
                input_tokens=_safe_int(model_data.get("input_tokens", 0)),
                output_tokens=_safe_int(model_data.get("output_tokens", 0)),
                estimated_cost_usd=_safe_float(model_data.get("estimated_cost_usd", 0.0)),
                input_cost_per_1m_usd=_safe_float(
                    model_data.get(
                        "input_cost_per_1m_usd", BASELINE_INPUT_COST_PER_1M_USD
                    )
                ),
                output_cost_per_1m_usd=_safe_float(
                    model_data.get(
                        "output_cost_per_1m_usd", BASELINE_OUTPUT_COST_PER_1M_USD
                    )
                ),
            )
        return loaded

    def _providers_from_payload(self, payload: Dict[str, Any]) -> Dict[str, ProviderSpend]:
        loaded: Dict[str, ProviderSpend] = {}
        for provider_name, provider_data in payload.items():
            if not isinstance(provider_data, dict):
                continue
            loaded[str(provider_name)] = self._provider_from_payload(
                str(provider_name), provider_data
            )
        return loaded

    def _load(self) -> None:
        if not self.ledger_path.exists():
            return
        try:
            data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
            self.record.total_cost_usd = _safe_float(data.get("total_cost_usd", 0.0))
            self.record.pricing_version = str(
                data.get("pricing_version") or PRICING_VERSION
            )
            self.record.unknown_model_policy = str(
                data.get("unknown_model_policy") or UNKNOWN_MODEL_POLICY
            )
            self.record.unknown_model_events = _safe_int(
                data.get("unknown_model_events", 0)
            )
            self.record.fallback_usage_count = _safe_int(
                data.get("fallback_usage_count", self.record.unknown_model_events)
            )
            for phase_name, phase_data in data.get("phases", {}).items():
                if not isinstance(phase_data, dict):
                    continue
                self.record.phases[str(phase_name)] = self._phase_from_payload(
                    str(phase_name), phase_data
                )
            models = data.get("models")
            if isinstance(models, dict):
                self.record.models = self._models_from_payload(models)
            providers = data.get("providers")
            if isinstance(providers, dict):
                self.record.providers = self._providers_from_payload(providers)
        except Exception as exc:
            logger.warning("Could not load existing spend ledger: %s", exc)

    def _save(self) -> None:
        try:
            self.ledger_path.write_text(
                json.dumps(asdict(self.record), indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error("Failed to save spend ledger: %s", exc)

    def price_usage(
        self,
        *,
        input_tokens: int,
        output_tokens: int,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        route: Optional[str] = None,
        cached_input_tokens: int = 0,
        service_tier: Optional[str] = None,
        is_batch: bool = False,
        prompt_token_count: Optional[int] = None,
        data_residency: str = "global",
    ) -> Dict[str, Any]:
        """Price a single LLM call.

        Backwards-compatible: callers that omit cached_input_tokens / service_tier
        / is_batch / prompt_token_count get the same flat pricing as before
        (just based on input/output rates).

        New: when these optimizer params are supplied, the returned dict
        includes the full `compute_optimized_cost` breakdown alongside the
        legacy `estimated_cost_usd` field. The legacy field becomes the
        optimizer-adjusted final cost so existing callers (accumulate, etc.)
        record the *effective* price they paid, not the headline rate.

        Unknown-model policy (TP-RTE-TRUTH-R2-001, F-10/F-11): when this
        ledger has a spend cap (`global_max_cost_usd is not None` — the exact
        same condition run_extraction_v5.py uses to decide a cap is active),
        an unknown model raises RuntimeError instead of silently pricing at
        $0.00/UNPRICED. A cap means the operator is relying on cost figures
        to make a stop/go decision; pricing an unpriced model at $0 would
        silently understate real spend and let it slip past the cap
        undetected — worse than the old $0.15/$0.60 baseline bug, not
        better. Without a cap, the call proceeds and the returned dict
        carries unknown_model=True / pricing_status=UNPRICED_UNKNOWN with a
        $0.00 rate — never a fabricated dollar figure.
        """
        resolved = get_model_cost_rate(provider=provider, model_id=model_id, route=route)
        if resolved.get("unknown_model") and self.record.global_max_cost_usd is not None:
            raise RuntimeError(
                "Unknown model pricing with a spend cap set "
                f"(max_cost_usd={self.record.global_max_cost_usd}): "
                f"provider={provider!r} model_id={model_id!r} route={route!r}. "
                "Add a priced row to config/pricing.yaml before running this "
                "route under a cost cap."
            )
        breakdown = compute_optimized_cost(
            resolved,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cached_input_tokens=cached_input_tokens,
            service_tier=service_tier,
            is_batch=is_batch,
            prompt_token_count=prompt_token_count,
            data_residency=data_residency,
        )
        return {
            **resolved,
            "input_tokens": breakdown["input_tokens"],
            "output_tokens": breakdown["output_tokens"],
            "estimated_cost_usd": breakdown["final_cost_usd"],
            "cost_breakdown": breakdown,
        }

    def accumulate(
        self,
        phase: str,
        input_tokens: int,
        output_tokens: int,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        route: Optional[str] = None,
        *,
        cached_input_tokens: int = 0,
        service_tier: Optional[str] = None,
        is_batch: bool = False,
        prompt_token_count: Optional[int] = None,
        data_residency: str = "global",
    ) -> Dict[str, Any]:
        with self._lock:
            priced = self.price_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                provider=provider,
                model_id=model_id,
                route=route,
                cached_input_tokens=cached_input_tokens,
                service_tier=service_tier,
                is_batch=is_batch,
                prompt_token_count=prompt_token_count,
                data_residency=data_residency,
            )
            if phase not in self.record.phases:
                self.record.phases[phase] = PhaseSpend(phase=phase)
            phase_spend = self.record.phases[phase]
            phase_spend.input_tokens += priced["input_tokens"]
            phase_spend.output_tokens += priced["output_tokens"]
            phase_spend.estimated_cost_usd += priced["estimated_cost_usd"]

            model_key = str(priced["pricing_key"])
            phase_model = phase_spend.models.get(model_key)
            if phase_model is None:
                phase_model = ModelSpend(
                    provider=str(priced["provider"]),
                    model_id=str(priced["model_id"]),
                    pricing_key=model_key,
                    pricing_source=str(priced["pricing_source"]),
                    **_model_surface_from_payload(priced),
                    pricing_version=str(priced["pricing_version"]),
                    unknown_model=bool(priced["unknown_model"]),
                    input_cost_per_1m_usd=_safe_float(priced["input_cost_per_1m_usd"]),
                    output_cost_per_1m_usd=_safe_float(priced["output_cost_per_1m_usd"]),
                )
                phase_spend.models[model_key] = phase_model
            phase_model.usage_count += 1
            phase_model.input_tokens += priced["input_tokens"]
            phase_model.output_tokens += priced["output_tokens"]
            phase_model.estimated_cost_usd += priced["estimated_cost_usd"]

            provider_key = str(priced["provider"] or "unknown")
            phase_provider = phase_spend.providers.get(provider_key)
            if phase_provider is None:
                phase_provider = ProviderSpend(provider=provider_key)
                phase_spend.providers[provider_key] = phase_provider
            phase_provider.usage_count += 1
            phase_provider.input_tokens += priced["input_tokens"]
            phase_provider.output_tokens += priced["output_tokens"]
            phase_provider.estimated_cost_usd += priced["estimated_cost_usd"]

            global_model = self.record.models.get(model_key)
            if global_model is None:
                global_model = ModelSpend(
                    provider=str(priced["provider"]),
                    model_id=str(priced["model_id"]),
                    pricing_key=model_key,
                    pricing_source=str(priced["pricing_source"]),
                    **_model_surface_from_payload(priced),
                    pricing_version=str(priced["pricing_version"]),
                    unknown_model=bool(priced["unknown_model"]),
                    input_cost_per_1m_usd=_safe_float(priced["input_cost_per_1m_usd"]),
                    output_cost_per_1m_usd=_safe_float(priced["output_cost_per_1m_usd"]),
                )
                self.record.models[model_key] = global_model
            global_model.usage_count += 1
            global_model.input_tokens += priced["input_tokens"]
            global_model.output_tokens += priced["output_tokens"]
            global_model.estimated_cost_usd += priced["estimated_cost_usd"]

            global_provider = self.record.providers.get(provider_key)
            if global_provider is None:
                global_provider = ProviderSpend(provider=provider_key)
                self.record.providers[provider_key] = global_provider
            global_provider.usage_count += 1
            global_provider.input_tokens += priced["input_tokens"]
            global_provider.output_tokens += priced["output_tokens"]
            global_provider.estimated_cost_usd += priced["estimated_cost_usd"]

            if priced["unknown_model"]:
                self.record.unknown_model_events += 1
                self.record.fallback_usage_count += 1
                logger.warning(
                    "SpendLedger using unknown-model fallback pricing provider=%s model=%s pricing_key=%s policy=%s",
                    priced["provider"] or "unknown",
                    priced["model_id"] or "unknown",
                    model_key,
                    self.record.unknown_model_policy,
                )

            self.record.total_cost_usd += priced["estimated_cost_usd"]
            self._save()
            return priced

    def check_limit(self, additional_cost_usd: float = 0.0) -> bool:
        if self.record.global_max_cost_usd is None:
            return True
        projected = self.record.total_cost_usd + _safe_float(additional_cost_usd)
        return projected <= self.record.global_max_cost_usd
