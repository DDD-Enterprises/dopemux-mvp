# Independent Embedded Audit — PR #1182

- **Auditor**: copilot-cli
- **Model**: claude-sonnet-4.6
- **Content head**: 7159d0b2481802837a9efbc4296666fccce7a908
- **PR**: 1182 · DDD-Enterprises/dopemux-mvp
- **Audit date**: 2026-08-02
- **Prior corroborating audit**: OpenRouter/Kimi K3 → PASS_WITH_RISKS (historical only)

---

## Verdict: PASS_WITH_RISKS

---

## Checklist Results

### 1. Gemini unresolved non-dispatchable
**PASS.** All 18 gemini-unresolved items carry `(None, None, False)` runners — confirmed non-dispatchable. `gemini_unresolved_all_non_dispatchable: true` in deterministic validation. No gemini-cli item received a live runner/model assignment. Routing correctly deferred with `model-selector-unresolved` flag.

### 2. No Anthropic/OpenAI model IDs on gemini-cli
**PASS.** `bad_anthropic_openai_on_gemini_cli: []` in deterministic validation. MASTER-PLAN §6c explicitly records: "never Anthropic/OpenAI model IDs on gemini-cli." Zero violations found in inline evidence.

### 3. Actionable leaf routing invariants
**PASS WITH RISK.** 355 actionable_leaf items. Routing rubric documented; class constraint (primary_runner + primary_model + backup_runner + backup_model, no concat) stated in §6 validation block. Risk: routing invariant enforcement is self-asserted — no independent schema validation run (`tp:validate` explicitly `NOT_RUN`). Sampling repairs in §5c show at least 3 items were demoted or corrected post-write-back, indicating pre-repair violations existed. No residual violations are claimed, but full coverage is unverifiable from inline evidence alone.

### 4. Class totals sum to 539
**PASS.** `actionable_leaf(355) + series_or_phase_container(72) + operator_gated_decision(28) + cross_repository_parked(2) + stale_or_cancellation_candidate(82) = 539`. `unique_ids: 539`, `duplicate_ids: 0`. `class_match_summary: true`. Deterministic validation agrees. **No anomaly.**

### 5. Luna-ready count = 12, all gpt-5-6-luna
**PASS.** `luna_ready_count: 12`, `luna_primary_models: {"gpt-5-6-luna": 12}`, `non_luna_with_luna_model: []`. MASTER-PLAN §6 states luna-ready revalidated deterministically; failing items demoted; destructive deletes explicitly excluded. §5 also confirms: items failing the luna-ready bar lose `luna-ready` **and** must not retain `primary_model=gpt-5-6-luna`. Count is consistent across deterministic validation and routing summary.

### 6. Operator and destructive gates
**PASS.** Operator-decision ledger (§4, 11 items) documented. `operator_gated_decision: 28` class assigned; these carry no `rec-*` / `model-*` tags (confirmed by routing null policy). Destructive items (DXO-W0-DELETE, red-lane items) flagged `needs-rescope` or `operator-gate`. Load-plan `forbidden_surfaces` and `red_lane_supervisor_items` lists are present and enumerate branch-protection mutations, schema enum changes, Codex-as-auditor, and AGY Tier 0 — all correctly gated. `closure_authorized_by_tag_alone=false` enforced on all `verify-close-candidate` items per §6.

### 7. Dependency evidence
**PASS WITH RISK.** `dependency_evidence.status: DB_EXPORTED`, `source_instance: dopemux-mvp-2e346e2084bca021`, `edge_count: 563` (`BLOCKS: 550`, `RELATES_TO: 13`). Full edge manifest present in `routing-table.json`. MASTER-PLAN §5 states wave-topology BLOCKS reconciled (`wave(prereq) <= wave(dependent)`). Risk: DB export is a point-in-time snapshot at replan write (origin/main `87fbdda574`); a "soft-refresh vs current main required before READY" is explicitly noted in §6. The PR does not include a post-merge DB re-verification. Edge manifest correctness is not independently provable from inline evidence — it is self-reported from the same session that wrote the tags.

### 8. Load-plan LOADED; Wave 0 not authorized for agent dispatch
**PASS.** Both load plans show `"loaded": true` and `"live_task_orchestrator_load": "LOADED"`. Wave 0 entries are in routing summary (`wave_0: 30`) but Wave 0 is scoped to "verify tasks / haiku/luna" — all verify-close-candidates, stale-candidate sweep, and DB-hygiene items. No Wave 0 item is an autonomous destructive action; all require human or verified-evidence confirmation. The audit prompt's concern ("Wave 0 needs operator") is satisfied: the operator-decision ledger and `verify-close-candidate` with evidence refs gating are in place.

