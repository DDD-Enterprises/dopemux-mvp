from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..storage.hashing import hash_json
from ..storage.sqlite_repo import BenchmarkCatalogRepo

MISSING_ROUTE_TELEMETRY = "MISSING_ROUTE_TELEMETRY"
MALFORMED_ROUTE_TELEMETRY = "MALFORMED_ROUTE_TELEMETRY"


class RouteTelemetryError(RuntimeError):
    def __init__(self, blocker_code: str, message: str) -> None:
        super().__init__(message)
        self.blocker_code = blocker_code


@dataclass(frozen=True)
class RouteIdentityRecord:
    benchmark_run_id: str
    case_attempt_id: str
    case_id: str
    phase_or_step_family: str
    surface_class: str
    runtime_version: str
    contract_version: str
    contract_snapshot_id: str
    evidence_bundle_id: str
    declared_route_id: str
    selected_route_identity: dict[str, Any]
    effective_route_signature: dict[str, list[str]]
    effective_route_signature_hash: str
    route_signature_source_refs: list[str]
    admissibility_status: str
    admissibility_blocker_codes: list[str]
    admissibility_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_run_id": self.benchmark_run_id,
            "case_attempt_id": self.case_attempt_id,
            "case_id": self.case_id,
            "phase_or_step_family": self.phase_or_step_family,
            "surface_class": self.surface_class,
            "runtime_version": self.runtime_version,
            "contract_version": self.contract_version,
            "contract_snapshot_id": self.contract_snapshot_id,
            "evidence_bundle_id": self.evidence_bundle_id,
            "declared_route_id": self.declared_route_id,
            "selected_route_identity": self.selected_route_identity,
            "effective_route_signature": self.effective_route_signature,
            "effective_route_signature_hash": self.effective_route_signature_hash,
            "route_signature_source_refs": self.route_signature_source_refs,
            "admissibility_status": self.admissibility_status,
            "admissibility_blocker_codes": self.admissibility_blocker_codes,
            "admissibility_notes": self.admissibility_notes,
        }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_ref(path: Path, attempt_root: Path) -> str:
    try:
        return str(path.relative_to(attempt_root))
    except ValueError:
        return str(path)


def _extract_signature(step_metrics: dict[str, Any]) -> dict[str, list[str]]:
    steps = step_metrics.get("steps")
    if not isinstance(steps, dict):
        raise RouteTelemetryError(MALFORMED_ROUTE_TELEMETRY, "STEP_METRICS.json missing steps object")
    signature: dict[str, list[str]] = {}
    for step_id, payload in sorted(steps.items()):
        if not isinstance(payload, dict):
            raise RouteTelemetryError(MALFORMED_ROUTE_TELEMETRY, f"STEP_METRICS step payload malformed: {step_id}")
        route_counts = payload.get("final_route_counts", {})
        if route_counts is None:
            continue
        if not isinstance(route_counts, dict):
            raise RouteTelemetryError(MALFORMED_ROUTE_TELEMETRY, f"STEP_METRICS final_route_counts malformed: {step_id}")
        routes = sorted(str(route) for route in route_counts.keys())
        if routes:
            signature[str(step_id)] = routes
    if not signature:
        raise RouteTelemetryError(MISSING_ROUTE_TELEMETRY, "STEP_METRICS.json did not contain any final_route_counts")
    return signature


def extract_effective_route_signature(step_metrics: dict[str, Any]) -> tuple[dict[str, list[str]], str]:
    signature = _extract_signature(step_metrics)
    return signature, hash_json(signature)


