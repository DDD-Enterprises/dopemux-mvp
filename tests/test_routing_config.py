from types import SimpleNamespace
from pathlib import Path
from copy import deepcopy

import yaml
from click.testing import CliRunner

import dopemux.routing_cli as routing_cli
from dopemux.routing_config import RoutingConfig, RoutingConfigError


def _write_yaml(path, data):
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _make_config(tmp_path, monkeypatch):
    template_path = tmp_path / "routing-template.yaml"
    config_path = tmp_path / "routing.yaml"

    template = {
        "version": 1,
        "mode": "api",
        "ports": {"litellm": 4000, "ccr": 4010},
        "providers": [{"name": "openai", "api_key_env": "OPENAI_API_KEY"}],
        "models": [{"name": "gpt-5.4-mini", "provider": "openai", "model_id": "openai/gpt-5.4-mini"}],
        "slots": {"default": "gpt-5.4-mini", "opus": "gpt-5.4-mini"},
        "fallbacks": {"gpt-5.4-mini": []},
        "default_fallbacks": ["gpt-5.4-mini"],
        "aliases": {"grok": "default", "claude-opus-4-6": "opus"},
    }
    _write_yaml(template_path, template)
    monkeypatch.setattr(RoutingConfig, "TEMPLATE_PATH", template_path)
    return template, config_path


def test_audit_alias_contract_reports_missing_and_mismatched_aliases(tmp_path, monkeypatch):
    template, config_path = _make_config(tmp_path, monkeypatch)
    current = dict(template)
    current["aliases"] = {"grok": "opus", "custom": "default"}
    _write_yaml(config_path, current)

    config = RoutingConfig(config_path=config_path)
    audit = config.audit_alias_contract()

    assert audit["stale"] is True
    assert audit["missing_aliases"] == {"claude-opus-4-6": "opus"}
    assert audit["mismatched_aliases"] == {
        "grok": {"expected": "default", "actual": "opus"}
    }


def test_repair_alias_contract_updates_template_aliases_only_and_creates_backup(
    tmp_path, monkeypatch
):
    template, config_path = _make_config(tmp_path, monkeypatch)
    current = dict(template)
    current["aliases"] = {"grok": "opus", "custom": "default"}
    _write_yaml(config_path, current)

    config = RoutingConfig(config_path=config_path)
    result = config.repair_alias_contract()
    repaired = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert result["changed"] is True
    assert result["audit"]["stale"] is False
    assert result["backup_path"] is not None
    assert Path(result["backup_path"]).exists()
    assert repaired["aliases"]["grok"] == "default"
    assert repaired["aliases"]["claude-opus-4-6"] == "opus"
    assert repaired["aliases"]["custom"] == "default"


def test_routing_doctor_reports_stale_alias_contract(tmp_path, monkeypatch):
    template, config_path = _make_config(tmp_path, monkeypatch)
    current = dict(template)
    current["aliases"] = {"grok": "default"}
    _write_yaml(config_path, current)

    config = RoutingConfig(config_path=config_path)
    fake_manager = SimpleNamespace(routing_config=config)
    monkeypatch.setattr(
        routing_cli.LaunchdServiceManager,
        "get_instance",
        staticmethod(lambda: fake_manager),
    )

    result = CliRunner().invoke(routing_cli.routing, ["doctor"])

    assert result.exit_code == 1
    assert "Stale routing alias contract detected" in result.output
    assert "claude-opus-4-6: expected opus" in result.output
    assert "dopemux routing repair-aliases --apply" in result.output


def test_routing_repair_aliases_apply_repairs_file(tmp_path, monkeypatch):
    template, config_path = _make_config(tmp_path, monkeypatch)
    current = dict(template)
    current["aliases"] = {"grok": "opus", "custom": "default"}
    _write_yaml(config_path, current)

    config = RoutingConfig(config_path=config_path)
    fake_manager = SimpleNamespace(routing_config=config)
    monkeypatch.setattr(
        routing_cli.LaunchdServiceManager,
        "get_instance",
        staticmethod(lambda: fake_manager),
    )

    result = CliRunner().invoke(routing_cli.routing, ["repair-aliases", "--apply"])
    repaired = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert result.exit_code == 0
    assert "Alias contract repaired" in result.output
    assert "Backup:" in result.output
    assert repaired["aliases"]["grok"] == "default"
    assert repaired["aliases"]["claude-opus-4-6"] == "opus"
    assert repaired["aliases"]["custom"] == "default"


def test_legacy_entries_without_enabled_remain_active(tmp_path, monkeypatch):
    template, config_path = _make_config(tmp_path, monkeypatch)
    _write_yaml(config_path, template)

    config = RoutingConfig(config_path=config_path)
    config.load()
    generated = config.generate_litellm_config("test-master-key")

    assert [entry["model_name"] for entry in generated["model_list"]] == [
        "gpt-5.4-mini"
    ]


def test_disabled_provider_and_models_are_omitted_from_active_generation(
    tmp_path, monkeypatch
):
    template, config_path = _make_config(tmp_path, monkeypatch)
    template["providers"].append(
        {
            "name": "candidate",
            "api_key_env": "CANDIDATE_API_KEY",
            "enabled": False,
        }
    )
    template["models"].extend(
        [
            {
                "name": "disabled-provider-model",
                "provider": "candidate",
                "model_id": "openai/candidate",
            },
            {
                "name": "disabled-model",
                "provider": "openai",
                "model_id": "openai/disabled",
                "enabled": False,
            },
        ]
    )
    _write_yaml(config_path, template)

    config = RoutingConfig(config_path=config_path)
    config.load()
    generated = config.generate_litellm_config("test-master-key")

    assert {entry["model_name"] for entry in generated["model_list"]} == {
        "gpt-5.4-mini"
    }


