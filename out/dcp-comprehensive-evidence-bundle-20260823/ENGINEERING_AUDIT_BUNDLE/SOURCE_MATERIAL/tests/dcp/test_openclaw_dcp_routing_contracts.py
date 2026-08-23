import copy
import json
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "contracts" / "openclaw-dcp-routing"
EXAMPLES_DIR = ARTIFACT_DIR / "example_route_decisions"

EXPECTED_JSON = {
    "routing_classifier.schema.json",
    "route_decision.schema.json",
    "openrouter_route_profiles.json",
    "structured_output_policy.json",
    "proof_requirements.schema.json",
    "route_decision_logger.schema.json",
    "benchmark_result.schema.json",
    "route_certification_ledger.schema.json",
    "pr_steward_merge_readiness.schema.json",
}

EXPECTED_YAML = {
    "openclaw_dcp_routing_policy.yaml",
    "model_pool_registry.yaml",
    "privacy_class_policy.yaml",
    "risk_class_policy.yaml",
    "forbidden_routes.yaml",
    "human_approval_gates.yaml",
    "audit_independence_rules.yaml",
    "release_gate_policy.yaml",
    "cost_policy.yaml",
    "benchmark_fixture_manifest.yaml",
}

EXPECTED_MARKDOWN = {
    "README.md",
    "runner_adapter_contract.md",
    "openclaw_proof_normalization_contract.md",
    "provider_availability_probe_spec.md",
    "local_benchmark_harness_requirements.md",
    "TURN4_ACCEPTANCE_CHECKLIST.md",
}

EXPECTED_EXAMPLES = {
    "R0_READ.json",
    "R1_DRAFT.json",
    "R2_TEST_ONLY.json",
    "R3_LOCAL_EDIT.json",
    "R4_MULTI_FILE_EDIT.json",
    "R5_SECURITY_OR_AUTHORITY.json",
    "R6_RELEASE_OR_PRODUCTION.json",
    "UNKNOWN.json",
}


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def schema_validator(schema_name: str) -> Draft7Validator:
    schema = load_json(ARTIFACT_DIR / schema_name)
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def assert_valid(validator: Draft7Validator, instance: dict) -> None:
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    assert not errors, "\n".join(error.message for error in errors)


def assert_invalid(validator: Draft7Validator, instance: dict) -> None:
    assert list(validator.iter_errors(instance))


def valid_merge_readiness() -> dict:
    return {
        "schema_version": "1.0.0",
        "pr_number": 123,
        "repo": "DDD-Enterprises/dopemux-mvp",
        "branch": "codex/example",
        "head_sha": "abcdef1234567890",
        "base_branch": "main",
        "changed_files": ["contracts/openclaw-dcp-routing/route_decision.schema.json"],
        "commits": [{"sha": "abcdef1234567890", "message": "feat(dcp): add contracts"}],
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
        "proof_bundle_refs": ["proof:current"],
        "audit_refs": ["audit:independent-pass"],
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


@pytest.mark.parametrize("name", sorted(EXPECTED_JSON))
def test_json_artifacts_parse(name: str):
    assert load_json(ARTIFACT_DIR / name)


@pytest.mark.parametrize("name", sorted(EXPECTED_YAML))
def test_yaml_artifacts_parse(name: str):
    assert load_yaml(ARTIFACT_DIR / name)


def test_artifact_filenames_and_locations_are_sane():
    assert ARTIFACT_DIR.is_dir()
    assert EXAMPLES_DIR.is_dir()
    actual_root_files = {path.name for path in ARTIFACT_DIR.iterdir() if path.is_file()}
    actual_examples = {path.name for path in EXAMPLES_DIR.iterdir() if path.is_file()}

    assert EXPECTED_JSON <= actual_root_files
    assert EXPECTED_YAML <= actual_root_files
    assert EXPECTED_MARKDOWN <= actual_root_files
    assert EXPECTED_EXAMPLES == actual_examples


@pytest.mark.parametrize("name", sorted(path for path in EXPECTED_JSON if path.endswith(".schema.json")))
def test_json_schema_artifacts_are_valid_schemas(name: str):
    Draft7Validator.check_schema(load_json(ARTIFACT_DIR / name))


@pytest.mark.parametrize("name", sorted(EXPECTED_EXAMPLES))
def test_example_route_decisions_validate(name: str):
    validator = schema_validator("route_decision.schema.json")
    assert_valid(validator, load_json(EXAMPLES_DIR / name))


def test_unknown_privacy_and_risk_fail_closed():
    unknown = load_json(EXAMPLES_DIR / "UNKNOWN.json")
    assert unknown["privacy_class"] == "UNKNOWN"
    assert unknown["risk_class"] == "UNKNOWN"
    assert unknown["decision_status"] in {"BLOCKED", "ESCALATED", "NEEDS_SUPERVISOR"}
    assert "UNKNOWN_PRIVACY_CLASS" in unknown["blocked_reasons"]
    assert "UNKNOWN_RISK_CLASS" in unknown["blocked_reasons"]

    validator = schema_validator("route_decision.schema.json")
    fail_open = copy.deepcopy(unknown)
    fail_open["decision_status"] = "SELECTED"
    assert_invalid(validator, fail_open)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("privacy_class", "PRIVATE_REPO_NO_SECRETS"),
        ("privacy_class", "PRIVATE_REPO_POSSIBLE_SECRETS"),
        ("privacy_class", "SECRET_BEARING"),
        ("privacy_class", "CLIENT_DATA"),
        ("privacy_class", "SECURITY_SENSITIVE"),
        ("privacy_class", "RELEASE_AUTHORITY"),
        ("risk_class", "R5_SECURITY_OR_AUTHORITY"),
        ("risk_class", "R6_RELEASE_OR_PRODUCTION"),
        ("structured_output_mode", "json_schema_strict"),
        ("structured_output_mode", "tool_schema_strict"),
    ],
)
def test_openrouter_free_forbidden_for_private_high_risk_and_schema_authority(field: str, value: str):
    validator = schema_validator("route_decision.schema.json")
    decision = load_json(EXAMPLES_DIR / "R0_READ.json")
    decision[field] = value
    assert decision["access_path"] == "openrouter_free"
    assert_invalid(validator, decision)


