import importlib
import stat
import uuid
from types import SimpleNamespace

import pytest


def test_operator_identity_is_random_persisted_uuid_with_private_permissions(tmp_path, monkeypatch):
    from services.adhd_engine.operator_identity import resolve_operator_user_id

    identity_path = tmp_path / ".dopemux" / "operator_id"
    monkeypatch.delenv("DOPEMUX_ADHD_USER_ID", raising=False)
    monkeypatch.delenv("ADHD_OPERATOR_USER_ID", raising=False)

    first = resolve_operator_user_id(identity_path=identity_path)
    second = resolve_operator_user_id(identity_path=identity_path)

    assert first == second
    assert uuid.UUID(first).version == 4
    assert identity_path.read_text(encoding="utf-8").strip() == first
    assert stat.S_IMODE(identity_path.stat().st_mode) == 0o600


def test_operator_identity_env_override_is_content_free_and_does_not_write_file(tmp_path, monkeypatch):
    from services.adhd_engine.operator_identity import resolve_operator_user_id

    identity_path = tmp_path / ".dopemux" / "operator_id"
    monkeypatch.setenv("DOPEMUX_ADHD_USER_ID", "operator-local-001")

    assert resolve_operator_user_id(identity_path=identity_path) == "operator-local-001"
    assert not identity_path.exists()


def test_operator_identity_rejects_pathlike_or_empty_overrides(tmp_path, monkeypatch):
    from services.adhd_engine.operator_identity import resolve_operator_user_id

    identity_path = tmp_path / ".dopemux" / "operator_id"
    monkeypatch.setenv("DOPEMUX_ADHD_USER_ID", "/Users/hue/code/dopemux-mvp")

    with pytest.raises(ValueError, match="content-free"):
        resolve_operator_user_id(identity_path=identity_path)

    monkeypatch.setenv("DOPEMUX_ADHD_USER_ID", "   ")
    with pytest.raises(ValueError, match="empty"):
        resolve_operator_user_id(identity_path=identity_path)


def test_adhd_settings_exposes_operator_identity_path(monkeypatch, tmp_path):
    managed_keys = ["ADHD_OPERATOR_ID_PATH", "DOPEMUX_ADHD_USER_ID", "ADHD_OPERATOR_USER_ID"]
    for key in managed_keys:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ADHD_OPERATOR_ID_PATH", str(tmp_path / "operator-id"))

    config = importlib.import_module("services.adhd_engine.config")
    config = importlib.reload(config)

    assert config.settings.operator_id_path == str(tmp_path / "operator-id")


@pytest.mark.asyncio
async def test_core_engine_threads_operator_identity_to_domain_components_and_listener(monkeypatch):
    from services.adhd_engine.core import engine as engine_module

    started = {}

    class FakeAttentionCalibrator:
        def __init__(self, user_id, storage_path=".calibration_data"):
            self.user_id = user_id
            self.storage_path = storage_path

    class FakeSocialBatteryMonitor:
        def __init__(self, user_id, bridge_client=None):
            self.user_id = user_id
            self.bridge_client = bridge_client

    class FakeNoArg:
        def __init__(self, *args, **kwargs):
            pass

    class FakeVoiceAssistant:
        def __init__(self, adhd_engine):
            self.adhd_engine = adhd_engine

    class FakeCoordinator:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeEventEmitter:
        def __init__(self, redis_url):
            self.redis_url = redis_url

    class FakeEventListener:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        async def start(self, user_id):
            started["user_id"] = user_id

    monkeypatch.setattr(engine_module, "resolve_operator_user_id", lambda: "operator-local-001")
    monkeypatch.setattr(engine_module, "AttentionCalibrator", FakeAttentionCalibrator)
    monkeypatch.setattr(engine_module, "SocialBatteryMonitor", FakeSocialBatteryMonitor)
    monkeypatch.setattr(engine_module, "HyperfocusGuard", FakeNoArg)
    monkeypatch.setattr(engine_module, "ProcrastinationDetector", FakeNoArg)
    monkeypatch.setattr(engine_module, "OverwhelmDetector", FakeNoArg)
    monkeypatch.setattr(engine_module, "TaskDecompositionAssistant", FakeNoArg)
    monkeypatch.setattr(engine_module, "VoiceAssistant", FakeVoiceAssistant)
    monkeypatch.setattr(engine_module, "DecompositionCoordinator", FakeCoordinator)
    monkeypatch.setattr(engine_module, "ADHDEventEmitter", FakeEventEmitter)
    monkeypatch.setattr(engine_module, "ADHDEventListener", FakeEventListener)

    engine = engine_module.ADHDAccommodationEngine()
    engine._initialize_domain_components()
    await engine._start_event_listener()

    assert engine.operator_user_id == "operator-local-001"
    assert engine.attention_calibrator.user_id == "operator-local-001"
    assert engine.social_battery_monitor.user_id == "operator-local-001"
    assert started["user_id"] == "operator-local-001"


@pytest.mark.asyncio
async def test_state_route_defaults_to_resolved_operator_identity(monkeypatch):
    from services.adhd_engine.api import routes
    from services.adhd_engine.core.models import AttentionState, EnergyLevel

    monkeypatch.setattr(routes, "resolve_operator_user_id", lambda: "operator-local-001")
    engine = SimpleNamespace(
        current_energy_levels={"operator-local-001": EnergyLevel.HIGH},
        current_attention_states={"operator-local-001": AttentionState.SCATTERED},
    )

    state = await routes.get_adhd_state(engine=engine)

    assert state["user_id"] == "operator-local-001"
    assert state["energy"] == "high"
    assert state["attention"] == "scattered"
