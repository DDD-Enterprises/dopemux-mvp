from __future__ import annotations

import copy
import json
import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


TRUTH_LABEL_SCHEMA_VERSION = "rte_truth_label_preservation_v1"
TRUTH_LABEL_META_KEY = "truth_label_preservation"

TRUTH_LABELS = frozenset(
    {
        "OBSERVED",
        "INFERRED",
        "CLAIMED",
        "UNKNOWN",
        "CONFLICTING",
        "RECOMMENDED",
        "LIVE_VALIDATION_REQUIRED",
        "MISSING",
        "BLOCKING",
        "ACCEPTED_WITH_RISK",
    }
)
PROTECTED_TRUTH_LABELS = frozenset({"UNKNOWN", "CONFLICTING"})
NON_AUTHORITATIVE_PROVENANCE_KINDS = frozenset(
    {"provider_repair", "sidefill", "comparison", "prescan_derived"}
)

TRUTH_LABEL_RECORD_REQUIRED_FIELDS: Tuple[str, ...] = (
    "truth_label",
    "previous_truth_label_if_changed",
    "label_source",
    "label_reason",
    "evidence_refs",
    "conflicting_values_if_any",
    "unknown_reason_if_any",
    "resolution_reason_if_any",
    "provenance_kind",
    "source_lane",
    "generated_at",
)

_SOURCE_BACKED_LABEL_SOURCES = frozenset(
    {
        "runtime_source",
        "source_excerpt",
        "source_artifact",
        "test_fixture",
        "higher_authority",
        "repo_truth",
    }
)

_PRESERVED_CONTEXT_KEYS = (
    "label_source",
    "label_reason",
    "evidence_refs",
    "conflicting_values_if_any",
    "conflicting_values",
    "unknown_reason_if_any",
    "unknown_reason",
    "resolution_reason_if_any",
)

_SECRET_SHAPED_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"]?[^'\"\s]{8,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|sk-[A-Za-z0-9_-]{20,}"
)
_HIGH_ENTROPY_RE = re.compile(r"^[A-Za-z0-9_\-]{40,}$")


def normalize_truth_label(value: Any) -> Optional[str]:
    token = str(value or "").strip().upper()
    return token if token in TRUTH_LABELS else None


def _source_lane_for_kind(provenance_kind: str) -> str:
    return {
        "primary_observed": "primary",
        "deterministic_parse_repair": "parse_repair",
        "deterministic_schema_repair": "schema_repair",
        "provider_repair": "repair",
        "sidefill": "sidefill",
        "enrichment": "enrichment",
        "comparison": "comparison",
        "prescan_derived": "prescan",
        "unknown_derived": "unknown_derived",
    }.get(str(provenance_kind or "").strip(), "unknown_derived")


def _safe_scalar(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    token = value.strip()
    if _SECRET_SHAPED_RE.search(token) or _HIGH_ENTROPY_RE.match(token):
        return "[REDACTED_SECRET_SHAPED_VALUE]"
    if len(token) > 160:
        return token[:157] + "..."
    return token


def _safe_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _safe_value(child)
            for key, child in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, list):
        return [_safe_value(child) for child in value[:20]]
    return _safe_scalar(value)


def _safe_refs(values: Iterable[Any]) -> List[str]:
    refs = sorted(
        {
            str(_safe_scalar(value)).strip()
            for value in values
            if str(value or "").strip()
        }
    )
    return refs[:50]


def _evidence_refs_from_container(container: Dict[str, Any]) -> List[str]:
    explicit_refs = container.get("evidence_refs")
    if isinstance(explicit_refs, list):
        return _safe_refs(explicit_refs)
    evidence = container.get("evidence")
    if not isinstance(evidence, list):
        return []
    refs: List[str] = []
    for row in evidence:
        if isinstance(row, dict):
            path = str(row.get("path") or "").strip()
            line_range = row.get("line_range")
            if (
                path
                and isinstance(line_range, list)
                and len(line_range) == 2
                and all(isinstance(value, int) for value in line_range)
            ):
                refs.append(f"{path}:{int(line_range[0])}-{int(line_range[1])}")
            elif path:
                refs.append(path)
        elif isinstance(row, str):
            refs.append(row)
    return _safe_refs(refs)


