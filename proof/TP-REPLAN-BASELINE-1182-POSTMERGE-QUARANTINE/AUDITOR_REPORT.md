# PR #1182 Post-Merge Audit Quarantine

- Packet: `TP-REPLAN-BASELINE-1182-POSTMERGE-QUARANTINE`
- Canonical Task Packet: `task-packets/TP-REPLAN-BASELINE-1182-POSTMERGE-QUARANTINE.json`
- Schema report path: `proof/TP-REPLAN-BASELINE-1182-POSTMERGE-QUARANTINE/AUDITOR_REPORT.md`
- PR-merge package (historical/support): `proof/pr_merge/embedded-audit/pr-1182/`
- Merged PR head (authoritative for landed content): `1b80fc6f11681baebdb00acc7f756ce8471a24b0`
- Merge commit on main: `fb710ef40500695882a5b421a3325150176fffa1`
- Formal status: **SKIPPED** (exact-head independent audit **NOT_PROVEN**)

## Decision

PR #1182 implementation content is merged and authoritative on `main`.
The audit lane is **not closed**. No exact-head independent audit attests the
content that landed.

## Why prior proofs are not exact-head evidence

1. **Merged head** `1b80fc6f…` is eight commits beyond content head
   `7159d0b2481802837a9efbc4296666fccce7a908` that a later Copilot audit bound.
   Those intermediate commits include substantive `routing-table.json` changes,
   so the Copilot proof is **not** a proof-only successor of the landed head.
2. Diverged proof tip `59374bc7…` contains the Copilot package but does **not**
   sit on the merged history; tree equivalence cannot rescue it.
3. The proof that shipped on main with the merge was bound to `b7387429…` and
   used `claude-code-cli`/`sonnet` as **schema carriers** while stating the real
   auditor was Codex. That is not truthful exact-head evidence and is preserved
   only as historical quarantine material (see review_bundle).

## Historical / corroborating evidence (not formal READY)

| Artifact | Role |
|----------|------|
| `review_bundle/HISTORICAL_MAIN_PROOF_BEFORE_QUARANTINE.json` | Pre-quarantine main PROOF (Codex exception + Claude carriers) |
| `review_bundle/HISTORICAL_MAIN_AUDITOR_REPORT_BEFORE_QUARANTINE.md` | Pre-quarantine main auditor report |
| `review_bundle/HISTORICAL_COPILOT_CLAUDE_SONNET_4_6_REPORT.md` | Copilot CLI audit of `7159d0b2…` (PASS_WITH_RISKS; not exact-head for merge) |
| `review_bundle/HISTORICAL_KIMI_K3_AUDITOR_REPORT.md` | OpenRouter/Kimi K3 corroboration (PASS_WITH_RISKS; not schema formal) |

## Explicit non-claims

- Does **not** claim PR Steward READY.
- Does **not** authorize Wave 0 dispatch.
- Does **not** re-open or re-merge PR #1182.
- Does **not** assert Claude or Codex as the formal auditor of the merged head.

## Operator note

Prefer an explicit operator manual-merge evidence exception over treating any
prior proof as exact-head readiness. A future exact-head audit, if ever required,
must re-bind to the actual landed content SHA and use a schema-truthful route.
