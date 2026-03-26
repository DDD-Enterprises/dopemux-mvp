"""Execution store and lease management implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Dict, Iterable, List, Optional, Sequence, Set
from uuid import UUID

from .models import (
    ExecutionDisposition,
    ExecutionEvent,
    ExecutionEventType,
    ExecutionPacket,
    ExecutionResult,
    ExecutionResultInput,
    LeaseState,
    PacketLease,
    PacketState,
    PacketStatusView,
)


class ExecutionError(Exception):
    """Base class for execution-related errors."""


class PacketNotFoundError(ExecutionError):
    """Raised when a packet does not exist."""

    def __init__(self, packet_id: str) -> None:
        self.packet_id = packet_id
        super().__init__(f"Packet not found: {packet_id}")


class PacketNotClaimableError(ExecutionError):
    """Raised when a packet exists but cannot be claimed."""

    def __init__(self, packet_id: str, reason: str) -> None:
        self.packet_id = packet_id
        self.reason = reason
        super().__init__(f"Packet {packet_id} is not claimable: {reason}")


class NoClaimablePacketError(ExecutionError):
    """Raised when queue-based checkout finds no eligible packet."""

    def __init__(self) -> None:
        super().__init__("No claimable packet available")


class LeaseNotFoundError(ExecutionError):
    """Raised when a lease does not exist."""

    def __init__(self, lease_id: UUID) -> None:
        self.lease_id = lease_id
        super().__init__(f"Lease not found: {lease_id}")


class LeaseExpiredError(ExecutionError):
    """Raised when an expired lease is used."""

    def __init__(self, lease_id: UUID) -> None:
        self.lease_id = lease_id
        super().__init__(f"Lease {lease_id} has expired")


class LeaseOwnershipError(ExecutionError):
    """Raised when an agent or worker instance does not own a lease."""

    def __init__(self, lease_id: UUID) -> None:
        self.lease_id = lease_id
        super().__init__(f"Lease {lease_id} is not owned by the supplied agent or worker instance")


class FencingTokenMismatchError(ExecutionError):
    """Raised when a stale fencing token is supplied."""

    def __init__(self, lease_id: UUID, token: int) -> None:
        self.lease_id = lease_id
        self.token = token
        super().__init__(f"Lease {lease_id} rejected stale fencing token {token}")


class LeaseStateError(ExecutionError):
    """Raised when a lease cannot perform the requested operation in its current state."""

    def __init__(self, lease_id: UUID, state: LeaseState) -> None:
        self.lease_id = lease_id
        self.state = state
        super().__init__(f"Lease {lease_id} is not ACTIVE (current state: {state})")


class ReleaseConflictError(ExecutionError):
    """Raised when a duplicate release conflicts with the stored result."""

    def __init__(self, lease_id: UUID) -> None:
        self.lease_id = lease_id
        super().__init__(f"Lease {lease_id} already has a different stored release result")


class ExecutionStore(ABC):
    """Abstract base class for packet, result, and event persistence."""

    @abstractmethod
    def create_packet(self, packet: ExecutionPacket) -> ExecutionPacket:
        """Store a new packet or return the existing packet."""

    @abstractmethod
    def get_packet(self, packet_id: str) -> Optional[ExecutionPacket]:
        """Retrieve one packet by ID."""

    @abstractmethod
    def list_packets(self) -> List[ExecutionPacket]:
        """List all packets."""

    @abstractmethod
    def update_packet(self, packet: ExecutionPacket) -> ExecutionPacket:
        """Persist a packet update."""

    @abstractmethod
    def create_result(self, result: ExecutionResult) -> ExecutionResult:
        """Persist a final result."""

    @abstractmethod
    def get_latest_result(self, packet_id: str) -> Optional[ExecutionResult]:
        """Return the latest result for a packet, if any."""

    @abstractmethod
    def get_result_for_lease(self, lease_id: UUID) -> Optional[ExecutionResult]:
        """Return the result stored for a lease, if any."""

    @abstractmethod
    def append_event(self, event: ExecutionEvent) -> ExecutionEvent:
        """Persist one execution event."""

    @abstractmethod
    def list_events(self, packet_id: str, limit: Optional[int] = None) -> List[ExecutionEvent]:
        """Return events for a packet in chronological order."""


class LeaseStore(ABC):
    """Abstract base class for packet lease management."""

    @abstractmethod
    def checkout_packet(
        self,
        agent_id: str,
        worker_instance_id: str,
        packet_id: Optional[str] = None,
        queue: Optional[str] = None,
        capabilities: Optional[Iterable[str]] = None,
        routing_hints: Optional[dict] = None,
        ttl_seconds: int = 300,
    ) -> PacketLease:
        """Atomically claim one packet."""

    @abstractmethod
    def renew_lease(
        self,
        lease_id: UUID,
        agent_id: str,
        worker_instance_id: str,
        fencing_token: int,
    ) -> PacketLease:
        """Renew one active lease."""

    @abstractmethod
    def release_lease(
        self,
        lease_id: UUID,
        agent_id: str,
        worker_instance_id: str,
        fencing_token: int,
        disposition: ExecutionDisposition,
        result: ExecutionResultInput,
    ) -> ExecutionResult:
        """Release one active lease with a structured result."""

    @abstractmethod
    def cancel_packet(self, packet_id: str, reason: str, actor: str, force: bool = True) -> ExecutionPacket:
        """Cancel one packet and revoke any active lease."""

    @abstractmethod
    def get_packet_status(self, packet_id: str) -> PacketStatusView:
        """Return a packet status view with lease, result, and events."""

    @abstractmethod
    def expire_leases(self, now: Optional[datetime] = None) -> List[PacketLease]:
        """Expire all overdue leases and return the expired leases."""


class InMemoryExecutionStore(ExecutionStore):
    """Thread-safe in-memory execution store."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._packets: Dict[str, ExecutionPacket] = {}
        self._results_by_packet: Dict[str, List[ExecutionResult]] = {}
        self._results_by_lease: Dict[UUID, ExecutionResult] = {}
        self._events_by_packet: Dict[str, List[ExecutionEvent]] = {}

    def create_packet(self, packet: ExecutionPacket) -> ExecutionPacket:
        with self._lock:
            if packet.packet_id in self._packets:
                return self._packets[packet.packet_id].model_copy(deep=True)
            stored = packet.model_copy(deep=True)
            self._packets[stored.packet_id] = stored
            self._events_by_packet.setdefault(stored.packet_id, []).append(
                ExecutionEvent(
                    event_type=ExecutionEventType.PACKET_CREATED,
                    packet_id=stored.packet_id,
                    actor_id=stored.owner_id,
                    details={"state": stored.state.value},
                )
            )
            return stored.model_copy(deep=True)

    def get_packet(self, packet_id: str) -> Optional[ExecutionPacket]:
        with self._lock:
            packet = self._packets.get(packet_id)
            return packet.model_copy(deep=True) if packet else None

    def list_packets(self) -> List[ExecutionPacket]:
        with self._lock:
            return [packet.model_copy(deep=True) for packet in self._packets.values()]

    def update_packet(self, packet: ExecutionPacket) -> ExecutionPacket:
        with self._lock:
            if packet.packet_id not in self._packets:
                raise PacketNotFoundError(packet.packet_id)
            stored = packet.model_copy(deep=True)
            self._packets[stored.packet_id] = stored
            return stored.model_copy(deep=True)

    def create_result(self, result: ExecutionResult) -> ExecutionResult:
        with self._lock:
            existing = self._results_by_lease.get(result.lease_id)
            if existing is not None:
                if existing.model_dump() != result.model_dump():
                    raise ReleaseConflictError(result.lease_id)
                return existing.model_copy(deep=True)
            stored = result.model_copy(deep=True)
            self._results_by_lease[stored.lease_id] = stored
            self._results_by_packet.setdefault(stored.packet_id, []).append(stored)
            return stored.model_copy(deep=True)

    def get_latest_result(self, packet_id: str) -> Optional[ExecutionResult]:
        with self._lock:
            results = self._results_by_packet.get(packet_id, [])
            if not results:
                return None
            return results[-1].model_copy(deep=True)

    def get_result_for_lease(self, lease_id: UUID) -> Optional[ExecutionResult]:
        with self._lock:
            result = self._results_by_lease.get(lease_id)
            return result.model_copy(deep=True) if result else None

    def append_event(self, event: ExecutionEvent) -> ExecutionEvent:
        with self._lock:
            stored = event.model_copy(deep=True)
            self._events_by_packet.setdefault(stored.packet_id, []).append(stored)
            return stored.model_copy(deep=True)

    def list_events(self, packet_id: str, limit: Optional[int] = None) -> List[ExecutionEvent]:
        with self._lock:
            events = self._events_by_packet.get(packet_id, [])
            if limit is not None:
                events = events[-limit:]
            return [event.model_copy(deep=True) for event in events]


