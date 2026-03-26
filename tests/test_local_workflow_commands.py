import json
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

import dopemux.commands.workflow_group_commands as workflow_commands
from dopemux.workflow import WorkflowKernel


class FakeOrchestrator:
    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root

    def build_worker_launch_spec(self, state):
        return SimpleNamespace(
            task_id=state.current_task_id,
            instance_id="B",
            branch_name="codex/workflow-demo-task-001",
            worktree_path=self.workspace_root / "worktrees" / "B",
            session_name="dopemux-main",
            window_name="workflow-task-001",
            command="dopemux start --role workflow-executor --no-recovery --prompt 'demo'",
        )


def test_workflow_group_round_trip(monkeypatch, tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    monkeypatch.chdir(workspace)
    monkeypatch.setenv("DOPEMUX_WORKSPACE_ROOT", str(workspace))
    monkeypatch.setenv("DOPEMUX_MAIN_REPO", str(workspace))
    monkeypatch.setenv("DOPEMUX_INSTANCE_ID", "A")
    monkeypatch.setattr(
        WorkflowKernel,
        "probe_pm_authority",
        lambda self: {"authority": "local-mirror", "reachable": False, "url": "http://localhost:8000"},
    )
    monkeypatch.setattr(workflow_commands, "WorkflowOrchestrator", FakeOrchestrator)

    runner = CliRunner()

    init_result = runner.invoke(
        workflow_commands.workflow_group,
        ["init", "Ship the internal workflow kit"],
    )
    assert init_result.exit_code == 0, init_result.output

    status_result = runner.invoke(
        workflow_commands.workflow_group,
        ["status", "--json-output"],
    )
    assert status_result.exit_code == 0, status_result.output
    status_payload = json.loads(status_result.output)
    assert status_payload["phase"] == "brief"
    assert status_payload["status"] == "active"

    inspect_result = runner.invoke(
        workflow_commands.workflow_group,
        ["inspect", "--json-output"],
    )
    assert inspect_result.exit_code == 0, inspect_result.output
    inspect_payload = json.loads(inspect_result.output)
    assert inspect_payload["launch_preview"]["instance_id"] == "B"

    cancel_result = runner.invoke(
        workflow_commands.workflow_group,
        ["cancel"],
    )
    assert cancel_result.exit_code == 0, cancel_result.output
