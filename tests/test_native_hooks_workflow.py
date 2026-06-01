import json

from dopemux.claude import native_hooks
from dopemux.claude.native_hooks import handle_event
from dopemux.workflow import WorkflowKernel, WorkflowStatus


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
