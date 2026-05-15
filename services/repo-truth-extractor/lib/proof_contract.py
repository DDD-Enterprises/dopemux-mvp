from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


CONFORMANCE_STATUSES: Tuple[str, ...] = (
    "SATISFIED",
    "PARTIAL",
    "MISSING",
    "UNKNOWN",
    "NOT_APPLICABLE",
)

ARTIFACT_CLASSIFICATIONS: Tuple[str, ...] = (
    "runtime_authority",
    "runtime_generated_evidence",
    "proof_governance_artifact",
    "generated_audit_context",
    "external_advisory_context",
    "sample_artifact_uncertain_lineage",
    "unknown",
)

PROOF_CONTRACT_REQUIRED_FIELDS: Tuple[str, ...] = (
    "bundle_id",
    "run_id",
    "source_version",
    "repo_root",
    "git_sha",
    "runner_sha",
    "command_argv",
    "cwd",
    "status",
    "validation_state",
    "run_posture",
    "generated_at",
    "phase_list",
    "generated_artifact_list",
    "authoritative_artifacts",
    "supporting_artifacts",
    "runtime_authority_artifacts",
    "generated_evidence_artifacts",
    "proof_governance_artifacts",
    "external_advisory_artifacts",
    "sample_or_uncertain_lineage_artifacts",
    "chain_of_custody",
    "warnings",
    "blockers",
    "handoff_refs",
    "parent_bundle_refs",
    "review_order_hint",
    "live_validation_status",
    "provider_call_status",
    "batch_operation_status",
    "redaction_status",
    "artifact_hashes",
)

_FIELD_ALIASES: Mapping[str, Tuple[str, ...]] = {
    "runner_sha": ("runner_sha", "runner_sha256"),
    "command_argv": ("command_argv", "argv", "cli.argv"),
    "generated_at": ("generated_at", "generated_at_utc", "created_at", "updated_at"),
    "phase_list": ("phase_list", "phases", "routing_step_tiers"),
    "generated_artifact_list": (
        "generated_artifact_list",
        "linked_artifacts",
        "artifacts",
        "proof_files",
        "changed_files",
    ),
    "warnings": ("warnings", "residual_risks"),
    "blockers": ("blockers", "blocking_reasons"),
    "artifact_hashes": ("artifact_hashes", "checksums"),
}

_NON_EMPTY_REQUIRED_FIELDS = frozenset(
    {
        "bundle_id",
        "run_id",
        "source_version",
        "repo_root",
        "git_sha",
        "runner_sha",
        "command_argv",
        "cwd",
        "status",
        "validation_state",
        "run_posture",
        "generated_at",
        "phase_list",
        "generated_artifact_list",
        "authoritative_artifacts",
        "supporting_artifacts",
        "runtime_authority_artifacts",
        "generated_evidence_artifacts",
        "proof_governance_artifacts",
        "external_advisory_artifacts",
        "sample_or_uncertain_lineage_artifacts",
        "chain_of_custody",
        "artifact_hashes",
    }
)

_RUNTIME_GENERATED_NAMES = frozenset(
    {
        "PROOF_PACK.json",
        "RUN_MANIFEST.json",
        "COVERAGE_ROLLUP.json",
        "RESUME_PROOF.json",
        "CERTIFICATION_RESULT.json",
        "RUN_DASHBOARD.json",
        "STEP_METRICS.json",
        "FAILURE_INDEX.json",
        "STRICT_PASSTHROUGH_ATTESTATIONS.json",
    }
)

_AUTHORITY_RANK = {
    "runtime_authority": 100,
    "proof_governance_artifact": 60,
    "runtime_generated_evidence": 50,
    "generated_audit_context": 40,
    "external_advisory_context": 30,
    "sample_artifact_uncertain_lineage": 20,
    "unknown": 0,
}


def _normalize_rel_path(path: str | Path) -> str:
    text = str(path).replace("\\", "/")
    marker = "/dopemux-mvp/"
    if marker in text:
        return text.split(marker, 1)[1]
    return text.lstrip("./")


