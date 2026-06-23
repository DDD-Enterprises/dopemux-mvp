"""
Tests for the DCP routing extension contracts (Packet 6).

These tests validate schema shape only. They do not execute routing, call
providers, or certify OpenClaw/OpenRouter runtime behavior.
"""

import copy
import json
import pathlib

import pytest
from jsonschema import Draft202012Validator

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_ROUTING_SCHEMAS = _REPO_ROOT / "schemas" / "dcp_extension" / "routing"

_ROUTE_DECISION_SCHEMA_PATH = _ROUTING_SCHEMAS / "route_decision.schema.json"
_LANE_ENGINE_SCHEMA_PATH = _ROUTING_SCHEMAS / "lane_engine.schema.json"
_OPENCLAW_ROUTE_SCHEMA_PATH = _ROUTING_SCHEMAS / "openclaw_route.schema.json"


def _load(path: pathlib.Path) -> dict:
    with path.open() as fh:
        return json.load(fh)


ROUTE_DECISION_SCHEMA = _load(_ROUTE_DECISION_SCHEMA_PATH)
LANE_ENGINE_SCHEMA = _load(_LANE_ENGINE_SCHEMA_PATH)
OPENCLAW_ROUTE_SCHEMA = _load(_OPENCLAW_ROUTE_SCHEMA_PATH)


def errors(schema: dict, instance: dict) -> list:
    return list(Draft202012Validator(schema).iter_errors(instance))


def valid_selected_route_decision() -> dict:
    model = "openrouter/public-low-risk"
    return {
        "schema_version": "dcp.routing.route_decision.v0",
        "decision_id": "rd_packet6_selected",
        "task_ref": "TP-DMX-DCP-ROUTING-EXTENSION-MAPPING-0001",
        "role": "cheap_file_reading",
        "lane_id": "public_read",
        "privacy_class": "PUBLIC_REPO",
        "risk_class": "R0_READ",
        "decision": "SELECTED",
        "selected_pool": "cheap_read",
        "selected_route": {
            "route_name": "route_public_openrouter_free",
            "route_profile": "public_low_risk",
            "selection_reason": "public read lane",
            "fallback_allowed": False,
        },
        "selected_route_id": "route_public_openrouter_free",
        "selected_provider": "openrouter",
        "selected_model": model,
        "provider": "openrouter",
        "requested_model": model,
        "actual_model": model,
        "actual_provider": "openrouter",
        "runner": "openrouter",
        "access_path": "openrouter_free",
        "consumer_plan_used": False,
        "api_route_used": True,
        "openrouter_profile": "or_free_sandbox",
        "structured_output_mode": "none",
        "live_write_runner_selected": False,
        "blocked_reasons": [],
        "proof_requirement": "minimal",
        "audit_requirement": "none",
        "human_gate_required": False,
        "human_approval_ref": None,
        "benchmark_certification_ref": None,
        "evidence_refs": ["docs/03-reference/dcp/dcp-routing-extension.md"],
        "created_at": "2026-06-22T00:00:00Z",
    }


def valid_blocked_route_decision() -> dict:
    return {
        "schema_version": "dcp.routing.route_decision.v0",
        "decision_id": "rd_packet6_blocked",
        "task_ref": "TP-DMX-DCP-ROUTING-EXTENSION-MAPPING-0001",
        "role": "security_review",
        "lane_id": "protected_authority",
        "privacy_class": "SECURITY_SENSITIVE",
        "risk_class": "R5_SECURITY_OR_AUTHORITY",
        "decision": "BLOCKED",
        "selected_pool": "security_release",
        "selected_route": None,
        "selected_route_id": None,
        "selected_provider": None,
        "selected_model": None,
        "provider": None,
        "requested_model": None,
        "actual_model": None,
        "actual_provider": None,
        "runner": None,
        "access_path": None,
        "consumer_plan_used": None,
        "api_route_used": None,
        "openrouter_profile": None,
        "structured_output_mode": "json_schema_strict",
        "live_write_runner_selected": False,
        "blocked_reasons": ["OPENROUTER_FREE_FORBIDDEN"],
        "proof_requirement": "security",
        "audit_requirement": "independent",
        "human_gate_required": True,
        "human_approval_ref": None,
        "benchmark_certification_ref": None,
        "evidence_refs": ["docs/03-reference/dcp/dcp-routing-extension.md"],
        "created_at": "2026-06-22T00:00:00Z",
    }


