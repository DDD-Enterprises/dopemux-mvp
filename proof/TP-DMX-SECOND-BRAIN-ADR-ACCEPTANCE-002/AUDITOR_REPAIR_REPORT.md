# Independent post-merge ADR acceptance-integrity audit — round 2

**Auditor role:** independent; no producer conversation history; round-1 report treated as prior claims to recheck, not as fact
**Audited content head:** `f7326b18397a4381df88ec4dc933eeb3f0011288`
**Round-1 head:** `1939640e4d94159875543f1e0a22dba65032602f`
**MA08_MAIN_SHA:** `75b4cfc581786a53445e412bfc8e25a6e0fdb978`
**Method:** recompute from checkout bytes only; do not inherit round-1 conclusions

---

## VERDICT

```text
PASS_ADR_ACCEPTANCE_EVIDENCE_READY_FOR_OPERATOR_REDISPOSITION
```

Evidence set remains sufficient and truthful enough for a fresh human ACCEPT / DEFER / REJECT decision on ADR-SB-001..010. Round-1 MF-1 is correctly repaired. No new blockers. No remaining must-fix of the MF-1 class.

```text
BLOCKERS: 0
MUST_FIX: 0
```

---

## BLOCKERS

None.

---

## MUST_FIX

None.

### Round-1 MF-1 disposition (recomputed)

Round 1 reported MF-1: §11 hard-gate parenthetical claimed `41 services at base and at head`. That number was the sum of two-space keys across `services:` + `volumes:` + `networks:`, mislabelled as services, and not equal at both ends (40 at base, 41 at head).

**Repair at `AUDITED_CONTENT_HEAD` is honest:**

1. Live hard-gate row now reads:
   `services:` 24 at base and 24 at head; addition is named VOLUME; `volumes:` 15 → 16.
2. New subsection **"Repair after independent audit round 1 (MF-1)"** quotes the defective original line, states both defects plainly (mislabel + false equality), and tables the per-section recount.
3. Gate answer unchanged and still correct: no fourth DB service; only `conport_supervision_state` volume.

**Independent recompute from `compose.yml` at both ends of the MA-08 window**
(`72af781e42e0702d9047946e0f5a250e7dff0fa5` → `75b4cfc581786a53445e412bfc8e25a6e0fdb978`):

| Measure | base | head |
|---|---:|---:|
| `services:` entries | **24** | **24** (identical name set) |
| `volumes:` names | **15** | **16** (`+ conport_supervision_state`) |
| `networks:` names | **1** | **1** |
| sum of those 2-space keys | **40** | **41** |

Volume name is at line 45 under `volumes:`; mount is `conport_supervision_state:/var/lib/conport-supervision` (supervision state, not a database). Service set unchanged; no new postgres/mysql/etc. service. Repair matches bytes and does not quietly re-word the defect.

**Repair-round scope:**
`git diff --name-only 1939640e..f7326b18` is entirely under `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/` (8 paths). No file outside that directory changed. Not a repair-scope blocker.

**Sibling-number scan** of the same document for the same defect class (mislabelled count or false both-ends equality): no second instance of that class found. Window/segment counts, class-table total 239, segment-C zeros, and the repaired compose counts recompute clean. One overbroad parenthetical is noted under NONBLOCKING_OBSERVATIONS, not a false integer equality of the MF-1 type.

---

## NONBLOCKING_OBSERVATIONS

1. **Headline `NO_NEW_MATERIAL_DRIFT` vs segment A `MATERIAL_DRIFT_CONTAINED` is honest** (agree with round 1 after recompute). Standing MA-08 rule separates authority/privacy blockers from contained runtime re-gating. Segment A’s ConPort project wall is re-reviewed, re-verified from compose bytes, and carried with ADR-SB-009 re-gate adjacency. Full-window character remains contained material drift in segment A; it is not dissolved by the headline.

2. **A31 surface-grounding remains substring-based and theoretically defeatable** (same residual hardness gap as round 1). Validator A31/A32 pass on current artifacts. No invented property/enum/const found in the seven typed artifacts that fails present grounding. Example sparse but traceable surface: `service-capability-receipt` property `current`.

3. **FO-01 status `repaired_candidate.sha256` = `946054a4…`** is FO-01-era candidate, not post-AC#2 `e4b28946…`. Correct as receipt projection.

