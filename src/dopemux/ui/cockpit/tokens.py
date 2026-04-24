"""Closed cockpit token validation."""

from __future__ import annotations

ALLOWED_STATUS_CHIPS = frozenset(
    {"LIVE", "BLOCKER", "OVERRIDE", "LOGGED", "AFTERCARE", "EDGE"}
)
PROVENANCE_LABELS = frozenset(
    {"RUNTIME_TRUTH", "EXTRACTED", "MIRRORED", "ADAPTER", "UNKNOWN"}
)
STATUS_NORMALIZATION = {
    "DEGRADED": "OVERRIDE",
    "FAILED": "BLOCKER",
    "BLOCKED": "BLOCKER",
    "SYNC": "AFTERCARE",
    "UNKNOWN": "EDGE",
}
FORBIDDEN_STATUS_CHIPS = frozenset(
    {"UNKNOWN", "DEGRADED", "FAILED", "BLOCKED", "SYNC", "DRAFT", "READY", "SUCCESS", "ERROR"}
)
FORBIDDEN_COPY = (
    "probably",
    "maybe",
    "I think",
    "as an AI",
    "magic",
    "brain",
    "autonomous",
    "smart",
    "seamless",
    "next-gen",
    "all set",
    "everything looks good",
    "supercharged",
)
FORBIDDEN_ARROWS = ("→", "⇒", "➜")


def normalize_status_chip(value: str) -> str:
    """Return a closed status chip, mapping known web/RTE values."""

    normalized = value.strip().upper()
    normalized = STATUS_NORMALIZATION.get(normalized, normalized)
    if normalized not in ALLOWED_STATUS_CHIPS:
        raise ValueError(f"status chip not allowed: {value}")
    return normalized


def validate_status_chip(value: str) -> str:
    """Validate a chip without applying compatibility aliases."""

    normalized = value.strip().upper()
    if normalized not in ALLOWED_STATUS_CHIPS:
        raise ValueError(f"status chip not allowed: {value}")
    return normalized


def validate_rendered_text(text: str) -> None:
    """Reject vocabulary that would weaken the static renderer contract."""

    for arrow in FORBIDDEN_ARROWS:
        if arrow in text:
            raise ValueError(f"forbidden arrow: {arrow}")
    if "..." in text or "…" in text:
        raise ValueError("ellipsis clipping is forbidden")
    lowered = text.lower()
    for phrase in FORBIDDEN_COPY:
        if phrase.lower() in lowered:
            raise ValueError(f"forbidden cockpit copy: {phrase}")
    for chip in FORBIDDEN_STATUS_CHIPS:
        if f"[{chip}]" in text:
            raise ValueError(f"forbidden status chip rendered: {chip}")
