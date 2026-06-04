"""Deterministic confidence-band rendering for honest ADHD UX surfaces."""

from __future__ import annotations

from enum import Enum
from typing import Optional, Union


class ConfidenceBandState(str, Enum):
    """Evidence state for a displayed confidence-like value."""

    MEASURED = "measured"
    INFERRED = "inferred"
    LOW_CONFIDENCE = "low-conf"
    CALIBRATING = "calibrating"
    UNAVAILABLE = "unavailable"


_STATE_LABELS = {
    ConfidenceBandState.MEASURED: "MEASURED",
    ConfidenceBandState.INFERRED: "INFERRED",
    ConfidenceBandState.LOW_CONFIDENCE: "LOW-CONF",
    ConfidenceBandState.CALIBRATING: "CALIBRATING",
    ConfidenceBandState.UNAVAILABLE: "UNAVAILABLE",
}


def _normalize_state(
    state: Union[ConfidenceBandState, str],
) -> ConfidenceBandState:
    if isinstance(state, ConfidenceBandState):
        return state
    normalized = str(state).strip().lower().replace("_", "-")
    if normalized == "low-confidence":
        normalized = ConfidenceBandState.LOW_CONFIDENCE.value
    try:
        return ConfidenceBandState(normalized)
    except ValueError:
        return ConfidenceBandState.UNAVAILABLE


def _format_percent(value: float) -> str:
    bounded = max(0.0, min(1.0, float(value)))
    return f"{bounded:.0%}"


def render_confidence_band(
    *,
    value: Optional[float],
    state: Union[ConfidenceBandState, str],
    confidence: Optional[float] = None,
    label: Optional[str] = None,
) -> str:
    """Render a value with an explicit evidence band.

    The rendered string is intentionally never just a number or percent. Unknown
    states fail closed to UNAVAILABLE instead of implying measurement.
    """
    normalized_state = _normalize_state(state)
    if confidence is not None and confidence < 0.5:
        normalized_state = ConfidenceBandState.LOW_CONFIDENCE

    state_label = _STATE_LABELS[normalized_state]
    prefix = f"{label}: " if label else ""

    if normalized_state == ConfidenceBandState.UNAVAILABLE or value is None:
        return f"{prefix}{state_label} no signal"
    if normalized_state == ConfidenceBandState.CALIBRATING:
        return f"{prefix}{state_label} {_format_percent(value)}"
    if normalized_state == ConfidenceBandState.LOW_CONFIDENCE:
        return f"{prefix}{state_label} {_format_percent(value)} verify"

    return f"{prefix}{state_label} {_format_percent(value)}"
