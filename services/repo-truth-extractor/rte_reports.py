from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence, Set

from reporting import (
    ReportingDeps,
    TelemetryWriterDeps,
    write_certification_result as _write_certification_result_impl,
    update_proof_pack as _update_proof_pack_impl,
    update_run_manifest_promptset_block as _update_run_manifest_promptset_block_impl,
    write_blocked_promptset_proof_pack as _write_blocked_promptset_proof_pack_impl,
    write_coverage_rollup as _write_coverage_rollup_impl,
    write_failure_index_snapshot as _write_failure_index_snapshot_impl,
    write_phase_coverage_manifest as _write_phase_coverage_manifest_impl,
    write_promptset_blocked_marker as _write_promptset_blocked_marker_impl,
    write_resume_proof as _write_resume_proof_impl,
    write_run_dashboard_snapshot as _write_run_dashboard_snapshot_impl,
    write_run_manifest as _write_run_manifest_impl,
    write_step_metrics_snapshot as _write_step_metrics_snapshot_impl,
)


def write_step_metrics_snapshot(
    deps: TelemetryWriterDeps,
    run_root: Path,
    phase: str,
    step_id: str,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    return _write_step_metrics_snapshot_impl(deps, run_root, phase, step_id, metrics)


def write_failure_index_snapshot(
    deps: TelemetryWriterDeps,
    run_root: Path,
    phase: str,
    step_id: str,
    failure_histogram: Dict[str, int],
    first_failure: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _write_failure_index_snapshot_impl(
        deps,
        run_root,
        phase,
        step_id,
        failure_histogram,
        first_failure,
    )


def write_run_dashboard_snapshot(
    deps: TelemetryWriterDeps,
    run_root: Path,
    payload: Dict[str, Any],
    source: str,
) -> Dict[str, Any]:
    return _write_run_dashboard_snapshot_impl(deps, run_root, payload, source)


def write_certification_result(
    deps: ReportingDeps,
    run_root: Path,
    *,
    validator_payload: Optional[Dict[str, Any]] = None,
    provider_preflight_payload: Optional[Dict[str, Any]] = None,
    topology_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _write_certification_result_impl(
        deps,
        run_root,
        validator_payload=validator_payload,
        provider_preflight_payload=provider_preflight_payload,
        topology_payload=topology_payload,
    )


def write_run_manifest(
    deps: ReportingDeps,
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    args: Any,
    run_context: Any,
    phases: list[str],
) -> Dict[str, Any]:
    return _write_run_manifest_impl(deps, root, dirs, run_id, args, run_context, phases)


def write_phase_coverage_manifest(
    deps: ReportingDeps,
    phase: str,
    phase_dir: Path,
    *,
    selected_step_ids: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    return _write_phase_coverage_manifest_impl(
        deps,
        phase,
        phase_dir,
        selected_step_ids=selected_step_ids,
    )


def write_coverage_rollup(
    deps: ReportingDeps,
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    promptset_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _write_coverage_rollup_impl(deps, root, dirs, run_id, promptset_report)


def write_resume_proof(
    deps: ReportingDeps,
    dirs: Dict[str, Path],
    run_id: str,
    phases: Iterable[str],
    *,
    promptset_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return _write_resume_proof_impl(
        deps,
        dirs,
        run_id,
        phases,
        promptset_report=promptset_report,
    )


def update_proof_pack(
    deps: ReportingDeps,
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    run_started_at: str,
    phase: str,
    phase_counts: Dict[str, Any],
    phase_started_at: str,
    phase_finished_at: str,
) -> None:
    _update_proof_pack_impl(
        deps,
        root,
        dirs,
        run_id,
        run_started_at,
        phase,
        phase_counts,
        phase_started_at,
        phase_finished_at,
    )


def write_blocked_promptset_proof_pack(
    deps: ReportingDeps,
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    run_started_at: str,
    phases: list[str],
    prompt_report: Dict[str, Any],
) -> None:
    _write_blocked_promptset_proof_pack_impl(
        deps,
        root,
        dirs,
        run_id,
        run_started_at,
        phases,
        prompt_report,
    )


def update_run_manifest_promptset_block(
    deps: ReportingDeps,
    run_root: Path,
    phase: str,
    prompt_report: Dict[str, Any],
) -> None:
    _update_run_manifest_promptset_block_impl(deps, run_root, phase, prompt_report)


def write_promptset_blocked_marker(
    deps: ReportingDeps,
    phase: str,
    phase_dir: Path,
    prompt_report: Dict[str, Any],
) -> None:
    _write_promptset_blocked_marker_impl(deps, phase, phase_dir, prompt_report)


def refresh_run_manifest_artifacts(
    run_root: Path,
    dirs: Dict[str, Path],
    *,
    collect_manifest_artifacts: Any,
    now_iso: Any,
    write_json: Any,
) -> None:
    manifest_path = run_root / "RUN_MANIFEST.json"
    payload: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    payload["artifacts"] = collect_manifest_artifacts(dirs)
    payload["artifacts_updated_at"] = now_iso()
    write_json(manifest_path, payload)


def update_run_manifest_contract_map(
    run_root: Path,
    contract_map_path: Optional[Path],
    *,
    phase_contract_map_filename: str,
    now_iso: Any,
    write_json: Any,
) -> None:
    if contract_map_path is None:
        return
    manifest_path = run_root / "RUN_MANIFEST.json"
    payload: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    payload["phase_contract_map"] = str(contract_map_path.resolve())
    payload["phase_contract_map_filename"] = phase_contract_map_filename
    payload["phase_contract_map_updated_at"] = now_iso()
    write_json(manifest_path, payload)


def write_runner_identity(
    root: Path,
    run_root: Path,
    run_id: str,
    *,
    now_iso: Any,
    get_git_sha: Any,
    runner_script: Path,
    sha256_text: Any,
    python_executable: str,
    write_json: Any,
) -> None:
    payload = {
        "run_id": run_id,
        "generated_at": now_iso(),
        "git_sha": get_git_sha(root),
        "runner_script_path": str(runner_script.resolve()),
        "runner_sha256": sha256_text(runner_script),
        "python_executable": python_executable,
        "python_version": platform.python_version(),
    }
    write_json(run_root / "RUNNER_IDENTITY.json", payload)


def _count_files(directory: Path, suffixes: Optional[Set[str]] = None) -> int:
    if not directory.exists():
        return 0
    count = 0
    for entry in sorted(directory.iterdir()):
        if not entry.is_file():
            continue
        if suffixes and entry.suffix.lower() not in suffixes:
            continue
        count += 1
    return count


def gather_phase_counts(phase_dir: Path) -> Dict[str, Any]:
    inputs_dir = phase_dir / "inputs"
    raw_dir = phase_dir / "raw"
    norm_dir = phase_dir / "norm"
    qa_dir = phase_dir / "qa"

    inputs_count = _count_files(inputs_dir)

    raw_ok = 0
    raw_failed = 0
    raw_total = 0
    if raw_dir.exists():
        for entry in sorted(raw_dir.iterdir()):
            if not entry.is_file():
                continue
            raw_total += 1
            if ".FAILED" in entry.name:
                raw_failed += 1
            elif entry.suffix.lower() == ".json":
                raw_ok += 1

    norm_count = _count_files(norm_dir, suffixes={".json"})
    qa_count = _count_files(qa_dir, suffixes={".json", ".md", ".txt"})

    return {
        "inputs": inputs_count,
        "raw": {"total": raw_total, "ok": raw_ok, "failed": raw_failed},
        "norm": norm_count,
        "qa": qa_count,
    }
