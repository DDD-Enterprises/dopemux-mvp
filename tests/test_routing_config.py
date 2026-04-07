from types import SimpleNamespace
from pathlib import Path

import yaml
from click.testing import CliRunner

import dopemux.routing_cli as routing_cli
from dopemux.routing_config import RoutingConfig


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
