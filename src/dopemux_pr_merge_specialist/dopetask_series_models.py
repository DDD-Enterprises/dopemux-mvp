"""DopetaskSeriesModels — read-only models for Task Packet series."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PacketStatus(str, Enum):
    """Normalized status for a single Task Packet inside a series."""
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    UNKNOWN = "UNKNOWN"


class SeriesStatus(str, Enum):
    """Normalized status for an entire Task Packet series."""
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATED = "VALIDATED"
    FINALIZED = "FINALIZED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


@dataclass
class DopetaskPacketRecord:
    """Read-only record of a single Task Packet in a series."""
    tp_id: str
    status: PacketStatus
    raw_status: str
    depends_on: List[str] = field(default_factory=list)
    is_final: bool = False
    bundle_path: Optional[str] = None
    title: str = "UNKNOWN"


@dataclass
class DopetaskSeriesIdentity:
    """Identity metadata for a Task Packet series."""
    series_id: str
    project_id: str
    version: str = "0.5.1"


@dataclass
class DopetaskSeriesResult:
    """Aggregated read-only result for a Task Packet series."""
    identity: DopetaskSeriesIdentity
    status: SeriesStatus
    raw_status: str
    packets: List[DopetaskPacketRecord]
    allowed_actions: List[str] = field(default_factory=list)
    computed_at: str = ""
