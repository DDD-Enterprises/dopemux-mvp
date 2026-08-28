#!/usr/bin/env python3
"""Validate P0 contract relationships JSON Schema Draft 7 cannot express."""

from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Any


RUN_CONTEXT_SCHEMA = "schemas/dcp/run_context_packet.schema.json"
AUDIT_RESULT_SCHEMA = "schemas/audit_broker/audit_result.schema.json"
AUDIT_EXECUTION_RECEIPT_SCHEMA = "schemas/audit_broker/audit_execution_receipt.schema.json"
COMPILED_CLAIM_SCHEMA = "schemas/second_brain/compiled_claim.schema.json"
IDENTITY_LAYERS = (
    "requested",
    "configured",
    "response_claimed",
    "proxy_reported",
    "provider_attested",
)
SUBJECT_FIELDS = ("packet_id", "head_sha", "tree_sha", "digest")


def _normalized_schema_path(schema_path: str) -> str:
    return PurePosixPath(schema_path.replace("\\", "/")).as_posix()


def _run_context_errors(instance: dict[str, Any], related_objects: list[dict[str, Any]] | None) -> list[str]:
    if instance.get("readiness") != "READY":
        return []

    context_items = instance.get("context_items")
    mandatory_evidence = instance.get("mandatory_evidence")
    if not isinstance(context_items, list) or not isinstance(mandatory_evidence, dict):
        return []
    bindings = mandatory_evidence.get("bindings")
    if not isinstance(bindings, list):
        return []

    items_by_ref: dict[str, list[dict[str, Any]]] = {}
    mandatory_refs: list[str] = []
    for item in context_items:
        if not isinstance(item, dict) or not isinstance(item.get("ref"), str):
            continue
        ref = item["ref"]
        items_by_ref.setdefault(ref, []).append(item)
        if item.get("mandatory") is True:
            mandatory_refs.append(ref)

    errors: list[str] = []
    plans = [
        candidate
        for candidate in related_objects or []
        if candidate.get("schema_version") == "dcp-context-plan.v0"
        and candidate.get("plan_id") == instance.get("plan_ref")
    ]
    if len(plans) != 1:
        return ["READY plan_ref must resolve to exactly one ContextPlan"]
    if plans[0].get("project_id") != instance.get("subject", {}).get("project_id"):
        return ["READY resolved ContextPlan project_id must match packet subject"]
    plan_mandatory_refs = plans[0].get("mandatory_evidence_refs")
    if not isinstance(plan_mandatory_refs, list):
        return ["READY resolved ContextPlan mandatory_evidence_refs is invalid"]
    bound_context_refs: set[str] = set()
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            continue
        required_ref = binding.get("required_ref")
        context_item_ref = binding.get("context_item_ref")
        if not isinstance(required_ref, str) or not isinstance(context_item_ref, str):
            continue
        if required_ref in bound_context_refs:
            errors.append(f"mandatory_evidence.bindings[{index}].required_ref must be unique")
        if required_ref != context_item_ref:
            errors.append(
                f"mandatory_evidence.bindings[{index}] required_ref must equal context_item_ref"
            )
        if required_ref not in plan_mandatory_refs:
            errors.append(
                f"mandatory_evidence.bindings[{index}].required_ref must belong to resolved ContextPlan"
            )
        matches = items_by_ref.get(context_item_ref, [])
        if len(matches) != 1:
            errors.append(
                f"mandatory_evidence.bindings[{index}].context_item_ref must resolve to exactly one context item"
            )
        elif matches[0].get("mandatory") is not True:
            errors.append(
                f"mandatory_evidence.bindings[{index}].context_item_ref must resolve to a mandatory context item"
            )
        elif matches[0].get("kind") == "DERIVED_EVIDENCE":
            errors.append(
                f"READY mandatory evidence {required_ref!r} cannot resolve to DERIVED_EVIDENCE"
            )
        if required_ref not in items_by_ref:
            errors.append(
                f"mandatory_evidence.bindings[{index}].required_ref must resolve to a context item"
            )
        bound_context_refs.add(context_item_ref)

    for ref in plan_mandatory_refs:
        if ref not in bound_context_refs:
            errors.append(f"resolved ContextPlan mandatory evidence {ref!r} has no evidence binding")

    for ref in mandatory_refs:
        if ref not in bound_context_refs:
            errors.append(f"mandatory context item {ref!r} has no evidence binding")
    return errors


