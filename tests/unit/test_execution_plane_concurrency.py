from concurrent.futures import ThreadPoolExecutor

import pytest

from dopemux.execution.models import ExecutionPacket, PacketState
from dopemux.execution.store import (
    InMemoryExecutionStore,
    InMemoryLeaseStore,
    StaleLeaseError,
)


@pytest.fixture
def execution_store():
    return InMemoryExecutionStore()


@pytest.fixture
def lease_store(execution_store):
    return InMemoryLeaseStore(execution_store)


def test_atomic_checkout_contention(execution_store, lease_store):
    packet_id = "TP-RACE"
    execution_store.create_packet(ExecutionPacket(packet_id=packet_id, owner_id="test"))

    results = []

    def checkout_task(agent_id):
        try:
            lease = lease_store.checkout(packet_id, agent_id, ttl_seconds=60)
            results.append(("success", agent_id, lease))
        except Exception as exc:  # pragma: no cover - assertion inspects aggregate results
            results.append(("fail", agent_id, exc))

    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(10):
            executor.submit(checkout_task, f"agent-{i}")

    successes = [r for r in results if r[0] == "success"]
    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"


def test_stale_holder_protection(execution_store, lease_store):
    packet_id = "TP-STALE"
    execution_store.create_packet(ExecutionPacket(packet_id=packet_id, owner_id="test"))

    lease_a = lease_store.checkout(packet_id, "agent-a", ttl_seconds=-1)
    lease_b = lease_store.checkout(packet_id, "agent-b", ttl_seconds=60)
    assert lease_b.lease_id != lease_a.lease_id

    with pytest.raises(StaleLeaseError):
        lease_store.heartbeat(lease_a.lease_id)

    with pytest.raises(StaleLeaseError):
        lease_store.release(lease_a.lease_id, final_state=PacketState.PROOF_GENERATED)

    packet = execution_store.get_packet(packet_id)
    assert packet is not None
    assert packet.state == PacketState.LEASED


def test_task_decomposer_to_execution_packet():
    from dopemux.adhd.task_decomposer import TaskRecord, TaskStatus

    record = TaskRecord(
        id="task-123",
        description="Test task",
        estimated_duration=30,
        priority="high",
        status=TaskStatus.PENDING,
    )

    packet = record.to_execution_packet(owner_id="user-1")

    assert packet.packet_id == "task-123"
    assert packet.owner_id == "user-1"
    assert packet.state == PacketState.READY
    assert packet.metadata["description"] == "Test task"
    assert packet.metadata["priority"] == "high"
    assert packet.metadata["estimated_duration"] == 30

    record.status = TaskStatus.COMPLETED
    assert record.to_execution_packet(owner_id="user-1").state == PacketState.PROOF_GENERATED
