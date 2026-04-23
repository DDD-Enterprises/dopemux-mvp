"""Token estimation utilities for prescan batch planning.

Provides fast character-based estimation with optional tiktoken fallback.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import tiktoken

    _TIKTOKEN_AVAILABLE = True
except ImportError:
    _TIKTOKEN_AVAILABLE = False


def estimate_tokens(
    text: str,
    method: str = "tiktoken",
    chars_per_token: float = 3.5,
) -> int:
    """Estimate token count for a string.

    Args:
        text: Input string.
        method: ``"tiktoken"`` for cl100k_base, ``"chars"`` for character-based.
        chars_per_token: Divisor when using chars method.

    Returns:
        Estimated token count (always ≥ 0).
    """
    if not text:
        return 0

    if _TIKTOKEN_AVAILABLE:
        try:
            enc = tiktoken.get_encoding("cl100k_base")
            return len(enc.encode(text))
        except Exception as e:
            logger.warning(f"tiktoken encoding failed, falling back to chars: {e}")

    # Fallback to character-based heuristic
    return max(1, int(len(text) / chars_per_token))


def estimate_file_tokens(
    path: Path,
    max_preview_bytes: int = 0,
    chars_per_token: float = 3.5,
) -> int:
    """Estimate token count for a file on disk.

    When *max_preview_bytes* is 0 the full file size is used for estimation
    without reading the file (fast path based on stat).  When > 0 the file
    is read up to that many bytes and the actual text is measured using the
    tokenizer.

    Returns 0 on read error.
    """
    try:
        size = path.stat().st_size
    except OSError:
        return 0

    if max_preview_bytes > 0:
        try:
            raw = path.read_bytes()[:max_preview_bytes]
            text = raw.decode("utf-8", errors="replace")
            return estimate_tokens(text, method="tiktoken", chars_per_token=chars_per_token)
        except OSError:
            return 0

    # Fast path — estimate from byte size without reading (heuristic)
    return max(1, int(size / chars_per_token))


def estimate_payload_overhead(pass_id: str) -> int:
    """Return estimated token overhead for a pass's system prompt + framing.

    This accounts for the system prompt, markdown headers, and JSON
    formatting that wrap the file content in each batch payload.
    """
    # Import here to avoid circular dependency
    from .grok_passes import PASS_SYSTEM_PROMPTS

    system_prompt = PASS_SYSTEM_PROMPTS.get(pass_id, "")
    # Framing overhead: markdown headers, separators, metadata lines
    framing_chars = 2000  # conservative estimate for markdown scaffolding
    total_chars = len(system_prompt) + framing_chars
    return max(1, int(total_chars / 4.0))
