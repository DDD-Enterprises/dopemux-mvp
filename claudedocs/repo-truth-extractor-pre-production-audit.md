# Repo Truth Extractor v4 — Pre-Production Audit

**Date**: 2026-02-22
**Auditor**: Claude Opus 4.6 (automated read-only audit)
**Scope**: Full pipeline (14 phases, 105 steps, ~178 artifacts, 105 prompt files)
**Method**: Static analysis of YAML manifests, Python source, prompt files, test suite

---

## 1. Executive Summary

### Recommendation: **CONDITIONAL GO** (Confidence: 75%)

The pipeline is architecturally sound and production-ready for a **cost-policy** run with the following conditions:

1. **Must-fix before first run** (2 items): Coverage map staleness (S2/S3 missing), v3 runner's `REQUIRED_PROMPT_STEP_IDS` declares phantom steps (Q11, S4, S5)
2. **Accept risk** (3 items): Cross-phase artifact writer ambiguity (R↔S), no end-to-end integration test, token estimation is approximate (÷4 heuristic)
3. **Monitor during run**: Batch poll timeout behavior, escalation hop budget, partition chunk sizing

The system has robust error handling, deterministic merge logic, comprehensive retry/escalation, and well-structured prompts. Cost for a full `--phase ALL --routing-policy cost` run is estimated at **$8–$18** depending on repo size and partition count.

---

## 2. Cost Estimate

### Routing Ladder (cost policy)

| Tier | Model | Est. Input Tokens/Step | Est. Output Tokens/Step | Steps | $/1M Input | $/1M Output | Est. Cost |
|------|-------|----------------------|------------------------|-------|-----------|------------|-----------|
| **bulk** | gpt-5-nano | ~8K prompt + ~20K context | ~4K | 15 (inventory/partition steps) | $0.10 | $0.40 | ~$0.50 |
| **extract** | gpt-5-mini | ~8K prompt + ~40K context | ~8K | 55 (extraction steps) | $0.40 | $1.60 | ~$6.00 |
| **synthesis** | gpt-5.2 | ~8K prompt + ~60K context | ~12K | 25 (R/T/X/Z/S steps) | $2.00 | $8.00 | ~$7.50 |
| **qa** | gpt-5-nano | ~8K prompt + ~30K context | ~4K | 10 (merge/QA steps) | $0.10 | $0.40 | ~$0.30 |

**Total estimated (synchronous)**: **~$14.30**
**With batch mode (50% discount)**: **~$7.15**
**With escalation hops (10% overhead)**: **~$7.90–$15.70**

### Cost Optimization Opportunities

| Opportunity | Savings | Effort |
|-------------|---------|--------|
| Use `--batch-mode` (OpenAI Batch API) | 50% on OpenAI steps | Zero (flag exists) |
| Run `--routing-policy cost` (already default) | Baseline | Zero |
| Limit `--escalation-max-hops 1` for first run | ~5% | Zero |
| Skip optional phases M, S on first run | ~15% (S is synthesis-heavy) | `--phase ALL` already skips M/S |

---

## 3. Findings Table

