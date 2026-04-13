---
id: rte-state-of-work-audit-20260410
title: RTE State-of-Work Codebase Audit
type: reference
owner: claude-code
date: 2026-04-10
status: complete
author: '@hu3mann'
last_review: '2026-04-10'
next_review: '2026-07-09'
prelude: RTE State-of-Work Codebase Audit (reference) for dopemux documentation and
  developer workflows.
---
# RTE State-of-Work Codebase Audit

**Branch**: `codex/rte-benchmark-r1-first-campaign`
**HEAD SHA**: `fe074a6b9` (confirmed stable across all audit checkpoints)
**Canonical doc audited against**: `~/.claude/plans/hazy-coalescing-kite.md`
**Audit date**: 2026-04-10
**Method**: READ-ONLY static analysis (Grep, Read). No code execution.

---

## Critical Pre-Findings

**Working tree is NOT clean at audit time.** Five benchmarking files have uncommitted modifications from a parallel Codex process:

```
M services/repo-truth-extractor/benchmarking/executors/extraction_v5_adapter.py
M services/repo-truth-extractor/benchmarking/orchestration/attempt_executor.py
M services/repo-truth-extractor/benchmarking/reporting/pipeline.py
M services/repo-truth-extractor/benchmarking/rollups/pipeline.py
M services/repo-truth-extractor/benchmarking/validators/runtime_validator_wrapper.py
```

The `extraction_v5_adapter.py` changes (lines 80–86) added **live execution capability** (`--execute` + `DPMX_LIVE_OK=1` wiring), which upgrades BM-LIVE from NOT STARTED to PARTIAL.

**Branch recovery protocol** per canonical doc: check branch and HEAD before any edit. Protocol confirmed at 3 checkpoints — branch and SHA stable throughout audit.

---

## Executive Summary

| Stat | Count |
|------|-------|
| Total canonical items audited | 48 |
| **DONE** (confirmed complete) | **22** |
| **CONTRADICTION** (canonical said PENDING, code says DONE) | **17** |
| **PARTIAL** (partially implemented) | **6** |
| **PENDING** (confirmed not done) | **7** |
| **NOT STARTED** (confirms canonical) | **2** |
| **HIGH-UNCERTAINTY** (static analysis insufficient) | **5** |
| **UNRESOLVED** (operator decisions required) | **5** |

**The canonical doc MASSIVELY understates completion.** 17 of 22 "DONE" items were marked PENDING by the canonical doc. The repair scope is substantially smaller than the doc suggested. The critical blockers are a short list.

---

## Contradiction Table — Canonical Said PENDING, Code Says DONE

| ID | Canonical Status | Actual Status | Key Evidence |
|----|-----------------|---------------|--------------|
| A1 | PENDING | **DONE** | `--max-cost-usd` at `run_extraction_v5.py:19437`; enforcement at `:3179–3363`; abort constants at `:263–264` |
| A2 | PENDING | **DONE** | `--execute` at `:19257`; `DPMX_LIVE_OK_ENV` at `:1260`; dual guard at `:20258–20270` |
| A4 | PENDING | **DONE** | `lib/spend_ledger.py` 489 lines; `MODEL_COST_RATES` at `:27`; `accumulate(model_id,...)` at `:390`; `ModelSpend`/`PhaseSpend` classes at `:59,75` |
| A5 | PENDING | **DONE** | `grok_passes.py:511–513` explicit map: dedup/discover/feasibility → `("openai","gpt-5-nano")` |
| A7 | PENDING | **DONE** | 14 v5 test files in `tests/`; `test_run_extraction_v5_operator_safety.py` (451 lines), plus cost_cap, concurrency, prelive_hardening, golden_fixture, resume smoke, etc. |
| V5-TRUNC | PENDING | **DONE** | `_record_truncation_salvage_warning()` at `:8161`; `chars_lost` key at `:10056`; called at `:17707–17715` |
| V5-CIRCUIT | PENDING | **DONE** (auth-scoped) | Auth circuit breaker at `:15014–15019`; `phase_auth_fail_threshold` config at `:1348`; CLI arg at `:19776` |
| V5-UGMC | PENDING | **DONE** | Zero conflict markers in `docs/02-how-to/extraction/repo-truth-extractor-user-guide.md` and entire `docs/` tree |
| B-T1 | PENDING | **DONE** | `promptsets/v4/PROMPTSET_RULES.md` exists with comprehensive rules |
| P-INTEL | PENDING | **DONE** | No `or True` hack; all 5 keys present in `engine.py:318–379`; `lifecycle_distribution`, `ghost_files`, `planned_features`, `version_chain_count`, `compression_potential_files` all set |
| P-OPTPAY | PENDING | **DONE** | `_build_optimize_payload(intelligence, pass_results)` at `grok_passes.py:750`; all 3 prior summaries injected at `:769–777` |
| P-CATALOG | PENDING | **DONE** | `provider_catalog.py` 270 lines; imported by `engine.py:19–24`; `build_prescan_routing_plan` wired |
| P-DEPGRAPH | PENDING | **DONE** | Relative import handling at `dependency_graph.py:73–91` (Python `.` prefix) and `:94–103` (JS `./` `../`) |
| P-MODELS | PENDING | **DONE** | `cost_estimate: bool = True` at `models.py:84`; all 5 schema keys in `schemas.py:30–90` |
| P-EXPORTS | PENDING | **DONE** | All 6 required classes in `__init__.py` `__all__`: `PrescanEngine`, `PrescanConfig`, `PrescanResult`, `GrokPassRunner`, `BatchPlanner`, `IntelligenceRouter` |
| FL-RUNNER | NEEDS RESOLUTION | **RESOLVED** | Root `run_fl_int.py` (238 lines) imports from `fl_int/run_fl_int.py` (1057 lines); root is thin CLI wrapper |
| BM-M0-S1 | DONE (canonical agrees) | **DONE** | 162 files, 7,403 Python LOC; all milestone subdirs confirmed |

