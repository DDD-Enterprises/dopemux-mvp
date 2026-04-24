# RTE Pre-Run Hygiene Stage 4 Consensus

Date: 2026-04-23

## Ambiguous Candidates Reviewed

- `.claude/`
- `.dopemux/`
- `.conport/`
- `proof/`
- `reports/`
- `extraction/repo-truth-extractor/v5/doctor/`
- `extraction/repo-truth-extractor/v5/runs/`
- `extraction/repo-truth-extractor/v5/latest_run_id.txt`
- `task-packets/.TP-WAVE7-RTE-UI-DESIGN-2026-04-21A.md.swp`

## Requested PAL Consensus Models

- `gpt-4.1` with `for` stance
- `claude-opus-4.5` with `against` stance

## Actual Provider Results

- `gpt-4.1`
  - failed with `insufficient_quota`
- `claude-opus-4.5`
  - unavailable with current provider keys

## Decision Rule Applied

Because the requested heterogeneous consensus could not execute literally, no synthetic model agreement was claimed.

Fallback operator rule:

- where ambiguity remained, default to truth-preservation-first
- use physical cleanup only for artifacts with no plausible truth role
- treat all ambiguous heavy trees as exclusion-only candidates

## Consensus Outcome

- preserve in place:
  - `.claude/`
  - `.dopemux/`
  - `.conport/`
  - `proof/`
  - `reports/`
  - RTE doctor/latest/runs evidence
- safe for physical cleanup:
  - `.DS_Store`
  - `__pycache__/`
  - `*.pyc`
  - `*.pyo`
  - `task-packets/.TP-WAVE7-RTE-UI-DESIGN-2026-04-21A.md.swp`