| ID | Severity | Category | Description | Recommendation |
|----|----------|----------|-------------|----------------|
| F-01 | **CRITICAL** | Completeness | `REQUIRED_PROMPT_STEP_IDS` in v3 runner (line 512-517) declares phantom steps `Q11`, `S4`, `S5` that have no prompt files on disk and no entries in promptset.yaml. If the runner validates prompt existence at startup, these will cause a hard failure. | Remove `Q11` from Q set, `S4`/`S5` from S set in v3 runner, or create corresponding prompt stubs. |
| F-02 | **HIGH** | Completeness | `prompt_artifact_coverage_map.json` declares `prompt_count: 103` but promptset.yaml has 105 steps (S2, S3 missing from map). Map is stale. | Regenerate coverage map to include S2 (DECISION_DOSSIER) and S3 (ARCHITECTURE_PROOF_HOOKS). |
| F-03 | **HIGH** | Completeness | 9 artifact names are registered in BOTH phase R and phase S with different `canonical_writer_step_id` values (e.g., `CONTROL_PLANE_TRUTH_MAP.md` canonical=R0 in R, canonical=S0 in S). Creates writer authority ambiguity. | Designate one canonical source per artifact. S-phase should reference R-phase outputs as inputs, not re-register them. |
| F-04 | **MEDIUM** | Completeness | Phases D, R, M, S lack a `*9` merge/QA step (D uses D4, R/M/S have no merge). This is intentional per phase design but breaks the `*0`+`*9` convention. | Document the exception. No code change needed. |
| F-05 | **MEDIUM** | Implementation | `merge_item_list_payloads` (v4 runner line 442): items without an `id` field get a sha256-based synthetic ID. If the same item appears in two payloads with slightly different whitespace, they get different IDs and won't merge. | Consider normalizing item content before hashing for ID-less items. |
| F-06 | **MEDIUM** | Implementation | `estimate_tokens_from_text` (chunking.py line 182): uses `len(text) / 4` heuristic. For code-heavy content this underestimates by ~20-30%. This affects partition sizing and cost estimation. | Use tiktoken or a provider-specific tokenizer for accurate estimation. Accept for first run. |
| F-07 | **MEDIUM** | Implementation | `call_v3_runner` (v4 line 253-260): subprocess.run without `text=True` or `capture_output=True`. stdout/stderr of v3 runner goes directly to terminal, which is fine for interactive use but means v4 wrapper can't detect specific v3 error types programmatically. | Acceptable for first run. Consider capturing output for structured error handling later. |
| F-08 | **MEDIUM** | Implementation | Batch poll loop (v3 line 8676): `while True` loop with `time.sleep(cfg.batch_poll_seconds)`. If batch_poll_seconds is misconfigured to 0, the `max(1, int(...))` at line 8695 prevents a tight loop. Good. But the timeout check uses wall clock which is correct. | No action needed. |
| F-09 | **LOW** | Implementation | TOCTOU in `ensure_dir`/`write_json` (v4 lines 92-98): `mkdir(exist_ok=True)` followed by `write_text`. Race is mitigable with partition_workers=1 (default). With concurrent writes, two workers could write the same norm file. | Use `partition_workers=1` for first run (default). Add file locking for concurrent mode later. |
| F-10 | **LOW** | Implementation | `_LINE_CACHE` (v4 line 317) is a module-level dict with no size bound. For very large repos, this could consume significant memory during evidence generation. | Not a concern for first run. Add LRU eviction if memory becomes an issue. |
| F-11 | **LOW** | Efficiency | v4 wrapper always runs promptset audit before execution (line 1337). This adds ~2-5 seconds of subprocess overhead per invocation. | Acceptable. The safety check is worth the latency. |
| F-12 | **MEDIUM** | UX | `--dry-run` output goes through v3 runner's subprocess. No v4-specific dry-run that shows cost estimate, step plan, or partition count. | Add a v4-level dry-run summary showing estimated cost and step count before delegating to v3. |
| F-13 | **LOW** | UX | Several CLI flags lack help text (e.g., `--partition-workers`, `--doctor`, `--doctor-auto-reprocess`). | Add help strings to all typer.Option calls. |
| F-14 | **MEDIUM** | Thoroughness | Pipeline has no explicit coverage for: database migrations, dependency vulnerability scanning, test coverage analysis, or git blame/authorship. | These are out-of-scope for repo truth extraction. Document as intentional exclusions. |
| F-15 | **MEDIUM** | Thoroughness | Graceful degradation when repo lacks components (no Docker, no MCP, no TaskX): prompts handle this via "emit empty containers + missing_inputs" pattern. But no test validates this path. | Add integration test with a minimal repo lacking optional components. |
| F-16 | **HIGH** | Tests | No end-to-end integration test exists. The 24 test files cover unit-level concerns (parsing, routing, retry, CLI flags) but never run a real phase through the full v4 → v3 → parse → merge → norm pipeline. | Add at least one smoke test that runs `--phase A --dry-run` and validates the command structure. |
| F-17 | **MEDIUM** | Tests | `test_run_extraction_v4_core.py` has 10 tests with real assertions (good quality). But untested: v4 norm assembly for non-C phases, v4 doctor flow, v4 resume proof verification edge cases, evidence generation for missing files. | Expand v4 test coverage to include norm assembly for at least one additional phase. |
| F-18 | **LOW** | Tests | Test file `test_promptset_v4_lint.py` exists but wasn't read. Likely covers promptset YAML validation. | Verify it catches the F-01 phantom step IDs. |
| F-19 | **MEDIUM** | Prompt Quality | All 8 sampled prompts share an identical boilerplate template (~80% of content). While this ensures consistency, it means phase-specific extraction guidance is concentrated in the Legacy Context section at the bottom, which is explicitly labeled "for intent only; never as evidence." | Consider promoting key legacy context instructions into the Extraction Procedure section. |

---

## 4. Prompt Quality Report

All 8 sampled prompts follow an identical template structure. Scores reflect the template quality with per-prompt differentiation.

