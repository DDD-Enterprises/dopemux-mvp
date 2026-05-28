import json
from pathlib import Path

from click.testing import CliRunner

from dopemux.orchestrator.operator_workflows import (
    approve_phrase,
    automation_pilot_decision,
    build_dashboard_snapshot,
    build_packet_draft,
    build_pr_queue,
    context_refresh_plan,
    context_status,
    final_readiness_report,
    memory_route_receipt,
    pr_comment_plan,
    transition_apply_plan,
    transition_preview,
    validate_transition_proof_envelope_file,
)
from src.dopemux.cli import cli


def _packet_payload() -> dict:
    return {
        "id": "TP-DMX-ORCH-TEST",
        "project": "dopemux-mvp",
        "target": "Test packet",
        "repo_binding": {
            "project_id": "DDD-Enterprises/dopemux-mvp",
            "repo_marker": ".dopetaskroot",
            "require_identity_match": True,
        },
        "series": {
            "id": "DMX-ORCH-INTEGRATION",
            "base_branch": "main",
            "parent_tp_id": None,
            "final_packet": False,
        },
        "commit": {
            "message": "test: packet",
            "allowlist": ["tests/**"],
        },
        "pr": {
            "title": "test: packet",
            "body": "Test packet",
            "base": "main",
        },
        "steps": [
            {
                "id": "validate",
                "task": "Validate",
                "validation": ["validator exits 0"],
            }
        ],
    }


def _proof_payload() -> dict:
    return {
        "bundle_id": "TP-DMX-ORCH-TEST-PROOF",
        "run_id": "test",
        "skill": "codex",
        "status": "READY_FOR_REVIEW",
        "validation_state": "PASSED",
        "manifest": {
            "bundle_id": "TP-DMX-ORCH-TEST-PROOF",
            "packet_id": "TP-DMX-ORCH-TEST",
            "generated_artifacts": ["task-packets/generated/TP-DMX-ORCH-TEST.json"],
        },
        "authoritative_artifacts": ["task-packets/generated/TP-DMX-ORCH-TEST.json"],
        "supporting_artifacts": ["tests/unit/orchestrator/test_operator_workflows.py"],
        "chain_of_custody": {
            "documented": True,
            "source_version": "TP-DMX-ORCH-TEST",
            "created_at": "2026-05-26T00:00:00Z",
            "parent_bundle_ids": [],
        },
        "warnings": [],
        "blockers": [],
    }


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def test_context_status_is_read_only_and_partial() -> None:
    report = context_status(
        changed_files=["src/dopemux/example.py"],
        stale_sources=["dope-context"],
    )

    assert report["read_only"] is True
    assert report["status"] == "STALE"
    assert report["sources"]["dope-context"]["fresh"] is False
    assert report["changed_file_count"] == 1


def test_context_refresh_plan_blocks_without_exact_approval() -> None:
    plan = context_refresh_plan(scope="repo", proof_id="proof-1")

    assert plan["decision"] == "blocked"
    assert plan["tier"] == "T4"
    assert plan["will_write"] is False
    assert "I AUTHORIZE" in plan["required_phrase"]


def test_memory_route_receipt_never_uses_task_orchestrator_as_owner() -> None:
    receipt = memory_route_receipt(
        kind="progress",
        content="Implementation reached review",
        proof_id="proof-1",
    )

    assert receipt["canonical_writer"] == "ConPort"
    assert receipt["mirror_writer"] == "dope-memory"
    assert receipt["task_orchestrator_role"] == "observe_route_only"
    assert receipt["will_write"] is False


def test_packet_forge_builds_draft_only_packet() -> None:
    draft = build_packet_draft(
        packet_id="TP-DMX-ORCH-DRAFT",
        target="Draft next packet",
    )

    assert draft["status"] == "DRAFT_ONLY"
    assert draft["packet"]["id"] == "TP-DMX-ORCH-DRAFT"
    assert draft["will_write"] is False
    assert draft["packet"]["commit"]["allowlist"] == ["UNKNOWN_UNTIL_REVIEW"]


