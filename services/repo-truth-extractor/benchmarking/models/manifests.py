from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .entities import BenchmarkModel
from .enums import BundleType
from .ids import utc_now_iso


@dataclass(frozen=True)
class BenchmarkRunManifest(BenchmarkModel):
    benchmark_run_id: str
    runtime_version: str
    contract_snapshot_ids: list[str]
    case_set_ids: list[str]
    status: str
    created_at_utc: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class SnapshotManifest(BenchmarkModel):
    benchmark_run_id: str
    runtime_version: str
    contract_version: str
    contract_snapshot_id: str
    registry_snapshot_files: list[str]
    created_at_utc: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class CaseSetManifest(BenchmarkModel):
    benchmark_run_id: str
    case_set_id: str
    case_ids: list[str]
    control_anchor_group_id: str
    created_at_utc: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class AttemptSummaryManifest(BenchmarkModel):
    benchmark_run_id: str
    case_set_id: str
    case_attempt_id: str
    route_id: str
    profile_id: str
    surface_class: str
    contract_gate_pass: bool
    validator_pass: bool
    task_success_score: float
    created_at_utc: str = field(default_factory=utc_now_iso)


@dataclass(frozen=True)
class EvidenceManifest(BenchmarkModel):
    bundle_id: str
    bundle_type: BundleType
    benchmark_run_id: str
    case_set_id: str
    case_attempt_id: str
    manifest_hash: str
    artifact_hashes: dict[str, str]
    artifact_refs: dict[str, str]
    immutable_written_at_utc: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_type", BundleType.coerce(self.bundle_type))


@dataclass(frozen=True)
class SmokeLinkageReport(BenchmarkModel):
    benchmark_run_id: str
    case_set_id: str
    case_attempt_id: str
    bundle_id: str
    bundle_path: str
    db_row_counts: dict[str, int]
    sample_attempt: dict[str, Any]
    evidence_manifest: dict[str, Any]
    created_at_utc: str = field(default_factory=utc_now_iso)

