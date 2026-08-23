from __future__ import annotations

import json
import random
from pathlib import Path

from dopemux.repository_planner.conflicts import classify_conflicts
from dopemux.repository_planner.snapshot import load_source_snapshot

FIXTURE_ROOT = (
    Path(__file__).parents[1] / "fixtures" / "repository_planner" / "foundation"
)


def _snapshot(name: str):
    return load_source_snapshot(
        json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))
    )


def test_blocking_source_disagreement_is_visible_and_stable() -> None:
    claims = list(_snapshot("adops.json").claims)
    expected = classify_conflicts(claims)
    random.Random(42).shuffle(claims)

    assert classify_conflicts(claims) == expected
    assert len(expected) == 1
    conflict = expected[0]
    assert conflict.field == "acceptance_state"
    assert conflict.values == ("DRAFT_NOT_ACCEPTED", "FINALITY_EVIDENCE_PRESENT")
    assert conflict.materiality == "BLOCKING"
    assert conflict.status == "OPEN"
    assert conflict.resolution_authority == "SOURCE_REPOSITORY"


def test_identical_claim_values_do_not_create_conflict() -> None:
    claim = _snapshot("dopemux.json").claims[0]
    assert classify_conflicts([claim, claim]) == ()
