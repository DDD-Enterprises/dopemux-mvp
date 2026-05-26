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
    assert "workflow" in result.output
    assert "hooks" in result.output
    assert "plugins" in result.output


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


def test_orchestrator_workflow_validate_outputs_json_report(tmp_path: Path) -> None:
    workflow_path = tmp_path / "workflow.yaml"
    workflow_path.write_text(
        "\n".join(
            [
                'schema_version: "1"',
                "id: daily-operator",
                "title: Daily operator workflow",
                "owner: dopemux",
                "authority:",
                "  primary_owner: task-orchestrator",
                "automation_tier: T1",
                "triggers:",
                "  - manual",
                "inputs:",
                "  - project_id",
                "steps:",
                "  - id: queue",
                "    tool: orchestrator.status.queue",
                "    mode: read",
                "    validation:",
                "      - queue report returned",
                "    on_failure: degrade",
                "outputs:",
                "  - items",
                "  - more_count",
                "  - next_token",
                "approval:",
                "  required: false",
            ]
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "orchestrator",
            "workflow",
            "validate",
            str(workflow_path),
            "--json-output",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "workflow_dsl"
    assert payload["status"] == "PASS"
    assert payload["valid"] is True
    assert payload["details"]["step_count"] == 1


def test_orchestrator_workflow_validate_exits_nonzero_for_invalid_workflow(
    tmp_path: Path,
) -> None:
    workflow_path = tmp_path / "workflow.yaml"
    workflow_path.write_text(
        "\n".join(
            [
                'schema_version: "1"',
                "id: daily-operator",
                "title: Daily operator workflow",
                "owner: dopemux",
                "authority: {}",
                "automation_tier: T1",
                "triggers:",
                "  - manual",
                "inputs:",
                "  - project_id",
                "steps:",
                "  - id: queue",
                "    tool: orchestrator.status.queue",
                "    mode: read",
                "    validation:",
                "      - queue report returned",
                "    on_failure: degrade",
                "outputs:",
                "  - items",
                "  - more_count",
                "  - next_token",
                "approval:",
                "  required: false",
            ]
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["orchestrator", "workflow", "validate", str(workflow_path)],
    )

    assert result.exit_code != 0
    assert "status: FAIL" in result.output
    assert "WORKFLOW_DSL_AUTHORITY_OWNER_MISSING" in result.output


def test_orchestrator_hooks_list_outputs_authority_hooks() -> None:
    result = CliRunner().invoke(
        cli,
        ["orchestrator", "hooks", "list", "--json-output"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["hook_count"] == 15
    assert payload["hooks"][0]["id"] == "on_startup"
    assert payload["hooks"][0]["tier"] == "T0"


def test_orchestrator_hooks_validate_outputs_json_report() -> None:
    result = CliRunner().invoke(
        cli,
        ["orchestrator", "hooks", "validate", "--json-output"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "plugin_hook_registry"
    assert payload["status"] == "PASS"
    assert payload["details"]["hook_count"] == 15


def test_orchestrator_hooks_validate_exits_nonzero_for_invalid_registry(
    tmp_path: Path,
) -> None:
    registry_path = tmp_path / "plugin_hooks.yaml"
    registry_path.write_text(
        "\n".join(
            [
                'schema_version: "1"',
                "id: task-orchestrator-plugin-hooks",
                "authority: docs/03-reference/systems/task-orchestrator/operator-integration-authority.md",
                "plugins: {}",
                "hooks:",
                "  - id: on_startup",
                "    trigger: startup",
                "    tier: T9000",
                "    automatic_allowed: true",
                "    approval_required: false",
                "    receipt_required: false",
                "    allowed_actions:",
                "      - orchestrator.status.queue",
                "    forbidden_actions:",
                "      - writes",
                "    failure_behavior: Degrade partial.",
                "    plugins: []",
            ]
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["orchestrator", "hooks", "validate", "--registry", str(registry_path)],
    )

    assert result.exit_code != 0
    assert "status: FAIL" in result.output
    assert "HOOK_REGISTRY_UNKNOWN_TIER" in result.output


def test_orchestrator_plugins_doctor_outputs_json_report() -> None:
    result = CliRunner().invoke(
        cli,
        ["orchestrator", "plugins", "doctor", "--json-output"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["kind"] == "plugin_hook_doctor"
    assert payload["status"] == "PASS"
    assert payload["details"]["read_only"] is True
