"""Tests for Dopemux mobile notification hooks."""

import pytest

from dopemux.mobile import hooks


class DummyCtx:
    def __init__(self, config_manager):
        self.obj = {"config_manager": config_manager}


def test_mobile_task_notification_success(monkeypatch):
    calls = []
    monkeypatch.setattr(hooks, "notify_mobile_event", lambda cfg, msg: calls.append(msg))

    ctx = DummyCtx(config_manager=hooks.ConfigManager())
    with hooks.mobile_task_notification(ctx, "Test Run", success_message="✅ done", failure_message="❌ fail"):
        pass

    assert calls == ["✅ done"]


def test_mobile_task_notification_failure(monkeypatch):
    calls = []
    monkeypatch.setattr(hooks, "notify_mobile_event", lambda cfg, msg: calls.append(msg))

    ctx = DummyCtx(config_manager=hooks.ConfigManager())

    with pytest.raises(RuntimeError):
        with hooks.mobile_task_notification(ctx, "Build", success_message="✅ ok", failure_message="❌ nope"):
            raise RuntimeError("boom")

    assert calls == ["❌ nope"]
