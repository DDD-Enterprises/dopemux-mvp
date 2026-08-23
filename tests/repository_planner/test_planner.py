from __future__ import annotations

import json
import random
from dataclasses import replace
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from dopemux.repository_planner.canonical import canonical_portfolio_bytes
from dopemux.repository_planner.models import LaneEvidence
from dopemux.repository_planner.planner import build_portfolio, plan_merge_order
from dopemux.repository_planner.snapshot import load_source_snapshot

FIXTURE_ROOT = (
    Path(__file__).parents[1] / "fixtures" / "repository_planner" / "foundation"
)
PORTFOLIO_SCHEMA = (
    Path(__file__).parents[2]
    / "schemas"
    / "project_control_plane"
    / "repository_planner_portfolio.schema.json"
)


def _snapshots():
    return tuple(
        load_source_snapshot(
            json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))
        )
        for name in ("dopemux.json", "adops.json", "dnh_crm.json")
    )


def _by_lane(portfolio):
    return {item.lane_id: item for item in plan_merge_order(portfolio)}


def test_portfolio_is_byte_deterministic_under_source_reordering() -> None:
    snapshots = list(_snapshots())
    first = canonical_portfolio_bytes(build_portfolio(snapshots))
    random.Random(7).shuffle(snapshots)
    second = canonical_portfolio_bytes(build_portfolio(snapshots))
    assert first == second
    assert first.endswith(b"\n")


def test_equal_primary_source_keys_and_multiple_candidates_remain_deterministic() -> (
    None
):
    source = _snapshots()[0]
    left = replace(source, evidence_class="A", claims=(), lanes=())
    right = replace(source, evidence_class="Z", claims=(), lanes=())
    assert canonical_portfolio_bytes(
        build_portfolio((left, right))
    ) == canonical_portfolio_bytes(build_portfolio((right, left)))

    first = replace(source.lanes[0], candidate_sha="a" * 40)
    second = replace(source.lanes[0], candidate_sha="b" * 40)
    portfolio = build_portfolio((replace(source, lanes=(second, first), claims=()),))
    assert [item.candidate_sha for item in portfolio.recommendations] == [
        "a" * 40,
        "b" * 40,
    ]


def test_canonical_portfolio_validates_against_strict_schema() -> None:
    validator = Draft202012Validator(
        json.loads(PORTFOLIO_SCHEMA.read_text(encoding="utf-8"))
    )
    payload = json.loads(canonical_portfolio_bytes(build_portfolio(_snapshots())))
    validator.validate(payload)
    payload["lanes"][0]["unexpected"] = True
    assert any(
        error.validator == "additionalProperties"
        for error in validator.iter_errors(payload)
    )


def test_fail_closed_recommendations_preserve_source_states() -> None:
    snapshots = _snapshots()
    before = repr(snapshots)
    portfolio = build_portfolio(snapshots)
    recommendations = _by_lane(portfolio)

    assert (
        recommendations["pcp-planner-foundation"].disposition
        == "READY_FOR_CONTROL_TOWER_REVIEW"
    )
    assert (
        recommendations["legacy-corpus-rating-002"].disposition
        == "DEFER_BLOCKING_CONFLICT"
    )
    assert recommendations["rdcp-evidence-bridge"].disposition == "DEFER_STALE_EVIDENCE"
    assert repr(snapshots) == before


def test_missing_dependency_waits_instead_of_inventing_readiness() -> None:
    snapshot = _snapshots()[0]
    lane = replace(snapshot.lanes[0], dependencies=("missing:lane",))
    portfolio = build_portfolio((replace(snapshot, lanes=(lane,)),))
    result = plan_merge_order(portfolio)[0]
    assert result.disposition == "WAIT_DEPENDENCY"
    assert "MISSING_DEPENDENCY:missing:lane" in result.reasons


def test_failed_gate_and_missing_audit_withhold_readiness() -> None:
    source = _snapshots()[0]
    failed = replace(source.lanes[0], lane_id="failed", gate_status="FAIL")
    unknown = replace(source.lanes[0], lane_id="unknown", audit_status="UNKNOWN")
    results = _by_lane(
        build_portfolio((replace(source, lanes=(failed, unknown), claims=()),))
    )
    assert results["failed"].disposition == "DEFER_FAILED_GATE"
    assert results["unknown"].disposition == "UNKNOWN"


def test_remote_commit_absence_independently_withholds_readiness() -> None:
    source = _snapshots()[0]
    lane = replace(source.lanes[0], lifecycle_state="REMOTE_COMMIT_ABSENT")
    result = build_portfolio(
        (replace(source, lanes=(lane,), claims=()),)
    ).recommendations[0]
    assert result.disposition != "READY_FOR_CONTROL_TOWER_REVIEW"
    assert "REMOTE_COMMIT_ABSENT" in result.reasons


def test_canonical_boundary_rejects_authority_promotion() -> None:
    portfolio = build_portfolio(_snapshots())
    object.__setattr__(portfolio, "authority", "CONTROL_TOWER")
    with pytest.raises(ValueError, match="authority"):
        canonical_portfolio_bytes(portfolio)


def test_canonical_boundary_rejects_structurally_invalid_models() -> None:
    portfolio = build_portfolio(_snapshots())
    object.__setattr__(portfolio.lanes[0], "candidate_sha", "not-a-sha")
    with pytest.raises(ValueError, match="schema validation"):
        canonical_portfolio_bytes(portfolio)


def test_dependency_cycle_is_an_explicit_blocker_with_stable_order() -> None:
    source = _snapshots()[0]
    lanes = (
        LaneEvidence("alpha", "a", "a" * 40, ("beta:b",), "PASS", "PASS", "READY"),
        LaneEvidence("beta", "b", "b" * 40, ("alpha:a",), "PASS", "PASS", "READY"),
    )
    portfolio = build_portfolio(
        (replace(source, project_id="cycle", lanes=lanes, claims=()),)
    )
    results = plan_merge_order(portfolio)
    assert [(item.project_id, item.lane_id) for item in results] == [
        ("alpha", "a"),
        ("beta", "b"),
    ]
    assert all(item.disposition == "WAIT_DEPENDENCY" for item in results)
    assert all("DEPENDENCY_CYCLE" in item.reasons for item in results)


def test_cycle_diagnostic_does_not_mislabel_downstream_lane() -> None:
    source = _snapshots()[0]
    lanes = (
        LaneEvidence("alpha", "a", "a" * 40, ("beta:b",), "PASS", "PASS", "READY"),
        LaneEvidence("beta", "b", "b" * 40, ("alpha:a",), "PASS", "PASS", "READY"),
        LaneEvidence("gamma", "c", "c" * 40, ("alpha:a",), "PASS", "PASS", "READY"),
    )
    results = build_portfolio(
        (replace(source, project_id="cycle", lanes=lanes, claims=()),)
    ).recommendations
    by_lane = {item.lane_id: item for item in results}
    assert "DEPENDENCY_CYCLE" in by_lane["a"].reasons
    assert "DEPENDENCY_CYCLE" in by_lane["b"].reasons
    assert "DEPENDENCY_CYCLE" not in by_lane["c"].reasons
