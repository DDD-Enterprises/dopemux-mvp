import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator, ValidationError, validate


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = REPO_ROOT / "contracts" / "openclaw-dcp-routing"
EXAMPLE_ROOT = CONTRACT_ROOT / "example_route_decisions"

REQUIRED_ARTIFACTS = [
    "README.md",
    "openclaw_dcp_routing_policy.yaml",
    "routing_classifier.schema.json",
    "route_decision.schema.json",
    "model_pool_registry.yaml",
    "privacy_class_policy.yaml",
    "risk_class_policy.yaml",
    "forbidden_routes.yaml",
    "human_approval_gates.yaml",
    "openrouter_route_profiles.json",
    "structured_output_policy.json",
    "proof_requirements.schema.json",
    "audit_independence_rules.yaml",
    "release_gate_policy.yaml",
    "runner_adapter_contract.md",
    "openclaw_proof_normalization_contract.md",
    "route_decision_logger.schema.json",
    "provider_availability_probe_spec.md",
    "cost_policy.yaml",
    "local_benchmark_harness_requirements.md",
    "benchmark_fixture_manifest.yaml",
    "benchmark_result.schema.json",
    "route_certification_ledger.schema.json",
    "pr_steward_merge_readiness.schema.json",
    "example_route_decisions/R0_READ.json",
    "example_route_decisions/R1_DRAFT.json",
    "example_route_decisions/R2_TEST_ONLY.json",
    "example_route_decisions/R3_LOCAL_EDIT.json",
    "example_route_decisions/R4_MULTI_FILE_EDIT.json",
    "example_route_decisions/R5_SECURITY_OR_AUTHORITY.json",
    "example_route_decisions/R6_RELEASE_OR_PRODUCTION.json",
    "example_route_decisions/UNKNOWN.json",
    "TURN4_ACCEPTANCE_CHECKLIST.md",
]

JSON_SCHEMA_FILES = [
    "routing_classifier.schema.json",
    "route_decision.schema.json",
    "proof_requirements.schema.json",
    "route_decision_logger.schema.json",
    "benchmark_result.schema.json",
    "route_certification_ledger.schema.json",
    "pr_steward_merge_readiness.schema.json",
]

EXAMPLE_FILES = [
    "R0_READ.json",
    "R1_DRAFT.json",
    "R2_TEST_ONLY.json",
    "R3_LOCAL_EDIT.json",
    "R4_MULTI_FILE_EDIT.json",
    "R5_SECURITY_OR_AUTHORITY.json",
    "R6_RELEASE_OR_PRODUCTION.json",
    "UNKNOWN.json",
]


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_required_artifacts_exist():
    missing = [path for path in REQUIRED_ARTIFACTS if not (CONTRACT_ROOT / path).is_file()]
    assert missing == []


@pytest.mark.parametrize("path", sorted(CONTRACT_ROOT.glob("**/*.json")))
def test_json_artifacts_parse(path: Path):
    assert _json(path)


@pytest.mark.parametrize("path", sorted(CONTRACT_ROOT.glob("**/*.yaml")))
def test_yaml_artifacts_parse(path: Path):
    assert _yaml(path)


@pytest.mark.parametrize("relative_path", JSON_SCHEMA_FILES)
def test_json_schemas_load(relative_path: str):
    schema = _json(CONTRACT_ROOT / relative_path)

    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema["type"] == "object"
    assert "properties" in schema
    assert "required" in schema
    Draft7Validator.check_schema(schema)


@pytest.mark.parametrize("example_name", EXAMPLE_FILES)
def test_example_route_decisions_validate(example_name: str):
    schema = _json(CONTRACT_ROOT / "route_decision.schema.json")
    example = _json(EXAMPLE_ROOT / example_name)

    validate(instance=example, schema=schema)


def test_unknown_route_decision_blocks_or_escalates_with_unknown_reasons():
    unknown = _json(EXAMPLE_ROOT / "UNKNOWN.json")

    assert unknown["decision_status"] in {"BLOCKED", "ESCALATED", "NEEDS_SUPERVISOR"}
    assert "UNKNOWN_PRIVACY_CLASS" in unknown["blocked_reasons"]
    assert "UNKNOWN_RISK_CLASS" in unknown["blocked_reasons"]
    assert unknown["human_gate_required"] is True