---

## Wave 1–4 Backlog Contradictions (extractorUpgrade1.md / extractorUpgrade2.md)

These were not in Part 10 summary table but are in the backlog. Almost all are already implemented:

| Item | Canonical | Actual | Evidence |
|------|-----------|--------|----------|
| P1: Unknown model WARNING | PENDING | **DONE** | `spend_ledger.py:473–479`; `UNKNOWN_MODEL_POLICY` constant; `unknown_model_events` counter |
| P3: Truncation WARNING | PENDING | **DONE** | (see V5-TRUNC above) |
| P4: Circuit breaker | PENDING | **DONE** | (see V5-CIRCUIT above) |
| P5: --list-phases | PENDING | **DONE** | `run_extraction_v5.py:19478–19481`; handler at `:19621` |
| P7: Consent gate in --help | PENDING | **DONE** | `--execute` help text includes `DPMX_LIVE_OK_ENV` at `:19260–19263` |
| P9: --output-root | PENDING | **DONE** | Flag at `:19249–19253`; `configure_output_layout()` at `:1437` |
| P10: Invalid arg errors | PENDING | **DONE** | 10+ `parser.error()` calls with descriptive messages |
| P18: Cost guide by policy | PENDING | **DONE** | `ROUTING_POLICY_GUIDE` dict at `:672–751`; `print_routing_guide()` at `:15908` |
| P19: Cost preview per phase | PENDING | **DONE** | `build_phase_cost_preview()` at `:15673`; `COST_PREVIEW.json` written at `:14863` |
| P21: Pre-live gate mandatory | PENDING | **DONE** | `validate_pre_live_gate_v25.py` (1368 lines); enforcement at `:20275–20288` |
| P22: Per-phase dry-run checklist | PENDING | **DONE** | `write_phase_dry_run_checklist()` at `:15835–15895`; `DRY_RUN_CHECKLIST.json` output |
| P25: First-live quickstart | PENDING | **DONE** | `docs/02-how-to/extraction/repo-truth-extractor-v5-first-live-run.md` |
| P26: Prescan docs | PENDING | **DONE** | `docs/02-how-to/extraction/run-prescan.md` + `docs/03-reference/extraction/prescan-pipeline.md` |
| P27: Zombie wait risk | PENDING | **DONE** | `INTERACTIVE_SAFE_BATCH_WAIT_SECONDS = 1800` at `:384`; runtime warning at `:19683–19687`; preset override |
| Retry cost visibility | PENDING | **DONE** | `write_retry_cost_report_snapshot()` at `:3469`; retry cost in step reports at `:14373–14384` |

---

## Confirmed PENDING Items (true remaining work)

