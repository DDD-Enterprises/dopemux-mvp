# RTE-TRUTH — Consolidated Findings & Remediation Backlog (Triage Gate P1.5)

**Adjudicator**: subagent (worktree `focused-mahavira-5bd29b`, branch `claude/rte-audit-improvement-f4beb7`, HEAD `542c17bb4`)
**Date**: 2026-07-11 · **Mode**: READ-ONLY except this file. No commits.
**Inputs**: A1-architecture, A2-cost-truthfulness, A3a/b/c/d-prompts, A4-cli-ux-docs, A5-ops-gates-proof, A6-fresh-eyes, A7-legacy-refgraph.
**Method**: dedup/merge across passes → conflict adjudication with primary-source verification → severity rank → wave routing → packet skeletons. One live code trace performed (conflict 2a — `src/dopemux/cli.py`, `run_extraction_v5.py`); all other findings accepted from the audit reports at their stated confidence.

Evidence labels: **OBSERVED** = re-verified in source this gate · **ACCEPTED** = taken from the cited audit pass without re-derivation · **NOT_RUN** = no runtime executed.

> **Wave taxonomy used here** (authoritative program definition): **R0** hygiene quick-wins · **R1** monolith seam extraction (ui.py → cli_args.py → phase modules C/D/X → costing corrected-cut; Collector deferred) · **R2** cost truthfulness **& spend/go-live safety** · **R3** prompt hardening (injection choke-point + schema expansion + content fixes) · **R4** CLI/docs · **R5** legacy retirement (v3 deletion deferred post-release). Note: A5 used its own R-labels where R1 meant "hygiene/config"; those are remapped here to the program's seam-focused R1 and to R0/R2 as noted per finding.

---

## 1. Executive Top-10 (ranked by change to operator/maintainer reality)

| # | Finding (ID) | Why it changes reality | Sev | Wave |
|---|---|---|---|---|
| 1 | **Prompt-injection: 0/138 prompts delimit untrusted content** (F-30) | Repo/home file bodies are pasted verbatim into paid-LLM user content with no "data not instructions" boundary; runtime-confirmed (TRACE.md L178). A poisoned `AGENTS.md`/dotfile can fabricate or suppress security findings that feed R10/R11. Single-choke-point fix exists. | CRIT | R3 |
| 2 | **Pricing untruth: catalog-collapse under-pricing + preview≠abort divergence** (F-10, F-11) | On catalog load failure every model silently reprices to `$0.15/$0.60` (33–50× under) while reporting "priced"; preview/preventive (E2, multiplier) and abort authority (E3, flat) disagree ~2× on flex profiles. Operators cannot trust any dollar number. | CRIT | R2 |
| 3 | **Wizard `--execute` is statically broken for all 14 phases** (F-40) | `extraction.py:48-49` appends nonexistent `--prescan-dir`; `upgrades run` has no such option and no `ignore_unknown_options` → Click rejects every phase after Stage 2 succeeds. The primary guided live path cannot run. | CRIT | R4 |
| 4 | **Quickstart teaches a disabled command, wrong namespace, and omits the consent gate** (F-41) | Official tutorial routes first-run users to `dopemux extract truth-run` (hard-disabled), the non-canonical `audit` surface, and never mentions `DPMX_LIVE_OK=1`. Day-one users hit a wall at max commitment. | CRIT | R4 |
| 5 | **C9 merge degrades every Gen-2 schema and is internally incoherent** (F-20) | The canonical merge step overwrites C1/C2/C7/C8 rich schemas with generic `id,component,symbol`, and its Outputs≠Schema≠procedure with impossible ordering. All prompt schema value is nullified downstream. | CRIT | R3 |
| 6 | **S7 is a production stub feeding S11/S12** (F-22) | `PROMPT_S7` self-admits "structural stub… highly unstructured markdown," no citation/anti-fab, yet is a required input to documentation-generation and the stability signature — fabrication propagates into consolidation artifacts. | CRIT | R3 |
| 7 | **Phase M fabricates by construction; H9 mandates uncomputable `sha256`** (F-21) | M-phase procedures require live-state queries + timestamps an LLM cannot do; H9's canonical manifest requires per-item hashes the model must invent. Any run of these phases emits fabricated "truth." | CRIT | R3 |
| 8 | **C8 SECRETS scan has no redaction rule** (F-23) | Exact-substring evidence excerpts copy real secret values into norm artifacts and paid-LLM context; feeds R11 security synthesis. | CRIT (sec) | R3 |
| 9 | **gitignore misses the real output path → 119 run artifacts committed** (F-01) | Root-anchored ignores never match `services/repo-truth-extractor/extraction/…`; 13 timestamped run dirs + spend ledgers are git-tracked (history growth, spend snapshots in VCS). | HIGH | R0 |
| 10 | **Definition-site inversion: `upgrades` is canonical, `rte` is the alias** (F-42) | Every core command is defined on the "legacy" `upgrades` group (unhidden) and merely attached to `rte` — the inverse of documented posture; any new `@upgrades.command` silently widens the legacy surface first. | HIGH | R4 |

*Honorable mention:* pre-live gate defaults to `CONDITIONAL_GO` on skipped PAL/preflight (F-13b, gate honesty) — the gate's weakest posture is its default posture.

---

## 2. Conflict Adjudications

### 2a. "All 11 profiles capped" (explorer-baseline) vs. "cap is opt-in, no wrapper auto-applies" (A2-4)

**VERDICT: Explorer-baseline VINDICATED. A2-4 OVERTURNED as written.** (confidence: high; wiring OBSERVED, abort behavior NOT_RUN)

