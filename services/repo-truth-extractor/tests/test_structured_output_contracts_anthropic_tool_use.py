"""Tests for the new `anthropic_tool_use` schema variant.

Covers TP-RTE-COSTPROFILE-E3-CONTRACTS-001 S5/S6/S7:
* `provider_schema_variant()` returns `anthropic_tool_use` for Anthropic
  direct and OpenRouter+anthropic/* models; the legacy three variants
  (`canonical`, `xai_relaxed`, `gemini_relaxed`) stay byte-identical for
  non-Anthropic providers (regression).
* `adapt_canonical_schema_for_variant(..., variant='anthropic_tool_use')`
  returns an Anthropic tool definition dict — `{name, description, input_schema}`
  — while preserving required field declarations and enum constraints.
* `build_provider_structured_output()` for an Anthropic route returns the
  `{tools: [...], tool_choice: {...}}` payload + `transport_mode='anthropic_tool_use'`
  meta so the runtime can route the request as Anthropic tool_use rather than
  OpenAI `response_format`.
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
    STRUCTURED_OUTPUT_MODE_JSON_SCHEMA,
    adapt_canonical_schema_for_variant,
    build_provider_structured_output,
    provider_schema_variant,
    provider_schema_variant_label,
)


# ----------------------------------------------------------- variant resolver


def test_anthropic_direct_returns_anthropic_tool_use_variant() -> None:
    assert provider_schema_variant("anthropic", "claude-opus-4.6") == "anthropic_tool_use"
    assert provider_schema_variant("anthropic", "claude-sonnet-4.6") == "anthropic_tool_use"
    assert provider_schema_variant("anthropic", "claude-haiku-4.5") == "anthropic_tool_use"


def test_openrouter_anthropic_models_return_anthropic_tool_use_variant() -> None:
    assert (
        provider_schema_variant("openrouter", "anthropic/claude-opus-4.6")
        == "anthropic_tool_use"
    )
    assert (
        provider_schema_variant("openrouter", "anthropic/claude-sonnet-4.6")
        == "anthropic_tool_use"
    )
    assert (
        provider_schema_variant("openrouter", "anthropic/claude-haiku-4.5")
        == "anthropic_tool_use"
    )


def test_legacy_three_variants_unchanged_for_non_anthropic() -> None:
    """Regression: the three pre-existing variants must remain byte-identical."""
    assert provider_schema_variant("openai", "gpt-5") == "canonical"
    assert provider_schema_variant("xai", "grok-code-fast-1") == "xai_relaxed"
    assert provider_schema_variant("gemini", "gemini-3.5-pro") == "gemini_relaxed"
    assert provider_schema_variant("openrouter", "openai/gpt-5") == "canonical"
    assert (
        provider_schema_variant("openrouter", "x-ai/grok-code-fast-1") == "xai_relaxed"
    )
    assert (
        provider_schema_variant("openrouter", "google/gemini-3.5-pro")
        == "gemini_relaxed"
    )
    assert (
        provider_schema_variant("openrouter", "gemini-3.5-pro-experimental")
        == "gemini_relaxed"
    )


def test_variant_label_for_anthropic() -> None:
    assert (
        provider_schema_variant_label("anthropic", "claude-opus-4.6")
        == "anthropic_tool_use_direct"
    )
    assert (
        provider_schema_variant_label("openrouter", "anthropic/claude-opus-4.6")
        == "openrouter_proxy_anthropic_tool_use"
    )


# --------------------------------------------------------- adapter shape test


def _sample_canonical_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "artifact_name": {"type": "string", "const": "audit_finding"},
            "severity": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
            },
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "path"],
                    "properties": {
                        "id": {"type": "string"},
                        "path": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
        },
        "required": ["artifact_name", "severity", "items"],
        "additionalProperties": False,
    }


def test_adapter_returns_tool_def_shape() -> None:
    tool_def = adapt_canonical_schema_for_variant(
        _sample_canonical_schema(),
        variant="anthropic_tool_use",
        schema_name="audit_finding_draft",
    )
    assert set(tool_def.keys()) == {"name", "description", "input_schema"}
    assert tool_def["name"].startswith("emit_")
    assert tool_def["name"] == "emit_audit_finding_draft"
    assert tool_def["input_schema"]["type"] == "object"


def test_adapter_preserves_required_and_enums() -> None:
    canonical = _sample_canonical_schema()
    tool_def = adapt_canonical_schema_for_variant(
        canonical,
        variant="anthropic_tool_use",
        schema_name="x",
    )
    schema = tool_def["input_schema"]
    assert schema["required"] == ["artifact_name", "severity", "items"]
    assert schema["properties"]["severity"]["enum"] == [
        "low",
        "medium",
        "high",
        "critical",
    ]
    # The const constraint is preserved (canonical schema; we do not strip it
    # for Anthropic — only xai_relaxed does).
    assert schema["properties"]["artifact_name"]["const"] == "audit_finding"


def test_adapter_does_not_mutate_input_schema() -> None:
    canonical = _sample_canonical_schema()
    before = repr(canonical)
    _ = adapt_canonical_schema_for_variant(
        canonical, variant="anthropic_tool_use", schema_name="x"
    )
    assert repr(canonical) == before


def test_adapter_name_sanitizes_unsafe_characters() -> None:
    tool_def = adapt_canonical_schema_for_variant(
        _sample_canonical_schema(),
        variant="anthropic_tool_use",
        schema_name="a.b/c d#1",
    )
    # Tool name must match ^[a-zA-Z0-9_-]{1,64}$
    import re

    assert re.fullmatch(r"emit_[A-Za-z0-9_-]{1,60}", tool_def["name"])


def test_adapter_wraps_non_object_root() -> None:
    schema = {"anyOf": [{"type": "string"}, {"type": "number"}]}
    tool_def = adapt_canonical_schema_for_variant(
        schema, variant="anthropic_tool_use", schema_name="x"
    )
    assert tool_def["input_schema"]["type"] == "object"
    assert "_root_" in tool_def["input_schema"]["properties"]


def test_adapter_emit_prefix_check_is_case_insensitive() -> None:
    """Inputs starting with 'EMIT_' / 'Emit_' shouldn't be double-prefixed."""
    for raw in ("EMIT_X", "Emit_x", "emit_x"):
        tool_def = adapt_canonical_schema_for_variant(
            _sample_canonical_schema(),
            variant="anthropic_tool_use",
            schema_name=raw,
        )
        # The case-insensitive check must NOT add an extra 'emit_' prefix.
        assert tool_def["name"].lower().startswith("emit_")
        assert not tool_def["name"].lower().startswith("emit_emit_")


