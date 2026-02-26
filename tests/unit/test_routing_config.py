"""Unit tests for RoutingConfig: validate(), generate_litellm_config(), generate_ccr_config()."""

from __future__ import annotations

import pytest
import yaml

from dopemux.routing_config import RoutingConfig, RoutingConfigError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_valid_config() -> dict:
    """Return the smallest valid routing config that passes validate()."""
    return {
        "version": 1,
        "mode": "subscription",
        "ports": {"litellm": 4000, "ccr": 4010},
        "providers": [
            {"name": "xai", "api_key_env": "XAI_API_KEY", "base_url": "https://api.x.ai/v1"},
        ],
        "models": [
            {"name": "grok-fast", "provider": "xai", "model_id": "xai/grok-fast"},
        ],
        "slots": {"default": "grok-fast"},
        "fallbacks": {},
        "default_fallbacks": [],
        "aliases": {},
    }


def _make_config(cfg: dict, tmp_path) -> RoutingConfig:
    """Write a routing config to a temp file and return a loaded RoutingConfig."""
    config_file = tmp_path / "routing.yaml"
    config_file.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    rc = RoutingConfig(config_path=config_file)
    rc.load()
    return rc


# ---------------------------------------------------------------------------
# validate() – happy-path
# ---------------------------------------------------------------------------

def test_validate_minimal_config_passes(tmp_path):
    cfg = _minimal_valid_config()
    rc = _make_config(cfg, tmp_path)
    # load() calls validate(); reaching here means no exception was raised.
    assert rc._loaded is True


def test_validate_alias_to_slot(tmp_path):
    cfg = _minimal_valid_config()
    cfg["aliases"] = {"fast": "default"}  # points to a slot name
    _make_config(cfg, tmp_path)  # should not raise


def test_validate_alias_to_model_directly(tmp_path):
    cfg = _minimal_valid_config()
    cfg["aliases"] = {"direct": "grok-fast"}  # points directly to a model name
    _make_config(cfg, tmp_path)  # should not raise


# ---------------------------------------------------------------------------
# validate() – failure modes
# ---------------------------------------------------------------------------

def test_validate_missing_providers_raises(tmp_path):
    cfg = _minimal_valid_config()
    cfg["providers"] = []
    with pytest.raises(RoutingConfigError, match="(?i)providers"):
        _make_config(cfg, tmp_path)


def test_validate_provider_missing_api_key_env_raises(tmp_path):
    cfg = _minimal_valid_config()
    cfg["providers"][0].pop("api_key_env")
    with pytest.raises(RoutingConfigError, match="api_key_env"):
        _make_config(cfg, tmp_path)


def test_validate_model_references_unknown_provider_raises(tmp_path):
    cfg = _minimal_valid_config()
    cfg["models"][0]["provider"] = "nonexistent"
    with pytest.raises(RoutingConfigError, match="unknown provider"):
        _make_config(cfg, tmp_path)


def test_validate_slot_references_unknown_model_raises(tmp_path):
    cfg = _minimal_valid_config()
    cfg["slots"] = {"default": "ghost-model"}
    with pytest.raises(RoutingConfigError, match="unknown model"):
        _make_config(cfg, tmp_path)


def test_validate_fallback_references_unknown_model_raises(tmp_path):
    cfg = _minimal_valid_config()
    cfg["fallbacks"] = {"grok-fast": ["no-such-model"]}
    with pytest.raises(RoutingConfigError, match="unknown model"):
        _make_config(cfg, tmp_path)


def test_validate_default_fallbacks_unknown_model_raises(tmp_path):
    cfg = _minimal_valid_config()
    cfg["default_fallbacks"] = ["no-such-model"]
    with pytest.raises(RoutingConfigError, match="unknown model"):
        _make_config(cfg, tmp_path)


def test_validate_alias_unknown_target_raises(tmp_path):
    cfg = _minimal_valid_config()
    cfg["aliases"] = {"bad-alias": "nowhere"}
    with pytest.raises(RoutingConfigError, match="unknown slot or model"):
        _make_config(cfg, tmp_path)


# ---------------------------------------------------------------------------
# generate_litellm_config()
# ---------------------------------------------------------------------------

def test_generate_litellm_config_structure(tmp_path):
    cfg = _minimal_valid_config()
    rc = _make_config(cfg, tmp_path)
    result = rc.generate_litellm_config(master_key="test-master-key")

    assert "model_list" in result
    assert "litellm_settings" in result
    assert "general_settings" in result
    assert result["general_settings"]["master_key"] == "test-master-key"

    # Model list should contain one entry
    assert len(result["model_list"]) == 1
    entry = result["model_list"][0]
    assert entry["model_name"] == "grok-fast"
    assert "litellm_params" in entry
    assert entry["litellm_params"]["model"] == "xai/grok-fast"


def test_generate_litellm_config_alias_to_slot(tmp_path):
    cfg = _minimal_valid_config()
    cfg["aliases"] = {"fast": "default"}  # slot → model "grok-fast"
    rc = _make_config(cfg, tmp_path)
    result = rc.generate_litellm_config(master_key="k")

    alias_map = result["litellm_settings"]["model_alias_map"]
    assert alias_map.get("fast") == "grok-fast"


def test_generate_litellm_config_alias_to_model_directly(tmp_path):
    """Aliases pointing directly at a model name must not raise KeyError."""
    cfg = _minimal_valid_config()
    cfg["aliases"] = {"direct": "grok-fast"}  # directly references a model
    rc = _make_config(cfg, tmp_path)
    result = rc.generate_litellm_config(master_key="k")

    alias_map = result["litellm_settings"]["model_alias_map"]
    assert alias_map.get("direct") == "grok-fast"


def test_generate_litellm_config_slot_mappings(tmp_path):
    cfg = _minimal_valid_config()
    rc = _make_config(cfg, tmp_path)
    result = rc.generate_litellm_config(master_key="k")

    alias_map = result["litellm_settings"]["model_alias_map"]
    # Slot "default" should map to "grok-fast"
    assert alias_map.get("default") == "grok-fast"


def test_generate_litellm_config_raises_when_not_loaded(tmp_path):
    config_file = tmp_path / "routing.yaml"
    config_file.write_text(yaml.safe_dump(_minimal_valid_config()), encoding="utf-8")
    rc = RoutingConfig(config_path=config_file)
    # Do NOT call rc.load()
    with pytest.raises(RoutingConfigError, match="not loaded"):
        rc.generate_litellm_config(master_key="k")


# ---------------------------------------------------------------------------
# generate_ccr_config()
# ---------------------------------------------------------------------------

def test_generate_ccr_config_structure(tmp_path):
    cfg = _minimal_valid_config()
    rc = _make_config(cfg, tmp_path)
    result = rc.generate_ccr_config(
        litellm_url="http://127.0.0.1:4000",
        litellm_key="my-litellm-key",
        ccr_api_key="my-ccr-key",
    )

    assert result["provider"] == "litellm"
    assert result["upstream_url"] == "http://127.0.0.1:4000"
    assert result["upstream_key"] == "my-litellm-key"
    assert result["api_key"] == "my-ccr-key"
    assert result["listen_port"] == 4010
    assert "default" in result["models"]


def test_generate_ccr_config_uses_litellm_key(tmp_path):
    """litellm_key must appear in the returned config (not silently dropped)."""
    cfg = _minimal_valid_config()
    rc = _make_config(cfg, tmp_path)
    result = rc.generate_ccr_config(
        litellm_url="http://127.0.0.1:4000",
        litellm_key="secret-key",
        ccr_api_key="ccr-key",
    )
    assert result.get("upstream_key") == "secret-key"
