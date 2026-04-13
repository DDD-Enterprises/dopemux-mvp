from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..policies.loader import load_policy_pack


_POLICY = load_policy_pack("freshness_policy_v1.json")


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


@dataclass(frozen=True)
class FreshnessPolicy:
    policy_id: str = str(_POLICY["policy_id"])
    policy_version: str = str(_POLICY["policy_version"])
    max_age_hours: float = float(_POLICY["max_age_hours"])


@dataclass(frozen=True)
class FreshnessOutcome:
    freshness_state: str
    dispute_state: str
    age_hours: float
    blockers: list[str]


def evaluate_freshness(
    benchmark_run: dict[str, Any],
    attempt: dict[str, Any],
    policy: FreshnessPolicy | None = None,
) -> FreshnessOutcome:
    active_policy = policy or FreshnessPolicy()
    evidence_timestamp = str(attempt.get("timestamp_utc") or benchmark_run.get("finished_at"))
    timestamp = _parse_utc(evidence_timestamp)
    age_hours = max(0.0, (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600.0)
    blockers: list[str] = []
    freshness_state = "fresh"
    if age_hours > active_policy.max_age_hours:
        freshness_state = "stale"
        blockers.append(str(_POLICY["stale_blocker"]))

    dispute_state = "clear"
    if attempt.get("unknowns_open"):
        dispute_state = "disputed"
        blockers.append(str(_POLICY["unknowns_blocker"]))
    if attempt.get("structural_failure_classification"):
        dispute_state = "disputed" if dispute_state == "clear" else dispute_state
    return FreshnessOutcome(
        freshness_state=freshness_state,
        dispute_state=dispute_state,
        age_hours=round(age_hours, 6),
        blockers=blockers,
    )