def test_forbidden_routes_encode_openrouter_free_block():
    forbidden = load_yaml(ARTIFACT_DIR / "forbidden_routes.yaml")
    block = next(item for item in forbidden["hard_blocks"] if item["id"] == "FR-002")
    assert block["block_reason"] == "OPENROUTER_FREE_FORBIDDEN"
    assert "PRIVATE_REPO_NO_SECRETS" in block["match"]["any_privacy_class"]
    assert "SECURITY_SENSITIVE" in block["match"]["any_privacy_class"]
    assert "RELEASE_AUTHORITY" in block["match"]["any_privacy_class"]
    assert "R5_SECURITY_OR_AUTHORITY" in block["match"]["any_risk_class"]
    assert "R6_RELEASE_OR_PRODUCTION" in block["match"]["any_risk_class"]
    assert "structured_task_packet_generation" in block["match"]["any_role"]
    assert "proof_validation" in block["match"]["any_role"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("proof_stale", True),
        ("checks_stale_to_head", True),
        ("blocking_thread_unresolved", True),
        ("diff_escapes_packet_allowlist", True),
        ("security_release_gate_lacks_approval", True),
    ],
)
def test_release_ready_rejects_boolean_blockers(field: str, value: bool):
    validator = schema_validator("pr_steward_merge_readiness.schema.json")
    readiness = valid_merge_readiness()
    readiness[field] = value
    assert_invalid(validator, readiness)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("failed_checks", ["contract-tests"]),
        ("unresolved_blockers", ["MISSING_AUDIT"]),
        ("unknown_reviewers_or_bots", ["unknown-bot"]),
        ("unclassified_review_items", ["review-comment-1"]),
    ],
)
def test_release_ready_rejects_non_empty_blocker_lists(field: str, value: list[str]):
    validator = schema_validator("pr_steward_merge_readiness.schema.json")
    readiness = valid_merge_readiness()
    readiness[field] = value
    assert_invalid(validator, readiness)


@pytest.mark.parametrize("field", ["proof_bundle_refs", "audit_refs"])
def test_release_ready_rejects_missing_required_evidence_refs(field: str):
    validator = schema_validator("pr_steward_merge_readiness.schema.json")
    readiness = valid_merge_readiness()
    readiness[field] = []
    assert_invalid(validator, readiness)


def test_no_runtime_routing_files_are_added():
    runtime_candidates = [
        ROOT / "src" / "dopemux" / "dcp" / "openclaw_routing.py",
        ROOT / "src" / "dopemux" / "dcp" / "openclaw_router.py",
        ROOT / "src" / "dopemux" / "dcp" / "route_engine.py",
    ]
    assert not any(path.exists() for path in runtime_candidates)
