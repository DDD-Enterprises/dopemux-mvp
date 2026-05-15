from __future__ import annotations

import copy
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


PROVENANCE_SCHEMA_VERSION = "rte_artifact_provenance_v1"
PROVENANCE_META_KEY = "artifact_provenance"

ALLOWED_PROVENANCE_KINDS = frozenset(
    {
        "primary_observed",
        "deterministic_parse_repair",
        "deterministic_schema_repair",
        "provider_repair",
        "sidefill",
        "enrichment",
        "comparison",
        "prescan_derived",
        "unknown_derived",
    }
)

FIELD_PROVENANCE_REQUIRED_FIELDS: Tuple[str, ...] = (
    "field_path",
    "artifact_name",
    "provenance_kind",
    "source_lane",
    "source_phase",
    "source_step_id",
    "source_partition_id",
    "reason_code",
    "confidence_if_available",
    "original_value_present",
    "original_value_ref",
    "replacement_value_present",
    "repair_or_sidefill_provider_if_any",
    "repair_or_sidefill_model_id_if_any",
    "request_meta_ref_if_any",
    "failed_sidecar_ref_if_any",
    "generated_at",
)

ARTIFACT_PROVENANCE_REQUIRED_FIELDS: Tuple[str, ...] = (
    "artifact_name",
    "provenance_kind",
    "source_lane",
    "source_phase",
    "source_step_id",
    "source_partition_id",
    "reason_code",
    "derived_field_count",
    "primary_observed_field_count",
    "failed_sidecar_refs",
    "raw_artifact_refs",
    "request_meta_refs",
    "prescan_influence_refs_if_any",
    "comparison_refs_if_any",
    "generated_at",
)

_SOURCE_LANE_BY_KIND = {
    "primary_observed": "primary",
    "deterministic_parse_repair": "parse_repair",
    "deterministic_schema_repair": "schema_repair",
    "provider_repair": "repair",
    "sidefill": "sidefill",
    "enrichment": "enrichment",
    "comparison": "comparison",
    "prescan_derived": "prescan",
    "unknown_derived": "unknown_derived",
}

_MISSING = object()


def _coerce_kind(provenance_kind: str) -> str:
    token = str(provenance_kind or "").strip()
    return token if token in ALLOWED_PROVENANCE_KINDS else "unknown_derived"


def source_lane_for_kind(provenance_kind: str) -> str:
    return _SOURCE_LANE_BY_KIND.get(_coerce_kind(provenance_kind), "unknown_derived")


def _iter_field_paths(value: Any, prefix: str) -> Iterable[Tuple[str, Any]]:
    if isinstance(value, dict):
        if not value:
            yield prefix, value
            return
        for key in sorted(value.keys(), key=str):
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_field_paths(value[key], child_prefix)
        return
    if isinstance(value, list):
        if not value:
            yield prefix, value
            return
        for idx, child in enumerate(value):
            yield from _iter_field_paths(child, f"{prefix}[{idx}]")
        return
    yield prefix, value


