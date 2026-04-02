---
id: REPO_TRUTH_EXTRACTOR_V5_PRELIVE_CONSOLIDATED_2026-04-01
title: Repo Truth Extractor v5 Pre-Live Consolidated Audit (2026-04-01)
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-04-01'
last_review: '2026-04-01'
next_review: '2026-07-01'
prelude: Consolidated ledger for repo-truth-extractor v5 prompt authority, worktree drift, branch-only drift, and stash provenance before bounded pre-live hardening.
---
# Repo Truth Extractor v5 Pre-Live Consolidated Audit (2026-04-01)

## 1. Current Canonical Runtime Truth

Directly observed from [run_extraction_v5.py](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v5.py), [promptset.yaml](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/promptset.yaml), and prompt-tree counts:

- Canonical runtime prompt root for non-Phase-S v5 execution is [services/repo-truth-extractor/promptsets/v4/prompts](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/promptsets/v4/prompts).
- Legacy fallback prompt root remains [services/repo-truth-extractor/prompts/v3](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/prompts/v3).
- Alternate Phase S registry root remains [services/repo-truth-extractor/prompts/phase_s](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/prompts/phase_s).
- The current branch prompt count under the canonical v4 root is 130 `PROMPT_*.md` files.
- A detached snapshot at `/Users/hue/code/dopemux-resolve-373` has the same canonical v4 prompt fingerprint as the current branch for `services/repo-truth-extractor/promptsets/v4/prompts`.
- `130 prompts` is valid for the canonical v4 runtime prompt root only. It is not safe shorthand for the whole repo.
- Same-count prompt trees are not equivalent by count alone:
  - `/private/tmp/dopemux-pr-merge-360-20260330_154557` has 130 prompt files but does not match the current v4 prompt fingerprint.
  - `/Users/hue/code/dopemux-work-20260330` has 130 prompt files but does not match the current v4 prompt fingerprint.

Observed runtime overlap that remains unresolved rather than normalized:

- [run_extraction_v5.py](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v5.py) still limits `PHASE_S_BASE_STEPS` and step validation text to `S0-S6`.
- Checked-in tests in [test_run_extraction_v5_promptset_truth.py](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/tests/test_run_extraction_v5_promptset_truth.py) and [test_phase_s_prompt_registry.py](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/tests/test_phase_s_prompt_registry.py) expect `S0-S12`.
- Conclusion: Phase S overlap between v4 promptset and registry-backed prompt roots is real, but its active runtime contract is drifted and must be treated as unresolved until reconciled in code and tests.

## 2. Prompt Inventory by Location

Prompt-bearing locations were counted by scanning for `PROMPT_*.md` plus broader `prompt*` filenames where needed.

| Location | Path | Count | Notes |
| --- | --- | ---: | --- |
| canonical v4 | `services/repo-truth-extractor/promptsets/v4/prompts` | 130 prompt files | Canonical non-S runtime prompt root |
| legacy v3 | `services/repo-truth-extractor/prompts/v3` | 109 prompt files | Legacy fallback root |
| phase_s | `services/repo-truth-extractor/prompts/phase_s` | 13 prompt files | Registry-backed alternate Phase S surface |
| archive | `services/repo-truth-extractor/archive` | 38 prompt files | Non-canonical archive copy |
| base | `services/repo-truth-extractor/prompts/base` | missing | No prompt base directory observed in this checkout |
| fixtures | `services/repo-truth-extractor/tests/fixtures` | 2 prompt files | Test fixtures only |
| benchmark copy | `tools/prompt_rewrite_v4/benchmark/prompts` | 105 prompt files | Benchmark copy, not runtime authority |
| tmp copies | `tmp` | 2 prompt files, 9 broader prompt-named files | Temporary evidence only |
| docs copies | `docs` | 42 prompt files, 170 broader prompt-named files | Historical/docs copies only |

## 3. Worktree Drift Summary

### Stale 127/128 prompt-count states

- 127-count worktrees:
  - `/private/tmp/dopemux-execution-replacement`
  - `/private/tmp/dopemux-memory-stack`
  - `/private/tmp/dopemux-pr-merge-312-20260329_203806`
  - `/private/tmp/dopemux-pr-merge-312-20260329_205912`
  - `/private/tmp/dopemux-pr-merge-312-live_drain_002`
  - `/private/tmp/dopemux-pr-merge-351-20260329_185921`
  - `/Users/hue/.gemini/tmp/dopemux-mvp/fix-routing`
- 128-count worktree:
  - `/private/tmp/dopemux-pr-merge-359-20260330_153827`

These are stale prompt-count states relative to the current canonical 130-file v4 root.

### 130-count worktrees matching current canonical v4 prompt fingerprint

- `/Users/hue/code/dopemux-mvp` on `codex/rte-v5-collect-and-harden-20260401`
- `/Users/hue/code/dopemux-resolve-372` on `codex/fl-int-f0-runtime-restoration`
- `/Users/hue/code/dopemux-resolve-373` detached

Note:
- `codex/fl-int-f0-runtime-restoration` still has non-prompt drift in [run_extraction_v5.py](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v5.py), but its canonical v4 prompt corpus matches the current branch.

