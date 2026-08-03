# Independent Embedded Audit — PR #1182

- Auditor: openrouter
- Model: moonshotai/kimi-k3
- Content head: 7159d0b2481802837a9efbc4296666fccce7a908
- Verdict: **PASS_WITH_RISKS**

## Scope

Replan export (`MASTER-PLAN.md`, `routing-table.json`) + inherited operational truth (defrag reference doc, index link, two load plans) + proof bundle. Diff is docs/ops/proof only — no executable surfaces, no `tools/pr_merge/**`, no workflow/protection/CODEOWNERS changes. Load-plan `forbidden_surfaces` are not touched by the changed-file set. Prior Codex proofs treated as historical; verdict rests on the deterministic validation and inline evidence.

## Must-verify results

| # | Check | Result |
|---|---|---|
| 1 | Gemini unresolved non-dispatchable | **PASS** — 18/18 at `(runner=None, model=None, dispatchable=False)`; `gemini_unresolved_all_non_dispatchable=true`; matches `model-selector-unresolved: 18` flag count |
| 2 | No Anthropic/OpenAI IDs on gemini-cli | **PASS** — `bad_anthropic_openai_on_gemini_cli: []`; policy restated in §6c |
| 3 | Actionable invariants | **PASS (summary level)** — `dispatchable_actionable=355` = `actionable_leaf` count; runner split 180 claude-code + 175 codex = 355, `none=184` = 72+28+2+82 non-actionable classes; model split 163+12+87+56+37 = 355, `none=184`. Per-item backup-runner/model and `routing_na_reason` fields not independently recomputed (attestation + arithmetic consistency only) |
| 4 | Class totals = 539 | **PASS** — 355+72+28+2+82 = 539 = `item_count` = `unique_ids`; `class_match_summary=true`; wave buckets 30+24+103+85+116+150+31(null) = 539 |
| 5 | Luna-ready 12, all gpt-5-6-luna | **PASS** — `luna_primary_models` contains only `gpt-5-6-luna: 12`; `non_luna_with_luna_model: []` (Codex P2 demotion invariant holds); flag count, ready count, and summary all = 12 |
| 6 | Operator/destructive gates | **PASS** — `operator-gate` flag 28 = `operator_gated_decision` class 28; stale cohort 26 stale-candidate + 56 needs-rescope = 82 = `stale_or_cancellation_candidate` (non-dispatchable); `closure_authorized_by_tag_alone=false`; "destructive deletes never luna-ready" enforced by invariant 5 |
| 7 | Dependency evidence | **PASS (count reconciliation)** — `dependency_evidence.status=DB_EXPORTED`, source instance `dopemux-mvp-2e346e2084bca021` matches defrag doc's canonical instance; 563 = 550 BLOCKS + 13 RELATES_TO; full manifest present in artifact (excerpt truncated in review bundle — individual edges not re-verified inline) |
| 8 | Load plans LOADED; Wave 0 not authorized | **PASS** — both plans `loaded: true` / `LOADED`, corroborated by defrag doc (TO-CANON 8 packets, EMBEDDED-AUDIT-RECONCILED 12 packets created as genuinely never-loaded); plan is a routing export, not an execution grant; verify-close-candidate tag explicitly never authorizes closure |
| 9 | Git rollback ≠ live DB reverse | **PASS** — §6b explicitly scopes rollback to the git commits and declares the live DB out-of-band |
| 10 | Wave 0 needs operator | **PASS WITH CAVEAT** — Wave 0 destructive items (6 TEST-root deletes, `cb80e2fc` cancel) are classed `stale_or_cancellation_candidate` = non-dispatchable, so no auto-picker can claim them. Caveat: see Finding F1 |

## Findings

**F1 (minor) — Wave 0 destructive prose not enumerated in the operator ledger.** §4 Wave 0 reads imperatively ("Junk TEST roots (6) → delete… → cancel"), but the numbered operator-decision ledger does not list these specific DB mutations. The class system structurally prevents agent dispatch (stale cohort has null routing, confirmed by validation), so this is a documentation gap, not an authorization hole. Recommend an explicit "operator-only DB mutation" line in the Wave 0 header or ledger entry before any delete/cancel is executed.

**F2 (minor) — Security-relevant defect scheduled behind Wave 3.** The newly surfaced adhd-dashboard fail-open auth (`verify_api_key→None` on 0.0.0.0:8097) is folded into DASH-001, whose unblock is Wave 0 but whose work sits in the Wave 3 SVCFIN chain. Given Wave 1 is the designated security lane, a fail-open auth bound to all interfaces arguably belongs there. Prioritization judgment, not an invariant violation — flagged for operator awareness.

**F3 (informational) — Attestation-based verification limits.** Per-item routing fields (backup runner/model on 355 leaves, `routing_na_reason` on 184 non-actionables) and the 563-edge manifest are validated via the deterministic summary + arithmetic reconciliation, not full independent recomputation from the truncated excerpt. Summary arithmetic is internally consistent across five independent cross-cuts (class, wave, flag, runner, model), which would be difficult to fake coincidentally.

**F4 (positive) — Internal consistency is strong.** Every flag count that must equal a class count does (operator-gate 28/28, cross-repo 2/2, stale+rescope 82/82, luna 12/12, gemini-unresolved 18/18). Premise flips, sampling repairs (b807751c, aafc2630, 207ec91a), the RTE-TRUTH ID collision, and the DXO-W0-DELETE CI-breakage rescope are disclosed rather than hidden. Schema constraint (`additionalProperties:false`) respected — no TP JSON in the diff, so `tp:validate NOT_RUN` is correctly justified.

**F5 (positive) — Staleness honesty.** Baseline pinned to `origin/main@87fbdda574` with an explicit self-imposed soft-refresh requirement before READY; "LANDED" claims correctly qualified as on-branch for unmerged PR #1136; stranded branches (including the no-PR `claude/rte-truth-followup` and complete R4-003 impl) enumerated in the operator ledger.

## Remaining risks

1. **Premise drift** — PR #1136/#1127 status, open-PR census (~39), and main have moved since 2026-08-02; the plan's own §6 soft-refresh gate must be honored before any wave executes.
2. **Gemini docs lane blocked** — 18 items non-dispatchable until a live-proven Google model selector exists; correctly fenced (no wrong-provider fallback), but throughput on docs routing is zero until resolved.
3. **Live DB divergence** — tags were written to the orchestrator DB out-of-band; a git revert of this PR does not unwind them (correctly documented in §6b). Operators must not treat branch revert as DB rollback.
4. **verify-close-candidate cohort (11 items)** — closure still requires per-item evidence review; 19 RTE-TRUTH "done" packets exist only on unmerged PR #1136.
5. **F1/F2** as above.

## Rationale

All ten must-verify invariants hold against the deterministic validation, with five independent summary cross-cuts reconciling exactly. The diff touches no forbidden or red-lane surfaces. The two substantive gaps (Wave 0 operator-gate prose, security-item placement) are documentation/prioritization issues with structural safeguards already preventing misuse — they warrant disclosure and correction, not blocking. No supervisor escalation is required: no schema enum changes, no protection/ruleset mutation, no CODEOWNERS, no `pull_request_target`. Hence **PASS_WITH_RISKS**: mergeable as a routing/planning artifact; execution of any wave remains gated on the operator ledger, the §6 staleness soft-refresh, and per-item evidence for verify-close.
