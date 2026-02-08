from services.adhd_engine.core import engine as engine_module


def test_resolve_task_orchestrator_url_prefers_settings(monkeypatch):
    monkeypatch.setattr(
        type(engine_module.settings),
        "task_orchestrator_url",
        "http://configured-host:8123",
        raising=False,
    )
    monkeypatch.setenv("TASK_ORCHESTRATOR_URL", "http://env-host:9000")

    assert engine_module._resolve_task_orchestrator_url() == "http://configured-host:8123"


def test_resolve_task_orchestrator_url_uses_env_when_setting_missing(monkeypatch):
    monkeypatch.delattr(type(engine_module.settings), "task_orchestrator_url", raising=False)
    monkeypatch.setenv("TASK_ORCHESTRATOR_URL", "http://env-only:9010")

    assert engine_module._resolve_task_orchestrator_url() == "http://env-only:9010"


def test_resolve_task_orchestrator_url_uses_default_when_unset(monkeypatch):
    monkeypatch.delattr(type(engine_module.settings), "task_orchestrator_url", raising=False)
    monkeypatch.delenv("TASK_ORCHESTRATOR_URL", raising=False)

    assert engine_module._resolve_task_orchestrator_url() == "http://task-orchestrator:8000"
