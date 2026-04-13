from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class SPStep:
    step_id: str
    prompt_file: str
    template_vars: Tuple[str, ...]
    schema_path: str | None = None


SP_STEPS: List[SPStep] = [
    SPStep("S0", "PROMPT_S0_OPUS_ARCHITECTURE_SYNTHESIS.md", ("SP_PHASE_INPUT_JSON",)),
    SPStep("S1", "PROMPT_S1_OPUS_MCP_TO_HOOKS_MIGRATION_PLAN.md", ("SP_PHASE_INPUT_JSON",)),
    SPStep("S2", "PROMPT_S2_DECISION_DOSSIER.md", ("SP_PHASE_INPUT_JSON",)),
    SPStep("S3", "PROMPT_S3_ARCH_PROOF_HOOKS.md", ("SP_PHASE_INPUT_JSON",)),
    SPStep("S4", "PROMPT_S4_TRUTH_PACK_INDEX.md", ("SP_PHASE_INPUT_JSON",)),
    SPStep("S5", "PROMPT_S5_DECISION_GRAPH.md", ("SP_PHASE_INPUT_JSON",)),
    SPStep("S6", "PROMPT_S6_LEANTIME_ANALYSIS.md", ("SP_PHASE_INPUT_JSON",)),
    SPStep("S7", "PROMPT_S7_DEDUPE_SORT.md", ("SCHEMA_JSON", "RULES_JSON", "CANONICAL_JSON")),
    SPStep("S8", "PROMPT_S8_DRIFT_CHECK.md", ("BASE_JSON", "NEW_JSON")),
    SPStep("S9", "PROMPT_S9_PROMOTION_READINESS.md", ("PROMOTION_RULES_JSON", "METRICS_JSON", "CANONICAL_JSON")),
    SPStep("S10", "PROMPT_S10_REDACTION_PASS.md", ("CANONICAL_JSON",)),
    SPStep("S11", "PROMPT_S11_CONTRACT_LINTER.md", ("CONTRACT_RULES_JSON", "CANONICAL_JSON")),
    SPStep("S12", "PROMPT_S12_STABILITY_SIGNATURE.md", ("CANONICAL_JSON",)),
]

SP_STEPS_BY_ID: Dict[str, SPStep] = {step.step_id: step for step in SP_STEPS}
