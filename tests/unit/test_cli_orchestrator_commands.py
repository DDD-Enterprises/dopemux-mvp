import ast
from pathlib import Path
from types import SimpleNamespace

from click.testing import CliRunner

from src.dopemux.cli import cli


class _Result(SimpleNamespace):
    def model_dump(self):
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_")
        }


def _queue_result(*, error=None, items=None, next_action=None):
    return _Result(
        canonical_backend="task-orchestrator",
        project_id="dopemux-mvp",
        provenance={
            "source": "task-orchestrator",
            "query_mode": "priority_queue",
            "project_id": "dopemux-mvp",
        },
        legality_result="available",
        queue_items=items or [],
        next_action=next_action,
        error=error,
    )


def _blockers_result(*, error=None, blockers=None):
    return _Result(
        canonical_backend="task-orchestrator",
        project_id="dopemux-mvp",
        provenance={
            "source": "task-orchestrator",
            "query_mode": "blockers",
            "project_id": "dopemux-mvp",
        },
        legality_result="available",
        active_blockers=blockers or [],
        error=error,
    )


def _workflow_result(*, error=None, state=None):
    return _Result(
        canonical_backend="task-orchestrator",
        project_id="dopemux-mvp",
        provenance={
            "source": "task-orchestrator",
            "query_mode": "workflow_state",
            "project_id": "dopemux-mvp",
        },
        legality_result="available",
        state=state or {},
        allowed_transitions=["start", "hold"],
        error=error,
    )


def test_orchestrator_group_is_registered():
    runner = CliRunner()

    result = runner.invoke(cli, ["orchestrator", "--help"])

    assert result.exit_code == 0, result.output
    assert "status" in result.output
    assert "daily" in result.output
    assert "queue" in result.output
    assert "blockers" in result.output


def test_orchestrator_queue_renders_top_three_more_count_and_next_token(monkeypatch):
    async def fake_queue(project_id: str):
        assert project_id == "dopemux-mvp"
        return _queue_result(
            items=[
                {"id": "TP-1", "title": "First"},
                {"id": "TP-2", "title": "Second"},
                {"id": "TP-3", "title": "Third"},
                {"id": "TP-4", "title": "Fourth"},
            ],
            next_action={"id": "TP-1", "title": "First"},
        )

    monkeypatch.setattr(
        "src.dopemux.commands.orchestrator_commands.pm_get_priority_queue",
        fake_queue,
    )

    result = CliRunner().invoke(cli, ["orchestrator", "queue"])

    assert result.exit_code == 0, result.output
    assert "Task Orchestrator Queue" in result.output
    assert "authority: task-orchestrator" in result.output
    assert "1. TP-1 First" in result.output
    assert "2. TP-2 Second" in result.output
    assert "3. TP-3 Third" in result.output
    assert "Fourth" not in result.output
    assert "more_count: 1" in result.output
    assert "next_token: TP-1" in result.output


def test_orchestrator_status_uses_workflow_state_read_helper(monkeypatch):
    async def fake_state(project_id: str):
        assert project_id == "custom-project"
        return _workflow_result(state={"status": "active", "phase": "work"})

    monkeypatch.setattr(
        "src.dopemux.commands.orchestrator_commands.pm_get_workflow_state",
        fake_state,
    )

    result = CliRunner().invoke(
        cli,
        ["orchestrator", "status", "--project-id", "custom-project"],
    )

    assert result.exit_code == 0, result.output
    assert "Task Orchestrator Status" in result.output
    assert "project: custom-project" in result.output
    assert "status: active" in result.output
    assert "phase: work" in result.output
    assert "allowed_transitions: start, hold" in result.output


def test_orchestrator_daily_surfaces_partial_failures(monkeypatch):
    async def fake_queue(project_id: str):
        return _queue_result(items=[{"id": "TP-1", "title": "Ready"}])

    async def fake_blockers(project_id: str):
        return _blockers_result(error="task-orchestrator timeout")

    async def fake_state(project_id: str):
        return _workflow_result(state={"status": "partial"})

    monkeypatch.setattr(
        "src.dopemux.commands.orchestrator_commands.pm_get_priority_queue",
        fake_queue,
    )
    monkeypatch.setattr(
        "src.dopemux.commands.orchestrator_commands.pm_get_blockers",
        fake_blockers,
    )
    monkeypatch.setattr(
        "src.dopemux.commands.orchestrator_commands.pm_get_workflow_state",
        fake_state,
    )

    result = CliRunner().invoke(cli, ["orchestrator", "daily"])

    assert result.exit_code == 0, result.output
    assert "Task Orchestrator Daily" in result.output
    assert "queue: available" in result.output
    assert "workflow_state: available" in result.output
    assert "blockers: ERROR task-orchestrator timeout" in result.output
    assert "partial_failures: 1" in result.output


def test_orchestrator_commands_do_not_call_write_capable_helpers():
    module_path = Path("src/dopemux/commands/orchestrator_commands.py")
    tree = ast.parse(module_path.read_text())

    forbidden = {
        "transition",
        "update",
        "write",
        "record",
        "post",
        "patch",
        "put",
        "delete",
        "clear_index",
    }
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called.add(func.id)
            elif isinstance(func, ast.Attribute):
                called.add(func.attr)

    assert called.isdisjoint(forbidden)
