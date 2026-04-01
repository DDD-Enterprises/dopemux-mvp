from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, List, Tuple


Route = Tuple[str, str, str]
REGISTRY_ROOT = Path(__file__).resolve().parents[1] / "prompts" / "phase_fl_int"
REGISTRY_PATH = REGISTRY_ROOT / "registry.json"
FL_INT_STEP_ORDER = ("F0", "F1", "F2", "F4", "L0", "L1", "L3", "L4")


@dataclass(frozen=True)
class FLIntStep:
    step_id: str
    prompt_file: str
    schema_file: str
    output_files: Tuple[str, ...]
    ladder_name: str
    routing_tier: str
    max_hops: int
    input_phase_ids: Tuple[str, ...]
    prior_step_ids: Tuple[str, ...]


STRUCTURE_LADDER: List[Route] = [
    ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
    ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
    ("openrouter", "anthropic/claude-opus-4-6", "OPENROUTER_API_KEY"),
]

REASONED_PLAN_LADDER: List[Route] = [
    ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
    ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
    ("openrouter", "anthropic/claude-opus-4-6", "OPENROUTER_API_KEY"),
]

CHEAP_EVAL_LADDER: List[Route] = [
    ("xai", "grok-4-1-fast-reasoning", "XAI_API_KEY"),
    ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
]

FL_INT_LADDERS: Dict[str, List[Route]] = {
    "structure": STRUCTURE_LADDER,
    "reasoned_plan": REASONED_PLAN_LADDER,
    "cheap_eval": CHEAP_EVAL_LADDER,
}


def _load_registry() -> Dict[str, object]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{REGISTRY_PATH} must decode to an object.")
    return payload


def _as_tuple(value: object) -> Tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def load_steps() -> List[FLIntStep]:
    payload = _load_registry()
    steps = payload.get("steps")
    if not isinstance(steps, dict):
        raise RuntimeError(f"{REGISTRY_PATH} must contain an object at steps.")
    loaded: List[FLIntStep] = []
    for step_id in FL_INT_STEP_ORDER:
        row = steps.get(step_id)
        if not isinstance(row, dict):
            raise RuntimeError(f"{REGISTRY_PATH} missing step {step_id}.")
        prompt_file = str(row.get("prompt_path") or "").strip()
        schema_file = str(row.get("schema_path") or "").strip()
        if not prompt_file or not schema_file:
            raise RuntimeError(f"{REGISTRY_PATH} step {step_id} missing prompt_path or schema_path.")
        loaded.append(
            FLIntStep(
                step_id=step_id,
                prompt_file=prompt_file,
                schema_file=schema_file,
                output_files=_as_tuple(row.get("outputs")),
                ladder_name=str(row.get("ladder_name") or "reasoned_plan").strip(),
                routing_tier=str(row.get("routing_tier") or "synthesis").strip(),
                max_hops=max(1, int(row.get("max_hops") or 1)),
                input_phase_ids=_as_tuple(row.get("input_phase_ids")),
                prior_step_ids=_as_tuple(row.get("prior_step_ids")),
            )
        )
    return loaded


FL_INT_STEPS: List[FLIntStep] = load_steps()


def ladder_for_step(step: FLIntStep) -> List[Route]:
    return list(FL_INT_LADDERS[step.ladder_name])
