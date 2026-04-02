import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Repo-local pricing authority is incomplete in this checkout. Until a canonical
# config/pricing.yaml exists, keep a deterministic baseline registry and make
# the fallback policy explicit in the ledger output instead of inventing rates.
PRICING_VERSION = "baseline_v1"
UNKNOWN_MODEL_POLICY = "baseline_v1_fallback"
BASELINE_INPUT_COST_PER_1M_USD = 0.15
BASELINE_OUTPUT_COST_PER_1M_USD = 0.60

_KNOWN_MODEL_KEYS = {
    "openai/gpt-5-nano",
    "openai/gpt-5-mini",
    "openai/gpt-5.2",
    "gemini/gemini-2.5-flash",
    "gemini/gemini-2.5-pro",
    "xai/grok-code-fast-1",
    "openrouter/openai/gpt-5-nano",
    "openrouter/openai/gpt-5-mini",
}


@dataclass
class ModelSpend:
    provider: str
    model_id: str
    pricing_key: str
    pricing_source: str
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


@dataclass
class SpendLedgerRecord:
    run_id: str
    global_max_cost_usd: float | None = None
    pricing_version: str = PRICING_VERSION
    unknown_model_policy: str = UNKNOWN_MODEL_POLICY
    phases: Dict[str, PhaseSpend] = field(default_factory=dict)
    models: Dict[str, ModelSpend] = field(default_factory=dict)
    total_cost_usd: float = 0.0
    unknown_model_events: int = 0


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


def _normalize_provider_model(
    provider: Optional[str],
    model_id: Optional[str],
) -> Tuple[str, str]:
    provider_token = str(provider or "").strip().lower()
    model_token = str(model_id or "").strip()
    if not provider_token and "/" in model_token:
        first, rest = model_token.split("/", 1)
        if first:
            return first.strip().lower(), rest.strip()
    return provider_token, model_token


def _pricing_candidates(provider: str, model_id: str) -> list[str]:
    provider_token, model_token = _normalize_provider_model(provider, model_id)
    lower_model = model_token.lower()
    candidates: list[str] = []

    def _push(token: str) -> None:
        normalized = str(token or "").strip().lower()
        if normalized and normalized not in candidates:
            candidates.append(normalized)

    if provider_token and lower_model:
        _push(f"{provider_token}/{lower_model}")
    _push(lower_model)
    if "/" in lower_model:
        _push(lower_model.split("/", 1)[1])
        parts = lower_model.split("/")
        if len(parts) >= 2:
            _push("/".join(parts[-2:]))
    return candidates


def _resolve_pricing(provider: Optional[str], model_id: Optional[str]) -> Dict[str, Any]:
    provider_token, model_token = _normalize_provider_model(provider, model_id)
    lookup_key = ""
    for candidate in _pricing_candidates(provider_token, model_token):
        if candidate in _KNOWN_MODEL_KEYS:
            lookup_key = candidate
            break
    if not lookup_key:
        fallback_key = ""
        if provider_token and model_token:
            fallback_key = f"{provider_token}/{model_token}".lower()
        elif model_token:
            fallback_key = model_token.lower()
        lookup_key = fallback_key or "unknown"
    unknown_model = lookup_key not in _KNOWN_MODEL_KEYS
    pricing_source = (
        "known_route_baseline_registry"
        if not unknown_model
        else f"unknown_model:{UNKNOWN_MODEL_POLICY}"
    )
    return {
        "provider": provider_token,
        "model_id": model_token,
        "pricing_key": lookup_key,
        "pricing_source": pricing_source,
        "pricing_version": PRICING_VERSION,
        "unknown_model": unknown_model,
        "input_cost_per_1m_usd": BASELINE_INPUT_COST_PER_1M_USD,
        "output_cost_per_1m_usd": BASELINE_OUTPUT_COST_PER_1M_USD,
    }


class SpendLedger:
    def __init__(self, run_dir: Path, run_id: str, max_cost_usd: float | None = None):
        self.ledger_path = run_dir / "spend_ledger.json"
        self.record = SpendLedgerRecord(
            run_id=run_id,
            global_max_cost_usd=max_cost_usd,
        )
        self._load()

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
            for phase_name, phase_data in data.get("phases", {}).items():
                if not isinstance(phase_data, dict):
                    continue
                self.record.phases[str(phase_name)] = self._phase_from_payload(
                    str(phase_name), phase_data
                )
            models = data.get("models")
            if isinstance(models, dict):
                self.record.models = self._models_from_payload(models)
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
    ) -> Dict[str, Any]:
        resolved = _resolve_pricing(provider, model_id)
        input_tokens = _safe_int(input_tokens)
        output_tokens = _safe_int(output_tokens)
        estimated_cost_usd = (
            (input_tokens / 1_000_000.0) * resolved["input_cost_per_1m_usd"]
            + (output_tokens / 1_000_000.0) * resolved["output_cost_per_1m_usd"]
        )
        return {
            **resolved,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": estimated_cost_usd,
        }

    def accumulate(
        self,
        phase: str,
        input_tokens: int,
        output_tokens: int,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        priced = self.price_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider=provider,
            model_id=model_id,
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

        global_model = self.record.models.get(model_key)
        if global_model is None:
            global_model = ModelSpend(
                provider=str(priced["provider"]),
                model_id=str(priced["model_id"]),
                pricing_key=model_key,
                pricing_source=str(priced["pricing_source"]),
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

        if priced["unknown_model"]:
            self.record.unknown_model_events += 1

        self.record.total_cost_usd += priced["estimated_cost_usd"]
        self._save()
        return priced

    def check_limit(self, additional_cost_usd: float = 0.0) -> bool:
        if self.record.global_max_cost_usd is None:
            return True
        projected = self.record.total_cost_usd + _safe_float(additional_cost_usd)
        return projected <= self.record.global_max_cost_usd