def _get_path(payload: Mapping[str, Any], dotted_path: str) -> tuple[bool, Any]:
    cursor: Any = payload
    for part in dotted_path.split("."):
        if not isinstance(cursor, Mapping) or part not in cursor:
            return False, None
        cursor = cursor[part]
    return True, cursor


def _has_value(value: Any, *, require_non_empty: bool) -> bool:
    if value is None:
        return False
    if not require_non_empty:
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _walk_values(value: Any) -> Iterable[Any]:
    if isinstance(value, Mapping):
        for key in sorted(value.keys(), key=str):
            yield from _walk_values(value[key])
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            yield from _walk_values(item)
        return
    yield value


def _contains_marker(payload: Mapping[str, Any], markers: set[str]) -> bool:
    for value in _walk_values(payload):
        if isinstance(value, str) and value in markers:
            return True
    return False


def _derive_provider_call_status(payload: Mapping[str, Any]) -> Optional[str]:
    explicit, value = _get_path(payload, "provider_call_status")
    if explicit and _has_value(value, require_non_empty=True):
        return str(value)

    provider_calls, row = _get_path(payload, "provider_calls.live_provider_calls_run")
    if provider_calls:
        return "RUN" if bool(row) else "NOT_RUN"

    for path in (
        "safety_boundary_confirmation.live_provider_calls_run",
        "live_provider_calls_run",
    ):
        present, value = _get_path(payload, path)
        if present:
            return "RUN" if bool(value) else "NOT_RUN"
    return None


def _derive_batch_operation_status(payload: Mapping[str, Any]) -> Optional[str]:
    explicit, value = _get_path(payload, "batch_operation_status")
    if explicit and _has_value(value, require_non_empty=True):
        return str(value)

    for path in (
        "batch_provider_operations",
        "provider_calls.batch_submit_poll_retrieve_cancel_run",
        "safety_boundary_confirmation.external_batch_jobs_submitted",
        "external_batch_jobs_submitted",
    ):
        present, value = _get_path(payload, path)
        if present:
            if isinstance(value, str):
                return value
            return "RUN" if bool(value) else "NOT_RUN"
    return None


def _derive_live_validation_status(payload: Mapping[str, Any]) -> Optional[str]:
    explicit, value = _get_path(payload, "live_validation_status")
    if explicit and _has_value(value, require_non_empty=True):
        return str(value)

    if _contains_marker(payload, {"LIVE_VALIDATION_REQUIRED"}):
        return "LIVE_VALIDATION_REQUIRED"
    if _contains_marker(payload, {"NOT_LIVE_VALIDATED"}):
        return "NOT_LIVE_VALIDATED"

    present, value = _get_path(payload, "live_validation_run")
    if present:
        return "RUN" if bool(value) else "NOT_RUN"

    present, value = _get_path(payload, "live_extraction_runs_run")
    if present:
        return "RUN" if bool(value) else "NOT_RUN"
    return None


def _derive_run_posture(payload: Mapping[str, Any]) -> Optional[str]:
    explicit, value = _get_path(payload, "run_posture")
    if explicit and _has_value(value, require_non_empty=True):
        return str(value)
    live_status = _derive_live_validation_status(payload)
    provider_status = _derive_provider_call_status(payload)
    if live_status in {"NOT_RUN", "NOT_LIVE_VALIDATED", "LIVE_VALIDATION_REQUIRED"}:
        return "STATIC_ONLY"
    if provider_status == "NOT_RUN":
        return "STATIC_ONLY"
    return None


def _derive_redaction_status(payload: Mapping[str, Any]) -> Optional[str]:
    explicit, value = _get_path(payload, "redaction_status")
    if explicit and _has_value(value, require_non_empty=True):
        return str(value)
    present, value = _get_path(payload, "redaction.status")
    if present and _has_value(value, require_non_empty=True):
        return str(value)
    return None


def _derived_status(field: str, payload: Mapping[str, Any]) -> Optional[str]:
    if field == "provider_call_status":
        return _derive_provider_call_status(payload)
    if field == "batch_operation_status":
        return _derive_batch_operation_status(payload)
    if field == "live_validation_status":
        return _derive_live_validation_status(payload)
    if field == "run_posture":
        return _derive_run_posture(payload)
    if field == "redaction_status":
        return _derive_redaction_status(payload)
    return None


