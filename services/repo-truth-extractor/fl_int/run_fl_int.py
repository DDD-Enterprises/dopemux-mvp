from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .collect_input import collect_input_bundle
from .fl_int_paths import ensure_fl_int_dirs
from .models import FL_INT_STEPS, FLIntStep
from .report_compiler import compile_fl_int_reports
from s_int.schema_validate import load_schema, validate_payload_or_raise


PromptExecutor = Callable[[FLIntStep, str, Dict[str, Any], Dict[str, Any]], Dict[str, Any]]


def _service_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _prompt_root() -> Path:
    return _service_root() / "prompts" / "phase_fl_int"


def _schema_root() -> Path:
    return _prompt_root() / "schemas"


def _render_prompt(step: FLIntStep, step_input: Dict[str, Any], prior_outputs: Dict[str, Any]) -> str:
    prompt_path = _prompt_root() / step.prompt_file
    text = prompt_path.read_text(encoding="utf-8")
    text = text.replace("{{FL_INT_INPUT_JSON}}", json.dumps(step_input, indent=2, sort_keys=True))
    text = text.replace("{{PRIOR_OUTPUTS_JSON}}", json.dumps(prior_outputs, indent=2, sort_keys=True))
    return text


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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
        design_path.write_text(str(payload["canonical_design_markdown"]).rstrip() + "\n", encoding="utf-8")
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


def run_fl_int(
    run_root: Path,
    *,
    dry_run: bool,
    out_root: Optional[Path] = None,
    prompt_executor: Optional[PromptExecutor] = None,
) -> Dict[str, Any]:
    dirs = ensure_fl_int_dirs(run_root, out_root=out_root)
    input_payload = collect_input_bundle(run_root, out_root=out_root)

    if dry_run:
        summary = {
            "status": "DRY_RUN",
            "run_id": input_payload["run_id"],
            "run_root": input_payload["run_root"],
            "output_root": str(dirs["root"]),
            "steps": [step.step_id for step in FL_INT_STEPS],
        }
        dirs["machine_summary"].write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        compile_fl_int_reports(dirs["root"], {})
        return summary

    if prompt_executor is None:
        raise RuntimeError("FL_INT execution requires a prompt_executor when not in dry-run mode.")

    outputs: Dict[str, Dict[str, Any]] = {}
    written_files: Dict[str, List[str]] = {}
    for step in FL_INT_STEPS:
        schema = load_schema(_schema_root() / step.schema_file)
        step_input = _step_input_payload(step, input_payload, outputs)
        rendered_prompt = _render_prompt(step, step_input, outputs)
        result = prompt_executor(step, rendered_prompt, schema, outputs)
        payload = result.get("payload")
        if not isinstance(payload, dict):
            raise RuntimeError(f"FL_INT step {step.step_id} did not return a JSON object payload.")
        validate_payload_or_raise(payload, schema, label=step.step_id)
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
    }
    dirs["machine_summary"].write_text(json.dumps(machine_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    compile_fl_int_reports(dirs["root"], outputs)
    return machine_summary
