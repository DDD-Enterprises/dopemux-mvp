from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

from output_safety import sanitize_payload_for_output, sanitize_text_for_output

from lib.proof_contract import (
    build_conformance_report,
    classify_artifact_authority_order,
)


RISK_DASHBOARD_JSON_FILENAME = "RTE_RISK_DASHBOARD.json"
RISK_DASHBOARD_MD_FILENAME = "RTE_RISK_DASHBOARD.md"

STATUS_VALUES = (
    "PASS_STATIC",
    "PASS_WITH_RISK",
    "STATIC_ONLY",
    "LIVE_VALIDATION_REQUIRED",
    "MISSING",
    "UNKNOWN",
    "BLOCKED",
    "NOT_APPLICABLE",
    "ACCEPTED_WITH_RISK",
)

REQUIRED_RISK_ITEM_IDS = (
    "LIVE_GATE",
    "PROVIDER_PAYLOAD_REDACTION",
    "FAILED_SIDECARS",
    "PRESCAN_STALENESS",
    "PRESCAN_INFLUENCE",
    "PROVENANCE_FIELDS",
    "TRUTH_LABELS",
    "PROVIDER_METADATA",
    "BATCH_STATIC",
    "LIVE_VALIDATION_PLAN",
    "PROOF_CONTRACT",
    "PASS1_IDENTITY",
    "GENERATED_ARTIFACT_AUTHORITY",
)

DEFAULT_PROVIDER_LANES = (
    "direct_xai",
    "openrouter_xai",
    "openai_compatible",
    "gemini_compatible",
)

PACKET_BASIS_ROOTS = {
    "LIVE_GATE": ("rte-pkt-01-live-gate",),
    "PROVIDER_PAYLOAD_REDACTION": ("rte-pkt-02-payload-redaction",),
    "FAILED_SIDECARS": ("rte-pkt-15-failed-sidecars",),
    "PRESCAN_STALENESS": ("rte-pkt-03-prescan-stale",),
    "PRESCAN_INFLUENCE": ("rte-pkt-04-prescan-influence",),
    "PROVENANCE_FIELDS": ("rte-pkt-05-provenance-fields",),
    "TRUTH_LABELS": ("rte-pkt-06-truth-labels",),
    "PROVIDER_METADATA": ("rte-pkt-07-xai-metadata",),
    "BATCH_STATIC": ("rte-pkt-08-xai-batch-static",),
    "LIVE_VALIDATION_PLAN": ("rte-pkt-09-live-validation-plan",),
    "PROOF_CONTRACT": ("rte-pkt-10-proof-contract",),
}


def _now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value, key=str)
    return [value]


def _as_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _bool_input(inputs: Mapping[str, Any], key: str, default: bool = False) -> bool:
    value = inputs.get(key)
    if value is None:
        return default
    return bool(value)


def _first_string(*values: Any) -> Optional[str]:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _status(value: Any, default: str = "UNKNOWN") -> str:
    token = str(value or "").strip().upper()
    if token in STATUS_VALUES:
        return token
    return default


def _item(item_id: str, status: str, **fields: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"id": item_id, "status": _status(status)}
    payload.update(fields)
    return payload