def test_route_decision_schema_blocks_unknown_privacy_or_risk_selection():
    schema = _json(CONTRACT_ROOT / "route_decision.schema.json")
    example = _json(EXAMPLE_ROOT / "R0_READ.json")

    for field, reason in [
        ("privacy_class", "UNKNOWN_PRIVACY_CLASS"),
        ("risk_class", "UNKNOWN_RISK_CLASS"),
    ]:
        candidate = copy.deepcopy(example)
        candidate[field] = "UNKNOWN"
        candidate["blocked_reasons"] = [reason]

        with pytest.raises(ValidationError):
            validate(instance=candidate, schema=schema)

        candidate["decision_status"] = "BLOCKED"
        validate(instance=candidate, schema=schema)


def test_openrouter_free_cannot_be_private_high_risk_or_schema_authority():
    schema = _json(CONTRACT_ROOT / "route_decision.schema.json")
    example = _json(EXAMPLE_ROOT / "R0_READ.json")

    forbidden_cases = [
        {"privacy_class": "PRIVATE_REPO_NO_SECRETS"},
        {"privacy_class": "SECRET_BEARING"},
        {"privacy_class": "CLIENT_DATA"},
        {"privacy_class": "SECURITY_SENSITIVE"},
        {"privacy_class": "RELEASE_AUTHORITY"},
        {"risk_class": "R5_SECURITY_OR_AUTHORITY"},
        {"risk_class": "R6_RELEASE_OR_PRODUCTION"},
        {"role": "proof_validation"},
        {"role": "structured_task_packet_generation"},
        {"role": "proof_bundle_generation"},
        {"role": "security_review"},
        {"role": "release_judgment"},
        {"structured_output_mode": "json_schema_strict"},
    ]

    for patch in forbidden_cases:
        candidate = {**example, **patch}
        with pytest.raises(ValidationError):
            validate(instance=candidate, schema=schema)


def test_selected_gated_route_requires_non_empty_human_approval_ref():
    schema = _json(CONTRACT_ROOT / "route_decision.schema.json")
    release = _json(EXAMPLE_ROOT / "R6_RELEASE_OR_PRODUCTION.json")

    validate(instance=release, schema=schema)

    for missing_ref in [None, ""]:
        candidate = copy.deepcopy(release)
        candidate["human_approval_ref"] = missing_ref

        with pytest.raises(ValidationError):
            validate(instance=candidate, schema=schema)

    blocked = copy.deepcopy(release)
    blocked["decision_status"] = "BLOCKED"
    blocked["human_approval_ref"] = None
    blocked["blocked_reasons"] = ["MISSING_HUMAN_APPROVAL"]
    validate(instance=blocked, schema=schema)


def test_selected_high_risk_route_must_set_human_gate():
    schema = _json(CONTRACT_ROOT / "route_decision.schema.json")
    security = _json(EXAMPLE_ROOT / "R5_SECURITY_OR_AUTHORITY.json")

    validate(instance=security, schema=schema)

    for patch in [
        {"human_gate_required": False},
        {"human_gate_required": True, "human_approval_ref": None},
        {"human_gate_required": True, "human_approval_ref": ""},
    ]:
        candidate = {**security, **patch}
        with pytest.raises(ValidationError):
            validate(instance=candidate, schema=schema)


def test_selected_trust_or_certified_lanes_require_benchmark_certification():
    schema = _json(CONTRACT_ROOT / "route_decision.schema.json")

    certified_examples = [
        _json(EXAMPLE_ROOT / "R3_LOCAL_EDIT.json"),
        _json(EXAMPLE_ROOT / "R4_MULTI_FILE_EDIT.json"),
        _json(EXAMPLE_ROOT / "R5_SECURITY_OR_AUTHORITY.json"),
        _json(EXAMPLE_ROOT / "R6_RELEASE_OR_PRODUCTION.json"),
    ]
    for example in certified_examples:
        validate(instance=example, schema=schema)

        candidate = copy.deepcopy(example)
        candidate["benchmark_certification_ref"] = None
        with pytest.raises(ValidationError):
            validate(instance=candidate, schema=schema)

        candidate["benchmark_certification_ref"] = ""
        with pytest.raises(ValidationError):
            validate(instance=candidate, schema=schema)


