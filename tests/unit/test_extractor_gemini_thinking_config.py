"""Unit tests for Gemini thinking config — TP-EXTR-GEMINI-THINKING-CONFIG-0002.

Network-free: all assertions operate on the output of _build_gemini_config_for_model(),
which is a deterministic dict builder.  GEMINI_API_KEY is not touched.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest

RUNNER_PATH = (
    Path(__file__).resolve().parents[2]
    / "services"
    / "repo-truth-extractor"
    / "run_extraction_v3.py"
)
SPEC = importlib.util.spec_from_file_location("run_extraction_v3", RUNNER_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)

BULK_MODEL = runner.DEFAULT_GEMINI_BULK_MODEL      # gemini-2.5-flash-lite
EXTRACT_MODEL = runner.DEFAULT_GEMINI_EXTRACT_MODEL  # gemini-2.5-flash
SYNTH_MODEL = runner.DEFAULT_GEMINI_SYNTH_MODEL    # gemini-2.5-pro


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _build(model_id: str, *, force_json: bool = False) -> dict:
    """Thin wrapper — call _build_gemini_config_for_model with a dummy prompt."""
    return runner._build_gemini_config_for_model(
        model_id=model_id,
        system_prompt="test prompt",
        force_json_output=force_json,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tests: bulk model
# ──────────────────────────────────────────────────────────────────────────────

def test_bulk_model_has_thinking_config():
    cfg = _build(BULK_MODEL)
    assert "thinking_config" in cfg, "bulk model must have thinking_config"


def test_bulk_model_thinking_budget_is_zero():
    cfg = _build(BULK_MODEL)
    tc = cfg["thinking_config"]
    # SDK returns a ThinkingConfig object with a thinking_budget attribute
    assert hasattr(tc, "thinking_budget"), (
        f"thinking_config must be a ThinkingConfig object, got {type(tc)}"
    )
    assert tc.thinking_budget == 0


def test_bulk_model_no_thinking_budget_tokens_key():
    """Regression: ensure the old wrong dict key is never used."""
    cfg = _build(BULK_MODEL)
    tc = cfg["thinking_config"]
    # Must NOT be a plain dict with the wrong key
    assert not isinstance(tc, dict), (
        "thinking_config must NOT be a plain dict — use ThinkingConfig SDK type"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tests: extract model
# ──────────────────────────────────────────────────────────────────────────────

def test_extract_model_thinking_disabled():
    cfg = _build(EXTRACT_MODEL)
    assert "thinking_config" in cfg
    tc = cfg["thinking_config"]
    assert hasattr(tc, "thinking_budget")
    assert tc.thinking_budget == 0


# ──────────────────────────────────────────────────────────────────────────────
# Tests: synthesis / Pro model — thinking NOT forced off
# ──────────────────────────────────────────────────────────────────────────────

def test_synth_model_does_not_force_thinking_off():
    cfg = _build(SYNTH_MODEL)
    # Pro/synth model must NOT have a thinking_config that disables thinking
    if "thinking_config" in cfg:
        tc = cfg["thinking_config"]
        if hasattr(tc, "thinking_budget"):
            assert tc.thinking_budget != 0, (
                "synthesis model must not hard-disable thinking"
            )


# ──────────────────────────────────────────────────────────────────────────────
# Tests: base config fields always present
# ──────────────────────────────────────────────────────────────────────────────

def test_base_config_fields_present():
    for model_id in (BULK_MODEL, EXTRACT_MODEL, SYNTH_MODEL):
        cfg = _build(model_id)
        assert cfg["temperature"] == 0.1
        assert "system_instruction" in cfg
        assert cfg["max_output_tokens"] == 8192


def test_force_json_output_sets_mime_type():
    cfg = _build(BULK_MODEL, force_json=True)
    assert cfg.get("response_mime_type") == "application/json"


def test_no_json_mime_type_when_not_forced():
    cfg = _build(BULK_MODEL, force_json=False)
    assert "response_mime_type" not in cfg


# ──────────────────────────────────────────────────────────────────────────────
# Tests: fail-closed when SDK unavailable
# ──────────────────────────────────────────────────────────────────────────────

def test_fails_closed_when_sdk_unavailable():
    """Regression: if ThinkingConfig cannot be constructed, the helper must raise — never fall back to an invented dict key."""
    import sys
    from unittest.mock import patch

    # google.genai is already imported, so we need to patch at the attribute level.
    # We replace google.genai.types with a MagicMock whose ThinkingConfig raises ImportError
    # to simulate environment where the SDK type is unavailable.
    import google.genai.types as _real_types

    class _FakeTypes:
        @staticmethod
        def ThinkingConfig(**_kwargs):  # type: ignore[override]
            raise ImportError("mocked: ThinkingConfig not available")

    with patch.object(sys.modules["google.genai"], "types", _FakeTypes):
        with pytest.raises((ValueError, ImportError)):
            runner._build_gemini_config_for_model(
                model_id=BULK_MODEL,
                system_prompt="test",
                force_json_output=False,
            )