def classify_artifact(
    artifact_path: str | Path,
    *,
    payload: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    rel_path = _normalize_rel_path(artifact_path)
    name = Path(rel_path).name
    payload = payload or {}

    if "/fixtures/" in f"/{rel_path}/" or "sample" in rel_path.lower():
        classification = "sample_artifact_uncertain_lineage"
    elif rel_path == "services/repo-truth-extractor/run_extraction_v5.py":
        classification = "runtime_authority"
    elif (
        rel_path.startswith("services/repo-truth-extractor/")
        and rel_path.endswith(".py")
        and "/tests/" not in rel_path
        and "/extraction/" not in rel_path
    ):
        classification = "runtime_authority"
    elif rel_path.startswith("src/dopemux/") and rel_path.endswith(".py"):
        classification = "runtime_authority"
    elif (
        rel_path.startswith("services/repo-truth-extractor/extraction/")
        or name in _RUNTIME_GENERATED_NAMES
    ):
        classification = "runtime_generated_evidence"
    elif (
        rel_path.startswith("out/rte-pkt-")
        or rel_path.startswith("proof/TP-RTE-")
        or rel_path.startswith("proof/rte-")
    ):
        classification = "proof_governance_artifact"
    elif (
        rel_path.startswith("out/rte-55pro-audit-pack/")
        or rel_path.startswith("audit_inputs/")
    ):
        classification = "generated_audit_context"
    elif "external" in rel_path.lower() or "/dr-upload/" in f"/{rel_path}/":
        classification = "external_advisory_context"
    else:
        classification = "unknown"

    live_validation_status = _derive_live_validation_status(payload)
    provider_call_status = _derive_provider_call_status(payload)
    static_only = live_validation_status in {
        "NOT_RUN",
        "NOT_LIVE_VALIDATED",
        "LIVE_VALIDATION_REQUIRED",
    } or provider_call_status == "NOT_RUN"

    return {
        "artifact_path": rel_path,
        "classification": classification,
        "authority_rank": _AUTHORITY_RANK[classification],
        "is_runtime_source_authority": classification == "runtime_authority",
        "is_generated_evidence": classification
        in {
            "runtime_generated_evidence",
            "proof_governance_artifact",
            "generated_audit_context",
            "sample_artifact_uncertain_lineage",
        },
        "static_only": bool(static_only),
        "live_validation_status": live_validation_status or "UNKNOWN",
        "provider_call_status": provider_call_status or "UNKNOWN",
        "authority_boundary": (
            "runtime source authority outranks generated proof evidence"
            if classification != "runtime_authority"
            else "runtime source authority"
        ),
    }


def classify_artifact_authority_order(
    artifact_paths: Sequence[str | Path],
) -> list[Dict[str, Any]]:
    rows = [classify_artifact(path) for path in artifact_paths]
    return sorted(
        rows,
        key=lambda row: (-int(row["authority_rank"]), row["artifact_path"]),
    )


def _field_status(
    field: str,
    payload: Mapping[str, Any],
) -> Dict[str, Any]:
    aliases = (field,) + _FIELD_ALIASES.get(field, ())
    seen = []
    require_non_empty = field in _NON_EMPTY_REQUIRED_FIELDS
    for alias in aliases:
        present, value = _get_path(payload, alias)
        if not present:
            continue
        seen.append(alias)
        if _has_value(value, require_non_empty=require_non_empty):
            status = (
                "SATISFIED"
                if alias == field or field != "source_version"
                else "PARTIAL"
            )
            reason = (
                "field present"
                if status == "SATISFIED"
                else "alias present but exact source_version absent"
            )
            return {
                "status": status,
                "observed_field": alias,
                "observed_value": value,
                "reason": reason,
            }

    derived = _derived_status(field, payload)
    if derived is not None:
        return {
            "status": "SATISFIED",
            "observed_field": f"derived.{field}",
            "observed_value": derived,
            "reason": "derived from explicit run-safety fields",
        }

    if field == "validation_state":
        for evidence_field in (
            "validations",
            "validation_summary",
            "validation_commands",
            "final_closeout_validation",
        ):
            present, value = _get_path(payload, evidence_field)
            if present and _has_value(value, require_non_empty=True):
                return {
                    "status": "PARTIAL",
                    "observed_field": evidence_field,
                    "observed_value": None,
                    "reason": (
                        "validation evidence present but validation_state is not "
                        "explicit"
                    ),
                }

    return {
        "status": "MISSING",
        "observed_field": None,
        "observed_value": None,
        "reason": (
            "field absent"
            if not seen
            else (
                "field present only with empty value where non-empty declaration is "
                "required"
            )
        ),
    }


def assess_exact_pass1_identity(payload: Mapping[str, Any]) -> Dict[str, Any]:
    run_present, run_id = _get_path(payload, "run_id")
    hashes_present, hashes = _get_path(payload, "artifact_hashes")
    pass1_present, pass1 = _get_path(payload, "pass1_artifact_identity")
    if (
        run_present
        and _has_value(run_id, require_non_empty=True)
        and hashes_present
        and _has_value(hashes, require_non_empty=True)
        and pass1_present
        and _has_value(pass1, require_non_empty=True)
    ):
        return {
            "status": "SATISFIED",
            "reason": (
                "run_id, artifact_hashes, and pass1_artifact_identity are present"
            ),
        }
    if run_present or hashes_present or pass1_present:
        return {
            "status": "PARTIAL",
            "reason": (
                "only part of run_id, artifact_hashes, and pass1_artifact_identity "
                "is present"
            ),
        }
    return {
        "status": "UNKNOWN",
        "reason": (
            "exact Pass 1 identity lacks run_id, artifact_hashes, and "
            "pass1_artifact_identity evidence"
        ),
    }


def build_conformance_report(
    payload: Mapping[str, Any],
    *,
    artifact_path: str | Path = "UNKNOWN",
    not_applicable_fields: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    not_applicable = set(not_applicable_fields or ())
    if not isinstance(payload, Mapping):
        return {
            "overall_status": "UNKNOWN",
            "reason": "payload is not a JSON object",
            "artifact": classify_artifact(artifact_path),
            "fields": {},
            "missing_fields": list(PROOF_CONTRACT_REQUIRED_FIELDS),
        }

    fields = {}
    for field in PROOF_CONTRACT_REQUIRED_FIELDS:
        if field in not_applicable:
            fields[field] = {
                "status": "NOT_APPLICABLE",
                "observed_field": None,
                "observed_value": None,
                "reason": "field explicitly marked not applicable by caller",
            }
        else:
            fields[field] = _field_status(field, payload)
    status_counts: Dict[str, int] = {status: 0 for status in CONFORMANCE_STATUSES}
    for result in fields.values():
        status_counts[str(result["status"])] += 1

    if (
        status_counts["MISSING"] == 0
        and status_counts["UNKNOWN"] == 0
        and status_counts["PARTIAL"] == 0
    ):
        overall_status = "SATISFIED"
    elif status_counts["SATISFIED"] == 0 and status_counts["PARTIAL"] == 0:
        overall_status = "MISSING"
    else:
        overall_status = "PARTIAL"

    artifact = classify_artifact(artifact_path, payload=payload)
    pass1_identity = assess_exact_pass1_identity(payload)
    is_full_bundle = overall_status == "SATISFIED"
    if is_full_bundle:
        proof_posture = "proof_contract_compliant_governance_bundle"
    elif artifact["classification"] in {
        "runtime_generated_evidence",
        "proof_governance_artifact",
    }:
        proof_posture = "run_proof_or_packet_evidence_not_full_bundle"
    else:
        proof_posture = "not_proof_contract_bundle"

    return {
        "overall_status": overall_status,
        "is_full_proof_contract_bundle": is_full_bundle,
        "proof_posture": proof_posture,
        "artifact": artifact,
        "fields": fields,
        "status_counts": status_counts,
        "missing_fields": [
            field
            for field, result in fields.items()
            if result["status"] in {"MISSING", "UNKNOWN"}
        ],
        "partial_fields": [
            field for field, result in fields.items() if result["status"] == "PARTIAL"
        ],
        "exact_pass1_identity": pass1_identity,
        "authority_boundary": (
            "generated artifacts do not outrank runtime source authority"
        ),
    }
