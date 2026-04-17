from __future__ import annotations

import argparse
import os
import platform
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

from rte_config import (
    COVERAGE_ROLLUP_FILENAME,
    CERTIFICATION_RESULT_FILENAME,
    FAILURE_INDEX_FILENAME,
    PROOF_PACK_FILENAME,
    RESUME_PROOF_FILENAME,
    RUN_DASHBOARD_FILENAME,
    STEP_METRICS_FILENAME,
)


@dataclass(frozen=True)
class TelemetryWriterDeps:
    telemetry_path: Callable[[Path, str], Path]
    load_json_object: Callable[[Path], Dict[str, Any]]
    write_json: Callable[[Path, Any], None]
    now_iso: Callable[[], str]
    telemetry_snapshot_lock: Any


@dataclass(frozen=True)
class ReportingDeps:
    write_json: Callable[[Path, Any], None]
    now_iso: Callable[[], str]
    get_git_sha: Callable[[Path], str]
    sha256_text: Callable[[Path], str]
    promptset_fingerprint: Callable[[Iterable[str]], Dict[str, Any]]
    refresh_run_manifest_artifacts: Callable[[Path, Dict[str, Path]], None]
    compute_run_status: Callable[..., str]
    update_run_manifest_status: Callable[..., str]
    read_step_qa_payloads: Callable[[Path], List[Dict[str, Any]]]
    coverage_for_phase: Callable[[str, Path], Dict[str, Any]]
    write_strict_passthrough_attestations: Callable[[Dict[str, Path], str, Iterable[str]], Dict[str, Any]]
    current_output_layout: Callable[[Path], Any]
    current_doctor_root: Callable[[Path], Path]
    load_json: Callable[[Path], Dict[str, Any]]
    read_repair_counters: Callable[[], Dict[str, int]]
    get_phase_prompts: Callable[[str], List[Any]]
    resolve_effective_step_tier: Callable[..., Any]
    routing_ladders_payload: Callable[[], Dict[str, Any]]
    effective_model_routing_payload: Callable[[], Dict[str, Any]]
    benchmark_route_ownership_payload: Callable[..., Dict[str, Any]]
    blocked_promptset_payload: Callable[[Dict[str, Any], str], Dict[str, Any]]
    resume_blocked_payload: Callable[[Dict[str, Any]], Dict[str, Any]]
    expected_artifact_present: Callable[[Path, str], bool]
    is_cost_abort_triggered: Callable[[], bool]
    promptset_blocked_reason: str
    prompt_hash_mode: str
    phases: Sequence[str]
    runner_script: Path
    default_routing_policy: str
    routing_policy_version: str
    s_prompts_legacy: str
    dpmx_webhook_url_env: str
    dpmx_webhook_secret_env: str
    dpmx_webhook_timeout_seconds_env: str
    dpmx_webhook_required_env: str
    dpmx_webhook_auto_continue_env: str
    dpmx_live_ok_env: str


def write_step_metrics_snapshot(
    deps: TelemetryWriterDeps,
    run_root: Path,
    phase: str,
    step_id: str,
    metrics: Dict[str, Any],
) -> Dict[str, Any]:
    target = deps.telemetry_path(run_root, STEP_METRICS_FILENAME)
    with deps.telemetry_snapshot_lock:
        payload = deps.load_json_object(target)
        steps = payload.get("steps")
        if not isinstance(steps, dict):
            steps = {}
        steps[f"{phase}:{step_id}"] = dict(metrics)
        snapshot = {
            "generated_at": deps.now_iso(),
            "run_id": run_root.name,
            "steps": dict(sorted(steps.items())),
        }
        deps.write_json(target, snapshot)
    return snapshot


