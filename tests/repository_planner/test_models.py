from __future__ import annotations

import copy
import dataclasses
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from dopemux.repository_planner.models import SourceSnapshot
from dopemux.repository_planner.snapshot import load_source_snapshot

ROOT = Path(__file__).parents[2]
FIXTURE = (
    ROOT / "tests" / "fixtures" / "repository_planner" / "foundation" / "dopemux.json"
)
SCHEMA = (
    ROOT / "schemas" / "project_control_plane" / "repository_planner_source.schema.json"
)


def _payload() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_validates_and_loads_into_frozen_models() -> None:
    payload = _payload()
    Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(
        payload
    )

    snapshot = load_source_snapshot(payload)

    assert snapshot.project_id == "dopemux-mvp"
    assert snapshot.authority == "NONE"
    assert snapshot.surface_class == "PROJECTION"
    assert snapshot.is_proof is False
    assert isinstance(snapshot.claims, tuple)
    assert isinstance(snapshot.lanes, tuple)
    with pytest.raises(FrozenInstanceError):
        snapshot.project_id = "mutated"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda payload: payload.update({"unexpected": True}), "unknown top-level"),
        (lambda payload: payload.update({"authority": "CONTROL_TOWER"}), "authority"),
        (
            lambda payload: payload["claims"][0].update({"source_sha256": "bad"}),
            "sha256",
        ),
        (lambda payload: payload["claims"][0].pop("source_locator"), "source_locator"),
        (
            lambda payload: payload["claims"][0].pop("transformation_id"),
            "transformation_id",
        ),
        (
            lambda payload: payload["lanes"][0].update({"gate_status": "SKIPPED"}),
            "gate_status",
        ),
        (
            lambda payload: payload["lanes"][0].update({"audit_status": "PENDING"}),
            "audit_status",
        ),
        (
            lambda payload: payload["lanes"].append(copy.deepcopy(payload["lanes"][0])),
            "duplicate lane",
        ),
        (
            lambda payload: payload["lanes"][0].update(
                {
                    "dependencies": [
                        {
                            "project_id": "a",
                            "lane_id": "b",
                            "candidate_sha": "a" * 40,
                        },
                        {
                            "project_id": "a",
                            "lane_id": "b",
                            "candidate_sha": "a" * 40,
                        },
                    ]
                }
            ),
            "duplicate dependencies",
        ),
        (lambda payload: payload.update({"fetched_at": "not-a-dateZ"}), "fetched_at"),
        (
            lambda payload: payload["claims"].append(
                copy.deepcopy(payload["claims"][0])
            ),
            "duplicate claim_id",
        ),
        (
            lambda payload: payload["claims"][0].update({"lane_id": "missing-lane"}),
            "unknown lane",
        ),
    ],
)
def test_loader_fails_closed_on_invalid_payload(mutation, message: str) -> None:
    payload = _payload()
    mutation(payload)
    with pytest.raises(ValueError, match=message):
        load_source_snapshot(payload)


def test_loader_does_not_mutate_input() -> None:
    payload = _payload()
    before = copy.deepcopy(payload)
    load_source_snapshot(payload)
    assert payload == before


def test_lifecycle_facts_are_not_recommendations() -> None:
    snapshot = load_source_snapshot(_payload())
    lane = snapshot.lanes[0]
    assert lane.lifecycle_state == "DESIGN_ACCEPTED"
    assert not hasattr(lane, "recommendation")
    assert snapshot.claims[0].transformation_id == "fixture-projection.v1"


def test_direct_source_model_cannot_promote_authority() -> None:
    snapshot = load_source_snapshot(_payload())
    with pytest.raises(ValueError, match="authority"):
        dataclasses.replace(snapshot, authority="CONTROL_TOWER")


@pytest.mark.parametrize(
    "fetched_at",
    [
        "2026-08-23 00:00:00Z",
        "20260823T000000Z",
        "2026-08-23T00:00Z",
        "2026-W34-7T00:00:00Z",
        "2026-08-23T00:00:00+00:00",
        "2026-02-30T00:00:00Z",
    ],
)
def test_loader_requires_canonical_rfc3339_utc(fetched_at: str) -> None:
    payload = _payload()
    payload["fetched_at"] = fetched_at
    with pytest.raises(ValueError, match="RFC 3339 UTC"):
        load_source_snapshot(payload)


def test_direct_source_construction_revalidates_complete_contract() -> None:
    snapshot = load_source_snapshot(_payload())
    with pytest.raises(ValueError, match="RFC 3339 UTC"):
        dataclasses.replace(snapshot, fetched_at="2026-08-23 00:00:00Z")
    with pytest.raises(ValueError, match="duplicate claim_id"):
        dataclasses.replace(snapshot, claims=(snapshot.claims[0], snapshot.claims[0]))
    with pytest.raises(ValueError, match="unknown lane"):
        dataclasses.replace(
            snapshot,
            claims=(dataclasses.replace(snapshot.claims[0], lane_id="absent"),),
        )
    assert isinstance(snapshot, SourceSnapshot)


def test_dependency_contract_is_structured_and_candidate_complete() -> None:
    payload = _payload()
    payload["lanes"][0]["dependencies"] = ["ambiguous:reference"]
    with pytest.raises(ValueError, match="dependency.*object"):
        load_source_snapshot(payload)

    payload = _payload()
    payload["lanes"][0]["dependencies"] = [
        {"project_id": "project", "lane_id": "lane", "candidate_sha": "bad"}
    ]
    with pytest.raises(ValueError, match="candidate_sha"):
        load_source_snapshot(payload)
