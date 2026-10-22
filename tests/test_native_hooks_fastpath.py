"""Empty-workflow-store fast path: skip the heavy workflow import, keep behavior.

The hook is registered with a catch-all matcher, so every tool call pays its
cost. When the workflow store is provably empty, ``_active_state`` must return
None without importing ``dopemux.workflow`` -- while heartbeats, red-lane
denies, and the full path for non-empty stores stay exactly as before.
"""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest

from dopemux.claude import native_hooks
from dopemux.claude.native_hooks import NativeHookAdapter

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git required")

RED_LANE_EDIT = {
    "hook_event_name": "PreToolUse",
    "tool_name": "Edit",
    "tool_input": {"file_path": ".github/workflows/ci-complete.yml"},
}


class FakeRedis:
    def __init__(self):
        self.calls = []

    def xadd(self, stream, fields, **_kwargs):
        self.calls.append((stream, fields))
        return "1-0"

    def close(self):
        pass


@pytest.fixture
def repo(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for name in ("DOPEMUX_WORKSPACE_ROOT", "DOPEMUX_MAIN_REPO"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "main")
    return tmp_path


@pytest.fixture
def loader_calls(monkeypatch):
    calls = []

    def _spy():
        calls.append(1)
        return False

    monkeypatch.setattr(native_hooks, "_ensure_workflow", _spy)
    return calls


@pytest.fixture
def fake_redis(monkeypatch):
    fake = FakeRedis()
    monkeypatch.setenv("DOPEMUX_NATIVE_HOOK_EVENTS_ENABLED", "1")
    monkeypatch.setattr(native_hooks, "_open_activity_redis_client", lambda: fake)
    monkeypatch.setattr(native_hooks, "should_emit_heartbeat", lambda *a, **k: True)
    return fake


def test_empty_store_skips_workflow_import_but_still_emits_heartbeats(repo, loader_calls, fake_redis):
    adapter = NativeHookAdapter(repo)
    for event, tool in (("PreToolUse", "Read"), ("PostToolUse", "Bash")):
        code, payload = adapter.handle_event(
            {"hook_event_name": event, "tool_name": tool, "tool_input": {}, "session_id": "s"}
        )
        assert (code, payload) == (0, {})

    assert loader_calls == []
    events = [json.loads(fields["data"]) for _stream, fields in fake_redis.calls]
    assert [(e["hook_event_name"], e["status"], e["tool_name"]) for e in events] == [
        ("PreToolUse", "attempt", "Read"),
        ("PostToolUse", "success", "Bash"),
    ]
    assert (repo / ".dopemux" / "workflows").is_dir()  # same mkdir side effect as the kernel


def test_empty_store_still_routes_red_lane_edit_through_surface_guard(repo, loader_calls, monkeypatch):
    monkeypatch.setenv("DOPEMUX_NATIVE_HOOK_EVENTS_ENABLED", "0")
    code, payload = NativeHookAdapter(repo).handle_event(dict(RED_LANE_EDIT, session_id="s"))
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert loader_calls == []


def test_workspace_root_override_takes_full_path(repo, loader_calls, monkeypatch):
    monkeypatch.setenv("DOPEMUX_NATIVE_HOOK_EVENTS_ENABLED", "0")
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(repo))
    code, payload = NativeHookAdapter(repo).handle_event(
        {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {}}
    )
    assert (code, payload) == (0, {})
    assert loader_calls == [1]


def test_non_empty_store_takes_full_path_and_enforces_limits(repo, monkeypatch):
    monkeypatch.setenv("DOPEMUX_NATIVE_HOOK_EVENTS_ENABLED", "0")
    from dopemux.workflow import WorkflowKernel

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(repo))
    WorkflowKernel(repo).create_or_resume(
        workflow_id="wf-limit",
        instance_id="main",
        mode="internal",
        max_iterations=0,
        max_minutes=30,
        completion_token="DONE",
    )
    monkeypatch.delenv("DOPEMUX_WORKSPACE_ROOT")

    adapter = NativeHookAdapter(repo)
    assert native_hooks._workflow_store_known_empty(repo) is False
    code, payload = adapter.handle_event(
        {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {}}
    )
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "iteration limit" in payload["hookSpecificOutput"]["permissionDecisionReason"]


def test_not_a_git_repo_defers_to_full_path(tmp_path, monkeypatch):
    for name in ("DOPEMUX_WORKSPACE_ROOT", "DOPEMUX_MAIN_REPO"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    assert native_hooks._workflow_store_known_empty(tmp_path) is False
