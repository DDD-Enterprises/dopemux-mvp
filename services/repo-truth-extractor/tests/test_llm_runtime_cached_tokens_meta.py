"""Tests for cached_tokens / cache_write_tokens normalization in
`_response_summary_metadata()`.

Covers TP-RTE-COSTPROFILE-E4-FINISH-001 S8: verify the cached-tokens shape
normalization handles each provider's native field name correctly —
OpenAI nests under `prompt_tokens_details.cached_tokens`, Anthropic uses
`cache_read_input_tokens` (+ `cache_creation_input_tokens` for writes),
Gemini uses `cached_content_token_count`.
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
from llm_runtime import _response_summary_metadata  # noqa: E402


def test_openai_cached_tokens_from_prompt_tokens_details() -> None:
    """OpenAI surfaces cached tokens under usage.prompt_tokens_details.cached_tokens."""
    summary = {
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 500,
            "total_tokens": 1500,
            "prompt_tokens_details": {"cached_tokens": 720},
        }
    }
    meta = _response_summary_metadata(summary)
    assert meta["cached_tokens"] == 720
    assert "cache_write_tokens" not in meta  # OpenAI doesn't expose writes
    assert meta["input_tokens"] == 1000


def test_openai_cached_tokens_top_level_preferred() -> None:
    """If usage has both top-level `cached_tokens` and nested details, top-level wins."""
    summary = {
        "usage": {
            "input_tokens": 1000,
            "cached_tokens": 850,
            "prompt_tokens_details": {"cached_tokens": 720},
        }
    }
    meta = _response_summary_metadata(summary)
    assert meta["cached_tokens"] == 850


def test_anthropic_cache_read_and_cache_creation_normalized() -> None:
    """Anthropic surfaces cache_read_input_tokens + cache_creation_input_tokens."""
    summary = {
        "usage": {
            "input_tokens": 1500,
            "output_tokens": 600,
            "cache_read_input_tokens": 1200,
            "cache_creation_input_tokens": 300,
        }
    }
    meta = _response_summary_metadata(summary)
    assert meta["cached_tokens"] == 1200
    assert meta["cache_write_tokens"] == 300


def test_gemini_cached_content_token_count() -> None:
    """Gemini surfaces cached_content_token_count."""
    summary = {
        "usage": {
            "input_tokens": 2000,
            "output_tokens": 800,
            "cached_content_token_count": 1750,
        }
    }
    meta = _response_summary_metadata(summary)
    assert meta["cached_tokens"] == 1750
    assert "cache_write_tokens" not in meta  # Gemini doesn't expose writes


def test_missing_usage_block_no_cache_keys() -> None:
    """No usage section → no cached_tokens / cache_write_tokens keys at all."""
    summary = {"finish_reason": "stop"}
    meta = _response_summary_metadata(summary)
    assert "cached_tokens" not in meta
    assert "cache_write_tokens" not in meta


def test_partial_usage_fields_handled() -> None:
    """Usage with only some fields shouldn't crash; missing fields stay absent."""
    summary = {"usage": {"input_tokens": 100, "prompt_tokens_details": {}}}
    meta = _response_summary_metadata(summary)
    assert meta["input_tokens"] == 100
    assert "cached_tokens" not in meta
    assert "cache_write_tokens" not in meta


def test_anthropic_only_cache_write_no_read() -> None:
    """First-time cache fill: cache_creation_input_tokens > 0, cache_read = 0."""
    summary = {
        "usage": {
            "input_tokens": 1000,
            "cache_creation_input_tokens": 800,
            "cache_read_input_tokens": 0,
        }
    }
    meta = _response_summary_metadata(summary)
    assert meta["cached_tokens"] == 0  # captured as 0, not absent
    assert meta["cache_write_tokens"] == 800


def test_non_dict_summary_returns_empty() -> None:
    """Defensive: non-dict input yields empty dict."""
    assert _response_summary_metadata(None) == {}
    assert _response_summary_metadata("string") == {}
    assert _response_summary_metadata(42) == {}
