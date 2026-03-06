from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PHASE_CODES = ["A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z"]
DOCTOR_REPROCESS_PLAN_FILENAME = "DOCTOR_REPROCESS_PLAN.json"
STRICT_CONTRACT_STEPS = {("D", "D0"), ("D", "D1")}

try:
    from lib.phase_contract_map import get_step_contract
except Exception:  # pragma: no cover - keep policy usable in isolated contexts
    get_step_contract = None  # type: ignore[assignment]


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _phase_dirs_from_run(run_dir: Path) -> Dict[str, Path]:
    phase_dirs: Dict[str, Path] = {}
    for entry in sorted(run_dir.iterdir()):
        if not entry.is_dir():
            continue
        phase = entry.name.split("_", 1)[0]
        if phase in PHASE_CODES and phase not in phase_dirs:
            phase_dirs[phase] = entry
    return phase_dirs


def _is_strict_contract_step(phase: str, step_id: str) -> bool:
    phase_code = str(phase or "").strip().upper()
    step_code = str(step_id or "").strip().upper()
    if get_step_contract is not None:
        try:
            row = get_step_contract(phase_code, step_code)
        except Exception:
            row = None
        if isinstance(row, dict):
            lane = row.get("lane") if isinstance(row.get("lane"), dict) else {}
            return bool(lane.get("strict_schema_required"))
    return (phase_code, step_code) in STRICT_CONTRACT_STEPS


