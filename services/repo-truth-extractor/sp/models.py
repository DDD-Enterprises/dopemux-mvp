"""SP (Synthesis Phase) step definitions and routing configuration."""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class SPStep:
    """Definition of a single SP (Synthesis Phase) step."""

    step_id: str
    prompt_file: str
    schema_path: Optional[str]
    template_vars: Tuple[str, ...]
    ladder_name: str
    routing_tier: str
    max_hops: int


# SP step definitions with template variable requirements
SP_STEPS: List[SPStep] = [
    # SP0-SP6: Synthesis prompts (input = R/X/T/Z phase outputs)
    SPStep("SP0", "PROMPT_SP0_OPUS_ARCHITECTURE_SYNTHESIS.md", None, ("SP_PHASE_INPUT_JSON",), "reasoned_plan", "synthesis", 3),
    SPStep("SP1", "PROMPT_SP1_OPUS_MCP_TO_HOOKS_MIGRATION_PLAN.md", None, ("SP_PHASE_INPUT_JSON",), "reasoned_plan", "synthesis", 3),
    SPStep("SP2", "PROMPT_SP2_DECISION_DOSSIER.md", None, ("SP_PHASE_INPUT_JSON",), "reasoned_plan", "synthesis", 3),
    SPStep("SP3", "PROMPT_SP3_ARCH_PROOF_HOOKS.md", None, ("SP_PHASE_INPUT_JSON",), "reasoned_plan", "synthesis", 3),
    SPStep("SP4", "PROMPT_SP4_TRUTH_PACK_INDEX.md", "schemas/SP4.json", ("SP_PHASE_INPUT_JSON",), "reasoned_plan", "synthesis", 3),
    SPStep("SP5", "PROMPT_SP5_DECISION_GRAPH.md", "schemas/SP5.json", ("SP_PHASE_INPUT_JSON",), "reasoned_plan", "synthesis", 3),
    SPStep("SP6", "PROMPT_SP6_LEANTIME_ANALYSIS.md", None, ("SP_PHASE_INPUT_JSON",), "reasoned_plan", "synthesis", 3),

    # SP7: Dedupe and stable sort (requires schema + rules + canonical)
    SPStep("SP7", "PROMPT_SP7_DEDUPE_SORT.md", "schemas/SP7.json", ("SCHEMA_JSON", "RULES_JSON", "CANONICAL_JSON"), "reasoned_plan", "synthesis", 3),

    # SP8: Drift check (requires base + new canonical)
    SPStep("SP8", "PROMPT_SP8_DRIFT_CHECK.md", "schemas/SP8.json", ("BASE_JSON", "NEW_JSON"), "reasoned_plan", "synthesis", 3),

    # SP9: Promotion readiness (requires canonical + promotion rules + metrics)
    SPStep("SP9", "PROMPT_SP9_PROMOTION_READINESS.md", "schemas/SP9.json", ("PROMOTION_RULES_JSON", "METRICS_JSON", "CANONICAL_JSON"), "reasoned_plan", "synthesis", 3),

    # SP10: Redaction pass (requires canonical)
    SPStep("SP10", "PROMPT_SP10_REDACTION_PASS.md", "schemas/SP10.json", ("CANONICAL_JSON",), "cheap_eval", "synthesis", 2),

    # SP11: Contract linter (requires canonical + contract rules)
    SPStep("SP11", "PROMPT_SP11_CONTRACT_LINTER.md", "schemas/SP11.json", ("CONTRACT_RULES_JSON", "CANONICAL_JSON"), "cheap_eval", "qa", 2),

    # SP12: Stability signature (requires canonical + prior outputs)
    SPStep("SP12", "PROMPT_SP12_STABILITY_SIGNATURE.md", "schemas/SP12.json", ("CANONICAL_JSON",), "cheap_eval", "qa", 2),
]

# Map step_id to SPStep for fast lookup
SP_STEPS_BY_ID = {step.step_id: step for step in SP_STEPS}
