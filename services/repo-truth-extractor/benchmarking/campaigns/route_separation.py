from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .admissibility import MALFORMED_ROUTE_TELEMETRY, MISSING_ROUTE_TELEMETRY
from .route_identity import RouteIdentityRecord

DECLARED_ROUTE_ALIASING = "DECLARED_ROUTE_ALIASING"
SELECTION_LAYER_OVERRIDE = "SELECTION_LAYER_OVERRIDE"
FALLBACK_CONVERGENCE = "FALLBACK_CONVERGENCE"
TELEMETRY_UNDER_RESOLUTION = "TELEMETRY_UNDER_RESOLUTION"
CASE_FAMILY_SPECIFIC_CONVERGENCE = "CASE_FAMILY_SPECIFIC_CONVERGENCE"
UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class RouteTruthRow:
    route_id: str
    cohort: str
    case_id: str
    surface_class: str
    declared_provider_name: str
    declared_model_key: str
    declared_provider_model_id: str
    declared_route_pin: str
    selected_route_identity: dict[str, Any]
    effective_route_signature: dict[str, list[str]] | None
    effective_route_signature_hash: str | None
    route_signature_source_refs: list[str]
    meaningfully_distinct_for_case_family: bool
    collapse_cause_codes: list[str]
    comparison_route_ids: list[str]
    comparison_signature_hashes: list[str]
    blocker_codes: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "cohort": self.cohort,
            "case_id": self.case_id,
            "surface_class": self.surface_class,
            "declared_provider_name": self.declared_provider_name,
            "declared_model_key": self.declared_model_key,
            "declared_provider_model_id": self.declared_provider_model_id,
            "declared_route_pin": self.declared_route_pin,
            "selected_route_identity": self.selected_route_identity,
            "effective_route_signature": self.effective_route_signature,
            "effective_route_signature_hash": self.effective_route_signature_hash,
            "route_signature_source_refs": self.route_signature_source_refs,
            "meaningfully_distinct_for_case_family": self.meaningfully_distinct_for_case_family,
            "collapse_cause_codes": self.collapse_cause_codes,
            "comparison_route_ids": self.comparison_route_ids,
            "comparison_signature_hashes": self.comparison_signature_hashes,
            "blocker_codes": self.blocker_codes,
            "notes": self.notes,
        }


def _normalized_selected_route(selected_route_identity: dict[str, Any]) -> str:
    provider = str(selected_route_identity.get("provider_name") or "").strip().lower()
    model = str(selected_route_identity.get("provider_model_id") or "").strip()
    if provider and model:
        return f"{provider}/{model}"
    representative = selected_route_identity.get("representative_phase_route")
    if isinstance(representative, dict):
        rep_provider = str(representative.get("provider") or "").strip().lower()
        rep_model = str(representative.get("model_id") or "").strip()
        if rep_provider and rep_model:
            return f"{rep_provider}/{rep_model}"
    return ""


def _normalized_representative_phase_route(selected_route_identity: dict[str, Any]) -> str:
    representative = selected_route_identity.get("representative_phase_route")
    if not isinstance(representative, dict):
        return ""
    rep_provider = str(representative.get("provider") or "").strip().lower()
    rep_model = str(representative.get("model_id") or "").strip()
    if rep_provider and rep_model:
        return f"{rep_provider}/{rep_model}"
    return ""


