"""Tests for scripts/audit/pr_audit_router.py."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.audit.pr_audit_router import (
    MultiModelAuditPlan,
    PrDiffStats,
    PrRiskClass,
    RouteResolution,
    _NON_BLOCKING_ROUTE_NAMES,
    _RISK_TIER_ROUTES,
    _validate_proof,
    build_audit_plan,
    classify_pr_risk,
    write_proof_artifact,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "proof" / "multi_model_pr_audit.schema.json"
PR_RISK_SCHEMA_PATH = ROOT / "schemas" / "audit" / "pr_risk.schema.json"
AUDIT_EXTRA_CLINK_CONF_DIR = ROOT / "scripts" / "audit" / "fixtures" / "clink_clients"
PAL_CLINK_CONF_DIR = (
    ROOT / "docker" / "mcp-servers-source" / "pal" / "pal-mcp-server" / "conf" / "cli_clients"
)
PAL_SUPPORTED_CLINK_RUNNERS = frozenset({"gemini", "codex", "claude"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan(
    risk: PrRiskClass = PrRiskClass.LOW,
    resolutions: tuple[RouteResolution, ...] | None = None,
    dry_run: bool = True,
) -> MultiModelAuditPlan:
    if resolutions is None:
        resolutions = tuple(
            RouteResolution(cli_name=n, available=False, blocking=n not in _NON_BLOCKING_ROUTE_NAMES)
            for n in _RISK_TIER_ROUTES[risk]
        )
    return MultiModelAuditPlan(
        risk_class=risk,
        requested_route_names=_RISK_TIER_ROUTES[risk],
        resolutions=resolutions,
        dry_run=dry_run,
    )


# ---------------------------------------------------------------------------
# classify_pr_risk
# ---------------------------------------------------------------------------

class TestClassifyPrRisk:
    def test_low_risk_small_diff(self) -> None:
        stats = PrDiffStats(files_changed=2, lines_added=30, lines_deleted=10)
        assert classify_pr_risk(stats) == PrRiskClass.LOW

    def test_medium_risk_schema_touch(self) -> None:
        stats = PrDiffStats(files_changed=1, lines_added=5, lines_deleted=2, touches_schema=True)
        assert classify_pr_risk(stats) == PrRiskClass.MEDIUM

    def test_medium_risk_large_diff_lines(self) -> None:
        stats = PrDiffStats(files_changed=3, lines_added=400, lines_deleted=200)
        assert classify_pr_risk(stats) == PrRiskClass.MEDIUM

    def test_medium_risk_many_files(self) -> None:
        stats = PrDiffStats(files_changed=21, lines_added=10, lines_deleted=5)
        assert classify_pr_risk(stats) == PrRiskClass.MEDIUM

    def test_high_risk_migration(self) -> None:
        stats = PrDiffStats(files_changed=1, lines_added=10, lines_deleted=0, touches_migration=True)
        assert classify_pr_risk(stats) == PrRiskClass.HIGH

    def test_high_risk_secrets_config(self) -> None:
        stats = PrDiffStats(files_changed=1, lines_added=1, lines_deleted=1, touches_secrets_config=True)
        assert classify_pr_risk(stats) == PrRiskClass.HIGH

    def test_high_risk_overrides_schema_touch(self) -> None:
        # Migration + schema → HIGH, not MEDIUM
        stats = PrDiffStats(
            files_changed=5,
            lines_added=100,
            lines_deleted=50,
            touches_schema=True,
            touches_migration=True,
        )
        assert classify_pr_risk(stats) == PrRiskClass.HIGH

    def test_boundary_exactly_500_lines_is_medium(self) -> None:
        stats = PrDiffStats(files_changed=1, lines_added=500, lines_deleted=1)
        assert classify_pr_risk(stats) == PrRiskClass.MEDIUM

    def test_boundary_500_lines_not_exceeded_is_low(self) -> None:
        # 250 added + 249 deleted = 499 total — still LOW
        stats = PrDiffStats(files_changed=1, lines_added=250, lines_deleted=249)
        assert classify_pr_risk(stats) == PrRiskClass.LOW


# ---------------------------------------------------------------------------
# Risk tier routes
# ---------------------------------------------------------------------------

class TestRiskTierRoutes:
    def test_low_tier_has_only_claude(self) -> None:
        assert _RISK_TIER_ROUTES[PrRiskClass.LOW] == ("claude-audit",)

    def test_medium_tier_has_claude_and_gemini(self) -> None:
        assert "claude-audit" in _RISK_TIER_ROUTES[PrRiskClass.MEDIUM]
        assert "gemini-audit" in _RISK_TIER_ROUTES[PrRiskClass.MEDIUM]

    def test_high_tier_includes_xai(self) -> None:
        assert "xai-grok-audit" in _RISK_TIER_ROUTES[PrRiskClass.HIGH]

    def test_xai_is_non_blocking(self) -> None:
        assert "xai-grok-audit" in _NON_BLOCKING_ROUTE_NAMES

    def test_cheaperinference_is_non_blocking(self) -> None:
        assert "cheaperinference-audit" in _NON_BLOCKING_ROUTE_NAMES

    def test_claude_audit_is_blocking(self) -> None:
        assert "claude-audit" not in _NON_BLOCKING_ROUTE_NAMES

    def test_gemini_audit_is_blocking(self) -> None:
        assert "gemini-audit" not in _NON_BLOCKING_ROUTE_NAMES


# ---------------------------------------------------------------------------
# build_audit_plan
# ---------------------------------------------------------------------------

class TestBuildAuditPlan:
    def test_dry_run_default(self, tmp_path: Path) -> None:
        stats = PrDiffStats(files_changed=2, lines_added=10, lines_deleted=5)
        plan = build_audit_plan(stats, conf_dir=tmp_path)
        assert plan.dry_run is True

    def test_risk_class_propagates(self, tmp_path: Path) -> None:
        stats = PrDiffStats(files_changed=1, lines_added=10, lines_deleted=5, touches_migration=True)
        plan = build_audit_plan(stats, conf_dir=tmp_path)
        assert plan.risk_class == PrRiskClass.HIGH

    def test_routes_unavailable_when_no_clink_configs(self, tmp_path: Path) -> None:
        # Empty conf_dir → no configs → all routes report unavailable
        stats = PrDiffStats(files_changed=1, lines_added=10, lines_deleted=5)
        plan = build_audit_plan(stats, conf_dir=tmp_path)
        assert not plan.has_any_available()

    def test_blocking_count_is_zero_with_no_routes(self, tmp_path: Path) -> None:
        stats = PrDiffStats(files_changed=1, lines_added=10, lines_deleted=5)
        plan = build_audit_plan(stats, conf_dir=tmp_path)
        assert plan.blocking_available_count() == 0

    def test_resolutions_match_tier_length(self, tmp_path: Path) -> None:
        stats = PrDiffStats(files_changed=1, lines_added=10, lines_deleted=5)
        plan = build_audit_plan(stats, conf_dir=tmp_path)
        assert len(plan.resolutions) == len(_RISK_TIER_ROUTES[PrRiskClass.LOW])

    def test_claude_route_available_when_clink_config_present_and_cli_on_path(
        self, tmp_path: Path
    ) -> None:
        # Write a minimal claude-audit clink config
        clink_cfg = {
            "name": "claude-audit",
            "command": "claude-audit-mock",
            "additional_args": [],
            "env": {},
            "roles": {"codereviewer": {"prompt_path": "systemprompts/clink/default_codereviewer.txt", "role_args": []}},
        }
        (tmp_path / "claude-audit.json").write_text(json.dumps(clink_cfg))

        stats = PrDiffStats(files_changed=1, lines_added=10, lines_deleted=5)
        # Mock shutil.which to report the command found
        with patch("scripts.audit.pr_audit_router.probe_capability", return_value=True):
            plan = build_audit_plan(stats, conf_dir=tmp_path)

        assert plan.has_any_available()

    def test_plan_requested_route_names_match_tier(self, tmp_path: Path) -> None:
        stats = PrDiffStats(files_changed=1, lines_added=10, lines_deleted=5, touches_schema=True)
        plan = build_audit_plan(stats, conf_dir=tmp_path)
        assert set(plan.requested_route_names) == set(_RISK_TIER_ROUTES[PrRiskClass.MEDIUM])


# ---------------------------------------------------------------------------
# write_proof_artifact
# ---------------------------------------------------------------------------

class TestWriteProofArtifact:
    def test_creates_multi_model_pr_audit_json(self, tmp_path: Path) -> None:
        plan = _make_plan()
        path = write_proof_artifact(plan, out=tmp_path, packet_id="TP-001")
        assert path.name == "MULTI_MODEL_PR_AUDIT.json"
        assert path.exists()

    def test_proof_is_valid_json(self, tmp_path: Path) -> None:
        plan = _make_plan()
        path = write_proof_artifact(plan, out=tmp_path, packet_id="TP-001")
        proof = json.loads(path.read_text())
        assert isinstance(proof, dict)

    def test_proof_contains_required_fields(self, tmp_path: Path) -> None:
        plan = _make_plan(risk=PrRiskClass.MEDIUM)
        path = write_proof_artifact(plan, out=tmp_path, packet_id="TP-002", git_sha="abc123")
        proof = json.loads(path.read_text())
        assert proof["packet_id"] == "TP-002"
        assert proof["head_sha"] == "abc123"
        assert proof["risk_class"] == "MEDIUM"
        assert proof["dry_run"] is True
        assert proof["executed"] is False
        assert proof["schema_version"] == "1.0"

    def test_proof_dry_run_flag_propagates(self, tmp_path: Path) -> None:
        plan = _make_plan(dry_run=True)
        path = write_proof_artifact(plan, out=tmp_path, packet_id="TP-003")
        proof = json.loads(path.read_text())
        assert proof["dry_run"] is True

    def test_dry_run_proof_is_not_a_passing_embedded_audit(self, tmp_path: Path) -> None:
        plan = _make_plan(dry_run=True)
        path = write_proof_artifact(plan, out=tmp_path, packet_id="TP-003")
        proof = json.loads(path.read_text())

        assert proof["executed"] is False
        assert proof["embedded_audit"]["status"] == "NEEDS_SUPERVISOR"

    def test_proof_resolutions_include_blocking_flag(self, tmp_path: Path) -> None:
        resolutions = (
            RouteResolution(cli_name="claude-audit", available=False, blocking=True),
            RouteResolution(cli_name="xai-grok-audit", available=False, blocking=False),
        )
        plan = MultiModelAuditPlan(
            risk_class=PrRiskClass.HIGH,
            requested_route_names=("claude-audit", "xai-grok-audit"),
            resolutions=resolutions,
            dry_run=True,
        )
        path = write_proof_artifact(plan, out=tmp_path, packet_id="TP-004")
        proof = json.loads(path.read_text())
        by_name = {r["cli_name"]: r for r in proof["resolutions"]}
        assert by_name["claude-audit"]["blocking"] is True
        assert by_name["xai-grok-audit"]["blocking"] is False

    def test_out_dir_created_if_missing(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c"
        plan = _make_plan()
        path = write_proof_artifact(plan, out=nested, packet_id="TP-005")
        assert path.exists()

    def test_schema_validation_fails_closed_on_bad_proof(self, tmp_path: Path) -> None:  # noqa: ARG002
        with pytest.raises(ValueError, match="schema-invalid"):
            _validate_proof({})

    def test_schema_validation_fails_on_invalid_risk_class(self, tmp_path: Path) -> None:  # noqa: ARG002
        proof = {
            "schema_version": "1.0",
            "packet_id": "X",
            "head_sha": "abc",
            "dry_run": True,
            "risk_class": "EXTREME",  # invalid
            "requested_route_names": [],
            "resolutions": [],
            "blocking_available_count": 0,
            "has_any_available": False,
            "executed": False,
            "execution_results": [],
        }
        with pytest.raises(ValueError, match="risk_class"):
            _validate_proof(proof)


# ---------------------------------------------------------------------------
# Schema files exist and are valid JSON
# ---------------------------------------------------------------------------

class TestSchemaFiles:
    def test_multi_model_pr_audit_schema_exists(self) -> None:
        assert SCHEMA_PATH.exists(), f"Missing: {SCHEMA_PATH}"

    def test_multi_model_pr_audit_schema_is_valid_json(self) -> None:
        data = json.loads(SCHEMA_PATH.read_text())
        assert data.get("title") == "Multi-Model PR Audit Proof Artifact"

    def test_pr_risk_schema_exists(self) -> None:
        assert PR_RISK_SCHEMA_PATH.exists(), f"Missing: {PR_RISK_SCHEMA_PATH}"

    def test_pr_risk_schema_is_valid_json(self) -> None:
        data = json.loads(PR_RISK_SCHEMA_PATH.read_text())
        assert "files_changed" in data["properties"]

    def test_xai_grok_clink_config_exists(self) -> None:
        cfg = AUDIT_EXTRA_CLINK_CONF_DIR / "xai-grok-audit.json"
        assert cfg.exists()

    def test_cheaperinference_clink_config_exists(self) -> None:
        cfg = AUDIT_EXTRA_CLINK_CONF_DIR / "cheaperinference-audit.json"
        assert cfg.exists()

    def test_xai_grok_clink_config_name_not_forbidden(self) -> None:
        from scripts.audit.route_schema import FORBIDDEN_CLI_NAMES
        cfg_path = AUDIT_EXTRA_CLINK_CONF_DIR / "xai-grok-audit.json"
        data = json.loads(cfg_path.read_text())
        assert data["name"] not in FORBIDDEN_CLI_NAMES

    def test_cheaperinference_clink_config_name_not_forbidden(self) -> None:
        from scripts.audit.route_schema import FORBIDDEN_CLI_NAMES
        cfg_path = AUDIT_EXTRA_CLINK_CONF_DIR / "cheaperinference-audit.json"
        data = json.loads(cfg_path.read_text())
        assert data["name"] not in FORBIDDEN_CLI_NAMES

    def test_pal_cli_clients_exclude_unsupported_clink_runners(self) -> None:
        for cfg_path in sorted(PAL_CLINK_CONF_DIR.glob("*.json")):
            data = json.loads(cfg_path.read_text())
            runner = (data.get("runner") or data.get("name", "")).strip().lower()
            assert runner in PAL_SUPPORTED_CLINK_RUNNERS, (
                f"{cfg_path.name} uses unsupported clink runner {runner!r}; "
                "move planned audit routes to scripts/audit/fixtures/clink_clients/"
            )
