from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from typing import Protocol, runtime_checkable

_HEAD_RE = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_RFC3339_UTC_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")


def _non_empty(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a non-empty string")


def validate_rfc3339_utc(value: str, label: str = "fetched_at") -> None:
    if not isinstance(value, str) or _RFC3339_UTC_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must use canonical RFC 3339 UTC syntax")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{label} must use canonical RFC 3339 UTC syntax") from exc


def utf8_key(value: str) -> bytes:
    return value.encode("utf-8")


@dataclass(frozen=True, slots=True)
class SourceRef:
    locator: str
    sha256: str
    observed_head: str
    fetched_at: str

    def __post_init__(self) -> None:
        _non_empty(self.locator, "source locator")
        if _SHA256_RE.fullmatch(self.sha256) is None:
            raise ValueError("source sha256 must be 64 lowercase hex characters")
        if _HEAD_RE.fullmatch(self.observed_head) is None:
            raise ValueError("source observed_head must be a Git object id")
        validate_rfc3339_utc(self.fetched_at, "source fetched_at")


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str
    project_id: str
    lane_id: str
    field: str
    value: str
    materiality: str
    freshness: str
    transformation_id: str
    source: SourceRef

    def __post_init__(self) -> None:
        for label, value in (
            ("claim_id", self.claim_id),
            ("project_id", self.project_id),
            ("lane_id", self.lane_id),
            ("field", self.field),
            ("value", self.value),
            ("transformation_id", self.transformation_id),
        ):
            _non_empty(value, label)
        if self.materiality not in {"BLOCKING", "NON_BLOCKING"}:
            raise ValueError("materiality is invalid")
        if self.freshness not in {"CURRENT", "STALE", "UNKNOWN"}:
            raise ValueError("freshness is invalid")


@dataclass(frozen=True, slots=True)
class LaneDependency:
    project_id: str
    lane_id: str
    candidate_sha: str

    def __post_init__(self) -> None:
        _non_empty(self.project_id, "dependency project_id")
        _non_empty(self.lane_id, "dependency lane_id")
        if _HEAD_RE.fullmatch(self.candidate_sha) is None:
            raise ValueError("dependency candidate_sha must be a Git object id")


@dataclass(frozen=True, slots=True)
class LaneEvidence:
    project_id: str
    lane_id: str
    candidate_sha: str
    dependencies: tuple[LaneDependency, ...]
    gate_status: str
    audit_status: str
    lifecycle_state: str

    def __post_init__(self) -> None:
        _non_empty(self.project_id, "lane project_id")
        _non_empty(self.lane_id, "lane_id")
        if _HEAD_RE.fullmatch(self.candidate_sha) is None:
            raise ValueError("candidate_sha must be a Git object id")
        if not isinstance(self.dependencies, tuple) or not all(
            isinstance(item, LaneDependency) for item in self.dependencies
        ):
            raise ValueError("dependencies must contain LaneDependency values")
        if len(self.dependencies) != len(set(self.dependencies)):
            raise ValueError("duplicate dependencies are not allowed")
        if self.gate_status not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("gate_status is invalid")
        if self.audit_status not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("audit_status is invalid")
        _non_empty(self.lifecycle_state, "lifecycle_state")


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

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("authority must be NONE")
        if self.surface_class != "PROJECTION":
            raise ValueError("surface_class must be PROJECTION")
        if self.is_proof is not False:
            raise ValueError("is_proof must be false")
        if self.schema_version != "pcp.repository_planner_source.v1":
            raise ValueError("schema_version is unsupported")
        _non_empty(self.project_id, "project_id")
        _non_empty(self.evidence_class, "evidence_class")
        if _HEAD_RE.fullmatch(self.observed_head) is None:
            raise ValueError("observed_head must be a Git object id")
        validate_rfc3339_utc(self.fetched_at)
        if self.freshness not in {"CURRENT", "STALE", "UNKNOWN"}:
            raise ValueError("freshness is invalid")
        if not isinstance(self.claims, tuple) or not all(
            isinstance(item, Claim) for item in self.claims
        ):
            raise ValueError("claims must contain Claim values")
        if not isinstance(self.lanes, tuple) or not all(
            isinstance(item, LaneEvidence) for item in self.lanes
        ):
            raise ValueError("lanes must contain LaneEvidence values")
        for claim in self.claims:
            SourceRef(
                claim.source.locator,
                claim.source.sha256,
                claim.source.observed_head,
                claim.source.fetched_at,
            )
            Claim(
                claim.claim_id,
                claim.project_id,
                claim.lane_id,
                claim.field,
                claim.value,
                claim.materiality,
                claim.freshness,
                claim.transformation_id,
                claim.source,
            )
        for lane in self.lanes:
            dependencies = tuple(
                LaneDependency(
                    dependency.project_id,
                    dependency.lane_id,
                    dependency.candidate_sha,
                )
                for dependency in lane.dependencies
            )
            LaneEvidence(
                lane.project_id,
                lane.lane_id,
                lane.candidate_sha,
                dependencies,
                lane.gate_status,
                lane.audit_status,
                lane.lifecycle_state,
            )
        claim_ids = [claim.claim_id for claim in self.claims]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("duplicate claim_id")
        lane_keys = [
            (lane.project_id, lane.lane_id, lane.candidate_sha) for lane in self.lanes
        ]
        if len(lane_keys) != len(set(lane_keys)):
            raise ValueError("duplicate project/lane/candidate identity")
        if any(lane.project_id != self.project_id for lane in self.lanes):
            raise ValueError("lane project_id does not match source")
        lane_ids = {lane.lane_id for lane in self.lanes}
        for claim in self.claims:
            if claim.project_id != self.project_id:
                raise ValueError("claim project_id does not match source")
            if claim.lane_id not in lane_ids:
                raise ValueError(f"claim references unknown lane: {claim.lane_id}")
            if claim.freshness != self.freshness:
                raise ValueError("claim freshness does not match source")
            if claim.source.observed_head != self.observed_head:
                raise ValueError("claim source observed_head does not match source")
            if claim.source.fetched_at != self.fetched_at:
                raise ValueError("claim source fetched_at does not match source")


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

    def __post_init__(self) -> None:
        if re.fullmatch(r"conflict:[0-9a-f]{64}", self.conflict_id) is None:
            raise ValueError("conflict_id is invalid")
        for label, value in (
            ("project_id", self.project_id),
            ("lane_id", self.lane_id),
            ("field", self.field),
        ):
            _non_empty(value, label)
        if len(self.values) < 2 or len(self.values) != len(set(self.values)):
            raise ValueError("conflict values must contain unique disagreement values")
        for source in self.sources:
            SourceRef(
                source.locator,
                source.sha256,
                source.observed_head,
                source.fetched_at,
            )
        if self.materiality not in {"BLOCKING", "NON_BLOCKING"}:
            raise ValueError("conflict materiality is invalid")
        if self.status != "OPEN":
            raise ValueError("conflict status must be OPEN")
        if self.resolution_authority != "SOURCE_REPOSITORY":
            raise ValueError("conflict resolution authority is invalid")


