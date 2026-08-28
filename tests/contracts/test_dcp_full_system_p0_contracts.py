from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator, FormatChecker

from scripts.governance.validate_dcp_p0_contract_semantics import (
    validate_p0_contract_semantics,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "dcp" / "full_system" / "p0"
PACKET_ID = "TP-DMX-DCP-FULL-SYSTEM-P0-AUTHORITY-CONTRACT-FREEZE-001"
PACKET_SHA256 = "27f4fb613942e84ea71bcb7c3d7ad2ad66388645d51546d5ce83664281eb4f8a"
RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _positive_cases() -> list[dict[str, Any]]:
    return _load_json(FIXTURE_ROOT / "positive_contracts.json")


def _case_map() -> dict[str, dict[str, Any]]:
    return {case["name"]: case for case in _positive_cases()}


def _audit_chain_instances() -> dict[str, dict[str, Any]]:
    cases = _case_map()
    names = (
        "capability_requirement_ref",
        "auditor_capability_snapshot",
        "auditor_certification",
        "audit_request",
        "audit_execution_receipt",
        "audit_result",
    )
    return {name: copy.deepcopy(cases[name]["instance"]) for name in names}


def _audit_chain_errors(chain: dict[str, dict[str, Any]]) -> list[str]:
    return _semantic_errors(
        _case_map()["audit_result"],
        chain["audit_result"],
        list(chain.values()),
    )


def _format_checker() -> FormatChecker:
    checker = FormatChecker()

    @checker.checks("date-time", raises=(TypeError, ValueError))
    def is_rfc3339(value: object) -> bool:
        if not isinstance(value, str) or RFC3339.fullmatch(value) is None:
            return False
        parsed = datetime.fromisoformat(
            value.removesuffix("Z") + ("+00:00" if value.endswith("Z") else "")
        )
        return parsed.tzinfo is not None

    return checker


def _validator(case: dict[str, Any]) -> Draft7Validator:
    schema = _load_json(REPO_ROOT / case["schema"])
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema, format_checker=_format_checker())


def _semantic_errors(
    case: dict[str, Any], instance: dict[str, Any], related_objects: list[dict[str, Any]] | None = None
) -> list[str]:
    if related_objects is None:
        related_objects = [case["instance"] for case in _positive_cases()]
    return validate_p0_contract_semantics(case["schema"], instance, related_objects=related_objects)


def _contract_is_valid(
    case: dict[str, Any], instance: dict[str, Any], related_objects: list[dict[str, Any]] | None = None
) -> bool:
    return _validator(case).is_valid(instance) and not _semantic_errors(case, instance, related_objects)


def _set_path(instance: dict[str, Any], path: str, value: Any) -> None:
    parts = path.split(".")
    cursor: Any = instance
    for part in parts[:-1]:
        cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
    leaf = parts[-1]
    if isinstance(cursor, list):
        cursor[int(leaf)] = value
    else:
        cursor[leaf] = value


def _remove_path(instance: dict[str, Any], path: str) -> None:
    parts = path.split(".")
    cursor: Any = instance
    for part in parts[:-1]:
        cursor = cursor[int(part)] if isinstance(cursor, list) else cursor[part]
    leaf = parts[-1]
    if isinstance(cursor, list):
        del cursor[int(leaf)]
    else:
        del cursor[leaf]