def test_selected_route_cannot_retain_blocked_reasons():
    schema = _json(CONTRACT_ROOT / "route_decision.schema.json")
    example = _json(EXAMPLE_ROOT / "R0_READ.json")

    candidate = copy.deepcopy(example)
    candidate["blocked_reasons"] = ["MISSING_SCHEMA_VALIDATION"]

    with pytest.raises(ValidationError):
        validate(instance=candidate, schema=schema)


def test_release_example_requires_human_gate_and_current_release_proof_posture():
    release = _json(EXAMPLE_ROOT / "R6_RELEASE_OR_PRODUCTION.json")

    assert release["risk_class"] == "R6_RELEASE_OR_PRODUCTION"
    assert release["role"] == "release_judgment"
    assert release["proof_requirement"] == "release"
    assert release["audit_requirement"] == "release"
    assert release["human_gate_required"] is True
    assert release["human_approval_ref"]
    assert release["benchmark_certification_ref"]
    assert any("merge_readiness:" in ref for ref in release["evidence_refs"])
    assert any("audit:" in ref for ref in release["evidence_refs"])


def test_pr_steward_ready_is_impossible_with_blocking_constraints():
    schema = _json(CONTRACT_ROOT / "pr_steward_merge_readiness.schema.json")
    ready = {
        "schema_version": "1.0.0",
        "pr_number": 123,
        "repo": "DDD-Enterprises/dopemux-mvp",
        "branch": "turn5-contracts",
        "head_sha": "abcdef1234567890",
        "base_branch": "main",
        "changed_files": ["contracts/openclaw-dcp-routing/README.md"],
        "commits": [{"sha": "abcdef1234567890", "message": "test"}],
        "checks": [
            {
                "name": "contract-tests",
                "status": "completed",
                "conclusion": "success",
                "head_sha": "abcdef1234567890",
            }
        ],
        "review_comments": [],
        "review_threads": [],
        "issue_comments": [],
        "bot_comments": [],
        "proof_bundle_refs": ["proof/ref"],
        "audit_refs": ["audit/ref"],
        "review_item_classifications": [],
        "unknown_reviewers_or_bots": [],
        "unclassified_review_items": [],
        "failed_checks": [],
        "checks_stale_to_head": False,
        "proof_stale": False,
        "blocking_thread_unresolved": False,
        "diff_escapes_packet_allowlist": False,
        "security_release_gate_lacks_approval": False,
        "unresolved_blockers": [],
        "status": "READY",
        "created_at": "2026-06-17T12:00:00Z",
    }
    validate(instance=ready, schema=schema)

    blocking_variants = [
        ("unknown_reviewers_or_bots", ["unknown-reviewer"]),
        ("unclassified_review_items", ["review-item-1"]),
        ("failed_checks", ["contract-tests"]),
        ("checks_stale_to_head", True),
        ("proof_stale", True),
        ("blocking_thread_unresolved", True),
        ("diff_escapes_packet_allowlist", True),
        ("security_release_gate_lacks_approval", True),
        ("unresolved_blockers", ["missing-security-approval"]),
        ("proof_bundle_refs", []),
        ("audit_refs", []),
    ]

    for field, value in blocking_variants:
        blocked = copy.deepcopy(ready)
        blocked[field] = value
        with pytest.raises(ValidationError):
            validate(instance=blocked, schema=schema)


def test_openrouter_profiles_preserve_required_fail_closed_controls():
    profiles = _json(CONTRACT_ROOT / "openrouter_route_profiles.json")["profiles"]

    free = profiles["or_free_sandbox"]
    assert "security_review" in free["forbidden_roles"]
    assert "release_judgment" in free["forbidden_roles"]
    assert "proof_validation" in free["forbidden_roles"]
    assert "structured_task_packet_generation" in free["forbidden_roles"]
    assert "proof_bundle_generation" in free["forbidden_roles"]

    private = profiles["or_paid_private_controlled"]
    assert private["data_collection"] == "deny"
    assert private["zdr"] is True
    assert private["required_provider_settings"]["data_collection"] == "deny"
    assert private["required_provider_settings"]["zdr"] is True

    structured = profiles["or_structured_noncritical"]
    assert structured["require_parameters"] is True
    assert structured["required_provider_settings"]["require_parameters"] is True
    assert structured["required_provider_settings"]["response_format"] == "json_schema"
    assert structured["required_provider_settings"]["strict"] is True
