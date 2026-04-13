from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, List, Tuple


Route = Tuple[str, str, str]
RouteStatus = str
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


@dataclass(frozen=True)
class FLIntRouteRecord:
    provider: str
    model_id: str
    api_key_env: str
    status: RouteStatus
    authority_source: str
    note: str

    @property
    def route(self) -> Route:
        return (self.provider, self.model_id, self.api_key_env)


FL_INT_ROUTE_STATUS_CONFIRMED = "confirmed"
FL_INT_ROUTE_STATUS_FUTURE_TARGET = "future_target"
FL_INT_ROUTE_STATUS_STALE = "stale"

_ROUTE_AUTHORITY_SOURCE_HANDOFF_PACK = "audit_prep/prompt1_handoff_pack_normalized.md"
_ROUTE_AUTHORITY_SOURCE_AUDIT = "docs/05-audit-reports/rte-state-of-work-audit-20260410.md"

FL_INT_ROUTE_RECORDS: Tuple[FLIntRouteRecord, ...] = (
    FLIntRouteRecord(
        provider="gemini",
        model_id="gemini-3-flash-preview",
        api_key_env="GEMINI_API_KEY",
        status=FL_INT_ROUTE_STATUS_FUTURE_TARGET,
        authority_source=_ROUTE_AUTHORITY_SOURCE_AUDIT,
        note="Absent from the normalized handoff-pack registry; keep as forward-looking benchmark target only.",
    ),
    FLIntRouteRecord(
        provider="gemini",
        model_id="gemini-3.1-pro-preview",
        api_key_env="GEMINI_API_KEY",
        status=FL_INT_ROUTE_STATUS_FUTURE_TARGET,
        authority_source=_ROUTE_AUTHORITY_SOURCE_AUDIT,
        note="Absent from the normalized handoff-pack registry; keep as forward-looking benchmark target only.",
    ),
    FLIntRouteRecord(
        provider="openrouter",
        model_id="openai/gpt-5.3-codex",
        api_key_env="OPENROUTER_API_KEY",
        status=FL_INT_ROUTE_STATUS_FUTURE_TARGET,
        authority_source=_ROUTE_AUTHORITY_SOURCE_AUDIT,
        note="Used elsewhere in repo routing, but not confirmed by the normalized handoff-pack registry.",
    ),
    FLIntRouteRecord(
        provider="openrouter",
        model_id="openai/gpt-5.2",
        api_key_env="OPENROUTER_API_KEY",
        status=FL_INT_ROUTE_STATUS_FUTURE_TARGET,
        authority_source=_ROUTE_AUTHORITY_SOURCE_AUDIT,
        note="Present as a route target in code, but not confirmed by the normalized handoff-pack registry.",
    ),
    FLIntRouteRecord(
        provider="openrouter",
        model_id="anthropic/claude-opus-4-6",
        api_key_env="OPENROUTER_API_KEY",
        status=FL_INT_ROUTE_STATUS_FUTURE_TARGET,
        authority_source=_ROUTE_AUTHORITY_SOURCE_AUDIT,
        note="The normalized handoff pack confirms Claude Sonnet 4, not this Opus slug.",
    ),
    FLIntRouteRecord(
        provider="xai",
        model_id="grok-4-1-fast-reasoning",
        api_key_env="XAI_API_KEY",
        status=FL_INT_ROUTE_STATUS_FUTURE_TARGET,
        authority_source=_ROUTE_AUTHORITY_SOURCE_AUDIT,
        note="Absent from the normalized handoff-pack registry; keep as a benchmark-only future target.",
    ),
)

FL_INT_ROUTE_RECORD_INDEX: Dict[Route, FLIntRouteRecord] = {
    record.route: record for record in FL_INT_ROUTE_RECORDS
}

STRUCTURE_LADDER: List[Route] = [
    ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY"),
    ("gemini", "gemini-3.1-pro-preview", "GEMINI_API_KEY"),
    ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
    ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
    ("openrouter", "anthropic/claude-opus-4-6", "OPENROUTER_API_KEY"),
]

REASONED_PLAN_LADDER: List[Route] = [
    ("gemini", "gemini-3.1-pro-preview", "GEMINI_API_KEY"),
    ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY"),
    ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
    ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
    ("openrouter", "anthropic/claude-opus-4-6", "OPENROUTER_API_KEY"),
]

CHEAP_EVAL_LADDER: List[Route] = [
    ("gemini", "gemini-3-flash-preview", "GEMINI_API_KEY"),
    ("xai", "grok-4-1-fast-reasoning", "XAI_API_KEY"),
    ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
]

FL_INT_LADDERS: Dict[str, List[Route]] = {
    "structure": STRUCTURE_LADDER,
    "reasoned_plan": REASONED_PLAN_LADDER,
    "cheap_eval": CHEAP_EVAL_LADDER,
}


def route_record_for(route: Route) -> FLIntRouteRecord:
    record = FL_INT_ROUTE_RECORD_INDEX.get(route)
    if record is None:
        raise KeyError(f"Missing FL_INT route governance record for {route!r}")
    return record


def route_status_for(route: Route) -> RouteStatus:
    return route_record_for(route).status


def ladder_route_records(name: str) -> List[FLIntRouteRecord]:
    return [route_record_for(route) for route in FL_INT_LADDERS[name]]


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


def ladder_records_for_step(step: FLIntStep) -> List[FLIntRouteRecord]:
    return ladder_route_records(step.ladder_name)