def _cause_codes_for_row(
    *,
    intended: dict[str, Any],
    record: RouteIdentityRecord | None,
    blocker_codes: list[str],
    comparison_rows: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    causes: list[str] = []
    notes: list[str] = []
    if any(code in {MISSING_ROUTE_TELEMETRY, MALFORMED_ROUTE_TELEMETRY} for code in blocker_codes):
        causes.append(TELEMETRY_UNDER_RESOLUTION)
        notes.append("Runtime telemetry required to derive an effective route signature was missing or malformed.")
    if record is None:
        if not causes:
            causes.append(UNRESOLVED)
            notes.append("No route identity record could be derived for this intended route.")
        return sorted(set(causes)), notes

    selected_route = _normalized_selected_route(record.selected_route_identity)
    representative_route = _normalized_representative_phase_route(record.selected_route_identity)
    declared_provider = str(intended.get("provider_name") or "").strip().lower()
    declared_model = str(intended.get("provider_model_id") or "").strip()
    declared_route = f"{declared_provider}/{declared_model}" if declared_provider and declared_model else ""
    declared_pin = str(record.selected_route_identity.get("route_pin") or "").strip()

    if representative_route and representative_route not in {declared_route, declared_pin}:
        causes.append(SELECTION_LAYER_OVERRIDE)
        notes.append(
            "Representative phase routing differs from the declared route intent, indicating step-level runtime selection overrides launch-time route identity."
        )
    elif selected_route and selected_route not in {declared_route, declared_pin}:
        causes.append(SELECTION_LAYER_OVERRIDE)
        notes.append(
            "Selected route identity differs from the declared route intent before effective signature comparison."
        )

    if comparison_rows:
        causes.append(CASE_FAMILY_SPECIFIC_CONVERGENCE)
        notes.append(
            "This case family converged to the same effective route signature as another declared route under the active runtime."
        )

    if not causes:
        causes.append(UNRESOLVED)
        notes.append("No stronger collapse cause could be established from the current runtime evidence.")
    return sorted(set(causes)), notes


def build_route_identity_truth_table(
    *,
    intended_routes: list[dict[str, Any]],
    route_identities: list[RouteIdentityRecord],
    route_errors: dict[tuple[str, str], list[dict[str, str]]] | None,
    admissibility: dict[str, Any],
) -> list[dict[str, Any]]:
    route_errors = route_errors or {}
    record_by_key = {(record.case_id, record.declared_route_id): record for record in route_identities}
    seen_keys: set[tuple[str, str]] = set()
    comparison_map: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in admissibility.get("comparisons", []):
        if not isinstance(row, dict):
            continue
        case_id = str(row.get("case_id") or "")
        if str(row.get("comparison_type")) == "control_pair" and bool(row.get("signatures_equal")):
            left = str(row.get("left_route_id") or "")
            right = str(row.get("right_route_id") or "")
            comparison_map.setdefault((case_id, left), []).append(row)
            comparison_map.setdefault((case_id, right), []).append(row)
        if str(row.get("comparison_type")) == "candidate_vs_control" and bool(row.get("signatures_equal")):
            candidate = str(row.get("candidate_route_id") or "")
            control = str(row.get("control_route_id") or "")
            comparison_map.setdefault((case_id, candidate), []).append(row)
            comparison_map.setdefault((case_id, control), []).append(row)

    table: list[dict[str, Any]] = []
    for intended in sorted(intended_routes, key=lambda item: (str(item["case_id"]), str(item["route_id"]))):
        case_id = str(intended["case_id"])
        route_id = str(intended["route_id"])
        if (case_id, route_id) in seen_keys:
            continue
        seen_keys.add((case_id, route_id))
        record = record_by_key.get((case_id, route_id))
        blocker_codes = [str(issue["blocker_code"]) for issue in route_errors.get((case_id, route_id), [])]
        comparison_rows = comparison_map.get((case_id, route_id), [])
        comparison_route_ids = sorted(
            {
                str(item.get("left_route_id") or item.get("control_route_id") or "")
                for item in comparison_rows
            }
            | {
                str(item.get("right_route_id") or item.get("candidate_route_id") or "")
                for item in comparison_rows
            }
            - {""}
            - {route_id}
        )
        comparison_hashes = sorted(
            {
                *(str(hash_value) for item in comparison_rows for hash_value in item.get("left_signature_hashes", [])),
                *(str(hash_value) for item in comparison_rows for hash_value in item.get("right_signature_hashes", [])),
                *(str(hash_value) for item in comparison_rows for hash_value in item.get("candidate_signature_hashes", [])),
                *(str(hash_value) for item in comparison_rows for hash_value in item.get("control_signature_hashes", [])),
            }
        )
        causes, notes = _cause_codes_for_row(
            intended=intended,
            record=record,
            blocker_codes=blocker_codes,
            comparison_rows=comparison_rows,
        )
        row = RouteTruthRow(
            route_id=route_id,
            cohort=str(intended["cohort"]),
            case_id=case_id,
            surface_class=str(intended.get("surface_class") or ""),
            declared_provider_name=str(intended.get("provider_name") or ""),
            declared_model_key=str(intended.get("model_key") or ""),
            declared_provider_model_id=str(intended.get("provider_model_id") or ""),
            declared_route_pin=(
                str(record.selected_route_identity.get("route_pin") or "")
                if record is not None
                else ""
            ),
            selected_route_identity=record.selected_route_identity if record is not None else {},
            effective_route_signature=record.effective_route_signature if record is not None else None,
            effective_route_signature_hash=record.effective_route_signature_hash if record is not None else None,
            route_signature_source_refs=record.route_signature_source_refs if record is not None else [],
            meaningfully_distinct_for_case_family=(
                record is not None and not bool(comparison_rows) and not blocker_codes
            ),
            collapse_cause_codes=causes,
            comparison_route_ids=comparison_route_ids,
            comparison_signature_hashes=comparison_hashes,
            blocker_codes=blocker_codes,
            notes=notes,
        )
        table.append(row.to_dict())
    return table


def classify_route_collapse(table: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for row in table if not bool(row.get("meaningfully_distinct_for_case_family"))]
    cause_counts: dict[str, int] = {}
    for row in rows:
        for code in row.get("collapse_cause_codes", []):
            cause_counts[str(code)] = cause_counts.get(str(code), 0) + 1
    return {
        "status": "collapse_observed" if rows else "no_collapse_detected",
        "cause_counts": cause_counts,
        "rows": rows,
    }


def build_corrected_control_strategy(
    *,
    manifest: dict[str, Any],
    truth_table: list[dict[str, Any]],
    admissibility: dict[str, Any],
) -> dict[str, Any]:
    strict_rows = [
        row
        for row in truth_table
        if str(row.get("case_id")) == "strict_extract_conflicting_evidence_v1"
    ]
    live_rows = [row for row in strict_rows if str(row.get("surface_class")) != "local_or_open_weight"]
    collapse_rows = [
        row
        for row in live_rows
        if not bool(row.get("meaningfully_distinct_for_case_family"))
    ]
    unique_live_hashes = {
        str(row.get("effective_route_signature_hash") or "")
        for row in live_rows
        if str(row.get("effective_route_signature_hash") or "")
    }
    can_restart = bool(live_rows) and not collapse_rows and len(unique_live_hashes) >= 2
    if can_restart:
        return {
            "status": "admissible_control_strategy",
            "strategy_type": "valid_control_pair",
            "campaign_id": manifest.get("campaign_id"),
            "target_case_family": "strict_extract_conflicting_evidence_v1",
            "admitted_route_ids": [str(row["route_id"]) for row in live_rows],
            "blocked_route_ids": [],
            "notes": [
                "Live routes are meaningfully distinct for the target case family under the current runtime evidence."
            ],
            "r1_restart_truthful": True,
        }
    blocked_route_ids = [str(row["route_id"]) for row in collapse_rows] or [str(row["route_id"]) for row in live_rows]
    return {
        "status": "blocked_lane_verdict",
        "strategy_type": "blocked_lane_verdict",
        "campaign_id": manifest.get("campaign_id"),
        "target_case_family": "strict_extract_conflicting_evidence_v1",
        "admitted_route_ids": [],
        "blocked_route_ids": sorted(set(blocked_route_ids)),
        "required_runtime_or_policy_change": (
            "A truthful route-level strict extraction contest requires a case family where declared route identity controls step routing, "
            "or a runtime change that allows campaign-selected routes to own JSON-managed step selection."
        ),
        "notes": [
            "Under current v5 runtime routing, strict_extract_conflicting_evidence_v1 is case-family-specifically converged to model_map step routes.",
            "The corrected strategy is to keep this lane blocked for route-level contesting until runtime route separation changes or a different case family is selected.",
        ],
        "admissibility_blocker_codes": list(admissibility.get("admissibility_blocker_codes", [])),
        "r1_restart_truthful": False,
    }


def render_route_collapse_diagnosis(
    *,
    truth_table: list[dict[str, Any]],
    admissibility: dict[str, Any],
) -> str:
    live_rows = [row for row in truth_table if str(row.get("surface_class")) != "local_or_open_weight"]
    collapse_rows = [row for row in live_rows if not bool(row.get("meaningfully_distinct_for_case_family"))]
    lines = [
        "# Route Collapse Diagnosis",
        "",
        "Observed runtime truth:",
        "- Declared route identity is preserved in benchmark metadata, but it is not authoritative for JSON-managed A-phase routing.",
        "- `run_extraction_v5.py` resolves JSON-managed step routes from `promptsets/v4/model_map.yaml` via `resolve_effective_step_route(...)` before non-contract route overrides matter.",
        "- The emitted route telemetry therefore reflects step-level contract routing, not launch-time candidate intent, for the investigated strict extraction lane.",
        "",
        "Diagnosis:",
    ]
    if collapse_rows:
        lines.extend(
            [
                "- The investigated strict extraction case family converged multiple declared routes onto the same effective step-routing signature.",
                "- This is selection-layer override plus case-family-specific convergence, not a benchmark storage/reporting artifact.",
                f"- Active admissibility blocker codes: {', '.join(admissibility.get('admissibility_blocker_codes', [])) or 'none'}",
            ]
        )
    else:
        lines.append("- No route collapse was detected in the bounded evidence set.")
    return "\n".join(lines) + "\n"


def render_r1b_decision_memo(
    *,
    truth_table: list[dict[str, Any]],
    classification: dict[str, Any],
    strategy: dict[str, Any],
) -> str:
    cause_counts = classification.get("cause_counts", {})
    lines = [
        "# R1B Decision Memo",
        "",
        "1. What caused the control/candidate collapse?",
        "- JSON-managed A-phase steps are resolved from `promptsets/v4/model_map.yaml` by the runtime before declared campaign route intent can own the step.",
        f"- Classified causes: {', '.join(sorted(cause_counts)) or 'none observed'}",
        "",
        "2. Is the collapse lane-specific or global?",
        "- The current evidence supports a lane-specific verdict for `strict_extract_conflicting_evidence_v1` / A-phase strict extraction.",
        "- This packet does not claim that all runtime-v5 case families are globally collapsed.",
        "",
        "3. Is there a valid distinct control set now?",
        f"- {('Yes' if strategy.get('r1_restart_truthful') else 'No')}.",
        "",
        "4. Can R1 be restarted truthfully?",
        f"- {('Yes' if strategy.get('r1_restart_truthful') else 'No')}.",
        "",
        "5. If yes, with what exact cohort and lane scope?",
    ]
    if strategy.get("r1_restart_truthful"):
        lines.append(f"- Admitted routes: {', '.join(strategy.get('admitted_route_ids', []))}")
    else:
        lines.append("- No truthful strict extraction route-level cohort exists under the active runtime for this lane.")
    lines.extend(
        [
            "",
            "6. If no, what runtime or policy change is required first?",
            f"- {strategy.get('required_runtime_or_policy_change', 'None.')}",
        ]
    )
    return "\n".join(lines) + "\n"
