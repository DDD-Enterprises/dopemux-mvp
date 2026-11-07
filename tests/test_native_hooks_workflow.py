import json

import pytest

from dopemux.claude import native_hooks
from dopemux.claude.native_hooks import handle_event
from dopemux.workflow import WorkflowKernel, WorkflowStatus


@pytest.fixture(autouse=True)
def _reaping_off_by_default(monkeypatch):
    """Stop/SessionEnd reap sidecars; these tests must never reach docker or a real registry."""
    monkeypatch.setenv("DOPEMUX_MCP_REAP", "0")


class FakeRedisClient:
    def __init__(self):
        self.xadd_calls = []
        self.closed = False

    def xadd(self, stream, fields, maxlen=None, approximate=True):
        self.xadd_calls.append(
            {
                "stream": stream,
                "fields": fields,
                "maxlen": maxlen,
                "approximate": approximate,
            }
        )
        return "1-0"

    def close(self):
        self.closed = True


class FailingRedisClient:
    def xadd(self, *_args, **_kwargs):
        raise RuntimeError("redis unavailable")

    def close(self):
        return None


def test_session_start_returns_strict_response_shape(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    kernel = WorkflowKernel(tmp_path)
    kernel.create_or_resume(
        workflow_id="wf-hook",
        instance_id="main",
        mode="internal",
        max_iterations=5,
        max_minutes=30,
        completion_token="DONE",
    )

    # Wrap in event_data shape expected by handle_event wrapper
    response = handle_event(
        "SessionStart",
        {
            "cwd": str(tmp_path),
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
            "attention_state": "focused",
        },
    )

    assert "systemMessage" in response
    assert "hookSpecificOutput" in response
    assert "additionalContext" in response["hookSpecificOutput"]


def test_pre_tool_use_blocks_when_limit_is_exceeded(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    kernel = WorkflowKernel(tmp_path)
    kernel.create_or_resume(
        workflow_id="wf-limit",
        instance_id="main",
        mode="internal",
        max_iterations=0,
        max_minutes=30,
        completion_token="DONE",
    )

    response = handle_event(
        "PreToolUse",
        {
            "cwd": str(tmp_path),
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
            "tool_name": "Read",
        },
    )

    assert "hookSpecificOutput" in response
    assert response["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_stop_hook_requires_checkpoint_or_completion_token(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    kernel = WorkflowKernel(tmp_path)
    state = kernel.create_or_resume(
        workflow_id="wf-stop",
        instance_id="main",
        mode="internal",
        max_iterations=5,
        max_minutes=30,
        completion_token="DONE",
    )

    blocked = handle_event(
        "Stop",
        {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}},
    )
    assert "decision" in blocked
    assert blocked["decision"] == "block"

    state.record_checkpoint("brief", True, message="brief approved")
    kernel.save(state)

    allowed = handle_event(
        "Stop",
        {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}},
    )
    assert allowed.get("decision") != "block"


def test_native_hooks_emit_content_free_activity_events(tmp_path, monkeypatch):
    fake_redis = FakeRedisClient()
    monkeypatch.setattr(native_hooks, "_open_activity_redis_client", lambda: fake_redis, raising=False)

    handle_event(
        "UserPromptSubmit",
        {
            "cwd": str(tmp_path),
            "session_id": "session-secret",
            "prompt": "secret prompt text",
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
        },
    )
    handle_event(
        "PreToolUse",
        {
            "cwd": str(tmp_path),
            "session_id": "session-secret",
            "tool_name": "Read",
            "tool_input": {"file_path": "/private/path/secret.py"},
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
        },
    )
    handle_event(
        "PostToolUse",
        {
            "cwd": str(tmp_path),
            "session_id": "session-secret",
            "tool_name": "Write",
            "tool_response": {"content": "secret response"},
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
        },
    )
    handle_event(
        "PostToolUseFailure",
        {
            "cwd": str(tmp_path),
            "session_id": "session-secret",
            "tool_name": "Bash",
            "error": "secret failure",
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
        },
    )

    assert [call["stream"] for call in fake_redis.xadd_calls] == [
        "dopemux:events",
        "dopemux:events",
        "dopemux:events",
        "dopemux:events",
    ]

    event_data = [json.loads(call["fields"]["data"]) for call in fake_redis.xadd_calls]
    assert [event["hook_event_name"] for event in event_data] == [
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
    ]
    assert [event["status"] for event in event_data] == [
        "observed",
        "attempt",
        "success",
        "failure",
    ]
    assert event_data[1]["tool_name"] == "Read"
    assert fake_redis.closed is True

    serialized = json.dumps(fake_redis.xadd_calls, sort_keys=True)
    forbidden_fragments = [
        "secret prompt text",
        "tool_input",
        "file_path",
        "/private/path/secret.py",
        "tool_response",
        "secret response",
        "secret failure",
        str(tmp_path),
        "session-secret",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in serialized


def test_native_hook_activity_emit_failure_does_not_block_hook(tmp_path, monkeypatch):
    monkeypatch.setattr(
        native_hooks,
        "_open_activity_redis_client",
        lambda: FailingRedisClient(),
        raising=False,
    )

    response = handle_event(
        "PreToolUse",
        {
            "cwd": str(tmp_path),
            "tool_name": "Read",
            "tool_input": {"file_path": "/private/path/secret.py"},
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
        },
    )

    assert response.get("decision") != "block"


def test_post_tool_failure_emits_bounded_error_capture(tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(native_hooks, "_open_activity_redis_client", lambda: FailingRedisClient(), raising=False)
    monkeypatch.setattr(
        native_hooks,
        "try_emit_promotable_capture_event",
        lambda event_type, payload, **kwargs: captured.append((event_type, payload, kwargs)),
    )

    response = handle_event(
        "PostToolUseFailure",
        {
            "cwd": str(tmp_path),
            "session_id": "session-secret",
            "tool_name": "Bash",
            "error": "secret failure with private path /tmp/secret",
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
        },
    )

    assert response.get("decision") != "block"
    assert captured
    event_type, payload, kwargs = captured[0]
    assert event_type == "error.encountered"
    assert payload["message"] == "Claude native hook tool failure"
    assert payload["error_kind"] == "hook_tool_failure"
    assert payload["tool_name"] == "Bash"
    assert kwargs["source"] == "dopemux.native_hooks"
    assert kwargs["emit_event_bus"] is False
    assert kwargs["session_id"] is None

    serialized = json.dumps(captured, sort_keys=True, default=str)
    assert "secret failure" not in serialized
    assert "session-secret" not in serialized


def test_post_tool_failure_capture_exception_does_not_block_hook(tmp_path, monkeypatch):
    def fail_capture(*_args, **_kwargs):
        raise RuntimeError("capture offline")

    monkeypatch.setattr(native_hooks, "_open_activity_redis_client", lambda: FailingRedisClient(), raising=False)
    monkeypatch.setattr(native_hooks, "try_emit_promotable_capture_event", fail_capture)

    response = handle_event(
        "PostToolUseFailure",
        {
            "cwd": str(tmp_path),
            "tool_name": "Bash",
            "error": "secret failure",
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
        },
    )

    assert response.get("decision") != "block"


# --- reap wiring (Task 5, D8/P-09) ---------------------------------------------------


def _record_reap(monkeypatch):
    from dopemux.mcp import reap

    calls = []

    def recorder(**kwargs):
        calls.append(kwargs)
        return None

    monkeypatch.setattr(reap, "maybe_reap", recorder)
    return calls


def test_stop_hook_calls_maybe_reap_before_allow(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    calls = _record_reap(monkeypatch)

    # No active workflow: the early return must still be preceded by the reap.
    response = handle_event("Stop", {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}})

    assert calls == [{"deadline_s": 60}]  # bounded inside the Stop hook budget
    assert response.get("decision") != "block"


def test_stop_hook_reap_runs_before_a_block_decision_too(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    kernel = WorkflowKernel(tmp_path)
    kernel.create_or_resume(
        workflow_id="wf-reap",
        instance_id="main",
        mode="internal",
        max_iterations=5,
        max_minutes=30,
        completion_token="DONE",
    )
    calls = _record_reap(monkeypatch)

    blocked = handle_event("Stop", {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}})

    assert calls == [{"deadline_s": 60}]  # bounded inside the Stop hook budget
    assert blocked["decision"] == "block"


def test_session_end_calls_reap_unthrottled(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    calls = _record_reap(monkeypatch)

    handle_event("SessionEnd", {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}})

    # SessionEnd's hook budget is short: one candidate, docker bounds, a 45 s deadline
    assert calls == [
        {
            "throttle_s": 0,
            "max_candidates": 1,
            "deadline_s": 45,
            "stop_time_s": 3,
            "cmd_timeout_s": 10.0,
        }
    ]


def test_reap_failure_does_not_change_hook_decision(tmp_path, monkeypatch):
    from dopemux.mcp import reap

    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    kernel = WorkflowKernel(tmp_path)
    state = kernel.create_or_resume(
        workflow_id="wf-reap-fail",
        instance_id="main",
        mode="internal",
        max_iterations=5,
        max_minutes=30,
        completion_token="DONE",
    )

    def boom(**kwargs):
        raise RuntimeError("docker exploded")

    monkeypatch.setattr(reap, "maybe_reap", boom)
    payload = {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}}

    assert handle_event("Stop", payload)["decision"] == "block"
    assert "decision" not in handle_event("SessionEnd", payload)

    state.record_checkpoint("brief", True, message="brief approved")
    kernel.save(state)
    assert handle_event("Stop", payload).get("decision") != "block"


def test_settings_gives_session_end_a_60_second_timeout():
    from pathlib import Path

    settings = json.loads(
        (Path(__file__).resolve().parents[1] / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    handlers = [h for group in settings["hooks"]["SessionEnd"] for h in group["hooks"]]
    assert [h.get("timeout") for h in handlers] == [60]
    assert all(h["type"] == "command" for h in handlers)