def _iter_truth_label_containers(
    value: Any,
    path: str,
) -> Iterable[Tuple[str, Dict[str, Any]]]:
    if isinstance(value, dict):
        if "truth_label" in value:
            field_path = f"{path}.truth_label" if path else "truth_label"
            yield field_path, value
        for key in sorted(value.keys(), key=str):
            child_path = f"{path}.{key}" if path else str(key)
            yield from _iter_truth_label_containers(value[key], child_path)
        return
    if isinstance(value, list):
        for idx, child in enumerate(value):
            yield from _iter_truth_label_containers(child, f"{path}[{idx}]")


def _field_record_lookup(
    field_records: Sequence[Dict[str, Any]],
) -> Dict[Tuple[str, str], Tuple[str, str]]:
    lookup: Dict[Tuple[str, str], Tuple[str, str]] = {}
    for record in field_records:
        if not isinstance(record, dict):
            continue
        artifact_name = str(record.get("artifact_name") or "").strip()
        field_path = str(record.get("field_path") or "").strip()
        provenance_kind = str(record.get("provenance_kind") or "").strip()
        if not artifact_name or not field_path or not provenance_kind:
            continue
        source_lane = str(record.get("source_lane") or "").strip() or _source_lane_for_kind(
            provenance_kind
        )
        current = lookup.get((artifact_name, field_path))
        if current and current[0] != "primary_observed":
            continue
        lookup[(artifact_name, field_path)] = (provenance_kind, source_lane)
    return lookup


def _container_item_id(container: Dict[str, Any]) -> Optional[str]:
    token = str(container.get("id") or "").strip()
    return token or None


def _record_for_container(
    *,
    artifact_name: str,
    field_path: str,
    container: Dict[str, Any],
    truth_label: str,
    provenance_kind: str,
    source_lane: str,
    generated_at: str,
    label_source_default: str,
    label_reason_default: str,
    transition_action: str,
    attempted_truth_label_if_any: Optional[str] = None,
    previous_truth_label_if_changed: Optional[str] = None,
    authoritative: Optional[bool] = None,
    source_phase: Optional[str] = None,
    source_step_id: Optional[str] = None,
    source_partition_id: Optional[str] = None,
    reason_code: Optional[str] = None,
) -> Dict[str, Any]:
    label_source = (
        str(container.get("label_source") or "").strip() or label_source_default
    )
    unknown_reason = container.get("unknown_reason_if_any")
    if unknown_reason is None:
        unknown_reason = container.get("unknown_reason")
    label_reason = (
        str(container.get("label_reason") or "").strip()
        or str(unknown_reason or "").strip()
        or label_reason_default
    )
    conflicting_values = container.get("conflicting_values_if_any")
    if conflicting_values is None:
        conflicting_values = container.get("conflicting_values")
    resolution_reason = container.get("resolution_reason_if_any")
    record_authoritative = bool(
        authoritative
        if authoritative is not None
        else provenance_kind not in NON_AUTHORITATIVE_PROVENANCE_KINDS
        and source_lane != "comparison"
    )
    return {
        "artifact_name": str(artifact_name),
        "field_path": str(field_path),
        "item_id": _container_item_id(container),
        "truth_label": str(truth_label),
        "previous_truth_label_if_changed": previous_truth_label_if_changed,
        "attempted_truth_label_if_any": attempted_truth_label_if_any,
        "label_source": label_source,
        "label_reason": label_reason,
        "evidence_refs": _evidence_refs_from_container(container),
        "conflicting_values_if_any": _safe_value(conflicting_values),
        "unknown_reason_if_any": _safe_value(unknown_reason),
        "resolution_reason_if_any": _safe_value(resolution_reason),
        "provenance_kind": str(provenance_kind),
        "source_lane": str(source_lane),
        "source_phase": source_phase,
        "source_step_id": source_step_id,
        "source_partition_id": source_partition_id,
        "reason_code": reason_code,
        "transition_action": str(transition_action),
        "authoritative": record_authoritative,
        "generated_at": str(generated_at),
    }


