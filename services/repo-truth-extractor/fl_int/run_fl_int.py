from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .collect_input import collect_input_bundle
from .fl_int_paths import ensure_fl_int_dirs
from .models import FL_INT_STEPS, FLIntStep
from .reduce_input import merge_f0_batch_payloads, merge_l0_batch_payloads, reduce_f0_input, reduce_l0_input
from .report_compiler import compile_fl_int_reports
from s_int.schema_validate import load_schema, validate_payload_or_raise
from output_safety import sanitize_text_for_output, sanitized_json_text


PromptExecutor = Callable[[FLIntStep, str, Dict[str, Any], Dict[str, Any]], Dict[str, Any]]


def _service_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _prompt_root() -> Path:
    return _service_root() / "prompts" / "phase_fl_int"


def _schema_root() -> Path:
    return _prompt_root()


def _render_prompt(step: FLIntStep, step_input: Dict[str, Any], prior_outputs: Dict[str, Any]) -> str:
    prompt_path = _prompt_root() / step.prompt_file
    text = prompt_path.read_text(encoding="utf-8")
    text = text.replace("{{FL_INT_INPUT_JSON}}", json.dumps(step_input, indent=2, sort_keys=True))
    text = text.replace("{{PRIOR_OUTPUTS_JSON}}", json.dumps(prior_outputs, indent=2, sort_keys=True))
    return text


def _normalize_items_envelope(value: Any, schema_name: str) -> Optional[Dict[str, Any]]:
    if isinstance(value, list):
        return {"schema": schema_name, "items": value}
    if not isinstance(value, dict):
        return None
    items = value.get("items")
    if not isinstance(items, list):
        return None
    normalized = dict(value)
    normalized.setdefault("schema", schema_name)
    return normalized


def _normalize_evidence_entry(
    value: Any,
    *,
    fallback_path: str,
    fallback_line_range: List[int],
) -> Optional[Dict[str, Any]]:
    if isinstance(value, str):
        excerpt = value.strip()
        if not excerpt:
            return None
        return {
            "path": fallback_path,
            "line_range": list(fallback_line_range),
            "excerpt": excerpt,
        }
    if not isinstance(value, dict):
        return None
    normalized = dict(value)
    path = str(normalized.get("path") or fallback_path or "unspecified").strip() or "unspecified"
    line_range = normalized.get("line_range")
    if not isinstance(line_range, list) or len(line_range) < 2:
        line_range = list(fallback_line_range)
    normalized["path"] = path
    normalized["line_range"] = line_range
    excerpt = normalized.get("excerpt")
    if isinstance(excerpt, str):
        normalized["excerpt"] = excerpt
    elif isinstance(normalized.get("text"), str):
        normalized["excerpt"] = str(normalized.get("text"))
    else:
        normalized["excerpt"] = ""
    return normalized


def _normalize_f0_item(row: Any) -> Any:
    if not isinstance(row, dict):
        return row
    normalized = dict(row)
    if not isinstance(normalized.get("claim_text"), str) or not str(normalized.get("claim_text") or "").strip():
        claim = normalized.get("claim")
        if isinstance(claim, str) and claim.strip():
            normalized["claim_text"] = claim
    if not isinstance(normalized.get("claim_text"), str) or not str(normalized.get("claim_text") or "").strip():
        for alias in ("name", "title"):
            value = normalized.get(alias)
            if isinstance(value, str) and value.strip():
                normalized["claim_text"] = value
                break
    if not isinstance(normalized.get("source_artifact"), str) or not str(normalized.get("source_artifact") or "").strip():
        source = normalized.get("source")
        if isinstance(source, str) and source.strip():
            normalized["source_artifact"] = source
    if not isinstance(normalized.get("source_artifact"), str) or not str(normalized.get("source_artifact") or "").strip():
        normalized["source_artifact"] = "unspecified"
    if not isinstance(normalized.get("plane"), str) or not str(normalized.get("plane") or "").strip():
        normalized["plane"] = "unspecified"

    fallback_path = str(normalized.get("path") or "unspecified").strip() or "unspecified"
    line_range = normalized.get("line_range")
    if not isinstance(line_range, list) or len(line_range) < 2:
        line_range = [0, 0]
    normalized["line_range"] = list(line_range)

    evidence = normalized.get("evidence")
    normalized_evidence: List[Dict[str, Any]] = []
    if isinstance(evidence, str):
        entry = _normalize_evidence_entry(
            evidence,
            fallback_path=fallback_path,
            fallback_line_range=normalized["line_range"],
        )
        if entry is not None:
            normalized_evidence.append(entry)
    elif isinstance(evidence, list):
        for item in evidence:
            entry = _normalize_evidence_entry(
                item,
                fallback_path=fallback_path,
                fallback_line_range=normalized["line_range"],
            )
            if entry is not None:
                normalized_evidence.append(entry)
    normalized["evidence"] = normalized_evidence
    if not isinstance(normalized.get("claim_text"), str) or not str(normalized.get("claim_text") or "").strip():
        first_excerpt = (
            str(normalized_evidence[0].get("excerpt") or "").strip()
            if normalized_evidence
            else ""
        )
        if first_excerpt:
            normalized["claim_text"] = first_excerpt
    return normalized