### 9. Git rollback ≠ live DB reverse
**PASS.** §6b rollback note explicitly distinguishes: "revert replan export commit for routing freeze; revert load-plan/defrag commit only if receipts must be unwound (live DB is out-of-band)." The db-defragmentation doc (correctly added as reference, not as a reversible artifact) notes that the DB manipulation is out-of-band from git. No claim that reverting the PR undoes DB state.

### 10. Wave 0 operator gate
**PASS WITH RISK.** Wave 0 items (30) are hygiene/verify tasks, not autonomous implementations. Operator-decision ledger (11 items) is explicit and documented. Risk: the five `unblock-candidate` items (stale-blocked unblocks) in Wave 0 do not have explicit per-item operator sign-off documented in this PR — unblock execution is implied safe but not gated by a receipt in the proof bundle.

---

## Findings

### F-01 — RISK · `tp:validate` NOT_RUN on rewritten TP JSON files
Routing recommendations kept out of TP JSON per `additionalProperties:false` constraint, but the routing repairs to existing packets were not independently schema-validated this session. Self-asserted compliance. **Severity: LOW** (routing lives in orchestrator tags, not TP fields; schema violation risk is contained).

### F-02 — RISK · Staleness baseline requires soft-refresh before execution
Replan written against origin/main `87fbdda574`. §6 explicitly flags "soft-refresh vs current main required before READY." ~39 open PRs, PR #1127 open, PR #1136 open unmerged. Any Wave 1+ dispatch without a refresh risks acting on a stale dependency picture. **Severity: MEDIUM.** Mitigation: gate runner dispatch on `git fetch` + re-export from DB against current main HEAD.

### F-03 — RISK · `claude/rte-truth-followup` has no PR
MASTER-PLAN §3 notes the followup branch (`a8faf22b49`, 6 packets including D-008 injection fix) has **no PR**. Merging #1136 does not land it. This is an undiscovered execution gap that could mislead downstream wave planning. Recorded in operator-decision ledger item 10 but not yet actioned. **Severity: MEDIUM.**

### F-04 — RISK · MERGE-001 packet references dead PR #1043
Noted in operator ledger item 1: MERGE-001 packet referenced dead PR #1043, retagged `needs-rescope`. Correct disposition; but the packet remains non-terminal with a stale premise. Execution against the old packet body would be incorrect. **Severity: LOW** (mitigated by `needs-rescope` tag).

### F-05 — INFO · adhd-dashboard fail-open auth (DASH-001 scope)
`verify_api_key → None` allows all requests on `0.0.0.0:8097`. Surfaced during replan, folded into DASH-001 as security scope. Not a PR #1182 defect, but a live defect confirmed during this audit window. **Severity: informational here** (owned by DASH-001).

### F-06 — INFO · `SuppressionTelemetry` referenced but absent from `event_coordinator.py`
Possible regression. Noted in §5b. Not in PR #1182 scope. **Severity: informational.**

### F-07 — INFO · DXO-W0-DELETE `needs-rescope` confirmed
"57 /tm:* commands" don't exist on main; "6 dead hooks" are live dependencies. Correctly marked `needs-rescope`. No execution risk from this PR. **Severity: informational.**

---

## Residual Risks Summary

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R-01 | `tp:validate` not run; routing invariants self-asserted | LOW | Run `tp:validate` before dispatch |
| R-02 | Staleness: replan baseline is `87fbdda574`, not current HEAD | MEDIUM | Soft-refresh + DB re-export before Wave 1+ dispatch |
| R-03 | `claude/rte-truth-followup` no PR; 6 packets unmerged | MEDIUM | Open PR or operator decision to drop/cherry-pick |
| R-04 | MERGE-001 needs-rescope not yet re-written | LOW | Rescope packet before RTE-TRUTH merge sequence |
| R-05 | 5 `unblock-candidate` items lack per-item operator receipt | LOW | Confirm unblocks before execution |

---

## Scope

PR contains 17 files: 2 replan exports (`MASTER-PLAN.md`, `routing-table.json`), 1 new reference doc (db-defragmentation), 1 index update, 2 load-plan updates, and 11 proof/bundle artifacts. All changed files are documentation, load-plan JSON, and proof artifacts. **No application code modified.** No compose files touched. No schema enum changes. No forbidden surfaces activated.

---

## Rationale for PASS_WITH_RISKS

All 10 deterministic checks pass or pass-with-documented-risk. No invariant is violated. No forbidden surface is activated. No destructive action is ungated. The two MEDIUM risks (staleness baseline, missing followup PR) are real but pre-existing conditions — they are correctly surfaced in the replan itself and do not constitute defects introduced by this PR. The proof bundle is structurally complete. Prior Kimi K3 PASS_WITH_RISKS verdict is consistent with this independent finding.

**This PR is safe to merge subject to the operator acknowledging R-02 and R-03 before authorizing Wave 1+ agent dispatch.**

---

*Audit complete. Read-only. No repository files modified.*
