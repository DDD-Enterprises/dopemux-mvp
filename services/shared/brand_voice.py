"""Shared Dopemux voice helpers for notifications and ADHD runtime services."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Iterable, List, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from dopemux.ui.theme import StatusChip
from dopemux.voice import HEADERS, validate_or_fallback

TONE_BY_CHIP = {
    StatusChip.LIVE: "live",
    StatusChip.BLOCKER: "blocker",
    StatusChip.OVERRIDE: "override",
    StatusChip.LOGGED: "logged",
    StatusChip.AFTERCARE: "aftercare",
    StatusChip.EDGE: "edge",
}


def _chip_text(chip: StatusChip) -> str:
    return f"[{chip.label}]"


def tone_name(chip: StatusChip, tone: str | None = None) -> str:
    """Return a stable tone label for a chip."""
    return tone or TONE_BY_CHIP.get(chip, "live")


def voice_header(value: str = "ui") -> str:
    """Return a voice header for a surface or legacy title string.

    Backward compatibility:
    - If `value` matches a known surface key in HEADERS, treat it as a surface
      and return the configured header.
    - Otherwise, treat `value` as a title and return a voice-safe header string.
    """
    # New behavior: surface-based headers
    if value in HEADERS:
        return HEADERS[value]

    # Backward compatibility: legacy callers passing a title string
    return validate_or_fallback(
        value,
        surface="ui",
        fallback="Dopemux update",
    )
def _fallback_for(chip: StatusChip) -> str:
    if chip is StatusChip.AFTERCARE:
        return "Session logged. Protect the recovery block."
    if chip is StatusChip.BLOCKER:
        return "Blocked. Check the trace and retry with one clean next step."
    if chip is StatusChip.OVERRIDE:
        return "Override recorded. Confirm the next action before proceeding."
    if chip is StatusChip.LOGGED:
        return "Logged. Receipt captured. Keep the next step visible."
    if chip is StatusChip.EDGE:
        return "Edge signal logged. Keep the next small step visible."
    return "Live signal locked. Keep the next step visible."


def brand_text(
    message: str,
    *,
    chip: StatusChip = StatusChip.LIVE,
    surface: str = "ui",
    fallback: str | None = None,
    include_chip: bool = True,
) -> str:
    """Return voice-safe plain text, optionally prefixed with a status chip."""
    safe = validate_or_fallback(message, surface=surface, fallback=fallback or _fallback_for(chip))
    if include_chip:
        return f"{_chip_text(chip)} {safe}"
    return safe


def brand_title(
    title: str,
    *,
    chip: StatusChip = StatusChip.LIVE,
    fallback: str | None = None,
) -> str:
    """Return a voice-safe title with chip notation."""
    return brand_text(
        title,
        chip=chip,
        surface="ui",
        fallback=fallback or f"{chip.label.title()} Dopemux update",
    )


def brand_list(
    items: Iterable[str],
    *,
    chip: StatusChip = StatusChip.EDGE,
    surface: str = "ui",
) -> List[str]:
    """Return a list of voice-safe suggestions while preserving list shape."""
    return [
        brand_text(item, chip=chip, surface=surface)
        for item in items
    ]


def brand_error(
    message: str,
    *,
    chip: StatusChip = StatusChip.BLOCKER,
    surface: str = "ui",
    fallback: str | None = None,
    include_chip: bool = True,
) -> str:
    """Return deterministic branded error copy."""
    return brand_text(
        message,
        chip=chip,
        surface=surface,
        fallback=fallback or _fallback_for(chip),
        include_chip=include_chip,
    )


def brand_log(
    message: str,
    *,
    chip: StatusChip = StatusChip.LIVE,
    surface: str = "ui",
    fallback: str | None = None,
    include_chip: bool = True,
) -> str:
    """Return branded operator log text."""
    return brand_text(
        message,
        chip=chip,
        surface=surface,
        fallback=fallback,
        include_chip=include_chip,
    )


def aftercare_text(message: str | None = None) -> str:
    """Return a deterministic aftercare message with chip notation."""
    return brand_text(
        message or "Session logged. Take the next recovery beat.",
        chip=StatusChip.AFTERCARE,
    )


def break_copy(duration_minutes: int, *, urgent: bool = False) -> tuple[str, str, str]:
    """Return branded title, notification body, and speech copy for break reminders."""
    if urgent:
        title = brand_title("Break needed now", chip=StatusChip.BLOCKER)
        body = brand_text(
            f"You've been in it for {duration_minutes} minutes. Cut the loop and take a 10-minute reset.",
            chip=StatusChip.BLOCKER,
        )
        speech = validate_or_fallback(
            f"Break needed now. You have been working for {duration_minutes} minutes. Take a ten minute reset.",
            surface="ui",
            fallback="Break needed now. Take a ten minute reset.",
        )
        return title, body, speech

    title = brand_title("Break check", chip=StatusChip.AFTERCARE)
    body = brand_text(
        f"You've been locked in for {duration_minutes} minutes. Take a 5-minute reset and protect the next block.",
        chip=StatusChip.AFTERCARE,
    )
    speech = validate_or_fallback(
        f"Break check. You have been working for {duration_minutes} minutes. Take a five minute reset.",
        surface="ui",
        fallback="Break check. Take a five minute reset.",
    )
    return title, body, speech


def hyperfocus_copy(duration_minutes: int) -> tuple[str, str, str]:
    """Return branded title, notification body, and speech copy for hyperfocus protection."""
    title = brand_title("Hyperfocus guard", chip=StatusChip.BLOCKER)
    body = brand_text(
        f"You've been running hot for {duration_minutes} minutes without a break. Step out for 15 minutes and reset.",
        chip=StatusChip.BLOCKER,
    )
    speech = validate_or_fallback(
        f"Hyperfocus guard. You have been working for {duration_minutes} minutes without a break. Step out for fifteen minutes and reset.",
        surface="ui",
        fallback="Hyperfocus guard. Step out for fifteen minutes and reset.",
    )
    return title, body, speech

def brand_payload(
    message: str,
    *,
    chip: StatusChip = StatusChip.LIVE,
    surface: str = "ui",
) -> Mapping[str, Any]:
    """Return additive branded payload metadata for API and event surfaces."""
    return {
        "message": brand_text(
            message,
            chip=chip,
            surface=surface,
        ),
        "status_chip": chip.label,
        "tone": tone_name(chip),
        "voice_header": voice_header(surface),
    }


__all__ = [
    "StatusChip",
    "TONE_BY_CHIP",
    "aftercare_text",
    "brand_error",
    "brand_list",
    "brand_log",
    "brand_payload",
    "brand_text",
    "brand_title",
    "break_copy",
    "hyperfocus_copy",
    "tone_name",
    "voice_header",
]
