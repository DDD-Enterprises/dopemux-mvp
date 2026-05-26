import copy
from pathlib import Path

import yaml

from dopemux.orchestrator.policy import (
    REQUIRED_TIERS,
    classify_capability,
    load_approval_policy,
    validate_policy_file,
)


def _write_yaml(path: Path, payload: dict) -> Path:
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")
    return path


def test_default_policy_declares_required_tiers_and_gates() -> None:
    policy = load_approval_policy()

    assert list(policy.tiers) == REQUIRED_TIERS
    assert policy.tiers["T0"].automatic_allowed is True
    assert policy.tiers["T1"].automatic_allowed is True
    assert policy.tiers["T4"].approval_required is True
    assert policy.tiers["T4"].receipt_required is True
    assert policy.tiers["TX"].decision == "refuse"
    assert policy.tiers["TU"].decision == "refuse"


def test_default_policy_validates_successfully() -> None:
    report = validate_policy_file()

    assert report.valid is True
    assert report.status == "PASS"
    assert report.errors == []
    assert report.details["tier_count"] == len(REQUIRED_TIERS)
    assert report.details["capability_count"] >= 10


def test_capability_classification_is_fail_closed_for_unknown_ids() -> None:
    decision = classify_capability("orchestrator.future.unlisted")

    assert decision.capability_id == "orchestrator.future.unlisted"
    assert decision.tier == "TU"
    assert decision.allowed is False
    assert decision.decision == "refuse"
    assert "not registered" in decision.reason


def test_transition_apply_requires_t4_approval_and_receipt() -> None:
    decision = classify_capability("orchestrator.transition.apply")

    assert decision.tier == "T4"
    assert decision.mode == "write"
    assert decision.approval_required is True
    assert decision.receipt_required is True
    assert decision.canonical_writer == "task-orchestrator"
    assert decision.allowed is False


def test_policy_validator_rejects_t4_without_receipt(tmp_path: Path) -> None:
    policy = load_approval_policy().to_dict()
    invalid = copy.deepcopy(policy)
    invalid["capabilities"]["orchestrator.transition.apply"][
        "receipt_required"
    ] = False
    path = _write_yaml(tmp_path / "policy.yaml", invalid)

    report = validate_policy_file(path)

    assert report.valid is False
    assert report.status == "FAIL"
    assert any(error["code"] == "POLICY_T4_RECEIPT_REQUIRED" for error in report.errors)


def test_policy_validator_rejects_write_without_canonical_writer(
    tmp_path: Path,
) -> None:
    policy = load_approval_policy().to_dict()
    invalid = copy.deepcopy(policy)
    invalid["capabilities"]["orchestrator.transition.apply"][
        "canonical_writer"
    ] = ""
    path = _write_yaml(tmp_path / "policy.yaml", invalid)

    report = validate_policy_file(path)

    assert report.valid is False
    assert any(error["code"] == "POLICY_WRITE_CANONICAL_WRITER_REQUIRED" for error in report.errors)