def write_failure_index_snapshot(
    deps: TelemetryWriterDeps,
    run_root: Path,
    phase: str,
    step_id: str,
    failure_histogram: Dict[str, int],
    first_failure: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    target = deps.telemetry_path(run_root, FAILURE_INDEX_FILENAME)
    with deps.telemetry_snapshot_lock:
        payload = deps.load_json_object(target)
        steps = payload.get("steps")
        if not isinstance(steps, dict):
            steps = {}
        ordered_hist = dict(
            sorted(
                (
                    (str(key), int(value))
                    for key, value in (failure_histogram or {}).items()
                    if int(value) > 0
                ),
                key=lambda row: (-row[1], row[0]),
            )
        )
        steps[f"{phase}:{step_id}"] = {
            "failure_histogram": ordered_hist,
            "first_failure": dict(first_failure) if isinstance(first_failure, dict) else None,
        }
        global_hist = Counter()
        for row in steps.values():
            if not isinstance(row, dict):
                continue
            hist = row.get("failure_histogram")
            if not isinstance(hist, dict):
                continue
            for key, value in hist.items():
                try:
                    global_hist[str(key)] += int(value)
                except Exception:
                    continue
        snapshot = {
            "generated_at": deps.now_iso(),
            "run_id": run_root.name,
            "steps": dict(sorted(steps.items())),
            "global_failure_histogram": dict(
                sorted(global_hist.items(), key=lambda row: (-row[1], row[0]))
            ),
        }
        deps.write_json(target, snapshot)
    return snapshot


def write_run_dashboard_snapshot(
    deps: TelemetryWriterDeps,
    run_root: Path,
    payload: Dict[str, Any],
    source: str,
) -> Dict[str, Any]:
    target = deps.telemetry_path(run_root, RUN_DASHBOARD_FILENAME)
    snapshot = {
        "generated_at": deps.now_iso(),
        "run_id": run_root.name,
        "source": str(source or "").strip() or "phase",
        "summary": dict(payload.get("summary")) if isinstance(payload.get("summary"), dict) else {},
        "payload": dict(payload),
    }
    deps.write_json(target, snapshot)
    return snapshot


def _normalize_gate_status(value: Optional[str]) -> str:
    token = str(value or "").strip().upper()
    if token in {"PASS", "PASSED", "READY", "OK"}:
        return "PASS"
    if token in {"FAIL", "FAILED", "BLOCKED", "NO_GO"}:
        return "FAIL"
    return "UNKNOWN"


def _gate_payload(status: str, *, source: str, evidence: Dict[str, Any], notes: Optional[str] = None) -> Dict[str, Any]:
    payload = {
        "status": status,
        "source": source,
        "evidence": evidence,
    }
    if notes:
        payload["notes"] = notes
    return payload


def write_certification_result(
    deps: ReportingDeps,
    run_root: Path,
    *,
    validator_payload: Optional[Dict[str, Any]] = None,
    provider_preflight_payload: Optional[Dict[str, Any]] = None,
    topology_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    telemetry_root = run_root / "telemetry"
    output_root = run_root.parent.parent if run_root.parent.name == "runs" else run_root.parent
    doctor_root = output_root / "doctor"
    proof_path = run_root / PROOF_PACK_FILENAME
    coverage_path = run_root / COVERAGE_ROLLUP_FILENAME
    resume_path = run_root / RESUME_PROOF_FILENAME
    dashboard_path = telemetry_root / RUN_DASHBOARD_FILENAME
    step_metrics_path = telemetry_root / STEP_METRICS_FILENAME
    failure_index_path = telemetry_root / FAILURE_INDEX_FILENAME

    if validator_payload is None:
        validator_path = run_root / "PRELIVE_VALIDATOR_RESULT.json"
        if validator_path.exists():
            validator_payload = deps.load_json(validator_path)

    if provider_preflight_payload is None and doctor_root.exists():
        provider_payloads: List[Dict[str, Any]] = []
        for candidate in sorted(doctor_root.glob("PROVIDER_PREFLIGHT*.json")):
            try:
                payload = deps.load_json(candidate)
            except Exception:
                continue
            if isinstance(payload, dict):
                provider_payloads.append(payload)
        if provider_payloads:
            provider_preflight_payload = {
                "status": "PASS"
                if all(
                    _normalize_gate_status(str(payload.get("status") or "")) == "PASS"
                    for payload in provider_payloads
                )
                else "FAIL",
                "layers": provider_payloads,
            }

    if topology_payload is None and doctor_root.exists():
        topology_path = doctor_root / "DOCTOR_FULL.json"
        if topology_path.exists():
            topology_payload = deps.load_json(topology_path)

    proof = deps.load_json(proof_path) if proof_path.exists() else {}
    coverage = deps.load_json(coverage_path) if coverage_path.exists() else {}
    resume = deps.load_json(resume_path) if resume_path.exists() else {}
    dashboard = deps.load_json(dashboard_path) if dashboard_path.exists() else {}
    step_metrics = deps.load_json(step_metrics_path) if step_metrics_path.exists() else {}
    failure_index = deps.load_json(failure_index_path) if failure_index_path.exists() else {}

    artifact_contract_evidence: Dict[str, Any] = {
        "proof_pack": str(proof_path.resolve()) if proof_path.exists() else None,
        "coverage_rollup": str(coverage_path.resolve()) if coverage_path.exists() else None,
        "resume_proof": str(resume_path.resolve()) if resume_path.exists() else None,
        "run_dashboard": str(dashboard_path.resolve()) if dashboard_path.exists() else None,
        "step_metrics": str(step_metrics_path.resolve()) if step_metrics_path.exists() else None,
        "failure_index": str(failure_index_path.resolve()) if failure_index_path.exists() else None,
    }
    artifact_contract_status = "UNKNOWN"
    if all(artifact_contract_evidence.values()):
        artifact_contract_status = "PASS"

    topology_probe_rows: List[Dict[str, Any]] = []
    if isinstance(topology_payload, dict):
        reachability = topology_payload.get("provider_reachability")
        probes = reachability.get("probes") if isinstance(reachability, dict) else None
        if isinstance(probes, list):
            topology_probe_rows = [row for row in probes if isinstance(row, dict)]

    topology_status = "UNKNOWN"
    if isinstance(topology_payload, dict):
        topology_status = _normalize_gate_status(
            str(topology_payload.get("status") or topology_payload.get("overall_status") or "")
        )
    elif isinstance(dashboard, dict) and dashboard:
        topology_status = _normalize_gate_status(str(dashboard.get("status") or dashboard.get("overall_status") or ""))

    live_provider_status = "UNKNOWN"
    live_provider_evidence: Dict[str, Any] = {
        "provider_preflight": provider_preflight_payload if isinstance(provider_preflight_payload, dict) else None,
        "topology_probes_observed": topology_probe_rows or None,
    }
    if isinstance(provider_preflight_payload, dict):
        live_provider_status = _normalize_gate_status(str(provider_preflight_payload.get("status") or ""))

    static_status = "UNKNOWN"
    static_evidence: Dict[str, Any] = {
        "prelive_validator": validator_payload if isinstance(validator_payload, dict) else None,
        "coverage_rollup": coverage if coverage else None,
        "resume_proof": resume if resume else None,
    }
    if isinstance(validator_payload, dict):
        static_status = _normalize_gate_status(str(validator_payload.get("status") or validator_payload.get("final_verdict") or ""))
    elif isinstance(proof, dict) and proof.get("run_status"):
        static_status = _normalize_gate_status(str(proof.get("run_status") or ""))

    gates = {
        "canonical_runner_correctness": _gate_payload(
            static_status,
            source="PRELIVE_VALIDATOR_RESULT.json" if isinstance(validator_payload, dict) else "PROOF_PACK.json",
            evidence=static_evidence,
            notes="Static/internal gate. Unknown when no validator evidence is present.",
        ),
        "live_provider_readiness": _gate_payload(
            live_provider_status,
            source="provider preflight payload",
            evidence=live_provider_evidence,
            notes="PASS requires explicit provider preflight evidence. Topology probe observations alone do not satisfy this gate.",
        ),
        "artifact_contract_stability": _gate_payload(
            artifact_contract_status,
            source="runtime artifact set",
            evidence=artifact_contract_evidence,
            notes="Pass requires the core evidence artifacts to exist in the run root and telemetry root.",
        ),
        "operator_topology_resilience": _gate_payload(
            topology_status,
            source="DOCTOR_FULL.json or RUN_DASHBOARD.json",
            evidence={
                "doctor_full": topology_payload if isinstance(topology_payload, dict) else None,
                "run_dashboard": dashboard if dashboard else None,
                "required_artifact_groups": (
                    topology_payload.get("required_artifact_groups")
                    if isinstance(topology_payload, dict)
                    else None
                ),
            },
            notes="PASS requires explicit topology status evidence. Artifact completeness alone does not satisfy this gate.",
        ),
    }

    gate_statuses = [gate["status"] for gate in gates.values()]
    if all(status == "PASS" for status in gate_statuses):
        overall_status = "VERIFIED"
    elif any(status == "FAIL" for status in gate_statuses):
        overall_status = "BLOCKED"
    else:
        overall_status = "UNKNOWN"

    payload = {
        "artifact_version": "RTE_CERTIFICATION_V1",
        "generated_at": deps.now_iso(),
        "run_id": run_root.name,
        "overall_status": overall_status,
        "gate_classification": {
            "canonical_runner_correctness": "static",
            "live_provider_readiness": "live_provider",
            "artifact_contract_stability": "contract",
            "operator_topology_resilience": "topology",
        },
        "gates": gates,
    }
    if isinstance(proof, dict) and proof:
        payload["proof_pack"] = {
            "path": str(proof_path.resolve()),
            "run_status": proof.get("run_status"),
            "blocked_reason": proof.get("blocked_reason"),
        }
    deps.write_json(run_root / CERTIFICATION_RESULT_FILENAME, payload)
    return payload


def write_run_manifest(
    deps: ReportingDeps,
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    args: argparse.Namespace,
    run_context: Any,
    phases: List[str],
) -> Dict[str, Any]:
    prompt_report = deps.promptset_fingerprint(phases)
    run_blocked = bool(prompt_report.get("blocked_promptset"))
    layout = deps.current_output_layout(root)
    routing_policy = str(getattr(args, "routing_policy", deps.default_routing_policy))
    disable_escalation = bool(getattr(args, "disable_escalation", False))
    escalation_max_hops = int(getattr(args, "escalation_max_hops", 2))
    batch_mode = bool(getattr(args, "batch_mode", False))
    batch_submit_only = bool(getattr(args, "batch_submit_only", False))
    batch_watch = bool(getattr(args, "batch_watch", False))
    batch_provider = str(getattr(args, "batch_provider", "auto"))
    batch_poll_seconds = int(getattr(args, "batch_poll_seconds", 30))
    batch_wait_timeout_seconds = int(getattr(args, "batch_wait_timeout_seconds", 86400))
    batch_max_requests_per_job = int(getattr(args, "batch_max_requests_per_job", 2000))
    manifest = {
        "run_id": run_id,
        "generated_at": deps.now_iso(),
        "repo_root": str(root.resolve()),
        "artifact_root": str(layout.extraction_root.resolve()),
        "run_root": str(dirs["root"].resolve()),
        "git_sha": deps.get_git_sha(root),
        "cli": {
            "phase": args.phase if args.phase else args.verify_phase_output,
            "preset": getattr(args, "preset", None),
            "preset_stage": getattr(args, "preset_stage", None),
            "skip_pre_live_validator": bool(getattr(args, "skip_pre_live_validator", False)),
            "dry_run": args.dry_run,
            "resume": args.resume,
            "max_files_docs": args.max_files_docs,
            "max_files_code": args.max_files_code,
            "max_chars": args.max_chars,
            "max_request_bytes": args.max_request_bytes,
            "file_truncate_chars": args.file_truncate_chars,
            "home_scan_mode": args.home_scan_mode,
            "fail_fast_auth": args.fail_fast_auth,
            "gemini_auth_mode": args.gemini_auth_mode,
            "gemini_model_id": args.gemini_model_id,
            "gemini_transport": args.gemini_transport,
            "openai_transport": args.openai_transport,
            "xai_transport": args.xai_transport,
            "s_prompts": getattr(args, "s_prompts", deps.s_prompts_legacy),
            "retry_policy": args.retry_policy,
            "retry_max_attempts": args.retry_max_attempts,
            "retry_base_seconds": args.retry_base_seconds,
            "retry_max_seconds": args.retry_max_seconds,
            "phase_auth_fail_threshold": args.phase_auth_fail_threshold,
            "partition_workers": args.partition_workers,
            "routing_policy": routing_policy,
            "disable_escalation": disable_escalation,
            "escalation_max_hops": escalation_max_hops,
            "batch_mode": batch_mode,
            "batch_submit_only": batch_submit_only,
            "batch_watch": batch_watch,
            "batch_provider": batch_provider,
            "batch_poll_seconds": batch_poll_seconds,
            "batch_wait_timeout_seconds": batch_wait_timeout_seconds,
            "batch_max_requests_per_job": batch_max_requests_per_job,
            "debug_phase_inputs": args.debug_phase_inputs,
            "fail_fast_missing_inputs": args.fail_fast_missing_inputs,
            "run_id_override": args.run_id,
            "run_id_source": run_context.source,
            "max_cost_usd": args.max_cost_usd,
            "run_id_resolution_precedence": [
                "explicit(--run-id)",
                f"implicit({layout.latest_run_file})",
                "generated(new timestamp run id)",
            ],
            "no_write_latest": args.no_write_latest,
            "write_latest_even_on_dry_run": args.write_latest_even_on_dry_run,
            "latest_run_id_written": run_context.latest_written,
            "latest_run_id_file": str(run_context.latest_file.resolve()),
            "doctor": args.doctor,
            "doctor_auth": args.doctor_auth,
            "preflight_providers": args.preflight_providers,
            "coverage_report": args.coverage_report,
            "ui": args.ui,
            "quiet": args.quiet,
            "jsonl_events": args.jsonl_events,
            "pretty": args.pretty,
            "print_promptpack": args.print_promptpack,
            "print_run_order": bool(getattr(args, "print_run_order", False)),
            "print_phase_routing": bool(getattr(args, "print_phase_routing", False)),
            "print_routing_guide": bool(getattr(args, "print_routing_guide", False)),
            "print_prescan_guide": bool(getattr(args, "print_prescan_guide", False)),
            "print_cost_preview": bool(getattr(args, "print_cost_preview", False)),
            "print_phase_prompts": getattr(args, "print_phase_prompts", None),
            "verify_phase_output": args.verify_phase_output,
            "print_config": args.print_config,
            "output_root": getattr(args, "output_root", None),
            "dpmx_webhook_url": os.getenv(deps.dpmx_webhook_url_env, "").strip(),
            "dpmx_webhook_secret_set": bool(os.getenv(deps.dpmx_webhook_secret_env, "").strip()),
            "dpmx_webhook_timeout_seconds": os.getenv(deps.dpmx_webhook_timeout_seconds_env, "").strip(),
            "dpmx_webhook_required": os.getenv(deps.dpmx_webhook_required_env, "").strip(),
            "dpmx_webhook_auto_continue": os.getenv(deps.dpmx_webhook_auto_continue_env, "").strip(),
            "dpmx_live_ok": os.getenv(deps.dpmx_live_ok_env, "").strip(),
        },
        "output_layout": {
            "artifact_root": str(layout.extraction_root.resolve()),
            "runs_root": str(layout.runs_root.resolve()),
            "latest_run_id_file": str(layout.latest_run_file.resolve()),
            "doctor_root": str(layout.doctor_root.resolve()),
        },
        "prompt_hash_mode": deps.prompt_hash_mode,
        "prompt_files": [row["path"] for row in prompt_report["prompt_hashes"]],
        "prompt_missing": prompt_report["prompt_missing"],
        "prompt_unreadable": prompt_report["prompt_unreadable"],
        "prompt_hash_errors": prompt_report["prompt_hash_errors"],
        "prompt_failures": prompt_report.get("prompt_failures", []),
        "prompt_failures_count": int(prompt_report.get("prompt_failures_count", 0)),
        "promptset_sha256": prompt_report["promptset_sha256"],
        "run_status": "BLOCKED" if run_blocked else "OK",
        "phase_status": "blocked_promptset" if run_blocked else "ready",
        "blocked_promptset": run_blocked,
        "routing_policy": routing_policy,
        "routing_policy_version": deps.routing_policy_version,
        "routing_step_tiers": {
            phase: {
                spec.step_id: deps.resolve_effective_step_tier(
                    routing_policy, phase, spec.step_id, tier_override=spec.tier_override
                )
                for spec in deps.get_phase_prompts(phase)
            }
            for phase in phases
        },
        "routing_ladders": deps.routing_ladders_payload(),
        "batch_config": {
            "enabled": batch_mode,
            "submit_only": batch_submit_only,
            "watch_mode": batch_watch,
            "provider": batch_provider,
            "poll_seconds": batch_poll_seconds,
            "wait_timeout_seconds": batch_wait_timeout_seconds,
            "max_requests_per_job": batch_max_requests_per_job,
        },
        "effective_model_routing": deps.effective_model_routing_payload(),
        "benchmark_route_ownership": deps.benchmark_route_ownership_payload(validate=False),
    }
    if run_blocked:
        manifest["blocked_reason"] = deps.promptset_blocked_reason
        manifest["blocked"] = deps.blocked_promptset_payload(prompt_report, at="preflight")
    deps.write_json(dirs["root"] / "RUN_MANIFEST.json", manifest)
    deps.refresh_run_manifest_artifacts(dirs["root"], dirs)
    return prompt_report


def update_run_manifest_promptset_block(
    deps: ReportingDeps,
    run_root: Path,
    phase: str,
    prompt_report: Dict[str, Any],
) -> None:
    manifest_path = run_root / "RUN_MANIFEST.json"
    payload: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            payload = deps.load_json(manifest_path)
        except Exception:
            payload = {}
    payload["run_status"] = "BLOCKED"
    payload["phase_status"] = "blocked_promptset"
    payload["blocked_promptset"] = True
    payload["blocked_reason"] = deps.promptset_blocked_reason
    payload["blocked_phase"] = phase
    payload["blocked_prompts_missing"] = prompt_report.get("prompt_missing", [])
    payload["blocked_prompts_unreadable"] = prompt_report.get("prompt_unreadable", [])
    payload["blocked_prompt_hash_errors"] = prompt_report.get("prompt_hash_errors", [])
    payload["prompt_failures"] = prompt_report.get("prompt_failures", [])
    payload["prompt_failures_count"] = int(prompt_report.get("prompt_failures_count", 0))
    payload["blocked"] = deps.blocked_promptset_payload(prompt_report, at="phase_execution")
    payload["prompt_hash_mode"] = deps.prompt_hash_mode
    payload["promptset_sha256"] = None
    payload["updated_at"] = deps.now_iso()
    deps.write_json(manifest_path, payload)


def write_promptset_blocked_marker(
    deps: ReportingDeps,
    phase: str,
    phase_dir: Path,
    prompt_report: Dict[str, Any],
) -> None:
    payload = {
        "generated_at": deps.now_iso(),
        "phase": phase,
        "status": "blocked_promptset",
        "blocked_reason": deps.promptset_blocked_reason,
        "prompt_hash_mode": deps.prompt_hash_mode,
        "promptset_sha256": None,
        "prompt_hashes": prompt_report.get("prompt_hashes", []),
        "prompt_missing": prompt_report.get("prompt_missing", []),
        "prompt_unreadable": prompt_report.get("prompt_unreadable", []),
        "prompt_hash_errors": prompt_report.get("prompt_hash_errors", []),
        "prompt_failures": prompt_report.get("prompt_failures", []),
        "missing_prompts_count": int(prompt_report.get("missing_prompts_count", 0)),
        "unreadable_prompts_count": int(prompt_report.get("unreadable_prompts_count", 0)),
        "prompt_failures_count": int(prompt_report.get("prompt_failures_count", 0)),
    }
    deps.write_json(phase_dir / "qa" / f"PHASE_{phase}_BLOCKED_PROMPTSET.json", payload)


def write_phase_coverage_manifest(
    deps: ReportingDeps,
    phase: str,
    phase_dir: Path,
    *,
    selected_step_ids: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    prompts = deps.get_phase_prompts(phase)
    if selected_step_ids:
        upper_selected = {str(sid).strip().upper() for sid in selected_step_ids if str(sid).strip()}
        prompts = [p for p in prompts if p.step_id.upper() in upper_selected]
    expected_outputs = {spec.step_id: list(spec.output_artifacts) for spec in prompts}
    prompt_declared_outputs = sorted({artifact for artifacts in expected_outputs.values() for artifact in artifacts})
    raw_dir = phase_dir / "raw"
    norm_dir = phase_dir / "norm"
    blocked_path = phase_dir / "qa" / f"PHASE_{phase}_BLOCKED_PROMPTSET.json"
    blocked_payload = deps.load_json(blocked_path)
    blocked_promptset = blocked_payload.get("status") == "blocked_promptset" if isinstance(blocked_payload, dict) else False
    missing_prompts_count = int(blocked_payload.get("missing_prompts_count", 0)) if blocked_promptset else 0
    unreadable_prompts_count = int(blocked_payload.get("unreadable_prompts_count", 0)) if blocked_promptset else 0
    qa_rows = deps.read_step_qa_payloads(phase_dir)
    qa_by_step: Dict[str, Dict[str, Any]] = {
        str(row.get("step_id")): row
        for row in qa_rows
        if isinstance(row, dict) and row.get("step_id")
    }
    observed_raw = sorted(entry.name for entry in raw_dir.iterdir() if entry.is_file()) if raw_dir.exists() else []
    observed_norm = sorted(entry.name for entry in norm_dir.iterdir() if entry.is_file()) if norm_dir.exists() else []
    undeclared_observed_outputs = sorted([name for name in observed_norm if name not in prompt_declared_outputs])
    counts = {
        "ok": 0,
        "failed": 0,
        "skipped": 0,
        "dry_run": 0,
        "blocked_promptset": 1 if blocked_promptset else 0,
        "missing_prompts_count": missing_prompts_count,
        "unreadable_prompts_count": unreadable_prompts_count,
    }
    contract_metrics_by_step: Dict[str, Dict[str, Any]] = {}
    contract_lane_hist = Counter()
    missing_expected_hist = Counter()
    repair_invocations_total = 0
    repair_successes_total = 0
    sidefill_invocations_total = 0
    for row in qa_rows:
        row_recomputed = int(row.get("recomputed_partitions", 0))
        row_failed = int(row.get("execution_failed_partitions", row.get("raw_failed", 0)))
        row_skipped = int(row.get("resume_skipped_partitions", 0))
        row_dry_run = int(row.get("dry_run_partitions", 0))
        row_ok = max(0, row_recomputed - row_failed - row_dry_run)
        counts["ok"] += row_ok
        counts["failed"] += row_failed
        counts["skipped"] += row_skipped
        counts["dry_run"] += row_dry_run
        step_id = str(row.get("step_id") or "")
        lane = str(row.get("contract_lane") or "").strip()
        if lane:
            contract_lane_hist[lane] += 1
        for artifact_name in row.get("missing_expected_artifacts", []) or []:
            token = str(artifact_name).strip()
            if token:
                missing_expected_hist[token] += 1
        repair_invocations_total += int(row.get("repair_invocations", 0) or 0)
        repair_successes_total += int(row.get("repair_successes", 0) or 0)
        sidefill_invocations_total += int(row.get("sidefill_invocations", 0) or 0)
        if step_id:
            contract_metrics_by_step[step_id] = {
                "contract_lane": lane or None,
                "strict_schema_required": bool(row.get("strict_schema_required", False)),
                "repair_invocations": int(row.get("repair_invocations", 0) or 0),
                "repair_successes": int(row.get("repair_successes", 0) or 0),
                "sidefill_invocations": int(row.get("sidefill_invocations", 0) or 0),
                "sidefill_filled_artifacts": list(row.get("sidefill_filled_artifacts", []) or []),
                "failure_stage_histogram": dict(
                    sorted(
                        (row.get("failure_stage_histogram", {}) if isinstance(row.get("failure_stage_histogram"), dict) else {}).items()
                    )
                ),
                "schema_id_normalizations": int(row.get("schema_id_normalizations", 0) or 0),
                "final_contract_status": row.get("final_contract_status"),
            }
    missing_required: List[Dict[str, str]] = []
    missing_reason_counts = {
        "failed": 0,
        "skipped_resume": 0,
        "dry_run": 0,
        "blocked_promptset": 1 if blocked_promptset else 0,
        "prompt_does_not_declare_it": 0,
        "pre_model_execution": 0,
        "model_execution": 0,
        "post_model_output": 0,
        "unknown": 0,
    }
    for step_id, artifacts in expected_outputs.items():
        step_row = qa_by_step.get(step_id, {})
        step_expected = set(step_row.get("expected_artifacts", [])) if isinstance(step_row, dict) else set()
        step_failed = int(step_row.get("execution_failed_partitions", step_row.get("raw_failed", 0))) if isinstance(step_row, dict) else 0
        step_skipped = int(step_row.get("resume_skipped_partitions", 0)) if isinstance(step_row, dict) else 0
        step_dry_run = int(step_row.get("dry_run_partitions", 0)) if isinstance(step_row, dict) else 0
        blocked_by_stage = (
            step_row.get("artifact_blocked_by_failure_stage", {})
            if isinstance(step_row, dict) and isinstance(step_row.get("artifact_blocked_by_failure_stage"), dict)
            else {}
        )
        for artifact_name in artifacts:
            if not deps.expected_artifact_present(norm_dir, artifact_name):
                reason = "unknown"
                if artifact_name not in step_expected and step_row:
                    reason = "prompt_does_not_declare_it"
                elif step_dry_run > 0:
                    reason = "dry_run"
                elif any(artifact_name in artifact_list for artifact_list in blocked_by_stage.values() if isinstance(artifact_list, list)):
                    for stage_name, artifact_list in blocked_by_stage.items():
                        if artifact_name in artifact_list:
                            reason = str(stage_name or "execution_failure")
                            break
                elif step_failed > 0:
                    reason = "failed"
                elif step_skipped > 0:
                    reason = "skipped_resume"
                missing_required.append({"step_id": step_id, "artifact": artifact_name, "reason": reason})
                missing_reason_counts[reason] += 1
    coverage = deps.coverage_for_phase(phase, phase_dir)
    payload = {
        "generated_at": deps.now_iso(),
        "phase": phase,
        "expected_outputs": expected_outputs,
        "prompt_declared_outputs": prompt_declared_outputs,
        "observed_outputs": {
            "raw": observed_raw,
            "norm": observed_norm,
            "undeclared_norm": undeclared_observed_outputs,
        },
        "counts": counts,
        "missing_required_artifacts": missing_required,
        "missing_required_artifacts_by_reason": missing_reason_counts,
        "response_parse_repairs": coverage.get("response_parse_repairs", {}),
        "contract_metrics": {
            "steps": contract_metrics_by_step,
            "lane_histogram": dict(sorted(contract_lane_hist.items())),
            "repair_invocations_total": repair_invocations_total,
            "repair_successes_total": repair_successes_total,
            "schema_repair_counters": deps.read_repair_counters(),
            "sidefill_invocations_total": sidefill_invocations_total,
            "missing_expected_artifacts_histogram": dict(sorted(missing_expected_hist.items())),
        },
        "blocked_promptset": {
            "status": "BLOCKED" if blocked_promptset else "CLEAR",
            "missing_prompts_count": missing_prompts_count,
            "unreadable_prompts_count": unreadable_prompts_count,
            "prompt_missing": blocked_payload.get("prompt_missing", []) if blocked_promptset else [],
            "prompt_unreadable": blocked_payload.get("prompt_unreadable", []) if blocked_promptset else [],
        },
        "status": "FAIL" if blocked_promptset or missing_required or counts.get("failed", 0) > 0 else "PASS",
    }
    deps.write_json(phase_dir / "qa" / f"PHASE_{phase}_COVERAGE.json", payload)
    return payload


def write_coverage_rollup(
    deps: ReportingDeps,
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    promptset_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    del root
    blocked_promptset = bool((promptset_report or {}).get("blocked_promptset"))
    if blocked_promptset:
        payload = {
            "generated_at": deps.now_iso(),
            "run_id": run_id,
            "phases": {},
            "missing_required_artifacts_total": 0,
            "run_status": "BLOCKED",
            "blocked_reason": deps.promptset_blocked_reason,
            "blocked_promptset": True,
            "prompt_failures_count": int((promptset_report or {}).get("prompt_failures_count", 0)),
            "phases_executed_count": 0,
        }
        deps.write_json(dirs["root"] / COVERAGE_ROLLUP_FILENAME, payload)
        deps.write_strict_passthrough_attestations(dirs, run_id, [])
        return payload
    phase_rollup: Dict[str, Any] = {}
    missing_total = 0
    repair_total = 0
    repair_events = []
    disposition_hist = Counter()
    for phase in deps.phases:
        coverage_path = dirs[phase] / "qa" / f"PHASE_{phase}_COVERAGE.json"
        if not coverage_path.exists():
            continue
        payload = deps.load_json(coverage_path)
        missing = payload.get("missing_required_artifacts")
        missing_count = len(missing) if isinstance(missing, list) else 0
        missing_total += missing_count
        repairs = payload.get("response_parse_repairs", {})
        repair_total += int(repairs.get("events_total", 0))
        repair_events.extend(repairs.get("events", []))
        hist = repairs.get("final_disposition_histogram", {})
        if isinstance(hist, dict):
            for key, value in hist.items():
                disposition_hist[key] += int(value)
        phase_rollup[phase] = {
            "status": payload.get("status", "UNKNOWN"),
            "missing_required_artifacts_count": missing_count,
            "missing_required_artifacts": missing if isinstance(missing, list) else [],
            "counts": payload.get("counts", {}),
            "contract_metrics": payload.get("contract_metrics", {}),
            "blocked_promptset": payload.get("blocked_promptset", {}),
            "response_parse_repairs": repairs,
            "coverage_file": str(coverage_path.resolve()),
        }
    cost_abort_triggered = deps.is_cost_abort_triggered()
    payload = {
        "generated_at": deps.now_iso(),
        "run_id": run_id,
        "phases": phase_rollup,
        "missing_required_artifacts_total": missing_total,
        "response_parse_repairs": {
            "events_total": repair_total,
            "events": repair_events,
            "final_disposition_histogram": dict(sorted(disposition_hist.items())),
        },
        "run_status": deps.compute_run_status(
            blocked_promptset=blocked_promptset,
            missing_required_artifacts_total=missing_total,
            phase_statuses={phase: value["status"] for phase, value in phase_rollup.items()},
            cost_abort_triggered=cost_abort_triggered,
        ),
        "blocked_reason": deps.promptset_blocked_reason if blocked_promptset else None,
        "blocked_promptset": blocked_promptset,
        "prompt_failures_count": int((promptset_report or {}).get("prompt_failures_count", 0)),
        "phases_executed_count": 0 if blocked_promptset else len(phase_rollup),
    }
    deps.write_json(dirs["root"] / COVERAGE_ROLLUP_FILENAME, payload)
    deps.update_run_manifest_status(
        dirs["root"],
        blocked_promptset=blocked_promptset,
        missing_required_artifacts_total=missing_total,
        phase_statuses={phase: value["status"] for phase, value in phase_rollup.items()},
    )
    deps.write_strict_passthrough_attestations(dirs, run_id, list(phase_rollup.keys()))
    return payload


def write_resume_proof(
    deps: ReportingDeps,
    dirs: Dict[str, Path],
    run_id: str,
    phases: Iterable[str],
    promptset_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    active_phases = sorted(set(phases))
    per_phase: Dict[str, Any] = {}
    total_skipped = 0
    total_recomputed = 0
    for phase in deps.phases:
        phase_dir = dirs[phase]
        inventory_path = phase_dir / "inputs" / "INVENTORY.json"
        partitions_path = phase_dir / "inputs" / "PARTITIONS.json"
        qa_rows = deps.read_step_qa_payloads(phase_dir)
        skipped = sum(int(row.get("resume_skipped_partitions", 0)) for row in qa_rows)
        recomputed = sum(int(row.get("recomputed_partitions", 0)) for row in qa_rows)
        if not qa_rows and not inventory_path.exists() and not partitions_path.exists():
            continue
        total_skipped += skipped
        total_recomputed += recomputed
        per_phase[phase] = {
            "resume_skipped_partitions": skipped,
            "recomputed_partitions": recomputed,
            "inventory_sha256": deps.sha256_text(inventory_path) if inventory_path.exists() else None,
            "partitions_sha256": deps.sha256_text(partitions_path) if partitions_path.exists() else None,
            "inventory_file": str(inventory_path.resolve()) if inventory_path.exists() else None,
            "partitions_file": str(partitions_path.resolve()) if partitions_path.exists() else None,
        }
    promptset = promptset_report if promptset_report is not None else deps.promptset_fingerprint(active_phases)
    blocked_promptset = bool(promptset.get("blocked_promptset"))
    cost_abort_triggered = deps.is_cost_abort_triggered()
    missing_total = 0
    phase_statuses: Dict[str, str] = {}
    for phase in active_phases:
        coverage_path = dirs[phase] / "qa" / f"PHASE_{phase}_COVERAGE.json"
        if coverage_path.exists():
            try:
                coverage_payload = deps.load_json(coverage_path)
                missing = coverage_payload.get("missing_required_artifacts", [])
                missing_total += len(missing)
                phase_statuses[phase] = coverage_payload.get("status", "UNKNOWN")
            except Exception:
                pass
    run_status = deps.compute_run_status(
        blocked_promptset=blocked_promptset,
        missing_required_artifacts_total=missing_total,
        phase_statuses=phase_statuses,
        cost_abort_triggered=cost_abort_triggered,
    )
    payload = {
        "generated_at": deps.now_iso(),
        "run_id": run_id,
        "active_phases": active_phases,
        "resume_status": "ready" if run_status == "OK" else "blocked",
        "run_status": run_status,
        "cost_abort_triggered": cost_abort_triggered,
        "totals": {
            "resume_skipped_partitions": total_skipped,
            "recomputed_partitions": total_recomputed,
        },
        "phases": per_phase,
        "prompt_hash_mode": promptset["prompt_hash_mode"],
        "promptset_sha256": promptset["promptset_sha256"],
        "prompt_hashes": promptset["prompt_hashes"],
        "prompt_missing": promptset["prompt_missing"],
        "prompt_unreadable": promptset["prompt_unreadable"],
        "prompt_hash_errors": promptset["prompt_hash_errors"],
        "prompt_failures": promptset.get("prompt_failures", []),
        "blocked_promptset": promptset["blocked_promptset"],
        "missing_prompts_count": promptset["missing_prompts_count"],
        "unreadable_prompts_count": promptset["unreadable_prompts_count"],
        "prompt_failures_count": promptset.get("prompt_failures_count", 0),
    }
    if blocked_promptset:
        payload["blocked_reason"] = deps.promptset_blocked_reason
        payload["blocked"] = deps.resume_blocked_payload(promptset)
    deps.write_json(dirs["root"] / RESUME_PROOF_FILENAME, payload)
    return payload


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
    deps.refresh_run_manifest_artifacts(dirs["root"], dirs)
    proof_path = dirs["root"] / PROOF_PACK_FILENAME
    proof: Dict[str, Any] = {}
    if proof_path.exists():
        try:
            proof = deps.load_json(proof_path)
        except Exception:
            proof = {}
    proof["run_id"] = run_id
    proof["git_sha"] = deps.get_git_sha(root)
    proof["runner_sha256"] = deps.sha256_text(deps.runner_script)
    proof["argv"] = sys.argv
    proof["python_version"] = platform.python_version()
    proof["cwd"] = str(root.resolve())
    proof["started_at"] = run_started_at
    proof.setdefault("phases", {})[phase] = {
        "started_at": phase_started_at,
        "finished_at": phase_finished_at,
        "counts": phase_counts,
    }
    proof["finished_at"] = phase_finished_at
    proof["updated_at"] = deps.now_iso()
    doctor_dir = deps.current_doctor_root(root)
    auth_doctor = doctor_dir / "AUTH_DOCTOR.json"
    full_doctor = doctor_dir / "DOCTOR_FULL.json"
    routing_fp = dirs["root"] / "RUN_ROUTING_FINGERPRINT.json"
    coverage_rollup = dirs["root"] / COVERAGE_ROLLUP_FILENAME
    resume_proof = dirs["root"] / RESUME_PROOF_FILENAME
    proof["linked_artifacts"] = {
        "coverage_rollup": str(coverage_rollup.resolve()) if coverage_rollup.exists() else None,
        "resume_proof": str(resume_proof.resolve()) if resume_proof.exists() else None,
        "run_routing_fingerprint": str(routing_fp.resolve()) if routing_fp.exists() else None,
        "doctor_auth": str(auth_doctor.resolve()) if auth_doctor.exists() else None,
        "doctor_full": str(full_doctor.resolve()) if full_doctor.exists() else None,
    }
    deps.write_json(proof_path, proof)


def write_blocked_promptset_proof_pack(
    deps: ReportingDeps,
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    run_started_at: str,
    phases: List[str],
    prompt_report: Dict[str, Any],
) -> None:
    deps.refresh_run_manifest_artifacts(dirs["root"], dirs)
    proof_path = dirs["root"] / PROOF_PACK_FILENAME
    proof: Dict[str, Any] = {}
    if proof_path.exists():
        try:
            proof = deps.load_json(proof_path)
        except Exception:
            proof = {}
    blocked_at = deps.now_iso()
    coverage_rollup = dirs["root"] / COVERAGE_ROLLUP_FILENAME
    resume_proof = dirs["root"] / RESUME_PROOF_FILENAME
    routing_fp = dirs["root"] / "RUN_ROUTING_FINGERPRINT.json"
    proof["run_id"] = run_id
    proof["git_sha"] = deps.get_git_sha(root)
    proof["runner_sha256"] = deps.sha256_text(deps.runner_script)
    proof["argv"] = sys.argv
    proof["python_version"] = platform.python_version()
    proof["cwd"] = str(root.resolve())
    proof["started_at"] = run_started_at
    proof["finished_at"] = blocked_at
    proof["updated_at"] = blocked_at
    proof["run_status"] = "BLOCKED"
    proof["blocked_reason"] = deps.promptset_blocked_reason
    proof["blocked"] = deps.blocked_promptset_payload(prompt_report, at="preflight")
    proof["phases"] = {phase: {"status": "NOT_EXECUTED"} for phase in phases}
    proof["linked_artifacts"] = {
        "coverage_rollup": str(coverage_rollup.resolve()) if coverage_rollup.exists() else None,
        "resume_proof": str(resume_proof.resolve()) if resume_proof.exists() else None,
        "run_routing_fingerprint": str(routing_fp.resolve()) if routing_fp.exists() else None,
    }
    deps.write_json(proof_path, proof)