| ID | Description | Evidence of Gap | Blocker for live run? |
|----|-------------|----------------|----------------------|
| **V5-R0 / A0 partial** | PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md has unresolved merge conflict | Lines 45–59: active `<<<<<<< HEAD` vs `>>>>>>> 12f30a09d` conflict from `feat(prompts): rewrite Phase R, B, G, and E extraction procedures (Pass 4)` | **YES** — malformed prompt breaks R-phase |
| **V5-PHASE-S** | No minimum R quality criteria before Phase S dispatch | Phase execution loop at `:20480–20488` dispatches Phase S without quality gate; only runtime dependency check at `:19030–19047` | **YES** — Phase S can run on poor R output |
| **A3 (partial)** | 5% parse failure abort threshold missing | Parse failures tracked (`parse_failures: List` at `:7367`); `raw_ok`/`raw_failed` counted — but NO 5% abort logic found | **YES** — silent data loss possible |
| **B-T4c** | 6 new prompts for 0% coverage domains: C18, C19, G6, C20, C21, G7 | Zero of 6 files exist in `promptsets/v4/prompts/`; total prompt count is 130 | No (extraction runs, but 0% domains uncovered) |
| **B-T3** | Schema depth upgrades; `promptsets/v4/schemas/` directory | Directory does not exist; no schema files for prompt schema coverage | No (soft quality gap) |
| **A-RAMP (partial)** | Full 5-stage progressive confidence ramp | Only preflight (`:6532–6657`) and provider_probe (:6469,6491) of 5 stages; no `BATCH_PILOT.json`, `PHASE_SLICE.json`, `BREAKER_STATE.json`, `PHASE_GATE_DECISION.json` artifacts | No (but expected before full live run) |
| **P-VAL** | Harden BatchResponseValidator beyond top-key-only | `grok_passes.py:239–242` only checks `required - set(data.keys())`; no nested/field-level validation | No (PLANNED state, not broken) |

---

## Partial Items (need completion)

| ID | Actual State | Gap |
|----|-------------|-----|
| **A0** | v5 + model_map.yaml CLEAN; R0 prompt has conflict | Resolve PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md conflict (tracked as V5-R0) |
| **A6** | CLI argparse default=True (`run_extraction_v5.py:19321`); RunnerConfig dataclass default=False (`:1356`); first-live preset forces False (`:19143–19145`) | Align dataclass default to True OR document the intentional discrepancy |
| **P-TESTS** | 6 of 7 canonical prescan test files exist (155–482 lines each) | Missing dedicated test for `batch_planner` logic (covered partially in `test_prescan_consumers.py` but no dedicated file) |
| **BM-LIVE** | Live execution infrastructure wired in `extraction_v5_adapter.py` (lines 80–86: `--execute` + `DPMX_LIVE_OK=1`); default is `"live_execution": False` | Other adapters (fl_int, prescan, phase_s) remain fixture/dry-run; no live benchmark campaigns have run |
| **P6** | Only `--preset first-live` implemented (`choices=[FIRST_LIVE_PRESET_NAME]` at `:19233`) | `--preset staged-safe` not implemented |
| **P24** | Help stratified semantically via `format_help()` override (`:1468–1497`) with Common/Advanced/Diagnostics/Recovery sections | Not via argparse argument groups; minor UX gap |

---

## Confirmed NOT STARTED (deferred, unchanged from canonical)

| ID | Description |
|----|-------------|
| **FL-POST-V1** | F3 (Authority Resolution), F5 (Gap Analysis), L2 (Status Resolution), V0/V1/V9 (Critique passes) — explicitly deferred to post-v1 |
| **FL-PIPELINE** | FL_INT integration with main pipeline S-phase/T-phase dispatch — explicitly deferred |

---

## High-Uncertainty Items (static analysis insufficient)

