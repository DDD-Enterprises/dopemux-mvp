"""Voice header injection and fail-closed validation for agent surfaces."""

from __future__ import annotations

from pathlib import Path

from .core import Surface, load_voice_gates, select_mode, validate_output

HEADER_DIR = Path(__file__).resolve().parents[3] / "dopemux_voice_branding_bundle" / "headers"


def _artifact_header(name: str, fallback: str) -> str:
    path = HEADER_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return fallback


HEADERS = {
    "cli": _artifact_header(
        "header_cli.md",
        "[LIVE] You are the DØPEMUX Ritual Daemon. Terse. Forensic. No fluff.",
    ),
    "ui": _artifact_header(
        "header_ui.md",
        "[LIVE] DØPEMUX UI mode. Crisp. Direct. No threats. {label, message, action}.",
    ),
    "agent": _artifact_header(
        "header_agent.md",
        "[LIVE] DØPEMUX agent mode. FACT and INFERENCE clearly split. UNKNOWN+TODO over guessing.",
    ),
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


def _normalize_surface(surface: str) -> Surface:
    if surface == "cli":
        return Surface.CLI
    if surface == "ui":
        return Surface.UI
    return Surface.AGENT


def _strip_header(text: str, header: str) -> str:
    if text.startswith(header):
        return text[len(header):].strip()
    return text


def _normalized_validation_text(surface: str, body: str) -> str:
    stripped = body.strip()
    if surface == "ui":
        return f"label: dopemux\nmessage: {stripped}\naction: review"
    if surface in {"cli", "agent", "guardian", "role"}:
        if any(token in stripped for token in ("NEXT:", "Next:", "Receipt:", "PROGRESS")):
            return stripped
        return f"{stripped}\nNEXT: keep the next step visible."
    return stripped


def inject_voice_header(prompt: str, surface: str = "agent") -> str:
    """Prepend the configured voice header to a prompt or generated brief."""
    header = HEADERS.get(surface, HEADERS["agent"])
    mode = select_mode(_normalize_surface(surface), prompt)
    header = header.replace("{{MODE}}", mode.value)
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
    if candidate:
        header = HEADERS.get(surface, HEADERS["agent"])
        normalized_surface = _normalize_surface(surface)
        mode = select_mode(normalized_surface, candidate)
        header_with_mode = header.replace("{{MODE}}", mode.value)
        body = _strip_header(candidate, header_with_mode)
        result = validate_output(
            normalized_surface,
            mode,
            _normalized_validation_text(surface, body or candidate),
            load_voice_gates(),
        )
        if result.ok:
            return candidate
    return fallback or FALLBACKS.get(surface, FALLBACKS["agent"])
