"""Voice helpers for agent, prompt, and deterministic validation surfaces."""

from .agent_headers import HEADERS, FALLBACKS, inject_voice_header, validate_or_fallback
from .core import (
    GateResult,
    GateViolation,
    Surface,
    VoiceMode,
    build_rewrite_instruction,
    load_voice_gates,
    select_mode,
    validate_output,
)

__all__ = [
    "GateResult",
    "GateViolation",
    "HEADERS",
    "FALLBACKS",
    "Surface",
    "VoiceMode",
    "build_rewrite_instruction",
    "inject_voice_header",
    "load_voice_gates",
    "select_mode",
    "validate_output",
    "validate_or_fallback",
]