def test_adapter_description_collapses_whitespace_and_truncates() -> None:
    """Multi-line / very long descriptions must be collapsed + bounded."""
    noisy = "line one\nline two\n\n\tline three " + ("X" * 1000)
    tool_def = adapt_canonical_schema_for_variant(
        _sample_canonical_schema(),
        variant="anthropic_tool_use",
        schema_name="x",
        description=noisy,
    )
    assert "\n" not in tool_def["description"]
    assert "\t" not in tool_def["description"]
    assert len(tool_def["description"]) <= 240


def test_adapter_default_description_safe_from_unbounded_name() -> None:
    """When no description supplied, default description sanitizes raw_name."""
    long_name = "a_" + ("b" * 500)
    tool_def = adapt_canonical_schema_for_variant(
        _sample_canonical_schema(),
        variant="anthropic_tool_use",
        schema_name=long_name,
    )
    # Default description embeds raw_name but is bounded to ≤ 240 chars.
    assert "\n" not in tool_def["description"]
    assert len(tool_def["description"]) <= 240


def test_adapter_raises_value_error_when_schema_name_missing() -> None:
    """Per docstring contract: schema_name is required for anthropic_tool_use.
    Fail closed rather than silently substituting a default that risks
    tool-choice collisions."""
    import pytest

    for missing in (None, "", "   "):
        with pytest.raises(ValueError, match="schema_name"):
            adapt_canonical_schema_for_variant(
                _sample_canonical_schema(),
                variant="anthropic_tool_use",
                schema_name=missing,
            )


# ----------------------------- build_provider_structured_output anthropic path


def test_build_provider_structured_output_anthropic_returns_tool_use_payload() -> None:
    schema = _sample_canonical_schema()
    response_format, meta = build_provider_structured_output(
        route={"provider": "anthropic", "model_id": "claude-opus-4.6"},
        transport="anthropic_messages_http",
        schema=schema,
        schema_name="audit_finding_draft",
        strict=True,
        contract_lane_name="ce_critical",
        mode=STRUCTURED_OUTPUT_MODE_JSON_SCHEMA,
    )
    assert isinstance(response_format, dict)
    assert set(response_format.keys()) == {"tools", "tool_choice"}
    assert len(response_format["tools"]) == 1
    assert response_format["tool_choice"] == {
        "type": "tool",
        "name": response_format["tools"][0]["name"],
    }
    assert meta["schema_variant"] == "anthropic_tool_use"
    assert meta["transport_mode"] == "anthropic_tool_use"
    assert meta["enabled"] is True
    assert meta["strict"] is True
    assert meta["anthropic_tool_use_payload"] == response_format


def test_build_provider_structured_output_openrouter_anthropic_uses_tool_use() -> None:
    schema = _sample_canonical_schema()
    response_format, meta = build_provider_structured_output(
        route={"provider": "openrouter", "model_id": "anthropic/claude-sonnet-4.6"},
        transport="openai_compat_http",
        schema=schema,
        schema_name="audit_finding_draft",
        strict=True,
        contract_lane_name="ce_critical",
        mode=STRUCTURED_OUTPUT_MODE_JSON_SCHEMA,
    )
    assert "tools" in response_format
    assert meta["schema_variant"] == "anthropic_tool_use"
    assert meta["provider_schema_variant"] == "openrouter_proxy_anthropic_tool_use"


def test_build_provider_structured_output_openai_unchanged_regression() -> None:
    """Regression: OpenAI route still returns response_format json_schema dict."""
    schema = _sample_canonical_schema()
    response_format, meta = build_provider_structured_output(
        route={"provider": "openai", "model_id": "gpt-5"},
        transport="openai_compat_http",
        schema=schema,
        schema_name="audit_finding_draft",
        strict=True,
        contract_lane_name="ce_critical",
        mode=STRUCTURED_OUTPUT_MODE_JSON_SCHEMA,
    )
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert meta["schema_variant"] == "canonical"
    assert meta["transport_mode"] == "response_format_json_schema"
