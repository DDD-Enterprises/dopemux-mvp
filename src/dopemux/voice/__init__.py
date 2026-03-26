"""Voice helpers for agent, prompt, and deterministic validation surfaces."""

from .agent_headers import HEADERS, FALLBACKS, inject_voice_header, validate_or_fallback
from .core import (
    DEFAULT_GATES,
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
    "DEFAULT_GATES",
    "FALLBACKS",
    "GateResult",
    "GateViolation",
    "HEADERS",
    "Surface",
    "VoiceMode",
    "build_rewrite_instruction",
    "inject_voice_header",
    "load_voice_gates",
    "select_mode",
    "validate_or_fallback",
    "validate_output",
]
