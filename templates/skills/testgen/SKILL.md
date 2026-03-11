---
name: testgen
description: Comprehensive test generation skill for TDD-driving and post-implementation validation from feature lists or task packets. Use when you need deterministic, traceable unit/smoke/integration/e2e/regression tests with explicit edge-case analysis and a fail-closed touched-code coverage gate (default at least 90%).
---

# Testgen

Use this skill to design and generate tests that prove implementation correctness against explicit requirements.

## Inputs

Provide one normalized request:

- `mode`: `tdd-driver` or `post-impl-generator`
- `source`: `feature-list` or `task-packet`
- `payload`: inline text, packet text, or payload file path
- `coverage_target`: integer percent (default `90`)
- `preferred_cli`: `auto`, `gemini`, `copilot`, `claude`
- `use_pal_testgen`: `auto`, `on`, `off`

## Pipeline

Run these phases in order and fail closed on ambiguity.

1. Intake and normalization.
2. Requirement decomposition and risk modeling (`thinkdeep` when available).
3. Deterministic sequencing (`planner` when available).
4. Edge-case and failure challenge pass (`consensus` when available).
5. Specialist authoring pass:
   - Primary: subagent (`clink`) when available.
   - Fallback: built-in test-specialist persona.
   - Optional augmentation: PAL `testgen` when enabled and available.
6. Layered generation:
   - Unit tests are mandatory.
   - Smoke/integration/e2e/regression are generated when applicable.
   - Non-applicable layers require explicit `N/A` with evidence.
7. Verification gate on touched code coverage (default `>=90`).

## Deterministic Rules

- If an explicit touched-file list is provided, treat it as the source of truth.
- Otherwise, resolve touched scope from VCS in this order: `git status` first, then `git diff`.
- If VCS-based resolution yields no trustworthy scope, fall back to requirement/feature-to-file mapping.
- If none of these sources are trustworthy, stop and request explicit scope before proceeding.
- Coverage is pass/fail for touched code; missing coverage evidence fails closed.
- Always return a traceability matrix from requirement IDs to test IDs.

## Output Contract

Return all sections:

1. `traceability_matrix`
2. `layer_plan` (unit/smoke/integration/e2e/regression)
3. `coverage_gate` (target, measured, status)
4. `na_layers` with rationale and evidence
5. `test_artifacts` list by file and layer

Detailed output and heuristics are defined in:

- `references/output_contract.md`
- `references/layer_policy.md`

## Python and JS/TS v1 Focus

Prioritize first-class support for:

- Python (`pytest`)
- JS/TS (`jest`, `vitest`)

For other stacks, keep behavior conservative and explicit about unsupported assumptions.

## Local Utility Scripts

Use bundled scripts for deterministic preprocessing and gate evaluation:

- `scripts/testgen_workflow.py`
- `scripts/testgen_cli.py`

Example:

```bash
python scripts/testgen_cli.py \
  --mode tdd-driver \
  --source feature-list \
  --payload-file /abs/path/features.txt \
  --coverage-target 90 \
  --preferred-cli auto \
  --use-pal-testgen auto
```
