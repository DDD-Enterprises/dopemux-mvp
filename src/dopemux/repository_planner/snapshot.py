from __future__ import annotations

import re
from collections.abc import Mapping

from .models import Claim, LaneDependency, LaneEvidence, SourceRef, SourceSnapshot

_HEAD_RE = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_TOP_LEVEL_KEYS = {
    "schema_version",
    "project_id",
    "authority",
    "surface_class",
    "is_proof",
    "evidence_class",
    "observed_head",
    "fetched_at",
    "freshness",
    "claims",
    "lanes",
}
_CLAIM_KEYS = {
    "claim_id",
    "lane_id",
    "field",
    "value",
    "materiality",
    "transformation_id",
    "source_locator",
    "source_sha256",
}
_LANE_KEYS = {
    "lane_id",
    "candidate_sha",
    "dependencies",
    "gate_status",
    "audit_status",
    "lifecycle_state",
}


def _exact_keys(payload: Mapping[str, object], expected: set[str], label: str) -> None:
    actual = set(payload)
    unknown = sorted(actual - expected)
    missing = sorted(expected - actual)
    if unknown:
        raise ValueError(f"unknown {label} fields: {', '.join(unknown)}")
    if missing:
        raise ValueError(f"missing {label} fields: {', '.join(missing)}")


def _string(payload: Mapping[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _sequence(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be an array")
    return value


def load_source_snapshot(payload: Mapping[str, object]) -> SourceSnapshot:
    """Validate and copy a strict non-authoritative source projection."""

    _exact_keys(payload, _TOP_LEVEL_KEYS, "top-level")
    if payload["schema_version"] != "pcp.repository_planner_source.v1":
        raise ValueError("schema_version is unsupported")
    if payload["authority"] != "NONE":
        raise ValueError("authority must be NONE")
    if payload["surface_class"] != "PROJECTION":
        raise ValueError("surface_class must be PROJECTION")
    if payload["is_proof"] is not False:
        raise ValueError("is_proof must be false")

    project_id = _string(payload, "project_id")
    observed_head = _string(payload, "observed_head")
    if _HEAD_RE.fullmatch(observed_head) is None:
        raise ValueError("observed_head must be a Git object id")
    fetched_at = _string(payload, "fetched_at")
    freshness = _string(payload, "freshness")
    if freshness not in {"CURRENT", "STALE", "UNKNOWN"}:
        raise ValueError("freshness is invalid")

    claims: list[Claim] = []
    seen_claims: set[str] = set()
    for index, raw_claim in enumerate(_sequence(payload["claims"], "claims")):
        claim = _mapping(raw_claim, f"claims[{index}]")
        _exact_keys(claim, _CLAIM_KEYS, f"claims[{index}]")
        source_sha256 = _string(claim, "source_sha256")
        if _SHA256_RE.fullmatch(source_sha256) is None:
            raise ValueError("source_sha256 must be 64 lowercase hex characters")
        materiality = _string(claim, "materiality")
        if materiality not in {"BLOCKING", "NON_BLOCKING"}:
            raise ValueError("materiality is invalid")
        claim_id = _string(claim, "claim_id")
        if claim_id in seen_claims:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        seen_claims.add(claim_id)
        source = SourceRef(
            locator=_string(claim, "source_locator"),
            sha256=source_sha256,
            observed_head=observed_head,
            fetched_at=fetched_at,
        )
        claims.append(
            Claim(
                claim_id=claim_id,
                project_id=project_id,
                lane_id=_string(claim, "lane_id"),
                field=_string(claim, "field"),
                value=_string(claim, "value"),
                materiality=materiality,
                freshness=freshness,
                transformation_id=_string(claim, "transformation_id"),
                source=source,
            )
        )

    lanes: list[LaneEvidence] = []
    seen_lanes: set[tuple[str, str]] = set()
    for index, raw_lane in enumerate(_sequence(payload["lanes"], "lanes")):
        lane = _mapping(raw_lane, f"lanes[{index}]")
        _exact_keys(lane, _LANE_KEYS, f"lanes[{index}]")
        candidate_sha = _string(lane, "candidate_sha")
        if _HEAD_RE.fullmatch(candidate_sha) is None:
            raise ValueError("candidate_sha must be a Git object id")
        dependencies: list[LaneDependency] = []
        for dependency_index, raw_dependency in enumerate(
            _sequence(lane["dependencies"], "dependencies")
        ):
            if not isinstance(raw_dependency, Mapping):
                raise ValueError("dependency must be an object")
            dependency = _mapping(
                raw_dependency,
                f"lanes[{index}].dependencies[{dependency_index}]",
            )
            _exact_keys(
                dependency,
                {"project_id", "lane_id", "candidate_sha"},
                f"lanes[{index}].dependencies[{dependency_index}]",
            )
            dependencies.append(
                LaneDependency(
                    project_id=_string(dependency, "project_id"),
                    lane_id=_string(dependency, "lane_id"),
                    candidate_sha=_string(dependency, "candidate_sha"),
                )
            )
        if len(dependencies) != len(set(dependencies)):
            raise ValueError("duplicate dependencies are not allowed")
        lane_id = _string(lane, "lane_id")
        lane_identity = (lane_id, candidate_sha)
        if lane_identity in seen_lanes:
            raise ValueError(f"duplicate lane: {lane_id}")
        seen_lanes.add(lane_identity)
        gate_status = _string(lane, "gate_status")
        if gate_status not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("gate_status is invalid")
        audit_status = _string(lane, "audit_status")
        if audit_status not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("audit_status is invalid")
        lanes.append(
            LaneEvidence(
                project_id=project_id,
                lane_id=lane_id,
                candidate_sha=candidate_sha,
                dependencies=tuple(dependencies),
                gate_status=gate_status,
                audit_status=audit_status,
                lifecycle_state=_string(lane, "lifecycle_state"),
            )
        )

    lane_ids = {lane.lane_id for lane in lanes}
    orphan_lanes = sorted({claim.lane_id for claim in claims} - lane_ids)
    if orphan_lanes:
        raise ValueError(f"claim references unknown lane: {', '.join(orphan_lanes)}")

    return SourceSnapshot(
        schema_version="pcp.repository_planner_source.v1",
        project_id=project_id,
        authority="NONE",
        surface_class="PROJECTION",
        is_proof=False,
        evidence_class=_string(payload, "evidence_class"),
        observed_head=observed_head,
        fetched_at=fetched_at,
        freshness=freshness,
        claims=tuple(claims),
        lanes=tuple(lanes),
    )
