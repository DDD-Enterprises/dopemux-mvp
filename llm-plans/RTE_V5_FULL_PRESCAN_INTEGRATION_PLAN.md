# RTE v5 Full Prescan Integration Plan

## Objective
Promote prescan from an optional advisory helper to a canonical preflight stage inside `run_extraction_v5.py` and canonical operator paths. This preserves `run_extraction_v5.py` as the extraction authority while keeping online prescan spend explicitly gated.

## Risk Level
High

## Task Class
Architecture-sensitive + call-flow-sensitive + API-sensitive.
Requires PAL chain: `analyze -> tracer -> thinkdeep -> challenge -> planner -> challenge -> codereview -> precommit`.

## Authorized Scope
- `services/repo-truth-extractor/run_extraction_v5.py`
- `services/repo-truth-extractor/run_prescan.py`
- `services/repo-truth-extractor/lib/prescan/**`
- `services/repo-truth-extractor/lib/intelligence_router.py`
- `src/dopemux/commands/extract_commands.py`
- `src/dopemux/commands/extractor_commands.py` (only if still part of canonical operator messaging)
- Relevant extractor/prescan tests
- Relevant extractor/prescan docs

## Forbidden Scope
- No extraction-v5 architecture rewrite beyond prescan stage integration.
- No broad provider framework redesign.
- No collapsing prescan into a new standalone authority.
- No hidden online spend defaults.
- No unrelated cleanup safari.

## Invariants
- `run_extraction_v5.py` remains canonical extraction runtime.
- `dopemux` remains coordinator/operator surface, not extraction owner.
- Extracted artifacts remain evidence artifacts, not runtime truth.
- Scope reduction remains explicit, not silent.
- Online prescan spend requires explicit authorization.

## Commit-Sized Slice Plan

### Slice 1: Harden Prescan Online Execution
**Objective**: Harden prescan online execution first.
**Why**: Current prescan is not safe enough to integrate into canonical flow.
**Verification**: Existing prescan hardening tests plus new route-consumption and online-gate tests.

### Slice 2: Add Integrated Prescan Stage to v5
**Objective**: Add integrated prescan stage to `run_extraction_v5.py`.
**Behavior**: Canonical v5 run creates a `prescan` subdir under the run tree, runs local prescan by default, loads router/intelligence from that subdir.
**Verification**: Integration test proving prescan stage runs and router is loaded.

### Slice 3: Unify Flag Contract
**Objective**: Unify flag contract.
**Behavior**: Deprecate dual `--prescan` / `--prescan-dir`; replace with:
  - `--skip-prescan`
  - `--prescan-import-dir`
  - `--allow-online-llm`
  - `--prescan-online`
  - `--prescan-allow-scope-reduction`
**Verification**: CLI tests covering defaults and mutual exclusions.

### Slice 4: Wire Canonical Operator Paths
**Objective**: Wire canonical operator paths.
**Behavior**: `dopemux extract truth-run` and canonical upgrades path invoke integrated v5 flow, not standalone prescan choreography.
**Verification**: `truth-run` CLI tests and operator-path tests.

### Slice 5: Add Artifact and Receipt Contract
**Objective**: Add artifact and receipt contract.
**Behavior**: Prescan writes under v5 run tree with stage receipt (`prescan_stage_receipt.json`) and attempt evidence.
**Verification**: Artifact schema tests and docs/runtime parity tests.

## Required Tests
At minimum:
- `truth-run` runs integrated local prescan by default.
- `--skip-prescan` bypasses stage 0.
- `--prescan-import-dir` uses external prescan instead of running local stage.
- Integrated prescan artifacts land under the v5 run tree (`.../v5/runs/<run_id>/prescan/`).
- Integrated router is loaded into partitioning.
- Scope reduction does not occur without explicit opt-in.
- Integrated online prescan requires `--allow-online-llm`.
- Routing-plan failure blocks integrated online prescan correctly.
- Docs and runtime flag names match.

## Proof Artifact
A proof file will be generated at `proof/rte_v5_full_prescan_integration.proof.json` covering slice completions, tests, code review status, residual risks, and PR URL.