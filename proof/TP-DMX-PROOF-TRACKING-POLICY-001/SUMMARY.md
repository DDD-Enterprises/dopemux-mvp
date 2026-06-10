# Capsule SUMMARY — TP-DMX-PROOF-TRACKING-POLICY-001

packet_id: TP-DMX-PROOF-TRACKING-POLICY-001
branch: claude/hungry-lalande-e617d2
head_sha_before: 4fe853a099b283b00e8eaed5c2abff2370b99ce9
verdict: READY_FOR_REVIEW

---

## Objective

Establish and document the rule: **proof bundles are tracked by default**. Resolve the path-schema contradiction between the generic `proof/<skill>/...` pattern and Development Factory packet paths (`proof/TP-DMX-*/`). Define commit lifecycle fields. Prevent stale-proof and done-without-proof claims. Resolve MODEL_ROUTING artifact tension.

---

## Decision Applied

**Option A — factory skill tier**: The Development Factory is named as an explicit `factory` skill tier within the `proof/<skill>/...` schema. Paths of the form `proof/TP-DMX-<id>/` are its canonical pattern — the `TP-DMX-` prefix makes the tier machine-identifiable without requiring an explicit `factory/` directory prefix. No exemption used.

---

## Changes Made

### docs/03-reference/development-factory/evidence-and-proof-flow.md
- Added `## Proof Git Tracking` section:
  - TRACK / DO_NOT_TRACK table (8 tracked types, 7 excluded types)
  - Gitignore strategy: keep `proof/*`, use `git add -f` explicitly
  - Model routing receipt policy: prefer inline `model_routing_receipt` in PROOF.json; `MODEL_ROUTING.json` allowed only if explicitly referenced
  - Stale-proof prevention: conditions under which a packet must NOT be declared done

### docs/03-reference/governance/proof-directory-rules.md
- Added `## Skill Tiers` section: table of all 4 skill tiers (`pr_prep`, `pr_merge`, `governance`, `factory`) with their path patterns
- Added `## Proof Git-Tracking Tier` section: summary TRACK / DO_NOT_TRACK table + pointer to full table in evidence-and-proof-flow.md
- Updated canonical patterns to include `proof/TP-DMX-<id>/...` (factory tier)
- Updated examples to show factory tier path

### docs/03-reference/governance/proof-path-normalization-rules.md
- Added `factory` to Skill Root values (`pr_prep`, `pr_merge`, `governance`, `factory`)
- Added factory tier canonical path note (special case: no `factory/` prefix needed)
- Added `### Force-Add Convention (git add -f)` section explaining why the blanket `proof/*` gitignore must NOT be removed and why explicit `git add -f` is required

### docs/03-reference/development-factory/red-lines-and-stop-conditions.md
- Added to Red Line Register: "Proof bundle not committed for a completed packet" — marks it a hard stop to claim done/complete/PR-clean without a committed PROOF.json + SUMMARY.md

---

## Invariants Verified

- ✅ Docs-only packet — no runtime code, schema, or config touched
- ✅ `.gitignore` not modified — `proof/*` safety net preserved
- ✅ No secrets committed
- ✅ Policy is additive — does not retroactively require re-committing past proof
- ✅ All red lines preserved and not weakened

---

## Validations

| Check | Status | Evidence |
|-------|--------|----------|
| No runtime code touched | PASS | src/, tests/, scripts/, .github/ absent from diff |
| No schema created | PASS | schemas/ not touched |
| No .gitignore modified | PASS | Not in allowed files |
| Red lines preserved | PASS | queue_drain, batch_resolve, LIVE_WRITE_READY, DCP-RED-MERGE-SEAM not weakened |
| rg policy terms in docs | TBD | Pending validation run |
| PROOF.json valid JSON | TBD | Pending validation run |

---

## Remaining Risks

- PAL external codereview not run (docs-only; risk is low but not zero)
- Pre-commit hooks not run
- `factory` tier normalization tooling not yet updated — path validator still only accepts `pr_prep|pr_merge|governance`
- This proof bundle itself uses the factory tier it defines (circular but intentional)

---

## Next Recommended Packet

`TP-RTE-S7-DRIFT-FIX-001` — re-scoped to verify-and-close: run S7 gate against injected drift, confirm FAIL.
