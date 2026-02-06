from datetime import datetime, timedelta
from pathlib import Path

import pytest

import dopemux.auto_detection_service as auto_detection_service
from dopemux.profile_detector import ProfileMatch


class _DummyConsole:
    def __init__(self):
        self.messages = []
        self.logger = self

    def info(self, message):
        self.messages.append(str(message))


class _DummyDetector:
    def __init__(self, *args, **kwargs):
        self._match = _make_match()

    def detect(self):
        return self._match


def _make_match(profile_name: str = "developer", confidence: float = 0.9) -> ProfileMatch:
    return ProfileMatch(
        profile_name=profile_name,
        confidence=confidence,
        total_score=confidence * 100.0,
        signal_scores={"git_branch": 30.0, "directory": 25.0},
        suggestion_level="auto" if confidence >= 0.85 else "prompt",
    )


@pytest.fixture(autouse=True)
def _patch_console(monkeypatch):
    fake_console = _DummyConsole()
    monkeypatch.setattr(auto_detection_service, "console", fake_console)
    monkeypatch.setattr(auto_detection_service, "ProfileDetector", _DummyDetector)
    return fake_console


def test_auto_detection_defaults_match_backlog_requirements():
    config = auto_detection_service.AutoDetectionConfig()
    assert config.check_interval_seconds == 300
    assert config.confidence_threshold == pytest.approx(0.85)
    assert config.debounce_minutes == 30
    assert config.quiet_hours_start == "22:00"
    assert config.quiet_hours_end == "08:00"


def test_should_suggest_enforces_threshold_debounce_quiet_hours_and_never_list(tmp_path: Path, monkeypatch):
    service = auto_detection_service.AutoDetectionService(workspace_root=tmp_path)
    monkeypatch.setattr(service.config, "is_quiet_hours", lambda: False)

    assert service.should_suggest("developer", 0.85) is True
    assert service.should_suggest("developer", 0.84) is False

    service.last_suggestion["developer"] = datetime.now() - timedelta(minutes=10)
    assert service.should_suggest("developer", 0.9) is False

    service.last_suggestion.clear()
    service.config.never_suggest.add("developer")
    assert service.should_suggest("developer", 0.9) is False

    service.config.never_suggest.clear()
    service.current_profile = "developer"
    assert service.should_suggest("developer", 0.9) is False

    service.current_profile = None
    monkeypatch.setattr(service.config, "is_quiet_hours", lambda: True)
    assert service.should_suggest("developer", 0.9) is False


def test_suggestion_acceptance_flow_supports_yes_no_and_never(tmp_path: Path, monkeypatch):
    service = auto_detection_service.AutoDetectionService(workspace_root=tmp_path)
    match = _make_match()

    monkeypatch.setattr("builtins.input", lambda _: "y")
    accepted = service.suggest_profile_switch("developer", match)
    assert accepted is True
    assert "developer" in service.last_suggestion

    monkeypatch.setattr("builtins.input", lambda _: "")
    accepted = service.suggest_profile_switch("developer", match)
    assert accepted is False

    saved_paths = []
    monkeypatch.setattr("builtins.input", lambda _: "never")
    monkeypatch.setattr(service.config, "save", lambda path: saved_paths.append(str(path)))
    accepted = service.suggest_profile_switch("developer", match)
    assert accepted is False
    assert "developer" in service.config.never_suggest
    assert saved_paths


def test_run_detection_cycle_returns_profile_when_accepted(tmp_path: Path, monkeypatch):
    service = auto_detection_service.AutoDetectionService(workspace_root=tmp_path)
    match = _make_match(profile_name="developer", confidence=0.91)

    monkeypatch.setattr(service.detector, "detect", lambda: match)
    monkeypatch.setattr(service, "should_suggest", lambda profile_name, confidence: True)
    monkeypatch.setattr(service, "suggest_profile_switch", lambda profile_name, m: True)

    selected = service.run_detection_cycle()
    assert selected == "developer"
    assert service.current_profile == "developer"


def test_create_default_settings_writes_expected_values(tmp_path: Path):
    output = tmp_path / ".dopemux" / "profile-settings.yaml"
    auto_detection_service.create_default_settings(output)
    text = output.read_text(encoding="utf-8")

    assert "check_interval_seconds: 300" in text
    assert "confidence_threshold: 0.85" in text
    assert "debounce_minutes: 30" in text