4. **`gates.implementation_planning: AUTHORIZED`** remains on FO-01 status/receipt. Distinct from `adr_acceptance_authorized: false` and `gates.adr_acceptance: CLOSED`. Not ADR disposition smuggling.

5. **Denominator chronology** (recomputed from git, not receipt prose): original contracts commit `2c15d62b` (2026-08-12 02:06) precedes re-freeze `3e0d8981` (05:57); contracts pinning the 160-clause inventory rewritten after at `6e1b4472` (06:26). Re-freeze commit touches inventory/worksheet/receipt/generators only — **no** `schemas/second_brain/**`, **no** validator. Super-set: 97 prior clause IDs retained (`removed_clause_ids: []`), 63 added. Sampling of ADR-SB-008 PM-firewall clauses and full-inventory `source_fragments` (0 non-substrings of candidate) supports a defensible census, not contracts-first tailoring of the current binding.

6. **Hard-gate parenthetical** `domain/classification model changed? NO (zero classification/privacy policy paths in the window)` is **overbroad** if read as a path-name grep: the full window includes e.g. `config/ai/model-routing.policy.yaml`, `config/pr_steward/policy.json`, and proof paths with `classification`/`policy` in the name. The document’s own segment-A table already classifies model-routing as NON-MATERIAL and the next hard-gate row acknowledges the routing change. Substantive domain/classification *model* answer still holds; this is not a false “41 services” integer equality. Not elevated to MUST_FIX.

7. **Session evidence for round 1:** `r1-019ffd2a-summary.json` has `current_model_id: grok-4.5` and `head_commit: 1939640e…` (round-1 head) — matches packet claims. Signals file also lists `modelsUsed: [grok-4.6, grok-4.5]` / `primaryModelId: grok-4.6` (runner telemetry). Custody-relevant fields on the summary object agree with the packet.

8. **`C1_CONTENT_HEAD.txt` at this head still names `1939640e…`.** Expected: prompt states C1 and this prompt are recorded in the *next* proof-only commit with this report.

---

## WHAT_I_VERIFIED_FROM_BYTES

### Identity / scope
- `HEAD == f7326b18397a4381df88ec4dc933eeb3f0011288`
- `75b4cfc5` is ancestor of audited head; commits on top of MA08 main: 2
- Diff `75b4cfc5..f7326b18`: **exactly 11 paths** — all under this packet’s proof directory plus `task-packets/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002.json`. Matches expected list. Substantive ADR/contract/validator/matrix/FO-01 bytes are main’s.
- Diff `1939640e..f7326b18` (repair round): **only** under `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/` (02 + audit custody artifacts). No out-of-scope change.

### §1 Ten ADRs
- All ADR-SB-001..010 present; each `**Status:** PROPOSED`; document `status: CANDIDATE`.
- Token `ACCEPTED` **absent** from candidate.
- Candidate sha256 recomputed: `e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c`.
- AC#2 (all ten): machine contracts parse/cover at acceptance; denial fixtures are enablement-time; absence ≠ implementation evidence.
- Contract family matches: `runtime_claims_permitted: false` (const in meta-schema); `denial_fixtures: NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE` (const). No contradiction of AC#2 sentences 2–3.
- Line count 375 → 375 across AC#2 (12 lines replaced each way).

### §2 Denominator
- Inventory sha256 recomputed: `b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dcd58af7f78a439`.
- Const-pinned as `FROZEN_INVENTORY_SHA256` in validator and both meta-schemas; also on all ten ADR contracts + coverage index + port contracts.
- Declared total 160 = actual entries (11+14+13+11+14+17+17+36+12+15).
- Re-freeze `3e0d8981`: no `schemas/second_brain/**`, no validator (file list verified).
- All 160 `source_fragments` are exact candidate substrings (recomputed).

### §3 Typed contracts
- 20 artifacts under `schemas/second_brain/contracts/**`.
- Validator: **94 checks, 0 failed**, exit 0 → `PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE` + `FO01_STALE_RECORD_RECONCILED`.
- Adversarial suite: **63 passed**, 0 failed.
- Ten ADR contracts + two port contracts pin candidate, ratification (`a23efdc6…`), inventory hashes.
- Coverage: 160 entries, `COVERED=160`, `MISSING=0`, `AMBIGUOUS=0`, `NOT_APPLICABLE_PROVEN=0`.
- Layer-B: no invented surface found that present A31 fails to catch. Ports `implementation_status: NOT_IMPLEMENTED`.
- No truthy runtime/implementation/enablement claims in contracts.