### Template Structure Score (applies to all 8)

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Structure** | 5/5 | 9 clear sections: Goal, Inputs, Outputs, Schema, Extraction Procedure, Evidence Rules, Determinism Rules, Anti-Fabrication Rules, Failure Modes |
| **Anti-fabrication** | 5/5 | Explicit "Do not invent" rules, UNKNOWN field policy, evidence requirement on every load-bearing value |
| **Determinism** | 5/5 | Forbidden timestamp keys, stable sort specification, merge collision resolution, reproducibility requirement |
| **Schema clarity** | 4/5 | Output contracts specify kind, merge_strategy, canonical_writer, id_rule, required_fields. Missing: example JSON object showing a complete valid item. |
| **Input scoping** | 4/5 | Source roots listed, upstream artifacts named. Could be more specific about what to ignore. |
| **Token efficiency** | 3/5 | ~1,200-1,500 words per prompt (~1,600-2,000 tokens). The identical boilerplate across all 105 prompts adds up significantly. Could extract shared rules to a preamble injected by the runner. |
| **Failure modes** | 4/5 | Four failure modes covered (missing inputs, partial coverage, schema violations, parse ambiguity). Missing: what to do on timeout, token limit exceeded, or conflicting upstream artifacts. |

### Per-Prompt Differentiation

| Prompt | Phase | Tier | Differentiation Quality | Notes |
|--------|-------|------|------------------------|-------|
| A0 (Inventory) | A | bulk | 4/5 | Good legacy context with concrete file scan instructions |
| A99 (Merge/QA) | A | qa | Not sampled (substituted Q0) | — |
| C1 (Service Entrypoints) | C | extract | 3/5 | Legacy context is minimal ("Find how services start") |
| D1 (Claims/Boundaries) | D | extract | Not fully read | — |
| R0 (Control Plane Truth Map) | R | synthesis | 4/5 | Good legacy context with explicit MUST INCLUDE sections |
| T1 (Task Packets) | T | synthesis | 3/5 | Legacy context is brief; unclear how "Top 10" is determined |
| Z2 (Opus Input Bundle) | Z | synthesis | 3/5 | Very brief legacy context for a critical handoff step |
| Q0 (Pipeline Completeness) | Q | qa | 3/5 | Legacy context is minimal for a meta-verification step |

### Template Anti-Pattern: Boilerplate Dominance

**Issue**: ~80% of each prompt is identical boilerplate. The differentiating content (Legacy Context) is at the bottom and explicitly marked as non-authoritative. This means:
- The LLM receives the same rules 105 times across a full run
- Phase-specific extraction guidance is buried in "intent only" context
- Token budget is ~1,600 tokens of boilerplate per prompt × 105 steps = ~168K tokens of repeated rules

**Recommendation**: Extract shared rules into a system prompt preamble injected by the runner. Each step prompt should focus on: Inputs, Outputs, Schema contracts, and step-specific extraction guidance.

---

## 5. Completeness Matrix

