"""Contract tests for local-only Cockpit runtime renderer primitives."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from dopemux.ui.cockpit.runtime_contract import (
    GLOBAL_SURFACES,
    SAFE_ACTION_TIERS,
    TOP_LEVEL_MODES,
    PackageLoadError,
    RuntimeConfig,
    build_gate_receipt,
    build_runtime_render_model,
    evaluate_safe_action_preflight,
    load_package_artifacts,
    render_runtime_snapshot,
)


REPO_ROOT = Path(__file__).resolve().parents[5]
PACKAGE_DIR = (
    REPO_ROOT
    / "out"
    / "cockpit-pack-remediation"
    / "TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA"
)
BASE_TIME = "2026-05-04T12:00:00Z"
EVALUATED_AT = datetime(2026, 5, 4, 12, 0, 0, tzinfo=UTC)


def _joined(*parts: str) -> str:
    return "".join(parts)


def _candidate(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "command": "dopemux cockpit runtime-render candidate",
        "resolved_params": {
            "required": {"target": "out/cockpit-runtime-render/proof.json"},
            "optional": {"force": {"value": False, "was_default": True}},
        },
        "cwd": str(REPO_ROOT),
        "worktree_metadata": {
            "branch": "codex/cockpit-runtime-render-001",
            "detached": False,
            "dirty": False,
            "worktree_root": str(REPO_ROOT),
        },
        "authority_domain": "dopemux operator control",
        "canonical_writer": "dopemux operator control",
        "safety_class": "CONFIRM_REQUIRED",
        "gate_tier": "T1",
        "side_effects": ["generated artifact"],
        "expected_proof": "ARTIFACT_AND_CHECKSUM",
        "rollback_or_abort": {
            "kind": "NOT_APPLICABLE",
            "value": "artifact write refused on unknown overwrite",
            "reason": "generated artifact",
        },
        "source_provenance": {
            "source_file": "src/dopemux/ui/cockpit/runtime_contract.py",
            "source_symbol": "evaluate_safe_action_preflight",
            "evidence_path_or_command": "PACKAGE_REMEDIATION_INDEX.json",
        },
        "palette_request_id": "palette-001",
        "palette_index_row_hash": "row-hash-001",
        "surface_origin": "COMMAND_PALETTE",
        "operator_intent": "CONFIRM_AND_RUN",
        "created_at_utc": BASE_TIME,
        "output_target_path": "out/cockpit-runtime-render/proof.json",
        "overwrite_behavior": "refuse_if_exists",
    }
    data.update(overrides)
    return data


def test_package_loader_fails_closed_on_missing_required_files(tmp_path: Path):
    with pytest.raises(PackageLoadError, match=r"\[BLOCKER\]"):
        load_package_artifacts(tmp_path)


def test_package_loader_parses_accepted_proof_and_index_files():
    package = load_package_artifacts(PACKAGE_DIR)
    assert package.index["packet_id"] == "TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA"
    assert package.proof["safe_for_claude_design"] == "NO"
    assert package.proof["ready_for_claude_design"] is False
    assert len(package.package_index_sha256) == 64
    assert len(package.proof_sha256) == 64


def test_runtime_render_model_preserves_modes_surfaces_and_tiers():
    package = load_package_artifacts(PACKAGE_DIR)
    model = build_runtime_render_model(package)
    assert model.top_level_modes == (
        "PM",
        "Implementer",
        "Overview",
        "Services",
        "Events",
    )
    assert len(model.top_level_modes) == 5
    assert model.global_surfaces == (
        "Command Palette",
        "Settings/Admin/Runtime",
        "Safe Actions / Proof Gate",
        "Unknown / Drift Queue",
    )
    assert model.safe_action_tiers == (
        "T0",
        "T0i",
        "T1",
        "T2",
        "T3",
        "T4",
        "T5",
        "T6",
        "TX",
        "TU",
    )
    assert TOP_LEVEL_MODES == model.top_level_modes
    assert GLOBAL_SURFACES == model.global_surfaces
    assert SAFE_ACTION_TIERS == model.safe_action_tiers


def test_runtime_snapshot_preserves_governance_and_boundaries():
    output = render_runtime_snapshot(PACKAGE_DIR)
    assert "safe_for_claude_design: NO" in output
    assert "READY_FOR_CLAUDE_DESIGN: not approved" in output
    top_line = next(line for line in output.splitlines() if line.startswith("top_level_modes:"))
    assert "PM | Implementer | Overview | Services | Events" in top_line
    assert "Safe Actions / Proof Gate" not in top_line
    assert "Command Palette broker-only" in output
    assert "cross-cutting and non-executing here" in output
    assert "T4 blocked until remote mutation policy exists" in output
    assert "TX/TU never executable" in output


def test_preflight_allows_confirm_for_resolved_executable_candidate():
    result = evaluate_safe_action_preflight(
        _candidate(),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "ALLOW_CONFIRM"
    assert result.can_confirm is True
    assert result.execution_status == "not_attempted"


def test_t4_is_refused_until_remote_policy_scope_exists():
    result = evaluate_safe_action_preflight(
        _candidate(gate_tier="T4", expected_proof="REMOTE_RECEIPT"),
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "REFUSE_T4_POLICY_MISSING"
    assert result.can_confirm is False
    assert result.refusal_reason == "REMOTE_MUTATION_POLICY_MISSING"


@pytest.mark.parametrize("tier", ["T0", "T0i"])
def test_t0_and_t0i_do_not_reach_confirm_affordance(tier: str):
    result = evaluate_safe_action_preflight(
        _candidate(gate_tier=tier),
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "REFUSE_NON_EXECUTABLE_TIER"
    assert result.can_confirm is False
    assert result.refusal_reason == "NON_EXECUTABLE_TIER"
    assert result.routing_destination == "INSPECT_RESULT"


@pytest.mark.parametrize(
    ("tier", "safety_class", "status"),
    [
        ("TX", "BLOCKED_IN_COCKPIT", "REFUSE_BLOCKED"),
        ("TU", "UNKNOWN", "REFUSE_UNKNOWN"),
    ],
)
def test_tx_and_tu_never_reach_confirm_affordance(
    tier: str,
    safety_class: str,
    status: str,
):
    result = evaluate_safe_action_preflight(
        _candidate(gate_tier=tier, safety_class=safety_class),
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == status
    assert result.can_confirm is False


def test_missing_required_preflight_field_refuses():
    candidate = _candidate()
    candidate.pop("output_target_path")
    result = evaluate_safe_action_preflight(
        candidate,
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "REFUSE_MISSING_FIELD"
    assert result.missing_fields == ("output_target_path",)


def test_unknown_canonical_writer_refuses_executable_tier():
    result = evaluate_safe_action_preflight(
        _candidate(canonical_writer="UNKNOWN"),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "REFUSE_AUTHORITY_CONFLICT"
    assert result.refusal_reason == "AUTHORITY_CONFLICT"


def test_index_drift_refuses_before_confirm():
    result = evaluate_safe_action_preflight(
        _candidate(),
        current_row_hash="different-row-hash",
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "REFUSE_INDEX_DRIFT"
    assert result.routing_destination == "RE_RENDER"


def test_unsafe_source_surface_refuses():
    result = evaluate_safe_action_preflight(
        _candidate(surface_origin="DEEP_LINK"),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "REFUSE_UNSAFE_SOURCE_SURFACE"
    assert result.refusal_reason == "UNSAFE_SOURCE_SURFACE"


def test_stale_handoff_refuses_by_timestamp():
    result = evaluate_safe_action_preflight(
        _candidate(created_at_utc="2026-05-02T11:00:00Z"),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
        config=RuntimeConfig(stale_proof_window_seconds=3600),
    )
    assert result.status == "REFUSE_STALE_HANDOFF"
    assert result.routing_destination == "RE_RENDER"


def test_receipts_include_required_fields_and_utc_timestamp():
    preflight = evaluate_safe_action_preflight(
        _candidate(),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    receipt = build_gate_receipt(
        event_type="gate_open",
        candidate=_candidate(),
        preflight=preflight,
        created_at_utc=BASE_TIME,
    )
    required_fields = {
        "gate_request_id",
        "palette_request_id",
        "action_row_hash",
        "tier",
        "safety_class",
        "authority_domain",
        "canonical_writer",
        "preflight_status",
        "confirmation_status",
        "execution_status",
        "proof_status",
        "proof_artifacts",
        "refusal_reason",
        "routing_destination",
        "surface_origin",
        "operator_id",
        "created_at_utc",
    }
    assert required_fields <= set(receipt)
    assert receipt["created_at_utc"].endswith("Z")
    assert receipt["operator_id"] == "NULL_NOT_AUTHENTICATED"
    assert receipt["execution_status"] == "not_attempted"


def test_receipt_redacts_secret_payloads():
    preflight = evaluate_safe_action_preflight(
        _candidate(),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    receipt = build_gate_receipt(
        event_type="gate_proof_captured",
        candidate=_candidate(),
        preflight=preflight,
        proof_artifacts={
            "api_key": "abc123",
            "nested": {"password": "hunter2"},
            "header": "Bearer abc123",
        },
        created_at_utc=BASE_TIME,
    )
    assert receipt["proof_artifacts"]["api_key"] == "[REDACTED]"
    assert receipt["proof_artifacts"]["nested"]["password"] == "[REDACTED]"
    assert receipt["proof_artifacts"]["header"] == "Bearer [REDACTED]"


def test_forbidden_positive_claims_absent_from_runtime_snapshot():
    output = render_runtime_snapshot(PACKAGE_DIR)
    forbidden = (
        _joined("READY_FOR_CLAUDE_DESIGN: ", "approved"),
        _joined("safe_for_claude_design: ", "YES"),
        _joined("Claude Design upload ", "allowed"),
        _joined("T4 ", "authorized"),
        _joined("runtime execution ", "implemented"),
    )
    for phrase in forbidden:
        assert phrase not in output


def test_runtime_renderer_implementation_has_no_forbidden_call_tokens():
    paths = [
        REPO_ROOT / "src" / "dopemux" / "ui" / "cockpit",
        REPO_ROOT / "src" / "dopemux" / "commands" / "cockpit_commands.py",
    ]
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for root in paths
        for path in ([root] if root.is_file() else sorted(root.glob("*.py")))
    )
    forbidden = (
        _joined("sub", "process"),
        _joined("shell", "=True"),
        _joined("os.", "system"),
        _joined("req", "uests"),
        _joined("ht", "tpx"),
        _joined("url", "lib"),
        _joined("soc", "ket"),
        _joined("doc", "ker"),
        _joined("kub", "ectl"),
        _joined("gh pr ", "create"),
        _joined("git ", "push"),
    )
    for token in forbidden:
        assert token not in text
