from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .collect_input import collect_input_bundle
from .models import S_INT_STEPS, SIntStep, ladder_for_step
from .report_compiler import compile_s_int_reports
from .s_int_paths import ensure_s_int_dirs
from .schema_validate import load_schema, validate_payload_or_raise


PromptExecutor = Callable[[SIntStep, str, Dict[str, Any], Dict[str, Any]], Dict[str, Any]]


def _service_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _prompt_root() -> Path:
    return _service_root() / "prompts" / "phase_s_int"


def _schema_root() -> Path:
    return _prompt_root() / "schemas"


def _render_prompt(step: SIntStep, input_payload: Dict[str, Any], prior_outputs: Dict[str, Any]) -> str:
    prompt_path = _prompt_root() / step.prompt_file
    text = prompt_path.read_text(encoding="utf-8")
    text = text.replace("{{S_INT_INPUT_JSON}}", json.dumps(input_payload, indent=2, sort_keys=True))
    text = text.replace("{{PRIOR_OUTPUTS_JSON}}", json.dumps(prior_outputs, indent=2, sort_keys=True))
    return text


def run_s_int(
    repo_root: Path,
    run_id: str,
    *,
    dry_run: bool,
    out_root: Optional[Path] = None,
    prompt_executor: Optional[PromptExecutor] = None,
) -> Dict[str, Any]:
    dirs = ensure_s_int_dirs(repo_root, run_id, out_root=out_root)
    input_payload = collect_input_bundle(repo_root, run_id, out_root=out_root)

    if dry_run:
        summary = {
            "status": "DRY_RUN",
            "run_id": run_id,
            "steps": [step.step_id for step in S_INT_STEPS],
        }
        dirs["machine_summary"].write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        compile_s_int_reports(dirs["root"], {})
        return summary

    if prompt_executor is None:
        raise RuntimeError("S_INT execution requires a prompt_executor when not in dry-run mode.")

    outputs: Dict[str, Dict[str, Any]] = {}
    for step in S_INT_STEPS:
        schema = load_schema(_schema_root() / step.schema_file)
        rendered_prompt = _render_prompt(step, input_payload, outputs)
        result = prompt_executor(step, rendered_prompt, schema, outputs)
        payload = result.get("payload")
        if not isinstance(payload, dict):
            raise RuntimeError(f"S_INT step {step.step_id} did not return a JSON object payload.")
        validate_payload_or_raise(payload, schema, label=step.step_id)
        outputs[step.step_id] = payload
        (dirs["root"] / f"{step.step_id}_{step.prompt_file.replace('.md', '.json').split('_', 1)[1]}").write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    machine_summary = {
        "status": "OK",
        "run_id": run_id,
        "steps": sorted(outputs.keys()),
        "step_statuses": {step_id: outputs[step_id].get("status", "UNKNOWN") for step_id in sorted(outputs)},
    }
    dirs["machine_summary"].write_text(json.dumps(machine_summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    compile_s_int_reports(dirs["root"], outputs)
    return machine_summary
