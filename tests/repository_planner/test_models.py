from __future__ import annotations

import copy
import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from dopemux.repository_planner.snapshot import load_source_snapshot


ROOT = Path(__file__).parents[2]
FIXTURE = ROOT / "tests" / "fixtures" / "repository_planner" / "foundation" / "dopemux.json"
SCHEMA = ROOT / "schemas" / "project_control_plane" / "repository_planner_source.schema.json"


def _payload() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_fixture_validates_and_loads_into_frozen_models() -> None:
    payload = _payload()
    Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(payload)

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
        (lambda payload: payload["claims"][0].update({"source_sha256": "bad"}), "sha256"),
        (lambda payload: payload["claims"][0].pop("source_locator"), "source_locator"),
        (lambda payload: payload["lanes"][0].update({"gate_status": "SKIPPED"}), "gate_status"),
        (lambda payload: payload["lanes"][0].update({"audit_status": "PENDING"}), "audit_status"),
        (lambda payload: payload["lanes"].append(copy.deepcopy(payload["lanes"][0])), "duplicate lane"),
        (lambda payload: payload["lanes"][0].update({"dependencies": ["a:b", "a:b"]}), "duplicate dependencies"),
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
