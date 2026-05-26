import ast
import json
from pathlib import Path

from click.testing import CliRunner

from src.dopemux.cli import cli


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
        "commit": {
            "message": "feat(orchestrator): add packet and proof validators",
            "allowlist": ["src/dopemux/orchestrator/validation/**"],
        },
        "pr": {
            "title": "feat(orchestrator): add packet and proof validators",
            "body": "Add read-only validators",
            "base": "main",
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
        "supporting_artifacts": [
            "tests/unit/test_cli_orchestrator_validation_commands.py"
        ],
        "chain_of_custody": {
            "documented": True,
            "source_version": "TP-DMX-ORCH-003",
            "created_at": "2026-05-26T00:00:00Z",
            "parent_bundle_ids": ["TP-DMX-ORCH-002"],
        },
        "warnings": [],
        "blockers": [],
    }


def test_orchestrator_validation_help_lists_packet_and_proof_commands() -> None:
    result = CliRunner().invoke(cli, ["orchestrator", "--help"])

    assert result.exit_code == 0, result.output
    assert "packet" in result.output
    assert "proof" in result.output
    assert "policy" in result.output


def test_orchestrator_packet_validate_outputs_json_report(tmp_path: Path) -> None:
    packet_path = _write_json(tmp_path / "packet.json", _packet_payload())

    result = CliRunner().invoke(
        cli,
        [
            "orchestrator",
            "packet",
            "validate",
            str(packet_path),
            "--json-output",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "task_packet"
    assert payload["status"] == "PASS"
    assert payload["valid"] is True
    assert payload["authority"] == "dopetask-canonical-spec"


def test_orchestrator_packet_validate_exits_nonzero_for_schema_error(
    tmp_path: Path,
) -> None:
    packet = _packet_payload()
    packet["undeclared"] = True
    packet_path = _write_json(tmp_path / "packet.json", packet)

    result = CliRunner().invoke(
        cli,
        ["orchestrator", "packet", "validate", str(packet_path)],
    )

    assert result.exit_code != 0
    assert "status: FAIL" in result.output
    assert "PACKET_SCHEMA_VIOLATION" in result.output


def test_orchestrator_proof_validate_outputs_json_report(tmp_path: Path) -> None:
    proof_path = _write_json(tmp_path / "proof.json", _proof_payload())

    result = CliRunner().invoke(
        cli,
        [
            "orchestrator",
            "proof",
            "validate",
            str(proof_path),
            "--json-output",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "proof_bundle"
    assert payload["status"] == "PASS"
    assert payload["valid"] is True
    assert payload["authority"] == "proof-bundle-governance"


def test_orchestrator_proof_validate_exits_nonzero_for_invalid_proof(
    tmp_path: Path,
) -> None:
    proof = _proof_payload()
    proof.pop("chain_of_custody")
    proof_path = _write_json(tmp_path / "proof.json", proof)

    result = CliRunner().invoke(
        cli,
        ["orchestrator", "proof", "validate", str(proof_path)],
    )

    assert result.exit_code != 0
    assert "status: FAIL" in result.output
    assert "PROOF_CHAIN_OF_CUSTODY_MISSING" in result.output


def test_orchestrator_validation_commands_do_not_execute_or_write() -> None:
    module_path = Path("src/dopemux/commands/orchestrator_commands.py")
    tree = ast.parse(module_path.read_text())

    forbidden = {
        "advance_item",
        "apply",
        "cancel",
        "checkout",
        "commit",
        "complete",
        "create",
        "delete",
        "execute",
        "open",
        "patch",
        "post",
        "put",
        "record",
        "remove",
        "run_packet",
        "start",
        "transition",
        "update",
        "write",
    }
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                called.add(func.id)
            elif isinstance(func, ast.Attribute):
                called.add(func.attr)

    assert called.isdisjoint(forbidden)


def test_orchestrator_policy_validate_outputs_json_report() -> None:
    result = CliRunner().invoke(
        cli,
        ["orchestrator", "policy", "validate", "--json-output"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "approval_policy"
    assert payload["status"] == "PASS"
    assert payload["valid"] is True
    assert payload["details"]["tier_count"] == 9


def test_orchestrator_policy_tiers_outputs_t4_gate() -> None:
    result = CliRunner().invoke(
        cli,
        ["orchestrator", "policy", "tiers", "--json-output"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["tiers"]["T4"]["approval_required"] is True
    assert payload["tiers"]["T4"]["receipt_required"] is True
    assert payload["tiers"]["TX"]["decision"] == "refuse"


def test_orchestrator_policy_classify_unknown_refuses() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "orchestrator",
            "policy",
            "classify",
            "orchestrator.future.unlisted",
            "--json-output",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["capability_id"] == "orchestrator.future.unlisted"
    assert payload["tier"] == "TU"
    assert payload["allowed"] is False
    assert payload["decision"] == "refuse"
