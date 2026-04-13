from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lib.spend_ledger import get_model_cost_rate


HARD_SPEND_CAP_USD = 3.0
SOFT_ATTEMPT_ALERT_USD = 0.40


def estimate_tokens(*chunks: Any) -> int:
    total_chars = sum(len(str(chunk or "")) for chunk in chunks)
    return max(1, total_chars // 4)


def projected_output_tokens(input_tokens: int, *, max_tokens: int) -> int:
    projected = max(64, input_tokens // 5)
    return min(max_tokens, projected)


@dataclass(frozen=True)
class SpendEstimate:
    provider: str
    model_id: str
    pricing_key: str
    pricing_source: str
    pricing_source_type: str
    pricing_status: str
    pricing_confidence: str
    pricing_currency: str
    surface_scope: str
    pricing_version: str
    pricing_match_type: str
    unknown_model: bool
    spend_truth_class: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    input_cost_per_1m_usd: float
    output_cost_per_1m_usd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model_id": self.model_id,
            "pricing_key": self.pricing_key,
            "pricing_source": self.pricing_source,
            "pricing_source_type": self.pricing_source_type,
            "pricing_status": self.pricing_status,
            "pricing_confidence": self.pricing_confidence,
            "pricing_currency": self.pricing_currency,
            "surface_scope": self.surface_scope,
            "pricing_version": self.pricing_version,
            "pricing_match_type": self.pricing_match_type,
            "unknown_model": self.unknown_model,
            "spend_truth_class": self.spend_truth_class,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "input_cost_per_1m_usd": self.input_cost_per_1m_usd,
            "output_cost_per_1m_usd": self.output_cost_per_1m_usd,
        }


@dataclass
class SpendGuard:
    hard_cap_usd: float = HARD_SPEND_CAP_USD
    per_attempt_soft_alert_usd: float = SOFT_ATTEMPT_ALERT_USD
    total_expected_spend_usd: float = 0.0
    total_measured_spend_usd: float = 0.0
    total_unknown_events: int = 0

    def estimate(
        self,
        *,
        provider: str,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> SpendEstimate:
        rate = get_model_cost_rate(provider=provider, model_id=model_id)
        estimated_cost_usd = (
            (float(rate["input_cost_per_1m_usd"]) * input_tokens)
            + (float(rate["output_cost_per_1m_usd"]) * output_tokens)
        ) / 1_000_000.0
        unknown_model = bool(rate.get("unknown_model", False))
        if unknown_model:
            self.total_unknown_events += 1
        return SpendEstimate(
            provider=str(rate.get("provider") or provider),
            model_id=str(rate.get("model_id") or model_id),
            pricing_key=str(rate.get("pricing_key") or f"{provider}/{model_id}"),
            pricing_source=str(rate.get("pricing_source") or "unknown"),
            pricing_source_type=str(rate.get("pricing_source_type") or "unknown"),
            pricing_status=str(rate.get("pricing_status") or "UNPRICED_UNKNOWN"),
            pricing_confidence=str(rate.get("pricing_confidence") or "UNKNOWN"),
            pricing_currency=str(rate.get("pricing_currency") or "USD"),
            surface_scope=str(rate.get("surface_scope") or "unknown"),
            pricing_version=str(rate.get("pricing_version") or "unknown"),
            pricing_match_type=str(rate.get("match_type") or "unknown"),
            unknown_model=unknown_model,
            spend_truth_class=(
                "partial_estimate"
                if unknown_model or str(rate.get("pricing_status") or "") != "PRICED_CONFIRMED"
                else "catalog_expected"
            ),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
            input_cost_per_1m_usd=float(rate["input_cost_per_1m_usd"]),
            output_cost_per_1m_usd=float(rate["output_cost_per_1m_usd"]),
        )

    def assert_can_afford(self, estimate: SpendEstimate) -> None:
        projected_total = self.total_expected_spend_usd + estimate.estimated_cost_usd
        if projected_total > self.hard_cap_usd:
            raise RuntimeError(
                "direct_model spend guard would exceed hard cap "
                f"(projected_total_usd={projected_total:.6f} hard_cap_usd={self.hard_cap_usd:.2f} "
                f"provider={estimate.provider} model={estimate.model_id})"
            )

    def record_expected(self, estimate: SpendEstimate) -> dict[str, Any]:
        self.total_expected_spend_usd += estimate.estimated_cost_usd
        return {
            **estimate.to_dict(),
            "hard_cap_usd": self.hard_cap_usd,
            "per_attempt_soft_alert_usd": self.per_attempt_soft_alert_usd,
            "soft_alert_triggered": estimate.estimated_cost_usd > self.per_attempt_soft_alert_usd,
            "projected_total_expected_spend_usd": self.total_expected_spend_usd,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "hard_cap_usd": self.hard_cap_usd,
            "per_attempt_soft_alert_usd": self.per_attempt_soft_alert_usd,
            "total_expected_spend_usd": self.total_expected_spend_usd,
            "total_measured_spend_usd": self.total_measured_spend_usd,
            "unknown_pricing_events": self.total_unknown_events,
        }
