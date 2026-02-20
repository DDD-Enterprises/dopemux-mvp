---
id: EXTRACTION-PROMPT-CONTRACT-V4
title: Extraction Prompt Contract V4
type: reference
owner: '@hu3mann'
date: '2026-02-20'
author: '@codex'
prelude: Required prompt sections and validation rules for Repo Truth Extractor v4 prompts.
graph_metadata:
  node_type: DocPage
  impact: high
  relates_to:
    - services/repo-truth-extractor/promptsets/v4/promptset.yaml
    - services/repo-truth-extractor/promptsets/v4/prompts/
    - scripts/repo_truth_extractor_promptset_audit_v4.py
---
# Extraction Prompt Contract v4

Repo Truth Extractor v4 prompt files live in `services/repo-truth-extractor/promptsets/v4/prompts/` and must satisfy a strict section contract.

## Required sections

Each prompt must include non-empty `##` sections:

- `Goal`
- `Inputs`
- `Outputs`
- `Schema`
- `Evidence Rules`
- `Determinism Rules`
- `Anti-Fabrication Rules`
- `Failure Modes`

## Prompt naming

- Filename format: `PROMPT_<STEP_ID>_<TITLE>.md`
- Step ID format: `<PHASE><NUMBER>` (example: `C10`)
- Ordering is numeric by step number within phase (for example `C9`, then `C10`)

## Output declaration

- Prompts must declare explicit output artifact filenames.
- Output filenames must be present in `services/repo-truth-extractor/promptsets/v4/artifacts.yaml` with matching phase.
- Canonical writer is declared in artifact registry, not inferred from prompt text.

## Evidence requirements

Load-bearing claims should include evidence fields:

- `path` (repo-relative)
- `line_range` (`[start,end]`)
- `excerpt` (<= 200 chars)

When evidence is unavailable, output must use explicit `UNKNOWN` placeholders.

## Determinism requirements

- Norm payloads must not include temporal keys:
  - `generated_at`
  - `timestamp`
  - `created_at`
  - `updated_at`
  - `run_id`
- Stable sort and stable dedup rules are required for list outputs.

## Lint workflow

Run strict lint:

```bash
python scripts/repo_truth_extractor_promptset_audit_v4.py --strict
```

Generate audit report:

```bash
python scripts/repo_truth_extractor_promptset_audit_v4.py \
  --strict \
  --report-out docs/05-audit-reports/RTE_V4_PROMPTSET_AUDIT_$(date +%F).md \
  --json-out reports/RTE_V4_PROMPTSET_AUDIT.json
```
