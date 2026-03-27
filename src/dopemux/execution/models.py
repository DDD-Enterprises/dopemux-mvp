"""Canonical execution domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field



def now_utc() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class PacketState(str, Enum):
    """Primary lifecycle state for executable packets."""

    PENDING = "PENDING"
    LEASED = "LEASED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ABANDONED = "ABANDONED"


class LeaseState(str, Enum):
    """State of a packet lease."""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"
    REVOKED = "REVOKED"


class ExecutionDisposition(str, Enum):
    """Final disposition recorded by a release."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ABANDONED = "ABANDONED"


class ExecutionEventType(str, Enum):
    """Structured event types for execution-plane transitions."""

    PACKET_CREATED = "PACKET_CREATED"
    LEASE_ACQUIRED = "LEASE_ACQUIRED"
    LEASE_RENEWED = "LEASE_RENEWED"
    LEASE_EXPIRED = "LEASE_EXPIRED"
    LEASE_RELEASED = "LEASE_RELEASED"
    LEASE_REVOKED = "LEASE_REVOKED"
    RESULT_RECORDED = "RESULT_RECORDED"
    PACKET_REQUEUED = "PACKET_REQUEUED"
    PACKET_CANCELLED = "PACKET_CANCELLED"
    PACKET_ABANDONED = "PACKET_ABANDONED"


class ExecutionDisposition(str, Enum):
    """Final outcome of an execution attempt."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"


class ExecutionResult(BaseModel):
    """Immutable record of an execution attempt."""

    packet_id: str
    lease_id: UUID
    agent_id: str
    disposition: ExecutionDisposition
    result_summary: str
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    started_at_utc: datetime
    completed_at_utc: datetime


class ExecutionPacket(BaseModel):
    """Authoritative state container for executable packets."""

    packet_id: str = Field(..., description="Unique packet identifier")
    owner_id: str = Field(..., description="Primary author or operator")
    task_id: Optional[str] = Field(default=None, description="Optional logical task identifier")
    depends_on: List[str] = Field(default_factory=list, description="Prerequisite packet IDs")
    state: PacketState = Field(default=PacketState.PENDING)
    attempt_count: int = Field(default=0, ge=0)
    max_attempts: int = Field(default=3, ge=1)
    last_error: Optional[str] = Field(default=None)
    last_agent_id: Optional[str] = Field(default=None)
    current_fencing_token: int = Field(default=0, ge=0)
    priority: int = Field(default=0)
    routing_hints: Dict[str, Any] = Field(default_factory=dict)
    canonical_inputs: Dict[str, Any] = Field(default_factory=dict)
    expected_outputs: Dict[str, Any] = Field(default_factory=dict)
    proof_requirements: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    proof_bundle: Dict[str, Any] = Field(default_factory=dict)
    created_at_utc: datetime = Field(default_factory=now_utc)
    updated_at_utc: datetime = Field(default_factory=now_utc)

    model_config = {"frozen": False}


class PacketLease(BaseModel):
    """Locking primitive for exclusive packet access."""

    lease_id: UUID = Field(default_factory=uuid4, description="Unique lease identifier")
    packet_id: str = Field(...)
    agent_id: str = Field(...)
    worker_instance_id: str = Field(...)
    fencing_token: int = Field(..., ge=1)
    issued_at_utc: datetime = Field(default_factory=now_utc)
    expires_at_utc: datetime = Field(...)
    last_renewed_at_utc: datetime = Field(default_factory=now_utc)
    ttl_seconds: int = Field(default=300, ge=1)
    state: LeaseState = Field(default=LeaseState.ACTIVE)
    result: Optional[ExecutionResult] = None

    model_config = {"frozen": False}


class ExecutionResultInput(BaseModel):
    """Structured release payload provided by the executor."""

    summary: str = Field(...)
    payload: Dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = Field(default=None)
    proof_ref: Optional[Any] = Field(default=None)

    model_config = {"frozen": False}


class ExecutionResult(BaseModel):
    """Durable result persisted when a lease is released."""

    result_id: UUID = Field(default_factory=uuid4)
    packet_id: str = Field(...)
    lease_id: UUID = Field(...)
    disposition: ExecutionDisposition = Field(...)
    summary: str = Field(...)
    payload: Dict[str, Any] = Field(default_factory=dict)
    error_code: Optional[str] = Field(default=None)
    proof_ref: Optional[Any] = Field(default=None)
    completed_at_utc: datetime = Field(default_factory=now_utc)

    model_config = {"frozen": False}


class ExecutionEvent(BaseModel):
    """Append-only event describing lease and packet transitions."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: ExecutionEventType = Field(...)
    packet_id: str = Field(...)
    lease_id: Optional[UUID] = Field(default=None)
    fencing_token: Optional[int] = Field(default=None)
    actor_id: str = Field(...)
    worker_instance_id: Optional[str] = Field(default=None)
    occurred_at_utc: datetime = Field(default_factory=now_utc)
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": False}


class PacketStatusView(BaseModel):
    """Operator-facing status view for one packet."""

    packet: ExecutionPacket
    lease: Optional[PacketLease] = Field(default=None)
    latest_result: Optional[ExecutionResult] = Field(default=None)
    events: List[ExecutionEvent] = Field(default_factory=list)

    model_config = {"frozen": False}
