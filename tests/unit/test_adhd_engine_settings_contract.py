import importlib


def _reload_config(monkeypatch, env_updates=None):
    env_updates = env_updates or {}
    managed_keys = [
        "API_HOST",
        "HOST",
        "TASK_ORCHESTRATOR_URL",
        "ENERGY_MONITOR_INTERVAL",
        "ATTENTION_MONITOR_INTERVAL",
        "ATTENTION_CHECK_INTERVAL",
        "COGNITIVE_MONITOR_INTERVAL",
        "BREAK_MONITOR_INTERVAL",
        "HYPERFOCUS_MONITOR_INTERVAL",
    ]
    for key in managed_keys:
        monkeypatch.delenv(key, raising=False)
    for key, value in env_updates.items():
        monkeypatch.setenv(key, value)

    config = importlib.import_module("services.adhd_engine.config")
    return importlib.reload(config)


def test_adhd_settings_exposes_runtime_required_fields(monkeypatch):
    config = _reload_config(monkeypatch)
    settings = config.settings

    required_attrs = [
        "api_host",
        "api_port",
        "task_orchestrator_url",
        "energy_monitor_interval",
        "attention_monitor_interval",
        "cognitive_monitor_interval",
        "break_monitor_interval",
        "hyperfocus_monitor_interval",
    ]
    for attr in required_attrs:
        assert hasattr(settings, attr), f"Missing settings attribute: {attr}"


def test_adhd_settings_supports_attention_check_interval_alias(monkeypatch):
    config = _reload_config(monkeypatch, {"ATTENTION_CHECK_INTERVAL": "91"})
    assert config.settings.attention_monitor_interval == 91


def test_adhd_settings_api_host_falls_back_to_host(monkeypatch):
    config = _reload_config(monkeypatch, {"HOST": "127.0.0.1"})
    assert config.settings.api_host == "127.0.0.1"