class InMemoryLeaseStore(LeaseStore):
    """Thread-safe in-memory lease store with deterministic semantics."""

    def __init__(self, execution_store: ExecutionStore) -> None:
        self._lock = RLock()
        self._execution_store = execution_store
        self._leases: Dict[UUID, PacketLease] = {}
        self._packet_to_active_lease: Dict[str, UUID] = {}
        self._lease_history_by_packet: Dict[str, List[UUID]] = {}

    def checkout_packet(
        self,
        agent_id: str,
        worker_instance_id: str,
        packet_id: Optional[str] = None,
        queue: Optional[str] = None,
        capabilities: Optional[Iterable[str]] = None,
        routing_hints: Optional[dict] = None,
        ttl_seconds: int = 300,
    ) -> PacketLease:
        with self._lock:
            now = self._now()
            self.expire_leases(now=now)
            capability_set = set(capabilities or [])
            candidate = self._select_packet_locked(packet_id, queue, capability_set, routing_hints)
            candidate.current_fencing_token += 1
            candidate.attempt_count += 1
            candidate.last_agent_id = agent_id
            candidate.last_error = None
            candidate.state = PacketState.LEASED
            candidate.updated_at_utc = now
            lease = PacketLease(
                packet_id=candidate.packet_id,
                agent_id=agent_id,
                worker_instance_id=worker_instance_id,
                fencing_token=candidate.current_fencing_token,
                issued_at_utc=now,
                expires_at_utc=now + timedelta(seconds=ttl_seconds),
                last_renewed_at_utc=now,
                ttl_seconds=ttl_seconds,
                state=LeaseState.ACTIVE,
            )
            self._leases[lease.lease_id] = lease
            self._packet_to_active_lease[candidate.packet_id] = lease.lease_id
            self._lease_history_by_packet.setdefault(candidate.packet_id, []).append(lease.lease_id)
            self._execution_store.update_packet(candidate)
            self._append_event_locked(
                ExecutionEventType.LEASE_ACQUIRED,
                candidate.packet_id,
                agent_id,
                lease_id=lease.lease_id,
                worker_instance_id=worker_instance_id,
                fencing_token=lease.fencing_token,
                details={"ttl_seconds": ttl_seconds, "attempt_count": candidate.attempt_count},
                occurred_at=now,
            )
            return lease.model_copy(deep=True)

    def renew_lease(
        self,
        lease_id: UUID,
        agent_id: str,
        worker_instance_id: str,
        fencing_token: int,
    ) -> PacketLease:
        with self._lock:
            lease = self._get_lease_locked(lease_id)
            now = self._now()
            self._expire_if_needed_locked(lease, now)
            self._assert_active_locked(lease)
            self._assert_owner_locked(lease, agent_id, worker_instance_id)
            self._assert_fencing_locked(lease, fencing_token)
            lease.last_renewed_at_utc = now
            lease.expires_at_utc = now + timedelta(seconds=lease.ttl_seconds)
            packet = self._get_packet_locked(lease.packet_id)
            if packet.state == PacketState.LEASED:
                packet.state = PacketState.RUNNING
                packet.updated_at_utc = now
                self._execution_store.update_packet(packet)
            self._append_event_locked(
                ExecutionEventType.LEASE_RENEWED,
                lease.packet_id,
                agent_id,
                lease_id=lease.lease_id,
                worker_instance_id=worker_instance_id,
                fencing_token=lease.fencing_token,
                details={"expires_at_utc": lease.expires_at_utc.isoformat()},
                occurred_at=now,
            )
            return lease.model_copy(deep=True)

    def release_lease(
        self,
        lease_id: UUID,
        agent_id: str,
        worker_instance_id: str,
        fencing_token: int,
        disposition: ExecutionDisposition,
        result: ExecutionResultInput,
    ) -> ExecutionResult:
        with self._lock:
            lease = self._get_lease_locked(lease_id)
            now = self._now()
            existing_result = self._execution_store.get_result_for_lease(lease_id)
            if lease.state == LeaseState.RELEASED:
                self._assert_owner_locked(lease, agent_id, worker_instance_id)
                self._assert_fencing_locked(lease, fencing_token)
                if existing_result is not None and self._result_matches(existing_result, disposition, result):
                    return existing_result
                raise ReleaseConflictError(lease_id)
            self._expire_if_needed_locked(lease, now)
            self._assert_active_locked(lease)
            self._assert_owner_locked(lease, agent_id, worker_instance_id)
            self._assert_fencing_locked(lease, fencing_token)
            stored_result = ExecutionResult(
                packet_id=lease.packet_id,
                lease_id=lease.lease_id,
                disposition=disposition,
                summary=result.summary,
                payload=result.payload,
                error_code=result.error_code,
                proof_ref=result.proof_ref,
                completed_at_utc=now,
            )
            stored_result = self._execution_store.create_result(stored_result)
            packet = self._get_packet_locked(lease.packet_id)
            packet.state = self._state_for_disposition(disposition)
            packet.updated_at_utc = now
            packet.last_error = result.error_code or packet.last_error
            if result.proof_ref is not None:
                packet.proof_bundle = dict(packet.proof_bundle)
                packet.proof_bundle["proof_ref"] = result.proof_ref
            self._execution_store.update_packet(packet)
            lease.state = LeaseState.RELEASED
            if self._packet_to_active_lease.get(packet.packet_id) == lease_id:
                del self._packet_to_active_lease[packet.packet_id]
            self._append_event_locked(
                ExecutionEventType.RESULT_RECORDED,
                packet.packet_id,
                agent_id,
                lease_id=lease.lease_id,
                worker_instance_id=worker_instance_id,
                fencing_token=lease.fencing_token,
                details={"disposition": disposition.value, "result_id": str(stored_result.result_id)},
                occurred_at=now,
            )
            self._append_event_locked(
                ExecutionEventType.LEASE_RELEASED,
                packet.packet_id,
                agent_id,
                lease_id=lease.lease_id,
                worker_instance_id=worker_instance_id,
                fencing_token=lease.fencing_token,
                details={"packet_state": packet.state.value},
                occurred_at=now,
            )
            return stored_result.model_copy(deep=True)

    def cancel_packet(self, packet_id: str, reason: str, actor: str, force: bool = True) -> ExecutionPacket:
        with self._lock:
            packet = self._get_packet_locked(packet_id)
            now = self._now()
            active_lease_id = self._packet_to_active_lease.get(packet_id)
            if active_lease_id is not None:
                lease = self._leases[active_lease_id]
                if lease.state == LeaseState.ACTIVE and not force:
                    raise PacketNotClaimableError(packet_id, "active lease present and force=False")
                if lease.state == LeaseState.ACTIVE and force:
                    lease.state = LeaseState.REVOKED
                    del self._packet_to_active_lease[packet_id]
                    self._append_event_locked(
                        ExecutionEventType.LEASE_REVOKED,
                        packet_id,
                        actor,
                        lease_id=lease.lease_id,
                        worker_instance_id=lease.worker_instance_id,
                        fencing_token=lease.fencing_token,
                        details={"reason": reason},
                        occurred_at=now,
                    )
            packet.state = PacketState.CANCELLED
            packet.last_error = reason
            packet.updated_at_utc = now
            self._execution_store.update_packet(packet)
            self._append_event_locked(
                ExecutionEventType.PACKET_CANCELLED,
                packet_id,
                actor,
                lease_id=active_lease_id,
                details={"reason": reason, "force": force},
                occurred_at=now,
            )
            return packet.model_copy(deep=True)

    def get_packet_status(self, packet_id: str) -> PacketStatusView:
        with self._lock:
            active_lease_id = self._packet_to_active_lease.get(packet_id)
            if active_lease_id is not None:
                self._expire_if_needed_locked(self._leases[active_lease_id], self._now())
                active_lease_id = self._packet_to_active_lease.get(packet_id)
            packet = self._get_packet_locked(packet_id)
            lease = self._status_lease_locked(packet_id, active_lease_id)
            latest_result = self._execution_store.get_latest_result(packet_id)
            events = self._execution_store.list_events(packet_id)
            return PacketStatusView(packet=packet, lease=lease, latest_result=latest_result, events=events)

    def expire_leases(self, now: Optional[datetime] = None) -> List[PacketLease]:
        with self._lock:
            current_time = now or self._now()
            expired: List[PacketLease] = []
            for lease_id in list(self._packet_to_active_lease.values()):
                lease = self._leases[lease_id]
                if lease.state != LeaseState.ACTIVE:
                    continue
                if lease.expires_at_utc <= current_time:
                    self._expire_lease_locked(lease, current_time)
                    expired.append(lease.model_copy(deep=True))
            return expired

    def _select_packet_locked(
        self,
        packet_id: Optional[str],
        queue: Optional[str],
        capabilities: Set[str],
        routing_hints: Optional[dict],
    ) -> ExecutionPacket:
        if packet_id is not None:
            packet = self._get_packet_locked(packet_id)
            if not self._is_claimable_locked(packet, queue, capabilities, routing_hints):
                raise PacketNotClaimableError(packet_id, "state, dependency, queue, or capability constraints failed")
            return packet
        candidates = [
            packet for packet in self._execution_store.list_packets()
            if self._is_claimable_locked(packet, queue, capabilities, routing_hints)
        ]
        if not candidates:
            raise NoClaimablePacketError()
        candidates.sort(key=lambda item: (-item.priority, item.created_at_utc, item.packet_id))
        return candidates[0]

    def _is_claimable_locked(
        self,
        packet: ExecutionPacket,
        queue: Optional[str],
        capabilities: Set[str],
        routing_hints: Optional[dict],
    ) -> bool:
        if packet.state != PacketState.PENDING:
            return False
        active_lease_id = self._packet_to_active_lease.get(packet.packet_id)
        if active_lease_id is not None:
            lease = self._leases[active_lease_id]
            if lease.state == LeaseState.ACTIVE:
                return False
        if not self._dependencies_satisfied_locked(packet.depends_on):
            return False
        packet_queue = packet.routing_hints.get("queue")
        if queue is not None and packet_queue != queue:
            return False
        requested_hints = routing_hints or {}
        for key, value in requested_hints.items():
            if packet.routing_hints.get(key) != value:
                return False
        required_capabilities = set(packet.routing_hints.get("required_capabilities", []))
        if required_capabilities and not required_capabilities.issubset(capabilities):
            return False
        return True

    def _dependencies_satisfied_locked(self, dependency_ids: Sequence[str]) -> bool:
        for dependency_id in dependency_ids:
            dependency = self._execution_store.get_packet(dependency_id)
            if dependency is None or dependency.state != PacketState.SUCCEEDED:
                return False
        return True

    def _expire_if_needed_locked(self, lease: PacketLease, now: datetime) -> None:
        if lease.state == LeaseState.ACTIVE and lease.expires_at_utc <= now:
            self._expire_lease_locked(lease, now)

    def _expire_lease_locked(self, lease: PacketLease, now: datetime) -> None:
        lease.state = LeaseState.EXPIRED
        if self._packet_to_active_lease.get(lease.packet_id) == lease.lease_id:
            del self._packet_to_active_lease[lease.packet_id]
        packet = self._get_packet_locked(lease.packet_id)
        packet.last_error = "LEASE_EXPIRED"
        packet.updated_at_utc = now
        if packet.attempt_count < packet.max_attempts:
            packet.state = PacketState.PENDING
            self._execution_store.update_packet(packet)
            self._append_event_locked(
                ExecutionEventType.LEASE_EXPIRED,
                packet.packet_id,
                lease.agent_id,
                lease_id=lease.lease_id,
                worker_instance_id=lease.worker_instance_id,
                fencing_token=lease.fencing_token,
                details={"requeued": True},
                occurred_at=now,
            )
            self._append_event_locked(
                ExecutionEventType.PACKET_REQUEUED,
                packet.packet_id,
                lease.agent_id,
                lease_id=lease.lease_id,
                worker_instance_id=lease.worker_instance_id,
                fencing_token=lease.fencing_token,
                details={"attempt_count": packet.attempt_count, "max_attempts": packet.max_attempts},
                occurred_at=now,
            )
            return
        packet.state = PacketState.ABANDONED
        self._execution_store.update_packet(packet)
        self._append_event_locked(
            ExecutionEventType.LEASE_EXPIRED,
            packet.packet_id,
            lease.agent_id,
            lease_id=lease.lease_id,
            worker_instance_id=lease.worker_instance_id,
            fencing_token=lease.fencing_token,
            details={"requeued": False},
            occurred_at=now,
        )
        self._append_event_locked(
            ExecutionEventType.PACKET_ABANDONED,
            packet.packet_id,
            lease.agent_id,
            lease_id=lease.lease_id,
            worker_instance_id=lease.worker_instance_id,
            fencing_token=lease.fencing_token,
            details={"attempt_count": packet.attempt_count, "max_attempts": packet.max_attempts},
            occurred_at=now,
        )

    def _assert_active_locked(self, lease: PacketLease) -> None:
        if lease.state == LeaseState.EXPIRED:
            raise LeaseExpiredError(lease.lease_id)
        if lease.state != LeaseState.ACTIVE:
            raise LeaseStateError(lease.lease_id, lease.state)
        active_lease_id = self._packet_to_active_lease.get(lease.packet_id)
        if active_lease_id != lease.lease_id:
            raise LeaseStateError(lease.lease_id, lease.state)

    def _assert_owner_locked(self, lease: PacketLease, agent_id: str, worker_instance_id: str) -> None:
        if lease.agent_id != agent_id or lease.worker_instance_id != worker_instance_id:
            raise LeaseOwnershipError(lease.lease_id)

    def _assert_fencing_locked(self, lease: PacketLease, fencing_token: int) -> None:
        if lease.fencing_token != fencing_token:
            raise FencingTokenMismatchError(lease.lease_id, fencing_token)
        packet = self._get_packet_locked(lease.packet_id)
        if packet.current_fencing_token != fencing_token:
            raise FencingTokenMismatchError(lease.lease_id, fencing_token)

    def _get_packet_locked(self, packet_id: str) -> ExecutionPacket:
        packet = self._execution_store.get_packet(packet_id)
        if packet is None:
            raise PacketNotFoundError(packet_id)
        return packet

    def _get_lease_locked(self, lease_id: UUID) -> PacketLease:
        lease = self._leases.get(lease_id)
        if lease is None:
            raise LeaseNotFoundError(lease_id)
        return lease

    def _status_lease_locked(self, packet_id: str, active_lease_id: Optional[UUID]) -> Optional[PacketLease]:
        if active_lease_id is not None:
            return self._leases[active_lease_id].model_copy(deep=True)
        history = self._lease_history_by_packet.get(packet_id, [])
        if not history:
            return None
        return self._leases[history[-1]].model_copy(deep=True)

    def _append_event_locked(
        self,
        event_type: ExecutionEventType,
        packet_id: str,
        actor_id: str,
        *,
        lease_id: Optional[UUID] = None,
        worker_instance_id: Optional[str] = None,
        fencing_token: Optional[int] = None,
        details: Optional[dict] = None,
        occurred_at: Optional[datetime] = None,
    ) -> None:
        self._execution_store.append_event(
            ExecutionEvent(
                event_type=event_type,
                packet_id=packet_id,
                lease_id=lease_id,
                fencing_token=fencing_token,
                actor_id=actor_id,
                worker_instance_id=worker_instance_id,
                occurred_at_utc=occurred_at or self._now(),
                details=details or {},
            )
        )

    def _result_matches(
        self,
        stored_result: ExecutionResult,
        disposition: ExecutionDisposition,
        result: ExecutionResultInput,
    ) -> bool:
        return (
            stored_result.disposition == disposition
            and stored_result.summary == result.summary
            and stored_result.payload == result.payload
            and stored_result.error_code == result.error_code
            and stored_result.proof_ref == result.proof_ref
        )

    def _state_for_disposition(self, disposition: ExecutionDisposition) -> PacketState:
        return PacketState(disposition.value)

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)


_execution_store: Optional[ExecutionStore] = None
_lease_store: Optional[LeaseStore] = None


def get_execution_store() -> ExecutionStore:
    global _execution_store
    if _execution_store is None:
        _execution_store = InMemoryExecutionStore()
    return _execution_store


def get_lease_store() -> LeaseStore:
    global _lease_store
    if _lease_store is None:
        _lease_store = InMemoryLeaseStore(get_execution_store())
    return _lease_store