def test_disabled_models_cannot_be_routing_targets(tmp_path, monkeypatch):
    template, config_path = _make_config(tmp_path, monkeypatch)
    template["models"].append(
        {
            "name": "candidate",
            "provider": "openai",
            "model_id": "openai/candidate",
            "enabled": False,
        }
    )
    template["slots"]["candidate"] = "candidate"
    _write_yaml(config_path, template)

    config = RoutingConfig(config_path=config_path)

    try:
        config.load()
    except RoutingConfigError as exc:
        assert "disabled model" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("disabled slot target unexpectedly validated")


def test_repo_template_kimi_fable_routes_are_qualified_and_not_promoted():
    routing = yaml.safe_load(RoutingConfig.TEMPLATE_PATH.read_text(encoding="utf-8"))
    providers = {provider["name"]: provider for provider in routing["providers"]}
    models = {model["name"]: model for model in routing["models"]}

    assert providers["cheaperinference"]["enabled"] is True
    assert providers["openrouter"]["enabled"] is False
    assert providers["moonshot"]["enabled"] is False
    assert providers["anthropic"]["enabled"] is False

    assert models["kimi-k3-ci"]["pal"]["reasoning_efforts"] == [
        "low",
        "high",
        "max",
    ]
    assert "medium" not in models["kimi-k3-ci"]["pal"]["reasoning_efforts"]
    assert models["kimi-k3-ci"]["pal"]["thinking_mode"] == "always_on"
    assert models["fable-5-ci"]["pal"]["thinking_mode"] == "adaptive_always_on"
    assert models["fable-5-ci"]["pal"]["max_output_tokens"] == 128000

    candidate_names = {
        "kimi-k3-or",
        "fable-5-or",
        "kimi-k3-direct",
        "fable-5-direct",
    }
    assert all(models[name]["enabled"] is False for name in candidate_names)
    promoted = set(routing["slots"].values()) | set(routing["default_fallbacks"])
    promoted.update(
        candidate
        for fallback_list in routing["fallbacks"].values()
        for candidate in fallback_list
    )
    assert not ({"kimi-k3-ci", "fable-5-ci"} | candidate_names) & promoted


def test_full_catalog_generation_includes_active_ci_routes_and_omits_candidates(
    tmp_path
):
    routing = yaml.safe_load(RoutingConfig.TEMPLATE_PATH.read_text(encoding="utf-8"))
    routing["freeflow"]["enabled"] = False
    config_path = tmp_path / "routing.yaml"
    _write_yaml(config_path, routing)

    config = RoutingConfig(config_path=config_path)
    config.load()
    generated = config.generate_litellm_config("test-master-key")
    names = {entry["model_name"] for entry in generated["model_list"]}

    assert {"kimi-k3-ci", "fable-5-ci"} <= names
    assert not {
        "kimi-k3-or",
        "fable-5-or",
        "kimi-k3-direct",
        "fable-5-direct",
    } & names


def test_catalog_sync_dry_run_is_side_effect_free_and_preserves_user_extras(
    tmp_path, monkeypatch
):
    template, config_path = _make_config(tmp_path, monkeypatch)
    current = deepcopy(template)
    current["providers"][0]["label"] = "stale"
    current["providers"].append(
        {"name": "user-provider", "api_key_env": "USER_API_KEY"}
    )
    current["models"].append(
        {
            "name": "user-model",
            "provider": "user-provider",
            "model_id": "openai/user-model",
        }
    )
    _write_yaml(config_path, current)
    before = config_path.read_bytes()

    config = RoutingConfig(config_path=config_path)
    result = config.sync_catalog_contract(apply=False)

    assert result["changed"] is False
    assert result["audit"]["stale"] is True
    assert "providers" in result["audit"]["changed_sections"]
    assert config_path.read_bytes() == before
    assert not list(tmp_path.glob("routing.yaml.bak.*"))


def test_catalog_sync_apply_is_backup_first_and_preserves_user_extras(
    tmp_path, monkeypatch
):
    template, config_path = _make_config(tmp_path, monkeypatch)
    current = deepcopy(template)
    current["providers"][0]["label"] = "stale"
    current["providers"].append(
        {"name": "user-provider", "api_key_env": "USER_API_KEY"}
    )
    current["models"].append(
        {
            "name": "user-model",
            "provider": "user-provider",
            "model_id": "openai/user-model",
        }
    )
    _write_yaml(config_path, current)
    before = config_path.read_bytes()

    config = RoutingConfig(config_path=config_path)
    result = config.sync_catalog_contract(apply=True)
    repaired = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    backup_path = Path(result["backup_path"])

    assert result["changed"] is True
    assert result["audit"]["stale"] is False
    assert backup_path.read_bytes() == before
    assert repaired["providers"][0] == template["providers"][0]
    assert any(row["name"] == "user-provider" for row in repaired["providers"])
    assert any(row["name"] == "user-model" for row in repaired["models"])


def test_routing_sync_catalog_cli_defaults_to_dry_run(tmp_path, monkeypatch):
    template, config_path = _make_config(tmp_path, monkeypatch)
    current = deepcopy(template)
    current["providers"][0]["label"] = "stale"
    _write_yaml(config_path, current)
    before = config_path.read_bytes()
    config = RoutingConfig(config_path=config_path)
    fake_manager = SimpleNamespace(routing_config=config)
    monkeypatch.setattr(
        routing_cli.LaunchdServiceManager,
        "get_instance",
        staticmethod(lambda: fake_manager),
    )

    result = CliRunner().invoke(routing_cli.routing, ["sync-catalog"])

    assert result.exit_code == 0
    assert "Dry run only" in result.output
    assert "providers" in result.output
    assert config_path.read_bytes() == before
