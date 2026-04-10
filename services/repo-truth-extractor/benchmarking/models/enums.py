from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    @classmethod
    def coerce(cls, value: str | "StrEnum") -> "StrEnum":
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError as exc:
            allowed = ", ".join(item.value for item in cls)
            raise ValueError(f"invalid {cls.__name__} value {value!r}; allowed: {allowed}") from exc


class SurfaceClass(StrEnum):
    DIRECT_PROVIDER_API = "direct_provider_api"
    OPENROUTER_ROUTED = "openrouter_routed"
    CHAT_OR_SUBSCRIPTION_SURFACE = "chat_or_subscription_surface"
    LOCAL_OR_OPEN_WEIGHT = "local_or_open_weight"


class EvidenceClass(StrEnum):
    METADATA_ONLY = "METADATA_ONLY"
    MIXED_EVIDENCE = "MIXED_EVIDENCE"
    BENCHMARK_DERIVED = "BENCHMARK_DERIVED"
    GOVERNANCE_DERIVED = "GOVERNANCE_DERIVED"


class ContractGateStrength(StrEnum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class BundleType(StrEnum):
    BENCHMARK_RUN = "benchmark_run"
    BENCHMARK_CASE_ATTEMPT = "benchmark_case_attempt"


class RecommendationState(StrEnum):
    NOT_EVALUATED = "not_evaluated"
    QUARANTINED = "quarantined"
    INELIGIBLE = "ineligible"
    EXPERIMENTAL_ONLY = "experimental_only"
    STALE_DISPUTED = "stale_disputed"
    ELIGIBLE_FOR_REVIEW = "eligible_for_review"
    RECOMMENDED_FOR_REVIEW = "recommended_for_review"


class DecisionType(StrEnum):
    APPROVE = "approve"
    DENY = "deny"
    DEFER = "defer"
    QUARANTINE = "quarantine"
    CLEAR_DISPUTE = "clear_dispute"
    DEMOTE = "demote"
    RETIRE = "retire"


class DecisionOutcome(StrEnum):
    RECORDED = "recorded"
    SUPERSEDED = "superseded"
