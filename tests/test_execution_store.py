from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Barrier, Thread
from typing import List

import pytest

from src.dopemux.execution.models import (
    ExecutionDisposition,
    ExecutionEventType,
    ExecutionPacket,
    ExecutionResultInput,
    LeaseState,
    PacketState,
)
from src.dopemux.execution.store import (
    FencingTokenMismatchError,
    InMemoryExecutionStore,
    InMemoryLeaseStore,
    LeaseExpiredError,
    LeaseOwnershipError,
    LeaseStateError,
    NoClaimablePacketError,
    PacketNotClaimableError,
    ReleaseConflictError,
)


class FailingResultExecutionStore(InMemoryExecutionStore):
    def create_result(self, result):
        raise RuntimeError("result persistence failed")


@pytest.fixture
def execution_store():
    return InMemoryExecutionStore()


@pytest.fixture
def lease_store(execution_store):
    return InMemoryLeaseStore(execution_store)



def make_packet(
    packet_id: str,
    *,
    state: PacketState = PacketState.PENDING,
    priority: int = 0,
    depends_on: list[str] | None = None,
    queue: str | None = None,
    required_capabilities: list[str] | None = None,
    max_attempts: int = 3,
    created_at: datetime | None = None,
) -> ExecutionPacket:
    routing_hints = {}
    if queue is not None:
        routing_hints["queue"] = queue
    if required_capabilities is not None:
        routing_hints["required_capabilities"] = required_capabilities
    return ExecutionPacket(
        packet_id=packet_id,
        owner_id="user-1",
        state=state,
        priority=priority,
        depends_on=depends_on or [],
        routing_hints=routing_hints,
        created_at_utc=created_at or datetime.now(timezone.utc),
        updated_at_utc=created_at or datetime.now(timezone.utc),
        max_attempts=max_attempts,
    )



def test_packet_creation_initial_state_and_event(execution_store):
    packet = execution_store.create_packet(make_packet("TP-1"))

    assert packet.state == PacketState.PENDING
    assert packet.attempt_count == 0
    assert packet.current_fencing_token == 0

    events = execution_store.list_events("TP-1")
    assert [event.event_type for event in events] == [ExecutionEventType.PACKET_CREATED]



def test_targeted_checkout_records_lease_fencing_attempt_and_event(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))

    lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1", ttl_seconds=90)
    packet = execution_store.get_packet("TP-1")
    status = lease_store.get_packet_status("TP-1")

    assert lease.packet_id == "TP-1"
    assert lease.agent_id == "agent-a"
    assert lease.worker_instance_id == "worker-a"
    assert lease.fencing_token == 1
    assert lease.ttl_seconds == 90
    assert packet.state == PacketState.LEASED
    assert packet.attempt_count == 1
    assert packet.last_agent_id == "agent-a"
    assert packet.current_fencing_token == 1
    assert status.lease.lease_id == lease.lease_id
    assert status.events[-1].event_type == ExecutionEventType.LEASE_ACQUIRED



def test_queue_checkout_respects_priority_dependencies_queue_and_capabilities(execution_store, lease_store):
    base_time = datetime(2026, 3, 26, tzinfo=timezone.utc)
    execution_store.create_packet(make_packet("DEP-OK", state=PacketState.SUCCEEDED, created_at=base_time))
    execution_store.create_packet(make_packet("DEP-BAD", state=PacketState.FAILED, created_at=base_time))
    execution_store.create_packet(
        make_packet(
            "TP-BLOCKED",
            priority=50,
            depends_on=["DEP-BAD"],
            queue="alpha",
            created_at=base_time + timedelta(seconds=1),
        )
    )
    execution_store.create_packet(
        make_packet(
            "TP-HIGH",
            priority=20,
            depends_on=["DEP-OK"],
            queue="alpha",
            required_capabilities=["python"],
            created_at=base_time + timedelta(seconds=2),
        )
    )
    execution_store.create_packet(
        make_packet(
            "TP-LOW",
            priority=10,
            queue="alpha",
            created_at=base_time + timedelta(seconds=3),
        )
    )
    execution_store.create_packet(
        make_packet(
            "TP-OTHER-QUEUE",
            priority=999,
            queue="beta",
            created_at=base_time + timedelta(seconds=4),
        )
    )

    lease = lease_store.checkout_packet(
        "agent-a",
        "worker-a",
        queue="alpha",
        capabilities={"python", "pytest"},
        ttl_seconds=60,
    )

    assert lease.packet_id == "TP-HIGH"

    second_lease = lease_store.checkout_packet("agent-b", "worker-b", queue="alpha", capabilities=set())
    assert second_lease.packet_id == "TP-LOW"



