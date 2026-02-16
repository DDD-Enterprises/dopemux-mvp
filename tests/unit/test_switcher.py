from pathlib import Path
from unittest.mock import MagicMock
import pytest

from dopemux.switcher import ProfileSwitcher, SwitchResult


class MockProfile:
    def __init__(self, name):
        self.name = name


class MockProfileManager:
    def __init__(self, active_profile=None, profiles=None):
        self.active_profile = active_profile
        self.profiles = profiles or {}
        self.set_active_calls = []

    def get_active_profile(self, workspace):
        return self.active_profile

    def get_profile(self, name):
        return self.profiles.get(name)

    def set_active_profile(self, workspace, profile_name):
        self.set_active_calls.append((workspace, profile_name))
        if profile_name == "raise_error":
            raise Exception("Failed to set active profile")
        self.active_profile = profile_name


class MockSessionManager:
    def __init__(self):
        self.save_calls = []
        self.restore_calls = 0

    def save_session(self, reason):
        self.save_calls.append(reason)

    def restore_session(self):
        self.restore_calls += 1


class MockClaudeManager:
    def __init__(self, apply_success=True):
        self.apply_success = apply_success
        self.apply_calls = []
        self.rollback_calls = []

    def apply_profile(self, profile):
        self.apply_calls.append(profile)
        if not self.apply_success:
            return False, None
        return True, Path("/tmp/backup")

    def rollback(self, backup_path):
        self.rollback_calls.append(backup_path)


@pytest.fixture
def workspace(tmp_path):
    return tmp_path


def test_switch_success(workspace):
    profile_name = "dev"
    profile = MockProfile(profile_name)
    pm = MockProfileManager(active_profile="base", profiles={profile_name: profile})
    sm = MockSessionManager()
    cm = MockClaudeManager()

    switcher = ProfileSwitcher(workspace, pm, sm, cm)
    result = switcher.switch(profile_name)

    assert result.success is True
    assert result.profile_name == profile_name
    assert result.previous_profile == "base"
    assert pm.active_profile == profile_name
    assert sm.save_calls == [f"profile switch base -> {profile_name}"]
    assert sm.restore_calls == 1
    assert cm.apply_calls == [profile]
    assert cm.rollback_calls == []


def test_switch_profile_not_found(workspace):
    pm = MockProfileManager(active_profile="base")
    sm = MockSessionManager()
    cm = MockClaudeManager()

    switcher = ProfileSwitcher(workspace, pm, sm, cm)
    result = switcher.switch("nonexistent")

    assert result.success is False
    assert result.error == "profile not found: nonexistent"
    assert result.previous_profile == "base"
    assert sm.save_calls == []


def test_switch_apply_failed(workspace):
    profile_name = "dev"
    profile = MockProfile(profile_name)
    pm = MockProfileManager(active_profile="base", profiles={profile_name: profile})
    sm = MockSessionManager()
    cm = MockClaudeManager(apply_success=False)

    switcher = ProfileSwitcher(workspace, pm, sm, cm)
    result = switcher.switch(profile_name)

    assert result.success is False
    assert result.error == "apply failed"
    assert pm.active_profile == "base"
    assert sm.save_calls == [f"profile switch base -> {profile_name}"]
    assert sm.restore_calls == 0


def test_switch_set_active_failed_triggers_rollback(workspace):
    profile_name = "raise_error"
    profile = MockProfile(profile_name)
    pm = MockProfileManager(active_profile="base", profiles={profile_name: profile})
    sm = MockSessionManager()
    cm = MockClaudeManager()

    switcher = ProfileSwitcher(workspace, pm, sm, cm)
    result = switcher.switch(profile_name)

    assert result.success is False
    assert "Failed to set active profile" in result.error
    assert cm.rollback_calls == [Path("/tmp/backup")]
    assert sm.restore_calls == 0
