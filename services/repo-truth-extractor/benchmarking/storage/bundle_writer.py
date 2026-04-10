from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models.entities import BenchmarkCaseAttempt, BenchmarkRun, EvidenceBundle
from ..models.manifests import (
    AttemptSummaryManifest,
    BenchmarkRunManifest,
    CaseSetManifest,
    EvidenceManifest,
    SnapshotManifest,
)
from .hashing import hash_file, hash_json, stable_json_dumps
from .paths import attempt_paths, case_set_paths, run_paths


@dataclass(frozen=True)
class WrittenBundle:
    bundle: EvidenceBundle
    artifact_hashes: dict[str, str]
    manifest_payload: dict[str, Any]
    attempt_dir: Path


def _write_immutable_json(path: Path, payload: dict[str, Any]) -> None:
    raw = stable_json_dumps(payload) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing != raw:
            raise RuntimeError(f"refusing to overwrite immutable benchmark artifact: {path}")
        return
    path.write_text(raw, encoding="utf-8")


class EvidenceBundleWriter:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root

    def write_run_layout(
        self,
        benchmark_run: BenchmarkRun,
        case_set_id: str,
        contract_version: str,
        contract_snapshot_id: str,
        registry_snapshot_files: list[str],
    ) -> None:
        run = run_paths(benchmark_run.benchmark_run_id, self.root)
        for directory in (
            run.run_root,
            run.registry_snapshots_dir,
            run.case_sets_dir,
            run.rollups_dir,
            run.recommendations_dir,
            run.governance_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        _write_immutable_json(
            run.run_manifest_path,
            BenchmarkRunManifest(
                benchmark_run_id=benchmark_run.benchmark_run_id,
                runtime_version=benchmark_run.runtime_version,
                contract_snapshot_ids=benchmark_run.contract_snapshot_ids,
                case_set_ids=[case_set_id],
                status=benchmark_run.status,
            ).to_dict(),
        )
        _write_immutable_json(
            run.snapshot_manifest_path,
            SnapshotManifest(
                benchmark_run_id=benchmark_run.benchmark_run_id,
                runtime_version=benchmark_run.runtime_version,
                contract_version=contract_version,
                contract_snapshot_id=contract_snapshot_id,
                registry_snapshot_files=registry_snapshot_files,
            ).to_dict(),
        )
        for relative_path in registry_snapshot_files:
            snapshot_path = run.registry_snapshots_dir / relative_path
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            if not snapshot_path.exists():
                snapshot_path.write_text(f"reserved:{relative_path}\n", encoding="utf-8")

    def write_case_set_layout(
        self,
        benchmark_run_id: str,
        case_set_id: str,
        case_ids: list[str],
        control_anchor_group_id: str,
    ) -> None:
        paths = case_set_paths(benchmark_run_id, case_set_id, self.root)
        paths.case_set_root.mkdir(parents=True, exist_ok=True)
        paths.attempts_dir.mkdir(parents=True, exist_ok=True)
        _write_immutable_json(
            paths.caseset_manifest_path,
            CaseSetManifest(
                benchmark_run_id=benchmark_run_id,
                case_set_id=case_set_id,
                case_ids=case_ids,
                control_anchor_group_id=control_anchor_group_id,
            ).to_dict(),
        )

    def write_attempt_bundle(
        self,
        attempt: BenchmarkCaseAttempt,
        route_trace: dict[str, Any],
        validator_results: dict[str, Any],
        task_eval: dict[str, Any],
        control_delta: dict[str, Any],
        executor_links: dict[str, Any],
        output_payloads: dict[str, Any],
    ) -> WrittenBundle:
        paths = attempt_paths(attempt.benchmark_run_id, attempt.case_set_id, attempt.case_attempt_id, self.root)
        paths.attempt_root.mkdir(parents=True, exist_ok=True)
        paths.outputs_dir.mkdir(parents=True, exist_ok=True)

        _write_immutable_json(
            paths.attempt_summary_path,
            AttemptSummaryManifest(
                benchmark_run_id=attempt.benchmark_run_id,
                case_set_id=attempt.case_set_id,
                case_attempt_id=attempt.case_attempt_id,
                route_id=attempt.route_id,
                profile_id=attempt.profile_id,
                surface_class=attempt.surface_class.value,
                contract_gate_pass=attempt.contract_gate_pass,
                validator_pass=attempt.validator_pass,
                task_success_score=attempt.task_success_score,
            ).to_dict(),
        )
        _write_immutable_json(paths.route_trace_path, route_trace)
        _write_immutable_json(paths.validator_results_path, validator_results)
        _write_immutable_json(paths.task_eval_path, task_eval)
        _write_immutable_json(paths.control_delta_path, control_delta)
        _write_immutable_json(paths.executor_links_path, executor_links)

        for relative_name, payload in output_payloads.items():
            output_path = paths.outputs_dir / relative_name
            if isinstance(payload, str):
                raw = payload if payload.endswith("\n") else f"{payload}\n"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                if output_path.exists():
                    existing = output_path.read_text(encoding="utf-8")
                    if existing != raw:
                        raise RuntimeError(f"refusing to overwrite immutable benchmark artifact: {output_path}")
                else:
                    output_path.write_text(raw, encoding="utf-8")
            else:
                _write_immutable_json(output_path, payload)

        artifact_paths = {
            "ATTEMPT_SUMMARY.json": paths.attempt_summary_path,
            "ROUTE_TRACE.json": paths.route_trace_path,
            "VALIDATOR_RESULTS.json": paths.validator_results_path,
            "TASK_EVAL.json": paths.task_eval_path,
            "CONTROL_DELTA.json": paths.control_delta_path,
            "EXECUTOR_LINKS.json": paths.executor_links_path,
        }
        for relative_name in output_payloads:
            artifact_paths[f"outputs/{relative_name}"] = paths.outputs_dir / relative_name

        artifact_hashes = {name: hash_file(path) for name, path in artifact_paths.items()}
        manifest_seed = {
            "bundle_id": attempt.evidence_bundle_id,
            "benchmark_run_id": attempt.benchmark_run_id,
            "case_set_id": attempt.case_set_id,
            "case_attempt_id": attempt.case_attempt_id,
            "artifact_hashes": artifact_hashes,
        }
        manifest_hash = hash_json(manifest_seed)
        manifest_payload = EvidenceManifest(
            bundle_id=attempt.evidence_bundle_id,
            bundle_type="benchmark_case_attempt",
            benchmark_run_id=attempt.benchmark_run_id,
            case_set_id=attempt.case_set_id,
            case_attempt_id=attempt.case_attempt_id,
            manifest_hash=manifest_hash,
            artifact_hashes=artifact_hashes,
            artifact_refs={name: str(path.relative_to(paths.attempt_root)) for name, path in artifact_paths.items()},
        ).to_dict()
        _write_immutable_json(paths.evidence_manifest_path, manifest_payload)

        bundle = EvidenceBundle(
            bundle_id=attempt.evidence_bundle_id,
            bundle_type="benchmark_case_attempt",
            benchmark_run_id=attempt.benchmark_run_id,
            root_path=str(paths.attempt_root),
            manifest_hash=manifest_hash,
            artifact_hashes=artifact_hashes,
            retention_class="immutable_smoke",
            content_hash=hash_json(manifest_payload),
            source_ref="filesystem_bundle_writer",
            notes=["M0 synthetic benchmark evidence bundle"],
        )
        return WrittenBundle(
            bundle=bundle,
            artifact_hashes=artifact_hashes,
            manifest_payload=manifest_payload,
            attempt_dir=paths.attempt_root,
        )

