from pathlib import Path
from types import SimpleNamespace

import dopemux.analytics as analytics
from dopemux import profile_analytics
from dopemux.claude_manager import ClaudeProfileManager
from dopemux.migration import (
    create_dry_run_update_config,
    format_migration_summary,
    inspect_migration_plan,
    migration_required,
)
from dopemux.profile_detector import DetectionContext, ProfileMatch
from dopemux.scorer import score_all_profiles, score_best_profile
from dopemux.session_manager import ProfileSessionManager
from dopemux.signal_collectors import collect_detection_signals
from dopemux.statusline_integration import render_profile_statusline
from dopemux.suggestion_engine import evaluate_suggestion, suggest_if_needed
from dopemux.switcher import ProfileSwitcher


def _sample_match(profile_name: str = "developer", confidence: float = 0.91) -> ProfileMatch:
    return ProfileMatch(
        profile_name=profile_name,
        confidence=confidence,
        total_score=confidence * 100.0,
        signal_scores={"git_branch": 30.0, "directory": 25.0},
        suggestion_level="auto" if confidence >= 0.85 else "prompt",
    )


def test_analytics_module_reexports_profile_analytics_symbols():
    assert analytics.ProfileAnalytics is profile_analytics.ProfileAnalytics
    assert analytics.generate_optimization_suggestions is profile_analytics.generate_optimization_suggestions
    assert analytics.get_stats_sync is profile_analytics.get_stats_sync


