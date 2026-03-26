"""
Execution store and lease management implementation.

Implements TP-SIA-EXEC-0001: core data models and locking primitives for the
Workflow / Execution Control Plane.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from .models import ExecutionPacket, PacketLease, PacketState, LeaseState


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


class ExecutionStore(ABC):
    """Abstract base class for ExecutionPacket persistence."""

    @abstractmethod
    def create_packet(self, packet: ExecutionPacket) -> ExecutionPacket:
        """Store a new packet. If packet_id exists, return existing."""
        raise NotImplementedError

    @abstractmethod
    def get_packet(self, packet_id: str) -> Optional[ExecutionPacket]:
        """Retrieve packet by ID."""
        raise NotImplementedError

    @abstractmethod
    def list_ready_packets(self) -> List[ExecutionPacket]:
        """List all packets in READY state."""
        raise NotImplementedError

    @abstractmethod
    def update_packet_state(self, packet_id: str, state: PacketState) -> ExecutionPacket:
        """Update the state of a packet."""
        raise NotImplementedError


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
        raise NotImplementedError

    @abstractmethod
    def heartbeat(self, lease_id: UUID) -> PacketLease:
        """
        Extend the expiry of an active lease.

        Raises:
            LeaseNotFoundError: lease_id does not exist.
            LeaseExpiredError: lease has already expired.
        """
        raise NotImplementedError

    @abstractmethod
    def release(self, lease_id: UUID, final_state: PacketState) -> PacketLease:
        """
        Transition packet to final_state and mark lease as RELEASED.

        Raises:
            LeaseNotFoundError: lease_id does not exist.
        """
        raise NotImplementedError


class InMemoryExecutionStore(ExecutionStore):
    """In-memory implementation of ExecutionStore."""

    def __init__(self) -> None:
        self._packets: Dict[str, ExecutionPacket] = {}

    def create_packet(self, packet: ExecutionPacket) -> ExecutionPacket:
        if packet.packet_id in self._packets:
            return self._packets[packet.packet_id].model_copy()
        self._packets[packet.packet_id] = packet.model_copy()
        return self._packets[packet.packet_id].model_copy()

    def get_packet(self, packet_id: str) -> Optional[ExecutionPacket]:
        packet = self._packets.get(packet_id)
        return packet.model_copy() if packet else None

    def list_ready_packets(self) -> List[ExecutionPacket]:
        return [p.model_copy() for p in self._packets.values() if p.state == PacketState.READY]

    def update_packet_state(self, packet_id: str, state: PacketState) -> ExecutionPacket:
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

    def checkout(self, packet_id: str, agent_id: str, ttl_seconds: int) -> PacketLease:
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
        lease = self._leases.get(lease_id)
        if not lease:
            raise LeaseNotFoundError(lease_id)

        now = datetime.now(timezone.utc)
        if lease.expires_at_utc <= now:
            lease.state = LeaseState.EXPIRED
            is_active_lease = self._packet_to_lease.get(lease.packet_id) == lease_id
            if is_active_lease:
                del self._packet_to_lease[lease.packet_id]
                packet = self._execution_store.get_packet(lease.packet_id)
                if packet and packet.state in {PacketState.LEASED, PacketState.EXECUTING}:
                    self._execution_store.update_packet_state(lease.packet_id, PacketState.READY)
            raise LeaseExpiredError(lease_id)

        lease.expires_at_utc = now + timedelta(seconds=lease.ttl_seconds)
        # Ensure packet state is EXECUTING if it was LEASED
        packet = self._execution_store.get_packet(lease.packet_id)
        if packet and packet.state == PacketState.LEASED:
            self._execution_store.update_packet_state(lease.packet_id, PacketState.EXECUTING)

        return lease.model_copy()

    def release(self, lease_id: UUID, final_state: PacketState) -> PacketLease:
        lease = self._leases.get(lease_id)
        if not lease:
            raise LeaseNotFoundError(lease_id)

        current_lease_id = self._packet_to_lease.get(lease.packet_id)
        if lease.state != LeaseState.ACTIVE or current_lease_id != lease_id:
            raise LeaseExpiredError(lease_id)

        lease.state = LeaseState.RELEASED
        self._execution_store.update_packet_state(lease.packet_id, final_state)
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