Primary-source trace at HEAD `542c17bb4`:
- `src/dopemux/cli.py:5317` — the `rte run` wrapper forwards `--routing-policy` whenever `routing_policy or not cost_profile`; since `--cost-profile` defaults `None`, `not cost_profile` is **always true**, so a routing-policy is always passed to the runner (default `balanced_openrouter`).
- `run_extraction_v5.py:23052-23075` — `main()` resolves a profile in **every** branch: with `--cost-profile`, with `--routing-policy`, or bare (`else → resolve_cost_profile(None)`).
- `run_extraction_v5.py:1054-1055` — `resolve_cost_profile(None)` returns `DEFAULT_COST_PROFILE, COST_PROFILES[DEFAULT_COST_PROFILE]`; every one of the 11 profiles carries `max_cost_usd_default` (grep: 11 hits, `:657–:909`).
- `run_extraction_v5.py:23136-23146` — **the auto-apply block A2-4 missed**: `if args.max_cost_usd is None: … args.max_cost_usd = float(profile_default)`. This mutation runs **before** the main `RunnerConfig(max_cost_usd=args.max_cost_usd)` at `:23492`, which flows into `initialize_spend_tracker` (`:23984`, runs only when `cfg.max_cost_usd is not None`).

**Consequence**: On both the `dopemux rte run` wrapper path *and* bare `python run_extraction_v5.py`, `max_cost_usd` is non-`None` by the time the tracker initializes, so the fail-closed E3 SpendTracker (System A) **is active on every normal run**. A2-4's parenthetical "profile `max_cost_usd_default` values are not applied automatically (not found in v5 arg handling)" is factually wrong at HEAD; cite `run_extraction_v5.py:23136-23146`.
**Retained (independent of 2a)**: A2-1 (E2/E3 divergence), A2-2 (catalog collapse), A2-7 (one-call overshoot) all survive — they concern *pricing correctness*, not *whether a cap exists*. A2-4 is **downgraded to LOW** and reframed as a **doc/help-text truth defect** (F-14): the auto-applied cap is the profile default, cannot be seen without reading the log line, and the `--max-cost-usd` help text ("profile default applied when unset") is the only operator-facing hint. **Advances A6-F8** from "wiring unknown" to "wiring present, runtime NOT_RUN" — do not collapse into "cap proven working."

### 2b. A5: S7-DRIFT proof `verdict:FAIL` is the gate working as intended (re-close)

**VERDICT: ACCEPT (re-close, no reopen).** (confidence: high; ACCEPTED + cross-confirmed)

`proof/TP-RTE-S7-DRIFT-FIX-001/PROOF.json` shows `status: READY_FOR_REVIEW`, `validation_state: PASSED`, `pytest 10/10`, all 7 validations PASS. The only `FAIL` strings live inside `s7_gate_result.verdict` / `verify_and_close_evidence.expected_status` — the **expected output of the S7 drift gate when fed a deliberately injected stale step** (`FAKE_STALE_STEP`). Gate-says-FAIL-on-bad-input *is* the passing result; the audit trigger was a naive grep for `FAIL`. Independently corroborated by A6 §6: commit `d2fe66cac` converted `collect_truth_split` from a hardcoded PASS/`NOT_IMPLEMENTED` into a real fail-closed per-step check, live at HEAD. → **Vindicated list.** Follow-up: namespace proof fixture/expected-output fields so verdict greps stop false-positiving (F-51, R3).

### 2c. A6 (spend_ledger fail-open = HIGH money risk) vs. A2 (part of CRIT A2-2) — unify severity

**VERDICT: UNIFY as ONE finding (F-10), severity CRIT — but rest CRIT on cost-truthfulness, not unbounded spend.** (confidence: high)

A6-F1 and A2-2 are the same defect (catalog-load failure → every model reprices to the `$0.15/$0.60` baseline with `match_type:"exact"`, `unknown_model:False`). My 2a finding sharpens the harm: E3 (the authoritative abort) prices via `load_pricing_registry` reading `config/pricing.yaml` **directly and fail-closed** — independent of `benchmarking/pricing/catalog.py`. So with the always-on default cap + intact E3, real spend is bounded to cap + one-call overshoot even during a catalog collapse (E3 fails closed at init if pricing.yaml itself breaks). A6-F1's "cap math runs on understated spend / blows through the cap" holds only for the **E2 preventive/projected check and the preview** (`_check_projected_cost_limit`, `build_phase_cost_preview`), **not** the E3 abort. The surviving harm is therefore **cost-untruthfulness** (preview lies 33–50×; operator may set a too-high explicit `--max-cost-usd` trusting a lying preview), not runaway spend. Kept **CRIT** on that rationale, single ID F-10, sources A2-2 + A6-F1.

---

## 3. Findings Register

Symbol-first references; line numbers secondary (they drift). Sources cite the audit pass + its finding ID. "Wave" is the single owning wave; cross-wave dependencies noted in §4.