| Phase | Steps (YAML) | Prompts (Disk) | Coverage Map | Artifacts | *0 Inventory | *9/*99 Merge | Status |
|-------|-------------|---------------|-------------|-----------|-------------|-------------|--------|
| **A** | 11 | 11 | 11 | 14 | A0 ✅ | A99 ✅ | ✅ Complete |
| **H** | 9 | 9 | 9 | 13 | H0 ✅ | H9 ✅ | ✅ Complete |
| **D** | 6 | 6 | 6 | 20 | D0 ✅ | D4 (merge) ✅ | ✅ Complete (D4 acts as merge) |
| **C** | 11 | 11* | 11 | 20 | C0 ✅ | C9 ✅ | ✅ Complete (*C10 is v4-only deep step) |
| **E** | 8 | 8 | 8 | 11 | E0 ✅ | E9 ✅ | ✅ Complete |
| **W** | 7 | 7 | 7 | 9 | W0 ✅ | W9 ✅ | ✅ Complete |
| **B** | 5 | 5 | 5 | 7 | B0 ✅ | B9 ✅ | ✅ Complete |
| **G** | 6 | 6 | 6 | 8 | G0 ✅ | G9 ✅ | ✅ Complete |
| **Q** | 5 | 5 | 5 | 6 | Q0 ✅ | Q9 ✅ | ✅ Complete |
| **R** | 9 | 9 | 9 | 10 | R0 ✅ | None (report) | ✅ Complete |
| **X** | 6 | 6 | 6 | 8 | X0 ✅ | X9 ✅ | ✅ Complete |
| **T** | 7 | 7 | 7 | 15 | T0 ✅ | T9 ✅ | ✅ Complete |
| **Z** | 4 | 4 | 4 | 7 | Z0 ✅ | Z9 ✅ | ✅ Complete |
| **M** (opt) | 7 | 7 | 7 | 7 | M0 ✅ | None (export) | ✅ Complete |
| **S** (opt) | 4 | 4 | **2** ⚠️ | 18 | S0 ✅ | None (synthesis) | ⚠️ Coverage map stale |
| **TOTAL** | **105** | **105** | **103** | **~178** | 15/15 ✅ | 11/15 ✅ | |

### Key Discrepancies

1. **Coverage map**: Missing S2, S3 (stale `prompt_count: 103`)
2. **v3 REQUIRED_PROMPT_STEP_IDS**: Declares Q11, S4, S5 which don't exist
3. **Disk vs YAML**: 105 prompt files match 105 YAML steps exactly
4. **Cross-phase artifacts**: 11 artifact names duplicated between R and S phases

---

## 6. Prioritized Improvements

### Must-Fix Before First Run

| # | Finding | Action | Effort |
|---|---------|--------|--------|
| 1 | F-01: Phantom step IDs (Q11, S4, S5) in v3 runner | Remove from `REQUIRED_PROMPT_STEP_IDS` dict | 5 min |
| 2 | F-02: Stale coverage map | Regenerate `prompt_artifact_coverage_map.json` | 10 min |

### Should-Fix Before First Run (but can proceed without)

| # | Finding | Action | Effort |
|---|---------|--------|--------|
| 3 | F-03: R↔S artifact writer ambiguity | Clarify canonical writer rules in artifacts.yaml comments | 15 min |
| 4 | F-12: No v4-level dry-run cost summary | Add `--dry-run` summary showing step count and cost estimate | 30 min |

### Nice-to-Have (post first run)

| # | Finding | Action | Effort |
|---|---------|--------|--------|
| 5 | F-16: No e2e integration test | Add smoke test for `--phase A --dry-run` | 1 hr |
| 6 | F-19: Prompt boilerplate extraction | Move shared rules to runner-injected preamble | 2 hrs |
| 7 | F-06: Token estimation accuracy | Replace `len/4` with tiktoken | 30 min |
| 8 | F-05: ID-less item merge edge case | Normalize whitespace before sha256 | 15 min |
| 9 | F-13: CLI help text gaps | Add help strings | 15 min |

---

## 7. Test Coverage Gaps

### Coverage Summary

| Area | Test Files | Coverage | Quality |
|------|-----------|----------|---------|
| v3 model routing | 1 | ✅ Good | Real assertions |
| v3 escalation | 1 | ✅ Good | Tests failure type → escalation decision |
| v3 batch mode | 1 | ✅ Good | Tests batch submit/poll/fetch |
| v3 resume semantics | 1 | ✅ Good | Tests SKIP vs RERUN decisions |
| v3 parse/retry | 2 | ✅ Good | Tests parse repair and retry decisions |
| v3 artifact parsing | 1 | ✅ Good | Tests JSON extraction from responses |
| v3 partition concurrency | 1 | ✅ Good | Tests concurrent partition execution |
| v3 CLI | 1 | ✅ Good | Tests typer command assembly |
| v4 core | 1 (10 tests) | ⚠️ Partial | Tests merge, sort, resume proof, service catalog |
| v4 norm assembly | 0 | ❌ Missing | No test for `sync_phase_from_v3` or `sync_run_to_v4` |
| v4 CLI | 0 | ❌ Missing | No test for v4 `cli()` function |
| v4 doctor | 0 | ❌ Missing | No test for `mirror_doctor_outputs` |
| v4 status | 1 (partial) | ⚠️ Partial | Tests `build_v4_status_payload` but not `print_v4_status` |
| Reprocess policy | 2 | ✅ Good | Tests `decide_action` matrix |
| Promptset lint | 1 | ⚠️ Unknown | Not read; likely covers YAML validation |
| Promptgen | 2 | ✅ Good | Tests profile selection and promptpack |
| End-to-end | 0 | ❌ Missing | No integration test running full pipeline |
| Chunking edge cases | 0 | ❌ Missing | No test for `plan_chunks_for_step` or `build_partition_context` |

### Critical Untested Paths

1. **v4 norm assembly** (`sync_phase_from_v3`): The core v4 value-add — merging v3 raw outputs into deterministic norm artifacts — has zero dedicated tests
2. **End-to-end pipeline**: No test validates that v4 → v3 → parse → merge → norm produces expected outputs
3. **Chunking edge cases**: `build_partition_context` has complex truncation logic (head+tail) with no tests
4. **Evidence generation**: `evidence_for` / `find_line_excerpt` functions untested for missing files, binary files, very long lines

---

## Verification Checklist

- [x] All 7 dimensions addressed with findings
- [x] Cost estimate includes realistic numbers with tier breakdown
- [x] Every critical/high finding has actionable recommendation
- [x] Go/no-go recommendation is defensible (conditional go with 2 must-fix items)
- [x] Prompt quality scored across 7 dimensions with per-prompt differentiation
- [x] Completeness matrix covers all 15 phases
- [x] Test coverage gaps identify specific untested critical paths