def _risk_items_by_id(items: Sequence[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_id: Dict[str, Dict[str, Any]] = {}
    for item in items:
        item_id = str(item.get("id") or "")
        if item_id:
            by_id[item_id] = dict(item)
    return by_id


def _proof_contract_status(report: Mapping[str, Any]) -> tuple[str, str]:
    overall = str(report.get("overall_status") or "").strip().upper()
    if overall == "SATISFIED":
        return "satisfied", "PASS_STATIC"
    if overall == "PARTIAL":
        return "partial", "PASS_WITH_RISK"
    if overall == "MISSING":
        return "missing", "MISSING"
    if overall == "NOT_APPLICABLE":
        return "not_applicable", "NOT_APPLICABLE"
    return "unknown", "UNKNOWN"


def _pass1_status(report: Mapping[str, Any]) -> tuple[str, str]:
    identity = _as_dict(report.get("exact_pass1_identity"))
    token = str(identity.get("status") or "").strip().upper()
    if token == "SATISFIED":
        return "known", "PASS_STATIC"
    return "unknown", "UNKNOWN"


def _relative_paths(root: Optional[Path], paths: Iterable[Path]) -> list[str]:
    rows: list[str] = []
    for path in paths:
        try:
            rows.append(str(path.relative_to(root)) if root is not None else str(path))
        except ValueError:
            rows.append(str(path))
    return sorted(rows)


def _find_downloaded_jsonl(run_root: Optional[Path]) -> list[str]:
    if run_root is None or not run_root.exists():
        return []
    candidates: list[Path] = []
    for path in run_root.rglob("*.jsonl"):
        rel = str(path.relative_to(run_root)).lower()
        if "download" in rel or "retriev" in rel or "batch" in rel:
            candidates.append(path)
    return _relative_paths(run_root, candidates)


def _find_live_validation_artifacts(run_root: Optional[Path]) -> list[str]:
    if run_root is None or not run_root.exists():
        return []
    names = {
        "LIVE_VALIDATION_RESULT.json",
        "RTE_LIVE_VALIDATION_RESULT.json",
        "PROVIDER_LIVE_VALIDATION.json",
        "BATCH_LIVE_VALIDATION.json",
    }
    paths = [
        path
        for path in run_root.rglob("*.json")
        if path.name in names or path.name.startswith("LIVE_VALIDATION_")
    ]
    return _relative_paths(run_root, paths)


def _collect_packet_basis(repo_root: Optional[Path]) -> Dict[str, bool]:
    if repo_root is None:
        return {item_id: False for item_id in PACKET_BASIS_ROOTS}
    out_root = repo_root / "out"
    return {
        item_id: any((out_root / dirname).exists() for dirname in dirnames)
        for item_id, dirnames in PACKET_BASIS_ROOTS.items()
    }


def collect_rte_risk_dashboard_inputs(
    *,
    run_id: Optional[str],
    run_root: Path,
    repo_root: Optional[Path] = None,
    git_sha: Optional[str] = None,
    run_dashboard: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    proof_path = run_root / "PROOF_PACK.json"
    manifest_path = run_root / "RUN_MANIFEST.json"
    proof_payload = _load_json(proof_path)
    manifest_payload = _load_json(manifest_path)
    proof_source = proof_path if proof_payload else manifest_path
    proof_contract_payload = proof_payload or manifest_payload

    proof_report = (
        build_conformance_report(
            proof_contract_payload,
            artifact_path=str(proof_source),
        )
        if proof_contract_payload
        else {}
    )

    downloaded_jsonl = _find_downloaded_jsonl(run_root)
    live_validation_artifacts = _find_live_validation_artifacts(run_root)

    return {
        "run_id_if_available": run_id,
        "repo_root_if_available": str(repo_root.resolve()) if repo_root else None,
        "git_sha_if_available": git_sha,
        "run_root_if_available": str(run_root.resolve()),
        "run_dashboard": dict(run_dashboard or {}),
        "proof_contract_report": proof_report,
        "proof_contract_artifact_path": str(proof_source.resolve())
        if proof_contract_payload
        else None,
        "downloaded_jsonl_files": downloaded_jsonl,
        "live_validation_artifacts": live_validation_artifacts,
        "accepted_packet_basis": _collect_packet_basis(repo_root),
        "live_validation_authorized": False,
        "live_provider_validated": False,
        "live_batch_validated": False,
    }


def build_rte_risk_dashboard(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    proof_report = _as_dict(inputs.get("proof_contract_report"))
    proof_contract_status, proof_risk_status = _proof_contract_status(proof_report)
    pass1_identity, pass1_risk_status = _pass1_status(proof_report)

    downloaded_jsonl = [
        str(path) for path in _as_list(inputs.get("downloaded_jsonl_files"))
    ]
    downloaded_jsonl_status = "FOUND" if downloaded_jsonl else "MISSING"
    accepted_packet_basis = _as_dict(inputs.get("accepted_packet_basis"))

    def packet_basis(item_id: str) -> bool:
        return bool(accepted_packet_basis.get(item_id, False))

    live_validation_artifacts = [
        str(path) for path in _as_list(inputs.get("live_validation_artifacts"))
    ]
    live_validation_authorized = _bool_input(
        inputs, "live_validation_authorized", default=False
    )
    live_validation_plan_exists = _bool_input(
        inputs,
        "live_validation_plan_exists",
        default=packet_basis("LIVE_VALIDATION_PLAN"),
    )
    live_provider_validated = _bool_input(inputs, "live_provider_validated", default=False)
    live_batch_validated = _bool_input(inputs, "live_batch_validated", default=False)

    provider_lanes = _as_dict(inputs.get("provider_lanes"))
    if not provider_lanes:
        provider_lanes = {
            lane: "LIVE_VALIDATION_REQUIRED" for lane in DEFAULT_PROVIDER_LANES
        }
    provider_lanes = {
        str(lane): _status(status, "LIVE_VALIDATION_REQUIRED")
        for lane, status in provider_lanes.items()
    }

    provider_call_status = (
        "PASS_STATIC"
        if live_provider_validated
        else (
            "LIVE_VALIDATION_REQUIRED"
            if any(status == "LIVE_VALIDATION_REQUIRED" for status in provider_lanes.values())
            else "UNKNOWN"
        )
    )
    batch_operation_status = (
        "PASS_STATIC" if live_batch_validated else "LIVE_VALIDATION_REQUIRED"
    )
    live_validation_status = (
        "PASS_STATIC"
        if live_validation_artifacts and live_validation_authorized
        else ("BLOCKED" if not live_validation_authorized else "LIVE_VALIDATION_REQUIRED")
    )

    artifact_authority_rows = classify_artifact_authority_order(
        [
            "services/repo-truth-extractor/run_extraction_v5.py",
            "telemetry/RUN_DASHBOARD.json",
            "telemetry/RTE_RISK_DASHBOARD.json",
            "out/rte-pkt-11-risk-dashboard/RTE-PKT-11_MANIFEST.json",
        ]
    )

    risk_items = [
        _item(
            "LIVE_GATE",
            "STATIC_ONLY",
            evidence_basis="local runtime/proof inputs",
            live_validation_required_boolean=True,
            live_validation_artifacts=live_validation_artifacts,
            live_use_boundary="static proof only; production live readiness not claimed",
        ),
        _item(
            "PROVIDER_PAYLOAD_REDACTION",
            "PASS_STATIC" if packet_basis("PROVIDER_PAYLOAD_REDACTION") else "UNKNOWN",
            evidence_basis="static packet/runtime redaction proof when available",
            coverage="provider-bound payload/error summaries only; no raw provider payload text",
            remaining_unknowns=(
                []
                if packet_basis("PROVIDER_PAYLOAD_REDACTION")
                else ["provider payload redaction proof not observed in current inputs"]
            ),
        ),
        _item(
            "FAILED_SIDECARS",
            "PASS_WITH_RISK" if packet_basis("FAILED_SIDECARS") else "UNKNOWN",
            evidence_basis="static failed-sidecar redaction proof when available",
            comparison_lane_failed_txt_unknown_if_applicable=True,
            remaining_unknowns=[
                "comparison-lane .FAILED.txt behavior remains unknown unless separate proof is present"
            ],
        ),
        _item(
            "PRESCAN_STALENESS",
            "ACCEPTED_WITH_RISK" if packet_basis("PRESCAN_STALENESS") else "UNKNOWN",
            evidence_basis="prescan receipt/static packet evidence when available",
            accepted_import_status="accepted only when identity/freshness evidence is present",
            rejected_import_behavior="stale or malformed imported prescan must be rejected or non-authoritative",
        ),
        _item(
            "PRESCAN_INFLUENCE",
            "ACCEPTED_WITH_RISK" if packet_basis("PRESCAN_INFLUENCE") else "UNKNOWN",
            evidence_basis="prescan influence labels/static packet evidence when available",
            influence_applied_or_not="accepted influence must be explicitly labeled",
            advisory_model_derived_status="model-derived prescan signals remain advisory unless accepted by runtime guards",
        ),
        _item(
            "PROVENANCE_FIELDS",
            "PASS_STATIC" if packet_basis("PROVENANCE_FIELDS") else "UNKNOWN",
            evidence_basis="repair/sidefill provenance static packet evidence when available",
            repaired_values_labeled=True,
            sidefilled_values_labeled=True,
        ),
        _item(
            "TRUTH_LABELS",
            "PASS_STATIC" if packet_basis("TRUTH_LABELS") else "UNKNOWN",
            evidence_basis="truth-label preservation static packet evidence when available",
            unknown_preservation=True,
            conflicting_preservation=True,
        ),
        _item(
            "PROVIDER_METADATA",
            "LIVE_VALIDATION_REQUIRED",
            evidence_basis="static fixture proof only unless live validation artifacts are present",
            requested_vs_returned_model="static fixture proven; live provider edge behavior unknown",
            refusal_incomplete_static=True,
            live_provider_shapes_required=True,
            provider_lanes=provider_lanes,
        ),
        _item(
            "BATCH_STATIC",
            "PASS_WITH_RISK" if packet_basis("BATCH_STATIC") else "UNKNOWN",
            evidence_basis="batch static fixture proof when available",
            downloaded_jsonl_status=downloaded_jsonl_status,
            downloaded_jsonl_files=downloaded_jsonl,
            not_live_validated=not live_batch_validated,
            live_validation_required=not live_batch_validated,
        ),
        _item(
            "LIVE_VALIDATION_PLAN",
            "BLOCKED" if not live_validation_authorized else "LIVE_VALIDATION_REQUIRED",
            evidence_basis="local authorization/live-validation artifact inventory",
            plan_exists=live_validation_plan_exists,
            execution_not_authorized=not live_validation_authorized,
            live_validation_artifacts=live_validation_artifacts,
        ),
        _item(
            "PROOF_CONTRACT",
            proof_risk_status,
            evidence_basis="RTE-PKT-10 proof-contract helper",
            run_proof_vs_bundle_proof=proof_report.get(
                "proof_posture", "unknown; no proof payload observed"
            ),
            missing_or_partial_fields=sorted(
                set(_as_list(proof_report.get("missing_fields")))
                | set(_as_list(proof_report.get("partial_fields")))
            ),
            conformance_status=proof_contract_status,
        ),
        _item(
            "PASS1_IDENTITY",
            pass1_risk_status,
            evidence_basis="proof-contract exact Pass 1 identity classifier",
            exact_identity_known_or_unknown=pass1_identity,
            reason=_as_dict(proof_report.get("exact_pass1_identity")).get(
                "reason",
                "exact Pass 1 identity evidence is absent from current inputs",
            ),
        ),
        _item(
            "GENERATED_ARTIFACT_AUTHORITY",
            "ACCEPTED_WITH_RISK",
            evidence_basis="artifact authority classifier",
            non_authority_label="generated artifacts are evidence, not runtime source truth",
            authority_order=artifact_authority_rows,
        ),
    ]

    by_id = _risk_items_by_id(risk_items)
    blockers = _collect_blockers(by_id)
    warnings = _collect_warnings(by_id)
    accepted_risks = _collect_accepted_risks(by_id)
    unknowns = _collect_unknowns(by_id)

    blockers.extend(str(item) for item in _as_list(inputs.get("blockers")))
    warnings.extend(str(item) for item in _as_list(inputs.get("warnings")))
    accepted_risks.extend(str(item) for item in _as_list(inputs.get("accepted_risks")))
    unknowns.extend(str(item) for item in _as_list(inputs.get("unknowns")))

    dashboard = {
        "run_id_if_available": _first_string(inputs.get("run_id_if_available")),
        "generated_at": _first_string(inputs.get("generated_at")) or _now_iso(),
        "repo_root_if_available": _first_string(inputs.get("repo_root_if_available")),
        "git_sha_if_available": _first_string(inputs.get("git_sha_if_available")),
        "live_use_readiness": "READY_FOR_LIMITED_DRY_STATIC_USE",
        "static_audit_verdict": "PASS_WITH_RISK",
        "overall_risk_level": "MEDIUM-HIGH",
        "provider_call_status": provider_call_status,
        "batch_operation_status": batch_operation_status,
        "live_validation_status": live_validation_status,
        "proof_contract_status": proof_contract_status,
        "artifact_authority_status": "generated_artifacts_are_non_authoritative_evidence",
        "risk_items": risk_items,
        "blockers": _dedupe_sorted(blockers),
        "warnings": _dedupe_sorted(warnings),
        "accepted_risks": _dedupe_sorted(accepted_risks),
        "unknowns": _dedupe_sorted(unknowns),
        "next_recommended_actions": [
            "Review RTE_RISK_DASHBOARD.md before treating static proof as live readiness.",
            "Run a separately authorized live-validation packet before claiming provider behavior.",
            "Keep downloaded batch JSONL as MISSING unless local artifacts are actually present.",
            "Resolve proof-contract partial/missing fields before treating run proof as a full bundle proof.",
        ],
    }
    return sanitize_payload_for_output(dashboard)


def _collect_blockers(by_id: Mapping[str, Mapping[str, Any]]) -> list[str]:
    rows = []
    live_plan = by_id.get("LIVE_VALIDATION_PLAN", {})
    if live_plan.get("execution_not_authorized") is True:
        rows.append("LIVE_VALIDATION_PLAN: live validation execution is not authorized")
    return rows


def _collect_warnings(by_id: Mapping[str, Mapping[str, Any]]) -> list[str]:
    rows = []
    for item_id in REQUIRED_RISK_ITEM_IDS:
        item = by_id.get(item_id, {})
        status = item.get("status")
        if status in {"LIVE_VALIDATION_REQUIRED", "MISSING", "PASS_WITH_RISK"}:
            rows.append(f"{item_id}: {status}")
    batch = by_id.get("BATCH_STATIC", {})
    if batch.get("downloaded_jsonl_status") == "MISSING":
        rows.append("BATCH_STATIC: downloaded JSONL inventory is MISSING")
    return rows


def _collect_accepted_risks(by_id: Mapping[str, Mapping[str, Any]]) -> list[str]:
    rows = []
    for item_id in REQUIRED_RISK_ITEM_IDS:
        item = by_id.get(item_id, {})
        if item.get("status") in {"ACCEPTED_WITH_RISK", "PASS_WITH_RISK"}:
            rows.append(f"{item_id}: accepted static proof with residual risk")
    return rows


def _collect_unknowns(by_id: Mapping[str, Mapping[str, Any]]) -> list[str]:
    rows = []
    for item_id in REQUIRED_RISK_ITEM_IDS:
        item = by_id.get(item_id, {})
        if item.get("status") == "UNKNOWN":
            rows.append(f"{item_id}: UNKNOWN")
    pass1 = by_id.get("PASS1_IDENTITY", {})
    if pass1.get("exact_identity_known_or_unknown") == "unknown":
        rows.append("PASS1_IDENTITY: exact Pass 1 artifact identity is UNKNOWN")
    return rows


def _dedupe_sorted(values: Iterable[Any]) -> list[str]:
    return sorted({sanitize_text_for_output(str(value)) for value in values if str(value)})


def render_rte_risk_dashboard_markdown(dashboard: Mapping[str, Any]) -> str:
    safe = sanitize_payload_for_output(dashboard)
    lines = [
        "# RTE Risk Dashboard",
        "",
        f"- Run ID: {safe.get('run_id_if_available') or 'UNKNOWN'}",
        f"- Generated at: {safe.get('generated_at') or 'UNKNOWN'}",
        f"- Live-use readiness: {safe.get('live_use_readiness') or 'UNKNOWN'}",
        f"- Static audit verdict: {safe.get('static_audit_verdict') or 'UNKNOWN'}",
        f"- Overall risk level: {safe.get('overall_risk_level') or 'UNKNOWN'}",
        f"- Provider call status: {safe.get('provider_call_status') or 'UNKNOWN'}",
        f"- Batch operation status: {safe.get('batch_operation_status') or 'UNKNOWN'}",
        f"- Live validation status: {safe.get('live_validation_status') or 'UNKNOWN'}",
        f"- Proof contract status: {safe.get('proof_contract_status') or 'UNKNOWN'}",
        "",
        "## Risk Items",
        "",
        "| ID | Status | Evidence | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for item in safe.get("risk_items", []):
        if not isinstance(item, Mapping):
            continue
        note_fields = []
        for key in (
            "downloaded_jsonl_status",
            "conformance_status",
            "exact_identity_known_or_unknown",
            "non_authority_label",
        ):
            value = item.get(key)
            if value is not None:
                note_fields.append(f"{key}={value}")
        notes = "; ".join(note_fields) if note_fields else "-"
        lines.append(
            "| {id} | {status} | {evidence} | {notes} |".format(
                id=_md_cell(item.get("id")),
                status=_md_cell(item.get("status")),
                evidence=_md_cell(item.get("evidence_basis", "-")),
                notes=_md_cell(notes),
            )
        )

    for section, key in (
        ("Blockers", "blockers"),
        ("Warnings", "warnings"),
        ("Accepted Risks", "accepted_risks"),
        ("Unknowns", "unknowns"),
        ("Next Recommended Actions", "next_recommended_actions"),
    ):
        lines.extend(["", f"## {section}", ""])
        values = safe.get(key, [])
        if not values:
            lines.append("- None")
            continue
        for value in values:
            lines.append(f"- {sanitize_text_for_output(str(value))}")

    return "\n".join(lines).rstrip() + "\n"


def _md_cell(value: Any) -> str:
    text = sanitize_text_for_output(str(value if value is not None else "UNKNOWN"))
    return text.replace("|", "\\|").replace("\n", " ")


def write_rte_risk_dashboard_artifacts(
    *,
    run_root: Path,
    dashboard: Mapping[str, Any],
    write_json: Optional[Any] = None,
) -> Dict[str, str]:
    telemetry_root = run_root / "telemetry"
    telemetry_root.mkdir(parents=True, exist_ok=True)
    json_path = telemetry_root / RISK_DASHBOARD_JSON_FILENAME
    md_path = telemetry_root / RISK_DASHBOARD_MD_FILENAME
    safe = sanitize_payload_for_output(dict(dashboard))
    if write_json is not None:
        write_json(json_path, safe)
    else:
        json_path.write_text(
            json.dumps(safe, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    md_path.write_text(render_rte_risk_dashboard_markdown(safe), encoding="utf-8")
    return {
        "risk_dashboard_json": str(json_path.resolve()),
        "risk_dashboard_markdown": str(md_path.resolve()),
    }