def valid_lane_engine() -> dict:
    return {
        "schema_version": "dcp.routing.lane_engine.v0",
        "default_unknown_behavior": "BLOCK_OR_ESCALATE",
        "live_write_runner_allowed": False,
        "lanes": [
            {
                "lane_id": "public_read",
                "privacy_classes": ["PUBLIC_SANDBOX", "PUBLIC_REPO"],
                "risk_classes": ["R0_READ", "R1_DRAFT"],
                "allowed_access_paths": ["direct_api", "local_self_hosted", "openrouter_free"],
                "forbidden_access_paths": [],
                "proof_requirement": "minimal",
                "audit_requirement": "none",
                "requires_human_approval": False,
                "fail_closed_on_unknown": True,
            },
            {
                "lane_id": "protected_authority",
                "privacy_classes": [
                    "PRIVATE_REPO_POSSIBLE_SECRETS",
                    "SECURITY_SENSITIVE",
                    "RELEASE_AUTHORITY",
                    "UNKNOWN",
                ],
                "risk_classes": [
                    "R5_SECURITY_OR_AUTHORITY",
                    "R6_RELEASE_OR_PRODUCTION",
                    "UNKNOWN",
                ],
                "allowed_access_paths": ["direct_api", "local_self_hosted", "manual_app"],
                "forbidden_access_paths": ["openrouter_free"],
                "proof_requirement": "security",
                "audit_requirement": "independent",
                "requires_human_approval": True,
                "fail_closed_on_unknown": True,
            },
        ],
    }


def valid_openclaw_route() -> dict:
    return {
        "schema_version": "dcp.routing.openclaw_route.v0",
        "route_id": "route_direct_frontier_authority",
        "route_kind": "direct_api",
        "provider": "openai",
        "access_path": "direct_api",
        "runner": "codex",
        "allowed_for_privacy_classes": ["SECURITY_SENSITIVE", "RELEASE_AUTHORITY"],
        "allowed_for_risk_classes": ["R5_SECURITY_OR_AUTHORITY", "R6_RELEASE_OR_PRODUCTION"],
        "openrouter_free": False,
        "benchmark_required": True,
        "structured_output_required": True,
        "proof_capture_required": True,
        "may_be_sole_authority": False,
        "live_write_runner": False,
        "status": "PROPOSED",
    }


class TestRouteDecisionContract:
    def test_selected_route_decision_validates(self):
        errs = errors(ROUTE_DECISION_SCHEMA, valid_selected_route_decision())
        assert errs == [], f"selected route decision has schema errors: {errs}"

    def test_blocked_route_decision_validates(self):
        errs = errors(ROUTE_DECISION_SCHEMA, valid_blocked_route_decision())
        assert errs == [], f"blocked route decision has schema errors: {errs}"

    def test_openrouter_free_is_rejected_for_protected_lane(self):
        tampered = valid_selected_route_decision()
        tampered["lane_id"] = "protected_authority"
        tampered["privacy_class"] = "SECURITY_SENSITIVE"
        tampered["risk_class"] = "R5_SECURITY_OR_AUTHORITY"
        tampered["proof_requirement"] = "security"
        tampered["audit_requirement"] = "independent"
        errs = errors(ROUTE_DECISION_SCHEMA, tampered)
        assert errs, "protected lanes must not select openrouter_free"

    def test_blocked_decision_requires_blocked_reason(self):
        tampered = valid_blocked_route_decision()
        tampered["blocked_reasons"] = []
        errs = errors(ROUTE_DECISION_SCHEMA, tampered)
        assert errs, "BLOCKED route decisions must carry at least one blocked reason"

    def test_route_decision_rejects_extra_fields(self):
        tampered = valid_selected_route_decision()
        tampered["runtime_router_enabled"] = True
        errs = errors(ROUTE_DECISION_SCHEMA, tampered)
        assert errs, "route decision contract must reject undeclared runtime fields"