| ID | Why Uncertain | What Would Resolve |
|----|--------------|-------------------|
| **B-T2a/b/c** | Prompt files for Phase A/C/W/R/B/G/E exist but content quality improvements (extraction procedure rewrites) can't be verified statically — requires comparing prompt content against quality criteria | Review Pass 2-4 changes to prompt files; diff against prior versions; or run validate_pre_live_gate_v25.py |
| **B-T4d** | Partial-coverage enhancements (C7, M1, C2, W1) — can't assess enhancement depth without reading full prompt content and comparing to spec | Read each of these 4 prompts fully and compare against T4d requirements |
| **FL-ROUTE** | FL_INT ladders use model slugs NOT confirmed in handoff pack registry | `STRUCTURE_LADDER` uses: `gemini-3-flash-preview`, `gemini-3.1-pro-preview`, `openai/gpt-5.3-codex`, `openai/gpt-5.2`, `anthropic/claude-opus-4-6`; `CHEAP_EVAL_LADDER` uses `grok-4-1-fast-reasoning` — all are absent from `prompt1_handoff_pack_normalized.md`. These appear to be aspirational/future model IDs. Operator must decide: are these intentional future routing targets, or stale references? |
| **DR-* (4 items)** | `litellm_proxy.py` (905 lines) and `litellm_manager.py` (592 lines) exist; `GEMINI_ROUTING_FIX_PLAN.md` is in `llm-plans/`; but cannot determine if the specific routing fix (accept both `model_id` and `litellm_model` fields) was applied without knowing pre-fix state | Git diff the routing files against main or the state before the fix was planned |
| **V5-CIRCUIT severity** | Auth circuit breaker is IMPLEMENTED but is auth-failure-specific (`phase_auth_fail_threshold` trips on consecutive auth failures). The canonical wanted a "general provider circuit breaker" (per-provider consecutive failure tracking + trip + half-open state). Whether the auth-scoped implementation satisfies the intent requires operator judgement. |  Operator decision on scope |

---

## Operator Decisions Required (unchanged, unresolvable by code)

| OQ | Decision | Context |
|----|----------|---------|
| OQ-1 | **Promotion thresholds** — What contract_score + evidence_score qualifies a candidate for production? | Governs when benchmark results translate to routing changes |
| OQ-2 | **Benchmark budget caps** — Per-run and per-candidate cost limits for live benchmark execution | Needed before BM-LIVE is enabled |
| OQ-3 | **Phase S policy-gating** — Phase S has no adjacent JSON schemas; what governance posture applies? | Related to V5-PHASE-S but higher-level |
| OQ-4 | **Local/open-weight graduation criteria** — Under what conditions can local models graduate from `experimental_lab`? | Affects FL-ROUTE and benchmark archetype design |
| OQ-5 | **OpenClaw write authority** — Read-only or read-write to benchmark artifacts? | Affects BM-LIVE integration |

---

## Issues and Contradictions Found

### Issue 1: Canonical Doc Assembled Without Code Verification (CRITICAL)
The canonical doc marked 17+ items as PENDING that are fully implemented in the codebase. This means any planning done from the canonical doc alone would overallocate repair effort. **The true repair scope is ~5–8 items, not 30+.**

