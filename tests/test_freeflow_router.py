from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml
from click.testing import CliRunner

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from dopemux.freeflow import (  # noqa: E402
    FreeflowQuotaLedger,
    FreeflowRouter,
    PROVIDER_CATALOG,
)
from dopemux.routing_config import RoutingConfig  # noqa: E402
from dopemux.routing_cli import routing  # noqa: E402


def _config() -> dict:
    return {
        "version": 1,
        "mode": "api",
        "ports": {"litellm": 4000, "ccr": 4010},
        "providers": [
            {
                "name": "ollama",
                "auth_mode": "none",
                "base_url": "http://127.0.0.1:11434",
            },
            {"name": "lmstudio", "auth_mode": "none", "api_key": "local"},
            {"name": "gemini", "api_key_env": "GEMINI_API_KEY"},
            {
                "name": "openrouter_free",
                "api_key_env": "OPENROUTER_API_KEY",
                "base_url": "https://openrouter.ai/api/v1",
            },
            {"name": "gemini_paid_cap", "api_key_env": "GEMINI_API_KEY"},
            {
                "name": "openrouter_paid_cap",
                "api_key_env": "OPENROUTER_API_KEY",
                "base_url": "https://openrouter.ai/api/v1",
            },
            {"name": "openai", "api_key_env": "OPENAI_API_KEY"},
            {"name": "openrouter", "api_key_env": "OPENROUTER_API_KEY"},
        ],
        "models": [
            {
                "name": "ollama-qwen3-coder",
                "provider": "ollama",
                "model_id": "ollama/qwen3-coder",
            },
            {
                "name": "lmstudio-local",
                "provider": "lmstudio",
                "model_id": "openai/local-model",
            },
            {
                "name": "gemini-2.5-flash-lite",
                "provider": "gemini",
                "model_id": "gemini/gemini-2.5-flash-lite",
            },
            {
                "name": "openrouter-free-router",
                "provider": "openrouter_free",
                "model_id": "openrouter/openrouter/free",
            },
            {
                "name": "gemini-flash-lite-preview-paid-cap",
                "provider": "gemini_paid_cap",
                "model_id": "gemini/gemini-2.5-flash-lite-preview-09-2025",
            },
            {
                "name": "openrouter-qwen3-coder-next-paid-cap",
                "provider": "openrouter_paid_cap",
                "model_id": "openrouter/qwen/qwen3-coder-next",
            },
            {
                "name": "openrouter-qwen3-coder-paid-cap",
                "provider": "openrouter_paid_cap",
                "model_id": "openrouter/qwen/qwen3-coder",
            },
            {
                "name": "openai-paid",
                "provider": "openai",
                "model_id": "openai/gpt-5-mini",
            },
            {
                "name": "openrouter-paid",
                "provider": "openrouter",
                "model_id": "openrouter/openai/gpt-5",
            },
        ],
        "slots": {"default": "openai-paid", "sonnet": "openai-paid"},
        "fallbacks": {
            "ollama-qwen3-coder": ["openai-paid", "gemini-2.5-flash-lite"],
            "gemini-2.5-flash-lite": ["openrouter-paid", "openrouter-free-router"],
        },
        "default_fallbacks": ["openai-paid", "gemini-2.5-flash-lite"],
        "aliases": {"claude-sonnet": "sonnet", "gpt-5": "sonnet"},
        "freeflow": {
            "enabled": True,
            "mode": "strict_free",
            "privacy_default": "local",
            "slots": {
                "default": "ollama-qwen3-coder",
                "sonnet": "ollama-qwen3-coder",
                "haiku": "gemini-2.5-flash-lite",
            },
            "default_fallbacks": [
                "lmstudio-local",
                "ollama-qwen3-coder",
                "gemini-2.5-flash-lite",
                "openrouter-free-router",
            ],
            "paid_cap": {
                "enabled": False,
                "daily_usd": 0.5,
                "monthly_usd": 5.0,
                "allowed_models": [
                    "gemini-flash-lite-preview-paid-cap",
                    "openrouter-qwen3-coder-next-paid-cap",
                ],
                "default_fallbacks": [
                    "gemini-flash-lite-preview-paid-cap",
                    "openrouter-qwen3-coder-next-paid-cap",
                ],
            },
        },
    }


def test_provider_catalog_contains_required_freeflow_providers() -> None:
    assert {
        "ollama",
        "lmstudio",
        "gemini",
        "groq",
        "cerebras",
        "openrouter_free",
        "cloudflare_workers_ai",
        "cohere_trial",
        "mistral_experiment",
        "github_models_poc",
        "hf_credits",
        "gemini_paid_cap",
        "openrouter_paid_cap",
    }.issubset(PROVIDER_CATALOG)