def build_route_identity_record(
    repo: BenchmarkCatalogRepo,
    attempt: dict[str, Any],
) -> RouteIdentityRecord:
    bundle = repo.fetch_bundle(str(attempt["evidence_bundle_id"]))
    if bundle is None:
        raise RouteTelemetryError(MISSING_ROUTE_TELEMETRY, f"missing evidence bundle {attempt['evidence_bundle_id']}")
    attempt_root = Path(str(bundle["root_path"]))
    route_trace_path = attempt_root / "ROUTE_TRACE.json"
    if not route_trace_path.exists():
        raise RouteTelemetryError(MISSING_ROUTE_TELEMETRY, f"missing route telemetry files: {[str(route_trace_path)]}")
    route_trace = _load_json(route_trace_path)
    step_metrics_path = attempt_root / "outputs" / "STEP_METRICS.json"
    if not step_metrics_path.exists():
        step_metrics_path = Path(str(route_trace.get("run_root") or "")) / "telemetry" / "STEP_METRICS.json"
    routing_fingerprint_path = attempt_root / "outputs" / "RUN_ROUTING_FINGERPRINT.json"
    if not routing_fingerprint_path.exists():
        routing_fingerprint_path = Path(str(route_trace.get("routing_fingerprint_path") or ""))
    failure_index_path = attempt_root / "outputs" / "FAILURE_INDEX.json"
    if not failure_index_path.exists():
        failure_index_path = Path(str(route_trace.get("run_root") or "")) / "telemetry" / "FAILURE_INDEX.json"

    missing = [str(path) for path in (step_metrics_path, routing_fingerprint_path) if not path.exists()]
    if missing:
        raise RouteTelemetryError(MISSING_ROUTE_TELEMETRY, f"missing route telemetry files: {missing}")

    step_metrics = _load_json(step_metrics_path)
    routing_fingerprint = _load_json(routing_fingerprint_path)
    effective_route_signature, signature_hash = extract_effective_route_signature(step_metrics)

    route_record = repo.fetch_route(str(attempt["route_id"])) or {}
    surface_record = repo.fetch_provider_surface(str(attempt["surface_id"])) or {}
    selected_route_identity = dict(route_trace.get("selected_route_identity") or {})
    selected_route_identity.setdefault("declared_route_id", str(attempt["route_id"]))
    selected_route_identity.setdefault("surface_id", str(attempt["surface_id"]))
    selected_route_identity.setdefault("surface_class", str(attempt["surface_class"]))
    selected_route_identity.setdefault("provider_name", str(surface_record.get("provider_name") or ""))
    selected_route_identity.setdefault("model_key", str(route_record.get("model_key") or ""))
    selected_route_identity.setdefault("provider_model_id", str(route_record.get("provider_model_id") or ""))
    selected_route_identity.setdefault("route_pin", str(route_record.get("route_pin") or ""))
    selected_route_identity.setdefault(
        "representative_phase_route",
        routing_fingerprint.get("effective_model_routing", {}).get("A"),
    )

    source_refs = [
        _source_ref(route_trace_path, attempt_root),
        _source_ref(step_metrics_path, attempt_root),
        _source_ref(routing_fingerprint_path, attempt_root),
    ]
    if failure_index_path.exists():
        source_refs.append(_source_ref(failure_index_path, attempt_root))

    return RouteIdentityRecord(
        benchmark_run_id=str(attempt["benchmark_run_id"]),
        case_attempt_id=str(attempt["case_attempt_id"]),
        case_id=str(attempt["case_id"]),
        phase_or_step_family=str(attempt["phase_or_step_family"]),
        surface_class=str(attempt["surface_class"]),
        runtime_version=str(attempt["runtime_version"]),
        contract_version=str(attempt["contract_version"]),
        contract_snapshot_id=str(attempt["contract_snapshot_id"]),
        evidence_bundle_id=str(attempt["evidence_bundle_id"]),
        declared_route_id=str(attempt["route_id"]),
        selected_route_identity=selected_route_identity,
        effective_route_signature=effective_route_signature,
        effective_route_signature_hash=signature_hash,
        route_signature_source_refs=source_refs,
        admissibility_status="derived",
        admissibility_blocker_codes=[],
        admissibility_notes=[],
    )
