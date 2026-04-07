from dopemux.claude.native_hooks import handle_event
from dopemux.workflow import WorkflowKernel, WorkflowStatus


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
