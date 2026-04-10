from __future__ import annotations

import json
import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.registry.seed_records import synthetic_fixture_records
from benchmarking.storage.bundle_writer import EvidenceBundleWriter
from benchmarking.storage.paths import attempt_paths, case_set_paths, run_paths


def test_bundle_writer_creates_expected_tree_and_hashes(tmp_path: Path) -> None:
    records = synthetic_fixture_records("deadbeef")
    writer = EvidenceBundleWriter(tmp_path)
    benchmark_run = records["benchmark_run"]
    case_set = records["benchmark_case_set"]
    attempt = records["benchmark_case_attempt"]

    writer.write_run_layout(
        benchmark_run=benchmark_run,
        case_set_id=case_set.case_set_id,
        contract_version=attempt.contract_version,
        contract_snapshot_id=records["contract_snapshot"].contract_snapshot_id,
        registry_snapshot_files=records["registry_snapshot_files"],
    )
    writer.write_case_set_layout(
        benchmark_run_id=benchmark_run.benchmark_run_id,
        case_set_id=case_set.case_set_id,
        case_ids=case_set.case_ids,
        control_anchor_group_id=case_set.control_anchor_group_id,
    )
    written = writer.write_attempt_bundle(
        attempt=attempt,
        route_trace=records["route_trace"],
        validator_results=records["validator_results_payload"],
        task_eval=records["task_eval_payload"],
        control_delta=records["control_delta_payload"],
        executor_links=records["executor_links_payload"],
        output_payloads=records["outputs"],
    )

    run = run_paths(benchmark_run.benchmark_run_id, tmp_path)
    case_set_paths_obj = case_set_paths(benchmark_run.benchmark_run_id, case_set.case_set_id, tmp_path)
    attempt_paths_obj = attempt_paths(benchmark_run.benchmark_run_id, case_set.case_set_id, attempt.case_attempt_id, tmp_path)
    assert run.run_manifest_path.exists()
    assert run.snapshot_manifest_path.exists()
    assert case_set_paths_obj.caseset_manifest_path.exists()
    assert attempt_paths_obj.attempt_summary_path.exists()
    assert attempt_paths_obj.evidence_manifest_path.exists()

    evidence_manifest = json.loads(attempt_paths_obj.evidence_manifest_path.read_text(encoding="utf-8"))
    assert evidence_manifest["bundle_id"] == attempt.evidence_bundle_id
    assert evidence_manifest["artifact_hashes"] == written.artifact_hashes
    assert all(len(value) == 64 for value in written.artifact_hashes.values())


def test_bundle_writer_refuses_non_deterministic_overwrite(tmp_path: Path) -> None:
    records = synthetic_fixture_records("deadbeef")
    writer = EvidenceBundleWriter(tmp_path)
    benchmark_run = records["benchmark_run"]
    case_set = records["benchmark_case_set"]
    attempt = records["benchmark_case_attempt"]
    writer.write_run_layout(
        benchmark_run=benchmark_run,
        case_set_id=case_set.case_set_id,
        contract_version=attempt.contract_version,
        contract_snapshot_id=records["contract_snapshot"].contract_snapshot_id,
        registry_snapshot_files=records["registry_snapshot_files"],
    )
    writer.write_case_set_layout(
        benchmark_run_id=benchmark_run.benchmark_run_id,
        case_set_id=case_set.case_set_id,
        case_ids=case_set.case_ids,
        control_anchor_group_id=case_set.control_anchor_group_id,
    )
    writer.write_attempt_bundle(
        attempt=attempt,
        route_trace=records["route_trace"],
        validator_results=records["validator_results_payload"],
        task_eval=records["task_eval_payload"],
        control_delta=records["control_delta_payload"],
        executor_links=records["executor_links_payload"],
        output_payloads=records["outputs"],
    )
    try:
        writer.write_attempt_bundle(
            attempt=attempt,
            route_trace={"changed": True},
            validator_results=records["validator_results_payload"],
            task_eval=records["task_eval_payload"],
            control_delta=records["control_delta_payload"],
            executor_links=records["executor_links_payload"],
            output_payloads=records["outputs"],
        )
    except RuntimeError as exc:
        assert "immutable benchmark artifact" in str(exc)
    else:
        raise AssertionError("expected immutable overwrite refusal")

