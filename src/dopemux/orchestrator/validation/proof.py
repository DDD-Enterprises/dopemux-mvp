"""Read-only proof bundle shape validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, List, Mapping

from .json_io import load_json_object
from .report import ValidationIssue, ValidationReport, issue, path_text, sort_issues


ALLOWED_PROOF_STATUSES = {
    "PLAN_ONLY",
    "SPECIFICATION_COMPLETE",
    "IMPLEMENTATION_STARTED",
    "IMPLEMENTATION_COMPLETE",
    "READY_FOR_REVIEW",
    "VERIFIED",
    "BLOCKED",
}

ALLOWED_VALIDATION_STATES = {
    "NOT_STARTED",
    "IN_PROGRESS",
    "PASSED",
    "FAILED",
    "PARTIAL",
}

READY_STATUSES = {"READY_FOR_REVIEW", "VERIFIED"}


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: Any) -> bool:
    return isinstance(value, list) and all(_non_empty_string(item) for item in value)


def _entry_has_artifact(entry: Any) -> bool:
    if not isinstance(entry, Mapping):
        return False
    for key in ("artifact", "artifact_path", "evidence", "evidence_path"):
        if _non_empty_string(entry.get(key)):
            return True
    return False


def _warning_blocker_entries(payload: Mapping[str, Any]) -> Iterable[Any]:
    for key in ("warnings", "blockers"):
        values = payload.get(key, [])
        if isinstance(values, list):
            yield from values


def _validate_manifest(payload: Mapping[str, Any]) -> List[ValidationIssue]:
    manifest = payload.get("manifest")
    if manifest is None:
        return [
            issue(
                "PROOF_MANIFEST_MISSING",
                "Proof bundle must include a manifest object.",
                path="/manifest",
            )
        ]
    if not isinstance(manifest, Mapping):
        return [
            issue(
                "PROOF_MANIFEST_INVALID",
                "Proof manifest must be a JSON object.",
                path="/manifest",
            )
        ]

    errors: List[ValidationIssue] = []
    if not _non_empty_string(manifest.get("bundle_id")):
        errors.append(
            issue(
                "PROOF_MANIFEST_BUNDLE_ID_MISSING",
                "Proof manifest must include manifest.bundle_id.",
                path="/manifest/bundle_id",
            )
        )
    if not _non_empty_string(manifest.get("packet_id")):
        errors.append(
            issue(
                "PROOF_MANIFEST_PACKET_ID_MISSING",
                "Proof manifest must include manifest.packet_id.",
                path="/manifest/packet_id",
            )
        )
    artifacts = manifest.get("generated_artifacts", manifest.get("artifacts"))
    if not _string_list(artifacts):
        errors.append(
            issue(
                "PROOF_MANIFEST_ARTIFACTS_MISSING",
                "Proof manifest must list generated artifacts.",
                path="/manifest/generated_artifacts",
            )
        )
    return errors


def _validate_chain(payload: Mapping[str, Any]) -> List[ValidationIssue]:
    chain = payload.get("chain_of_custody")
    if chain is None:
        return [
            issue(
                "PROOF_CHAIN_OF_CUSTODY_MISSING",
                "Proof bundle must include chain_of_custody.",
                path="/chain_of_custody",
            )
        ]
    if not isinstance(chain, Mapping):
        return [
            issue(
                "PROOF_CHAIN_OF_CUSTODY_INVALID",
                "chain_of_custody must be a JSON object.",
                path="/chain_of_custody",
            )
        ]

    errors: List[ValidationIssue] = []
    if chain.get("documented") is not True:
        errors.append(
            issue(
                "PROOF_CHAIN_OF_CUSTODY_UNDOCUMENTED",
                "chain_of_custody.documented must be true.",
                path="/chain_of_custody/documented",
            )
        )
    if not _non_empty_string(chain.get("source_version")):
        errors.append(
            issue(
                "PROOF_CHAIN_SOURCE_VERSION_MISSING",
                "chain_of_custody.source_version must be present.",
                path="/chain_of_custody/source_version",
            )
        )
    if not _non_empty_string(chain.get("created_at")):
        errors.append(
            issue(
                "PROOF_CHAIN_CREATED_AT_MISSING",
                "chain_of_custody.created_at must be present.",
                path="/chain_of_custody/created_at",
            )
        )
    parent_ids = chain.get("parent_bundle_ids", [])
    if not isinstance(parent_ids, list):
        errors.append(
            issue(
                "PROOF_CHAIN_PARENT_IDS_INVALID",
                "chain_of_custody.parent_bundle_ids must be a list when present.",
                path="/chain_of_custody/parent_bundle_ids",
            )
        )
    return errors


def _validate_statuses(payload: Mapping[str, Any]) -> List[ValidationIssue]:
    errors: List[ValidationIssue] = []
    status = payload.get("status")
    if status not in ALLOWED_PROOF_STATUSES:
        errors.append(
            issue(
                "PROOF_STATUS_INVALID",
                f"status must be one of {sorted(ALLOWED_PROOF_STATUSES)}.",
                path="/status",
            )
        )

    validation_state = payload.get("validation_state")
    if validation_state not in ALLOWED_VALIDATION_STATES:
        errors.append(
            issue(
                "PROOF_VALIDATION_STATE_INVALID",
                f"validation_state must be one of {sorted(ALLOWED_VALIDATION_STATES)}.",
                path="/validation_state",
            )
        )

    blockers = payload.get("blockers", [])
    if status in READY_STATUSES and isinstance(blockers, list) and blockers:
        errors.append(
            issue(
                "PROOF_BLOCKERS_CONFLICT_WITH_STATUS",
                "READY_FOR_REVIEW and VERIFIED proof bundles cannot carry blockers.",
                path="/blockers",
            )
        )
    return errors


def _validate_artifacts(payload: Mapping[str, Any]) -> List[ValidationIssue]:
    errors: List[ValidationIssue] = []
    authoritative = payload.get("authoritative_artifacts")
    if not _string_list(authoritative):
        errors.append(
            issue(
                "PROOF_AUTHORITATIVE_ARTIFACTS_INVALID",
                "authoritative_artifacts must be a non-empty list of strings.",
                path="/authoritative_artifacts",
            )
        )

    supporting = payload.get("supporting_artifacts", [])
    if not isinstance(supporting, list) or not all(
        isinstance(item, str) for item in supporting
    ):
        errors.append(
            issue(
                "PROOF_SUPPORTING_ARTIFACTS_INVALID",
                "supporting_artifacts must be a list of strings when present.",
                path="/supporting_artifacts",
            )
        )
        supporting = []

    for key in ("warnings", "blockers"):
        if not isinstance(payload.get(key, []), list):
            errors.append(
                issue(
                    "PROOF_WARNING_OR_BLOCKER_LIST_INVALID",
                    f"{key} must be a list when present.",
                    path=f"/{key}",
                )
            )

    entries = list(_warning_blocker_entries(payload))
    if (
        entries
        and not supporting
        and not all(_entry_has_artifact(entry) for entry in entries)
    ):
        errors.append(
            issue(
                "PROOF_WARNING_OR_BLOCKER_ARTIFACT_MISSING",
                "Warnings and blockers must be supported by artifacts or inline artifact references.",
                path="/warnings",
            )
        )
    return errors


def validate_proof_file(proof_path: str | Path) -> ValidationReport:
    proof = Path(proof_path)
    payload, load_errors = load_json_object(proof)
    errors: List[ValidationIssue] = [*load_errors]

    if payload is not None:
        errors.extend(_validate_manifest(payload))
        errors.extend(_validate_chain(payload))
        errors.extend(_validate_statuses(payload))
        errors.extend(_validate_artifacts(payload))

    sorted_errors = sort_issues(errors)
    status = "PASS" if not sorted_errors else "FAIL"
    return ValidationReport(
        kind="proof_bundle",
        path=path_text(proof),
        authority="proof-bundle-governance",
        status=status,
        valid=status == "PASS",
        errors=sorted_errors,
        details={
            "authority_boundary": "read_only_proof_shape_validation_only",
            "allowed_statuses": sorted(ALLOWED_PROOF_STATUSES),
            "allowed_validation_states": sorted(ALLOWED_VALIDATION_STATES),
        },
        exit_code=0 if status == "PASS" else 3,
    )
