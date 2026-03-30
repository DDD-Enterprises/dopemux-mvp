"""
Execution store and lease management implementation.

Implements TP-SIA-EXEC-0001: core data models and locking primitives for the
Workflow / Execution Control Plane.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .models import (
    ExecutionDisposition,
    ExecutionPacket,
    ExecutionResult,
    LeaseState,
    PacketLease,
    PacketState,
)


class ExecutionError(Exception):
    """Base class for execution-related errors."""

    pass


class PacketNotFoundError(ExecutionError):
    """Raised when a packet_id does not exist."""

    def __init__(self, packet_id: str) -> None:
        self.packet_id = packet_id
        super().__init__(f"Packet not found: {packet_id}")


class PacketNotReadyError(ExecutionError):
    """Raised when attempting to checkout a packet that is not in READY state."""

    def __init__(self, packet_id: str, state: PacketState) -> None:
        self.packet_id = packet_id
        self.state = state
        super().__init__(f"Packet {packet_id} is not READY (current state: {state})")


class LeaseNotFoundError(ExecutionError):
    """Raised when a lease_id does not exist."""

    def __init__(self, lease_id: UUID) -> None:
        self.lease_id = lease_id
        super().__init__(f"Lease not found: {lease_id}")


class LeaseExpiredError(ExecutionError):
    """Raised when an operation is attempted on an expired lease."""

    def __init__(self, lease_id: UUID) -> None:
        self.lease_id = lease_id
        super().__init__(f"Lease {lease_id} has expired")


class StaleLeaseError(ExecutionError):
    """Raised when an operation uses a non-authoritative lease."""

    def __init__(self, lease_id: UUID, packet_id: str) -> None:
        self.lease_id = lease_id
        self.packet_id = packet_id
        super().__init__(
            f"Lease {lease_id} for packet {packet_id} is stale (no longer authoritative)"
        )


class ExecutionStore(ABC):
    """Abstract base class for ExecutionPacket persistence."""

    @abstractmethod
    def create_packet(self, packet: ExecutionPacket) -> ExecutionPacket:
        """Store a new packet. If packet_id exists, return existing."""
        pass

    @abstractmethod
    def get_packet(self, packet_id: str) -> Optional[ExecutionPacket]:
        """Retrieve packet by ID."""
        pass

    @abstractmethod
    def list_ready_packets(self) -> List[ExecutionPacket]:
        """List all packets in READY state."""
        pass

    @abstractmethod
    def update_packet_state(self, packet_id: str, state: PacketState) -> ExecutionPacket:
        """Update the state of a packet."""
        pass


class LeaseStore(ABC):
    """Abstract base class for PacketLease management."""

    @abstractmethod
    def checkout(self, packet_id: str, agent_id: str, ttl_seconds: int) -> PacketLease:
        """
        Atomically transition packet to LEASED and create a lease.

        Raises:
            PacketNotFoundError: packet_id does not exist.
            PacketNotReadyError: packet is not in READY state.
        """
        pass

    @abstractmethod
    def heartbeat(self, lease_id: UUID) -> PacketLease:
        """
        Extend the expiry of an active lease.

        Raises:
            LeaseNotFoundError: lease_id does not exist.
            LeaseExpiredError: lease has already expired.
            StaleLeaseError: lease is no longer authoritative.
        """
        pass

    @abstractmethod
    def release(
        self,
        lease_id: UUID,
        final_state: PacketState,
        disposition: ExecutionDisposition = ExecutionDisposition.SUCCEEDED,
        result_summary: str = "",
        artifacts: Optional[Dict[str, Any]] = None,
    ) -> PacketLease:
        """
        Transition packet to final_state and mark lease as RELEASED.

        Raises:
            LeaseNotFoundError: lease_id does not exist.
            StaleLeaseError: lease is no longer authoritative.
        """
        pass


class InMemoryExecutionStore(ExecutionStore):
    """In-memory implementation of ExecutionStore."""

    def __init__(self) -> None:
        self._packets: Dict[str, ExecutionPacket] = {}
        self._lock = Lock()

    def create_packet(self, packet: ExecutionPacket) -> ExecutionPacket:
        with self._lock:
            if packet.packet_id in self._packets:
                return self._packets[packet.packet_id].model_copy()
            self._packets[packet.packet_id] = packet.model_copy()
            return self._packets[packet.packet_id].model_copy()

    def get_packet(self, packet_id: str) -> Optional[ExecutionPacket]:
        with self._lock:
            packet = self._packets.get(packet_id)
            return packet.model_copy() if packet else None

    def list_ready_packets(self) -> List[ExecutionPacket]:
        with self._lock:
            return [p.model_copy() for p in self._packets.values() if p.state == PacketState.READY]

    def update_packet_state(self, packet_id: str, state: PacketState) -> ExecutionPacket:
        with self._lock:
            if packet_id not in self._packets:
                raise PacketNotFoundError(packet_id)
            self._packets[packet_id].state = state
            return self._packets[packet_id].model_copy()


class InMemoryLeaseStore(LeaseStore):
    """In-memory implementation of LeaseStore."""

    def __init__(self, execution_store: ExecutionStore) -> None:
        self._execution_store = execution_store
        self._leases: Dict[UUID, PacketLease] = {}
        # Track active lease per packet_id
        self._packet_to_lease: Dict[str, UUID] = {}
        self._lock = Lock()

    def checkout(self, packet_id: str, agent_id: str, ttl_seconds: int) -> PacketLease:
        with self._lock:
            now = datetime.now(timezone.utc)
            packet = self._execution_store.get_packet(packet_id)
            if not packet:
                raise PacketNotFoundError(packet_id)
            if packet.state != PacketState.READY:
                active_lease_id = self._packet_to_lease.get(packet_id)
                if active_lease_id is None or packet.state not in {PacketState.LEASED, PacketState.EXECUTING}:
                    raise PacketNotReadyError(packet_id, packet.state)

                lease = self._leases.get(active_lease_id)
                if lease is None or lease.state != LeaseState.ACTIVE:
                    raise PacketNotReadyError(packet_id, packet.state)

                if lease.expires_at_utc > now:
                    raise PacketNotReadyError(packet_id, packet.state)

                lease.state = LeaseState.EXPIRED
                del self._packet_to_lease[packet_id]

            expires_at = now + timedelta(seconds=ttl_seconds)
            lease = PacketLease(
                lease_id=uuid4(),
                packet_id=packet_id,
                agent_id=agent_id,
                leased_at_utc=now,
                expires_at_utc=expires_at,
                ttl_seconds=ttl_seconds,
                state=LeaseState.ACTIVE,
            )

            self._execution_store.update_packet_state(packet_id, PacketState.LEASED)
            self._leases[lease.lease_id] = lease
            self._packet_to_lease[packet_id] = lease.lease_id
            return lease.model_copy()

    def heartbeat(self, lease_id: UUID) -> PacketLease:
        with self._lock:
            lease = self._leases.get(lease_id)
            if not lease:
                raise LeaseNotFoundError(lease_id)

            if self._packet_to_lease.get(lease.packet_id) != lease_id:
                raise StaleLeaseError(lease_id, lease.packet_id)

            now = datetime.now(timezone.utc)
            if lease.expires_at_utc < now:
                lease.state = LeaseState.EXPIRED
                if self._packet_to_lease.get(lease.packet_id) == lease_id:
                    del self._packet_to_lease[lease.packet_id]
                raise LeaseExpiredError(lease_id)

            lease.expires_at_utc = now + timedelta(seconds=lease.ttl_seconds)
            packet = self._execution_store.get_packet(lease.packet_id)
            if packet and packet.state == PacketState.LEASED:
                self._execution_store.update_packet_state(lease.packet_id, PacketState.EXECUTING)

            return lease.model_copy()

    def release(
        self,
        lease_id: UUID,
        final_state: PacketState,
        disposition: ExecutionDisposition = ExecutionDisposition.SUCCEEDED,
        result_summary: str = "",
        artifacts: Optional[Dict[str, Any]] = None,
    ) -> PacketLease:
        with self._lock:
            lease = self._leases.get(lease_id)
            if not lease:
                raise LeaseNotFoundError(lease_id)

            if self._packet_to_lease.get(lease.packet_id) != lease_id:
                raise StaleLeaseError(lease_id, lease.packet_id)

            now = datetime.now(timezone.utc)
            lease.state = LeaseState.RELEASED
            lease.result = ExecutionResult(
                packet_id=lease.packet_id,
                lease_id=lease_id,
                agent_id=lease.agent_id,
                disposition=disposition,
                result_summary=result_summary,
                artifacts=artifacts or {},
                started_at_utc=lease.leased_at_utc,
                completed_at_utc=now,
            )
            self._execution_store.update_packet_state(lease.packet_id, final_state)
            if self._packet_to_lease.get(lease.packet_id) == lease_id:
                del self._packet_to_lease[lease.packet_id]

            return lease.model_copy()


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
