from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

SERVICE_ROOT = Path(__file__).resolve().parents[2] / "services" / "task-orchestrator"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

try:
    from app.services.task_coordinator import TaskCoordinator
    from dopemux.execution.models import PacketState
    from dopemux.execution.store import InMemoryExecutionStore, InMemoryLeaseStore
    from task_orchestrator.models import AgentType, OrchestrationTask, TaskStatus
except (ImportError, ModuleNotFoundError) as exc:
    pytest.skip(f"task-orchestrator service deps not available: {exc}", allow_module_level=True)


@pytest.mark.asyncio
async def test_execute_batch_uses_leases_for_monitoring(monkeypatch: pytest.MonkeyPatch):
    execution_store = InMemoryExecutionStore()
    lease_store = InMemoryLeaseStore(execution_store)

    monkeypatch.setattr(
        "app.services.task_coordinator.get_execution_store",
        lambda: execution_store,
    )
    monkeypatch.setattr(
        "app.services.task_coordinator.get_lease_store",
        lambda: lease_store,
    )

    coordinator = TaskCoordinator(workspace_id="/tmp/test-workspace")

    async def _noop(*args: Any, **kwargs: Any) -> None:
        return None

    async def _monitor(task: OrchestrationTask, lease_id=None) -> None:
        assert lease_id is not None
        lease_store.heartbeat(lease_id)

    async def _recovery_statistics() -> dict[str, int]:
        return {"total_switches": 0}

    monkeypatch.setattr(coordinator.conport_adapter, "update_task_in_conport", _noop)
    monkeypatch.setattr(coordinator.context_recovery, "detect_context_switch", _noop)
    monkeypatch.setattr(
        coordinator.context_recovery,
        "get_recovery_statistics",
        _recovery_statistics,
    )
    monkeypatch.setattr(coordinator, "_monitor_execution", _monitor)

    task = OrchestrationTask(
        id="task-lease-1",
        leantime_id=101,
        title="Lease-backed execution",
        description="Verify coordinator heartbeat and release flow",
        status=TaskStatus.PENDING,
        priority=3,
        complexity_score=0.4,
        estimated_minutes=15,
        assigned_agent=AgentType.SERENA,
        energy_required="medium",
        dependencies=[],
        context_switches_allowed=2,
        break_frequency_minutes=25,
    )
    coordinator.tasks[task.id] = task

    results = await coordinator._execute_batch([task.id])

    assert results["completed"] == [task.id]
    assert results["failed"] == []
    packet = execution_store.get_packet(task.id)
    assert packet is not None
    assert packet.state == PacketState.PROOF_GENERATED
