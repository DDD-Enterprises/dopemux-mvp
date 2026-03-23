"""Voice helpers for agent and prompt surfaces."""

from .agent_headers import HEADERS, FALLBACKS, inject_voice_header, validate_or_fallback

__all__ = [
    "HEADERS",
    "FALLBACKS",
    "inject_voice_header",
    "validate_or_fallback",
]
