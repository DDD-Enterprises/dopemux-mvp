from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import replace

from .conflicts import classify_conflicts
from .models import LaneProjection, PortfolioProjection, Recommendation, SourceSnapshot


def _lane_key(project_id: str, lane_id: str) -> str:
    return f"{project_id}:{lane_id}"


def _ordered_lane_keys(lanes: dict[str, LaneProjection]) -> tuple[tuple[str, ...], set[str]]:
    dependents: dict[str, set[str]] = defaultdict(set)
    indegree = {key: 0 for key in lanes}
    for key, lane in lanes.items():
        for dependency in lane.dependencies:
            if dependency in lanes:
                dependents[dependency].add(key)
                indegree[key] += 1

    ready = sorted(key for key, degree in indegree.items() if degree == 0)
    ordered: list[str] = []
    while ready:
        key = ready.pop(0)
        ordered.append(key)
        for dependent in sorted(dependents[key]):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort()

    cycle_keys = set(lanes) - set(ordered)
    ordered.extend(sorted(cycle_keys))
    return tuple(ordered), cycle_keys


def plan_merge_order(portfolio: PortfolioProjection) -> tuple[Recommendation, ...]:
    """Produce deterministic recommendations; never commands or authority."""

    lanes = {
        _lane_key(lane.project_id, lane.lane_id): lane for lane in portfolio.lanes
    }
    ordered_keys, cycle_keys = _ordered_lane_keys(lanes)
    blocking_conflicts = {
        _lane_key(conflict.project_id, conflict.lane_id)
        for conflict in portfolio.conflicts
        if conflict.status == "OPEN" and conflict.materiality == "BLOCKING"
    }
    results: dict[str, Recommendation] = {}

    for key in ordered_keys:
        lane = lanes[key]
        reasons: list[str] = []
        disposition = "READY_FOR_CONTROL_TOWER_REVIEW"
        if key in blocking_conflicts:
            disposition = "DEFER_BLOCKING_CONFLICT"
            reasons.append("OPEN_BLOCKING_CONFLICT")
        elif lane.freshness == "STALE":
            disposition = "DEFER_STALE_EVIDENCE"
            reasons.append("STALE_EVIDENCE")
        elif lane.freshness == "UNKNOWN":
            disposition = "UNKNOWN"
            reasons.append("UNKNOWN_FRESHNESS")
        elif lane.gate_status == "FAIL" or lane.audit_status == "FAIL":
            disposition = "DEFER_FAILED_GATE"
            reasons.append("FAILED_GATE_OR_AUDIT")
        elif lane.gate_status == "UNKNOWN" or lane.audit_status == "UNKNOWN":
            disposition = "UNKNOWN"
            reasons.append("UNKNOWN_GATE_OR_AUDIT")
        elif key in cycle_keys:
            disposition = "WAIT_DEPENDENCY"
            reasons.append("DEPENDENCY_CYCLE")
        else:
            missing = sorted(dep for dep in lane.dependencies if dep not in lanes)
            if missing:
                disposition = "WAIT_DEPENDENCY"
                reasons.extend(f"MISSING_DEPENDENCY:{dep}" for dep in missing)
            else:
                waiting = sorted(
                    dep
                    for dep in lane.dependencies
                    if dep not in results
                    or results[dep].disposition != "READY_FOR_CONTROL_TOWER_REVIEW"
                )
                if waiting:
                    disposition = "WAIT_DEPENDENCY"
                    reasons.extend(f"DEPENDENCY_NOT_READY:{dep}" for dep in waiting)
        results[key] = Recommendation(
            project_id=lane.project_id,
            lane_id=lane.lane_id,
            candidate_sha=lane.candidate_sha,
            disposition=disposition,
            reasons=tuple(reasons),
        )
    return tuple(results[key] for key in ordered_keys)


def build_portfolio(sources: Sequence[SourceSnapshot]) -> PortfolioProjection:
    """Build a stable read model from immutable snapshots."""

    ordered_sources = tuple(
        sorted(sources, key=lambda item: (item.project_id, item.observed_head))
    )
    claims = tuple(claim for source in ordered_sources for claim in source.claims)
    lanes = tuple(
        sorted(
            (
                LaneProjection(
                    project_id=lane.project_id,
                    lane_id=lane.lane_id,
                    candidate_sha=lane.candidate_sha,
                    dependencies=tuple(sorted(lane.dependencies)),
                    gate_status=lane.gate_status,
                    audit_status=lane.audit_status,
                    lifecycle_state=lane.lifecycle_state,
                    freshness=source.freshness,
                )
                for source in ordered_sources
                for lane in source.lanes
            ),
            key=lambda item: (item.project_id, item.lane_id, item.candidate_sha),
        )
    )
    base = PortfolioProjection(
        authority="NONE",
        surface_class="PROJECTION",
        is_proof=False,
        sources=ordered_sources,
        lanes=lanes,
        conflicts=classify_conflicts(claims),
    )
    return replace(base, recommendations=plan_merge_order(base))
