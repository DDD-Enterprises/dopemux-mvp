from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


Route = Tuple[str, str, str]


@dataclass(frozen=True)
class SIntStep:
    step_id: str
    prompt_file: str
    schema_file: str
    ladder_name: str
    routing_tier: str
    max_hops: int


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

S_INT_LADDERS: Dict[str, List[Route]] = {
    "structure": STRUCTURE_LADDER,
    "reasoned_plan": REASONED_PLAN_LADDER,
    "cheap_eval": CHEAP_EVAL_LADDER,
}

S_INT_STEPS: List[SIntStep] = [
    SIntStep("S16", "S16_mcp_split_validity.md", "S16.json", "structure", "synthesis", 3),
    SIntStep("S17", "S17_hook_surface_map.md", "S17.json", "structure", "synthesis", 3),
    SIntStep("S18", "S18_contract_coverage.md", "S18.json", "reasoned_plan", "synthesis", 3),
    SIntStep("S19", "S19_gradecard.md", "S19.json", "cheap_eval", "qa", 2),
    SIntStep("S20", "S20_v1_release_plan.md", "S20.json", "reasoned_plan", "synthesis", 3),
]


def ladder_for_step(step: SIntStep) -> List[Route]:
    return list(S_INT_LADDERS[step.ladder_name])
