"""Tests for prompt_caching_directives_for_provider().

Covers TP-RTE-COSTPROFILE-E3-CONTRACTS-001 S4/S7: provider-appropriate prompt
cache directives — Anthropic `cache_control_markers` (capped at the Anthropic
API limit of 4), OpenAI/OpenRouter `prompt_cache_key` (stable hash of the
prefix structure), Gemini `cached_content_name` (only under explicit opt-in).
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_service_root_on_path() -> None:
    root = Path(__file__).resolve().parents[3]
    service_root = root / "services" / "repo-truth-extractor"
    if str(service_root) not in sys.path:
        sys.path.insert(0, str(service_root))


_ensure_service_root_on_path()
from lib.structured_output_contracts import (  # noqa: E402
    prompt_caching_directives_for_provider,
)


# --------------------------------------------------------------------- guards


def test_strategy_none_returns_applied_false() -> None:
    result = prompt_caching_directives_for_provider(
        "anthropic", "claude-opus-4.6", cache_strategy="none"
    )
    assert result["applied"] is False
    assert result["strategy"] == "none"
    assert result["cache_control_markers"] == []
    assert result["prompt_cache_key"] is None
    assert result["cached_content_name"] is None


def test_strategy_auto_without_enable_returns_applied_false() -> None:
    result = prompt_caching_directives_for_provider(
        "anthropic",
        "claude-opus-4.6",
        cache_strategy="auto",
        auto_cache_enabled=None,
    )
    assert result["applied"] is False
    assert result["strategy"] == "none"

    result = prompt_caching_directives_for_provider(
        "anthropic",
        "claude-opus-4.6",
        cache_strategy="auto",
        auto_cache_enabled=False,
    )
    assert result["applied"] is False


def test_invalid_strategy_falls_back_to_none() -> None:
    result = prompt_caching_directives_for_provider(
        "anthropic",
        "claude-opus-4.6",
        cache_strategy="bogus",
        auto_cache_enabled=True,
    )
    assert result["applied"] is False
    assert result["strategy"] == "none"


# ------------------------------------------------------------------ Anthropic


def test_anthropic_direct_emits_cache_control_markers_when_enabled() -> None:
    result = prompt_caching_directives_for_provider(
        "anthropic",
        "claude-opus-4.6",
        prompt_text_lengths=[1000, 2000, 500],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    assert result["applied"] is True
    assert result["strategy"] == "auto"
    assert result["prompt_cache_key"] is None
    assert result["cached_content_name"] is None
    assert len(result["cache_control_markers"]) >= 1
    for marker in result["cache_control_markers"]:
        assert marker["type"] == "ephemeral"
        assert isinstance(marker["block_index"], int)


def test_anthropic_via_openrouter_emits_markers() -> None:
    result = prompt_caching_directives_for_provider(
        "openrouter",
        "anthropic/claude-sonnet-4.6",
        prompt_text_lengths=[500, 500, 500],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    assert result["applied"] is True
    assert len(result["cache_control_markers"]) >= 1


def test_anthropic_marker_count_capped_at_four() -> None:
    """Anthropic API limit: at most 4 cache_control markers per request."""
    result = prompt_caching_directives_for_provider(
        "anthropic",
        "claude-opus-4.6",
        prompt_text_lengths=list(range(20)),  # 20 blocks → still capped at 4
        cache_strategy="cache_control_explicit",
        auto_cache_enabled=True,
    )
    assert len(result["cache_control_markers"]) <= 4
    assert len(result["cache_control_markers"]) == 4


def test_anthropic_marker_default_when_no_lengths() -> None:
    """Without prompt_text_lengths, emit at least one marker so the caller still
    benefits from caching the system prefix."""
    result = prompt_caching_directives_for_provider(
        "anthropic",
        "claude-opus-4.6",
        cache_strategy="cache_control_explicit",
    )
    assert result["applied"] is True
    assert len(result["cache_control_markers"]) == 1


# -------------------------------------------------------------------- OpenAI


def test_openai_direct_emits_prompt_cache_key() -> None:
    result = prompt_caching_directives_for_provider(
        "openai",
        "gpt-5",
        prompt_text_lengths=[1000, 200],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    assert result["applied"] is True
    assert isinstance(result["prompt_cache_key"], str)
    assert len(result["prompt_cache_key"]) == 32
    assert result["cache_control_markers"] == []
    assert result["cached_content_name"] is None


def test_openai_prompt_cache_key_is_deterministic() -> None:
    a = prompt_caching_directives_for_provider(
        "openai",
        "gpt-5",
        prompt_text_lengths=[1000, 200],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    b = prompt_caching_directives_for_provider(
        "openai",
        "gpt-5",
        prompt_text_lengths=[1000, 200],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    assert a["prompt_cache_key"] == b["prompt_cache_key"]


def test_openai_prompt_cache_key_changes_with_lengths() -> None:
    a = prompt_caching_directives_for_provider(
        "openai",
        "gpt-5",
        prompt_text_lengths=[1000, 200],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    b = prompt_caching_directives_for_provider(
        "openai",
        "gpt-5",
        prompt_text_lengths=[1500, 200],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    assert a["prompt_cache_key"] != b["prompt_cache_key"]


def test_openrouter_passthrough_routes_to_openai_cache_path() -> None:
    """OpenRouter routes that aren't anthropic/gemini/xai use OpenAI prompt_cache_key."""
    result = prompt_caching_directives_for_provider(
        "openrouter",
        "openai/gpt-5",
        prompt_text_lengths=[500],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    assert result["applied"] is True
    assert isinstance(result["prompt_cache_key"], str)
    assert result["cache_control_markers"] == []


# --------------------------------------------------------------------- Gemini


def test_gemini_implicit_cache_under_auto_returns_none() -> None:
    """Gemini implicit cache is automatic; under 'auto' no directive emitted."""
    result = prompt_caching_directives_for_provider(
        "gemini",
        "gemini-3.5-pro",
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    assert result["applied"] is False
    assert result["strategy"] == "none"


def test_gemini_explicit_emits_cached_content_name() -> None:
    result = prompt_caching_directives_for_provider(
        "gemini",
        "gemini-3.5-pro",
        cache_strategy="cache_control_explicit",
    )
    assert result["applied"] is True
    assert result["cached_content_name"] == "cached/gemini-3.5-pro/explicit"
    assert result["cache_control_markers"] == []
    assert result["prompt_cache_key"] is None


# ------------------------------------------------------------------- fallback


def test_unknown_provider_returns_none() -> None:
    result = prompt_caching_directives_for_provider(
        "mystery",
        "some-model",
        cache_strategy="cache_control_explicit",
        auto_cache_enabled=True,
    )
    assert result["applied"] is False
    assert result["strategy"] == "none"


def test_xai_direct_returns_none_for_now() -> None:
    """xAI has no documented prompt-cache mechanism; fail-closed by default."""
    result = prompt_caching_directives_for_provider(
        "xai",
        "grok-code-fast-1",
        cache_strategy="cache_control_explicit",
        auto_cache_enabled=True,
    )
    assert result["applied"] is False
    assert result["strategy"] == "none"


def test_anthropic_marker_indices_point_at_last_prefix_blocks() -> None:
    """Per packet S4: cache markers should be on the LAST K prefix blocks
    (closest to the mutable tail), not the first K. This maximizes the
    cached prefix size.

    For 6 blocks with K=4 markers: indices should be [1,2,3,4] (leaving the
    final block 5 — the mutable tail — unmarked), not [0,1,2,3].
    """
    result = prompt_caching_directives_for_provider(
        "anthropic",
        "claude-opus-4.6",
        prompt_text_lengths=[100, 200, 300, 400, 500, 600],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    assert result["applied"] is True
    indices = [marker["block_index"] for marker in result["cache_control_markers"]]
    assert indices == [1, 2, 3, 4]


def test_anthropic_marker_indices_3_block_prefix() -> None:
    """3 total blocks, K=2 markers → indices [0, 1] (block 2 is mutable tail)."""
    result = prompt_caching_directives_for_provider(
        "anthropic",
        "claude-opus-4.6",
        prompt_text_lengths=[100, 200, 300],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    indices = [marker["block_index"] for marker in result["cache_control_markers"]]
    assert indices == [0, 1]


def test_prompt_text_lengths_filter_non_positive() -> None:
    """Zero / negative lengths are filtered out before marker computation —
    guards against upstream bugs that would produce nonsensical cache keys
    or marker counts."""
    # 6 raw values but only 4 are positive ints → behaves like lengths=[1,2,3,4].
    result = prompt_caching_directives_for_provider(
        "anthropic",
        "claude-opus-4.6",
        prompt_text_lengths=[0, 1, -5, 2, 3, 4],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    # With 4 positive lengths, count = min(4, max(1, 3)) = 3, start = max(0, 4-1-3) = 0.
    indices = [marker["block_index"] for marker in result["cache_control_markers"]]
    assert indices == [0, 1, 2]


def test_openai_prompt_cache_key_ignores_non_positive_lengths() -> None:
    """Negative/zero lengths must NOT change the OpenAI cache key — they're
    filtered before the hash so callers can't inadvertently fragment caching."""
    a = prompt_caching_directives_for_provider(
        "openai",
        "gpt-5",
        prompt_text_lengths=[100, 200],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    b = prompt_caching_directives_for_provider(
        "openai",
        "gpt-5",
        prompt_text_lengths=[100, 0, -1, 200, "x"],
        cache_strategy="auto",
        auto_cache_enabled=True,
    )
    assert a["prompt_cache_key"] == b["prompt_cache_key"]
