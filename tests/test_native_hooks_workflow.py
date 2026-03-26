from dopemux.claude.native_hooks import handle_event
from dopemux.workflow import WorkflowStore


def test_session_start_returns_strict_response_shape(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    store = WorkflowStore(tmp_path)
    store.create_or_resume(
        workflow_id="wf-hook",
        instance_id="main",
        mode="internal",
        max_iterations=5,
        max_minutes=30,
        completion_token="DONE",
    )

    response = handle_event(
        "SessionStart",
        {
            "cwd": str(tmp_path),
            "env": {"DOPEMUX_INSTANCE_ID": "main"},
            "attention_state": "focused",
        },
    )

    assert set(response.keys()) == {"systemMessage", "additionalContext"}
    assert response["additionalContext"]["workflow"]["phase"] == "brief"
    assert response["additionalContext"]["decision"] == "continue"


def test_pre_tool_use_blocks_when_limit_is_exceeded(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    store = WorkflowStore(tmp_path)
    store.create_or_resume(
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

    assert response["additionalContext"]["decision"] == "block"
    assert "max_iterations" in response["additionalContext"]["violations"]


def test_stop_hook_requires_checkpoint_or_completion_token(tmp_path, monkeypatch):
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(tmp_path))
    store = WorkflowStore(tmp_path)
    state = store.create_or_resume(
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
    assert blocked["additionalContext"]["decision"] == "block"

    state.record_checkpoint("brief", True, message="brief approved")
    store.save(state)

    allowed = handle_event(
        "Stop",
        {"cwd": str(tmp_path), "env": {"DOPEMUX_INSTANCE_ID": "main"}},
    )
    assert allowed["additionalContext"]["decision"] == "continue"