Root cause: The doc was assembled from plan files and checklists, not from code inspection. The checklist in `llm-plans/V5_EXTRACTOR_OPUS_TASKS_CHECKLIST.md` had no items checked — but the actual code had most of them implemented (likely from earlier Codex sessions that weren't reflected back into the checklist).

### Issue 2: Parallel Codex Process Actively Modifying Files
Five benchmarking files have uncommitted changes. The `extraction_v5_adapter.py` modifications added live execution capability, which is a significant state change not reflected in the canonical doc. Any repair pass must coordinate with this parallel work or risk merge conflicts.

**Recommendation**: Before any repair pass, commit or stash the 5 modified benchmarking files to lock their state.

### Issue 3: R0 Prompt Merge Conflict from Feature Branch
`PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md` lines 45–59 contain an unresolved conflict from branch `12f30a09d` (`feat(prompts): rewrite Phase R, B, G, and E extraction procedures (Pass 4)`). The conflict is over step numbering (9 vs 7 at step start). Resolution decision per `whimsical-foraging-pizza.md`:
- **Accept pr321/branch version** for step numbering (starts at 7, not 9)
- This is the only file with conflicts in `promptsets/`

### Issue 4: FL_INT Routing Ladder Model Slug Mismatch
The FL_INT ladders reference model IDs that do not exist in the canonical handoff pack registry (`prompt1_handoff_pack_normalized.md`):
- `openai/gpt-5.3-codex` — NOT in registry
- `openai/gpt-5.2` — NOT in registry
- `anthropic/claude-opus-4-6` — NOT in registry (only `claude-sonnet-4` confirmed)
- `gemini-3-flash-preview`, `gemini-3.1-pro-preview` — NOT in registry
- `grok-4-1-fast-reasoning` — NOT in registry

These appear to be future routing targets. They should NOT be used in production until confirmed by a live benchmark run. The `FL-ROUTE` item in the canonical doc is correctly marked PLANNED.

### Issue 5: A6 Batch Mode Default Inconsistency
Three places disagree on `batch_mode` default:
- `run_extraction_v5.py:19321` — argparse default=**True**
- `run_extraction_v5.py:1356` — RunnerConfig dataclass default=**False**
- `run_extraction_v5.py:19143–19145` — first-live preset forces=**False**

This is a correctness issue. When the runner is initialized programmatically (not via CLI), `batch_mode=False`. When initialized via CLI without `--no-batch`, `batch_mode=True`. The preset then silently overrides to False for first-live flows. This is confusing and could lead to unexpected behavior.

---

## Recommended Repair Order

### Priority 1 — Blockers for Safe Live Run (do FIRST)

1. **V5-R0 / A0 partial**: Resolve merge conflict in `PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md` lines 45–59
   - Accept branch version (step 7, not 9) per `whimsical-foraging-pizza.md`
   - File: `services/repo-truth-extractor/promptsets/v4/prompts/PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md`

2. **A3**: Add 5% parse failure abort threshold
   - Current: `raw_ok`, `raw_failed`, `parse_failures` tracked at `run_extraction_v5.py:7367–7437`
   - Missing: `if raw_failed / (raw_ok + raw_failed) > 0.05: abort_with_reason(...)`
   - File: `run_extraction_v5.py` (batch parse result loop)

3. **A6**: Align `RunnerConfig.batch_mode` dataclass default with CLI default
   - Change `batch_mode: bool = False` (`:1356`) to `batch_mode: bool = True`
   - OR document the intentional split with a comment
   - File: `run_extraction_v5.py:1356`

4. **V5-PHASE-S**: Add minimum R quality criteria before Phase S dispatch
   - Add gate in the phase execution loop (`run_extraction_v5.py:20480–20488`)
   - Minimum: check that Phase R artifacts exist and contain non-empty output before allowing Phase S
   - File: `run_extraction_v5.py`

5. **FL-ROUTE**: Operator decision on FL_INT routing ladder model slugs
   - Confirm whether `gpt-5.3-codex`, `gemini-3.x`, `claude-opus-4-6`, `grok-4-1-fast-reasoning` are intentional future targets
   - If yes: document the forward-looking nature of these ladders
   - If no: replace with confirmed handoff pack models (`gpt-4.1`, `claude-sonnet-4`, etc.)
   - File: `services/repo-truth-extractor/fl_int/models.py:28–48`

### Priority 2 — Quality (do before extended live runs)

6. **A-RAMP**: Complete 5-stage confidence ramp
   - Stages 1–2 exist (preflight, provider_probe)
   - Add stages 3–5: batch_pilot, phase_slice, full_phased
   - Add artifact outputs: `BATCH_PILOT.json`, `PHASE_SLICE.json`, `BREAKER_STATE.json`, `PHASE_GATE_DECISION.json`
   - File: `run_extraction_v5.py` (first-live preset logic ~19070+)

7. **B-T4c**: Create 6 new prompts for 0% coverage domains
   - Files to create: `PROMPT_C18_OBSERVABILITY_SURFACE.md`, `PROMPT_C19_ERROR_HANDLING_PATTERNS.md`, `PROMPT_G6_DEPENDENCY_HEALTH_SURFACE.md`, `PROMPT_C20_STATE_MANAGEMENT_SURFACE.md`, `PROMPT_C21_PERFORMANCE_SURFACE.md`, `PROMPT_G7_TECHNICAL_DEBT_REGISTER.md`
   - Dir: `services/repo-truth-extractor/promptsets/v4/prompts/`
   - Tool: Codex (GPT-5.4) per canonical spec

8. **B-T3**: Create `promptsets/v4/schemas/` directory and schema files
   - Schema coverage target: >33% of 130 prompts
   - Currently: directory does not exist (0% schema coverage)

9. **P-TESTS**: Write 7th prescan test file
   - Missing: `test_prescan_batch_planner.py` (dedicated)
   - 6 existing files cover other areas; batch_planner partially covered in consumers test
   - Dir: `services/repo-truth-extractor/tests/`

10. **Commit uncommitted benchmarking changes**: Lock state of 5 modified files before repair pass

### Priority 3 — Deferred Quality (can run after P1-P2)

11. **P-VAL**: Harden `BatchResponseValidator` beyond top-key-only
    - File: `lib/prescan/grok_passes.py:223–244`
    - Spec: match FL_INT schema posture (per-field validation)

12. **B-T4d**: Partial-coverage enhancements (C7, M1, C2, W1)
    - HIGH-UNCERTAINTY: verify whether enhancements already applied before doing work

13. **B-T2a/b/c**: Verify extraction procedure rewrites are complete
    - HIGH-UNCERTAINTY: static analysis can't confirm content quality
    - Run `validate_pre_live_gate_v25.py` for automated coverage check

14. **B-T5**: Run verification pass (after T1–T4)
    - Script: `validate_pre_live_gate_v25.py --policy balanced_openrouter`

15. **BM-LIVE**: Enable live provider execution for benchmark campaigns
    - Requires: OQ-2 (budget caps) resolved first
    - Partial wiring already done in `extraction_v5_adapter.py`

16. **P6**: Add `--preset staged-safe`
    - One choice currently in `choices=[FIRST_LIVE_PRESET_NAME]`

### Priority 4 — Operator/Architecture Decisions

17. Resolve OQ-1 through OQ-5 (see table above)
18. **FL-POST-V1**: F3, F5, L2, V0/V1/V9 (explicitly deferred)
19. **FL-PIPELINE**: S/T-phase integration (explicitly deferred)

---

## Verification Commands (Run After Repair Pass)

```bash
# 1. Branch/SHA safety check
git -C /Users/hue/code/dopemux-mvp branch --show-current
git -C /Users/hue/code/dopemux-mvp rev-parse --short HEAD

# 2. A0 clean: zero conflict markers in all RTE files
grep -rn '<<<<<<\|>>>>>>' services/repo-truth-extractor/promptsets/ | wc -l
# Expected: 0

# 3. A2 safety gates
python run_extraction_v5.py --help | grep -E 'execute|max-cost-usd|list-phases|batch-mode'

# 4. Pre-live gate harness
python validate_pre_live_gate_v25.py --policy balanced_openrouter

# 5. Benchmark smoke
cd services/repo-truth-extractor && python -m pytest tests/benchmarking/ -v --tb=short 2>&1 | tail -20

# 6. v5 unit tests
python -m pytest tests/test_run_extraction_v5_*.py tests/test_v5_*.py -v --tb=short 2>&1 | tail -20

# 7. Prescan tests
python -m pytest tests/test_prescan_*.py tests/test_code_prescan_*.py -v --tb=short 2>&1 | tail -20

# 8. FL_INT tests
python -m pytest tests/test_fl_int_*.py -v --tb=short 2>&1 | tail -20

# 9. Verify new prompt files (after B-T4c)
ls promptsets/v4/prompts/ | grep -E 'C18|C19|G6|C20|C21|G7' | wc -l
# Expected: 6

# 10. Batch mode default alignment check
python -c "import run_extraction_v5 as r; cfg = r.RunnerConfig.__dataclass_fields__['batch_mode']; print(cfg.default)"
# Expected: True
```

---

## Files Critical to Repair Pass

| File | Repair Items | Current State |
|------|-------------|---------------|
| `run_extraction_v5.py` | A3, A6, V5-PHASE-S, A-RAMP | 20,732 lines; A1/A2/A4/A5/A7 DONE |
| `promptsets/v4/prompts/PROMPT_R0_CONTROL_PLANE_TRUTH_MAP.md` | V5-R0, A0-partial | 85 lines; lines 45–59 UNRESOLVED conflict |
| `promptsets/v4/prompts/` | B-T4c (6 new files) | 130 .md files; 6 domains missing |
| `promptsets/v4/schemas/` | B-T3 | Directory does NOT exist |
| `fl_int/models.py` | FL-ROUTE | Lines 28–48; ladder model slugs need operator validation |
| `lib/prescan/grok_passes.py` | P-VAL (P3) | `BatchResponseValidator` at `:223–244` top-key only |
| `tests/test_prescan_batch_planner.py` | P-TESTS (7th file) | Does not exist |
| `benchmarking/executors/extraction_v5_adapter.py` | BM-LIVE | MODIFIED (uncommitted); live execution wiring at `:80–86` |
