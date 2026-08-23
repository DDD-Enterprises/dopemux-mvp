from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import asdict, replace
import json

from .conflicts import classify_conflicts
from .models import (
    LaneDependency,
    LaneProjection,
    PortfolioProjection,
    Recommendation,
    SourceSnapshot,
    utf8_key,
)

LaneKey = tuple[str, str, str]


def _lane_key(lane: LaneProjection) -> LaneKey:
    return (lane.project_id, lane.lane_id, lane.candidate_sha)


def _lane_sort_key(key: LaneKey) -> tuple[bytes, bytes, bytes]:
    return tuple(utf8_key(part) for part in key)  # type: ignore[return-value]


def _dependency_key(dependency: LaneDependency) -> LaneKey:
    return (
        dependency.project_id,
        dependency.lane_id,
        dependency.candidate_sha,
    )


def _lane_ref(key: LaneKey) -> str:
    return f"{key[0]}/{key[1]}@{key[2]}"


def _cycle_keys(edges: dict[LaneKey, set[LaneKey]]) -> set[LaneKey]:
    index = 0
    stack: list[LaneKey] = []
    on_stack: set[LaneKey] = set()
    indices: dict[LaneKey, int] = {}
    lowlinks: dict[LaneKey, int] = {}
    cycles: set[LaneKey] = set()

    def visit(node: LaneKey) -> None:
        nonlocal index
        indices[node] = lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for dependency in sorted(edges[node], key=_lane_sort_key):
            if dependency not in indices:
                visit(dependency)
                lowlinks[node] = min(lowlinks[node], lowlinks[dependency])
            elif dependency in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[dependency])
        if lowlinks[node] != indices[node]:
            return
        component: list[LaneKey] = []
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        if len(component) > 1 or node in edges[node]:
            cycles.update(component)

    for node in sorted(edges, key=_lane_sort_key):
        if node not in indices:
            visit(node)
    return cycles


def _ordered_lane_keys(
    lanes: dict[LaneKey, LaneProjection],
) -> tuple[tuple[LaneKey, ...], set[LaneKey]]:
    edges = {
        key: {
            _dependency_key(dependency)
            for dependency in lane.dependencies
            if _dependency_key(dependency) in lanes
        }
        for key, lane in lanes.items()
    }
    dependents: dict[LaneKey, set[LaneKey]] = defaultdict(set)
    indegree = {key: 0 for key in lanes}
    for key, dependencies in edges.items():
        for dependency in dependencies:
            if dependency != key:
                dependents[dependency].add(key)
                indegree[key] += 1

    ready = sorted(
        (key for key, degree in indegree.items() if degree == 0), key=_lane_sort_key
    )
    ordered: list[LaneKey] = []
    while ready:
        key = ready.pop(0)
        ordered.append(key)
        for dependent in sorted(dependents[key], key=_lane_sort_key):
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                ready.append(dependent)
                ready.sort(key=_lane_sort_key)

    remaining = set(lanes) - set(ordered)
    ordered.extend(sorted(remaining, key=_lane_sort_key))
    return tuple(ordered), _cycle_keys(edges)


def plan_merge_order(portfolio: PortfolioProjection) -> tuple[Recommendation, ...]:
    """Produce deterministic recommendations; never commands or authority."""

    lanes = {_lane_key(lane): lane for lane in portfolio.lanes}
    if len(lanes) != len(portfolio.lanes):
        raise ValueError("duplicate project/lane/candidate identity")
    ordered_keys, cycle_keys = _ordered_lane_keys(lanes)
    blocking_conflicts = {
        (conflict.project_id, conflict.lane_id)
        for conflict in portfolio.conflicts
        if conflict.status == "OPEN" and conflict.materiality == "BLOCKING"
    }
    results: dict[LaneKey, Recommendation] = {}

    for key in ordered_keys:
        lane = lanes[key]
        reasons: list[str] = []
        disposition = "READY_FOR_CONTROL_TOWER_REVIEW"
        if (lane.project_id, lane.lane_id) in blocking_conflicts:
            disposition = "DEFER_BLOCKING_CONFLICT"
            reasons.append("OPEN_BLOCKING_CONFLICT")
        elif lane.lifecycle_state == "REMOTE_COMMIT_ABSENT":
            disposition = "DEFER_FAILED_GATE"
            reasons.append("REMOTE_COMMIT_ABSENT")
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
            missing = sorted(
                (
                    _dependency_key(dependency)
                    for dependency in lane.dependencies
                    if _dependency_key(dependency) not in lanes
                ),
                key=_lane_sort_key,
            )
            if missing:
                disposition = "WAIT_DEPENDENCY"
                reasons.extend(
                    f"MISSING_DEPENDENCY:{_lane_ref(dep)}" for dep in missing
                )
            else:
                waiting = sorted(
                    (
                        _dependency_key(dependency)
                        for dependency in lane.dependencies
                        if _dependency_key(dependency) not in results
                        or results[_dependency_key(dependency)].disposition
                        != "READY_FOR_CONTROL_TOWER_REVIEW"
                    ),
                    key=_lane_sort_key,
                )
                if waiting:
                    disposition = "WAIT_DEPENDENCY"
                    reasons.extend(
                        f"DEPENDENCY_NOT_READY:{_lane_ref(candidate)}"
                        for candidate in waiting
                    )
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
        sorted(
            sources,
            key=lambda item: json.dumps(
                asdict(item),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8"),
        )
    )
    claims = tuple(claim for source in ordered_sources for claim in source.claims)
    lanes = tuple(
        sorted(
            (
                LaneProjection(
                    project_id=lane.project_id,
                    lane_id=lane.lane_id,
                    candidate_sha=lane.candidate_sha,
                    dependencies=tuple(
                        sorted(
                            lane.dependencies,
                            key=lambda item: _lane_sort_key(_dependency_key(item)),
                        )
                    ),
                    gate_status=lane.gate_status,
                    audit_status=lane.audit_status,
                    lifecycle_state=lane.lifecycle_state,
                    freshness=source.freshness,
                )
                for source in ordered_sources
                for lane in source.lanes
            ),
            key=lambda item: _lane_sort_key(_lane_key(item)),
        )
    )
    lane_keys = [_lane_key(lane) for lane in lanes]
    if len(lane_keys) != len(set(lane_keys)):
        raise ValueError("duplicate project/lane/candidate identity")
    base = PortfolioProjection(
        authority="NONE",
        surface_class="PROJECTION",
        is_proof=False,
        sources=ordered_sources,
        lanes=lanes,
        conflicts=classify_conflicts(claims),
    )
    return replace(base, recommendations=plan_merge_order(base))