def _shape_map(parse_shapes_payload: Dict[str, Any]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    mapping: Dict[Tuple[str, str], Dict[str, Any]] = {}
    rows = parse_shapes_payload.get("rows")
    if not isinstance(rows, list):
        return mapping
    for row in rows:
        if not isinstance(row, dict):
            continue
        step_id = str(row.get("step_id") or "").strip()
        partition_id = str(row.get("partition_id") or "").strip()
        if not step_id or not partition_id:
            continue
        mapping[(step_id, partition_id)] = dict(row)
    return mapping


def _final_failure_map(request_meta_payload: Dict[str, Any]) -> Dict[Tuple[str, str], str]:
    mapping: Dict[Tuple[str, str], str] = {}
    rows = request_meta_payload.get("rows")
    if not isinstance(rows, list):
        return mapping
    for row in rows:
        if not isinstance(row, dict):
            continue
        step_id = str(row.get("step_id") or "").strip()
        partition_id = str(row.get("partition_id") or "").strip()
        if not step_id or not partition_id:
            continue
        mapping[(step_id, partition_id)] = str(row.get("final_failure_type") or "unknown_failure")
    return mapping


def decide_action(
    *,
    final_failure_type: str,
    parse_shape: Optional[str],
    parse_shape_row: Optional[Dict[str, Any]] = None,
    phase: Optional[str] = None,
    step_id: Optional[str] = None,
    schema_reason: Optional[str] = None,
) -> Dict[str, Any]:
    failure = str(final_failure_type or "unknown_failure")
    shape = str(parse_shape or "unknown")
    shape_row = parse_shape_row if isinstance(parse_shape_row, dict) else {}
    phase_code = str(phase or "").strip().upper()
    step_code = str(step_id or "").strip().upper()
    schema_token = str(schema_reason or "").strip()
    is_strict_contract_step = _is_strict_contract_step(phase_code, step_code)
    if failure in {"auth", "auth_rejected", "api_key_missing_or_invalid"}:
        return {
            "action": "manual_auth_fix",
            "rerun": False,
            "notes": "Run doctor-auth and fix credentials before rerun.",
        }
    if failure in {"quota_or_billing", "rate_limit"}:
        return {
            "action": "rerun_conservative",
            "rerun": True,
            "partition_workers": 1,
            "notes": "Rerun with deterministic low-concurrency settings.",
        }
    if failure == "parse":
        if shape in {"truncated_string", "truncated_container"}:
            return {
                "action": "rerun_shrink_on_truncation",
                "rerun": True,
                "partition_workers": 1,
                "notes": "Runner shrink lane will halve file set deterministically.",
            }
        if shape == "other":
            has_unmatched_closer = bool(shape_row.get("has_unmatched_closer")) or int(
                shape_row.get("unmatched_closer_count") or 0
            ) > 0
            has_unclosed_container = bool(shape_row.get("has_unclosed_container")) or int(
                shape_row.get("unclosed_container_count") or 0
            ) > 0
            has_in_string_unclosed = bool(shape_row.get("in_string_unclosed"))
            has_odd_quotes = int(shape_row.get("quotes_mod2") or 0) == 1
            if has_unmatched_closer or has_unclosed_container or has_in_string_unclosed or has_odd_quotes:
                return {
                    "action": "rerun_shrink_on_malformed",
                    "rerun": True,
                    "partition_workers": 1,
                    "notes": "Runner shrink lane handles other/unbalanced parse failures deterministically.",
                }
            return {
                "action": "rerun_parse_other_once",
                "rerun": True,
                "partition_workers": 1,
                "notes": "Retry parse=other once; escalate to manual review if unchanged.",
            }
        if shape in {"multi_json", "fence_wrapped", "preamble", "suffix_only_closer_junk"}:
            return {
                "action": "rerun_parse_repair",
                "rerun": True,
                "partition_workers": 1,
                "notes": "Rerun once and rely on deterministic parse-repair lanes.",
            }
    if failure in {"missing_success_json", "io_persist"}:
        return {
            "action": "rerun_regenerate_success",
            "rerun": True,
            "partition_workers": 1,
            "notes": "Regenerate success artifact and clean stale sidecars.",
        }
    if failure in {"schema", "contract_violation"}:
        # NOTE: This logic is tightly coupled to the error message format.
        # If the schema validation reason for missing artifacts changes, this check must be updated.
        if is_strict_contract_step and "missing_expected_artifacts:" in schema_token:
            return {
                "action": "sidefill_missing_artifacts",
                "rerun": True,
                "partition_workers": 1,
                "notes": "Run strict sidefill for missing expected artifacts before full rerun.",
            }
        if is_strict_contract_step:
            return {
                "action": "strict_contract_rerun",
                "rerun": True,
                "partition_workers": 1,
                "notes": "Rerun strict contract emitter with targeted repair lane.",
            }
        return {
            "action": "rerun_once_then_manual",
            "rerun": True,
            "partition_workers": 1,
            "notes": "If still failing, escalate for prompt/schema contract changes.",
        }
    return {
        "action": "manual_review",
        "rerun": False,
        "notes": "No deterministic automated action for this failure class yet.",
    }


def build_phase_reprocess_plan(phase: str, phase_dir: Path, run_id: str) -> Dict[str, Any]:
    qa_dir = phase_dir / "qa"
    rollup = _load_json(qa_dir / "PHASE_FAILURE_ROLLUP.json")
    parse_shapes = _load_json(qa_dir / "PARSE_FAILURE_SHAPES.json")
    request_meta_index = _load_json(qa_dir / "PHASE_REQUEST_META_INDEX.json")

    shape_by_partition = _shape_map(parse_shapes)
    final_failure_by_partition = _final_failure_map(request_meta_index)
    failures = rollup.get("failures")
    if not isinstance(failures, list):
        failures = []

    rows: List[Dict[str, Any]] = []
    rerun_partitions: List[str] = []
    action_hist = Counter()
    failure_hist = Counter()

    for failure_row in failures:
        if not isinstance(failure_row, dict):
            continue
        step_id = str(failure_row.get("step_id") or "").strip()
        partition_id = str(failure_row.get("partition_id") or "").strip()
        if not step_id or not partition_id:
            continue
        fallback_failure = str(
            failure_row.get("resolved_cause")
            or failure_row.get("validation_reason")
            or "unknown_failure"
        )
        final_failure_type = final_failure_by_partition.get((step_id, partition_id), fallback_failure)
        shape_row = shape_by_partition.get((step_id, partition_id), {})
        shape = str(shape_row.get("shape") or "other") if isinstance(shape_row, dict) else None
        schema_reason = str(failure_row.get("validation_reason") or "").strip()
        if not schema_reason and isinstance(shape_row, dict):
            schema_reason = str(shape_row.get("schema_gate_reason") or "").strip()
        action = decide_action(
            final_failure_type=final_failure_type,
            parse_shape=shape,
            parse_shape_row=shape_row,
            phase=phase,
            step_id=step_id,
            schema_reason=schema_reason,
        )
        row = {
            "phase": phase,
            "step_id": step_id,
            "partition_id": partition_id,
            "final_failure_type": final_failure_type,
            "parse_shape": shape,
            "schema_reason": schema_reason or None,
            **action,
        }
        rows.append(row)
        action_hist[str(action.get("action"))] += 1
        failure_hist[final_failure_type] += 1
        if action.get("rerun"):
            rerun_partitions.append(partition_id)

    rerun_partitions = sorted(set(rerun_partitions))
    return {
        "run_id": run_id,
        "phase": phase,
        "phase_dir": str(phase_dir.resolve()),
        "plan_rows": rows,
        "rerun_partitions": rerun_partitions,
        "action_histogram": dict(sorted(action_hist.items())),
        "final_failure_histogram": dict(sorted(failure_hist.items())),
        "total_failures": len(rows),
    }


def build_run_reprocess_plan(
    *,
    run_dir: Path,
    run_id: str,
    phases: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    phase_dirs = _phase_dirs_from_run(run_dir)
    target_phases = list(phases or sorted(phase_dirs.keys()))
    payload_phases: Dict[str, Any] = {}
    total_failures = 0
    total_rerun_partitions = 0
    action_hist = Counter()

    for phase in target_phases:
        phase_dir = phase_dirs.get(phase)
        if phase_dir is None:
            continue
        phase_plan = build_phase_reprocess_plan(phase, phase_dir, run_id)
        payload_phases[phase] = phase_plan
        total_failures += int(phase_plan.get("total_failures", 0))
        total_rerun_partitions += len(phase_plan.get("rerun_partitions", []))
        for action, count in phase_plan.get("action_histogram", {}).items():
            action_hist[str(action)] += int(count)

    return {
        "run_id": run_id,
        "run_dir": str(run_dir.resolve()),
        "phases": payload_phases,
        "summary": {
            "phases_planned": len(payload_phases),
            "total_failures": total_failures,
            "total_rerun_partitions": total_rerun_partitions,
            "action_histogram": dict(sorted(action_hist.items())),
        },
    }


def write_doctor_reprocess_plan(run_dir: Path, payload: Dict[str, Any]) -> Path:
    doctor_dir = run_dir.parents[1] / "doctor"
    doctor_dir.mkdir(parents=True, exist_ok=True)
    out_path = doctor_dir / DOCTOR_REPROCESS_PLAN_FILENAME
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return out_path
