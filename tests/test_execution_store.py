import pytest

from dopemux.execution.models import ExecutionPacket, LeaseState, PacketState
from dopemux.execution.store import (
    InMemoryExecutionStore,
    InMemoryLeaseStore,
    LeaseExpiredError,
    PacketNotFoundError,
    PacketNotReadyError,
)

@pytest.fixture
def execution_store():
    return InMemoryExecutionStore()


@pytest.fixture
def lease_store(execution_store):
    return InMemoryLeaseStore(execution_store)


def test_packet_creation(execution_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    created = execution_store.create_packet(packet)
    assert created.packet_id == "TP-1"
    assert created.state == PacketState.READY


def test_checkout_success(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    execution_store.create_packet(packet)

    lease = lease_store.checkout("TP-1", "agent-1", ttl_seconds=60)
    assert lease.packet_id == "TP-1"
    assert lease.agent_id == "agent-1"
    assert lease.state == LeaseState.ACTIVE

    # Verify packet state updated
    updated_packet = execution_store.get_packet("TP-1")
    assert updated_packet.state == PacketState.LEASED


def test_checkout_non_existent_packet(lease_store):
    with pytest.raises(PacketNotFoundError):
        lease_store.checkout("NON-EXISTENT", "agent-1", ttl_seconds=60)


def test_checkout_already_leased(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    execution_store.create_packet(packet)
    lease_store.checkout("TP-1", "agent-1", ttl_seconds=60)

    with pytest.raises(PacketNotReadyError):
        lease_store.checkout("TP-1", "agent-2", ttl_seconds=60)


def test_heartbeat_extends_expiry(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    execution_store.create_packet(packet)
    lease = lease_store.checkout("TP-1", "agent-1", ttl_seconds=60)

    original_expiry = lease.expires_at_utc
    updated_lease = lease_store.heartbeat(lease.lease_id)

    assert updated_lease.expires_at_utc > original_expiry
    assert execution_store.get_packet("TP-1").state == PacketState.EXECUTING


def test_heartbeat_expired_lease(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    execution_store.create_packet(packet)

    # Create lease with negative TTL (instantly expired)
    lease = lease_store.checkout("TP-1", "agent-1", ttl_seconds=-1)

    with pytest.raises(LeaseExpiredError):
        lease_store.heartbeat(lease.lease_id)


def test_release_packet(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    execution_store.create_packet(packet)
    lease = lease_store.checkout("TP-1", "agent-1", ttl_seconds=60)

    released_lease = lease_store.release(lease.lease_id, final_state=PacketState.PROOF_GENERATED)

    assert execution_store.get_packet("TP-1").state == PacketState.PROOF_GENERATED
    assert released_lease.state == LeaseState.RELEASED


def test_reclaim_expired_lease(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    execution_store.create_packet(packet)

    # Agent 1 takes lease and it expires
    lease_store.checkout("TP-1", "agent-1", ttl_seconds=-1)

    # Agent 2 should be able to checkout now
    lease2 = lease_store.checkout("TP-1", "agent-2", ttl_seconds=60)
    assert lease2.agent_id == "agent-2"
    assert execution_store.get_packet("TP-1").state == PacketState.LEASED


def test_checkout_rejects_non_ready_terminal_state(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1", state=PacketState.PROOF_GENERATED)
    execution_store.create_packet(packet)

    with pytest.raises(PacketNotReadyError):
        lease_store.checkout("TP-1", "agent-1", ttl_seconds=60)


def test_heartbeat_expiry_returns_packet_to_ready(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    execution_store.create_packet(packet)
    lease = lease_store.checkout("TP-1", "agent-1", ttl_seconds=1)

    lease_store._leases[lease.lease_id].expires_at_utc = lease_store._leases[lease.lease_id].expires_at_utc.replace(
        year=2000
    )

    with pytest.raises(LeaseExpiredError):
        lease_store.heartbeat(lease.lease_id)

    assert execution_store.get_packet("TP-1").state == PacketState.READY
    assert "TP-1" not in lease_store._packet_to_lease


def test_stale_heartbeat_cannot_clobber_newer_lease(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    execution_store.create_packet(packet)
    stale_lease = lease_store.checkout("TP-1", "agent-1", ttl_seconds=-1)
    fresh_lease = lease_store.checkout("TP-1", "agent-2", ttl_seconds=60)

    with pytest.raises(LeaseExpiredError):
        lease_store.heartbeat(stale_lease.lease_id)

    assert execution_store.get_packet("TP-1").state == PacketState.LEASED
    active_lease = lease_store.heartbeat(fresh_lease.lease_id)
    assert active_lease.state == LeaseState.ACTIVE
    assert execution_store.get_packet("TP-1").state == PacketState.EXECUTING


def test_stale_release_cannot_overwrite_packet_state(execution_store, lease_store):
    packet = ExecutionPacket(packet_id="TP-1", owner_id="user1")
    execution_store.create_packet(packet)
    lease = lease_store.checkout("TP-1", "agent-1", ttl_seconds=60)
    lease_store.release(lease.lease_id, final_state=PacketState.PROOF_GENERATED)

    with pytest.raises(LeaseExpiredError):
        lease_store.release(lease.lease_id, final_state=PacketState.READY)

    assert execution_store.get_packet("TP-1").state == PacketState.PROOF_GENERATED