def _mutated_instance(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    case = _case_map()[spec["base"]]
    instance = copy.deepcopy(case["instance"])
    for mutation in spec.get("mutations", []):
        if mutation.get("operation", "set") == "remove":
            _remove_path(instance, mutation["path"])
        else:
            _set_path(instance, mutation["path"], mutation["value"])
    return case, instance


@pytest.mark.parametrize("case", _positive_cases(), ids=lambda case: case["name"])
def test_positive_contracts_validate(case: dict[str, Any]) -> None:
    errors = list(_validator(case).iter_errors(case["instance"]))
    assert errors == [], [error.message for error in errors]
    assert _semantic_errors(case, case["instance"]) == []


@pytest.mark.parametrize("case", _positive_cases(), ids=lambda case: case["name"])
def test_unknown_root_properties_fail_closed(case: dict[str, Any]) -> None:
    instance = copy.deepcopy(case["instance"])
    instance["unexpected_authority"] = True
    assert not _validator(case).is_valid(instance)


@pytest.mark.parametrize(
    "spec",
    _load_json(FIXTURE_ROOT / "adversarial_contracts.json"),
    ids=lambda spec: spec["name"],
)
def test_adversarial_contracts_fail_closed(spec: dict[str, Any]) -> None:
    case, instance = _mutated_instance(spec)
    assert not _contract_is_valid(case, instance), spec["name"]


def test_exactly_one_runtime_context_envelope_contract_is_accepted() -> None:
    specs = _load_json(FIXTURE_ROOT / "runtime_context_envelopes.json")
    accepted = 0
    for spec in specs:
        case, instance = _mutated_instance(spec)
        accepted += int(_contract_is_valid(case, instance))
    assert accepted == 1


def test_audit_result_outcome_classes_do_not_overlap() -> None:
    case = _case_map()["audit_result"]
    validator = _validator(case)
    base = case["instance"]

    valid_outcomes = [
        {"class": "JUDGMENT", "status": "PASS", "substantive_judgment_rendered": True},
        {
            "class": "TERMINAL_INTAKE_FAILURE",
            "status": "HEAD_MISMATCH",
            "substantive_judgment_rendered": False,
        },
        {
            "class": "PREJUDGMENT_EXECUTION_FAILURE",
            "status": "TRANSPORT_FAILURE",
            "substantive_judgment_rendered": False,
            "retry_disposition": "POLICY_REQUIRED",
        },
    ]
    for outcome in valid_outcomes:
        instance = copy.deepcopy(base)
        instance["outcome"] = outcome
        assert validator.is_valid(instance), outcome

    mismatched = copy.deepcopy(base)
    mismatched["outcome"] = {
        "class": "JUDGMENT",
        "status": "TRANSPORT_FAILURE",
        "substantive_judgment_rendered": False,
    }
    assert not validator.is_valid(mismatched)


def test_required_identity_unknown_is_terminal_not_judgment() -> None:
    case = _case_map()["audit_result_required_identity_unknown"]
    validator = _validator(case)
    terminal = copy.deepcopy(case["instance"])
    assert validator.is_valid(terminal)

    terminal["outcome"] = {
        "class": "JUDGMENT",
        "status": "PASS",
        "substantive_judgment_rendered": True,
    }
    assert not validator.is_valid(terminal)


def test_ready_packet_rejects_self_consistent_evidence_from_wrong_plan() -> None:
    packet_case = _case_map()["run_context_packet"]
    wrong_plan = copy.deepcopy(_case_map()["context_plan"]["instance"])
    wrong_plan["plan_id"] = "CTX-PLAN-OTHER"
    wrong_plan["mandatory_evidence_refs"] = ["repo://OTHER.md"]

    assert not _contract_is_valid(packet_case, packet_case["instance"], [wrong_plan])


def test_satisfied_result_rejects_uniform_identity_substitution_from_request() -> None:
    result_case = _case_map()["audit_result"]
    result = copy.deepcopy(result_case["instance"])
    for layer in result["identities"].values():
        layer["model"] = "gpt-5.5"
    request = copy.deepcopy(_case_map()["audit_request"]["instance"])
    request["requested_identity"] = {"provider": "anthropic", "model": "claude-sonnet-4-6"}

    assert not _contract_is_valid(result_case, result, [request])


def test_satisfied_result_rejects_uniform_provider_substitution_from_request() -> None:
    result_case = _case_map()["audit_result"]
    result = copy.deepcopy(result_case["instance"])
    for layer in result["identities"].values():
        layer["provider"] = "openai"
    request = copy.deepcopy(_case_map()["audit_request"]["instance"])
    assert not _contract_is_valid(result_case, result, [request])


def test_cross_object_resolution_rejects_duplicate_project_and_subject_mismatch() -> None:
    packet_case = _case_map()["run_context_packet"]
    plan = copy.deepcopy(_case_map()["context_plan"]["instance"])
    duplicate = copy.deepcopy(packet_case["instance"])
    duplicate["mandatory_evidence"]["bindings"].append(copy.deepcopy(duplicate["mandatory_evidence"]["bindings"][0]))
    assert not _contract_is_valid(packet_case, duplicate, [plan])
    plan["project_id"] = "other-project"
    assert not _contract_is_valid(packet_case, packet_case["instance"], [plan])
    result_case = _case_map()["audit_result"]
    request = copy.deepcopy(_case_map()["audit_request"]["instance"])
    request["subject"]["head_sha"] = "a" * 40
    assert not _contract_is_valid(result_case, result_case["instance"], [request])


def test_satisfied_result_requires_certification_snapshot_chain() -> None:
    result_case = _case_map()["audit_result"]
    request_case = _case_map()["audit_request"]
    request = copy.deepcopy(request_case["instance"])
    request["certification_ref"] = "AUD-CERT-MISSING"

    assert _validator(request_case).is_valid(request)
    assert _validator(result_case).is_valid(result_case["instance"])
    assert (
        "SATISFIED certification_ref must resolve to exactly one AuditorCertification"
        in _semantic_errors(result_case, result_case["instance"], [request])
    )


def test_satisfied_result_rejects_same_model_execution_provider_substitution() -> None:
    receipt_case = _case_map()["audit_execution_receipt"]
    receipt = copy.deepcopy(receipt_case["instance"])
    for layer in receipt["identities"].values():
        layer["provider"] = "openrouter"

    schema_errors = list(_validator(receipt_case).iter_errors(receipt))
    assert schema_errors == [], [error.message for error in schema_errors]
    assert (
        "COMPLETED execution identity requested must exactly match resolved AuditRequest"
        in _semantic_errors(
            receipt_case,
            receipt,
            [
                _case_map()["audit_request"]["instance"],
                _case_map()["audit_result"]["instance"],
            ],
        )
    )


def test_ready_packet_rejects_derived_mandatory_source_evidence() -> None:
    packet_case = _case_map()["run_context_packet"]
    packet = copy.deepcopy(packet_case["instance"])
    packet["context_items"][0]["kind"] = "DERIVED_EVIDENCE"

    assert _validator(packet_case).is_valid(packet)
    assert (
        "READY mandatory evidence 'repo://AGENTS.md' cannot resolve to DERIVED_EVIDENCE"
        in _semantic_errors(
            packet_case,
            packet,
            [_case_map()["context_plan"]["instance"]],
        )
    )


@pytest.mark.parametrize("provider_policy_state", ["UNKNOWN", "INELIGIBLE"])
def test_eligible_compiled_claim_requires_eligible_input_policy(
    provider_policy_state: str,
) -> None:
    claim_case = _case_map()["compiled_claim"]
    compiler_input = copy.deepcopy(_case_map()["knowledge_compiler_input"]["instance"])
    compiler_input["policy"]["provider_policy_state"] = provider_policy_state

    assert _validator(claim_case).is_valid(claim_case["instance"])
    assert (
        "eligible CompiledClaim input_ref must resolve to exactly one ELIGIBLE KnowledgeCompilerInput"
        in _semantic_errors(claim_case, claim_case["instance"], [compiler_input])
    )


@pytest.mark.parametrize(
    ("target", "path", "value", "expected_error"),
    [
        (
            "auditor_certification",
            "request_ref",
            "AUD-REQ-OTHER",
            "SATISFIED AuditorCertification request_ref must match AuditRequest",
        ),
        (
            "auditor_certification",
            "capability_requirement_refs",
            ["CAP-OTHER"],
            "SATISFIED AuditorCertification capability_requirement_refs must match AuditRequest",
        ),
        (
            "auditor_certification",
            "subject.head_sha",
            "a" * 40,
            "SATISFIED certification/request subject head_sha must match",
        ),
        (
            "auditor_certification",
            "snapshot_ref",
            "AUD-CAP-MISSING",
            "SATISFIED snapshot_ref must resolve to exactly one AuditorCapabilitySnapshot",
        ),
        (
            "auditor_certification",
            "snapshot_freshness",
            "STALE",
            "SATISFIED AuditorCertification snapshot_freshness is invalid",
        ),
        (
            "auditor_certification",
            "judgment_authorized",
            False,
            "SATISFIED AuditorCertification judgment_authorized is invalid",
        ),
        (
            "auditor_capability_snapshot",
            "subject.digest",
            "sha256:" + "a" * 64,
            "SATISFIED snapshot/request subject digest must match",
        ),
        (
            "auditor_capability_snapshot",
            "freshness",
            "UNKNOWN",
            "SATISFIED AuditorCapabilitySnapshot freshness must be CURRENT",
        ),
        (
            "auditor_capability_snapshot",
            "route",
            {"state": "UNKNOWN", "runner": None, "tool": None, "evidence_refs": []},
            "SATISFIED snapshot route must be OBSERVED and match AuditRequest",
        ),
        (
            "auditor_capability_snapshot",
            "capability_states.0.capability",
            "other_capability",
            "SATISFIED capability 'independent_audit' must resolve to exactly one snapshot state",
        ),
        (
            "auditor_capability_snapshot",
            "capability_states.0.state",
            "UNKNOWN",
            "SATISFIED capability 'independent_audit' must be AVAILABLE with required evidence",
        ),
        (
            "auditor_capability_snapshot",
            "identities.requested.provider",
            "openrouter",
            "SATISFIED snapshot identity requested must be OBSERVED and match AuditRequest",
        ),
        (
            "auditor_capability_snapshot",
            "identities.configured.model",
            "same-name-other-model",
            "SATISFIED snapshot identity configured must be OBSERVED and match AuditRequest",
        ),
        (
            "auditor_capability_snapshot",
            "identities.provider_attested",
            {"state": "UNKNOWN", "provider": None, "model": None, "evidence_refs": []},
            "SATISFIED snapshot identity provider_attested must be OBSERVED and match AuditRequest",
        ),
        (
            "auditor_capability_snapshot",
            "independence",
            {"state": "UNKNOWN", "evidence_refs": []},
            "SATISFIED snapshot independence must be VERIFIED",
        ),
        (
            "capability_requirement_ref",
            "requested_identity.provider",
            "openrouter",
            "SATISFIED capability_requirement_ref 'CAP-AUDIT-001' identity must match AuditRequest",
        ),
        (
            "audit_request",
            "required_capabilities",
            ["other_capability"],
            "SATISFIED AuditRequest required_capabilities must equal resolved capability requirements",
        ),
    ],
)
def test_satisfied_result_rejects_invalid_certification_chain(
    target: str, path: str, value: Any, expected_error: str
) -> None:
    chain = _audit_chain_instances()
    _set_path(chain[target], path, value)
    assert expected_error in _audit_chain_errors(chain)


@pytest.mark.parametrize(
    ("duplicated_object", "expected_error"),
    [
        ("audit_request", "SATISFIED request_ref must resolve to exactly one AuditRequest"),
        (
            "capability_requirement_ref",
            "SATISFIED capability_requirement_ref 'CAP-AUDIT-001' must resolve to exactly one CapabilityRequirementRef",
        ),
        (
            "auditor_certification",
            "SATISFIED certification_ref must resolve to exactly one AuditorCertification",
        ),
        (
            "auditor_capability_snapshot",
            "SATISFIED snapshot_ref must resolve to exactly one AuditorCapabilitySnapshot",
        ),
        (
            "audit_execution_receipt",
            "SATISFIED result_ref must resolve from exactly one AuditExecutionReceipt",
        ),
    ],
)
def test_satisfied_result_rejects_ambiguous_chain_objects(
    duplicated_object: str, expected_error: str
) -> None:
    chain = _audit_chain_instances()
    related_objects = list(chain.values()) + [copy.deepcopy(chain[duplicated_object])]
    assert expected_error in _semantic_errors(
        _case_map()["audit_result"],
        chain["audit_result"],
        related_objects,
    )


def test_satisfied_result_resolves_every_compatible_capability_requirement() -> None:
    chain = _audit_chain_instances()
    second_requirement = copy.deepcopy(chain["capability_requirement_ref"])
    second_requirement["requirement_id"] = "CAP-POLICY-001"
    second_requirement["capability"] = "policy_audit"
    chain["audit_request"]["capability_requirement_refs"].append("CAP-POLICY-001")
    chain["audit_request"]["required_capabilities"].append("policy_audit")
    chain["auditor_certification"]["capability_requirement_refs"].append(
        "CAP-POLICY-001"
    )
    chain["auditor_capability_snapshot"]["capability_states"].append(
        {
            "capability": "policy_audit",
            "state": "AVAILABLE",
            "evidence_refs": ["proof://policy-capability"],
        }
    )
    related_objects = list(chain.values()) + [second_requirement]
    assert _semantic_errors(
        _case_map()["audit_result"], chain["audit_result"], related_objects
    ) == []

    second_requirement["requested_identity"]["provider"] = "openrouter"
    assert (
        "SATISFIED capability_requirement_ref 'CAP-POLICY-001' identity must match AuditRequest"
        in _semantic_errors(
            _case_map()["audit_result"], chain["audit_result"], related_objects
        )
    )


@pytest.mark.parametrize(
    ("path", "value", "expected_error"),
    [
        (
            "route.runner",
            "other-runner",
            "COMPLETED execution route must exactly match AuditRequest",
        ),
        (
            "subject_digest",
            "sha256:" + "a" * 64,
            "COMPLETED execution subject_digest must match AuditRequest",
        ),
        (
            "identities.configured",
            {"state": "UNKNOWN", "provider": None, "model": None, "evidence_refs": []},
            "COMPLETED execution identity configured must exactly match resolved AuditRequest",
        ),
        (
            "execution_state",
            "PREJUDGMENT_FAILED",
            "SATISFIED AuditExecutionReceipt execution_state must be COMPLETED",
        ),
    ],
)
def test_satisfied_result_rejects_execution_receipt_mismatch(
    path: str, value: Any, expected_error: str
) -> None:
    chain = _audit_chain_instances()
    _set_path(chain["audit_execution_receipt"], path, value)
    assert expected_error in _audit_chain_errors(chain)


@pytest.mark.parametrize(
    ("request_refs", "receipt_refs"),
    [
        (["bundle://review"], ["bundle://review"]),
        (
            ["bundle://review", "bundle://appendix"],
            ["bundle://appendix", "bundle://review"],
        ),
        (
            ["bundle://review", "bundle://appendix"],
            ["bundle://appendix", "bundle://extra", "bundle://review"],
        ),
    ],
)
def test_completed_receipt_accepts_order_insensitive_required_evidence_superset(
    request_refs: list[str], receipt_refs: list[str]
) -> None:
    chain = _audit_chain_instances()
    chain["audit_request"]["mandatory_evidence_refs"] = request_refs
    chain["audit_execution_receipt"]["mandatory_evidence"]["refs"] = receipt_refs

    assert _audit_chain_errors(chain) == []


@pytest.mark.parametrize(
    ("request_refs", "receipt_refs"),
    [
        (["bundle://review"], ["bundle://other"]),
        (["bundle://review", "bundle://appendix"], ["bundle://review"]),
        (
            ["bundle://review", "bundle://appendix"],
            ["bundle://other", "bundle://extra"],
        ),
        (["request://current/review"], ["request://other/review"]),
    ],
)
def test_completed_receipt_rejects_missing_required_evidence_refs(
    request_refs: list[str], receipt_refs: list[str]
) -> None:
    chain = _audit_chain_instances()
    chain["audit_request"]["mandatory_evidence_refs"] = request_refs
    chain["audit_execution_receipt"]["mandatory_evidence"]["refs"] = receipt_refs

    assert (
        "COMPLETED execution mandatory_evidence.refs must include every AuditRequest mandatory_evidence_ref"
        in _audit_chain_errors(chain)
    )


def test_audit_request_rejects_duplicate_mandatory_evidence_refs() -> None:
    request_case = _case_map()["audit_request"]
    request = copy.deepcopy(request_case["instance"])
    request["mandatory_evidence_refs"].append(request["mandatory_evidence_refs"][0])
    chain = _audit_chain_instances()
    chain["audit_request"] = request

    assert not _validator(request_case).is_valid(request)
    assert (
        "COMPLETED execution mandatory_evidence refs must be unique exact strings"
        in _audit_chain_errors(chain)
    )


def test_audit_execution_receipt_rejects_duplicate_mandatory_evidence_refs() -> None:
    receipt_case = _case_map()["audit_execution_receipt"]
    receipt = copy.deepcopy(receipt_case["instance"])
    receipt["mandatory_evidence"]["refs"].append(receipt["mandatory_evidence"]["refs"][0])
    chain = _audit_chain_instances()
    chain["audit_execution_receipt"] = receipt

    assert not _validator(receipt_case).is_valid(receipt)
    assert (
        "COMPLETED execution mandatory_evidence refs must be unique exact strings"
        in _audit_chain_errors(chain)
    )


def test_satisfied_result_model_field_mismatch_fails_closed() -> None:
    chain = _audit_chain_instances()
    chain["audit_result"]["identities"]["configured"]["model"] = "same-name-other-model"

    assert (
        "SATISFIED identity configured must exactly match resolved AuditRequest"
        in _audit_chain_errors(chain)
    )


def test_ready_packet_allows_supplemental_derived_evidence_with_canonical_binding() -> None:
    packet_case = _case_map()["run_context_packet"]
    packet = packet_case["instance"]
    assert any(
        item["kind"] == "DERIVED_EVIDENCE" and item["mandatory"] is False
        for item in packet["context_items"]
    )
    assert _contract_is_valid(
        packet_case,
        packet,
        [_case_map()["context_plan"]["instance"]],
    )


def test_eligible_compiled_claim_requires_input_ref_structurally() -> None:
    claim_case = _case_map()["compiled_claim"]
    claim = copy.deepcopy(claim_case["instance"])
    del claim["input_ref"]
    assert not _validator(claim_case).is_valid(claim)


@pytest.mark.parametrize("resolution", ["missing", "wrong", "ambiguous"])
def test_eligible_compiled_claim_rejects_invalid_input_resolution(resolution: str) -> None:
    claim_case = _case_map()["compiled_claim"]
    claim = copy.deepcopy(claim_case["instance"])
    compiler_input = copy.deepcopy(_case_map()["knowledge_compiler_input"]["instance"])
    related_inputs: list[dict[str, Any]] = [compiler_input]
    if resolution == "missing":
        related_inputs = []
    elif resolution == "wrong":
        compiler_input["input_id"] = "KC-IN-OTHER"
    else:
        related_inputs.append(copy.deepcopy(compiler_input))

    assert (
        "eligible CompiledClaim input_ref must resolve to exactly one ELIGIBLE KnowledgeCompilerInput"
        in _semantic_errors(claim_case, claim, related_inputs)
    )


def test_p0_packet_bytes_match_immutable_issuance() -> None:
    packet = REPO_ROOT / "task-packets" / f"{PACKET_ID}.json"
    assert hashlib.sha256(packet.read_bytes()).hexdigest() == PACKET_SHA256


def test_dcp_manifest_registers_only_three_p0_contracts_once_with_schema_versions() -> None:
    manifest = _load_json(REPO_ROOT / "schemas" / "dcp" / "manifest.json")
    p0_files = {
        "schemas/dcp/context_plan.schema.json",
        "schemas/dcp/run_context_packet.schema.json",
        "schemas/dcp/capability_requirement_ref.schema.json",
    }
    registered = [
        entry["schema_file"]
        for entry in manifest["contracts"]
        if entry["schema_file"] in p0_files
    ]
    assert sorted(registered) == sorted(p0_files)
    assert len(registered) == len(set(registered))
    for entry in manifest["contracts"]:
        if entry["schema_file"] in p0_files:
            schema = _load_json(REPO_ROOT / entry["schema_file"])
            assert schema["properties"]["schema_version"]["const"] == entry["schema_version"]