### 130-count worktrees with content drift

- `/private/tmp/dopemux-pr-merge-360-20260330_154557` on `prmerge/20260330_154557-360`
- `/private/tmp/dopemux-pr-merge-363-drain_attempt_3` on `prmerge/drain_attempt_3-363`
- `/Users/hue/code/dopemux-pr-362`
- `/Users/hue/code/dopemux-resolve-364`
- `/Users/hue/code/dopemux-resolve-367`
- `/Users/hue/code/dopemux-resolve-370`
- `/Users/hue/code/dopemux-work-20260330` on `opus/v5-extractor-schema-expansion`

### Unrelated, partial, prunable, or absent extractor surfaces

- Missing/prunable worktrees:
  - `/private/tmp/dopemux-fl-int-f0-runtime-main`
  - `/private/tmp/dopemux-main-clean`
  - `/Users/hue/code/dopemux-mvp/llm-plans/ci-fix-worktree`
- Partial/non-authoritative prompt roots:
  - `/private/tmp/dopemux-pr-merge-flight-visibility` has 0 canonical v4 prompt files
  - `/private/tmp/dopemux-pr310` has 0 canonical v4 prompt files
  - `/private/tmp/dopemux-pr310-fix` has 0 canonical v4 prompt files
  - `/private/tmp/dopemux-pr321` has 4 canonical v4 prompt files

## 4. Branch-Only Drift

Inspected against current local `main` and then against the new collection branch:

- `codex/v5-extractor-production-recovery`
  - Mixed runtime/config/docs drift.
  - Contains batch-policy and retrieval work, but also older prompt/config state and deletions of now-present FL-int surfaces.
- `feat/v5-prompt-refactor-and-system-cleanup`
  - Large prompt/config rewrite branch.
  - Removes current `G5`, `Q11`, and `R11` prompt/model-map entries and drops FL-int-related promptset metadata.
  - Not acceptable as a prompt authority source for this TP.
- `feat/v5-ready-cheap-models`
  - Routing/model-map experiment branch.
  - Also removes current `G5`, `Q11`, and `R11` prompt/model-map entries.
  - Not acceptable as a prompt authority source for this TP.

## 5. Stash Provenance

Relevant stash identified:

- `stash@{Thu Mar 26 15:55:12 2026}` on `codex/v5-extractor-production-recovery`

Observed from stash name-status and targeted diff inspection:

- It is relevant to extractor recovery/hardening.
- It is mixed, not prompt-only:
  - docs
  - batch clients
  - batch retriever
  - phase contract map
  - run_extraction_v5 live-batch policy
- It includes explicit live-batch consent language around `DPMX_LIVE_OK=1`, provider restrictions, and multi-provider batch retrieval.
- It also carries broader churn and older-tree deletions, so it is not safe to apply wholesale.

Collection rule for this stash:

- selective manual port only after file-level review
- no direct stash apply

## 6. Superseded or Disputed Findings

Historical blanket claims that are unsafe as universal truth after current inspection:

- `130 prompts` as repo-wide truth
  - superseded
  - safe only for the canonical v4 runtime prompt root
- same-count prompt trees are equivalent
  - superseded
  - disproven by `prmerge/20260330_154557-360` and `opus/v5-extractor-schema-expansion`
- prompt authority can be inferred from whichever branch was last touched
  - superseded
  - branch-only drift and stash-only drift both exist
- whole-promptset rewrite branches are safe collection sources by prompt count alone
  - superseded
  - `feat/v5-prompt-refactor-and-system-cleanup` and `feat/v5-ready-cheap-models` both conflict with the current canonical additions

Previously cited runtime claims requiring caution until re-proven in code paths:

- statements about spend-ledger deadness or non-use must be treated as disputed unless the current runtime lanes are traced directly in [run_extraction_v5.py](/Users/hue/code/dopemux-mvp/services/repo-truth-extractor/run_extraction_v5.py) and exercised by tests

## 7. Immediate Patch Scope

Bounded pre-live hardening scope for this TP only:

- repair `R0` numbering / prompt hygiene
- make `spend_ledger.py` model-aware with explicit unknown-model policy
- map runtime spend lanes and enforce live `--max-cost-usd`
- surface truncation salvage warnings
- surface deterministic sidefill conflicts where feasible
- improve degraded dependency visibility for phase prerequisites
- add `--list-phases`
- improve `DPMX_LIVE_OK` discoverability
- add tests, validation runs, and proof bundle

## 8. Deferred Backlog

Explicitly deferred out of this TP:

- first-live staged preset
- routing-policy cost guide
- cost preview per phase
- retry-cost visibility
- per-phase dry-run checklist
- single-partition billing verification drill
- v5/v3 output-path fix or compatibility cleanup
- `--output-root`
- invalid-argument recovery improvements
- stratified help
- prescan clarity
- timeout/zombie-wait review
- unsupported input warnings
- prompt bloat audit
- legacy-context leakage reduction
- thin-phase skip heuristics
- excerpt-length review
- partition completeness review
- protect Phase S from weak R
- split `run_extraction_v5.py`
