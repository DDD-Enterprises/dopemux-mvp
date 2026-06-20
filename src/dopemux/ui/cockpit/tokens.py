"""Cockpit rendered-text validation helpers."""

from __future__ import annotations

from typing import Any

from dopemux.voice import (
    GateResult,
    GateViolation,
    Surface,
    VoiceMode,
    load_voice_gates,
    select_mode,
    validate_output,
)


def _is_full_cockpit_render(text: str) -> bool:
    """Detect full TUI/markdown cockpit output (not label:/message:/action: payload)."""
    stripped = text.lstrip()
    return stripped.startswith("#") or "# Dopemux Cockpit" in text


def _has_required_closer(text: str, required: list[str]) -> bool:
    stripped = text.strip()
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    markdown_lines = [line.lstrip("#").strip() for line in lines]
    for token in required:
        if stripped.endswith(token):
            return True
        if any(line.startswith(token) for line in lines):
            return True
        base = token.rstrip(":")
        if any(line == base for line in markdown_lines):
            return True
        if any(line.startswith(f"{base}:") for line in markdown_lines):
            return True
    return False


def validate_rendered_text(
    text: str,
    *,
    surface: Surface = Surface.UI,
    mode: VoiceMode | None = None,
    gates: dict[str, Any] | None = None,
) -> GateResult:
    """Validate rendered cockpit text, including UI closer enforcement."""
    config = gates or load_voice_gates()
    selected_mode = mode or select_mode(surface, text)
    validation_surface = surface
    if surface is Surface.UI and _is_full_cockpit_render(text):
        validation_surface = Surface.CLI
    result = validate_output(validation_surface, selected_mode, text, config)
    violations = list(result.violations)

    closers = config.get("lexical_gates", {}).get("required_closers", [])
    if closers and not _has_required_closer(text, closers):
        if not any(item.code == "MISSING_CLOSER" for item in violations):
            violations.append(
                GateViolation(
                    "MISSING_CLOSER",
                    "Rendered cockpit text must include NEXT:/Receipt:/PROGRESS.",
                )
            )

    return GateResult(ok=not violations, violations=violations)


__all__ = ["validate_rendered_text"]
