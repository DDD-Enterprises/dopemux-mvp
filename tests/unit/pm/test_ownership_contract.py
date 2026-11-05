"""Independent v2 serialization and strict-ingress examples."""

import importlib
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def contract():
    assert importlib.util.find_spec("dopemux.pm.ownership"), "v2 contract is unavailable"
    return importlib.import_module("dopemux.pm.ownership")


@pytest.fixture
def vectors():
    return json.loads(
        (Path(__file__).parents[3] / "schemas/pm/ownership-v2/vectors.json").read_text()
    )


def test_pinned_bytes(contract, vectors):
    c = contract
    assert (
        c.command_digest(vectors["command"], **vectors["trusted_context_fixture"])
        == vectors["request_sha256"]
    )
    assert c.new_task_id(vectors["identity_tuple"]) == vectors["proposed_new_task_id"]
    assert (
        c.canonical_json({"\U00010000": "astral", "\ue000": "bmp"}).hex()
        == vectors["unicode_vector"]["canonical_hex"]
    )
    changed = dict(vectors["identity_tuple"], project_id="other")
    assert c.new_task_id(changed) != vectors["proposed_new_task_id"]
    changed = dict(vectors["identity_tuple"], source_instance_id="other")
    assert c.new_task_id(changed) != vectors["proposed_new_task_id"]


@pytest.mark.parametrize("raw", ['{"a":1,"a":2}', '{"a":NaN}', "[]", '{"a":"\\ud800"}'])
def test_ambiguous_json_rejected(contract, raw):
    with pytest.raises(ValueError):
        contract.parse_json_object(raw)


@pytest.mark.parametrize(
    "field,value",
    [
        ("expected_version", True),
        ("expected_version", 1.0),
        ("expected_version", "1"),
        ("task_id", " x"),
        ("actor", "admin"),
        ("reason", "\ud800"),
        ("idempotency_key", " x"),
        ("admission_epoch", 0),
    ],
)
def test_strict_command(contract, vectors, field, value):
    body = dict(vectors["command"], **{field: value})
    with pytest.raises(ValueError):
        contract.TransitionCommand.model_validate(body)


def test_required_fields_and_explicit_resume(contract, vectors):
    body = dict(vectors["command"])
    del body["reason"]
    with pytest.raises(ValueError):
        contract.TransitionCommand.model_validate(body)
    body = dict(vectors["command"], transition="resume", reason=" ")
    with pytest.raises(ValueError):
        contract.TransitionCommand.model_validate(body)
    body.update(reason="Unblocked")
    assert contract.TransitionCommand.model_validate(body).transition == "resume"


def test_receipt_relations_and_detachment(contract, vectors):
    ctx = {k: v for k, v in vectors["trusted_context_fixture"].items() if k != "operation_kind"}
    original = vectors["receipt"]
    result = contract.validate_receipt(original, vectors["command"], **ctx)
    assert result == original and result is not original
    for patch in (
        {"project_id": "foreign"},
        {"version_after": 9},
        {"to_status": "DONE"},
        {"outcome": "illegal"},
        {"request_sha256": "0" * 64},
    ):
        with pytest.raises(ValueError):
            contract.validate_receipt(dict(original, **patch), vectors["command"], **ctx)


def test_creation_identity_and_protected_fields(contract, vectors):
    body = dict(
        schema_version="dopemux.pm.create-command.v1",
        idempotency_key="create",
        admission_epoch=1,
        identity=vectors["identity_tuple"],
        title="Task",
        description=None,
        dependencies=[],
        linked_ids={},
        completion_policy_id="kernel-v1",
    )
    assert contract.CreateTaskCommand.model_validate(body).title == "Task"
    for patch in (
        {"meta": {"project_id": "x"}},
        {"dependencies": ["b", "a"]},
        {"dependencies": ["a", "a"]},
        {"binding_version": 3},
    ):
        with pytest.raises(ValueError):
            contract.CreateTaskCommand.model_validate(dict(body, **patch))


def test_done_receipt_binds_the_requested_snapshot(contract, vectors):
    context = {k: v for k, v in vectors["trusted_context_fixture"].items() if k != "operation_kind"}
    command = dict(
        vectors["command"],
        transition="done",
        reason="Verified completion",
        completion_evidence_ref={"id": "sealed", "sha256": "1" * 64},
    )
    receipt = dict(
        vectors["receipt"],
        from_status="IN_PROGRESS",
        to_status="DONE",
        request_sha256=contract.command_digest(
            command, **context, operation_kind="task.transition"
        ),
        completion_verification={
            "policy_id": "kernel-v1",
            "policy_version": 1,
            "snapshot_sha256": "2" * 64,
            "gate_scope": "workflow-kernel:task-evidence-shape",
        },
    )
    with pytest.raises(ValueError, match="snapshot"):
        contract.validate_receipt(receipt, command, **context)
    receipt["completion_verification"]["snapshot_sha256"] = "1" * 64
    assert contract.validate_receipt(receipt, command, **context) == receipt
