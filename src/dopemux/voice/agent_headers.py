"""Voice header injection and fail-closed validation for agent surfaces."""

from __future__ import annotations

from ..ui.voice import validate_output

HEADERS = {
    "cli": "[LIVE] You are the DØPEMUX Ritual Daemon. Terse. Forensic. No fluff.",
    "ui": "[LIVE] DØPEMUX UI mode. Crisp. Direct. No threats. {label, message, action}.",
    "agent": "[LIVE] DØPEMUX agent mode. FACT and INFERENCE clearly split. UNKNOWN+TODO over guessing.",
    "guardian": "[LIVE] DØPEMUX guardian mode. Protect focus. Prefer calm guidance and one clean next step.",
    "role": "[LIVE] DØPEMUX role mode. State the mission, attention profile, and required tool surface.",
}

FALLBACKS = {
    "cli": "[LIVE] Output blocked by the Dopemux voice gate. NEXT: restate the action in one direct line.",
    "ui": "[LIVE] Output blocked. label: voice gate. message: restate with one clear next step. action: tighten the copy.",
    "agent": (
        "[LIVE] Output blocked by the Dopemux voice gate. "
        "FACT: draft withheld. INFERENCE: phrasing drifted off-brand. "
        "UNKNOWN: clean replacement text. TODO: restate with evidence and one next step."
    ),
    "guardian": (
        "[LIVE] Guardian copy blocked by the Dopemux voice gate. "
        "FACT: focus support message withheld. UNKNOWN: safe replacement details. "
        "TODO: restate with calm guidance and one next step."
    ),
    "role": (
        "[LIVE] Role brief blocked by the Dopemux voice gate. "
        "FACT: role metadata is available. UNKNOWN: safe role framing. "
        "TODO: restate the mission, attention profile, and server surface."
    ),
}


def inject_voice_header(prompt: str, surface: str = "agent") -> str:
    """Prepend the configured voice header to a prompt or generated brief."""
    header = HEADERS.get(surface, HEADERS["agent"])
    body = prompt.strip()
    if not body:
        return header
    if body.startswith(header):
        return body
    return f"{header}\n\n{body}"


def validate_or_fallback(
    text: str,
    surface: str = "agent",
    fallback: str | None = None,
) -> str:
    """Return validated text, or a deterministic branded fallback if it fails."""
    candidate = text.strip()
    if candidate and not validate_output(candidate):
        return candidate
    return fallback or FALLBACKS.get(surface, FALLBACKS["agent"])