def artifact_field_maps(
    artifacts: Sequence[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    maps: Dict[str, Dict[str, Any]] = {}
    for row in artifacts:
        if not isinstance(row, dict):
            continue
        artifact_name = str(row.get("artifact_name") or "").strip()
        if not artifact_name:
            continue
        maps[artifact_name] = {
            field_path: copy.deepcopy(value)
            for field_path, value in _iter_field_paths(row.get("payload"), "payload")
        }
    return maps


def _value_ref(
    *,
    artifact_name: str,
    field_path: str,
    value_present: bool,
    fallback_ref: Optional[str],
) -> Optional[str]:
    if value_present:
        return f"{artifact_name}:{field_path}"
    return str(fallback_ref) if fallback_ref else None


def make_field_record(
    *,
    field_path: str,
    artifact_name: str,
    provenance_kind: str,
    source_phase: str,
    source_step_id: str,
    source_partition_id: str,
    reason_code: str,
    generated_at: str,
    original_value_present: bool,
    replacement_value_present: bool,
    original_value_ref: Optional[str] = None,
    source_lane: Optional[str] = None,
    confidence_if_available: Optional[Any] = None,
    repair_or_sidefill_provider_if_any: Optional[str] = None,
    repair_or_sidefill_model_id_if_any: Optional[str] = None,
    request_meta_ref_if_any: Optional[str] = None,
    failed_sidecar_ref_if_any: Optional[str] = None,
) -> Dict[str, Any]:
    kind = _coerce_kind(provenance_kind)
    return {
        "field_path": str(field_path),
        "artifact_name": str(artifact_name),
        "provenance_kind": kind,
        "source_lane": str(source_lane or source_lane_for_kind(kind)),
        "source_phase": str(source_phase),
        "source_step_id": str(source_step_id),
        "source_partition_id": str(source_partition_id),
        "reason_code": str(reason_code),
        "confidence_if_available": confidence_if_available,
        "original_value_present": bool(original_value_present),
        "original_value_ref": original_value_ref,
        "replacement_value_present": bool(replacement_value_present),
        "repair_or_sidefill_provider_if_any": repair_or_sidefill_provider_if_any,
        "repair_or_sidefill_model_id_if_any": repair_or_sidefill_model_id_if_any,
        "request_meta_ref_if_any": request_meta_ref_if_any,
        "failed_sidecar_ref_if_any": failed_sidecar_ref_if_any,
        "generated_at": str(generated_at),
    }


def records_for_artifact_fields(
    artifacts: Sequence[Dict[str, Any]],
    *,
    provenance_kind: str,
    source_phase: str,
    source_step_id: str,
    source_partition_id: str,
    reason_code: str,
    generated_at: str,
    original_artifacts: Optional[Sequence[Dict[str, Any]]] = None,
    original_context_ref: Optional[str] = None,
    source_lane: Optional[str] = None,
    repair_or_sidefill_provider_if_any: Optional[str] = None,
    repair_or_sidefill_model_id_if_any: Optional[str] = None,
    request_meta_ref_if_any: Optional[str] = None,
    failed_sidecar_ref_if_any: Optional[str] = None,
) -> List[Dict[str, Any]]:
    after_maps = artifact_field_maps(artifacts)
    before_maps = artifact_field_maps(original_artifacts or [])
    rows: List[Dict[str, Any]] = []
    for artifact_name in sorted(after_maps.keys()):
        before_fields = before_maps.get(artifact_name, {})
        for field_path in sorted(after_maps[artifact_name].keys()):
            original_present = field_path in before_fields
            rows.append(
                make_field_record(
                    field_path=field_path,
                    artifact_name=artifact_name,
                    provenance_kind=provenance_kind,
                    source_phase=source_phase,
                    source_step_id=source_step_id,
                    source_partition_id=source_partition_id,
                    reason_code=reason_code,
                    generated_at=generated_at,
                    original_value_present=original_present,
                    replacement_value_present=True,
                    original_value_ref=_value_ref(
                        artifact_name=artifact_name,
                        field_path=field_path,
                        value_present=original_present,
                        fallback_ref=original_context_ref,
                    ),
                    source_lane=source_lane,
                    repair_or_sidefill_provider_if_any=repair_or_sidefill_provider_if_any,
                    repair_or_sidefill_model_id_if_any=repair_or_sidefill_model_id_if_any,
                    request_meta_ref_if_any=request_meta_ref_if_any,
                    failed_sidecar_ref_if_any=failed_sidecar_ref_if_any,
                )
            )
    return rows


def records_for_changed_fields(
    before_artifacts: Sequence[Dict[str, Any]],
    after_artifacts: Sequence[Dict[str, Any]],
    *,
    provenance_kind: str,
    source_phase: str,
    source_step_id: str,
    source_partition_id: str,
    reason_code: str,
    generated_at: str,
    original_context_ref: Optional[str] = None,
    source_lane: Optional[str] = None,
    repair_or_sidefill_provider_if_any: Optional[str] = None,
    repair_or_sidefill_model_id_if_any: Optional[str] = None,
    request_meta_ref_if_any: Optional[str] = None,
    failed_sidecar_ref_if_any: Optional[str] = None,
) -> List[Dict[str, Any]]:
    before_maps = artifact_field_maps(before_artifacts)
    after_maps = artifact_field_maps(after_artifacts)
    rows: List[Dict[str, Any]] = []
    for artifact_name in sorted(set(before_maps.keys()) | set(after_maps.keys())):
        before_fields = before_maps.get(artifact_name, {})
        after_fields = after_maps.get(artifact_name, {})
        for field_path in sorted(set(before_fields.keys()) | set(after_fields.keys())):
            before_value = before_fields.get(field_path, _MISSING)
            after_value = after_fields.get(field_path, _MISSING)
            if before_value == after_value:
                continue
            original_present = before_value is not _MISSING
            replacement_present = after_value is not _MISSING
            rows.append(
                make_field_record(
                    field_path=field_path,
                    artifact_name=artifact_name,
                    provenance_kind=provenance_kind,
                    source_phase=source_phase,
                    source_step_id=source_step_id,
                    source_partition_id=source_partition_id,
                    reason_code=reason_code,
                    generated_at=generated_at,
                    original_value_present=original_present,
                    replacement_value_present=replacement_present,
                    original_value_ref=_value_ref(
                        artifact_name=artifact_name,
                        field_path=field_path,
                        value_present=original_present,
                        fallback_ref=original_context_ref,
                    ),
                    source_lane=source_lane,
                    repair_or_sidefill_provider_if_any=repair_or_sidefill_provider_if_any,
                    repair_or_sidefill_model_id_if_any=repair_or_sidefill_model_id_if_any,
                    request_meta_ref_if_any=request_meta_ref_if_any,
                    failed_sidecar_ref_if_any=failed_sidecar_ref_if_any,
                )
            )
    return rows


def _stable_unique(values: Iterable[Any]) -> List[str]:
    return sorted({str(value) for value in values if str(value or "").strip()})


def build_artifact_provenance_payload(
    *,
    artifacts: Sequence[Dict[str, Any]],
    field_records: Sequence[Dict[str, Any]],
    source_phase: str,
    source_step_id: str,
    source_partition_id: str,
    generated_at: str,
    raw_artifact_refs: Optional[Sequence[str]] = None,
    failed_sidecar_refs: Optional[Sequence[str]] = None,
    request_meta_refs: Optional[Sequence[str]] = None,
    prescan_influence_refs_if_any: Optional[Sequence[str]] = None,
    comparison_refs_if_any: Optional[Sequence[str]] = None,
    truth_label_records: Optional[Sequence[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    final_maps = artifact_field_maps(artifacts)
    normalized_field_records = [
        dict(record)
        for record in field_records
        if isinstance(record, dict)
        and str(record.get("provenance_kind") or "") in ALLOWED_PROVENANCE_KINDS
    ]
    normalized_field_records.sort(
        key=lambda row: (
            str(row.get("artifact_name") or ""),
            str(row.get("field_path") or ""),
            str(row.get("provenance_kind") or ""),
            str(row.get("reason_code") or ""),
        )
    )
    normalized_truth_label_records = [
        dict(record) for record in truth_label_records or [] if isinstance(record, dict)
    ]
    normalized_truth_label_records.sort(
        key=lambda row: (
            str(row.get("artifact_name") or ""),
            str(row.get("field_path") or ""),
            str(row.get("truth_label") or ""),
            str(row.get("provenance_kind") or ""),
            str(row.get("transition_action") or ""),
        )
    )

    derived_paths_by_artifact: Dict[str, set[str]] = {}
    kinds_by_artifact: Dict[str, set[str]] = {}
    request_refs_by_artifact: Dict[str, set[str]] = {}
    failed_refs_by_artifact: Dict[str, set[str]] = {}
    for record in normalized_field_records:
        artifact_name = str(record.get("artifact_name") or "").strip()
        field_path = str(record.get("field_path") or "").strip()
        if not artifact_name or not field_path:
            continue
        if bool(record.get("replacement_value_present", True)):
            derived_paths_by_artifact.setdefault(artifact_name, set()).add(field_path)
        kind = _coerce_kind(str(record.get("provenance_kind") or ""))
        if kind != "primary_observed":
            kinds_by_artifact.setdefault(artifact_name, set()).add(kind)
        request_ref = record.get("request_meta_ref_if_any")
        if request_ref:
            request_refs_by_artifact.setdefault(artifact_name, set()).add(
                str(request_ref)
            )
        failed_ref = record.get("failed_sidecar_ref_if_any")
        if failed_ref:
            failed_refs_by_artifact.setdefault(artifact_name, set()).add(
                str(failed_ref)
            )

    artifact_records: List[Dict[str, Any]] = []
    artifact_order = [
        str(row.get("artifact_name") or "").strip()
        for row in artifacts
        if isinstance(row, dict) and str(row.get("artifact_name") or "").strip()
    ]
    for artifact_name in artifact_order:
        all_paths = set(final_maps.get(artifact_name, {}).keys())
        derived_paths = derived_paths_by_artifact.get(artifact_name, set())
        derived_count = len(derived_paths)
        primary_count = max(0, len(all_paths - derived_paths))
        derived_kinds = kinds_by_artifact.get(artifact_name, set())
        if not derived_kinds:
            provenance_kind = "primary_observed"
            reason_code = "primary_observed_extraction"
        elif len(derived_kinds) == 1:
            provenance_kind = next(iter(derived_kinds))
            reason_code = f"{provenance_kind}_fields_present"
        else:
            provenance_kind = "unknown_derived"
            reason_code = "multiple_derived_field_kinds_present"
        artifact_records.append(
            {
                "artifact_name": artifact_name,
                "provenance_kind": provenance_kind,
                "source_lane": source_lane_for_kind(provenance_kind),
                "source_phase": str(source_phase),
                "source_step_id": str(source_step_id),
                "source_partition_id": str(source_partition_id),
                "reason_code": reason_code,
                "derived_field_count": int(derived_count),
                "primary_observed_field_count": int(primary_count),
                "failed_sidecar_refs": _stable_unique(
                    list(failed_sidecar_refs or [])
                    + list(failed_refs_by_artifact.get(artifact_name, set()))
                ),
                "raw_artifact_refs": _stable_unique(raw_artifact_refs or []),
                "request_meta_refs": _stable_unique(
                    list(request_meta_refs or [])
                    + list(request_refs_by_artifact.get(artifact_name, set()))
                ),
                "prescan_influence_refs_if_any": _stable_unique(
                    prescan_influence_refs_if_any or []
                ),
                "comparison_refs_if_any": _stable_unique(
                    comparison_refs_if_any or []
                ),
                "generated_at": str(generated_at),
            }
        )

    summary = {
        "field_records_total": len(normalized_field_records),
        "artifact_records_total": len(artifact_records),
        "derived_field_records_total": sum(
            1
            for record in normalized_field_records
            if record.get("provenance_kind") != "primary_observed"
        ),
        "primary_observed_artifacts_total": sum(
            1
            for record in artifact_records
            if record.get("provenance_kind") == "primary_observed"
        ),
        "derived_artifacts_total": sum(
            1
            for record in artifact_records
            if record.get("provenance_kind") != "primary_observed"
        ),
        "provenance_kinds": sorted(
            {
                str(record.get("provenance_kind"))
                for record in (
                    normalized_field_records
                    + artifact_records
                    + normalized_truth_label_records
                )
                if str(record.get("provenance_kind") or "").strip()
            }
        ),
        "truth_label_records_total": len(normalized_truth_label_records),
        "protected_truth_label_records_total": sum(
            1
            for record in normalized_truth_label_records
            if str(record.get("truth_label") or "") in {"UNKNOWN", "CONFLICTING"}
        ),
        "truth_labels": sorted(
            {
                str(record.get("truth_label"))
                for record in normalized_truth_label_records
                if str(record.get("truth_label") or "").strip()
            }
        ),
    }
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "generated_at": str(generated_at),
        "field_records": normalized_field_records,
        "artifact_records": artifact_records,
        "truth_label_records": normalized_truth_label_records,
        "summary": summary,
    }


def validate_provenance_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if payload.get("schema_version") != PROVENANCE_SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    field_records = payload.get("field_records")
    if not isinstance(field_records, list):
        errors.append("field_records_not_list")
        field_records = []
    artifact_records = payload.get("artifact_records")
    if not isinstance(artifact_records, list):
        errors.append("artifact_records_not_list")
        artifact_records = []
    for idx, record in enumerate(field_records):
        if not isinstance(record, dict):
            errors.append(f"field_record_{idx}_not_object")
            continue
        missing = set(FIELD_PROVENANCE_REQUIRED_FIELDS) - set(record.keys())
        if missing:
            errors.append(f"field_record_{idx}_missing:{','.join(sorted(missing))}")
        if record.get("provenance_kind") not in ALLOWED_PROVENANCE_KINDS:
            errors.append(f"field_record_{idx}_invalid_kind")
    for idx, record in enumerate(artifact_records):
        if not isinstance(record, dict):
            errors.append(f"artifact_record_{idx}_not_object")
            continue
        missing = set(ARTIFACT_PROVENANCE_REQUIRED_FIELDS) - set(record.keys())
        if missing:
            errors.append(f"artifact_record_{idx}_missing:{','.join(sorted(missing))}")
        if record.get("provenance_kind") not in ALLOWED_PROVENANCE_KINDS:
            errors.append(f"artifact_record_{idx}_invalid_kind")
    return errors