class TestLaneEngineContract:
    def test_lane_engine_validates(self):
        errs = errors(LANE_ENGINE_SCHEMA, valid_lane_engine())
        assert errs == [], f"lane engine has schema errors: {errs}"

    def test_lane_engine_forbids_live_write_runner(self):
        tampered = valid_lane_engine()
        tampered["live_write_runner_allowed"] = True
        errs = errors(LANE_ENGINE_SCHEMA, tampered)
        assert errs, "routing contract must not allow live-write runners"

    def test_unknown_lane_fails_closed(self):
        tampered = valid_lane_engine()
        tampered["default_unknown_behavior"] = "ALLOW"
        errs = errors(LANE_ENGINE_SCHEMA, tampered)
        assert errs, "unknown routing conditions must fail closed"


class TestRouteDecisionNegativeFixtures:
    @pytest.mark.parametrize(
        "fixture_name",
        [
            "invalid_selected_unknown_provider.json",
            "invalid_selected_unknown_actual_model.json",
            "invalid_selected_openrouter_free_private.json",
            "invalid_selected_r5_missing_human_approval.json",
            "invalid_selected_r5_missing_benchmark.json",
            "invalid_selected_live_write_runner_true.json",
            "invalid_selected_structured_without_strict_mode.json",
        ],
    )
    def test_invalid_fixtures_fail_schema(self, fixture_name: str):
        fixture_path = _REPO_ROOT / "tests" / "dcp_extension" / "fixtures" / "routing" / fixture_name
        instance = _load(fixture_path)
        errs = errors(ROUTE_DECISION_SCHEMA, instance)
        assert errs, f"expected invalid fixture to fail: {fixture_name}"

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "valid_blocked_unknown_privacy.json",
            "valid_selected_public_read_direct_api.json",
            "valid_selected_r4_with_embedded_audit.json",
            "valid_selected_r5_with_independent_audit_and_approval.json",
        ],
    )
    def test_valid_fixtures_pass_schema(self, fixture_name: str):
        fixture_path = _REPO_ROOT / "tests" / "dcp_extension" / "fixtures" / "routing" / fixture_name
        instance = _load(fixture_path)
        errs = errors(ROUTE_DECISION_SCHEMA, instance)
        assert errs == [], f"valid fixture failed schema: {fixture_name} -> {errs}"


class TestOpenClawRouteContract:
    def test_openclaw_route_validates(self):
        errs = errors(OPENCLAW_ROUTE_SCHEMA, valid_openclaw_route())
        assert errs == [], f"OpenClaw route has schema errors: {errs}"

    def test_openrouter_free_rejected_for_security_or_release_route(self):
        tampered = copy.deepcopy(valid_openclaw_route())
        tampered["route_id"] = "route_bad_openrouter_free_authority"
        tampered["route_kind"] = "openrouter_free"
        tampered["provider"] = "openrouter"
        tampered["access_path"] = "openrouter_free"
        tampered["openrouter_free"] = True
        errs = errors(OPENCLAW_ROUTE_SCHEMA, tampered)
        assert errs, "OpenRouter-free route must not cover security or release classes"

    def test_openclaw_route_forbids_live_write_runner(self):
        tampered = valid_openclaw_route()
        tampered["live_write_runner"] = True
        errs = errors(OPENCLAW_ROUTE_SCHEMA, tampered)
        assert errs, "OpenClaw route contract must not define live-write runners"
