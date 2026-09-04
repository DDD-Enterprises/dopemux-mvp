"""P1 ownership evidence: closed OWNED/FOREIGN/AMBIGUOUS/UNKNOWN evaluator.

Covers Task 5 of TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import jsonschema
import pytest

from dopemux.mcp.docker_inspect import inspect_container_mounts
from dopemux.mcp.ownership import (
    LeaseEvidence,
    ProbeEvidence,
    RegistryEvidence,
    StorageEvidence,
    evaluate_ownership,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "schemas/mcp/ownership-evidence.schema.json"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _validate(evidence) -> None:
    jsonschema.validate(evidence.to_schema_dict(), _schema())


def _verified_registry() -> RegistryEvidence:
    return RegistryEvidence(verified=True, project_id="prj_a", registry_generation=3)


def _verified_lease() -> LeaseEvidence:
    return LeaseEvidence(verified=True, lease_id="lease-1")


def _verified_probe(family: str = "conport") -> ProbeEvidence:
    return ProbeEvidence(verified=True, service_family=family)


def _verified_storage() -> StorageEvidence:
    return StorageEvidence(verified=True, evidence="project-bound mount")


# ---- exact-owned -----------------------------------------------------------


def test_exact_owned_all_four_verified():
    evidence = evaluate_ownership(
        registry=_verified_registry(),
        lease=_verified_lease(),
        probe=_verified_probe(),
        storage=_verified_storage(),
    )
    _validate(evidence)
    assert evidence.classification == "OWNED"
    assert evidence.mutation_eligible is True


def test_owned_requires_identifying_fields_populated():
    with pytest.raises(ValueError):
        evaluate_ownership(
            registry=RegistryEvidence(verified=True),  # no project_id/generation
            lease=_verified_lease(),
            probe=_verified_probe(),
            storage=_verified_storage(),
        )


# ---- foreign-port -----------------------------------------------------------


def test_foreign_expected_port_owner_is_foreign_never_adopted():
    evidence = evaluate_ownership(
        registry=RegistryEvidence(verified=False),
        lease=LeaseEvidence(verified=False),
        probe=_verified_probe(),
        storage=StorageEvidence(verified=False),
        label_status="WRONG_PROJECT",
    )
    _validate(evidence)
    assert evidence.classification == "FOREIGN"
    assert evidence.mutation_eligible is False


def test_foreign_wins_over_partial_evidence():
    """Even with three of four classes verified, an explicit WRONG_PROJECT
    label signal must still deny as FOREIGN, never AMBIGUOUS-toward-adopt."""

    evidence = evaluate_ownership(
        registry=_verified_registry(),
        lease=_verified_lease(),
        probe=_verified_probe(),
        storage=StorageEvidence(verified=False),
        label_status="WRONG_PROJECT",
    )
    _validate(evidence)
    assert evidence.classification == "FOREIGN"
    assert evidence.mutation_eligible is False


# ---- family-only (probe-only) -----------------------------------------------


def test_unlabeled_right_family_service_stays_unknown():
    evidence = evaluate_ownership(
        registry=RegistryEvidence(verified=False),
        lease=LeaseEvidence(verified=False),
        probe=_verified_probe("conport"),
        storage=StorageEvidence(verified=False),
        label_status="UNLABELED",
    )
    _validate(evidence)
    assert evidence.classification == "UNKNOWN"
    assert evidence.mutation_eligible is False


def test_no_evidence_at_all_is_unknown():
    evidence = evaluate_ownership(
        registry=RegistryEvidence(verified=False),
        lease=LeaseEvidence(verified=False),
        probe=ProbeEvidence(verified=False),
        storage=StorageEvidence(verified=False),
    )
    _validate(evidence)
    assert evidence.classification == "UNKNOWN"
    assert evidence.mutation_eligible is False


# ---- labels-only (compose/name circumstantial match) -----------------------


def test_labels_only_compose_match_is_ambiguous_not_owned():
    evidence = evaluate_ownership(
        registry=RegistryEvidence(verified=False),
        lease=LeaseEvidence(verified=False),
        probe=ProbeEvidence(verified=False),
        storage=StorageEvidence(verified=False),
        label_status="COMPOSE_MATCH",
    )
    _validate(evidence)
    assert evidence.classification == "AMBIGUOUS"
    assert evidence.mutation_eligible is False


# ---- wrong-storage -----------------------------------------------------------


def test_wrong_storage_denies_even_with_three_verified():
    evidence = evaluate_ownership(
        registry=_verified_registry(),
        lease=_verified_lease(),
        probe=_verified_probe(),
        storage=StorageEvidence(verified=False, evidence="foreign mount"),
    )
    _validate(evidence)
    assert evidence.classification == "AMBIGUOUS"
    assert evidence.mutation_eligible is False


@pytest.mark.parametrize("classification", ["FOREIGN", "AMBIGUOUS", "UNKNOWN"])
def test_non_owned_classifications_always_schema_valid(classification):
    """Every non-OWNED path emitted by evaluate_ownership must independently
    satisfy the schema's mutation_eligible=false constraint."""

    cases = {
        "FOREIGN": dict(
            registry=RegistryEvidence(verified=False),
            lease=LeaseEvidence(verified=False),
            probe=ProbeEvidence(verified=False),
            storage=StorageEvidence(verified=False),
            label_status="WRONG_PROJECT",
        ),
        "AMBIGUOUS": dict(
            registry=RegistryEvidence(verified=False),
            lease=LeaseEvidence(verified=False),
            probe=ProbeEvidence(verified=False),
            storage=StorageEvidence(verified=False),
            label_status="COMPOSE_MATCH",
        ),
        "UNKNOWN": dict(
            registry=RegistryEvidence(verified=False),
            lease=LeaseEvidence(verified=False),
            probe=ProbeEvidence(verified=False),
            storage=StorageEvidence(verified=False),
        ),
    }
    evidence = evaluate_ownership(**cases[classification])
    _validate(evidence)
    assert evidence.classification == classification
    assert evidence.mutation_eligible is False


# ---- docker_inspect: read-only mount extraction -----------------------------


def _fake_completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["docker"], returncode=returncode, stdout=stdout, stderr="")


def test_inspect_container_mounts_parses_source_destination():
    def runner(*args, **kwargs):
        return _fake_completed(
            json.dumps(
                [
                    {"Source": "/var/lib/dopemux/conport", "Destination": "/data"},
                    {"Source": "/var/lib/dopemux/conport", "Destination": "/data"},
                ]
            )
        )

    mounts = inspect_container_mounts("abc123", runner=runner)
    assert mounts == ["/var/lib/dopemux/conport:/data"]


def test_inspect_container_mounts_never_raises_on_docker_failure():
    def runner(*args, **kwargs):
        return _fake_completed("", returncode=1)

    assert inspect_container_mounts("abc123", runner=runner) == []


def test_inspect_container_mounts_never_raises_on_malformed_json():
    def runner(*args, **kwargs):
        return _fake_completed("not-json")

    assert inspect_container_mounts("abc123", runner=runner) == []


def test_inspect_container_mounts_never_invokes_mutating_docker_commands():
    seen_args: list = []

    def runner(cmd, **kwargs):
        seen_args.append(cmd)
        return _fake_completed("[]")

    inspect_container_mounts("abc123", runner=runner)
    assert len(seen_args) == 1
    assert seen_args[0][:2] == ["docker", "inspect"]
    forbidden = {"rm", "stop", "kill", "start", "run", "exec", "up", "down"}
    assert not (forbidden & set(seen_args[0]))