def _has_source_backed_resolution(
    *,
    old_label: str,
    attempted_label: Optional[str],
    candidate: Dict[str, Any],
) -> bool:
    if attempted_label != "OBSERVED":
        return False
    label_source = str(candidate.get("label_source") or "").strip().lower()
    if label_source not in _SOURCE_BACKED_LABEL_SOURCES:
        return False
    if not _evidence_refs_from_container(candidate):
        return False
    if old_label == "CONFLICTING" and not str(
        candidate.get("resolution_reason_if_any") or ""
    ).strip():
        return False
    return True


def _copy_missing_context(
    source: Dict[str, Any],
    target: Dict[str, Any],
    *,
    overwrite: bool = False,
) -> None:
    for key in _PRESERVED_CONTEXT_KEYS:
        if key not in source:
            if overwrite:
                target.pop(key, None)
            continue
        if overwrite or key not in target or target.get(key) in (None, "", []):
            target[key] = copy.deepcopy(source[key])


def _matching_items_by_id(items: List[Any]) -> Dict[str, Dict[str, Any]]:
    rows: Dict[str, Dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = _container_item_id(item)
        if item_id:
            rows[item_id] = item
    return rows


def _preserve_value(
    *,
    original: Any,
    candidate: Any,
    artifact_name: str,
    path: str,
    provenance_kind: str,
    source_lane: str,
    source_phase: str,
    source_step_id: str,
    source_partition_id: str,
    reason_code: str,
    generated_at: str,
    records: List[Dict[str, Any]],
) -> None:
    if isinstance(original, dict) and not isinstance(candidate, dict):
        _append_removed_protected_records(
            original=original,
            artifact_name=artifact_name,
            path=path,
            provenance_kind=provenance_kind,
            source_lane=source_lane,
            generated_at=generated_at,
            reason_code=reason_code,
            source_phase=source_phase,
            source_step_id=source_step_id,
            source_partition_id=source_partition_id,
            records=records,
        )
        return
    if not isinstance(original, dict) or not isinstance(candidate, dict):
        return

    old_label = normalize_truth_label(original.get("truth_label"))
    if old_label in PROTECTED_TRUTH_LABELS:
        attempted_label = normalize_truth_label(candidate.get("truth_label"))
        field_path = f"{path}.truth_label" if path else "truth_label"
        if attempted_label != old_label:
            if _has_source_backed_resolution(
                old_label=old_label,
                attempted_label=attempted_label,
                candidate=candidate,
            ):
                candidate.setdefault("previous_truth_label_if_changed", old_label)
                _copy_missing_context(original, candidate)
                records.append(
                    _record_for_container(
                        artifact_name=artifact_name,
                        field_path=field_path,
                        container=candidate,
                        truth_label=str(attempted_label),
                        provenance_kind=provenance_kind,
                        source_lane=source_lane,
                        generated_at=generated_at,
                        label_source_default="source_backed_transition",
                        label_reason_default=f"allowed_transition:{reason_code}",
                        transition_action="allowed_with_evidence",
                        attempted_truth_label_if_any=attempted_label,
                        previous_truth_label_if_changed=old_label,
                        source_phase=source_phase,
                        source_step_id=source_step_id,
                        source_partition_id=source_partition_id,
                        reason_code=reason_code,
                    )
                )
            else:
                candidate["truth_label"] = old_label
                _copy_missing_context(original, candidate, overwrite=True)
                transition_action = (
                    "blocked_protected_label_drop"
                    if attempted_label is None
                    else "blocked_protected_label_upgrade"
                )
                records.append(
                    _record_for_container(
                        artifact_name=artifact_name,
                        field_path=field_path,
                        container=candidate,
                        truth_label=old_label,
                        provenance_kind=provenance_kind,
                        source_lane=source_lane,
                        generated_at=generated_at,
                        label_source_default="protected_label_guard",
                        label_reason_default=f"blocked_transition:{reason_code}",
                        transition_action=transition_action,
                        attempted_truth_label_if_any=attempted_label,
                        source_phase=source_phase,
                        source_step_id=source_step_id,
                        source_partition_id=source_partition_id,
                        reason_code=reason_code,
                    )
                )
        else:
            _copy_missing_context(original, candidate)

    original_items = original.get("items")
    candidate_items = candidate.get("items")
    if isinstance(original_items, list) and isinstance(candidate_items, list):
        original_by_id = _matching_items_by_id(original_items)
        candidate_by_id = _matching_items_by_id(candidate_items)
        for item_id in sorted(set(original_by_id) - set(candidate_by_id)):
            original_index = original_items.index(original_by_id[item_id])
            _append_removed_protected_records(
                original=original_by_id[item_id],
                artifact_name=artifact_name,
                path=f"{path}.items[{original_index}]",
                provenance_kind=provenance_kind,
                source_lane=source_lane,
                generated_at=generated_at,
                reason_code=reason_code,
                source_phase=source_phase,
                source_step_id=source_step_id,
                source_partition_id=source_partition_id,
                records=records,
            )
        for item_id in sorted(set(original_by_id) & set(candidate_by_id)):
            candidate_index = candidate_items.index(candidate_by_id[item_id])
            _preserve_value(
                original=original_by_id[item_id],
                candidate=candidate_by_id[item_id],
                artifact_name=artifact_name,
                path=f"{path}.items[{candidate_index}]",
                provenance_kind=provenance_kind,
                source_lane=source_lane,
                source_phase=source_phase,
                source_step_id=source_step_id,
                source_partition_id=source_partition_id,
                reason_code=reason_code,
                generated_at=generated_at,
                records=records,
            )

    for key in sorted(set(original.keys()) - set(candidate.keys()), key=str):
        if key in {"items", "truth_label"}:
            continue
        next_path = f"{path}.{key}" if path else str(key)
        _append_removed_protected_records(
            original=original.get(key),
            artifact_name=artifact_name,
            path=next_path,
            provenance_kind=provenance_kind,
            source_lane=source_lane,
            generated_at=generated_at,
            reason_code=reason_code,
            source_phase=source_phase,
            source_step_id=source_step_id,
            source_partition_id=source_partition_id,
            records=records,
        )

    for key in sorted(set(original.keys()) & set(candidate.keys()), key=str):
        if key in {"items", "truth_label"}:
            continue
        next_path = f"{path}.{key}" if path else str(key)
        _preserve_value(
            original=original.get(key),
            candidate=candidate.get(key),
            artifact_name=artifact_name,
            path=next_path,
            provenance_kind=provenance_kind,
            source_lane=source_lane,
            source_phase=source_phase,
            source_step_id=source_step_id,
            source_partition_id=source_partition_id,
            reason_code=reason_code,
            generated_at=generated_at,
            records=records,
        )


def _append_removed_protected_records(
    *,
    original: Any,
    artifact_name: str,
    path: str,
    provenance_kind: str,
    source_lane: str,
    generated_at: str,
    reason_code: str,
    source_phase: str,
    source_step_id: str,
    source_partition_id: str,
    records: List[Dict[str, Any]],
) -> None:
    if not isinstance(original, dict):
        return
    for field_path, container in _iter_truth_label_containers(original, path):
        truth_label = normalize_truth_label(container.get("truth_label"))
        if truth_label not in PROTECTED_TRUTH_LABELS:
            continue
        records.append(
            _record_for_container(
                artifact_name=artifact_name,
                field_path=field_path,
                container=container,
                truth_label=truth_label,
                provenance_kind=provenance_kind,
                source_lane=source_lane,
                generated_at=generated_at,
                label_source_default="protected_label_guard",
                label_reason_default=f"artifact_substitution_preserved:{reason_code}",
                transition_action="protected_label_original_context_preserved",
                source_phase=source_phase,
                source_step_id=source_step_id,
                source_partition_id=source_partition_id,
                reason_code=reason_code,
            )
        )


def preserve_protected_truth_labels(
    *,
    original_artifacts: Sequence[Dict[str, Any]],
    candidate_artifacts: Sequence[Dict[str, Any]],
    provenance_kind: str,
    source_lane: Optional[str],
    source_phase: str,
    source_step_id: str,
    source_partition_id: str,
    reason_code: str,
    generated_at: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    original_by_name = {
        str(row.get("artifact_name") or "").strip(): row
        for row in original_artifacts
        if isinstance(row, dict) and str(row.get("artifact_name") or "").strip()
    }
    candidate_rows = [copy.deepcopy(row) for row in candidate_artifacts]
    records: List[Dict[str, Any]] = []
    lane = str(source_lane or "").strip() or _source_lane_for_kind(provenance_kind)
    for row in candidate_rows:
        if not isinstance(row, dict):
            continue
        artifact_name = str(row.get("artifact_name") or "").strip()
        original_row = original_by_name.get(artifact_name)
        if not isinstance(original_row, dict):
            continue
        _preserve_value(
            original=original_row.get("payload"),
            candidate=row.get("payload"),
            artifact_name=artifact_name,
            path="payload",
            provenance_kind=provenance_kind,
            source_lane=lane,
            source_phase=source_phase,
            source_step_id=source_step_id,
            source_partition_id=source_partition_id,
            reason_code=reason_code,
            generated_at=generated_at,
            records=records,
        )
    return candidate_rows, records


def collect_truth_label_records(
    *,
    artifacts: Sequence[Dict[str, Any]],
    field_records: Sequence[Dict[str, Any]],
    default_provenance_kind: str,
    default_source_lane: Optional[str],
    generated_at: str,
    label_source_default: str,
    label_reason_default: str,
    authoritative: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    lookup = _field_record_lookup(field_records)
    rows: List[Dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        artifact_name = str(artifact.get("artifact_name") or "").strip()
        if not artifact_name:
            continue
        for field_path, container in _iter_truth_label_containers(
            artifact.get("payload"), "payload"
        ):
            truth_label = normalize_truth_label(container.get("truth_label"))
            if not truth_label:
                continue
            provenance_kind, source_lane = lookup.get(
                (artifact_name, field_path),
                (
                    str(default_provenance_kind),
                    str(default_source_lane or "")
                    or _source_lane_for_kind(default_provenance_kind),
                ),
            )
            rows.append(
                _record_for_container(
                    artifact_name=artifact_name,
                    field_path=field_path,
                    container=container,
                    truth_label=truth_label,
                    provenance_kind=provenance_kind,
                    source_lane=source_lane,
                    generated_at=generated_at,
                    label_source_default=label_source_default,
                    label_reason_default=label_reason_default,
                    transition_action="preserved",
                    previous_truth_label_if_changed=container.get(
                        "previous_truth_label_if_changed"
                    ),
                    authoritative=authoritative,
                )
            )
    return rows


def _summary(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    labels = Counter(str(row.get("truth_label") or "") for row in records)
    kinds = Counter(str(row.get("provenance_kind") or "") for row in records)
    actions = Counter(str(row.get("transition_action") or "") for row in records)
    protected_total = sum(
        1 for row in records if row.get("truth_label") in PROTECTED_TRUTH_LABELS
    )
    return {
        "records_total": len(records),
        "protected_records_total": protected_total,
        "labels": dict(sorted(labels.items())),
        "provenance_kinds": dict(sorted(kinds.items())),
        "transition_actions": dict(sorted(actions.items())),
    }


def build_truth_label_preservation_payload(
    *,
    artifacts: Sequence[Dict[str, Any]],
    field_records: Sequence[Dict[str, Any]],
    transition_records: Sequence[Dict[str, Any]],
    generated_at: str,
    default_provenance_kind: str = "primary_observed",
    default_source_lane: Optional[str] = "primary",
    label_source_default: str = "artifact_payload",
    label_reason_default: str = "truth_label_present",
    authoritative: Optional[bool] = None,
) -> Dict[str, Any]:
    records = collect_truth_label_records(
        artifacts=artifacts,
        field_records=field_records,
        default_provenance_kind=default_provenance_kind,
        default_source_lane=default_source_lane,
        generated_at=generated_at,
        label_source_default=label_source_default,
        label_reason_default=label_reason_default,
        authoritative=authoritative,
    )
    records.extend([dict(row) for row in transition_records if isinstance(row, dict)])
    records.sort(
        key=lambda row: (
            str(row.get("artifact_name") or ""),
            str(row.get("field_path") or ""),
            str(row.get("truth_label") or ""),
            str(row.get("provenance_kind") or ""),
            str(row.get("transition_action") or ""),
            str(row.get("attempted_truth_label_if_any") or ""),
        )
    )
    return {
        "schema_version": TRUTH_LABEL_SCHEMA_VERSION,
        "generated_at": str(generated_at),
        "protected_labels": sorted(PROTECTED_TRUTH_LABELS),
        "record_required_fields": list(TRUTH_LABEL_RECORD_REQUIRED_FIELDS),
        "records": records,
        "summary": _summary(records),
    }


def build_truth_label_rollup_payload(
    *,
    phase: str,
    step_id: str,
    records: Sequence[Dict[str, Any]],
    generated_at: str,
) -> Dict[str, Any]:
    rows = [dict(row) for row in records if isinstance(row, dict)]
    rows.sort(
        key=lambda row: (
            str(row.get("source_partition_id") or ""),
            str(row.get("artifact_name") or ""),
            str(row.get("field_path") or ""),
            str(row.get("truth_label") or ""),
            str(row.get("transition_action") or ""),
        )
    )
    return {
        "schema_version": TRUTH_LABEL_SCHEMA_VERSION,
        "phase": str(phase),
        "step_id": str(step_id),
        "generated_at": str(generated_at),
        "protected_labels": sorted(PROTECTED_TRUTH_LABELS),
        "record_required_fields": list(TRUTH_LABEL_RECORD_REQUIRED_FIELDS),
        "records": rows,
        "summary": _summary(rows),
    }


def validate_truth_label_payload(payload: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if payload.get("schema_version") != TRUTH_LABEL_SCHEMA_VERSION:
        errors.append("schema_version_mismatch")
    records = payload.get("records")
    if not isinstance(records, list):
        errors.append("records_not_list")
        return errors
    for idx, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record_{idx}_not_object")
            continue
        missing = set(TRUTH_LABEL_RECORD_REQUIRED_FIELDS) - set(record.keys())
        if missing:
            errors.append(f"record_{idx}_missing:{','.join(sorted(missing))}")
        label = normalize_truth_label(record.get("truth_label"))
        if not label:
            errors.append(f"record_{idx}_invalid_truth_label")
        if (
            record.get("transition_action") == "blocked_protected_label_upgrade"
            and record.get("attempted_truth_label_if_any") is None
        ):
            errors.append(f"record_{idx}_blocked_transition_missing_attempt")
        serialized = json.dumps(record, sort_keys=True, default=str)
        if _SECRET_SHAPED_RE.search(serialized):
            errors.append(f"record_{idx}_contains_secret_shaped_value")
    return errors