@dataclass(frozen=True, slots=True)
class LaneProjection:
    project_id: str
    lane_id: str
    candidate_sha: str
    dependencies: tuple[LaneDependency, ...]
    gate_status: str
    audit_status: str
    lifecycle_state: str
    freshness: str

    def __post_init__(self) -> None:
        LaneEvidence(
            self.project_id,
            self.lane_id,
            self.candidate_sha,
            self.dependencies,
            self.gate_status,
            self.audit_status,
            self.lifecycle_state,
        )
        if self.freshness not in {"CURRENT", "STALE", "UNKNOWN"}:
            raise ValueError("freshness is invalid")


@dataclass(frozen=True, slots=True)
class Recommendation:
    project_id: str
    lane_id: str
    candidate_sha: str
    disposition: str
    reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        _non_empty(self.project_id, "recommendation project_id")
        _non_empty(self.lane_id, "recommendation lane_id")
        if _HEAD_RE.fullmatch(self.candidate_sha) is None:
            raise ValueError("recommendation candidate_sha must be a Git object id")
        if self.disposition not in {
            "READY_FOR_CONTROL_TOWER_REVIEW",
            "DEFER_BLOCKING_CONFLICT",
            "DEFER_STALE_EVIDENCE",
            "DEFER_FAILED_GATE",
            "UNKNOWN",
            "WAIT_DEPENDENCY",
        }:
            raise ValueError("recommendation disposition is invalid")
        if not isinstance(self.reasons, tuple) or not all(
            isinstance(reason, str) and reason for reason in self.reasons
        ):
            raise ValueError("recommendation reasons are invalid")


@dataclass(frozen=True, slots=True)
class PortfolioProjection:
    authority: str
    surface_class: str
    is_proof: bool
    sources: tuple[SourceSnapshot, ...]
    lanes: tuple[LaneProjection, ...]
    conflicts: tuple[Conflict, ...]
    recommendations: tuple[Recommendation, ...] = ()

    def __post_init__(self) -> None:
        if self.authority != "NONE":
            raise ValueError("authority must be NONE")
        if self.surface_class != "PROJECTION":
            raise ValueError("surface_class must be PROJECTION")
        if self.is_proof is not False:
            raise ValueError("is_proof must be false")
        for source in self.sources:
            SourceSnapshot(
                source.schema_version,
                source.project_id,
                source.authority,
                source.surface_class,
                source.is_proof,
                source.evidence_class,
                source.observed_head,
                source.fetched_at,
                source.freshness,
                source.claims,
                source.lanes,
            )
        for lane in self.lanes:
            LaneProjection(
                lane.project_id,
                lane.lane_id,
                lane.candidate_sha,
                lane.dependencies,
                lane.gate_status,
                lane.audit_status,
                lane.lifecycle_state,
                lane.freshness,
            )
        for conflict in self.conflicts:
            Conflict(
                conflict.conflict_id,
                conflict.project_id,
                conflict.lane_id,
                conflict.field,
                conflict.values,
                conflict.sources,
                conflict.materiality,
                conflict.status,
                conflict.resolution_authority,
            )
        for recommendation in self.recommendations:
            Recommendation(
                recommendation.project_id,
                recommendation.lane_id,
                recommendation.candidate_sha,
                recommendation.disposition,
                recommendation.reasons,
            )
        claim_ids = [
            claim.claim_id for source in self.sources for claim in source.claims
        ]
        if len(claim_ids) != len(set(claim_ids)):
            raise ValueError("duplicate claim_id across portfolio sources")
        lane_keys = [
            (lane.project_id, lane.lane_id, lane.candidate_sha) for lane in self.lanes
        ]
        if len(lane_keys) != len(set(lane_keys)):
            raise ValueError("duplicate project/lane/candidate identity")


@runtime_checkable
class ProjectExtensionAdapter(Protocol):
    extension_id: str

    def matches(self, generic_export: Mapping[str, object]) -> bool: ...

    def enrich(
        self, generic_export: Mapping[str, object], source_root: Path
    ) -> SourceSnapshot: ...
