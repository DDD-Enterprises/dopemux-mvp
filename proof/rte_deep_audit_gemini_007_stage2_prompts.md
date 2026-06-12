# RTE Deep Audit Stage 2: Prompt Architecture

## Prompt Inventory & Structure
- **Canonical Manifest:** `services/repo-truth-extractor/promptsets/v4/promptset.yaml` (v4.0).
- **Prompt Files:** Located in `promptsets/v4/prompts/`.
- **Template Discipline:** Prompts (e.g., `PROMPT_A1_INSTRUCTION_SURFACES.md`) follow a strict 9-section template: Goal, Inputs, Outputs, Schema, Extraction Procedure, Evidence Rules, Determinism Rules, Anti-Fabrication Rules, Failure Modes.
- **Evidence Mandate:** Every fact must be tied to a file path, line range, and excerpt.

## Prompt/Runtime Alignment
- **Execution Mode:** v5 runner defaults to v4 promptsets. This "Logic v5 / Contract v4" split appears stable but creates a dependency on legacy folder structures.
- **Gating Behavior:** `run_extraction_v5.py` implements `apply_promptset_preflight_block`. This gate is active and will halt execution if the prompt set is invalid or missing required steps.
- **Phase S Complexity:** Phase S supports both `legacy` (v3) and `registry` (modern) modes. Registry mode uses a `registry.json` to map steps to prompts, providing a path away from hard-coded v3 logic.

## Ranked Weaknesses
1.  **Phase S Ambiguity (Medium Risk):** The coexistence of legacy/registry modes for Phase S is an operational hazard. If an operator accidentally uses `legacy` mode, they are running v3 prompts in a v5 pipeline.
2.  **Legacy Context (Low Risk):** Prompts contain "Legacy Context" blocks for intent. While helpful for human review, they could confuse an LLM if not properly delimited in the final rendered prompt.
3.  **Hard-coded Version Paths (Low Risk):** `rte_promptset.py` hard-codes the `v4` path as a fallback.

## Verdict
Prompt architecture is **High Fidelity and Robust**. The schema-first design and evidence mandate are the primary drivers of truth quality in this system.