def test_double_checkout_rejected_while_lease_is_active(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))
    lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1")

    with pytest.raises(PacketNotClaimableError):
        lease_store.checkout_packet("agent-b", "worker-b", packet_id="TP-1")



def test_renew_transitions_to_running_and_rejects_wrong_owner_and_stale_token(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))
    lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1")

    renewed = lease_store.renew_lease(lease.lease_id, "agent-a", "worker-a", lease.fencing_token)
    packet = execution_store.get_packet("TP-1")

    assert renewed.expires_at_utc > lease.expires_at_utc
    assert packet.state == PacketState.RUNNING

    with pytest.raises(LeaseOwnershipError):
        lease_store.renew_lease(lease.lease_id, "agent-a", "worker-b", lease.fencing_token)

    with pytest.raises(FencingTokenMismatchError):
        lease_store.renew_lease(lease.lease_id, "agent-a", "worker-a", lease.fencing_token + 1)



def test_release_persists_structured_result_and_is_idempotent_for_same_payload(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))
    lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1")
    result_input = ExecutionResultInput(
        summary="completed",
        payload={"tests": ["unit"]},
        proof_ref="proof://bundle-1",
    )

    result = lease_store.release_lease(
        lease.lease_id,
        "agent-a",
        "worker-a",
        lease.fencing_token,
        ExecutionDisposition.SUCCEEDED,
        result_input,
    )
    repeated = lease_store.release_lease(
        lease.lease_id,
        "agent-a",
        "worker-a",
        lease.fencing_token,
        ExecutionDisposition.SUCCEEDED,
        result_input,
    )
    status = lease_store.get_packet_status("TP-1")

    assert result.result_id == repeated.result_id
    assert status.packet.state == PacketState.SUCCEEDED
    assert status.latest_result.summary == "completed"
    assert status.lease.state == LeaseState.RELEASED
    assert status.packet.proof_bundle["proof_ref"] == "proof://bundle-1"
    assert [event.event_type for event in status.events[-2:]] == [
        ExecutionEventType.RESULT_RECORDED,
        ExecutionEventType.LEASE_RELEASED,
    ]



def test_conflicting_duplicate_release_is_rejected(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))
    lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1")
    lease_store.release_lease(
        lease.lease_id,
        "agent-a",
        "worker-a",
        lease.fencing_token,
        ExecutionDisposition.SUCCEEDED,
        ExecutionResultInput(summary="completed"),
    )

    with pytest.raises(ReleaseConflictError):
        lease_store.release_lease(
            lease.lease_id,
            "agent-a",
            "worker-a",
            lease.fencing_token,
            ExecutionDisposition.SUCCEEDED,
            ExecutionResultInput(summary="different"),
        )



def test_stale_release_rejected_after_expiry_and_reassignment(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))
    first = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1", ttl_seconds=1)
    lease_store.expire_leases(now=first.expires_at_utc + timedelta(seconds=1))
    second = lease_store.checkout_packet("agent-b", "worker-b", packet_id="TP-1")

    assert second.fencing_token == 2

    with pytest.raises(LeaseExpiredError):
        lease_store.release_lease(
            first.lease_id,
            "agent-a",
            "worker-a",
            first.fencing_token,
            ExecutionDisposition.SUCCEEDED,
            ExecutionResultInput(summary="late"),
        )



def test_expiry_requeues_within_retry_budget_and_abandons_at_limit(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-REQUEUE", max_attempts=2))
    requeue_lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-REQUEUE", ttl_seconds=1)
    expired = lease_store.expire_leases(now=requeue_lease.expires_at_utc + timedelta(seconds=1))
    status = lease_store.get_packet_status("TP-REQUEUE")

    assert expired[0].state == LeaseState.EXPIRED
    assert status.packet.state == PacketState.PENDING
    assert status.events[-1].event_type == ExecutionEventType.PACKET_REQUEUED

    execution_store.create_packet(make_packet("TP-ABANDON", max_attempts=1))
    abandon_lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-ABANDON", ttl_seconds=1)
    lease_store.expire_leases(now=abandon_lease.expires_at_utc + timedelta(seconds=1))
    abandon_status = lease_store.get_packet_status("TP-ABANDON")

    assert abandon_status.packet.state == PacketState.ABANDONED
    assert abandon_status.events[-1].event_type == ExecutionEventType.PACKET_ABANDONED



def test_cancel_revokes_active_lease_and_blocks_future_renew_and_release(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))
    lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1")

    lease_store.cancel_packet("TP-1", reason="operator stop", actor="supervisor")
    status = lease_store.get_packet_status("TP-1")

    assert status.packet.state == PacketState.CANCELLED
    assert status.lease.state == LeaseState.REVOKED

    with pytest.raises(LeaseStateError):
        lease_store.renew_lease(lease.lease_id, "agent-a", "worker-a", lease.fencing_token)

    with pytest.raises(LeaseStateError):
        lease_store.release_lease(
            lease.lease_id,
            "agent-a",
            "worker-a",
            lease.fencing_token,
            ExecutionDisposition.CANCELLED,
            ExecutionResultInput(summary="late cancel"),
        )



