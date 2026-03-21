from pathlib import Path

from dopemux.claude.native_hooks import NativeHookAdapter
from dopemux.workflow import WorkflowKernel, WorkflowPhase


def _setup_workflow(monkeypatch, tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(workspace))
    monkeypatch.setenv("DOPEMUX_MAIN_REPO", str(workspace))
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "A")
    monkeypatch.setattr(
        WorkflowKernel,
        "probe_pm_authority",
        lambda self: {"authority": "local-mirror", "reachable": False, "url": "http://localhost:8000"},
    )
    kernel = WorkflowKernel(workspace)
    state = kernel.init_workflow(prompt="Exercise native hooks")
    return workspace, kernel, state


def test_pre_tool_use_denies_when_iteration_budget_is_spent(monkeypatch, tmp_path: Path):
    workspace, kernel, state = _setup_workflow(monkeypatch, tmp_path)
    state.max_iterations = 1
    state.iteration = 2
    kernel.save(state)

    adapter = NativeHookAdapter(workspace)
    exit_code, payload = adapter.handle_event(
        {"hook_event_name": "PreToolUse", "tool_name": "write_file"}
    )

    assert exit_code == 0
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "iteration limit reached" in payload["systemMessage"].lower()


def test_stop_blocks_without_checkpoint_and_allows_with_checkpoint(monkeypatch, tmp_path: Path):
    workspace, kernel, state = _setup_workflow(monkeypatch, tmp_path)
    state.phase = WorkflowPhase.RESEARCH
    kernel.save(state)

    adapter = NativeHookAdapter(workspace)

    _, blocked = adapter.handle_event(
        {"hook_event_name": "Stop", "response": "Still collecting evidence."}
    )
    assert blocked["decision"] == "block"

    _, allowed = adapter.handle_event(
        {
            "hook_event_name": "Stop",
            "response": (
                '<workflow-checkpoint phase="research" status="complete" '
                'task="task-001" summary="Research captured" />'
            ),
        }
    )
    refreshed = kernel.load(state.workflow_id)

    assert "decision" not in allowed
    assert refreshed.checkpoints[-1].phase == WorkflowPhase.RESEARCH