| ID | Sev | Title | Sources | Symbols / evidence | Wave | Packet |
|---|---|---|---|---|---|---|
| F-01 | HIGH | gitignore root-anchored; misses `services/…/extraction/`; 119 run artifacts + spend ledgers git-tracked | A5 §5.1; P0 stray-dir | `.gitignore:303-314,366`; `services/repo-truth-extractor/extraction/**` | R0 | R0-001 (rules) / R0-008 (sweep) |
| F-02 | LOW | Non-strict regression xfails rot silently (XPASS on fix goes unreported); no TP ref on FA-* | A5 §1.4 | `xfail_strict`; FA-3/FA-7/FA-8 markers | R0 | R0-002 |
| F-03 | MED | `extractor-full` CI has no per-test timeout; one hung test burns the 45-min job | A5 §3.2 | `ci-complete.yml:342-346`; no `pytest-timeout` | R0 | R0-003 |
| F-04 | MED | No ruff/mypy/flake8 in any CI job; declared strict mypy profile is aspirational | A5 §3.3-3.4 | `pyproject.toml:285-297`; 0 lint jobs | R0 | R0-004 |
| F-05 | MED | Tree-sitter imports fail-open (`TREE_SITTER_AVAILABLE=False` → `analyze_file` returns `{}`) — silent degraded prescan | A5 §1.1 (D1,D4-D6) | `lib/prescan/code_prescan.py:6-14,64-65` | R0 | R0-005 |
| F-06 | LOW | Pre-live gate default output dir inside repo tree | A5 §2.3 | `validate_pre_live_gate_v25.py:317-319` | R0 | R0-006 |
| F-07 | LOW | Dead/duplicate code: `compose.yml` dup in `phases/a.py`; dead `_add_extractor_alias_if_missing`; wizard dead conditionals | A1 §4; A4 W-4/W-5, §1.3 | `phases/a.py`; `cli.py:5706`; `preflight.py:47,123` | R0 | R0-007 |
| F-08 | LOW | Contract-map guard `pytest.skip` silently drops coverage if targets stop emitting | A5 §1.3 | `test_tp_rtx_v5_phase_recovery_hardening.py:327,381,397` | R3 | R3-004 (rides section-validator) |
| — | — | **— R1 monolith seam extraction —** | | | | |
| F-09 | (plan) | Seam-plan corrections: `OperatorArgumentParser`→`cli_args.py` (not ui.py); costing two-stage cut (System A extract, System B guards stay) | A1 §2 Seam1/2/3 | `run_extraction_v5.py:2452,4183,11400` | R1 | R1-002/R1-004 |
| — | — | **— R2 cost truthfulness & spend/go-live safety —** | | | | |
| F-10 | CRIT | Fail-open catalog collapse silently reprices all models to `$0.15/$0.60` (33–50× under) while reporting "priced"; corrupts E2 preview/preventive | A2-2; A6-F1 | `lib/spend_ledger.py:19,95-97,137,286-299,357-362` | R2 | R2-001 |
| F-11 | CRIT | Preview/preventive pricing (E2, multiplier) ≠ abort-authority pricing (E3, flat); ~2× divergence on flex profiles; two ledgers, two totals, both can abort | A2-1; A1 §2 Seam2 | `v5:11152` vs `v5:4526`; `cfg.ledger` vs `SpendTrackerState` | R2 | R2-001 |
| F-12 | HIGH | Three contradictory output-token heuristics (15/10/2%) + two tokenizers (chars/3.5 vs /4), none measured or printed; reasoning models unmodeled | A2-3; A2-5 | `cost_estimator.py:33,49`; `v5:11066,11071,11083` | R2 | R2-002 |
| F-13 | MED | E3 one-call overshoot (record-then-compare); `cost_cap_mode` decorative; `make_projected_cost_check` (F2-MED-1 fix) dead in v5 | A2-7; A2-6 | `v5:4806-4812`; `spend_ledger.py:580` | R2 | R2-003 |
| F-13b | MED-HIGH | Pre-live gate defaults to `CONDITIONAL_GO` when PAL/online-preflight are skipped (conditions never block); un-opted skip should be NO_GO | A5 §2.1-2.2 | `validate_pre_live_gate_v25.py:780,958,1490-1492` | R2 | R2-004 |
| F-14 | LOW | Auto-applied cap is the profile default only; `--max-cost-usd` help text is the sole operator hint; `cost_cap_mode`/`fail_closed_if` are declarative-only (see 2a) | A2-4 (overturned→reframed) | `v5:23136-23146`; `cli.py:5188` | R2 | R2-004 |
| F-15 | MED | SPEND_LEDGER.json non-atomic (`path.write_text`, full rewrite per event, process-local lock only) — crash can truncate the spend record | A5 §5.3 | `write_json` `v5:3676-3692`; `_write_spend_ledger_snapshot:4544` | R2 | R2-003 |
| F-16 | HIGH | Prescan incremental/full parity broken: incremental run produces semantically different artifacts than full recompute | A5 §1.1 (D2) | `test_prescan_incremental.py:490` (xfail strict) | R2 | R2-005 (TP-RTE-WALKER-006) |
| F-17 | HIGH | Optimize-pass payload schema drift: prior-pass summaries nested under wrong keys, passed as dict not string to `_call_grok` | A5 §1.1 (D3) | `lib/prescan/grok_passes.py:506-521` | R2 | R2-005 |
| F-18 | MED | `--status` (text mode) with typo'd run-id writes telemetry sidecar under phantom run dir — violates readonly introspection | A5 §1.2 (FA-7) | `test_fa_7_med_1_status_no_telemetry.py:58` | R2 | R2-005 |
| F-19 | MED | No automated retention/rotation; `extraction_hygiene.py` is unwired manual CLI; unbounded runs/doctor growth; no log rotation | A5 §5.2,5.4 | `extraction_hygiene.py`; `configure_run_file_logger:2289` | R2 | R2-005 |
| F-19b | HIGH | FA-8 preflight probe returns `AMBIGUOUS_PROVIDER_BLOCK` with valid keys while curl succeeds; double-gated (skipif∧xfail) so it never signals in CI | A5 §1.2 (FA-8) | `test_fa_8_high_1_preflight_probe.py:37,41`; suspect `call_llm` payload | R2 | R2-004 |
| F-19c | MED | Gemini SDK path passes no request timeout (`get_gemini_client` called without `timeout_seconds`) — a hung call stalls a lane indefinitely | A6-F4 | `llm_runtime.py:733` vs `v5:10645` | R2 | R2-004 |
| F-19d | MED | Raw `dpmx_webhook_url` (bearer-equivalent) embedded verbatim in RUN_MANIFEST | A6-F5 | `reporting.py:588` | R2 | R2-004 |
| — | — | **— R3 prompt hardening —** | | | | |
| F-20 | CRIT | C9 canonical merge degrades C1/C2/C7/C8 rich schemas AND is internally incoherent (Outputs≠Schema≠procedure, owns artifacts produced after it) | A3a F1,F2 | `PROMPT_C9`; `EVENTBUS_SURFACE`/`SERVICE_ENTRYPOINTS` field loss | R3 | R3-001 (first — gates all schema work) |
| F-21 | CRIT | Phase M mandates live-state query + timestamps (LLM-infeasible → fabricated); H9 mandates uncomputable per-item `sha256` | A3b F-1,F-2 | `PROMPT_M0-M6`; `HOMECTRL_NORM_MANIFEST` | R3 | R3-005a |
| F-22 | CRIT | S7 is a self-admitted production stub feeding required inputs S11/S12; fabrications propagate into consolidation + stability signature | A3c C1 | `PROMPT_S7`; feeds `PROMPT_S11/S12` | R3 | R3-005b |
| F-23 | CRIT (sec) | C8 SECRETS_RISK_LOCATIONS has no excerpt-redaction rule → real secrets copied into artifacts + paid-LLM context; H1 redaction rule is legacy-only (non-binding) | A3a F3; A3b F-6 | `PROMPT_C8` SECRETS; `PROMPT_H1` legacy block | R3 | R3-004 |
| F-24 | HIGH | T-phase load-bearing contract (packet sections, authority hierarchy, stop conditions) marooned in the non-normative Legacy block; generic boilerplate is normative | A3c C2 | `PROMPT_T0/T1/T3` | R3 | R3-005c |
| F-25 | HIGH | E-phase: 6 procedures emit artifact filenames absent from declared contracts + disjoint required-field sets (E5/E6) + nonexistent upstream names | A3b F-3 | `PROMPT_E1-E6` | R3 | R3-005a |
| F-26 | HIGH | `TP_BACKLOG_TOPN.json` multi-writer collision (T0/T1/T5 all write, all declare canonical=T9) | A3c H1 | `PROMPT_T0/T1/T5` | R3 | R3-005c |
| F-27 | HIGH | Determinism-rule violation baked into T0/T1 (and H/M) legacy schemas: required `run_id`/`generated_at` vs §Determinism ban | A3c H2; A3b F-7 | `TP_BACKLOG_TOPN`; `PROMPT_H0-H9` legacy | R3 | R3-005c / R3-004 |
| F-28 | HIGH | G9 merge/QA excludes G5/G6/G7 (the 3 schema-backed artifacts); parallel A99/C9 orphan of A11-A13/EVENTBUS outputs | A3b F-4; A3a A99 | `PROMPT_G9`; `PROMPT_A99` | R3 | R3-005d |
| F-29 | HIGH | Synthesis grounding gap: R7/R8/S4/S5/S6 aggregate many upstream artifacts with no per-claim upstream-artifact attribution; add synthesis-tier evidence variant to RULES | A3c H3 | `PROMPT_R7/R8/S4/S5/S6` vs R11 `←ARTIFACT:item_id` | R3 | R3-006 |
| F-30 | CRIT (sec) | Zero injection defense across all 138 prompts; untrusted repo/home bodies enter paid LLM undelimited; runtime-confirmed. Fix = wrap `build_partition_context` return + shared preamble + template convention; flips FA-3 | A3a F6; A3b F-14; A3c H4; A4d §2.1-2.3; A5 FA-3 | `build_partition_context` `v5:12781`; `prompt_prefix` `v5:15301,21540`; `test_fa_3_high_1…` | R3 | R3-002 |
| F-31 | HIGH | `required_prompt_sections` unenforced (zero runtime readers); PROMPTSET_RULES not among any template's runner-context inputs → anti-fab regime is a pointer checked by nothing for ~30 templates | A3b F-5 | `run_extraction_v4.py:104-110`; `template_renderer.py:20-37` | R3 | R3-004 |
| F-32 | HIGH | Duplicate/near-duplicate output surfaces (REFUSAL_GUARDRAILS B2/C4; hooks A5/A13; ADHD C13/C17) doubling token cost, no canonical arbitration | A3a F5 | `PROMPT_B2/C4`, `A5/A13`, `C13/C17` | R3 | R3-005d |
| F-33 | MED | Gen-1 "Legacy Context" blocks embed contradictory container shape with `generated_at`; A99 rule #4 fix not propagated | A3a F4; A3b F-7 | `PROMPT_A2-A9` legacy JSON shapes | R3 | R3-004 |
| F-34 | MED | Graph outputs declared under `json_item_list`+`itemlist_by_id` while requiring `nodes,edges,schema` (D3,E3,R5,X4) | A3b F-8; A3c M3; A3d DEF-6 | `PROMPT_D3/E3/R5/X4` | R3 | R3-005e |
| F-35 | MED | Duplicate/broken step numbering (two "6."/"7.") in E1-E6, G0, G4, R1-R8 — degrades instruction-following on anti-fab steps | A3b F-10; A3c M1 | `PROMPT_E1-E6,R1-R8` | R3 | R3-005e |
| F-36 | MED | Highest-value artifacts carry thinnest contracts (`id,evidence` only): D1 claims/boundaries, E2 env-chain, G1 CI-gates | A3b F-11 | `PROMPT_D1/E2/G1` | R3 | R3-003 |
| F-37 | MED | Hardcoded `implementer="GPT-5.3-Codex"` provenance (M3/M4/M5) — false metadata when any other model runs | A3b F-13 | `PROMPT_M3/M4/M5` | R3 | R3-005a |
| F-38 | MED | Unbounded/absent enums on scored fields (B3 `severity` no vocab; Gen-1 QA fields free-form); S0 input-as-output contract confusion; dual-alias S0-S6 double-emit | A3a F8; A3c M2,M4 | `PROMPT_B3`; `PROMPT_S0-S6` | R3 | R3-003 |
| F-39 | HIGH | Schema-expansion opportunity (post-C9): C8/C2/C1/C7/C14 + G5 AUTH_FLOW ready to schematize; add evidence-object subschema to G6/G7; Q11/S12 near-schema'd | A3a §candidates; A3b G5/G6/G7; A3c | `schemas/C18-C21`; `PROMPT_G5/G6/G7/Q11/S12` | R3 | R3-003 |
| — | — | **— R4 CLI / UX / docs —** | | | | |
| F-40 | CRIT | Wizard `--execute` statically broken: builds `--prescan-dir` (nonexistent on `upgrades run`), no `ignore_unknown_options` → every phase rejected; wizard never checks `DPMX_LIVE_OK`; routing-policy free-text | A4 W-1/U-1, W-2, W-3 | `ux/wizard/extraction.py:48-49,146-150`; `cli.py:5136-5228` | R4 | R4-001 |
| F-41 | CRIT | Quickstart teaches disabled `extract truth-run`, the non-canonical `audit` surface, omits `DPMX_LIVE_OK`, mislabels default profile; prescan false-equivalence | A4 J-1,J-2,J-3,J-4,J-5,J-6,J-7 | `extraction-quickstart.md:127-176`; `extract_commands.py:876,998` | R4 | R4-005 |
| F-42 | HIGH | Definition-site inversion: all core commands defined on unhidden `upgrades`; `rte` is attach-site alias; new `@upgrades.command` widens legacy surface first | A4 §1.3, U-2 | `cli.py:5103-5642` `@upgrades.command`; `upgrades_commands.py:22` | R4 | R4-002 |
| F-43 | HIGH | Flag inconsistency: workers (`--workers` def 1/10 vs `--partition-workers` def 1); routing-policy (8-Choice vs free-text vs 4-Choice); wizard static `ROUTING_LADDERS` estimate drifts from `lib/pricing_surface` | A4 U-3,U-4,W-7 | `audit_commands.py:90-97`; `cli.py:4962-4973`; `cost_profiles.py:20` | R4 | R4-004 |
| F-44 | MED | Three uncoordinated `status` impls; `rte trace --dry-run` always-on/undocumented-live; `promptset audit` v4-only dead-end; scan phase-list omits S | A4 U-5,U-6,U-7,U-8,W-8 | `audit_commands.py:123`; `cli.py:5642,5639,5041` | R4 | R4-004 |
| F-45 | MED | v5-native `rte scan` needed: standalone zero-LLM prescan producer feeding `rte run --prescan-import-dir`; retire `--allow-legacy-v3-scan`/repscan delegation | A4 §4.3 | `run_repscan.py`; `run_integrated_prescan_stage v5:8111`; `lib/prescan/engine.py` | R4 | R4-003 |
| F-46 | MED | Docs sweep: 8 active docs present `upgrades` as runnable; regenerate 10 truth-snapshot files; dedupe `user-journey.md` pair (~20 mention-edits) | A4 §3 | `docs/03-reference/extraction/*`; `docs/03-reference/truth/*` | R4 | R4-005 |
| F-47 | LOW | ~380 lines unreachable after `raise` in `truth_run`; hidden `--engine-version` v3 alias warning-only; referral-chain double-refusal (repscan→rte scan) | A4 U-9,U-10,U-11 | `extract_commands.py:1002-1382`; `cli.py:4977-4983,82-85` | R4 | R4-006 |
| F-48 | MED | Generated promptset set stale/orphaned (2032 timestamp, 5-of-137 rendered) and `run_sync`/integrity not wired to any runtime/CI path — decide authoritative (add gate) or disposable | A4d §2.4,2.5 | `promptsets/generated/…/SYNC_MANIFEST.json`; `sync_engine.py` | R4 | R4-006 |
| F-49 | LOW | W/X/Z template nits: domain fields outside `required_item_fields` (DEF-1); brittle line refs (DEF-2); procedure↔contract name drift (DEF-4); X1-X4 generic boilerplate (DEF-5); stale v3 path (DEF-7) | A4d DEF-1..7 | `PROMPT_W4/W5/X0-X4/Z9` | R3 | R3-005e |
| — | — | **— R5 legacy retirement —** | | | | |
| F-50 | MED | Legacy surface retirement (guided by A7 refgraph): `run_repscan`/v4 external shims where unreferenced; `sp/models.py` routing-metadata shadow-twin; base_prompts/archive legacy prompts. **v3 NOT deleted** (80 test + 10 runtime refs) — deferred post-release | A7 §1-9; A6-F7 | `run_repscan.py`; `sp/models.py:SP_STEPS`; `PipelineRunner` 7 runtime refs | R5 | R5-001 |
| F-51 | MED | Proof-bundle schema inconsistency (some use `validation_state`/nested `verdict`, others bare `exit_code` arrays) → unreliable automated verdict extraction (caused this gate's 2 false alarms); standardize proof-dir layout derivable from TP ID; namespace expected-output fields | A5 §4.1,4.2,4.3 | `proof/**/PROOF.json` | R3 | R3-001 (rides) / or R0 doc |

**Severity counts** (54 register rows + 1 plan-note F-09):

- **CRIT (9)** — F-10, F-11, F-20, F-21, F-22, F-23, F-30, F-40, F-41 *(F-23 & F-30 are the two security CRITs)*
- **HIGH (16)** — F-01, F-12, F-16, F-17, F-19b, F-24, F-25, F-26, F-27, F-28, F-29, F-31, F-32, F-39, F-42, F-43
- **MED (22)** — F-03, F-04, F-05, F-13, F-13b, F-15, F-18, F-19, F-19c, F-19d, F-33, F-34, F-35, F-36, F-37, F-38, F-44, F-45, F-46, F-48, F-50, F-51
- **LOW (7)** — F-02, F-06, F-07, F-08, F-14, F-47, F-49

---

## 4. Wave Plans & Packet Skeletons

**Hard wave dependencies** (respect strictly):
- **R1 before R2/R3/R4** for any v5-touching work (program rule). R2-001 edits the costing module R1-004 extracts → **R1-004 before R2-001**.
- **Intra-R3: R3-001 (C9) first** — A3a: "any schema expansion of C1/C2/C7/C8 is void unless C9 is reconciled first."
- **R3-002 injection wrap** targets `build_partition_context` (stays in the monolith — *not* a seam target), but should follow R1 so diffs land on the carved file.
- **R4-005 docs sweep after R4-001/R4-002** — docs must match fixed code, not the reverse.
- All R0 packets are parallel-safe and seam-independent **except** F-01's `git rm --cached` sweep (R0-008), which is blocked on an operator fixtures decision — do not bundle it with the mechanical ignore-rule packet, and do not call it a quick-win.

### R0 — hygiene quick-wins (parallel-safe)
| Packet | Title | Findings | Acceptance (dry-run-verifiable) | Diff | Order |
|---|---|---|---|---|---|
| TP-RTE-TRUTH-R0-001 | Service-anchored gitignore rules | F-01 (rules half) | `git check-ignore -v` matches new `services/…/extraction/v5/{runs,doctor}/…`; diff touches only `.gitignore` | S | 1 |
| TP-RTE-TRUTH-R0-002 | Strict xfail + TP-ref discipline | F-02 | `xfail_strict=true` service-wide; every remaining xfail carries a TP ref; collection shows strict | S | any |
| TP-RTE-TRUTH-R0-003 | `pytest-timeout` on extractor-full | F-03 | dep added; `--timeout=120 --timeout-method=thread` in CI; job config diff | S | any |
| TP-RTE-TRUTH-R0-004 | Service lint config + `extractor-lint` CI (warn-only baseline) | F-04 | `services/repo-truth-extractor/{ruff.toml,mypy}`; new CI job; warn-only/baseline first | M | any |
| TP-RTE-TRUTH-R0-005 | Tree-sitter fail-closed (or explicit degraded-mode metadata) | F-05 | import failure raises on live prescan (or records `degraded:true`); unit test | S | any |
| TP-RTE-TRUTH-R0-006 | Pre-live gate default output-dir out of repo tree | F-06 | default path outside worktree (or `--output-dir` required); test | S | any |
| TP-RTE-TRUTH-R0-007 | Trivial dead-code deletions | F-07 | `phases/a.py` dedup, `_add_extractor_alias_if_missing` removed, wizard dead conditionals fixed; tests pass | S | any |
| TP-RTE-TRUTH-R0-008 | **Blocked** run-artifact `git rm --cached` sweep | F-01 (sweep half) | operator decision on load-bearing fixture runs first; then `git rm -r --cached` non-fixture runs; history-size note | M | **needs decision** |

### R1 — monolith seam extraction (sequential; dry-run is the regression harness)
| Packet | Title | Findings | Acceptance | Diff | Order |
|---|---|---|---|---|---|
| TP-RTE-TRUTH-R1-001 | Extract `extractor/ui.py` (UI, UiConfig; inject `append_jsonl` callable) | F-09 | dry-run event parity; single JSONL lock preserved; test re-export shims | M | 1 |
| TP-RTE-TRUTH-R1-002 | Extract `extractor/cli_args.py` (`build_parser` + `OperatorArgumentParser`; named default constants for literal-coupling; delete dead introspection block :23692-23713; consolidate `phase_sequence`) | F-09; F-07 (main-func part) | `--help` parity; all `--print-*`/introspection modes exit-identical; profile budget overrides still fire | M | 2 |
| TP-RTE-TRUTH-R1-003 | Extract `extractor/phases/{c,d,x}.py` (+h optional) via `PhaseRunnerDeps` extension | F-09 | dry-run phase C/D/X parity; `runners` dict behavior unchanged | M | 2 (parallel w/ 001/002) |
| TP-RTE-TRUTH-R1-004 | Extract `extractor/costing.py` System A (SpendTracker) — corrected two-stage cut; `get_active_spend_tracker()` accessor; System B guards stay | F-09 | capped-run parity; `update_run_manifest_status` uses accessor; System A unit tests | M-H | 3 (after 001-003) |

### R2 — cost truthfulness & spend/go-live safety
| Packet | Title | Findings | Acceptance | Diff | Order |
|---|---|---|---|---|---|
| TP-RTE-TRUTH-R2-001 | Single pricing authority on `pricing.yaml`; catalog-fail = blocker on costed ops; unknown-model raise-with-cap / `UNPRICED`-without; coverage + `stale_after` CI gate | F-10, F-11, F-13(part) | fixture table (A2 §5.5): preview==preventive==accounting on identical usage; catalog-fail fixture → startup error; coverage gate ties `COST_PROFILES`+ladders to priced rows | L | after R1-004 |
| TP-RTE-TRUTH-R2-002 | Tokenizer + per-lane output-ratio unification; printed assumptions in every preview | F-12 | shared `estimate_tokens`; `output_ratio[lane][family]` table; preview header states pricing sha/tokenizer/ratio/multipliers; fixture tolerances | M-L | after R2-001 |
| TP-RTE-TRUTH-R2-003 | Cap-enforcement hardening + spend-ledger atomicity + `--llm-temperature` | F-13, F-15, F-38(temp A2-8) | pre-check-before-spend overshoot test; `cost_cap_mode` wired-or-removed; atomic tmp+`os.replace`; temperature flag range-validated 0-2, gpt-5 omission preserved | M | after R2-001 |
| TP-RTE-TRUTH-R2-004 | Go-live safety cluster: gate `--allow-conditional` opt-in; FA-8 preflight fix; Gemini SDK timeout; webhook-URL redaction; cap help-text truth | F-13b, F-19b, F-19c, F-19d, F-14 | gate = NO_GO on un-opted skip; FA-8 XPASS; Gemini `timeout_seconds` threaded; manifest webhook flag-only; help text corrected | M | any (post-R1) |
| TP-RTE-TRUTH-R2-005 | Walker/prescan (TP-RTE-WALKER-006): incremental parity, optimize payload contract, `--status` telemetry readonly, drop darwin xfails, wire retention/log rotation | F-16, F-17, F-18, F-19, F-05(drop markers) | incremental `_normalized_outputs`==full; optimize payload flat schema+str-serialized; `--status` no telemetry write; markers dropped XPASS-clean; hygiene wired post-run | L | after R0-005 |

### R3 — prompt hardening
| Packet | Title | Findings | Acceptance | Diff | Order |
|---|---|---|---|---|---|
| TP-RTE-TRUTH-R3-001 | **C9 merge reconciliation** (gates all schema work) + proof-field namespacing | F-20, F-51 | C9 Outputs==Schema==procedure; no field downgrade of C1/C2/C7/C8; ordering coherent | M | **1st in R3** |
| TP-RTE-TRUTH-R3-002 | Injection separator: wrap `build_partition_context` return in `<repo_content>…</repo_content>` + shared `prompt_prefix` preamble constant (dedupe 15301/21540) + template convention line; drop FA-3 xfail | F-30 | FA-3 green; both dispatch sites + async R path wrapped; dry-run payload shows delimiter + preamble | M | after R1 |
| TP-RTE-TRUTH-R3-003 | Schema expansion (post-C9): C8/C2/C1/C7/C14 + G5; evidence-object subschema for G6/G7; thin-contract + enum fixes | F-39, F-36, F-38 | `.schema.json` files via strict-output lane; validator rejects fabricated `{note:…}` evidence; `line_range` min/order asserts | M-L | after R3-001 |
| TP-RTE-TRUTH-R3-004 | Anti-fab regime wiring: secrets-redaction binding (C8/H1/H/M), wire section validator, inject PROMPTSET_RULES to context, strip determinism-violating legacy keys | F-23, F-27, F-31, F-33, F-08 | redaction rule in binding body masks secret span; section validator wired to v4; determinism keys removed; RULES verifiably in context | M | after R3-001 |
| TP-RTE-TRUTH-R3-005a-e | Per-phase content fixes: (a) M recast + H9 sha256 + E-emit-names + M-implementer; (b) S7 rewrite; (c) T-phase contract promote + TP_BACKLOG writers + run_id/generated_at; (d) G9/A99/C9 merge-scope + duplicate surfaces; (e) graph-kind + step-numbering + W/X/Z nits | F-21,F-25,F-37 / F-22 / F-24,F-26,F-27 / F-28,F-32 / F-34,F-35,F-49 | per-defect; each phase's dry-run promptset-truth test passes; determinism lints clean | M×5 | after R3-001 |
| TP-RTE-TRUTH-R3-006 | Synthesis-tier evidence variant in PROMPTSET_RULES (`{upstream_artifact,item_id,excerpt}`) mandated for R7/R8/S4/S5/S6 | F-29 | citation shape required on all prior-output-consuming steps; validator/lint | S-M | after R3-004 |

### R4 — CLI / UX / docs
| Packet | Title | Findings | Acceptance | Diff | Order |
|---|---|---|---|---|---|
| TP-RTE-TRUTH-R4-001 | Wizard execute-path repair: fix `--prescan-dir`→`--prescan-import-dir` (or add passthrough); Stage-0 `DPMX_LIVE_OK` preflight; routing-policy `Choice` | F-40 | wizard `--execute` builds a valid `rte run` command for all phases (dry-run); consent preflight before 14 prompts | M | 1 (highest-value) |
| TP-RTE-TRUTH-R4-002 | Definition-site inversion (rte canonical, upgrades hidden alias) | F-42 | 7 decorators → `@rte.command`; alias-back loop; `upgrades.hidden=True`+deprecation warning; wizard subprocess → `rte run`; both surfaces work | M | after R1 |
| TP-RTE-TRUTH-R4-003 | v5-native `rte scan` (standalone prescan producer) | F-45 | zero-LLM default; emits importable artifacts consumed by `rte run --prescan-import-dir --skip-prescan`; retire `--allow-legacy-v3-scan` | M-L | after R4-002 |
| TP-RTE-TRUTH-R4-004 | Flag standardization + status/trace/promptset-audit cleanup | F-43, F-44 | single `--workers/-w` (`--partition-workers` hidden alias); wizard estimate reads `lib/pricing_surface`; status impls reconciled | M | after R4-002 |
| TP-RTE-TRUTH-R4-005 | Docs sweep to canonical rte surface | F-41, F-46 | `docs/` grep free of runnable `upgrades`; quickstart uses `rte` + `DPMX_LIVE_OK`; truth-snapshots regenerated/annotated; user-journey deduped | M | after R4-001/002 |
| TP-RTE-TRUTH-R4-006 | Dead-code + generated-set decision | F-47, F-48 | 380 dead lines removed; generated set either CI-gated (`run_sync`+integrity) or annotated disposable + regenerated | S-M | any (post-R4-002) |

### R5 — legacy retirement
| Packet | Title | Findings | Acceptance | Diff | Order |
|---|---|---|---|---|---|
| TP-RTE-TRUTH-R5-001 | Retire unreferenced legacy surfaces (repscan/v4 shims, `sp/` shadow-twin routing metadata, base_prompts/archive prompts) | F-50 | A7-style refgraph re-run shows 0 RUNTIME refs to retired targets; **v3 untouched** (test/runtime coupling) | M | last |

---

## 5. Deferred (post-program) — with reason

1. **`run_extraction_v3.py` deletion** — A7: 80 TEST + 10 RUNTIME refs; program charter defers v3 deletion post-release. (F-50 explicitly excludes v3.)
2. **Full v3 routing audit** — second cost-profile-unaware routing path (A6 deferred); separate scope decision.
3. **`--max-cost-usd` runtime hard-stop behavior test** (A6-F8) — wiring **confirmed present this gate** (2a); dynamic proof needs a spend-capped live run — out of this program's dry-run mandate.
4. **Benchmarking secret-redaction gaps** (A6-F2 xai/AIza/XAI_API_KEY patterns) + **two `_SECRET_PATTERNS` copies** (A6-F3) — benchmarking is internal-only (no `src/dopemux/` import; A6 §1 reachability), low operator exposure; consolidate onto `output_safety.sanitize_text_for_output` as a refactor, not a gate finding.
5. **s_int/fl_int hardcoded model-ladder governance** (A6-F6) — spend accounting + caps still apply (routes flow through v5 `call_llm`); governance-only debt, expanding `--cost-profile` to cover S_INT/FL_INT ladders is scope.
6. **`audit_tp008.py` packaging** (A6 §4) — cosmetic; load-by-path works.
7. **Benchmarking orchestration/registry/rollups/scoring/synthesis deep dives** (A6 deferred) — surveyed structurally, no red flags.

---

## 6. Explicitly Vindicated (do NOT re-litigate)

| Item | Verdict | Evidence |
|---|---|---|
| **S7-DRIFT proof `verdict:FAIL`** | Expected gate output on injected `FAKE_STALE_STEP`; RE-CLOSE, no reopen | A5 §4.1; A6 §6 (`d2fe66cac` truth-split now real fail-closed); `PROOF.json` PASSED/10-of-10 |
| **GOLIVE-REMEDIATION-001/-002 proofs** | Work PROVEN; "empty dir" was an auditor path-assumption error (bundles live at `proof/rte-golive-remediation/…`) | A5 §4.2; jsonschema PASS, 49 tests -001; commits ancestors of HEAD |
| **Batch clients** (TP-RTE-BATCH-E2E-006) | Bundle CONSISTENT; honest RED→GREEN trail; merged PR #615, ancestor of HEAD | A5 §4.3 |
| **FA-4 pair** (secret-assign regex + walker env variants) | Both FIXED, markers removed; `\b`→lookarounds redacts `AWS_SECRET_ACCESS_KEY=…`; env glob list extended | A5 §1.2 (`output_safety.py:23`; `lib/prescan/models.py:81-88`) |
| **`audit_tp008.py`** | Live, referenced from operator validation + tests; CLEAN (no subprocess/eval); **do not archive** | A6 §4 |
| **All 11 profiles carry an auto-applied default cap** (NEW, conflict 2a) | Explorer-baseline CONFIRMED; E3 SpendTracker active on every normal `rte run` and bare-runner invocation | `cli.py:5317`; `run_extraction_v5.py:1054-1055,23136-23146,23492,23984` |
| **`pricing/` package + promptgen render pipeline + llm_runtime secret hygiene** | Clean/fail-closed: pricing raises on missing yaml; render injects only metadata not file bodies (templates clean); header values never persisted | A6 §1,§2; A4d §2.1 |

---

## Validation

- **PASS**: conflict 2a re-verified against primary source (`src/dopemux/cli.py`, `run_extraction_v5.py`) — 5 symbol sites confirmed; nine audit reports read in full (A7 mechanical dump read head+tail+structure).
- **NOT_RUN**: no tests, no runner, no live LLM. All non-2a findings ACCEPTED at their source pass's stated confidence; runtime abort behavior of the auto-applied cap remains NOT_RUN (see Deferred #3).
- **UNKNOWN / residual**: exact final severity of prompt-content findings depends on runtime model behavior (A3* scored templates, not outputs); which committed `extraction/` runs are load-bearing fixtures (blocks R0-008); provenance of `docs/03-reference/truth/*` (R4-005 to verify).

**Files touched**: this file only (`claudedocs/rte-truth-program-2026-07/CONSOLIDATED-FINDINGS.md`).
**Git state**: branch `claude/rte-audit-improvement-f4beb7`, HEAD `542c17bb4`, no commits.
**Rollback**: `rm claudedocs/rte-truth-program-2026-07/CONSOLIDATED-FINDINGS.md`.