def test_collect_detection_signals_returns_context_and_scores(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    base_context = DetectionContext(current_dir=tmp_path, git_branch="feature/test")

    class DummyDetector:
        def _gather_context(self):
            return base_context

        def detect(self, context=None):
            assert context is base_context
            assert context.current_dir == workspace.resolve()
            return _sample_match()

    snapshot = collect_detection_signals(detector=DummyDetector(), workspace=workspace)
    assert snapshot.context is base_context
    assert snapshot.signal_scores["git_branch"] == 30.0


def test_scorer_facades_delegate_to_detector():
    match = _sample_match()

    class DummyDetector:
        def __init__(self):
            self.detect_called = False
            self.get_all_called = False

        def detect(self, context=None):
            self.detect_called = True
            return match

        def get_all_scores(self, context=None):
            self.get_all_called = True
            return {"developer": match}

    detector = DummyDetector()
    assert score_best_profile(detector=detector).profile_name == "developer"
    assert detector.detect_called is True
    assert score_all_profiles(detector=detector)["developer"].confidence == 0.91
    assert detector.get_all_called is True


def test_profile_session_manager_save_and_restore(tmp_path, monkeypatch):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    (workspace / ".dopemux").mkdir()

    calls = {"saved": None, "restored": False}

    class DummyContextManager:
        def __init__(self, path):
            assert path == workspace.resolve()

        def save_context(self, message, force):
            calls["saved"] = (message, force)
            return "ctx-123"

        def restore_latest(self):
            calls["restored"] = True
            return {"session_id": "ctx-123"}

    import dopemux.adhd as adhd_module

    monkeypatch.setattr(adhd_module, "ContextManager", DummyContextManager)

    manager = ProfileSessionManager(workspace=workspace)
    assert manager.save_session("switch reason") == "ctx-123"
    assert manager.restore_session() == {"session_id": "ctx-123"}
    assert calls["saved"] == ("switch reason", True)
    assert calls["restored"] is True


def test_profile_session_manager_no_dopemux_dir_returns_none(tmp_path):
    workspace = tmp_path / "empty"
    workspace.mkdir()
    manager = ProfileSessionManager(workspace=workspace)
    assert manager.save_session("x") is None
    assert manager.restore_session() is None


def test_claude_profile_manager_apply_and_rollback():
    calls = {"rollback": None}

    class DummyConfig:
        def apply_profile(self, profile, create_backup, dry_run, return_backup_path):
            assert profile.name == "developer"
            assert create_backup is True
            assert dry_run is False
            assert return_backup_path is True
            return True, Path("/tmp/backup.json")

        def rollback_to_backup(self, backup_path):
            calls["rollback"] = backup_path

    manager = ClaudeProfileManager(config=DummyConfig())
    applied, backup_path = manager.apply_profile(SimpleNamespace(name="developer"))
    assert applied is True
    assert backup_path == Path("/tmp/backup.json")
    assert manager.rollback(backup_path) is True
    assert calls["rollback"] == Path("/tmp/backup.json")
    assert manager.rollback(None) is False


def test_profile_switcher_success_path(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()

    class DummyProfileManager:
        def __init__(self):
            self.set_calls = []

        def get_active_profile(self, path):
            assert path == workspace.resolve()
            return "full"

        def get_profile(self, name):
            if name == "developer":
                return SimpleNamespace(name="developer")
            return None

        def set_active_profile(self, path, profile_name):
            self.set_calls.append((path, profile_name))

    class DummySessionManager:
        def save_session(self, reason):
            assert "full -> developer" in reason
            return "ctx-1"

        def restore_session(self):
            return {"ok": True}

    class DummyClaudeManager:
        def apply_profile(self, profile):
            assert profile.name == "developer"
            return True, Path("/tmp/backup.json")

        def rollback(self, backup_path):
            raise AssertionError("rollback should not be called")

    profile_manager = DummyProfileManager()
    switcher = ProfileSwitcher(
        workspace=workspace,
        profile_manager=profile_manager,
        session_manager=DummySessionManager(),
        claude_manager=DummyClaudeManager(),
    )

    result = switcher.switch("developer")
    assert result.success is True
    assert result.previous_profile == "full"
    assert result.profile_name == "developer"
    assert "set_active_profile" in result.timings
    assert profile_manager.set_calls[0][1] == "developer"


def test_profile_switcher_rolls_back_on_failure(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()
    rollback_calls = []

    class DummyProfileManager:
        def get_active_profile(self, path):
            return "full"

        def get_profile(self, name):
            return SimpleNamespace(name=name)

        def set_active_profile(self, path, profile_name):
            raise RuntimeError("write failed")

    class DummySessionManager:
        def save_session(self, reason):
            return "ctx-1"

        def restore_session(self):
            return {"ok": True}

    class DummyClaudeManager:
        def apply_profile(self, profile):
            return True, Path("/tmp/backup.json")

        def rollback(self, backup_path):
            rollback_calls.append(backup_path)
            return True

    switcher = ProfileSwitcher(
        workspace=workspace,
        profile_manager=DummyProfileManager(),
        session_manager=DummySessionManager(),
        claude_manager=DummyClaudeManager(),
    )

    result = switcher.switch("developer")
    assert result.success is False
    assert "write failed" in (result.error or "")
    assert rollback_calls == [Path("/tmp/backup.json")]


def test_profile_switcher_returns_error_when_profile_missing(tmp_path):
    workspace = tmp_path / "repo"
    workspace.mkdir()

    class DummyProfileManager:
        def get_active_profile(self, path):
            return "full"

        def get_profile(self, name):
            return None

    switcher = ProfileSwitcher(
        workspace=workspace,
        profile_manager=DummyProfileManager(),
        session_manager=SimpleNamespace(save_session=lambda reason: None, restore_session=lambda: None),
        claude_manager=SimpleNamespace(apply_profile=lambda profile: (True, None), rollback=lambda backup: True),
    )
    result = switcher.switch("missing")
    assert result.success is False
    assert result.error == "profile not found: missing"


def test_render_profile_statusline_formats_match():
    match = _sample_match(profile_name="developer", confidence=0.88)
    text = render_profile_statusline(active_profile="full", pending_match=match)
    assert "profile:full" in text
    assert "suggest:developer(88%)" in text
    assert "mode:auto" in text
    assert render_profile_statusline(active_profile=None) == "profile:none"


def test_suggestion_engine_uses_service_policy(monkeypatch):
    match = _sample_match(confidence=0.92)

    class DummyDetector:
        def detect(self, context=None):
            return match

    service = SimpleNamespace(
        config=SimpleNamespace(
            enabled=True,
            confidence_threshold=0.85,
            never_suggest=set(),
            is_quiet_hours=lambda: False,
        ),
        current_profile="full",
        should_suggest=lambda profile_name, confidence: True,
        suggest_profile_switch=lambda profile_name, match: True,
    )

    evaluation = evaluate_suggestion(detector=DummyDetector(), service=service, current_profile="full")
    assert evaluation.should_prompt is True
    assert evaluation.reason == "service_policy_allows"
    accepted = suggest_if_needed(service=service, detector=DummyDetector(), current_profile="full")
    assert accepted == "developer"
    assert service.current_profile == "developer"


def test_suggestion_engine_returns_reason_when_blocked():
    match = _sample_match(confidence=0.70)

    class DummyDetector:
        def detect(self, context=None):
            return match

    service = SimpleNamespace(
        config=SimpleNamespace(
            enabled=False,
            confidence_threshold=0.85,
            never_suggest=set(),
            is_quiet_hours=lambda: False,
        ),
        current_profile=None,
        should_suggest=lambda profile_name, confidence: False,
        suggest_profile_switch=lambda profile_name, match: False,
    )

    evaluation = evaluate_suggestion(detector=DummyDetector(), service=service)
    assert evaluation.should_prompt is False
    assert evaluation.reason == "service_disabled"
    assert suggest_if_needed(service=service, detector=DummyDetector()) is None


def test_migration_helpers_inspect_and_format_plan():
    dummy_info = SimpleNamespace(
        current="1.2.0",
        target="1.3.0",
        migration_path=["1.2.0", "1.3.0"],
        requires_migration=True,
        breaking_changes=False,
    )
    dummy_manager = SimpleNamespace(check_for_updates=lambda: dummy_info)
    plan = inspect_migration_plan(manager=dummy_manager)
    assert plan.current == "1.2.0"
    assert plan.target == "1.3.0"
    assert plan.path == ["1.2.0", "1.3.0"]
    assert migration_required(manager=dummy_manager) is True
    summary = format_migration_summary(plan)
    assert "current=1.2.0" in summary
    assert "migration=required" in summary


def test_create_dry_run_update_config_sets_expected_defaults():
    config = create_dry_run_update_config(timeout_minutes=45)
    assert config.dry_run is True
    assert config.timeout_minutes == 45

