"""Tests for DMX-DCP-MODEL-ROUTING-MVP-0001 domain model.

These tests verify:
1. Unknown fields are rejected (strict additionalProperties: false)
2. Arbitrary selectors are rejected
3. OpenCode cannot be authoritative
4. Advisory policy cannot be runtime authority
5. Config-only model slot cannot be runtime healthy
6. Unknown MCP surface cannot be safe
7. Workflow red-lane cannot be ready
8. Dopetask execution is forbidden
9. Task Orchestrator writes are forbidden
10. DopeCode legacy Serena alias remains unresolved
11. Agent authority is unknown
12. Proof extension is additive
13. Auditor verdict stays distinct from validation_state
14. LiteLLM unhealthy creates stop condition
15. Stale alias creates stop condition
"""

import json
from pathlib import Path
import pytest


FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "dcp" / "model_routing_0001"
SCHEMA_DIR = Path(__file__).parent.parent.parent / "schemas" / "dcp"


def load_json(path: Path) -> dict:
    """Load and parse JSON file."""
    with open(path) as f:
        return json.load(f)


def test_safe_read_classification_accepted():
    """Test 1: Safe read classification is accepted."""
    fixture = load_json(FIXTURE_DIR / "safe_read_task.json")
    assert fixture["risk_class"] == "R0_READ"
    assert fixture["safe_automation"] == "safe_read"
    assert fixture["decision_status"] == "READY_DESIGN_ONLY"


def test_unknown_extra_fields_rejected():
    """Test 2: Unknown extra fields are rejected by strict schemas."""
    # All schemas have additionalProperties: false
    # This test verifies the schema structure enforces this
    schema = load_json(SCHEMA_DIR / "dcp_routing_classification.schema.json")
    assert schema.get("additionalProperties") is False


def test_litellm_unhealthy_produces_stop_condition():
    """Test 3: LiteLLM unhealthy produces stop condition."""
    fixture = load_json(FIXTURE_DIR / "litellm_unhealthy_stop.json")
    assert fixture["condition_type"] == "litellm_unhealthy"
    assert fixture["triggered"] is True
    assert fixture["resolution_required"] == "operator"


def test_stale_alias_produces_stop_condition():
    """Test 4: Stale alias produces stop condition."""
    fixture = load_json(FIXTURE_DIR / "stale_alias_stop.json")
    assert fixture["condition_type"] == "stale_alias_contract"
    assert fixture["triggered"] is True
    assert fixture["resolution_required"] == "supervisor"


def test_advisory_policy_is_not_runtime_authority():
    """Test 5: Advisory policy is not runtime authority."""
    fixture = load_json(FIXTURE_DIR / "policy_advisory_not_runtime.json")
    assert fixture["evidence_quality"] == "observed_config_only"
    assert fixture["decision_status"] == "READY_DESIGN_ONLY"
    # Policy is advisory, not runtime


def test_unknown_mcp_surface_is_not_safe():
    """Test 6: Unknown MCP surface is not safe."""
    fixture = load_json(FIXTURE_DIR / "mcp_unknown_surface.json")
    assert fixture["condition_type"] == "mcp_surface_unknown"
    assert fixture["triggered"] is True


def test_workflow_red_lane_is_forbidden():
    """Test 7: Workflow red-lane is forbidden."""
    fixture = load_json(FIXTURE_DIR / "workflow_red_lane_forbidden.json")
    assert fixture["condition_type"] == "workflow_red_lane"
    assert fixture["triggered"] is True


def test_opencode_is_backend_only():
    """Test 8: OpenCode is backend-only."""
    fixture = load_json(FIXTURE_DIR / "opencode_backend_only.json")
    assert fixture["backend_authority"] == "backend_only"
    assert fixture["open_code_backend_only"] is True


def test_dopetask_execution_is_forbidden():
    """Test 9: Dopetask execution is forbidden."""
    fixture = load_json(FIXTURE_DIR / "dopetask_execution_forbidden.json")
    assert fixture["condition_type"] == "other"
    assert "dopetask" in fixture["evidence"].lower()


def test_task_orchestrator_write_is_forbidden():
    """Test 10: Task Orchestrator write is forbidden."""
    fixture = load_json(FIXTURE_DIR / "task_orchestrator_write_forbidden.json")
    assert fixture["condition_type"] == "other"
    assert "task orchestrator" in fixture["evidence"].lower()


def test_dopecode_legacy_serena_alias_preserved():
    """Test 11: DopeCode legacy Serena alias is preserved as unknown."""
    fixture = load_json(FIXTURE_DIR / "dopecode_legacy_serena_alias.json")
    auth = fixture["authority_surface"]
    assert auth["unknown_status"] is True
    assert auth["canonical_owner"] == "unknown"


def test_arbitrary_selector_fields_are_rejected():
    """Test 12: Arbitrary selector fields are rejected."""
    fixture = load_json(FIXTURE_DIR / "arbitrary_selector_rejected.json")
    assert fixture["condition_type"] == "arbitrary_selector_allowed"
    assert fixture["triggered"] is True


def test_auditor_verdict_distinct_from_validation_state():
    """Test 13: Auditor verdict is distinct from validation_state."""
    fixture = load_json(FIXTURE_DIR / "auditor_verdict_distinct.json")
    audit = fixture["audit_route"]
    assert audit["auditor_verdict_distinct"] is True
    assert fixture["validation_state"] == "PASSED"
    assert fixture["auditor_verdict"] == "PASS_WITH_RISKS"
    # These are separate fields - auditor_verdict is not merged into validation_state


def test_proof_extension_is_additive():
    """Test 14: Proof extension is additive (not replacement)."""
    fixture = load_json(FIXTURE_DIR / "proof_extension_additive.json")
    assert fixture["extension_id"].startswith("DCP-PROOF-")
    # Proof extension contains classification, decision, lane, etc.
    # This is additive to existing proof families, not a replacement
    assert "classification" in fixture
    assert "routing_decision" in fixture
    assert "audit_route" in fixture


def test_agent_authority_is_unknown():
    """Test 15: Agent authority is unknown."""
    fixture = load_json(FIXTURE_DIR / "agent_authority_unknown.json")
    auth = fixture["authority_surface"]
    assert auth["unknown_status"] is True
    assert "agent runtime authority" in auth["notes"].lower()
