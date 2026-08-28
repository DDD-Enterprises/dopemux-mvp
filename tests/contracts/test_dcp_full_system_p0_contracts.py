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
        layer["value"] = "gpt-5.5"
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