def test_sensitive_requests_select_only_local_routes(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")
    decision = FreeflowRouter(_config(), ledger).choose_route(
        sensitivity_class="memory",
        estimated_input_tokens=10,
        estimated_output_tokens=10,
    )

    assert decision["decision"] == "selected"
    assert decision["provider"] in {"ollama", "lmstudio"}


def test_non_sensitive_requests_prefer_hosted_free_when_available(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")
    decision = FreeflowRouter(_config(), ledger).choose_route(
        sensitivity_class="non_sensitive",
        estimated_input_tokens=10,
        estimated_output_tokens=10,
    )

    assert decision["decision"] == "selected"
    assert decision["provider"] == "gemini"


def test_strict_free_litellm_config_filters_paid_routes(tmp_path: Path) -> None:
    path = tmp_path / "routing.yaml"
    path.write_text(yaml.safe_dump(_config(), sort_keys=False), encoding="utf-8")
    routing_config = RoutingConfig(path)
    routing_config.load()

    generated = routing_config.generate_litellm_config("sk-test")
    model_names = {row["model_name"] for row in generated["model_list"]}
    serialized = json.dumps(generated, sort_keys=True)

    assert "openai-paid" not in model_names
    assert "openrouter-paid" not in model_names
    assert "gemini-flash-lite-preview-paid-cap" not in model_names
    assert "openrouter-qwen3-coder-next-paid-cap" not in model_names
    assert "openai/gpt-5-mini" not in serialized
    assert "openrouter/openai/gpt-5" not in serialized
    assert (
        generated["litellm_settings"]["model_alias_map"]["claude-sonnet"]
        == "ollama-qwen3-coder"
    )
    assert set(generated["litellm_settings"]["default_fallbacks"]).issubset(model_names)


def test_strict_free_litellm_config_uses_deterministic_default_fallback(
    tmp_path: Path,
) -> None:
    data = _config()
    data["freeflow"]["slots"].pop("default")
    data["freeflow"]["slots"].pop("sonnet")
    path = tmp_path / "routing.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    routing_config = RoutingConfig(path)
    routing_config.load()

    generated = routing_config.generate_litellm_config("sk-test")

    assert generated["litellm_settings"]["model_alias_map"]["claude-sonnet"] == (
        "ollama-qwen3-coder"
    )
    assert generated["litellm_settings"]["model_alias_map"]["gpt-5"] == (
        "ollama-qwen3-coder"
    )


def test_local_auth_mode_validates_without_api_key_env(tmp_path: Path) -> None:
    path = tmp_path / "routing.yaml"
    path.write_text(yaml.safe_dump(_config(), sort_keys=False), encoding="utf-8")

    config = RoutingConfig(path)
    loaded = config.load()

    assert loaded["providers"][0]["auth_mode"] == "none"


def test_local_base_url_with_inline_auth_mode_validates(
    tmp_path: Path,
) -> None:
    data = _config()
    data["providers"].append(
        {
            "name": "proxy_local",
            "auth_mode": "none",
            "base_url": "http://localhost:12345/v1",
        }
    )
    data["models"].append(
        {
            "name": "proxy-local-model",
            "provider": "proxy_local",
            "model_id": "proxy/local-model",
        }
    )
    path = tmp_path / "routing.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    config = RoutingConfig(path)
    loaded = config.load()

    assert loaded["providers"][-1]["auth_mode"] == "none"


def test_hosted_provider_with_inline_auth_mode_fails_validation(
    tmp_path: Path,
) -> None:
    data = _config()
    data["providers"].append(
        {
            "name": "openai_inline",
            "auth_mode": "none",
            "api_key": "dummy",
            "base_url": "https://api.openai.com/v1",
        }
    )
    data["models"].append(
        {
            "name": "openai-inline-model",
            "provider": "openai_inline",
            "model_id": "openai/gpt-5-mini",
        }
    )
    path = tmp_path / "routing.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    config = RoutingConfig(path)

    try:
        config.load()
    except Exception as exc:
        assert "not a local provider" in str(exc)
    else:
        raise AssertionError("expected hosted inline auth validation to fail")


def test_hosted_provider_without_api_key_env_fails_validation(tmp_path: Path) -> None:
    data = _config()
    data["providers"].append({"name": "bad_hosted"})
    data["models"].append(
        {"name": "bad-hosted-model", "provider": "bad_hosted", "model_id": "bad/model"}
    )
    path = tmp_path / "routing.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")

    config = RoutingConfig(path)

    try:
        config.load()
    except Exception as exc:
        assert "missing 'api_key_env'" in str(exc)
    else:
        raise AssertionError("expected hosted provider validation to fail")


def test_freeflow_cli_doctor_json(tmp_path: Path, monkeypatch) -> None:
    routing_path = tmp_path / "routing.yaml"
    ledger_path = tmp_path / "quota.sqlite"
    routing_path.write_text(
        yaml.safe_dump(_config(), sort_keys=False), encoding="utf-8"
    )
    monkeypatch.setenv("DOPEMUX_FREEFLOW_LEDGER", str(ledger_path))
    monkeypatch.setattr(RoutingConfig, "DEFAULT_CONFIG_PATH", routing_path)

    result = CliRunner().invoke(
        routing,
        ["freeflow", "doctor", "--offline", "--json"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["enabled"] is True
    assert payload["summary"]["blocked_paid_or_unknown_routes"] >= 2
    assert payload["ledger_path"] == str(ledger_path)


def test_freeflow_cli_quota_json(tmp_path: Path, monkeypatch) -> None:
    ledger_path = tmp_path / "quota.sqlite"
    monkeypatch.setenv("DOPEMUX_FREEFLOW_LEDGER", str(ledger_path))

    result = CliRunner().invoke(routing, ["freeflow", "quota", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ledger_path"] == str(ledger_path)
    assert "buckets" in payload
    assert "cooldowns" in payload


def test_freeflow_cli_routes_json(tmp_path: Path, monkeypatch) -> None:
    routing_path = tmp_path / "routing.yaml"
    routing_path.write_text(
        yaml.safe_dump(_config(), sort_keys=False), encoding="utf-8"
    )
    monkeypatch.setattr(RoutingConfig, "DEFAULT_CONFIG_PATH", routing_path)

    result = CliRunner().invoke(routing, ["freeflow", "routes", "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    route_names = {route["name"] for route in payload["routes"]}
    assert "ollama-qwen3-coder" in route_names
    assert "openai-paid" in route_names
    paid_route = next(
        route for route in payload["routes"] if route["name"] == "openai-paid"
    )
    assert paid_route["strict_free_allowed"] is False


def test_paid_cap_enabled_adds_only_allowlisted_paid_routes(tmp_path: Path) -> None:
    data = _config()
    data["freeflow"]["paid_cap"]["enabled"] = True
    path = tmp_path / "routing.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    routing_config = RoutingConfig(path)
    routing_config.load()

    generated = routing_config.generate_litellm_config("sk-test")
    model_names = {row["model_name"] for row in generated["model_list"]}
    preview = next(
        row
        for row in generated["model_list"]
        if row["model_name"] == "gemini-flash-lite-preview-paid-cap"
    )

    assert "gemini-flash-lite-preview-paid-cap" in model_names
    assert "openrouter-qwen3-coder-next-paid-cap" in model_names
    assert "openrouter-qwen3-coder-paid-cap" not in model_names
    assert "openai-paid" not in model_names
    assert (
        preview["litellm_params"]["model"]
        == "gemini/gemini-2.5-flash-lite-preview-09-2025"
    )
    assert preview["model_info"]["freeflow_paid"] is True
    assert preview["model_info"]["freeflow_pricing"] == {
        "input_usd_per_million": 0.10,
        "output_usd_per_million": 0.40,
    }


def test_paid_cap_route_selected_only_when_free_routes_disabled(
    tmp_path: Path, monkeypatch
) -> None:
    data = _config()
    data["freeflow"]["paid_cap"]["enabled"] = True
    data["freeflow"]["disabled_models"] = [
        "ollama-qwen3-coder",
        "lmstudio-local",
        "gemini-2.5-flash-lite",
        "openrouter-free-router",
    ]
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")
    decision = FreeflowRouter(data, ledger).choose_route(
        sensitivity_class="non_sensitive",
        estimated_input_tokens=1000,
        estimated_output_tokens=1000,
    )

    assert decision["decision"] == "selected"
    assert decision["reason"] == "paid_cap_route_selected"
    assert decision["model_name"] == "gemini-flash-lite-preview-paid-cap"


def test_sensitive_requests_do_not_select_paid_cap_route(
    tmp_path: Path, monkeypatch
) -> None:
    data = _config()
    data["freeflow"]["paid_cap"]["enabled"] = True
    data["freeflow"]["disabled_models"] = [
        "ollama-qwen3-coder",
        "lmstudio-local",
        "gemini-2.5-flash-lite",
        "openrouter-free-router",
    ]
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    ledger = FreeflowQuotaLedger(tmp_path / "quota.sqlite")
    decision = FreeflowRouter(data, ledger).choose_route(
        sensitivity_class="memory",
        estimated_input_tokens=1000,
        estimated_output_tokens=1000,
    )

    assert decision["decision"] != "selected"
    assert decision["provider"] is None
