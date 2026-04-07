---
id: REPO_TRUTH_EXTRACTOR_V5_PROMPT_AUTHORITY_DECISION_2026-04-01
title: Repo Truth Extractor v5 Prompt Authority Decision (2026-04-01)
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-07-01'
prelude: Prompt authority and collection decision note for TP-CODEX-RTE-V5-COLLECT-AND-HARDEN-20260401.
---
# Repo Truth Extractor v5 Prompt Authority Decision (2026-04-01)

## Canonical Prompt Root

Observed authority for this implementation branch:

- canonical prompt root: [services/repo-truth-extractor/promptsets/v4/prompts](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/prompts)
- canonical promptset contract companions:
  - [services/repo-truth-extractor/promptsets/v4/promptset.yaml](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/promptset.yaml)
  - [services/repo-truth-extractor/promptsets/v4/artifacts.yaml](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/artifacts.yaml)
  - [services/repo-truth-extractor/promptsets/v4/model_map.yaml](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/model_map.yaml)
- legacy fallback root: [services/repo-truth-extractor/prompts/v3](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/prompts/v3)
- alternate Phase S registry root: [services/repo-truth-extractor/prompts/phase_s](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/prompts/phase_s)

Observed in the canonical v4 root already present on this branch:

- [PROMPT_G5_AUTH_FLOW_SURFACE.md](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_G5_AUTH_FLOW_SURFACE.md)
- [PROMPT_Q11_ARTIFACT_COLLISION_REPORT.md](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_Q11_ARTIFACT_COLLISION_REPORT.md)
- [PROMPT_R11_SECURITY_RISK_SYNTHESIS.md](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R11_SECURITY_RISK_SYNTHESIS.md)

Conclusion:

- No prompt-file additions are required from candidate branches just to reach the current canonical 130-file surface.

## Collection Plan

| Source | Files of interest | Drift type | Recommended action | Decision basis |
| --- | --- | --- | --- | --- |
| `prmerge/20260330_154557-360` worktree `/private/tmp/dopemux-pr-merge-360-20260330_154557` | `promptsets/v4/artifacts.yaml`, `promptsets/v4/model_map.yaml`, `promptsets/v4/prompts/PROMPT_A5_HOOKS_SURFACE.md`, `promptsets/v4/prompts/PROMPT_R11_SECURITY_RISK_SYNTHESIS.md` | mixed | inspect only | Same 130 count but prompt/config drift remains; no direct prompt-root authority gain over current branch |
| `codex/fl-int-f0-runtime-restoration` worktree `/Users/hue/code/dopemux-resolve-372` | `run_extraction_v5.py` | runner-only | inspect only | Prompt fingerprint matches current branch exactly; only runtime drift remains |
| `opus/v5-extractor-schema-expansion` worktree `/Users/hue/code/dopemux-work-20260330` | `run_extraction_v5.py`, `run_fl_int.py`, `fl_int/**`, `PROMPT_R11_SECURITY_RISK_SYNTHESIS.md` | mixed | ignore for prompt authority; inspect only for later runtime overlap | Same-count prompt drift plus FL-int/schema expansion outside this TP's prompt authority needs |
| `codex/v5-extractor-production-recovery` | `run_extraction_v5.py`, `lib/batch_clients.py`, `lib/batch_retriever.py`, `lib/phase_contract_map.py`, docs | mixed | manual port only if later overlap is needed | Contains relevant live-batch gating ideas but also older prompt/config state and deletions |
| `feat/v5-prompt-refactor-and-system-cleanup` | `promptsets/v4/{promptset,artifacts,model_map}.yaml`, `PROMPT_S12_STABILITY_SIGNATURE.md` | mixed | ignore | Removes current `G5/Q11/R11` entries and drops current promptset surfaces |
| `feat/v5-ready-cheap-models` | `promptsets/v4/model_map.yaml`, `promptsets/v4/{promptset,artifacts}.yaml`, broad prompt rewrites | mixed | ignore | Routing/model experiment branch; also removes current `G5/Q11/R11` entries |
| `stash@{Thu Mar 26 15:55:12 2026}` | `run_extraction_v5.py`, `lib/batch_clients.py`, `lib/batch_retriever.py`, `lib/phase_contract_map.py`, extraction docs | mixed | open stash contents, then manual port selective hunks only | Stash contains relevant live-batch consent and retrieval work but cannot be applied wholesale |

## Accepted Drift Files To Port

Accepted at Stage 1:

- none

Reason:

- The current branch already contains the canonical v4 additions (`G5`, `Q11`, `R11`).
- Candidate branch prompt/config deltas either regress current prompt authority or represent branch-local routing experiments rather than canonical prompt truth.

## Rejected Drift Files

Rejected as prompt-authority sources:

- `prmerge/20260330_154557-360`
  - [artifacts.yaml](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/artifacts.yaml)
    - rejects current FL-int artifact entries and removes current `allow_empty_array_fields.status` allowances
  - [model_map.yaml](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/model_map.yaml)
    - cheap-model routing experiment (`grok-4-1-fast-reasoning`, `openai/gpt-5-mini`) rather than prompt authority
  - [PROMPT_A5_HOOKS_SURFACE.md](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_A5_HOOKS_SURFACE.md)
    - duplicates path blocks and broadens generic rules without proving canonical superiority
  - [PROMPT_R11_SECURITY_RISK_SYNTHESIS.md](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R11_SECURITY_RISK_SYNTHESIS.md)
    - removes explicit evidence-anchor requirements currently present on this branch
- `feat/v5-prompt-refactor-and-system-cleanup`
  - rejects `G5`, `Q11`, and `R11` entries from promptset/model/artifact contracts
- `feat/v5-ready-cheap-models`
  - rejects `G5`, `Q11`, and `R11` entries from promptset/model/artifact contracts

## artifacts.yaml, model_map.yaml, and promptset.yaml Drift Classification

Current branch authority classification:

- [promptset.yaml](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/promptset.yaml)
  - authoritative for prompt-to-step contract mapping on this branch
- [artifacts.yaml](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/artifacts.yaml)
  - authoritative for artifact writer/reader expectations on this branch
- [model_map.yaml](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/model_map.yaml)
  - authoritative for current branch routing contract, but candidate branch changes to it are not automatically authoritative

Candidate-branch drift classification:

- `prmerge/20260330_154557-360` changes to these files are branch-local experiments, not canonical upgrades to import wholesale
- `feat/v5-prompt-refactor-and-system-cleanup` and `feat/v5-ready-cheap-models` changes are rejected as authority because they regress current promptset membership

## Phase S Overlap

Observed:

- `run_extraction_v5.py` points Phase S at the registry-backed [prompts/phase_s](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/prompts/phase_s) surface in normal resolution.
- The checked-in Phase S registry tests expect `S0-S12`.
- The checked-in Phase S post-tail prompt tests verify prompt files `S7` through `S12` under the phase_s root.
- Current `run_extraction_v5.py` still restricts step-selection validation text and `PHASE_S_BASE_STEPS` to `S0-S6`.

Decision:

- Phase S overlap with the v4 promptset is unresolved, not cleanly stale.
- The registry-backed `phase_s` surface is clearly intentional.
- The current runtime contract around which `S` steps are selectable and required is drifted.
- No prompt-authority merge should collapse Phase S registry truth into the v4 root until the runtime/test mismatch is reconciled in code.
