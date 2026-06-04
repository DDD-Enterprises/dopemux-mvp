# DCP Adversarial Architecture Audit (Opus, Stage 3)

> [!NOTE]
> **Provenance**: `EXTERNAL_PROPOSED`  
> **Status**: Preservation Only (Design Input / Audit Artifact)

**Auditor**: Opus (adversarial architecture auditor), 2026-06-03
**Target**: `DCP_ARCHITECTURE_SYNTHESIS_GPT55.md` (GPT-5.5 Pro decision artifact) — auditing the *synthesis decision*, not re-auditing the evidence.
**Inputs**: 3 lens drafts (`_audit_drafts/A.md` ledger-blind, `B.md` ledger-aware/laundering, `C.md` premature-build/unsafe), synthesis §12 (10 self-flagged weak assumptions), `DCP_5_5_SYNTHESIS_INPUT_PACK.md` (primary-source spot-checks).
**Gate scope**: The GATING verdict is scoped to **TP-DCP-0001 ONLY** — the contract-locking, read-only first packet (synthesis §10). D1–D16 critique is **non-blocking ADVISORY for later stages** and labeled as such.
**Authority frame**: Repo-runtime evidence (pack §1–§10, from `evidence/*.md`) OUTRANKS external DR (pack §9, VENDOR_DOCS / LOWER_THAN_REPO_RUNTIME). Open PRs #765–792 + generated TP series stay CLAIMED_ONLY. UNKNOWN is not promoted.
**Ground-truth treated as RESOLVED** (operator-run read-only vs `origin/main` @5dbfef5e, 2026-06-02 — not reopened):
- `steward_gate.py` ABSENT in origin/main AND feature HEAD (exists only in unmerged PRs #765–767).
- `execute_or_dry_run(merge_cmd, execute=True)` at `queue_drain.py:617/2006/2017` **IS in origin/main** → ungated `gh pr merge` capability is ACCEPTED AUTHORITY in main while its guard is unbuilt. **Resolves L-09: synthesis "quarantine; build the gate first" is VINDICATED.**
- PR-Steward ADVISORY surface (`pr-steward.yml`, `tools/pr_steward/intake.py`, `scripts/pr-steward`) IS in origin/main → **Resolves L-01 for the advisory surface**; unmerged `dopemux pr-steward` CLI bits stay CLAIMED_ONLY.
- dNh `PROOF_CONTRACT_VERSION="1.2"` confirmed in runtime (`bundle.py:25`) vs bootstrap "v1" → `.v0` DCP naming correctly sidesteps. **Resolves K-27.**

---

## 1. Gate verdict — TP-DCP-0001

### **GO_WITH_FIXES**

The first packet is correctly scoped as a read-only, static-fixture-only contract lock that touches **no** live adapter, network call, subprocess-to-external, merge/review automation, Dopetask exec, ConPort/TO/CRM/bridge surface, or cockpit — and it explicitly stays clear of the in-main, ungated `execute=True` merge seam that ground-truth confirms is live and unguarded. That side-effect/quarantine posture is **GO** and is vindicated by ground-truth (L-09, L-01-advisory, K-27 all tip in the synthesis's favor). It is **not GO** as written for one structural reason: the *deliverable of this packet is the locked contract floor itself*, and §6.2/§6.3/§6.4 (chronicle-receipt / evidence-hit / helper-receipt) plus the synthesis-invented `DCP_PROOF_POINTER` fields are **external-DR-derived (DR-016, VENDOR_DOCS) or synthesis-invented field-lists carrying no provenance tag and no validation-status marker**, locked into "the DCP contract floor" (§4) where every downstream packet will cite them as repo-authoritative. The `.v0` naming the packet mandates hedges *version* (K-27) only — it carries no provenance/validation hedge, so the durability hazard the HARD FRAME names (external DR silently acquiring repo-runtime authority) ships through this packet ungated. This is fixable without redesign — every §6 finding is REVISE, not KILL; the packet's purpose is sound. Hence **GO_WITH_FIXES**, not NO_GO. The 2-of-3 lens consensus (A REVISE, C HOLD-pending-fixes) gates on this; the lone GO lens (B) collapses into the same place — its "single actionable REVISE" (add provenance tag + §11 carry-forward) is a fix that *must precede the lock*, and for this packet the lock is the build, so the fix must precede the build.

**Blocker count (gates TP-DCP-0001): 1** (§6 provenance — Must-Fix #1).
**Must-fix count: 5** (one blocker + four MAJOR/MINOR gate-integrity fixes — §2).

---

## 2. Must-fix BEFORE building TP-DCP-0001

These are concrete, bounded changes. #1 is the blocker; #2–#5 are MAJOR/MINOR gate-integrity defects that all three lenses (or verified primary-source reads) support.

1. **[BLOCKER · §6 / §4 / §10 Scope IN] Provenance-tag every contract field-list; demote external/invented shapes out of the flat DECIDED frame.**
   §4 enumerates 9 generic contracts as flat fact; §6 specifies 4 as field-lists with **zero per-field provenance**. Verified counts: §6.3 `DCP_EVIDENCE_HIT` = **exactly 17 fields** (matches pack §9.1 / D13 "DR-016 17-field Evidence-Hit spec" verbatim); §6.2 `DCP_CHRONICLE_RECEIPT` = 22 (pack D12 "DR-016 ~24-field"); §6.4 `DCP_HELPER_RECEIPT` = 15 (pack "DR-016 ~20-field"; no repo-runtime helper-receipt exists). Fix: tag each of the 9 §4 contracts `REPO_VALIDATED` / `EXTERNAL_PROPOSED (DR-016)` / `SYNTHESIS_INVENTED`, and mark the EXTERNAL/INVENTED ones `status: PROVISIONAL — UNVERIFIED_ENFORCEMENT until repo-local field-vocab reconciliation`. Add a §11 carry-forward row: "DR-016 field-vocab is external-seeded; pack flags D12 'field-name vocab UNKNOWN (repo-local)' + DR-016 §7's 13 repo-only UNKNOWNs PENDING before any contract leaves `.v0`."

2. **[BLOCKER-adjacent acceptance criterion · §10] Add a per-field provenance acceptance gate so the fixture cannot validate circularly.**
   §10 Acceptance is "static fixture validates" — a fixture the author writes to match the external-derived schema validates circularly; nothing checks field provenance. Add: *"each contract field is either (a) cross-checked against a cited repo artifact, or (b) carries an `external-proposed` / `synthesis-invented` provenance flag; the embedded audit verifies provenance tags are present, not that the fixture round-trips."* (Closes the A-1 / C-01 circularity that makes #1 enforceable rather than cosmetic.)

3. **[MAJOR · §10 Acceptance] Re-scope "no subprocess" — it currently forbids the packet's own validation and proof bundle.**
   §10 Scope IN requires "schema validation tests" (= pytest = subprocess) and §10 Acceptance requires a "proof bundle" with branch/SHA fields (= `git` = subprocess), while the *same Acceptance line* says "no subprocess/network/... calls." As written the gate forbids its own satisfaction; read charitably it is a local-subprocess loophole. Fix: *"no live external/network/GitHub/Dopetask/chronicle/ConPort/TO/CRM/bridge/mutation subprocess; local pytest + read-only `git rev-parse`/`git status` for proof metadata permitted."* (Lens C-02; verified textually self-contradictory.)

4. **[MAJOR · §10 Acceptance] Encode auditor ≠ implementer for the packet's own sign-off — the packet defines the self-certification red lane.**
   §5 lists "self-certifying implementer/auditor/supervisor loop (hard block)" + "AI-agent-authority-collapse" as universal lanes this packet itself authors. §10 says only "embedded audit reviews only the contract artifact" — verified: **no** "auditor ≠ implementer" / independent-audit / supervisor-sign-off-separate constraint appears anywhere in §10. The packet that defines the role-separation lane must encode role separation for its own acceptance or it violates the lane on contact. Fix: add to §10 Acceptance: *"embedded audit performed by an actor distinct from the contract author; no self-certification; supervisor sign-off recorded separately (DR-012 role separation; §5 hard block)."* (Lens C-03.)

5. **[MAJOR/MINOR · §4 / §10 Scope IN] Derive-or-defer the three shapeless repo-derived contracts; mark `DCP_CONTROL_SNAPSHOT` projection fields provisional.**
   §10 Scope IN names all 9 contracts as the floor, but the synthesis decides field-shape for only 4 (+ red-lane enumeration). `DCP_MUTATION_CLASS`, `DCP_APPROVAL_ARTIFACT`, `DCP_PROJECT_RESOURCE_MAP` are Scope IN with **no decided shape** — and these are precisely the contracts with *repo authority available* (`config/orchestrator/approval_policy.yaml` + `policy.py` for mutation-class/tiers T5/T6/TX; repo path inventory for the resource map). Authoring first-draft shapes is what a contract-locking packet does, so "cannot complete" is overstated — but the must-fix is specific: **either derive `DCP_MUTATION_CLASS` (and the approval-artifact tier bindings) from the cited `approval_policy.yaml`/`policy.py`, or explicitly de-scope the three shapeless contracts from TP-DCP-0001 Scope IN into a follow-on packet** so the floor is honest about what it locks. Separately, tag `DCP_CONTROL_SNAPSHOT` per-surface projection fields PROVISIONAL pending `DCP_PROJECT_RESOURCE_MAP` + canonical-root resolution (L-12); lock only the envelope + authority-metadata wrapper, not per-surface projection fields. (Lens A-2 inversion + C-05.) The C-04 fixture guard — "SHA/hash values are illustrative placeholders authored from pasted evidence text only; no file-system traversal of the target repo" — folds in here.

---

## 3. Per-decision verdicts (D1–D16) — ADVISORY (non-blocking for the first packet)

`affects_first_packet=false` for every row below (TP-DCP-0001 has no adapters, cockpit, PR-plane, or live reads). These are later-stage advisories.

| Decision | Lens consensus | Verdict | Evidence basis | Note |
|---|---|---|---|---|
| D1 Core location | A: observed-surface, weak but self-flagged; B/C: DR-011 correctly demoted | **HOLD** | OBSERVED (mixed CLI/services/adapter/artifact workspace) | Location rests on observed-surface convenience; DR-011 (external, lower rank) correctly stripped to §11 advisory. §12 #1 already flags "separate package may be better post-stabilization." No laundering. |
| D2 TO posture | B/C: separation OBSERVED-sound; BOUNDARY memo ranked above runtime in pack authority-order | **NEEDS-EVIDENCE** | OBSERVED name-collision (TP-0001/0002/0003) + DERIVED (BOUNDARY memo) | Separation sound, must NOT be nuked. Settledness leans on BOUNDARY memo ("synthesis-only, no new recon"); verify K-05 S3→S1 `server.py` compose coupling + K-02/03 canonical root before any jpicklyk projection. §11 L-07/L-12 carry this. |
| D3 Dopetask scope | A: reads series-state that does not exist today; B: OBSERVED 9-module zero-subprocess adapter | **NEEDS-EVIDENCE** | OBSERVED (rg-confirmed zero-subprocess adapter) | "Read existing bundles" is sound for *existing proof bundles* but `.dopetask/series/` state.json does NOT exist (`find` → only project.json); `from_series_id` requires an absent file. Series-state acquisition UNDEFINED (3 options). Wishful for the live-adapter stage; sidestepped in packet 1 by static fixture. |
| D4 Generic/project split | B/C: asymmetry preserved, DR-015 packaging demoted | **HOLD** | OBSERVED asymmetry (XPROJ) + EXTERNAL packaging (DR-015) | Correctly splits architecture-language from package-names ("DR-015 packaging names not runtime-mandated"). Deny-by-default + "profiles add stricter rules only" is leak-resistant. Clean. |
| D5 Cockpit MVP | B/C: `safe_for_claude_design:NO` travels inline | **HOLD** | OBSERVED (governed TUI on main) | L-04 worry (design-gate not traveling) resolved — §7 PRESERVED RISK carries "code consumable read-only, NOT design-cleared, implementer mode unbuilt" inline. Web Palette correctly UNKNOWN/OPEN_SCOPE. |
| D6 Automation ladder | All: correctly PROVISIONAL | **HOLD** | INFERENCE (UX step-count DEFERRED) | Honestly marked PROVISIONAL; UX evidence deferred (L-10). No over-claim. |
| D7 First build packet | All: scope decision sound | **HOLD** | OBSERVED scope | The contract-locking-only posture is the right floor. (Its *content* defects are the §2 must-fixes, but the decision to lock-first is correct.) |
| D8 Dry-run set | All: forbidden set correct | **HOLD** | OBSERVED forbidden set + EXTERNAL gates corroborating | LIVE_WRITE_READY master gate kept default-deny/undefined+blocking (K-46). Advisory for later: synthesis does not yet specify *who defines* LIVE_WRITE_READY or *what proof closes it* — flag for D8 closure, not packet 1. |
| D9 Proof representation | A: pack endorsed "B OR C", synthesis chose "B+C" (union) | **REVISE** | OBSERVED (5 shape families, PROOF-0001) + EXTERNAL (DR-005 compose) | Pack O-8 + line 241: "Evidence supports **B or C**" (either/or). Synthesis decided **B+C** (new pointer artifact AND dispatcher) — more than endorsed. Self-flagged §12 #4. Pressure-test whether dispatcher (C) alone suffices, deferring the new pointer (B) until a consumer needs it. Packet 1 can lock the pointer as `.v0` provisional regardless. |
| D10 Red lanes | B: universal "authority-collapse" lane rests partly on EXTERNAL DR-012 | **REVISE** | OBSERVED (RUNTIME-0001 membership) + EXTERNAL (DR-012 role-sep) | Universal lanes are deny-by-default *hardening* (fails safe — opposite of laundering risk), so MINOR. But cite the repo-grounded slice (schema-level Codex exclusion in `embedded_audit.schema.json` + S5 proof validation) separately from the DR-012 general principle, so the lane is not later read as fully repo-proven enforcement when only a slice is. |
| D11 Memory split | All: clean; no system promoted to AUTHORITY | **HOLD** | OBSERVED (MEMCTX-0001 READ/EXPORT/POINTER) | Outranks + corroborates DR-014. dopecon-bridge NOT treated as authority (K-28 README overclaim not inherited). Clean. |
| D12 Chronicle receipt | A/B/C: §6.2 field-list is the laundering hazard *when locked* | **REVISE** | **EXTERNAL (DR-016 ~24-field)**; pack: "field-name vocab UNKNOWN (repo-local)" | As a *later-stage decision* the receipt *idea* is repo-grounded (`memory_writers.py` WriteReceipt); the specific shape is DR-016's. The packet-1 lock is the Must-Fix #1 blocker; the decision itself is REVISE (provenance-label before leaving `.v0`). |
| D13 Retrieval source-trace | A/B/C: §6.3 = 17 fields = DR-016 verbatim | **REVISE** | **EXTERNAL (DR-016 17-field)**; pack: `complexity` NOT in dope-context return | The 17 fields *operationalize the repo's own anti-laundering discipline* (`authority_tier ⊥ confidence`, `derived`, `canonical_writer`, SHA-freshness) — congruent with MEMCTX-0001, not foreign. But the one external field that WAS runtime-checked (`complexity`) FAILED. Provenance-label; reconcile vocab before `.v0` exit. |
| D14 Cockpit timeline source | All: artifacts-first, chronicle-enrich-later as UNKNOWN | **HOLD** | OBSERVED posture | Correct provisional framing; chronicle enrich deferred to endpoint/deployed-primary resolution. |
| D15 Tooling boundaries | B: helper-receipt slice (§6.4) is DR-016-derived | **HOLD** (decision) / **REVISE** (§6.4 field-list) | OBSERVED (DR-015 BUILD_AFTER_CORE + repo infra) + EXTERNAL (helper-receipt) | Contracts-first / hooks-enforce / humans-approve / `defaultEnabled:false` is OBSERVED-sound. Only the §6.4 helper-receipt field-list inherits the Must-Fix #1 hazard. L-06 (config ≠ enforcement; duplicate in CI) correctly carried. |
| D16 Mirrors/proxies | All: clean | **HOLD** | OBSERVED (dopecon-bridge TRANSPORT_ONLY routes.py + manifest) | "Mirrors/bridges/proxies/indexes never authority; every payload carries upstream authority metadata." K-28 README overclaim not inherited. Clean. |

---

## 4. Authority-laundering findings

**The one genuine laundering finding (§6 / DR-016).** The synthesis resolves an UNKNOWN by importing an external-authority shape *without labeling that it did so*. Precise charge:
- Pack §14 **D12** explicitly flags the chronicle-receipt "**field-name vocab UNKNOWN (repo-local)**" and pack §9.1 notes DR-016 §7's "**13 repo-only UNKNOWNs**." The synthesis §6.2 **resolved that UNKNOWN** by adopting the DR-016 ~24-field shape (rendered as 22 fields) and presenting it as a flat **DECIDED** generic contract.
- §6.3 `DCP_EVIDENCE_HIT` = **exactly 17 fields**, matching pack D13 "DR-016 **17**-field Evidence-Hit spec" — exact-count match ⇒ DR-016 was the template, not repo runtime.
- All DR is `VENDOR_DOCS / LOWER_THAN_REPO_RUNTIME`, and the pack states the C3 rule outright (line 376): *"any synthesis reading corroboration as validation has introduced authority laundering."*
- **The mechanism that makes it gate**: TP-DCP-0001 §10 Scope IN locks these as "the contract floor." Once locked, downstream packets cite the schema as authoritative, and VENDOR_DOCS field-lists silently acquire repo rank — the corroboration→authority promotion the HARD FRAME forbids.

**Calibration — what this charge is NOT (do not overclaim):**
- It is **not** "fabricated fields." Some fields are repo/DR-005-grounded: `head_sha`, `dirty_worktree`, `mixed_sha_artifact_set`, `validation_state`, `auditor_verdict` trace to DR-005 / GATE-EXT-4 / the S5 proof surface; the `DCP_PROOF_POINTER` repo-grounded core is observed in the dNh RDCP `PROOF_POINTER.json`. The charge is that §6 **blends repo-grounded + external-derived + synthesis-invented fields into one uniform DECIDED contract with no provenance tag on any field.**
- It is **not** "the pack's own checklist is the right repo-runtime shape." The pack's D12 required-fields list is "checklist #2" (campaign-derived), not a runtime schema. The clean charge is the **unlabeled resolution of a flagged UNKNOWN via external authority**, not "the external shape is wrong."
- Lens B's narrow point is **correct and credited**: these are greenfield DCP-owned *output* artifacts of which the synthesis is the canonical writer, so seeding a new schema from an external design template makes **no false claim about repo state** — it is not fact-laundering in the narrow sense. B's error is treating that as sufficient for non-blocking: it does not touch the *durability* mechanism (external DR acquiring repo rank at the lock), which is the actual gating hazard. Hence blocker, fixed by provenance-labeling (Must-Fix #1/#2), not by deletion.

**L-03 (DR-011 → architecture floor): CHECKED — CLEAN, not a laundering finding.** All three lenses agree DR-011 was correctly demoted: it does not appear in the executive decision, the D1 row, or §3; it appears only in §11 as "DR-011 advisory, never authority." The "architecture steer" connotation the ledger warned about is stripped; the D1 model is owned on OBSERVED basis. Treating this DR citation as laundering would decalibrate the audit. Residual (MINOR, not a defect): the *pack's* §14 D1 source column still reads "DR-011 (DCP≈Backstage+OPA+verifier+broker)" — but that is the input pack, not the decision artifact.

**§6 field-list congruence (mitigating, repo-grounded):** the EVIDENCE_HIT discipline (`authority_tier ⊥ confidence`, `derived`, `canonical_writer`, SHA-derived `freshness_state`) has repo grounding via MEMCTX-0001 (pack §2.2/§6), which outranks and corroborates DR-014/DR-016. So the external field-list is *congruent* with repo-runtime principles, not a foreign authority model — which is exactly why the verdict is REVISE (label it), not KILL.

---

## 5. Residual UNKNOWNs — triaged

| UNKNOWN | Collapsible now (read-only)? | Needs runtime/admin? | Handling |
|---|---|---|---|
| L-01 advisory PR-Steward surface in main | **RESOLVED** (ground-truth) | — | IN origin/main; CLI bits (#770) stay CLAIMED_ONLY. Do not reopen. |
| L-09 `execute=True` merge seam | **RESOLVED** (ground-truth) | — | Seam in main, guard absent → synthesis VINDICATED. Restate as universal build-time invariant (§6). Do not reopen. |
| K-27 dNh proof version (1.2 vs v1) | **RESOLVED** (ground-truth) | — | `.v0` DCP naming sidesteps both. Do not reopen. |
| L-02 ConPort/dope-memory endpoints CONFLICTING (K-30/31) | No | Runtime probe needed | §11 "provisional, no binding v1" — correct; do not bind in v1. |
| L-07 BOUNDARY memo rank; K-05 S3→S1 compose coupling | **Partially** (read compose/server.py) | Runtime verify coupling | Read-only inspection of `server.py` + compose can collapse K-05; canonical root (K-02/03) needs runtime. Block jpicklyk projection until then. |
| L-12 canonical TO root + resource maps absent | **Partially** (repo path inventory) | — | Resource-map enumeration is read-only-collapsible; projection stays blocked until it exists. |
| D3 `.dopetask/series/` state acquisition | No | Decide strategy | State.json absent today; 3 unresolved acquisition options. Block live Dopetask adapter until decided. |
| LIVE_WRITE_READY definition (K-46) | No | Design + admin | Kept default-deny/undefined+blocking. Defining it (who/what-proof) is a D8 concern, explicitly out of packet 1. |
| L-13/K-44 Gemini→Antigravity auditor cutover (2026-06-18) | No | Recheck after date | Today 2026-06-03 → ~15 days pre-cutover; auditor route "AVAILABLE" is time-boxed. §11 "UNKNOWN until rechecked" — recheck after 06-18. |
| L-15/K-38/K-39 web Palette / neon_dashboard scope | No | Operator scope decision | UNKNOWN/OPEN_SCOPE; not in cockpit MVP. Correct. |
| K-26 PAL clink execution | Config AVAILABLE; exec NEEDS_SUPERVISOR | Supervisor | Correctly held: config available, execution needs supervisor. |
| DR-016 repo-local field-vocab (13 UNKNOWNs) | No (the actual gate) | Reconcile vs runtime | The Must-Fix #1 carry-forward; PENDING before any contract leaves `.v0`. |

---

## 6. Top build-time red lines

1. **THE #1 RED LINE — the in-main, ungated `execute=True` merge seam. DCP must NEVER import, call, or wire into it.** Ground-truth confirms `execute_or_dry_run(merge_cmd, execute=True)` at `queue_drain.py:617/2006/2017` is in `origin/main` while its guard (`steward_gate.py`) is absent — an ungated `gh pr merge` capability accepted as authority in main. This is a **hard, universal build-time invariant for TP-DCP-0001 and every later packet**: DCP must never import/call/wire into the `execute=True` seam, never call `scripts/batch_resolve_and_merge.py`, and never adopt `src/dopemux_pr_merge_specialist` — independent of whether the broader PR-merge stack is ever adopted. Elevate this from a quarantine footnote (synthesis §11/L-09) to a **named universal red-lane invariant** so it cannot erode in D9/D10-era packets. For packet 1 specifically this is satisfied (read-only, static fixture, no subprocess) — the action is to *name* it so it stays satisfied.
2. **Never compute live SHAs/hashes against a target-repo tree.** The `DCP_PROOF_POINTER` fields (`source_head_sha`, `source_artifact_sha256`) are exactly what an implementer is tempted to "fill in for real" via `git`/file-hashing. Combined with the C-02 subprocess ambiguity this is a soft live-read path. Fixture SHAs are illustrative placeholders authored from pasted evidence text only; no file-system traversal of the target repo (Must-Fix #5 / C-04).
3. **Never let the contract-locking packet self-certify the role-separation lane it defines.** Auditor ≠ implementer; supervisor sign-off recorded separately (Must-Fix #4 / C-03). The packet that *defines* "self-certifying implementer/auditor/supervisor loop (hard block)" must encode that separation for its own acceptance.
4. **Never bind ConPort/dope-memory/TO endpoints in v1.** Endpoints are CONFLICTING (K-30/31); LIVE_WRITE_READY is undefined+blocking (K-46). No live write until LIVE_WRITE_READY is *defined and proven*.
5. **Never promote corroboration to authority.** External DR (VENDOR_DOCS) corroborating a repo posture is not validation of it; mirrors/proxies/indexes/cache-freshness are never authority. This is the principle the §6 blocker violates and the one the provenance-tag fix restores.

---

## 7. What VALIDATE / the ledger MISSED (from the Lens A cold-read blind pass)

Lens A read only the synthesis + pack (not the contradiction ledger), and the ledger-aware passes (B) under-weighted what A surfaced. Net "missed" items:

1. **The specificity inversion (A-2).** The synthesis is **most-specified exactly where it has an external DR-016 template** (§6 receipts — full field-lists, DECIDED) and **least-specified exactly where repo authority is available and required** (`DCP_MUTATION_CLASS` from `approval_policy.yaml`/`policy.py`, `DCP_APPROVAL_ARTIFACT`, `DCP_PROJECT_RESOURCE_MAP` — Scope IN but shapeless). The ledger's L-rows track laundering risk per-decision but did not name this inversion as a single failure mode. It is the structural signature of the §6 hazard: external template available ⇒ over-specified; repo derivation required ⇒ skipped.
2. **The circular-validation gap in the §10 acceptance gate.** "Static fixture validates" is the *only* acceptance check on the receipt schemas, and a fixture authored to match the external-derived shape validates circularly — provenance is never checked. Neither VALIDATE nor the ledger flagged that the acceptance gate cannot catch the very laundering the ledger worried about. (Drives Must-Fix #2.)
3. **C-02 / C-03 / C-04 — three packet-1 safety defects only the premature-build lens (C) caught, and which the synthesis's own §12 self-audit missed entirely.** The "no subprocess" line forbids the packet's own pytest + git-proof step (verified self-contradictory); §10 has no auditor≠implementer constraint (verified absent); the fixture "from supplied evidence" is one interpretation from live-deriving SHAs. The §12 weak-assumptions list (10 items) contains none of these — it is a *design-quality* self-audit, not a *gate-integrity* one. The gate-integrity defects came only from an adversarial premature-build read.
4. **D3 reads state that does not exist (A-4).** "Read existing bundles" sounds achievable but `.dopetask/series/` state.json is absent today and the acquisition strategy is undefined — a wishful framing the ledger carried as L-12-adjacent but did not pin to D3's specific "read-spine" claim.

---

## 8. Overall

The synthesis is a disciplined decision artifact and is **safe to act on for the first packet once the five must-fixes land** — its read-only/quarantine/contract-lock-first posture is correct, its CLAIMED_ONLY discipline holds everywhere, UNKNOWNs are preserved, and the three ground-truth-resolved items (L-01-advisory, L-09, K-27) each vindicate it. The five highest-risk ledger items (L-01, L-02, L-03, L-04, L-09) are all handled and carried forward in §11. The gate is **GO_WITH_FIXES**, not NO_GO, because every defect is REVISE-class and bounded — no redesign is required. **The single biggest residual risk is the §6 contract floor shipping unlabeled**: if `DCP_EVIDENCE_HIT` / `DCP_CHRONICLE_RECEIPT` / `DCP_HELPER_RECEIPT` + the invented proof-pointer fields lock as flat "DECIDED" with no provenance and no validation-status marker, then at the exact moment this packet is designed to create durability, external DR-016 (VENDOR_DOCS) and synthesis-invention silently acquire repo-runtime authority that every downstream packet inherits — the corroboration→authority promotion the HARD FRAME forbids — and the `.v0` hedge does not catch it because `.v0` is a version marker, not a provenance marker. Provenance-tagging the nine §4 contracts (or deferring the external/invented schemas out of packet 1) collapses that risk to zero while preserving the packet's purpose.

---

### Verdict block
- **gate_verdict**: GO_WITH_FIXES
- **blocker_count**: 1 (§6 unlabeled external-DR/invented contract floor — Must-Fix #1)
- **must_fix_count**: 5 (§2)
- **top_risks**: (1) §6 contract floor ships unlabeled → external DR-016 + synthesis-invention acquire repo authority at the lock (durability hazard, the gating risk); (2) `.v0` hedges version not validation — two hazards, one hedged; (3) §10 "static fixture validates" validates circularly with no provenance check; (4) §10 "no subprocess" forbids the packet's own validation/proof + leaves a self-certification gap (auditor≠implementer absent); (5) build-time: the in-main ungated `execute=True` merge seam must be a named universal invariant DCP never wires into.
