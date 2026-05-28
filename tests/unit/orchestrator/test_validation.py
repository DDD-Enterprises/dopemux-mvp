import json
from pathlib import Path

from dopemux.orchestrator.validation.packets import validate_packet_file
from dopemux.orchestrator.validation.proof import validate_proof_file


SCHEMA_PATH = Path("docs/03-reference/spec/dopetask/dopetask-canonical-spec.json")


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _packet_payload() -> dict:
    return {
        "id": "TP-DMX-ORCH-003",
        "project": "dopemux-mvp",
        "target": "Add validators",
        "repo_binding": {
            "project_id": "DDD-Enterprises/dopemux-mvp",
            "repo_marker": ".dopetaskroot",
            "require_identity_match": True,
        },
        "series": {
            "id": "DMX-ORCH-INTEGRATION",
            "base_branch": "main",
            "parent_tp_id": "TP-DMX-ORCH-002",
            "final_packet": False,
        },
        "execution": {
            "agent": "codex",
            "branch": "codex/tp-dmx-orch-003-validators",
        },
        "commit": {
            "message": "feat(orchestrator): add packet and proof validators",
            "allowlist": ["src/dopemux/orchestrator/validation/**"],
            "verify": ["python -m pytest -q tests/unit/orchestrator"],
        },
        "pr": {
            "title": "feat(orchestrator): add packet and proof validators",
            "body": "Add read-only validators",
            "base": "main",
        },
        "pal_chain": {
            "enabled": True,
            "steps": ["analyze", "planner", "codereview", "precommit"],
        },
        "steps": [
            {
                "id": "validate",
                "task": "Validate packet",
                "validation": ["schema validation exits 0"],
            }
        ],
    }


def _proof_payload() -> dict:
    return {
        "bundle_id": "TP-DMX-ORCH-003-PROOF",
        "run_id": "tp-dmx-orch-003-local",
        "skill": "codex",
        "status": "READY_FOR_REVIEW",
        "validation_state": "PASSED",
        "created_at": "2026-05-26T00:00:00Z",
        "manifest": {
            "bundle_id": "TP-DMX-ORCH-003-PROOF",
            "packet_id": "TP-DMX-ORCH-003",
            "generated_artifacts": [
                "task-packets/generated/TP-DMX-ORCH-003.json",
                "proof/dmx-orch-integration/TP-DMX-ORCH-003/PROOF.json",
            ],
        },
        "authoritative_artifacts": [
            "task-packets/generated/TP-DMX-ORCH-003.json",
            "proof/dmx-orch-integration/TP-DMX-ORCH-003/PROOF.json",
        ],
        "supporting_artifacts": ["tests/unit/orchestrator/test_validation.py"],
        "chain_of_custody": {
            "documented": True,
            "source_version": "TP-DMX-ORCH-003",
            "created_at": "2026-05-26T00:00:00Z",
            "parent_bundle_ids": ["TP-DMX-ORCH-002"],
        },
        "warnings": [],
        "blockers": [],
    }


def test_packet_validator_accepts_schema_valid_packet(tmp_path: Path) -> None:
    packet_path = _write_json(tmp_path / "packet.json", _packet_payload())

    report = validate_packet_file(
        packet_path,
        schema_path=SCHEMA_PATH,
    )

    assert report.valid is True
    assert report.status == "PASS"
    assert report.exit_code == 0
    assert report.errors == []


def test_packet_validator_rejects_schema_violation(tmp_path: Path) -> None:
    packet = _packet_payload()
    packet["undeclared"] = True
    packet_path = _write_json(tmp_path / "packet.json", packet)

    report = validate_packet_file(
        packet_path,
        schema_path=SCHEMA_PATH,
    )

    assert report.valid is False
    assert report.status == "FAIL"
    assert report.exit_code != 0
    assert any(error["code"] == "PACKET_SCHEMA_VIOLATION" for error in report.errors)


def test_packet_validator_missing_schema_fails_closed(tmp_path: Path) -> None:
    packet_path = _write_json(tmp_path / "packet.json", _packet_payload())

    report = validate_packet_file(
        packet_path,
        schema_path=tmp_path / "missing-schema.json",
    )

    assert report.valid is False
    assert report.status == "UNKNOWN"
    assert report.exit_code != 0
    assert report.errors == [
        {
            "code": "REQUIRES_REPO_INSPECTION",
            "message": (
                f"Packet schema path is missing: {tmp_path / 'missing-schema.json'}"
            ),
            "path": "",
            "severity": "error",
        }
    ]


def test_proof_validator_accepts_minimal_governance_bundle(tmp_path: Path) -> None:
    proof_path = _write_json(tmp_path / "proof.json", _proof_payload())

    report = validate_proof_file(proof_path)

    assert report.valid is True
    assert report.status == "PASS"
    assert report.exit_code == 0
    assert report.errors == []


def test_proof_validator_requires_manifest(tmp_path: Path) -> None:
    proof = _proof_payload()
    proof.pop("manifest")
    proof_path = _write_json(tmp_path / "proof.json", proof)

    report = validate_proof_file(proof_path)

    assert report.valid is False
    assert report.status == "FAIL"
    assert any(error["code"] == "PROOF_MANIFEST_MISSING" for error in report.errors)


def test_proof_validator_requires_chain_of_custody(tmp_path: Path) -> None:
    proof = _proof_payload()
    proof.pop("chain_of_custody")
    proof_path = _write_json(tmp_path / "proof.json", proof)

    report = validate_proof_file(proof_path)

    assert report.valid is False
    assert report.status == "FAIL"
    assert any(
        error["code"] == "PROOF_CHAIN_OF_CUSTODY_MISSING"
        for error in report.errors
    )


def test_proof_validator_rejects_invalid_status(tmp_path: Path) -> None:
    proof = _proof_payload()
    proof["status"] = "DONE"
    proof_path = _write_json(tmp_path / "proof.json", proof)

    report = validate_proof_file(proof_path)

    assert report.valid is False
    assert any(error["code"] == "PROOF_STATUS_INVALID" for error in report.errors)


def test_proof_validator_requires_artifact_backing_for_warnings(tmp_path: Path) -> None:
    proof = _proof_payload()
    proof["warnings"] = ["static validation only"]
    proof["supporting_artifacts"] = []
    proof_path = _write_json(tmp_path / "proof.json", proof)

    report = validate_proof_file(proof_path)

    assert report.valid is False
    assert any(
        error["code"] == "PROOF_WARNING_OR_BLOCKER_ARTIFACT_MISSING"
        for error in report.errors
    )


def test_proof_validator_rejects_empty_string_supporting_artifacts(tmp_path: Path) -> None:
    proof = _proof_payload()
    proof["warnings"] = ["static validation only"]
    proof["supporting_artifacts"] = [""]
    proof_path = _write_json(tmp_path / "proof.json", proof)

    report = validate_proof_file(proof_path)

    assert report.valid is False
    assert any(
        error["code"] == "PROOF_SUPPORTING_ARTIFACTS_INVALID"
        for error in report.errors
    )
