from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .route_identity import RouteIdentityRecord

IDENTICAL_CONTROL_SIGNATURE = "IDENTICAL_CONTROL_SIGNATURE"
CANDIDATE_CONTROL_COLLAPSE = "CANDIDATE_CONTROL_COLLAPSE"
UNSTABLE_EFFECTIVE_SIGNATURE = "UNSTABLE_EFFECTIVE_SIGNATURE"
MISSING_ROUTE_TELEMETRY = "MISSING_ROUTE_TELEMETRY"
MALFORMED_ROUTE_TELEMETRY = "MALFORMED_ROUTE_TELEMETRY"
INSUFFICIENT_PREFLIGHT_EVIDENCE = "INSUFFICIENT_PREFLIGHT_EVIDENCE"


@dataclass(frozen=True)
class AdmissibilityRouteRow:
    route_id: str
    cohort: str
    case_id: str
    case_attempt_ids: list[str]
    declared_route_id: str
    selected_route_identity: dict[str, Any]
    effective_route_signature_hashes: list[str]
    effective_route_signature: dict[str, list[str]] | None
    route_signature_source_refs: list[str]
    admissibility_status: str
    admissibility_blocker_codes: list[str]
    admissibility_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "cohort": self.cohort,
            "case_id": self.case_id,
            "case_attempt_ids": self.case_attempt_ids,
            "declared_route_id": self.declared_route_id,
            "selected_route_identity": self.selected_route_identity,
            "effective_route_signature_hashes": self.effective_route_signature_hashes,
            "effective_route_signature": self.effective_route_signature,
            "route_signature_source_refs": self.route_signature_source_refs,
            "admissibility_status": self.admissibility_status,
            "admissibility_blocker_codes": self.admissibility_blocker_codes,
            "admissibility_notes": self.admissibility_notes,
        }


def evaluate_admissibility(
    *,
    benchmark_run_ids: list[str],
    route_identities: list[RouteIdentityRecord],
    intended_routes: list[dict[str, Any]],
    route_errors: dict[tuple[str, str], list[dict[str, str]]] | None = None,
    required_repeat_count: int = 1,
) -> dict[str, Any]:
    route_groups: dict[tuple[str, str], list[RouteIdentityRecord]] = {}
    for record in route_identities:
        route_groups.setdefault((record.case_id, record.declared_route_id), []).append(record)

    route_rows: list[AdmissibilityRouteRow] = []
    overall_blockers: set[str] = set()
    comparisons: list[dict[str, Any]] = []
    intended_pairs: dict[tuple[str, str], dict[str, Any]] = {
        (str(item["case_id"]), str(item["route_id"])): item for item in intended_routes
    }
    route_errors = route_errors or {}

    for key, intended in sorted(intended_pairs.items()):
        records = route_groups.get(key, [])
        blockers: list[str] = []
        notes: list[str] = []
        signature_hashes = sorted({record.effective_route_signature_hash for record in records})
        selected_identity = records[0].selected_route_identity if records else {
            "declared_route_id": intended["route_id"],
            "surface_class": intended.get("surface_class"),
            "provider_name": intended.get("provider_name"),
            "model_key": intended.get("model_key"),
            "provider_model_id": intended.get("provider_model_id"),
        }
        effective_signature = records[0].effective_route_signature if records else None
        source_refs: list[str] = []
        for record in records:
            source_refs.extend(ref for ref in record.route_signature_source_refs if ref not in source_refs)
        for issue in route_errors.get(key, []):
            blocker = str(issue["blocker_code"])
            if blocker not in blockers:
                blockers.append(blocker)
            notes.append(str(issue["message"]))
        if len(records) < required_repeat_count:
            blockers.append(INSUFFICIENT_PREFLIGHT_EVIDENCE)
            notes.append(
                f"required {required_repeat_count} preflight evidence rows for {intended['route_id']} but found {len(records)}"
            )
        if len(signature_hashes) > 1:
            blockers.append(UNSTABLE_EFFECTIVE_SIGNATURE)
            notes.append(f"effective route signature changed across preflight runs: {signature_hashes}")
        status = "blocked" if blockers else "admissible"
        overall_blockers.update(blockers)
        route_rows.append(
            AdmissibilityRouteRow(
                route_id=str(intended["route_id"]),
                cohort=str(intended["cohort"]),
                case_id=str(intended["case_id"]),
                case_attempt_ids=[record.case_attempt_id for record in records],
                declared_route_id=str(intended["route_id"]),
                selected_route_identity=selected_identity,
                effective_route_signature_hashes=signature_hashes,
                effective_route_signature=effective_signature,
                route_signature_source_refs=source_refs,
                admissibility_status=status,
                admissibility_blocker_codes=blockers,
                admissibility_notes=notes,
            )
        )

    control_rows = [row for row in route_rows if row.cohort == "control"]
    for index, left in enumerate(control_rows):
        for right in control_rows[index + 1 :]:
            if left.case_id != right.case_id:
                continue
            equal = bool(left.effective_route_signature_hashes) and left.effective_route_signature_hashes == right.effective_route_signature_hashes
            comparisons.append(
                {
                    "comparison_type": "control_pair",
                    "case_id": left.case_id,
                    "left_route_id": left.route_id,
                    "right_route_id": right.route_id,
                    "left_signature_hashes": left.effective_route_signature_hashes,
                    "right_signature_hashes": right.effective_route_signature_hashes,
                    "signatures_equal": equal,
                }
            )
            if equal:
                overall_blockers.add(IDENTICAL_CONTROL_SIGNATURE)

    candidate_rows = [row for row in route_rows if row.cohort not in {"control"}]
    for candidate in candidate_rows:
        for control in control_rows:
            if candidate.case_id != control.case_id:
                continue
            equal = bool(candidate.effective_route_signature_hashes) and candidate.effective_route_signature_hashes == control.effective_route_signature_hashes
            comparisons.append(
                {
                    "comparison_type": "candidate_vs_control",
                    "case_id": candidate.case_id,
                    "candidate_route_id": candidate.route_id,
                    "control_route_id": control.route_id,
                    "candidate_signature_hashes": candidate.effective_route_signature_hashes,
                    "control_signature_hashes": control.effective_route_signature_hashes,
                    "signatures_equal": equal,
                }
            )
            if equal:
                overall_blockers.add(CANDIDATE_CONTROL_COLLAPSE)

    status = "blocked" if overall_blockers else "admissible"
    invalidated = status == "blocked"
    return {
        "analysis_version": "route_identity_admissibility_v1",
        "benchmark_run_ids": benchmark_run_ids,
        "required_repeat_count": required_repeat_count,
        "status": status,
        "campaign_state": "invalidated" if invalidated else "admissible",
        "admissibility_blocker_codes": sorted(overall_blockers),
        "routes": [row.to_dict() for row in route_rows],
        "comparisons": comparisons,
        "notes": [
            "Declared route identity is insufficient on its own; admissibility is based on effective route signatures derived from runtime telemetry."
        ],
    }