### §4 FO-01
- Receipt sha256 recomputed: `d2325fa27a6541fa9b1cbce3032c7f2af31f7a448e81eb80e3b69e57a58705cd`.
- Status sha256: `bc2decd1eec9660c9889059cacf41e6ca3333f5cb809516dcb5b0b38e6c99687`.
- Status is receipt projection (validator B02/B11 pass).
- `adr_acceptance_gate_eligible: true` **and** `adr_acceptance_authorized: false` (both surfaces).
- `gates.adr_acceptance: CLOSED`.

### §5 Traceability
- Contract `sb_dec_references` == matrix `recommended_corrected_decision_ids` for all ten ADRs (exact list equality recomputed).
- Live candidate parse: **28** references, **26** distinct (SB-DEC-006 and SB-DEC-019 double-cited).
- SB-DEC-026 in `unlinked_decisions`; **not** in any contract `sb_dec_references`.
- Operator posture `A_LEAVE_UNLINKED` recorded in `ac2-acceptance-condition-amendment.json` / `ADR_CANDIDATE_AMENDMENT_HEAD.json`.

### §6 MA-08 (hardest pass; includes MF-1 recheck)
Recomputed window base `72af781e` → `75b4cfc5`:

| Claim | Document | Recomputed |
|---|---:|---:|
| Commits | 94 | 94 |
| Files | 823 | 823 |
| +ins / −del | 144356 / 2636 | match |
| Seg A / B / C commits | 22 / 5 / 67 | 22 / 5 / 67 (sum 94) |
| Seg C files | 239 | 239 |
| Seg C +ins/−del | 37015 / 1210 | match |

- Segment C class table sums to **239**.
- Prior MA-08 (branch `tp/DMX-SB-ADR-ACCEPTANCE-001`) could truthfully write segment-B zeros for runtime and schema/contract; segment C cannot (4 runtime + 21 schema) — enumerations complete and match `git diff --name-only`.
- Segment C: compose / model-routing / docs/90-adr / authority-map / privacy-classification path hits = 0 as claimed for that segment.
- `task-promotion-request` / `TaskPromotionRequest` / `task_promotion`: **no hits** under `src/` or `services/`.
- Authority tree: zero files in segment C; binding/ledger/matrix content-identical to prior MA-08 end `cfa4927a` (custody SHAs hold).
- MF-1 compose recount: see MUST_FIX section (repaired; verified).

### §7 Custody / disposition provenance
- All 13 listed custody sha256 values recomputed — **all match**, including contracts aggregate `b2bfcf6f…` and 20-file count.
- Controlling prior disposition: blanket DEFER via supersession lineage + conflict notice Option 1 (on main); not a per-ADR DEFER ledger on main.
- `19fa74faa9` exists on local branch `tp/DMX-SB-ADR-ACCEPTANCE-001` only; **not** ancestor of main; ledger shows 10× `operator_disposition: ACCEPT`; packet correctly classifies as superseded / not inherited.
- Added packet files: **no** ADR disposition recorded (`operator_disposition: ACCEPT` absent); no smuggling of ACCEPT election into disposition fields.
- No `docs/90-adr/adr-sb-*` on main.

### Agreement with round 1
Where round 1 claimed PASS on §§1–5, §6 (except MF-1), and §7: **recomputed and agree**. MF-1 defect confirmed as described; repair confirmed correct. No new blocker introduced by the repair commit.

---

## WHAT_I_COULD_NOT_VERIFY

1. **Operator conversation that uttered the blanket DEFER** — only repository records (supersession lineage, conflict notice). Those records are on main and consistent; the live utterance is outside this checkout.
2. **That `origin/main` still equals `75b4cfc5` on the remote right now** — custody pins that SHA; this audit is bound to the pin, not a live remote re-fetch at report time.
3. **Runtime behaviour of any system** — correctly out of scope. Nothing here was treated as implementation evidence.
4. **Whether A31 would catch a future invented property built from incidental fragment substrings** — residual theoretical gap; not observed in present artifacts.
5. **Worksheet step 04 / operator redisposition** — not present in the packet delta (by design; awaiting operator).

---

**Bottom line:** Round-1 must-fix is repaired honestly and recomputes. Evidence remains ready for operator redisposition. Gate string clears with `MUST_FIX: 0`.
