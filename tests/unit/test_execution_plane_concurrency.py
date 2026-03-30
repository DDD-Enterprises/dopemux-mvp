from concurrent.futures import ThreadPoolExecutor

import pytest

from dopemux.execution.models import ExecutionPacket, PacketState
from dopemux.execution.store import (
    InMemoryExecutionStore,
    InMemoryLeaseStore,
    StaleLeaseError,
)


import threading
import time
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

import pytest
from dopemux.execution.models import ExecutionPacket, PacketState, LeaseState
from dopemux.execution.store import (
    InMemoryExecutionStore,
    InMemoryLeaseStore,
    LeaseExpiredError,
    StaleLeaseError,
)

@pytest.fixture
def lease_store(execution_store):
    return InMemoryLeaseStore(execution_store)


def test_atomic_checkout_contention(execution_store, lease_store):
def test_atomic_checkout_contention(execution_store, lease_store):
    """
    PROVE: Two agents try to lease the same packet at the same time.
    One should succeed, and the other should fail.
    """
    packet_id = "TP-RACE"
    execution_store.create_packet(ExecutionPacket(packet_id=packet_id, owner_id="test"))

    results = []

    def checkout_task(agent_id):
        try:
            lease = lease_store.checkout(packet_id, agent_id, ttl_seconds=60)
            results.append(("success", agent_id, lease))
        except Exception as exc:  # pragma: no cover - assertion inspects aggregate results
            results.append(("fail", agent_id, exc))

        except Exception as e:
            results.append(("fail", agent_id, e))

    # Using threads to simulate real concurrency
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
    
    # With locking in InMemoryLeaseStore, this MUST be exactly 1.
    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}: {[s[1] for s in successes]}"

def test_stale_holder_protection(execution_store, lease_store):
    """
    PROVE: Agent A gets lease 1, it expires, Agent B gets lease 2.
    Agent A must not be able to heartbeat or release using lease 1.
    """
    packet_id = "TP-STALE"
    execution_store.create_packet(ExecutionPacket(packet_id=packet_id, owner_id="test"))

    # Agent A takes lease and it 'expires' (we simulate this by just setting TTL to -1)
    lease_a = lease_store.checkout(packet_id, "agent-a", ttl_seconds=-1)
    
    # Agent B takes the new lease
    lease_b = lease_store.checkout(packet_id, "agent-b", ttl_seconds=60)
    assert lease_b.lease_id != lease_a.lease_id

    # Agent A tries to heartbeat lease_a - should be rejected as STALE
    with pytest.raises(StaleLeaseError):
         lease_store.heartbeat(lease_a.lease_id)

    # Agent A tries to release lease_a - should be rejected as STALE
    with pytest.raises(StaleLeaseError):
        lease_store.release(lease_a.lease_id, final_state=PacketState.PROOF_GENERATED)
    
    # Verify packet state remained LEASED (from Agent B's checkout)
    packet = execution_store.get_packet(packet_id)
    assert packet.state == PacketState.LEASED
    assert packet.state != PacketState.PROOF_GENERATED

def test_task_decomposer_integration():
    """
    PROVE: A TaskRecord can be wrapped into an ExecutionPacket.
    """
    from dopemux.adhd.task_decomposer import TaskRecord, TaskStatus
    from dopemux.execution.models import PacketState

    record = TaskRecord(
        id="task-123",
        description="Test task",
        estimated_duration=30,
        priority="high",
        status=TaskStatus.PENDING,
    )

    packet = record.to_execution_packet(owner_id="user-1")

        status=TaskStatus.PENDING
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
    # Test state mapping
    record.status = TaskStatus.COMPLETED
    packet_done = record.to_execution_packet(owner_id="user-1")
    assert packet_done.state == PacketState.PROOF_GENERATED