def _items_from_envelope(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    items = value.get("items")
    if not isinstance(items, list):
        return []
    return [row for row in items if isinstance(row, dict)]


def _derive_f4_meta(
    payload: Dict[str, Any],
    prior_outputs: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    classified_items = _items_from_envelope(
        (prior_outputs or {}).get("F1", {}).get("design_claims_classified")
    )
    contradiction_items = _items_from_envelope(
        (prior_outputs or {}).get("F2", {}).get("design_contradictions")
    )

    repo_proven_current_count = 0
    historical_count = 0
    target_count = 0
    unknown_count = 0
    for row in classified_items:
        evidence_class = str(row.get("evidence_class") or "").strip().upper()
        if evidence_class == "REPO_PROVEN_CURRENT":
            repo_proven_current_count += 1
        elif evidence_class == "HISTORICAL":
            historical_count += 1
        elif evidence_class == "TARGET":
            target_count += 1
        else:
            unknown_count += 1

    missing_evidence = payload.get("missing_evidence")
    missing_evidence_count = len(missing_evidence) if isinstance(missing_evidence, list) else 0
    contradictions = []
    for row in contradiction_items:
        contradiction_id = str(row.get("id") or "").strip()
        if not contradiction_id:
            continue
        contradictions.append(
            {
                "contradiction_id": contradiction_id,
                "status": str(row.get("status") or "UNKNOWN"),
            }
        )

    return {
        "section_summaries": [
            {
                "section_id": "current_state",
                "title": "Current State (REPO_PROVEN_CURRENT)",
                "claim_count": repo_proven_current_count,
            },
            {
                "section_id": "historical_and_target",
                "title": "Historical / Intent",
                "claim_count": historical_count + target_count,
            },
            {
                "section_id": "contradictions",
                "title": "Contradictions",
                "claim_count": len(contradictions),
            },
            {
                "section_id": "missing_evidence",
                "title": "Missing Evidence",
                "claim_count": missing_evidence_count,
            },
        ],
        "contradictions": contradictions,
        "statistics": {
            "repo_proven_current_count": repo_proven_current_count,
            "historical_count": historical_count,
            "target_count": target_count,
            "unknown_count": unknown_count,
        },
    }


def normalize_step_payload(
    step_id: str,
    payload: Dict[str, Any],
    prior_outputs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    normalized = dict(payload)
    if not isinstance(normalized.get("missing_evidence"), list):
        normalized["missing_evidence"] = []
    if not isinstance(normalized.get("status"), str):
        normalized["status"] = "OK"

    item_envelopes = {
        "F0": ("design_claims_raw", ("DESIGN_CLAIMS_RAW", "DESIGN_CLAIMS_RAW.json"), "DESIGN_CLAIMS_RAW@v1"),
        "F1": (
            "design_claims_classified",
            ("DESIGN_CLAIMS_CLASSIFIED", "DESIGN_CLAIMS_CLASSIFIED.json"),
            "DESIGN_CLAIMS_CLASSIFIED@v1",
        ),
        "F2": (
            "design_contradictions",
            ("DESIGN_CONTRADICTIONS", "DESIGN_CONTRADICTIONS.json"),
            "DESIGN_CONTRADICTIONS@v1",
        ),
        "L0": (
            "feature_candidates_raw",
            ("FEATURE_CANDIDATES_RAW", "FEATURE_CANDIDATES_RAW.json"),
            "FEATURE_CANDIDATES_RAW@v1",
        ),
        "L3": (
            "feature_ledger_routing",
            ("FEATURE_LEDGER_ROUTING", "FEATURE_LEDGER_ROUTING.json"),
            "FEATURE_LEDGER_ROUTING@v1",
        ),
    }
    envelope_spec = item_envelopes.get(step_id)
    if envelope_spec is not None:
        field_name, aliases, schema_name = envelope_spec
        value = normalized.get(field_name)
        if value is None:
            for alias in aliases:
                if alias in normalized:
                    value = normalized[alias]
                    break
        wrapped = _normalize_items_envelope(value, schema_name)
        if wrapped is not None:
            if step_id == "F0":
                wrapped = dict(wrapped)
                wrapped["items"] = [_normalize_f0_item(row) for row in list(wrapped.get("items") or [])]
            normalized[field_name] = wrapped
        return normalized

    if step_id == "L1":
        feature_value = normalized.get("feature_candidates_normalized")
        if feature_value is None:
            feature_value = normalized.get("FEATURE_CANDIDATES_NORMALIZED")
        if feature_value is None:
            feature_value = normalized.get("FEATURE_CANDIDATES_NORMALIZED.json")
        wrapped_features = _normalize_items_envelope(feature_value, "FEATURE_CANDIDATES_NORMALIZED@v1")
        if wrapped_features is not None:
            normalized["feature_candidates_normalized"] = wrapped_features

        merge_value = normalized.get("feature_merge_log")
        if merge_value is None:
            merge_value = normalized.get("FEATURE_MERGE_LOG")
        if merge_value is None:
            merge_value = normalized.get("FEATURE_MERGE_LOG.json")
        wrapped_merges = _normalize_items_envelope(merge_value, "FEATURE_MERGE_LOG@v1")
        if wrapped_merges is not None:
            normalized["feature_merge_log"] = wrapped_merges
        return normalized

    if step_id == "F4":
        if not isinstance(normalized.get("canonical_design_markdown"), str):
            for alias in ("canonical_design_markdown", "canonical_design_md", "CANONICAL_DESIGN.md", "CANONICAL_DESIGN"):
                value = normalized.get(alias)
                if isinstance(value, str):
                    normalized["canonical_design_markdown"] = value
                    break
        if not isinstance(normalized.get("canonical_design_markdown"), str):
            envelope = normalized.get("canonical_design")
            if isinstance(envelope, dict):
                for alias in ("canonical_design_markdown", "canonical_design_md", "markdown", "text"):
                    value = envelope.get(alias)
                    if isinstance(value, str):
                        normalized["canonical_design_markdown"] = value
                        break
        if not isinstance(normalized.get("meta"), dict):
            for alias in ("CANONICAL_DESIGN_META.json", "CANONICAL_DESIGN_META"):
                value = normalized.get(alias)
                if isinstance(value, dict):
                    normalized["meta"] = value
                    break
        if not isinstance(normalized.get("meta"), dict):
            normalized["meta"] = _derive_f4_meta(normalized, prior_outputs)
        return normalized

    if step_id == "L4":
        if not isinstance(normalized.get("master_feature_ledger"), dict):
            for alias in ("MASTER_FEATURE_LEDGER.json", "MASTER_FEATURE_LEDGER"):
                value = normalized.get(alias)
                if isinstance(value, dict):
                    normalized["master_feature_ledger"] = value
                    break
        return normalized

    return normalized


def _step_input_payload(
    step: FLIntStep,
    input_payload: Dict[str, Any],
    prior_outputs: Dict[str, Any],
) -> Dict[str, Any]:
    selected_phases: Dict[str, Any] = {}
    for phase_id in step.input_phase_ids:
        phase_payload = input_payload["phases"].get(phase_id)
        if isinstance(phase_payload, dict):
            selected_phases[phase_id] = phase_payload
    notes: List[str] = []
    if "X" in step.input_phase_ids and "X" not in selected_phases:
        notes.append("Optional phase X is absent for this run.")
    return {
        "schema_version": "FL_INT_STEP_INPUT_V1",
        "step_id": step.step_id,
        "run_id": input_payload["run_id"],
        "run_root": input_payload["run_root"],
        "required_phase_ids": input_payload["required_phase_ids"],
        "optional_phase_ids": input_payload["optional_phase_ids"],
        "available_phase_ids": input_payload["available_phase_ids"],
        "selected_phase_ids": sorted(selected_phases.keys()),
        "prior_step_ids": list(step.prior_step_ids),
        "upstream_phases": selected_phases,
        "notes": notes,
        "known_prior_steps": sorted(prior_outputs.keys()),
    }


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(sanitized_json_text(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(sanitize_text_for_output(text), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _request_meta_summary(meta: Dict[str, Any]) -> Dict[str, Any]:
    route_attempts = meta.get("route_attempts")
    retry_trace = meta.get("retry_trace")
    return {
        "provider": meta.get("provider"),
        "model_id": meta.get("model_id"),
        "api_key_env_requested": meta.get("api_key_env_requested"),
        "status_code": meta.get("status_code"),
        "failure_type": meta.get("failure_type"),
        "provider_error_reason": meta.get("provider_error_reason"),
        "transport": meta.get("transport"),
        "timeout_seconds": meta.get("timeout_seconds"),
        "route_hop_index": meta.get("route_hop_index"),
        "route_hop_total": meta.get("route_hop_total"),
        "response_received": meta.get("response_received"),
        "request_payload_bytes": meta.get("request_payload_bytes"),
        "route_attempts": route_attempts if isinstance(route_attempts, list) else [],
        "retry_trace": retry_trace if isinstance(retry_trace, list) else [],
    }


def _route_summary(route: Any) -> Dict[str, Any]:
    if isinstance(route, (list, tuple)) and len(route) >= 3:
        return {
            "provider": route[0],
            "model_id": route[1],
            "api_key_env": route[2],
        }
    return {
        "provider": None,
        "model_id": None,
        "api_key_env": None,
    }


def _trace_path(dirs: Dict[str, Path], batch_id: str) -> Path:
    return dirs["raw"] / f"{batch_id}_TRACE.json"


def _failure_path(dirs: Dict[str, Path], batch_id: str) -> Path:
    return dirs["raw"] / f"{batch_id}_FAILURE.json"


def _response_path(dirs: Dict[str, Path], batch_id: str) -> Path:
    return dirs["raw"] / f"{batch_id}_RESPONSE.txt"


def _append_stage(
    trace: Dict[str, Any],
    *,
    stage: str,
    started_monotonic: float,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    timestamp = _now_iso()
    history = list(trace.get("stage_history") or [])
    history.append(
        {
            "stage": stage,
            "at": timestamp,
            **(extra or {}),
        }
    )
    trace["stage"] = stage
    trace["updated_at"] = timestamp
    trace["elapsed_seconds"] = round(time.monotonic() - started_monotonic, 3)
    trace["stage_history"] = history
    if extra:
        trace.update(extra)


def _write_trace(path: Path, trace: Dict[str, Any]) -> None:
    _write_json(path, trace)


def _new_f0_trace(
    *,
    batch_id: str,
    step: FLIntStep,
    input_payload: Dict[str, Any],
    output_root: Path,
    step_input: Dict[str, Any],
    rendered_prompt: str,
    selected_chunk_count: int,
) -> Dict[str, Any]:
    return {
        "schema_version": "F0_BATCH_TRACE_V1",
        "batch_id": batch_id,
        "step_id": step.step_id,
        "run_id": input_payload["run_id"],
        "run_root": input_payload["run_root"],
        "output_root": str(output_root),
        "started_at": _now_iso(),
        "updated_at": _now_iso(),
        "elapsed_seconds": 0.0,
        "stage": "batch_start",
        "stage_history": [],
        "selected_route": _route_summary(None),
        "input_json_bytes": len(json.dumps(step_input, indent=2, sort_keys=True).encode("utf-8")),
        "rendered_prompt_chars": len(rendered_prompt),
        "selected_chunk_count": selected_chunk_count,
        "response_received": False,
        "response_text_chars": 0,
        "request_meta": {},
    }


def _write_failure_artifact(
    *,
    dirs: Dict[str, Path],
    batch_id: str,
    trace: Dict[str, Any],
    request_meta: Dict[str, Any],
    timeout_seconds: int,
    terminal_stage: str,
    route: Any,
) -> str:
    failure_payload = {
        "schema_version": "F0_BATCH_FAILURE_V1",
        "batch_id": batch_id,
        "step_id": "F0",
        "run_root": trace.get("run_root"),
        "output_root": trace.get("output_root"),
        "terminal_stage": terminal_stage,
        "failure_type": request_meta.get("failure_type"),
        "provider_error_reason": request_meta.get("provider_error_reason"),
        "status_code": request_meta.get("status_code"),
        "timeout_seconds": timeout_seconds,
        "elapsed_seconds": trace.get("elapsed_seconds"),
        "route": _route_summary(route),
        "request_meta": _request_meta_summary(request_meta),
    }
    path = _failure_path(dirs, batch_id)
    _write_json(path, failure_payload)
    return str(path.relative_to(dirs["root"]))


def _write_failed_machine_summary(
    *,
    dirs: Dict[str, Path],
    input_payload: Dict[str, Any],
    outputs: Dict[str, Dict[str, Any]],
    written_files: Dict[str, List[str]],
    reduction_written: List[str],
    batch_counts: Dict[str, int],
    selected_chars: Dict[str, int],
    failed_step: str,
    failed_batch: str,
    failure_artifacts: List[str],
) -> None:
    payload = {
        "status": "FAILED",
        "run_id": input_payload["run_id"],
        "run_root": input_payload["run_root"],
        "output_root": str(dirs["root"]),
        "steps": [step.step_id for step in FL_INT_STEPS],
        "step_statuses": {
            step_id: outputs[step_id].get("status", "UNKNOWN")
            for step_id in sorted(outputs)
        },
        "written_files": written_files,
        "reduction_artifacts": reduction_written,
        "batch_counts": batch_counts,
        "selected_chars": selected_chars,
        "failed_step": failed_step,
        "failed_batch": failed_batch,
        "failure_artifacts": failure_artifacts,
    }
    dirs["machine_summary"].write_text(
        sanitized_json_text(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _truncate_response_text(text: str, limit: int = 20000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[TRUNCATED]...\n"


def _artifact_from_reduced_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "artifact_name": f"{row['source_artifact']}#{row['chunk_id']}",
        "kind": str(row.get("kind") or "reduced"),
        "source_artifact": row["source_artifact"],
        "source_path": row["source_path"],
        "path": row["path"],
        "line_range": list(row["line_range"]),
        "score": int(row["score"]),
        "guardrail_preserved": bool(row["guardrail_preserved"]),
        "keep_reason": str(row["keep_reason"]),
        "char_count": int(row["char_count"]),
        "content": str(row["content"]),
    }


def _reduced_phase_payload(
    phase_id: str,
    norm_dir: str,
    rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    artifacts = [_artifact_from_reduced_row(row) for row in rows]
    return {
        "phase_id": phase_id,
        "norm_dir": norm_dir,
        "artifact_count": len(artifacts),
        "artifact_names": [artifact["artifact_name"] for artifact in artifacts],
        "artifacts": artifacts,
    }


def _canonical_design_meta(payload: Dict[str, Any]) -> Dict[str, Any]:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    return {
        "schema_version": "CANONICAL_DESIGN_META_V1",
        "status": payload.get("status", "UNKNOWN"),
        "missing_evidence": list(payload.get("missing_evidence", [])),
        **meta,
    }


def _master_feature_ledger(payload: Dict[str, Any]) -> Dict[str, Any]:
    ledger = (
        payload.get("master_feature_ledger")
        if isinstance(payload.get("master_feature_ledger"), dict)
        else {}
    )
    return {
        "schema_version": "MASTER_FEATURE_LEDGER_V1",
        "status": payload.get("status", "UNKNOWN"),
        "missing_evidence": list(payload.get("missing_evidence", [])),
        **ledger,
    }


def _write_step_outputs(step: FLIntStep, payload: Dict[str, Any], run_root: Path) -> List[str]:
    written: List[str] = []
    step_result_path = run_root / f"STEP_{step.step_id}_RESULT.json"
    _write_json(step_result_path, payload)
    written.append(step_result_path.name)

    if step.step_id == "F0":
        _write_json(run_root / "DESIGN_CLAIMS_RAW.json", payload["design_claims_raw"])
        written.append("DESIGN_CLAIMS_RAW.json")
    elif step.step_id == "F1":
        _write_json(run_root / "DESIGN_CLAIMS_CLASSIFIED.json", payload["design_claims_classified"])
        written.append("DESIGN_CLAIMS_CLASSIFIED.json")
    elif step.step_id == "F2":
        _write_json(run_root / "DESIGN_CONTRADICTIONS.json", payload["design_contradictions"])
        written.append("DESIGN_CONTRADICTIONS.json")
    elif step.step_id == "F4":
        design_path = run_root / "CANONICAL_DESIGN.md"
        design_path.write_text(sanitize_text_for_output(str(payload["canonical_design_markdown"]).rstrip() + "\n"), encoding="utf-8")
        _write_json(run_root / "CANONICAL_DESIGN_META.json", _canonical_design_meta(payload))
        written.extend(["CANONICAL_DESIGN.md", "CANONICAL_DESIGN_META.json"])
    elif step.step_id == "L0":
        _write_json(run_root / "FEATURE_CANDIDATES_RAW.json", payload["feature_candidates_raw"])
        written.append("FEATURE_CANDIDATES_RAW.json")
    elif step.step_id == "L1":
        _write_json(run_root / "FEATURE_CANDIDATES_NORMALIZED.json", payload["feature_candidates_normalized"])
        _write_json(run_root / "FEATURE_MERGE_LOG.json", payload["feature_merge_log"])
        written.extend(["FEATURE_CANDIDATES_NORMALIZED.json", "FEATURE_MERGE_LOG.json"])
    elif step.step_id == "L3":
        _write_json(run_root / "FEATURE_LEDGER_ROUTING.json", payload["feature_ledger_routing"])
        written.append("FEATURE_LEDGER_ROUTING.json")
    elif step.step_id == "L4":
        _write_json(run_root / "MASTER_FEATURE_LEDGER.json", _master_feature_ledger(payload))
        written.append("MASTER_FEATURE_LEDGER.json")

    return written


def _write_reduction_artifacts(
    dirs: Dict[str, Path],
    *,
    f0_reduction: Dict[str, Any],
    l0_reduction: Optional[Dict[str, Any]] = None,
) -> List[str]:
    written: List[str] = []
    f0_reduction_path = dirs["root"] / "F0_INPUT_REDUCTION.json"
    _write_json(f0_reduction_path, f0_reduction)
    written.append(f0_reduction_path.name)
    f0_batch_plan_path = dirs["raw"] / "F0_BATCH_PLAN.json"
    _write_json(
        f0_batch_plan_path,
        {
            "schema_version": "F0_BATCH_PLAN_V1",
            "batches": f0_reduction.get("batches", []),
        },
    )
    written.append(str(f0_batch_plan_path.relative_to(dirs["root"])))
    if l0_reduction is not None:
        l0_reduction_path = dirs["root"] / "L0_INPUT_REDUCTION.json"
        _write_json(l0_reduction_path, l0_reduction)
        written.append(l0_reduction_path.name)
        l0_batch_plan_path = dirs["raw"] / "L0_BATCH_PLAN.json"
        _write_json(
            l0_batch_plan_path,
            {
                "schema_version": "L0_BATCH_PLAN_V1",
                "batches": l0_reduction.get("batches", []),
            },
        )
        written.append(str(l0_batch_plan_path.relative_to(dirs["root"])))
    return written


def _execute_step_once(
    *,
    step: FLIntStep,
    step_input: Dict[str, Any],
    prior_outputs: Dict[str, Any],
    prompt_executor: PromptExecutor,
) -> Dict[str, Any]:
    schema = load_schema(_schema_root() / step.schema_file)
    rendered_prompt = _render_prompt(step, step_input, prior_outputs)
    result = prompt_executor(step, rendered_prompt, schema, prior_outputs)
    payload = result.get("payload")
    if not isinstance(payload, dict):
        raise RuntimeError(f"FL_INT step {step.step_id} did not return a JSON object payload.")
    payload = normalize_step_payload(step.step_id, payload, prior_outputs)
    validate_payload_or_raise(payload, schema, label=step.step_id)
    return payload


def _f0_batch_step_input(
    step: FLIntStep,
    input_payload: Dict[str, Any],
    batch_rows: List[Dict[str, Any]],
    batch_id: str,
) -> Dict[str, Any]:
    phase = input_payload["phases"].get("D") or {}
    return {
        "schema_version": "FL_INT_STEP_INPUT_V1",
        "step_id": step.step_id,
        "run_id": input_payload["run_id"],
        "run_root": input_payload["run_root"],
        "required_phase_ids": input_payload["required_phase_ids"],
        "optional_phase_ids": input_payload["optional_phase_ids"],
        "available_phase_ids": input_payload["available_phase_ids"],
        "selected_phase_ids": ["D"],
        "prior_step_ids": list(step.prior_step_ids),
        "upstream_phases": {
            "D": _reduced_phase_payload("D", str(phase.get("norm_dir") or ""), batch_rows),
        },
        "notes": [f"FL_INT reduced batch {batch_id} for F0."],
        "known_prior_steps": [],
    }


def _l0_batch_step_input(
    step: FLIntStep,
    input_payload: Dict[str, Any],
    family: str,
    batch_rows: List[Dict[str, Any]],
    prior_outputs: Dict[str, Any],
) -> Dict[str, Any]:
    selected_phases: Dict[str, Any] = {}
    if family in {"D", "C", "X"}:
        phase = input_payload["phases"].get(family) or {}
        selected_phases[family] = _reduced_phase_payload(family, str(phase.get("norm_dir") or ""), batch_rows)
    notes = [f"FL_INT reduced batch for L0 family {family}."]
    if family == "X" and not selected_phases:
        notes.append("Optional phase X is absent for this run.")
    return {
        "schema_version": "FL_INT_STEP_INPUT_V1",
        "step_id": step.step_id,
        "run_id": input_payload["run_id"],
        "run_root": input_payload["run_root"],
        "required_phase_ids": input_payload["required_phase_ids"],
        "optional_phase_ids": input_payload["optional_phase_ids"],
        "available_phase_ids": input_payload["available_phase_ids"],
        "selected_phase_ids": sorted(selected_phases.keys()),
        "prior_step_ids": list(step.prior_step_ids),
        "upstream_phases": selected_phases,
        "notes": notes,
        "known_prior_steps": sorted(prior_outputs.keys()),
    }


def _batch_rows_for_ids(rows: List[Dict[str, Any]], selected_ids: List[str]) -> List[Dict[str, Any]]:
    by_id = {str(row.get("chunk_id")): row for row in rows}
    return [by_id[row_id] for row_id in selected_ids if row_id in by_id]


def _write_batch_input(path: Path, payload: Dict[str, Any]) -> None:
    _write_json(path, payload)


def _batch_result_path(dirs: Dict[str, Path], batch_id: str) -> Path:
    return dirs["raw"] / f"{batch_id}_RESULT.json"


def _batch_input_path(dirs: Dict[str, Path], batch_id: str) -> Path:
    return dirs["raw"] / f"{batch_id}_INPUT.json"


def _l0_f1_prior_outputs(outputs: Dict[str, Dict[str, Any]], batch_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    ids = {str(item.get("section_key") or "") for item in batch_rows}
    return {
        "F1": {
            "status": outputs["F1"].get("status", "UNKNOWN"),
            "missing_evidence": list(outputs["F1"].get("missing_evidence", [])),
            "design_claims_classified": {
                "schema": outputs["F1"]["design_claims_classified"]["schema"],
                "items": [
                    dict(row)
                    for row in (((outputs["F1"].get("design_claims_classified") or {}).get("items")) or [])
                    if str(row.get("id") or "") in ids
                ],
            },
        }
    }


def run_fl_int(
    run_root: Path,
    *,
    dry_run: bool,
    out_root: Optional[Path] = None,
    prompt_executor: Optional[PromptExecutor] = None,
    f0_batch_timeout_seconds: int = 210,
) -> Dict[str, Any]:
    dirs = ensure_fl_int_dirs(run_root, out_root=out_root)
    input_payload = collect_input_bundle(run_root, out_root=out_root)
    f0_reduction = reduce_f0_input(input_payload)

    if dry_run:
        l0_reduction = reduce_l0_input(input_payload, {"_f0_reduction": f0_reduction})
        reduction_written = _write_reduction_artifacts(
            dirs,
            f0_reduction=f0_reduction,
            l0_reduction=l0_reduction,
        )
        summary = {
            "status": "DRY_RUN",
            "run_id": input_payload["run_id"],
            "run_root": input_payload["run_root"],
            "output_root": str(dirs["root"]),
            "steps": [step.step_id for step in FL_INT_STEPS],
            "reduction_artifacts": reduction_written,
            "batch_counts": {
                "F0": len(f0_reduction.get("batches", [])),
                "L0": len(l0_reduction.get("batches", [])),
            },
            "selected_chars": {
                "F0": int(f0_reduction.get("total_selected_chars") or 0),
                "L0": int(l0_reduction.get("total_selected_chars") or 0),
            },
        }
        dirs["machine_summary"].write_text(sanitized_json_text(summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
        compile_fl_int_reports(dirs["root"], {})
        return summary

    if prompt_executor is None:
        raise RuntimeError("FL_INT execution requires a prompt_executor when not in dry-run mode.")

    outputs: Dict[str, Dict[str, Any]] = {}
    written_files: Dict[str, List[str]] = {}
    reduction_written = _write_reduction_artifacts(dirs, f0_reduction=f0_reduction)
    batch_counts = {
        "F0": len(f0_reduction.get("batches", [])),
        "L0": 0,
    }
    selected_chars = {
        "F0": int(f0_reduction.get("total_selected_chars") or 0),
        "L0": 0,
    }

    for step in FL_INT_STEPS:
        if step.step_id == "F0":
            selected_chunks = list(f0_reduction.get("selected_chunks") or [])
            batch_payloads: List[Dict[str, Any]] = []
            schema = load_schema(_schema_root() / step.schema_file)
            for batch in f0_reduction.get("batches", []):
                batch_id = str(batch["batch_id"])
                batch_rows = _batch_rows_for_ids(selected_chunks, list(batch.get("selected_ids") or []))
                step_input = _f0_batch_step_input(step, input_payload, batch_rows, batch_id)
                _write_batch_input(_batch_input_path(dirs, batch_id), step_input)
                rendered_prompt = _render_prompt(step, step_input, {})
                trace = _new_f0_trace(
                    batch_id=batch_id,
                    step=step,
                    input_payload=input_payload,
                    output_root=dirs["root"],
                    step_input=step_input,
                    rendered_prompt=rendered_prompt,
                    selected_chunk_count=len(batch_rows),
                )
                trace_path = _trace_path(dirs, batch_id)
                started_monotonic = time.monotonic()
                _append_stage(trace, stage="batch_start", started_monotonic=started_monotonic)
                _write_trace(trace_path, trace)

                failure_artifacts: List[str] = []
                response_text = ""
                request_meta: Dict[str, Any] = {}
                route: Any = None

                def _write_failed_state(terminal_stage: str) -> None:
                    nonlocal failure_artifacts
                    if response_text:
                        response_rel = str(_response_path(dirs, batch_id).relative_to(dirs["root"]))
                        _write_text(_response_path(dirs, batch_id), _truncate_response_text(response_text))
                        if response_rel not in failure_artifacts:
                            failure_artifacts.append(response_rel)
                    failure_rel = _write_failure_artifact(
                        dirs=dirs,
                        batch_id=batch_id,
                        trace=trace,
                        request_meta=request_meta,
                        timeout_seconds=f0_batch_timeout_seconds,
                        terminal_stage=terminal_stage,
                        route=route,
                    )
                    if failure_rel not in failure_artifacts:
                        failure_artifacts.append(failure_rel)
                    _write_failed_machine_summary(
                        dirs=dirs,
                        input_payload=input_payload,
                        outputs=outputs,
                        written_files=written_files,
                        reduction_written=reduction_written,
                        batch_counts=batch_counts,
                        selected_chars=selected_chars,
                        failed_step=step.step_id,
                        failed_batch=batch_id,
                        failure_artifacts=failure_artifacts,
                    )

                def _enforce_timeout(terminal_stage: str) -> None:
                    if trace.get("elapsed_seconds", 0.0) <= float(f0_batch_timeout_seconds):
                        return
                    request_meta.setdefault("failure_type", "timeout")
                    request_meta.setdefault(
                        "provider_error_reason",
                        f"f0_batch_timeout:{f0_batch_timeout_seconds}s",
                    )
                    _append_stage(
                        trace,
                        stage=terminal_stage,
                        started_monotonic=started_monotonic,
                    )
                    _write_trace(trace_path, trace)
                    _write_failed_state(terminal_stage)
                    raise RuntimeError(
                        f"FL_INT step F0 batch {batch_id} exceeded timeout after {trace['elapsed_seconds']}s."
                    )

                def _observer(stage_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
                    payload = payload or {}
                    next_route = payload.get("route")
                    summary = payload.get("request_meta")
                    extra = {
                        "selected_route": _route_summary(next_route if next_route is not None else route),
                        "response_received": bool(payload.get("response_received", trace.get("response_received", False))),
                        "response_text_chars": int(payload.get("response_text_chars", trace.get("response_text_chars", 0))),
                    }
                    if isinstance(summary, dict) and summary:
                        extra["request_meta"] = _request_meta_summary(summary)
                    _append_stage(trace, stage=stage_name, started_monotonic=started_monotonic, extra=extra)
                    _write_trace(trace_path, trace)

                try:
                    result = prompt_executor(
                        step,
                        rendered_prompt,
                        schema,
                        {"__fl_int_diag_observer__": _observer},
                    )
                    request_meta = (
                        dict(result.get("request_meta") or {})
                        if isinstance(result.get("request_meta"), dict)
                        else {}
                    )
                    response_text = str(result.get("response_text") or "")
                    route = result.get("route")
                    trace["selected_route"] = _route_summary(route)
                    trace["response_received"] = bool(request_meta.get("response_received") or response_text)
                    trace["response_text_chars"] = len(response_text)
                    trace["request_meta"] = _request_meta_summary(request_meta)
                    _write_trace(trace_path, trace)

                    _enforce_timeout("provider_call_timeout")

                    payload = result.get("payload")
                    if not isinstance(payload, dict):
                        terminal_stage = str(trace.get("stage") or "provider_call_return")
                        _write_failed_state(terminal_stage)
                        failure_type = str(request_meta.get("failure_type") or "invalid_json")
                        raise RuntimeError(
                            f"FL_INT step {step.step_id} batch {batch_id} failed at "
                            f"{terminal_stage} failure_type={failure_type}."
                        )

                    _append_stage(trace, stage="schema_validate_start", started_monotonic=started_monotonic)
                    _write_trace(trace_path, trace)
                    validate_payload_or_raise(payload, schema, label=step.step_id)
                    _append_stage(trace, stage="schema_validate_return", started_monotonic=started_monotonic)
                    _write_trace(trace_path, trace)

                    _enforce_timeout("schema_validate_timeout")

                    _append_stage(trace, stage="artifact_write_start", started_monotonic=started_monotonic)
                    _write_trace(trace_path, trace)
                    _write_json(_batch_result_path(dirs, batch_id), payload)
                    _append_stage(trace, stage="artifact_write_success", started_monotonic=started_monotonic)
                    _write_trace(trace_path, trace)
                    batch_payloads.append(payload)
                except Exception:
                    if not failure_artifacts:
                        _write_failed_state(str(trace.get("stage") or "batch_start"))
                    raise
            merged_payload = merge_f0_batch_payloads(batch_payloads)
            validate_payload_or_raise(merged_payload, load_schema(_schema_root() / step.schema_file), label=step.step_id)
            outputs[step.step_id] = merged_payload
            written_files[step.step_id] = _write_step_outputs(step, merged_payload, dirs["root"])
            continue

        if step.step_id == "L0":
            l0_context = dict(outputs)
            l0_context["_f0_reduction"] = f0_reduction
            l0_reduction = reduce_l0_input(input_payload, l0_context)
            reduction_written = _write_reduction_artifacts(
                dirs,
                f0_reduction=f0_reduction,
                l0_reduction=l0_reduction,
            )
            batch_counts["L0"] = len(l0_reduction.get("batches", []))
            selected_chars["L0"] = int(l0_reduction.get("total_selected_chars") or 0)
            selected_by_family = l0_reduction.get("selected_by_family") or {}
            batch_payloads = []
            for batch in l0_reduction.get("batches", []):
                batch_id = str(batch["batch_id"])
                family = batch_id.split("_")[2]
                family_rows = list(selected_by_family.get(family) or [])
                batch_rows = _batch_rows_for_ids(family_rows, list(batch.get("selected_ids") or []))
                step_input = _l0_batch_step_input(step, input_payload, family, batch_rows, outputs)
                prior_context = _l0_f1_prior_outputs(outputs, batch_rows) if family == "F1" else {}
                _write_batch_input(_batch_input_path(dirs, batch_id), step_input)
                payload = _execute_step_once(
                    step=step,
                    step_input=step_input,
                    prior_outputs=prior_context,
                    prompt_executor=prompt_executor,
                )
                _write_json(_batch_result_path(dirs, batch_id), payload)
                batch_payloads.append(payload)
            merged_payload = merge_l0_batch_payloads(batch_payloads)
            validate_payload_or_raise(merged_payload, load_schema(_schema_root() / step.schema_file), label=step.step_id)
            outputs[step.step_id] = merged_payload
            written_files[step.step_id] = _write_step_outputs(step, merged_payload, dirs["root"])
            continue

        step_input = _step_input_payload(step, input_payload, outputs)
        payload = _execute_step_once(
            step=step,
            step_input=step_input,
            prior_outputs=outputs,
            prompt_executor=prompt_executor,
        )
        outputs[step.step_id] = payload
        written_files[step.step_id] = _write_step_outputs(step, payload, dirs["root"])

    machine_summary = {
        "status": "OK",
        "run_id": input_payload["run_id"],
        "run_root": input_payload["run_root"],
        "output_root": str(dirs["root"]),
        "steps": [step.step_id for step in FL_INT_STEPS],
        "step_statuses": {step_id: outputs[step_id].get("status", "UNKNOWN") for step_id in sorted(outputs)},
        "written_files": written_files,
        "reduction_artifacts": reduction_written,
        "batch_counts": batch_counts,
        "selected_chars": selected_chars,
    }
    dirs["machine_summary"].write_text(sanitized_json_text(machine_summary, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    compile_fl_int_reports(dirs["root"], outputs)
    return machine_summary
