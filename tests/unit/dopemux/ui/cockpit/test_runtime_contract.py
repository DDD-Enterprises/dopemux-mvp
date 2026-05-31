"""Contract tests for local-only Cockpit runtime renderer primitives."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from pathlib import Path

import pytest

from dopemux.ui.cockpit.runtime_contract import (
    ALLOWED_UNKNOWN_DRIFT_AFFORDANCES,
    COMMAND_PALETTE_SEARCH_AXES,
    GLOBAL_SURFACES,
    SAFE_ACTION_TIERS,
    TOP_LEVEL_MODES,
    UNKNOWN_DRIFT_REASON_CODES,
    PackageLoadError,
    RuntimeConfig,
    build_settings_admin_runtime_summary,
    build_gate_receipt,
    build_runtime_render_model,
    build_unknown_drift_queue_item,
    build_unknown_drift_queue_summary,
    evaluate_safe_action_preflight,
    load_package_artifacts,
    map_settings_admin_row_to_gate_tier,
    redact_secrets,
    render_runtime_snapshot,
    route_command_palette_row,
    normalize_command_palette_index_row,
    runtime_snapshot_payload,
    stable_sha256,
    verify_claude_design_gate,
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


def _t5_candidate(**overrides: object) -> dict[str, object]:
    data = _candidate(
        gate_tier="T5",
        expected_proof="SERVICE_STATUS_AND_LOG",
        service_id="dopemux-rte",
        service_scope="local",
        expected_state_transition="stopped -> running",
        pre_state_snapshot={"status": "stopped"},
        typed_confirmation="dopemux-rte",
    )
    data.update(overrides)
    return data


def _t6_candidate(**overrides: object) -> dict[str, object]:
    data = _candidate(
        gate_tier="T6",
        expected_proof="TP_RUNNER_PROOF",
        tp_or_task_id="TP-DMX-COCKPIT-SAFE-ACTIONS-001",
        runner_id="dopetask-local",
        branch="codex/cockpit-ui-safe-actions-001",
        output_or_proof_target="proof/cockpit-safe-actions/TP-DMX-COCKPIT-SAFE-ACTIONS-001",
        tp_gate_present=True,
        typed_confirmation="TP-DMX-COCKPIT-SAFE-ACTIONS-001",
    )
    data.update(overrides)
    return data


def _palette_row(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "command_path": "dopemux cockpit run",
        "parent_group": "dopemux cockpit",
        "authority_domain": "dopemux operator control",
        "canonical_writer": "dopemux operator control",
        "safe_ui_exposure": "CONFIRM_REQUIRED",
        "cockpit_placement": "PM",
        "current_cockpit_coverage": "PARTIAL",
        "activation_status": "ACTIVE",
        "source_file": "src/dopemux/commands/cockpit_commands.py",
        "source_symbol": "cockpit",
        "help_text_or_summary": "Run the guarded cockpit surface.",
        "evidence_path_or_command": "dopemux cockpit --help",
        "parameter_schema": {
            "required_parameters": [{"name": "mode", "value": "pm"}],
            "optional_parameters": [{"name": "dry_run", "default": True}],
            "cwd_target": str(REPO_ROOT),
            "output_target": "NOT_APPLICABLE",
            "side_effects": ["execution_handoff"],
        },
        "proof_requirement": "TP_RUNNER_PROOF",
        "gate_tier": "T6",
        "allowed_palette_outcomes": ["Inspect", "OpenSafeActionGate"],
        "blocked_reason": "NOT_APPLICABLE",
        "unknown_reason": "NOT_APPLICABLE",
        "updated_at_or_source_timestamp": BASE_TIME,
    }
    data.update(overrides)
    return data


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def test_package_loader_resolves_repo_relative_package_dir_from_subdirectory(monkeypatch):
    monkeypatch.chdir(REPO_ROOT / "src")
    package = load_package_artifacts(
        "out/cockpit-pack-remediation/TP-DMX-COCKPIT-PACK-REMEDIATE-006-IA"
    )
    assert package.package_dir == PACKAGE_DIR


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
    assert "Settings/Admin/Runtime" not in model.top_level_modes
    assert "Settings/Admin/Runtime" in model.global_surfaces
    assert "Unknown / Drift Queue" not in model.top_level_modes
    assert "Unknown / Drift Queue" in model.global_surfaces
    assert model.unknown_drift_queue.surface_kind == "secondary/global surface"
    assert model.unknown_drift_queue.execution_allowed is False
    assert model.safe_for_claude_design == "YES"
    assert model.ready_for_claude_design == "approved"
    assert model.invariants["claude_design_blocked"] is False
    assert model.invariants["claude_design_gate_verified"] is True


def test_claude_design_gate_verifies_all_eight_blockers_before_flip():
    package = load_package_artifacts(PACKAGE_DIR)
    gate = verify_claude_design_gate(package)

    assert gate.packet_id == "TP-DMX-COCKPIT-GATE-FLIP-001"
    assert gate.safe_for_claude_design == "YES"
    assert gate.ready_for_claude_design == "approved"
    assert gate.claude_design_blocked is False
    assert {condition["id"] for condition in gate.conditions} == {
        "COMMAND_PALETTE",
        "SAFE_ACTIONS",
        "SETTINGS_RUNTIME",
        "UNKNOWN_DRIFT",
        "PACK_REMEDIATE_IA",
        "RUNTIME_RENDER",
        "INVENTORY_REGEN",
        "EVIDENCE_LEDGER",
    }
    assert all(condition["passed"] is True for condition in gate.conditions)


def test_runtime_snapshot_preserves_governance_and_boundaries():
    output = render_runtime_snapshot(PACKAGE_DIR)
    assert "safe_for_claude_design: YES" in output
    assert "READY_FOR_CLAUDE_DESIGN: approved" in output
    top_line = next(line for line in output.splitlines() if line.startswith("top_level_modes:"))
    assert "PM | Implementer | Overview | Services | Events" in top_line
    assert "Safe Actions / Proof Gate" not in top_line
    assert "Command Palette broker-only" in output
    assert "cross-cutting and non-executing here" in output
    assert "T4 blocked until remote mutation policy exists" in output
    assert "TX/TU never executable" in output
    assert "settings_admin_runtime:" in output
    assert "surface_name: Settings/Admin/Runtime" in output
    assert "flow_group_count: 9" in output
    assert "row_count: 62" in output
    assert "unknown_tier_count: 62" in output
    assert "unknown_drift_queue:" in output
    assert "surface_name: Unknown / Drift Queue" in output
    assert "settings_unknown_tier_count: 62" in output
    assert "execution_allowed: false" in output
    assert "runtime_reclassification_allowed: false" in output
    assert "requires_packet_for_resolution: true" in output
    assert "claude_design_blocked: false" in output
    assert "claude_design_gate_verified: true" in output


def test_command_palette_search_axes_cover_spec_axes():
    assert COMMAND_PALETTE_SEARCH_AXES == (
        "command_path",
        "parent_group",
        "source_symbol",
        "authority_domain",
        "safe_ui_exposure",
        "cockpit_placement",
        "canonical_writer",
        "proof_requirement",
        "source_file",
        "evidence_path_or_command",
        "activation_status",
    )


def test_command_palette_normalizes_missing_fields_to_unknown_without_mutation():
    raw = _palette_row()
    raw.pop("canonical_writer")
    before = dict(raw)

    normalized = normalize_command_palette_index_row(raw)

    assert raw == before
    assert normalized["canonical_writer"] == "UNKNOWN"
    assert len(normalized["row_hash"]) == 64
    assert normalized["broker_only"] is True
    assert normalized["executes"] is False


def test_command_palette_routes_confirm_required_rows_to_safe_action_gate_without_execution():
    decision = route_command_palette_row(_palette_row())

    assert decision.outcome == "OpenSafeActionGate"
    assert decision.routing_destination == "SAFE_ACTION_GATE"
    assert decision.rule_id == "R-7"
    assert decision.executes is False
    assert decision.broker_only is True


def test_command_palette_routes_settings_admin_rows_to_settings_surface():
    decision = route_command_palette_row(
        _palette_row(
            cockpit_placement="Settings/Admin",
            allowed_palette_outcomes=["Inspect", "OpenSettingsAdminRuntime"],
        )
    )

    assert decision.outcome == "OpenSettingsAdminRuntime"
    assert decision.routing_destination == "SETTINGS_ADMIN_RUNTIME"
    assert decision.executes is False


def test_command_palette_never_executes_blocked_unknown_or_external_rows():
    cases = [
        (
            _palette_row(
                safe_ui_exposure="BLOCKED_IN_COCKPIT",
                gate_tier="TX",
                allowed_palette_outcomes=["ShowBlockedReason"],
                blocked_reason="blocked by cockpit policy",
            ),
            "ShowBlockedReason",
            "SHOW_BLOCKED_REASON",
        ),
        (
            _palette_row(
                safe_ui_exposure="UNKNOWN",
                gate_tier="TU",
                allowed_palette_outcomes=["ShowUnknownDriftReason"],
                unknown_reason="authority unresolved",
            ),
            "ShowUnknownDriftReason",
            "UNKNOWN_DRIFT_QUEUE",
        ),
        (
            _palette_row(
                safe_ui_exposure="EXTERNAL_ONLY",
                gate_tier="TX",
                cockpit_placement="External/Not Cockpit",
                allowed_palette_outcomes=["Inspect", "CopyCommand"],
            ),
            "CopyCommand",
            "ORIGINATING_SURFACE",
        ),
    ]

    for row, outcome, destination in cases:
        decision = route_command_palette_row(row)
        assert decision.outcome == outcome
        assert decision.routing_destination == destination
        assert decision.executes is False
        assert decision.can_open_safe_action_gate is False


def test_command_palette_unknown_authority_fails_closed_to_unknown_drift_queue():
    decision = route_command_palette_row(
        _palette_row(
            authority_domain="unknown / conflicting",
            canonical_writer="UNKNOWN",
            allowed_palette_outcomes=["Inspect", "OpenSafeActionGate"],
        )
    )

    assert decision.outcome == "ShowUnknownDriftReason"
    assert decision.routing_destination == "UNKNOWN_DRIFT_QUEUE"
    assert decision.refusal_reason == "AUTHORITY_CONFLICT"
    assert decision.can_open_safe_action_gate is False


def test_command_palette_unresolved_required_parameter_fails_closed_before_gate():
    decision = route_command_palette_row(
        _palette_row(
            parameter_schema={
                "required_parameters": [{"name": "target", "value": "UNKNOWN"}],
                "optional_parameters": [],
                "cwd_target": str(REPO_ROOT),
                "output_target": "NOT_APPLICABLE",
                "side_effects": ["execution_handoff"],
            }
        )
    )

    assert decision.outcome == "ShowUnknownDriftReason"
    assert decision.routing_destination == "UNKNOWN_DRIFT_QUEUE"
    assert decision.refusal_reason == "PARAM_UNRESOLVED"
    assert decision.can_open_safe_action_gate is False


def test_command_palette_unknown_required_parameters_string_fails_closed_before_gate():
    decision = route_command_palette_row(
        _palette_row(
            parameter_schema={
                "required_parameters": "UNKNOWN",
                "optional_parameters": [],
                "cwd_target": str(REPO_ROOT),
                "output_target": "NOT_APPLICABLE",
                "side_effects": ["execution_handoff"],
            }
        )
    )

    assert decision.outcome == "ShowUnknownDriftReason"
    assert decision.routing_destination == "UNKNOWN_DRIFT_QUEUE"
    assert decision.refusal_reason == "PARAM_UNRESOLVED"
    assert decision.can_open_safe_action_gate is False


def test_settings_admin_summary_uses_package_handoff_without_mutating_artifact():
    source = PACKAGE_DIR / "SETTINGS_ADMIN_RUNTIME_PACKAGE_HANDOFF.md"
    before = _sha(source)
    package = load_package_artifacts(PACKAGE_DIR)
    summary = build_settings_admin_runtime_summary(package)
    after = _sha(source)
    assert before == after
    assert summary.surface_kind == "secondary/global surface"
    assert summary.surface_name == "Settings/Admin/Runtime"
    assert summary.row_count == 62
    assert summary.unknown_tier_count == 62
    assert summary.gate_required_count == "UNKNOWN"
    assert summary.blocked_count == "UNKNOWN"
    assert summary.open_downstream_owner == "TP-DMX-COCKPIT-SETTINGS-RUNTIME-001"
    assert len(summary.flow_groups) == 9
    assert "SETTINGS_ADMIN_RUNTIME_PACKAGE_HANDOFF.md" in summary.source_artifact_path


def test_runtime_snapshot_payload_includes_settings_admin_summary():
    payload = runtime_snapshot_payload(PACKAGE_DIR)
    settings = payload["settings_admin_runtime"]
    assert settings["surface_name"] == "Settings/Admin/Runtime"
    assert settings["surface_kind"] == "secondary/global surface"
    assert settings["row_count"] == 62
    assert settings["unknown_tier_count"] == 62
    assert settings["mapped_tier_counts"]["TU"] == 0
    assert settings["refusal_counts"]["UNKNOWN_DRIFT_QUEUE"] == 62
    assert settings["safe_for_claude_design"] == "YES"
    assert settings["READY_FOR_CLAUDE_DESIGN"] == "approved"
    assert len(settings["flow_groups"]) == 9


def test_unknown_drift_reason_taxonomy_contains_required_codes():
    required = {
        "UNKNOWN",
        "AUTHORITY_CONFLICT",
        "PARAM_UNRESOLVED",
        "CWD_UNRESOLVED",
        "PROOF_REQUIREMENT_UNKNOWN",
        "ROLLBACK_UNKNOWN",
        "SIDE_EFFECTS_UNKNOWN",
        "REMOTE_MUTATION_POLICY_MISSING",
        "TP_GATE_ABSENT",
        "AUTHORITY_DRIFT_MID_FLOW",
        "CLASS_DRIFT_MID_FLOW",
        "UNSAFE_SOURCE_SURFACE",
        "STALE_PROOF_GATE",
        "INDEX_DRIFT",
        "STALE_HANDOFF",
        "DEFINED_NOT_REGISTERED",
        "OPTIONAL_IMPORT_UNKNOWN",
        "DEPRECATED_BLOCKED",
        "MISSING_REQUIRED_FIELD",
        "UNKNOWN_CANONICAL_WRITER",
        "UNKNOWN_AUTHORITY_DOMAIN",
        "SETTINGS_ROW_TIER_UNKNOWN",
    }
    assert required <= set(UNKNOWN_DRIFT_REASON_CODES)


def test_unknown_drift_queue_item_defaults_and_redacts_secret_like_values():
    item = build_unknown_drift_queue_item(
        source_surface="Command Palette",
        source_artifact_path="out/example.md",
        source_packet_id="TP-EXAMPLE",
        source_row_id="row-1",
        command_or_row_label="show token=abc123",
        reason_code="UNKNOWN",
        reason_detail="blocked because api_key=secret123",
        evidence_refs=("Authorization: Bearer abc123", "password=hunter2"),
    )
    payload = item.as_payload()
    assert payload["can_execute"] is False
    assert payload["can_reclassify_at_runtime"] is False
    assert payload["requires_packet"] is True
    assert payload["command_or_row_label"] == "show token=[REDACTED]"
    assert payload["reason_detail"] == "blocked because api_key=[REDACTED]"
    assert payload["evidence_refs"] == [
        "Authorization: [REDACTED]",
        "password=[REDACTED]",
    ]


def test_unknown_drift_queue_hashes_redacted_seed_before_deriving_ids():
    first = build_unknown_drift_queue_item(
        source_surface="Command Palette",
        source_artifact_path="out/example.md",
        source_packet_id="TP-EXAMPLE",
        source_row_id="row-1",
        command_or_row_label="rotate token=alpha",
        reason_code="UNKNOWN",
        reason_detail="blocked because token=alpha",
    )
    second = build_unknown_drift_queue_item(
        source_surface="Command Palette",
        source_artifact_path="out/example.md",
        source_packet_id="TP-EXAMPLE",
        source_row_id="row-1",
        command_or_row_label="rotate token=beta",
        reason_code="UNKNOWN",
        reason_detail="blocked because token=beta",
    )
    assert first.row_hash == second.row_hash
    assert first.queue_item_id == second.queue_item_id
    assert "alpha" not in str(first.as_payload())
    assert "beta" not in str(second.as_payload())


def test_unknown_drift_summary_uses_accepted_sources_without_mutating_artifacts():
    source_paths = [
        PACKAGE_DIR / "PACKAGE_REMEDIATION_INDEX.json",
        PACKAGE_DIR / "PROOF.json",
        PACKAGE_DIR / "UNKNOWN_DRIFT_PACKAGE_HANDOFF.md",
        REPO_ROOT
        / "out"
        / "cockpit-runtime-render"
        / "TP-DMX-COCKPIT-RUNTIME-RENDER-001"
        / "PROOF.json",
        REPO_ROOT
        / "out"
        / "cockpit-settings-runtime"
        / "TP-DMX-COCKPIT-SETTINGS-RUNTIME-001"
        / "PROOF.json",
    ]
    before = {path: _sha(path) for path in source_paths}
    package = load_package_artifacts(PACKAGE_DIR)
    summary = build_unknown_drift_queue_summary(package)
    after = {path: _sha(path) for path in source_paths}
    assert before == after
    assert summary.surface_name == "Unknown / Drift Queue"
    assert summary.surface_kind == "secondary/global surface"
    assert summary.execution_allowed is False
    assert summary.runtime_reclassification_allowed is False
    assert summary.requires_packet_for_resolution is True
    assert summary.settings_unknown_tier_count == 62


def test_unknown_drift_snapshot_payload_contains_aggregate_counts_and_sources():
    payload = runtime_snapshot_payload(PACKAGE_DIR)
    queue = payload["unknown_drift_queue"]
    assert queue["surface_name"] == "Unknown / Drift Queue"
    assert queue["surface_kind"] == "secondary/global surface"
    assert queue["total_queue_items"] >= 487
    assert queue["total_queue_items_is_lower_bound"] is True
    assert queue["reason_counts"]["DEFINED_NOT_REGISTERED"] == 30
    assert queue["reason_counts"]["OPTIONAL_IMPORT_UNKNOWN"] == 2
    assert queue["reason_counts"]["DEPRECATED_BLOCKED"] == 7
    assert queue["reason_counts"]["AUTHORITY_CONFLICT"] == 14
    assert queue["reason_counts"]["SETTINGS_ROW_TIER_UNKNOWN"] == "UNKNOWN"
    assert queue["reason_counts"]["REMOTE_MUTATION_POLICY_MISSING"] == "UNKNOWN"
    assert queue["reason_counts"]["UNKNOWN"] == "UNKNOWN"
    assert queue["stale_proof_count"] == 1
    assert queue["index_drift_count"] == "UNKNOWN"
    assert queue["settings_unknown_tier_count"] == 62
    assert queue["execution_allowed"] is False
    assert queue["runtime_reclassification_allowed"] is False
    assert queue["requires_packet_for_resolution"] is True
    assert "Unknown / Drift Queue" in payload["global_surfaces"]
    assert "Unknown / Drift Queue" not in payload["top_level_modes"]
    refs = "\n".join(queue["source_artifact_refs"])
    assert "SAFE_ACTION_GATE_TO_UNKNOWN_DRIFT_HANDOFF.md" in refs
    assert "PALETTE_TO_UNKNOWN_DRIFT_HANDOFF.md" in refs
    assert "UNKNOWN_DRIFT_QUEUE_SPEC.md" in refs


def test_unknown_drift_queue_allows_only_display_copy_inspect_affordances():
    payload = runtime_snapshot_payload(PACKAGE_DIR)
    allowed = payload["unknown_drift_queue"]["allowed_affordances"]
    assert allowed == list(ALLOWED_UNKNOWN_DRIFT_AFFORDANCES)
    forbidden_fragments = ("Resolve", "Approve", "Promote", "Demote", "Retry", "Execute")
    for affordance in allowed:
        assert not any(fragment in affordance for fragment in forbidden_fragments)


@pytest.mark.parametrize(
    ("row", "tier", "can_confirm", "gate_required", "route", "reason"),
    [
        (
            {"safety_class": "DISPLAY_ONLY"},
            "T0",
            False,
            False,
            "NOT_APPLICABLE",
            None,
        ),
        (
            {"safety_class": "INSPECT_ACTION"},
            "T0i",
            False,
            True,
            "NOT_APPLICABLE",
            None,
        ),
        (
            {
                "safety_class": "CONFIRM_REQUIRED",
                "side_effect_kind": "config_mutation",
            },
            "T2",
            True,
            True,
            "NOT_APPLICABLE",
            None,
        ),
        (
            {
                "safety_class": "CONFIRM_REQUIRED",
                "side_effect_kind": "local_write",
            },
            "T3",
            True,
            True,
            "NOT_APPLICABLE",
            None,
        ),
        (
            {
                "safety_class": "CONFIRM_REQUIRED",
                "side_effect_kind": "remote_mutation",
            },
            "T4",
            False,
            True,
            "UNKNOWN_DRIFT_QUEUE",
            "REMOTE_MUTATION_POLICY_MISSING",
        ),
        (
            {
                "safety_class": "CONFIRM_REQUIRED",
                "side_effect_kind": "service_start_stop",
            },
            "T5",
            True,
            True,
            "NOT_APPLICABLE",
            None,
        ),
        (
            {
                "safety_class": "CONFIRM_REQUIRED",
                "side_effect_kind": "execution_handoff",
            },
            "T6",
            True,
            True,
            "NOT_APPLICABLE",
            None,
        ),
        (
            {"safety_class": "BLOCKED_IN_COCKPIT"},
            "TX",
            False,
            False,
            "SHOW_BLOCKED_REASON",
            "BLOCKED_IN_COCKPIT",
        ),
        (
            {"safety_class": "UNKNOWN"},
            "TU",
            False,
            False,
            "UNKNOWN_DRIFT_QUEUE",
            "UNKNOWN_CLASS",
        ),
        (
            {"safety_class": "EXTERNAL_ONLY"},
            "TU",
            False,
            False,
            "ORIGINATING_SURFACE",
            "EXTERNAL_ONLY",
        ),
    ],
)
def test_settings_admin_row_tier_mapping_from_explicit_evidence(
    row: dict[str, object],
    tier: str,
    can_confirm: bool,
    gate_required: bool,
    route: str,
    reason: str | None,
):
    mapping = map_settings_admin_row_to_gate_tier(row)
    assert mapping.tier == tier
    assert mapping.can_confirm is can_confirm
    assert mapping.gate_required is gate_required
    assert mapping.refusal_route == route
    assert mapping.refusal_reason == reason
    assert mapping.execution_status == "not_attempted"


def test_settings_admin_insufficient_evidence_maps_to_unknown_drift_queue():
    mapping = map_settings_admin_row_to_gate_tier({"safety_class": "CONFIRM_REQUIRED"})
    assert mapping.tier == "TU"
    assert mapping.can_confirm is False
    assert mapping.gate_required is False
    assert mapping.refusal_route == "UNKNOWN_DRIFT_QUEUE"
    assert mapping.refusal_reason == "GATE_TIER_UNKNOWN"


def test_settings_admin_blocked_rows_never_confirm():
    mapping = map_settings_admin_row_to_gate_tier(
        {"safety_class": "BLOCKED_IN_COCKPIT", "side_effect_kind": "config_mutation"}
    )
    assert mapping.tier == "TX"
    assert mapping.can_confirm is False
    assert mapping.gate_required is False
    assert mapping.refusal_route == "SHOW_BLOCKED_REASON"


def test_settings_admin_t4_maps_but_refuses_until_remote_policy_exists():
    mapping = map_settings_admin_row_to_gate_tier(
        {"safety_class": "CONFIRM_REQUIRED", "side_effect_kind": "remote_mutation"}
    )
    assert mapping.tier == "T4"
    assert mapping.can_confirm is False
    assert mapping.gate_required is True
    assert mapping.remote_policy_required is True
    assert mapping.refusal_reason == "REMOTE_MUTATION_POLICY_MISSING"


def test_confirmable_settings_admin_rows_require_safe_action_gate():
    for side_effect in ("config_mutation", "local_write", "service_start_stop", "execution_handoff"):
        mapping = map_settings_admin_row_to_gate_tier(
            {"safety_class": "CONFIRM_REQUIRED", "side_effect_kind": side_effect}
        )
        assert mapping.can_confirm is True
        assert mapping.gate_required is True
        assert mapping.execution_status == "not_attempted"


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


@pytest.mark.parametrize(
    ("candidate", "expected_status"),
    [
        (_t5_candidate(typed_confirmation="wrong-service"), "REFUSE_TYPED_CONFIRMATION_MISMATCH"),
        (_t6_candidate(typed_confirmation="wrong-task"), "REFUSE_TYPED_CONFIRMATION_MISMATCH"),
    ],
)
def test_t5_and_t6_refuse_before_typed_confirmation_matches(
    candidate: dict[str, object],
    expected_status: str,
):
    result = evaluate_safe_action_preflight(
        candidate,
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == expected_status
    assert result.can_confirm is False
    assert result.refusal_reason == "TYPED_CONFIRMATION_MISMATCH"
    assert result.routing_destination == "SAFE_ACTION_GATE"
    assert result.execution_status == "not_attempted"


@pytest.mark.parametrize("candidate", [_t5_candidate(), _t6_candidate()])
def test_t5_and_t6_allow_confirm_only_after_typed_confirmation_matches(
    candidate: dict[str, object],
):
    result = evaluate_safe_action_preflight(
        candidate,
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "ALLOW_CONFIRM"
    assert result.can_confirm is True
    assert result.execution_status == "not_attempted"


def test_t6_refuses_when_task_packet_gate_is_absent():
    result = evaluate_safe_action_preflight(
        _t6_candidate(tp_gate_present=False),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "REFUSE_TP_GATE_ABSENT"
    assert result.can_confirm is False
    assert result.refusal_reason == "TP_GATE_ABSENT"
    assert result.routing_destination == "UNKNOWN_DRIFT_QUEUE"


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


def test_external_only_preflight_routes_to_originating_inspect_copy_path():
    result = evaluate_safe_action_preflight(
        _candidate(safety_class="EXTERNAL_ONLY"),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    assert result.status == "REFUSE_EXTERNAL_ONLY"
    assert result.can_confirm is False
    assert result.refusal_reason == "EXTERNAL_ONLY"
    assert result.routing_destination == "ORIGINATING_SURFACE"


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
        "event_timestamp_utc",
        "gate_open_timestamp_utc",
        "confirm_timestamp_utc",
        "proof_timestamp_utc",
        "typed_confirmation_match",
        "diff_acknowledged",
        "remote_mutation_policy_reference",
        "tp_or_task_id",
        "service_id",
        "stale_proof_tag",
        "event_type",
        "schema_version",
    }
    assert required_fields <= set(receipt)
    assert receipt["created_at_utc"].endswith("Z")
    assert receipt["event_timestamp_utc"] == BASE_TIME
    assert receipt["gate_open_timestamp_utc"] == BASE_TIME
    assert receipt["schema_version"] == "dopemux.cockpit.safe_action_gate.receipt.v1"
    assert receipt["operator_id"] == "NULL_NOT_AUTHENTICATED"
    assert receipt["execution_status"] == "not_attempted"


def test_receipt_recomputes_action_hash_from_redacted_canonical_candidate():
    candidate = _candidate(action_row_hash="caller-supplied", token="secret-one")
    preflight = evaluate_safe_action_preflight(
        candidate,
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    receipt = build_gate_receipt(
        event_type="gate_open",
        candidate=candidate,
        preflight=preflight,
        created_at_utc=BASE_TIME,
    )
    canonical = redact_secrets(candidate)
    canonical.pop("action_row_hash")
    assert receipt["action_row_hash"] == stable_sha256(canonical)
    assert receipt["action_row_hash"] != "caller-supplied"


def test_receipt_nulls_palette_request_id_for_non_palette_origin():
    preflight = evaluate_safe_action_preflight(
        _candidate(surface_origin="PM"),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    receipt = build_gate_receipt(
        event_type="gate_open",
        candidate=_candidate(surface_origin="PM"),
        preflight=preflight,
        created_at_utc=BASE_TIME,
    )
    assert receipt["palette_request_id"] is None


def test_receipt_default_gate_request_id_is_stable_across_lifecycle_events():
    preflight = evaluate_safe_action_preflight(
        _candidate(),
        current_row_hash="row-hash-001",
        evaluated_at_utc=EVALUATED_AT,
    )
    opened = build_gate_receipt(
        event_type="gate_open",
        candidate=_candidate(),
        preflight=preflight,
        created_at_utc=BASE_TIME,
    )
    confirmed = build_gate_receipt(
        event_type="gate_confirmed",
        candidate=_candidate(),
        preflight=preflight,
        created_at_utc="2026-05-04T12:01:00Z",
    )
    assert opened["gate_request_id"] == confirmed["gate_request_id"]


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