def test_result_persistence_failure_does_not_complete_release():
    execution_store = FailingResultExecutionStore()
    lease_store = InMemoryLeaseStore(execution_store)
    execution_store.create_packet(make_packet("TP-1"))
    lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1")

    with pytest.raises(RuntimeError, match="result persistence failed"):
        lease_store.release_lease(
            lease.lease_id,
            "agent-a",
            "worker-a",
            lease.fencing_token,
            ExecutionDisposition.SUCCEEDED,
            ExecutionResultInput(summary="done"),
        )

    status = lease_store.get_packet_status("TP-1")
    assert status.packet.state == PacketState.LEASED
    assert status.lease.state == LeaseState.ACTIVE
    assert status.latest_result is None



def test_concurrent_targeted_checkout_only_one_agent_wins(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))
    barrier = Barrier(3)
    winners: List[str] = []
    errors: List[str] = []

    def runner(agent_id: str, worker_id: str) -> None:
        barrier.wait()
        try:
            lease_store.checkout_packet(agent_id, worker_id, packet_id="TP-1")
            winners.append(agent_id)
        except PacketNotClaimableError as exc:
            errors.append(exc.reason)

    threads = [
        Thread(target=runner, args=("agent-a", "worker-a")),
        Thread(target=runner, args=("agent-b", "worker-b")),
    ]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()

    assert len(winners) == 1
    assert len(errors) == 1



def test_renew_beats_sweeper_when_done_before_expiry_and_fails_after_expiry(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))
    lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1", ttl_seconds=5)
    lease_store._leases[lease.lease_id].expires_at_utc = datetime.now(timezone.utc) + timedelta(seconds=1)

    renewed = lease_store.renew_lease(lease.lease_id, "agent-a", "worker-a", lease.fencing_token)
    not_expired = lease_store.expire_leases(now=renewed.expires_at_utc - timedelta(seconds=1))
    status = lease_store.get_packet_status("TP-1")

    assert not not_expired
    assert status.packet.state == PacketState.RUNNING
    assert status.lease.state == LeaseState.ACTIVE

    lease_store._leases[lease.lease_id].expires_at_utc = datetime.now(timezone.utc) - timedelta(seconds=1)
    lease_store.expire_leases()
    with pytest.raises(LeaseExpiredError):
        lease_store.renew_lease(lease.lease_id, "agent-a", "worker-a", lease.fencing_token)



def test_get_packet_status_exposes_packet_lease_result_and_events(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-1"))
    lease = lease_store.checkout_packet("agent-a", "worker-a", packet_id="TP-1")
    lease_store.renew_lease(lease.lease_id, "agent-a", "worker-a", lease.fencing_token)
    lease_store.release_lease(
        lease.lease_id,
        "agent-a",
        "worker-a",
        lease.fencing_token,
        ExecutionDisposition.FAILED,
        ExecutionResultInput(summary="lint failed", error_code="LINT_FAIL"),
    )

    status = lease_store.get_packet_status("TP-1")

    assert status.packet.packet_id == "TP-1"
    assert status.packet.state == PacketState.FAILED
    assert status.lease.state == LeaseState.RELEASED
    assert status.latest_result.error_code == "LINT_FAIL"
    assert [event.event_type for event in status.events] == [
        ExecutionEventType.PACKET_CREATED,
        ExecutionEventType.LEASE_ACQUIRED,
        ExecutionEventType.LEASE_RENEWED,
        ExecutionEventType.RESULT_RECORDED,
        ExecutionEventType.LEASE_RELEASED,
    ]



def test_queue_checkout_raises_when_no_packet_is_claimable(execution_store, lease_store):
    execution_store.create_packet(make_packet("TP-BLOCKED", depends_on=["MISSING"]))

    with pytest.raises(NoClaimablePacketError):
        lease_store.checkout_packet("agent-a", "worker-a")
