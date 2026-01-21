"""Tests for Claude Code Router integration helpers."""

from __future__ import annotations

import json
import sys
from importlib import util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "dopemux" / "dope_brainz_router.py"
MODULE_NAME = "dopemux.dope_brainz_router"
spec = util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
claude_router = util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[MODULE_NAME] = claude_router
spec.loader.exec_module(claude_router)

ClaudeCodeRouterInfo = claude_router.ClaudeCodeRouterInfo
ClaudeCodeRouterManager = claude_router.ClaudeCodeRouterManager


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def test_prepare_config_creates_expected_layout(tmp_path):
    manager = ClaudeCodeRouterManager(tmp_path, "B", 3030)

    config_path = manager.prepare_config(
        provider_url="http://127.0.0.1:4130/v1/chat/completions",
        provider_models=("openrouter-openai-gpt-5", "openrouter-openai-gpt-5-mini"),
        provider_name="litellm",
        provider_key_env_var="DOPEMUX_LITELLM_MASTER_KEY",
    )

    config = _read_json(config_path)
    assert config["PORT"] == 3486
    assert config["HOST"] == "127.0.0.1"
    assert config["NON_INTERACTIVE_MODE"] is True
    assert config["APIKEY"]

    provider_entries = {p["name"]: p for p in config["Providers"]}
    assert provider_entries["litellm"]["api_base_url"].endswith("/v1/chat/completions")
    assert provider_entries["litellm"]["api_key"] == "$DOPEMUX_LITELLM_MASTER_KEY"
    assert provider_entries["litellm"]["models"] == [
        "openrouter-openai-gpt-5",
        "openrouter-openai-gpt-5-mini",
    ]

    assert config["Router"]["default"] == "litellm,openrouter-openai-gpt-5"
    assert config["Router"]["background"] == "litellm,openrouter-xai-grok-code-fast"

    assert manager.api_key_path.exists()
    assert manager._process_env_overrides["HOME"].endswith("claude-code-router/B")
    assert manager._process_env_overrides["SERVICE_PORT"] == "3486"


def test_prepare_config_preserves_other_providers(tmp_path):
    manager = ClaudeCodeRouterManager(tmp_path, "A", 3000)
    manager.prepare_config(
        provider_url="http://127.0.0.1:4100/v1/chat/completions",
        provider_models=("openrouter-openai-gpt-5", "openrouter-openai-gpt-5-mini"),
    )

    config = _read_json(manager.config_path)
    config["Providers"].append(
        {
            "name": "custom",
            "api_base_url": "https://api.example.com/v1",
            "api_key": "dummy",
            "models": ["custom-model"],
        }
    )
    manager.config_path.write_text(json.dumps(config, indent=2))

    # Update with a new provider URL to ensure replacement happens
    manager.prepare_config(
        provider_url="http://127.0.0.1:4101/v1/chat/completions",
        provider_models=("openrouter-openai-gpt-5",),
    )

    updated = _read_json(manager.config_path)
    providers = {p["name"]: p for p in updated["Providers"]}
    assert "custom" in providers
    assert providers["litellm"]["api_base_url"].endswith("4101/v1/chat/completions")
    assert providers["litellm"]["models"] == ["openrouter-openai-gpt-5"]


def test_build_client_env(tmp_path):
    manager = ClaudeCodeRouterManager(tmp_path, "C", 3060)
    manager.prepare_config(
        provider_url="http://127.0.0.1:4150/v1/chat/completions",
        provider_models=("openrouter-openai-gpt-5",),
    )

    info = ClaudeCodeRouterInfo(
        host=manager.host,
        port=manager.port,
        config_path=manager.config_path,
        home_path=manager.instance_home,
        log_path=manager.log_path,
        api_key=manager._api_key,
        already_running=True,
    )

    env = manager.build_client_env(info)
    assert env["ANTHROPIC_BASE_URL"] == info.base_url
    assert env["ANTHROPIC_API_KEY"] == manager._api_key
    assert env["CLAUDE_CODE_ROUTER_CONFIG"] == str(manager.config_path)
    assert env["CLAUDE_CODE_ROUTER_HOME"].endswith("C")
