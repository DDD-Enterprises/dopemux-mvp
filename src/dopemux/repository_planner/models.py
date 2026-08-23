from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class SourceRef:
    locator: str
    sha256: str
    observed_head: str
    fetched_at: str


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    project_id: str
    lane_id: str
    field: str
    value: str
    materiality: str
    freshness: str
    source: SourceRef


@dataclass(frozen=True, slots=True)
class LaneEvidence:
    project_id: str
    lane_id: str
    candidate_sha: str
    dependencies: tuple[str, ...]
    gate_status: str
    audit_status: str
    lifecycle_state: str


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    schema_version: str
    project_id: str
    authority: str
    surface_class: str
    is_proof: bool
    evidence_class: str
    observed_head: str
    fetched_at: str
    freshness: str
    claims: tuple[Claim, ...]
    lanes: tuple[LaneEvidence, ...]


@dataclass(frozen=True, slots=True)
class Conflict:
    conflict_id: str
    project_id: str
    lane_id: str
    field: str
    values: tuple[str, ...]
    sources: tuple[SourceRef, ...]
    materiality: str
    status: str
    resolution_authority: str


@dataclass(frozen=True, slots=True)
class LaneProjection:
    project_id: str
    lane_id: str
    candidate_sha: str
    dependencies: tuple[str, ...]
    gate_status: str
    audit_status: str
    lifecycle_state: str
    freshness: str


@dataclass(frozen=True, slots=True)
class Recommendation:
    project_id: str
    lane_id: str
    candidate_sha: str
    disposition: str
    reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PortfolioProjection:
    authority: str
    surface_class: str
    is_proof: bool
    sources: tuple[SourceSnapshot, ...]
    lanes: tuple[LaneProjection, ...]
    conflicts: tuple[Conflict, ...]
    recommendations: tuple[Recommendation, ...] = ()


@runtime_checkable
class ProjectExtensionAdapter(Protocol):
    extension_id: str

    def matches(self, generic_export: Mapping[str, object]) -> bool: ...

    def enrich(
        self, generic_export: Mapping[str, object], source_root: Path
    ) -> SourceSnapshot: ...