def test_intake_and_audit_cli_validate_packet_and_proof(tmp_path: Path) -> None:
    packet = _write_json(tmp_path / "packet.json", _packet_payload())
    proof = _write_json(tmp_path / "proof.json", _proof_payload())

    result = CliRunner().invoke(
        cli,
        [
            "orchestrator",
            "intake",
            "--packet",
            str(packet),
            "--proof",
            str(proof),
            "--json-output",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["verdict"] == "PASS"
    assert payload["will_accept"] is False


def test_transition_apply_requires_typed_approval() -> None:
    preview = transition_preview(
        workflow_id="wf-1",
        transition="start",
        proof_id="proof-1",
    )
    plan = transition_apply_plan(
        workflow_id="wf-1",
        transition="start",
        idempotency_key="idem-1",
        proof_id="proof-1",
        approval_phrase="wrong",
    )

    assert preview["tier"] == "T1"
    assert plan["decision"] == "blocked"
    assert plan["will_write"] is False
    assert plan["canonical_writer"] == "task-orchestrator"


def test_transition_proof_envelope_validator_rejects_missing_receipt(
    tmp_path: Path,
) -> None:
    envelope = {
        "schema_version": "1",
        "workflow_id": "wf-1",
        "transition": "start",
        "idempotency_key": "idem-1",
        "actor": "operator",
        "canonical_writer": "task-orchestrator",
    }
    path = _write_json(tmp_path / "envelope.json", envelope)

    report = validate_transition_proof_envelope_file(path)

    assert report.valid is False
    assert any(
        error["code"] == "TRANSITION_PROOF_RECEIPT_MISSING"
        for error in report.errors
    )


def test_pr_comment_plan_is_t5_and_gated() -> None:
    plan = pr_comment_plan(pr_number=123, body="Ready", proof_id="proof-1")
    queue = build_pr_queue(
        [{"number": 123, "checks": "passing", "proof": "present"}]
    )

    assert plan["tier"] == "T5"
    assert plan["decision"] == "blocked"
    assert plan["will_write"] is False
    assert queue["items"][0]["readiness"] == "merge_candidate"


def test_dashboard_and_automation_pilot_are_read_first() -> None:
    dashboard = build_dashboard_snapshot()
    t1 = automation_pilot_decision("orchestrator.hooks.validate")
    t4 = automation_pilot_decision("orchestrator.transition.apply")

    assert dashboard["read_only"] is True
    assert [panel["id"] for panel in dashboard["panels"]] == [
        "today",
        "authority",
        "packets",
        "proof",
        "risks",
        "pr_queue",
        "context",
        "do_not_touch",
    ]
    assert t1["decision"] == "allow"
    assert t4["decision"] == "blocked"


def test_final_readiness_requires_proof_and_acceptance(tmp_path: Path) -> None:
    proof = _write_json(tmp_path / "proof.json", _proof_payload())

    report = final_readiness_report(proof_path=proof)

    assert report["proof"]["status"] == "PASS"
    assert report["acceptance"]["status"] == "UNKNOWN"
    assert report["ready_for_merge"] is False


def test_context_refresh_cli_accepts_exact_phrase() -> None:
    phrase = approve_phrase(
        operation="context refresh repo",
        resource="dopemux-mvp",
        writer="dope-context",
        proof_id="proof-1",
    )

    result = CliRunner().invoke(
        cli,
        [
            "orchestrator",
            "context",
            "refresh",
            "--scope",
            "repo",
            "--proof-id",
            "proof-1",
            "--approval-phrase",
            phrase,
            "--json-output",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "ready_for_canonical_writer"
    assert payload["will_write"] is False


def test_remaining_operator_workflow_cli_surfaces(tmp_path: Path) -> None:
    packet = _write_json(tmp_path / "packet.json", _packet_payload())
    proof = _write_json(tmp_path / "proof.json", _proof_payload())
    envelope = _write_json(
        tmp_path / "envelope.json",
        {
            "schema_version": "1",
            "workflow_id": "wf-1",
            "transition": "start",
            "idempotency_key": "idem-1",
            "actor": "operator",
            "canonical_writer": "task-orchestrator",
            "receipt": {
                "proof_id": "proof-1",
                "operation": "workflow transition start",
                "status": "accepted",
            },
        },
    )

    cases = [
        (
            [
                "orchestrator",
                "memory",
                "route",
                "--kind",
                "decision",
                "--content",
                "Use canonical writer",
                "--proof-id",
                "proof-1",
                "--json-output",
            ],
            ("canonical_writer", "ConPort"),
        ),
        (
            [
                "orchestrator",
                "forge",
                "packet",
                "--packet-id",
                "TP-DMX-ORCH-DRAFT",
                "--target",
                "Draft next packet",
                "--json-output",
            ],
            ("status", "DRAFT_ONLY"),
        ),
        (
            [
                "orchestrator",
                "audit",
                "--packet",
                str(packet),
                "--proof",
                str(proof),
                "--json-output",
            ],
            ("verdict", "PASS"),
        ),
        (
            [
                "orchestrator",
                "transition",
                "preview",
                "--workflow-id",
                "wf-1",
                "--transition-name",
                "start",
                "--proof-id",
                "proof-1",
                "--json-output",
            ],
            ("tier", "T1"),
        ),
        (
            [
                "orchestrator",
                "transition",
                "proof",
                "validate",
                str(envelope),
                "--json-output",
            ],
            ("status", "PASS"),
        ),
        (
            [
                "orchestrator",
                "pr",
                "queue",
                "--pr",
                "123:passing:present",
                "--json-output",
            ],
            ("kind", "pr_queue"),
        ),
        (
            [
                "orchestrator",
                "pr",
                "comment",
                "--pr-number",
                "123",
                "--body",
                "Ready",
                "--proof-id",
                "proof-1",
                "--json-output",
            ],
            ("tier", "T5"),
        ),
        (
            ["orchestrator", "dashboard", "snapshot", "--json-output"],
            ("read_only", True),
        ),
        (
            [
                "orchestrator",
                "automation",
                "pilot",
                "orchestrator.hooks.validate",
                "--json-output",
            ],
            ("decision", "allow"),
        ),
        (
            ["orchestrator", "dangerous", "check", "--json-output"],
            ("kind", "dangerous_check"),
        ),
        (
            [
                "orchestrator",
                "final",
                "proof",
                "--proof",
                str(proof),
                "--json-output",
            ],
            ("ready_for_merge", False),
        ),
    ]

    for args, (key, expected) in cases:
        result = CliRunner().invoke(cli, args)

        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload[key] == expected


def _envelope_payload() -> dict:
    return {
        "schema_version": "1",
        "workflow_id": "wf-1",
        "transition": "queue->work",
        "idempotency_key": "k-1",
        "actor": "operator",
        "canonical_writer": "task-orchestrator",
        "receipt": {
            "proof_id": "p-1",
            "operation": "advance_item",
            "status": "OK",
        },
    }


def test_transition_proof_envelope_accepts_supported_schema_version(tmp_path):
    envelope_path = tmp_path / "envelope.json"
    envelope_path.write_text(json.dumps(_envelope_payload()), encoding="utf-8")

    report = validate_transition_proof_envelope_file(envelope_path)

    assert report.status == "PASS", report.errors
    assert report.valid is True
    assert report.errors == []


def test_transition_proof_envelope_rejects_unsupported_schema_version(tmp_path):
    envelope = _envelope_payload()
    envelope["schema_version"] = "999"
    envelope_path = tmp_path / "envelope.json"
    envelope_path.write_text(json.dumps(envelope), encoding="utf-8")

    report = validate_transition_proof_envelope_file(envelope_path)

    assert report.status == "FAIL"
    assert report.valid is False
    codes = {error["code"] for error in report.errors}
    assert "TRANSITION_PROOF_SCHEMA_VERSION_UNSUPPORTED" in codes