def _related_matches(
    related_objects: list[dict[str, Any]] | None,
    *,
    schema_version: str,
    id_field: str,
    expected_id: Any,
) -> list[dict[str, Any]]:
    return [
        candidate
        for candidate in related_objects or []
        if candidate.get("schema_version") == schema_version
        and candidate.get(id_field) == expected_id
    ]


def _identity_provider_model(observation: Any) -> tuple[Any, Any]:
    if not isinstance(observation, dict):
        return None, None
    return observation.get("provider"), observation.get("model", observation.get("value"))


def _subject_errors(prefix: str, observed: Any, expected: Any) -> list[str]:
    if not isinstance(observed, dict) or not isinstance(expected, dict):
        return [f"{prefix} subject must be present"]
    return [
        f"{prefix} subject {field} must match"
        for field in SUBJECT_FIELDS
        if observed.get(field) != expected.get(field)
    ]


def _resolve_capability_requirements(
    request: dict[str, Any], related_objects: list[dict[str, Any]] | None
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    refs = request.get("capability_requirement_refs")
    if not isinstance(refs, list) or not refs:
        return ["SATISFIED AuditRequest capability_requirement_refs is invalid"], [], []

    errors: list[str] = []
    requirements: list[dict[str, Any]] = []
    required_layers: list[str] = []
    request_identity = request.get("requested_identity")
    for ref in refs:
        matches = _related_matches(
            related_objects,
            schema_version="dcp-capability-requirement-ref.v0",
            id_field="requirement_id",
            expected_id=ref,
        )
        if len(matches) != 1:
            errors.append(
                f"SATISFIED capability_requirement_ref {ref!r} must resolve to exactly one CapabilityRequirementRef"
            )
            continue
        capability_requirement = matches[0]
        requirements.append(capability_requirement)
        if capability_requirement.get("requested_identity") != request_identity:
            errors.append(
                f"SATISFIED capability_requirement_ref {ref!r} identity must match AuditRequest"
            )
        if capability_requirement.get("substitution_allowed") is not False:
            errors.append(
                f"SATISFIED capability_requirement_ref {ref!r} must forbid substitution"
            )
        evidence_policy = capability_requirement.get("evidence_policy")
        layers = evidence_policy.get("required_identity_layers") if isinstance(evidence_policy, dict) else None
        if not isinstance(layers, list) or not layers:
            errors.append(
                f"SATISFIED capability_requirement_ref {ref!r} identity policy is invalid"
            )
            continue
        for layer in layers:
            if isinstance(layer, str) and layer not in required_layers:
                required_layers.append(layer)

    resolved_capabilities = [requirement.get("capability") for requirement in requirements]
    if request.get("required_capabilities") != resolved_capabilities:
        errors.append(
            "SATISFIED AuditRequest required_capabilities must equal resolved capability requirements"
        )
    return errors, requirements, required_layers


def _audit_execution_receipt_errors(
    instance: dict[str, Any], related_objects: list[dict[str, Any]] | None
) -> list[str]:
    if instance.get("execution_state") != "COMPLETED":
        return []

    requests = _related_matches(
        related_objects,
        schema_version="audit-broker-audit-request.v0",
        id_field="request_id",
        expected_id=instance.get("request_ref"),
    )
    if len(requests) != 1:
        return ["COMPLETED request_ref must resolve to exactly one AuditRequest"]
    results = _related_matches(
        related_objects,
        schema_version="audit-broker-audit-result.v0",
        id_field="result_id",
        expected_id=instance.get("result_ref"),
    )
    if len(results) != 1:
        return ["COMPLETED result_ref must resolve to exactly one AuditResult"]

    request = requests[0]
    result = results[0]
    errors: list[str] = []
    if result.get("request_ref") != request.get("request_id"):
        errors.append("COMPLETED AuditResult request_ref must match AuditRequest")
    request_subject = request.get("subject")
    if not isinstance(request_subject, dict) or instance.get("subject_digest") != request_subject.get(
        "digest"
    ):
        errors.append("COMPLETED execution subject_digest must match AuditRequest")
    if instance.get("route") != request.get("requested_route"):
        errors.append("COMPLETED execution route must exactly match AuditRequest")

    requirement = result.get("identity_requirement")
    required_layers = requirement.get("required_layers") if isinstance(requirement, dict) else None
    if not isinstance(required_layers, list):
        required_layers = []
    requested_identity = request.get("requested_identity")
    request_provider = (
        requested_identity.get("provider") if isinstance(requested_identity, dict) else None
    )
    request_model = requested_identity.get("model") if isinstance(requested_identity, dict) else None
    receipt_identities = instance.get("identities")
    result_identities = result.get("identities")
    for layer in required_layers:
        receipt_observation = (
            receipt_identities.get(layer) if isinstance(receipt_identities, dict) else None
        )
        receipt_provider, receipt_model = _identity_provider_model(receipt_observation)
        if (
            not isinstance(receipt_observation, dict)
            or receipt_observation.get("state") != "OBSERVED"
            or receipt_provider != request_provider
            or receipt_model != request_model
        ):
            errors.append(
                f"COMPLETED execution identity {layer} must exactly match resolved AuditRequest"
            )
        result_observation = (
            result_identities.get(layer) if isinstance(result_identities, dict) else None
        )
        result_provider, result_model = _identity_provider_model(result_observation)
        if result_provider != receipt_provider or result_model != receipt_model:
            errors.append(f"COMPLETED execution identity {layer} must match AuditResult")
    return errors


def _audit_result_errors(instance: dict[str, Any], related_objects: list[dict[str, Any]] | None) -> list[str]:
    requirement = instance.get("identity_requirement")
    identities = instance.get("identities")
    if not isinstance(requirement, dict) or not isinstance(identities, dict):
        return []
    if requirement.get("disposition") != "SATISFIED":
        return []

    requests = _related_matches(
        related_objects,
        schema_version="audit-broker-audit-request.v0",
        id_field="request_id",
        expected_id=instance.get("request_ref"),
    )
    if len(requests) != 1:
        return ["SATISFIED request_ref must resolve to exactly one AuditRequest"]
    requested_identity = requests[0].get("requested_identity")
    request_model = requested_identity.get("model") if isinstance(requested_identity, dict) else None
    request_provider = requested_identity.get("provider") if isinstance(requested_identity, dict) else None
    if not isinstance(request_model, str) or not isinstance(request_provider, str):
        return ["SATISFIED resolved AuditRequest requested_identity is invalid"]
    request = requests[0]
    result_subject = instance.get("subject")
    request_subject = request.get("subject")
    requested = identities.get("requested")
    expected = requested.get("value") if isinstance(requested, dict) else None
    if not isinstance(expected, str):
        return []

    errors = _subject_errors("SATISFIED request/result", result_subject, request_subject)
    if expected != request_model:
        errors.append("SATISFIED requested identity must exactly match resolved AuditRequest")
    for layer in IDENTITY_LAYERS:
        observation = identities.get(layer)
        observed = observation.get("value") if isinstance(observation, dict) else None
        provider = observation.get("provider") if isinstance(observation, dict) else None
        if observed != request_model or provider != request_provider:
            errors.append(f"SATISFIED identity {layer} must exactly match resolved AuditRequest")

    requirement_errors, requirements, required_layers = _resolve_capability_requirements(
        request, related_objects
    )
    errors.extend(requirement_errors)
    requirement_ref = requirement.get("requirement_ref")
    requirements_by_ref = {
        candidate.get("requirement_id"): candidate for candidate in requirements
    }
    resolved_identity_requirement = requirements_by_ref.get(requirement_ref)
    if resolved_identity_requirement is None:
        errors.append(
            "SATISFIED identity_requirement.requirement_ref must resolve within AuditRequest"
        )
    else:
        evidence_policy = resolved_identity_requirement.get("evidence_policy")
        expected_layers = (
            evidence_policy.get("required_identity_layers")
            if isinstance(evidence_policy, dict)
            else None
        )
        if requirement.get("required_layers") != expected_layers:
            errors.append(
                "SATISFIED identity_requirement.required_layers must match CapabilityRequirementRef"
            )

    certifications = _related_matches(
        related_objects,
        schema_version="audit-broker-auditor-certification.v0",
        id_field="certification_id",
        expected_id=request.get("certification_ref"),
    )
    if len(certifications) != 1:
        errors.append(
            "SATISFIED certification_ref must resolve to exactly one AuditorCertification"
        )
        return errors
    certification = certifications[0]
    if certification.get("request_ref") != request.get("request_id"):
        errors.append("SATISFIED AuditorCertification request_ref must match AuditRequest")
    errors.extend(
        _subject_errors("SATISFIED certification/request", certification.get("subject"), request_subject)
    )
    if certification.get("capability_requirement_refs") != request.get(
        "capability_requirement_refs"
    ):
        errors.append(
            "SATISFIED AuditorCertification capability_requirement_refs must match AuditRequest"
        )
    certification_contract = {
        "subject_scope": "AUDIT_ONLY",
        "snapshot_freshness": "CURRENT",
        "capability_state": "SATISFIED",
        "identity_alignment": "MATCHED",
        "independence": "VERIFIED",
        "judgment_authorized": True,
        "repository_mutation_authorized": False,
        "task_mutation_authorized": False,
    }
    for field, expected_value in certification_contract.items():
        if certification.get(field) != expected_value:
            errors.append(f"SATISFIED AuditorCertification {field} is invalid")

    snapshots = _related_matches(
        related_objects,
        schema_version="audit-broker-auditor-capability-snapshot.v0",
        id_field="snapshot_id",
        expected_id=certification.get("snapshot_ref"),
    )
    if len(snapshots) != 1:
        errors.append(
            "SATISFIED snapshot_ref must resolve to exactly one AuditorCapabilitySnapshot"
        )
        return errors
    snapshot = snapshots[0]
    errors.extend(
        _subject_errors("SATISFIED snapshot/request", snapshot.get("subject"), request_subject)
    )
    if snapshot.get("freshness") != "CURRENT":
        errors.append("SATISFIED AuditorCapabilitySnapshot freshness must be CURRENT")

    request_route = request.get("requested_route")
    snapshot_route = snapshot.get("route")
    if (
        not isinstance(snapshot_route, dict)
        or snapshot_route.get("state") != "OBSERVED"
        or snapshot_route.get("runner")
        != (request_route.get("runner") if isinstance(request_route, dict) else None)
        or snapshot_route.get("tool")
        != (request_route.get("tool") if isinstance(request_route, dict) else None)
    ):
        errors.append("SATISFIED snapshot route must be OBSERVED and match AuditRequest")

    capability_states = snapshot.get("capability_states")
    if not isinstance(capability_states, list):
        capability_states = []
    for capability_requirement in requirements:
        capability = capability_requirement.get("capability")
        matching_states = [
            state
            for state in capability_states
            if isinstance(state, dict) and state.get("capability") == capability
        ]
        evidence_policy = capability_requirement.get("evidence_policy")
        minimum_evidence_refs = (
            evidence_policy.get("minimum_evidence_refs")
            if isinstance(evidence_policy, dict)
            else None
        )
        if len(matching_states) != 1:
            errors.append(
                f"SATISFIED capability {capability!r} must resolve to exactly one snapshot state"
            )
            continue
        evidence_refs = matching_states[0].get("evidence_refs")
        if (
            matching_states[0].get("state") != "AVAILABLE"
            or not isinstance(evidence_refs, list)
            or not isinstance(minimum_evidence_refs, int)
            or len(evidence_refs) < minimum_evidence_refs
        ):
            errors.append(
                f"SATISFIED capability {capability!r} must be AVAILABLE with required evidence"
            )

    snapshot_identities = snapshot.get("identities")
    for layer in required_layers:
        observation = (
            snapshot_identities.get(layer) if isinstance(snapshot_identities, dict) else None
        )
        provider, model = _identity_provider_model(observation)
        if (
            not isinstance(observation, dict)
            or observation.get("state") != "OBSERVED"
            or provider != request_provider
            or model != request_model
        ):
            errors.append(
                f"SATISFIED snapshot identity {layer} must be OBSERVED and match AuditRequest"
            )
    independence = snapshot.get("independence")
    if (
        request.get("independence_required") is not True
        or not isinstance(independence, dict)
        or independence.get("state") != "VERIFIED"
        or not independence.get("evidence_refs")
    ):
        errors.append("SATISFIED snapshot independence must be VERIFIED")

    receipts = _related_matches(
        related_objects,
        schema_version="audit-broker-audit-execution-receipt.v0",
        id_field="result_ref",
        expected_id=instance.get("result_id"),
    )
    if len(receipts) != 1:
        errors.append(
            "SATISFIED result_ref must resolve from exactly one AuditExecutionReceipt"
        )
        return errors
    receipt = receipts[0]
    if receipt.get("execution_state") != "COMPLETED":
        errors.append("SATISFIED AuditExecutionReceipt execution_state must be COMPLETED")
    related_for_receipt = [
        candidate
        for candidate in related_objects or []
        if not (
            candidate.get("schema_version") == "audit-broker-audit-result.v0"
            and candidate.get("result_id") == instance.get("result_id")
        )
    ]
    related_for_receipt.append(instance)
    errors.extend(_audit_execution_receipt_errors(receipt, related_for_receipt))
    receipt_route = receipt.get("route")
    if isinstance(snapshot_route, dict) and receipt_route != {
        "runner": snapshot_route.get("runner"),
        "tool": snapshot_route.get("tool"),
    }:
        errors.append("SATISFIED execution route must exactly match observed snapshot route")
    return errors


def _compiled_claim_errors(
    instance: dict[str, Any], related_objects: list[dict[str, Any]] | None
) -> list[str]:
    if instance.get("eligible_for_materialization") is not True:
        return []
    inputs = _related_matches(
        related_objects,
        schema_version="sb-knowledge-compiler-input.v0",
        id_field="input_id",
        expected_id=instance.get("input_ref"),
    )
    if len(inputs) != 1:
        return [
            "eligible CompiledClaim input_ref must resolve to exactly one ELIGIBLE KnowledgeCompilerInput"
        ]
    policy = inputs[0].get("policy")
    if not isinstance(policy, dict) or policy.get("provider_policy_state") != "ELIGIBLE":
        return [
            "eligible CompiledClaim input_ref must resolve to exactly one ELIGIBLE KnowledgeCompilerInput"
        ]
    return []


def validate_p0_contract_semantics(
    schema_path: str, instance: Any, *, related_objects: list[dict[str, Any]] | None = None
) -> list[str]:
    """Return stable semantic errors for one schema/instance pair."""

    if not isinstance(instance, dict):
        return ["instance must be an object"]
    normalized = _normalized_schema_path(schema_path)
    if normalized.endswith(RUN_CONTEXT_SCHEMA):
        return _run_context_errors(instance, related_objects)
    if normalized.endswith(AUDIT_RESULT_SCHEMA):
        return _audit_result_errors(instance, related_objects)
    if normalized.endswith(AUDIT_EXECUTION_RECEIPT_SCHEMA):
        return _audit_execution_receipt_errors(instance, related_objects)
    if normalized.endswith(COMPILED_CLAIM_SCHEMA):
        return _compiled_claim_errors(instance, related_objects)
    return []


def _validate_fixture_file(path: Path) -> list[str]:
    fixtures = json.loads(path.read_text(encoding="utf-8"))
    related_objects = [fixture.get("instance") for fixture in fixtures if isinstance(fixture.get("instance"), dict)]
    errors: list[str] = []
    for fixture in fixtures:
        name = fixture.get("name", "<unnamed>")
        schema = fixture.get("schema")
        instance = fixture.get("instance")
        if not isinstance(schema, str):
            errors.append(f"{name}: schema path is missing")
            continue
        errors.extend(
            f"{name}: {error}"
            for error in validate_p0_contract_semantics(schema, instance, related_objects=related_objects)
        )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    errors = _validate_fixture_file(args.fixtures)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: P0 semantic validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
