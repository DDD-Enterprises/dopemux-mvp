"""Deny/block visibility, timezone-aware timestamps, import degradation (audit F-01/F-02/F-05).

Claude Code only shows hook stderr to the model on exit 2, and ignores stdout on
exit 2. Hooks must therefore deny via exit 0 plus structured stdout JSON
(PreToolUse ``permissionDecision: deny``; Stop ``decision: block``) and may echo
the reason to stderr as a belt-and-braces diagnostic.
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import warnings
from pathlib import Path

import pytest

from dopemux.claude import native_hooks
from dopemux.claude.native_hooks import EXIT_SUCCESS, NativeHookAdapter

_ROOT = Path(__file__).resolve().parents[1]
RED_LANE_EDIT = {
    "hook_event_name": "PreToolUse",
    "tool_name": "Edit",
    "tool_input": {"file_path": ".github/workflows/ci-complete.yml"},
}


@pytest.fixture(autouse=True)
def _quiet_activity(monkeypatch):
    monkeypatch.setenv("DOPEMUX_NATIVE_HOOK_EVENTS_ENABLED", "0")


def _run_main(monkeypatch, capsys, payload):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    with pytest.raises(SystemExit) as exc:
        native_hooks.main()
    captured = capsys.readouterr()
    return exc.value.code, captured.out, captured.err


def test_deny_tool_exits_zero_with_pretooluse_deny_json(tmp_path):
    adapter = NativeHookAdapter(tmp_path)
    code, payload = adapter._deny_tool("nope", "ctx")
    assert code == EXIT_SUCCESS
    assert payload["systemMessage"] == "nope"
    out = payload["hookSpecificOutput"]
    assert out["hookEventName"] == "PreToolUse"
    assert out["permissionDecision"] == "deny"
    assert out["permissionDecisionReason"] == "nope"
    assert out["additionalContext"] == "ctx"


def test_deny_tool_omits_additional_context_when_absent(tmp_path):
    _, payload = NativeHookAdapter(tmp_path)._deny_tool("nope")
    assert "additionalContext" not in payload["hookSpecificOutput"]


def test_block_stop_exits_zero_with_decision_block(tmp_path):
    code, payload = NativeHookAdapter(tmp_path)._block_stop("keep going", "ctx")
    assert code == EXIT_SUCCESS
    assert payload["decision"] == "block"
    assert "keep going" in payload["reason"]
    assert "ctx" in payload["reason"]


def test_main_red_lane_edit_denies_via_stdout_and_stderr(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    code, out, err = _run_main(monkeypatch, capsys, RED_LANE_EDIT)
    assert code == 0
    body = json.loads(out)
    assert body["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert body["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
    reason = body["hookSpecificOutput"]["permissionDecisionReason"]
    assert "ci-complete.yml" in reason
    assert body["systemMessage"] == reason
    assert "ci-complete.yml" in err


def test_main_allow_path_has_empty_stderr(monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    payload = dict(RED_LANE_EDIT, tool_input={"file_path": "docs/readme.md"})
    code, _out, err = _run_main(monkeypatch, capsys, payload)
    assert code == 0
    assert err == ""


def test_legacy_handle_event_still_reports_block_for_deny(tmp_path):
    response = native_hooks.handle_event(
        "PreToolUse", dict(RED_LANE_EDIT, cwd=str(tmp_path))
    )
    assert response["decision"] == "block"
    assert response["hookSpecificOutput"]["permissionDecision"] == "deny"


class _FakeRedis:
    def __init__(self):
        self.calls = []

    def xadd(self, stream, fields, **kwargs):
        self.calls.append(fields)

    def close(self):
        pass


def test_activity_timestamp_is_timezone_aware_z_and_warning_free(monkeypatch):
    fake = _FakeRedis()
    monkeypatch.setenv("DOPEMUX_NATIVE_HOOK_EVENTS_ENABLED", "1")
    monkeypatch.setattr(native_hooks, "_open_activity_redis_client", lambda: fake)
    monkeypatch.setattr(native_hooks, "should_emit_heartbeat", lambda *a, **k: True)
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        assert native_hooks._emit_activity_event(hook_event_name="PreToolUse", status="attempt")
    ts = fake.calls[0]["timestamp"]
    assert ts.endswith("Z") and "+00:00" not in ts
    from datetime import datetime

    assert datetime.fromisoformat(ts.replace("Z", "+00:00")).utcoffset().total_seconds() == 0


def test_hook_degrades_without_workflow_deps_and_still_denies(monkeypatch, tmp_path):
    """Missing pydantic (workflow import chain) must not disable red-lane denies."""
    for name in (
        "dopemux.workflow",
        "dopemux.workflow.service",
        "dopemux.memory.capture_client",
    ):
        monkeypatch.setitem(sys.modules, name, None)  # import -> ImportError
    path = Path(native_hooks.__file__)
    spec = importlib.util.spec_from_file_location("native_hooks_no_workflow", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # must not raise

    adapter = mod.NativeHookAdapter(tmp_path)
    code, payload = adapter.handle_event(dict(RED_LANE_EDIT, session_id="s"))
    assert code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"

    # Other events degrade to "no workflow state" rather than raising.
    for event in ("SessionStart", "UserPromptSubmit", "Stop", "PostToolUse", "SessionEnd"):
        code, _ = adapter.handle_event({"hook_event_name": event, "tool_name": "Read"})
        assert code == 0


def test_settings_native_hook_entries_have_timeout():
    settings = json.loads((_ROOT / ".claude" / "settings.json").read_text())
    seen = 0
    for groups in settings["hooks"].values():
        for group in groups:
            for hook in group["hooks"]:
                if "run_native_hooks.sh" in hook.get("command", ""):
                    seen += 1
                    assert hook.get("timeout") == 30
    assert seen >= 11
