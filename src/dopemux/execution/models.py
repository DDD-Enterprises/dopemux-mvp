"""
Canonical Execution Domain Models.

Implements TP-SIA-EXEC-0001: core data models and locking primitives for the
Workflow / Execution Control Plane.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PacketState(str, Enum):
    """Execution lifecycle state for a Task Packet."""

    READY = "READY"  # Available for lease
    LEASED = "LEASED"  # Checked out by an agent
    EXECUTING = "EXECUTING"  # Agent is actively processing (heartbeat active)
    PROOF_GENERATED = "PROOF_GENERATED"  # Work complete, verification artifacts present
    AUDITED = "AUDITED"  # Human or Supervisor has verified the proof
    COMMITTED = "COMMITTED"  # Changes merged to target branch


class LeaseState(str, Enum):
    """State of a packet lease."""

    ACTIVE = "ACTIVE"  # Lease is within TTL
    EXPIRED = "EXPIRED"  # Heartbeat missed; packet returned to READY
    RELEASED = "RELEASED"  # Graceful handoff or completion


class ExecutionPacket(BaseModel):
    """Authoritative state container for an executable packet."""

    packet_id: str = Field(..., description="Unique string (e.g., 'TP-SIA-EXEC-0001')")
    owner_id: str = Field(..., description="Primary author/operator")
    depends_on: List[str] = Field(default_factory=list, description="Prerequisite packet IDs")
    state: PacketState = Field(default=PacketState.READY)
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Branch names, initial commit SHAs, requirements"
    )
    proof_bundle: Dict[str, Any] = Field(
        default_factory=dict, description="Links to logs, diffs, and test results"
    )

    model_config = {"frozen": False}


class PacketLease(BaseModel):
    """Locking primitive for exclusive packet access."""

    lease_id: UUID = Field(..., description="UUID4 unique lease identifier")
    packet_id: str = Field(..., description="Targeted packet ID")
    agent_id: str = Field(..., description="Identifier of the leasing entity (e.g., 'gemini-2.5-pro')")
    leased_at_utc: datetime = Field(..., description="Timestamp of checkout")
    expires_at_utc: datetime = Field(..., description="Hard deadline for next heartbeat")
    state: LeaseState = Field(default=LeaseState.ACTIVE)

    model_config = {"frozen": False}
