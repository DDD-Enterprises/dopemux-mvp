Independent evidence audit. Starting from git identity and the claimed 4-file delta, then recomputing each evidence claim from bytes.Re-freeze chronology looks suspicious — contracts commit earlier than re-freeze. Digging into git order and MA-08 next.# Independent post-merge ADR acceptance-integrity audit

**Auditor role:** independent, no producer conversation history
**Audited content head:** `1939640e4d94159875543f1e0a22dba65032602f`
**MA08_MAIN_SHA:** `75b4cfc581786a53445e412bfc8e25a6e0fdb978`
**Method:** recompute from checkout bytes only

---

## VERDICT

```text
PASS_ADR_ACCEPTANCE_EVIDENCE_READY_FOR_OPERATOR_REDISPOSITION
```

Evidence set is sufficient and truthful enough for a fresh human ACCEPT / DEFER / REJECT decision on ADR-SB-001..010. No BLOCKER found.

```text
BLOCKERS: 0
MUST_FIX: 1
```

---

## BLOCKERS

None.

---

## MUST_FIX

### MF-1. Hard-gate parenthetical misstates compose service count as `41`

In `02_MA08_DRIFT_RECHECK.md` §11:

```text
fourth canonical DB created?  NO  (…; 41 services at base and at head)
```

**From bytes:**

| Measure | base `72af781e` | head `75b4cfc5` |
|---|---:|---:|
| `services:` blocks | **24** | **24** |
| `volumes:` names | 15 | 16 (`conport_supervision_state` added) |
| `networks:` names | 1 | 1 |
| All 2-space keys | **40** | **41** |

`41` is the sum of network + volume + service *names* at head, not service count. Base total of that sum is **40**, not 41. So both the label (“services”) and the equality claim fail recompute.

**Substantive hard-gate answer still holds:** no new DB service; only named volume `conport_supervision_state` at line 45; service set unchanged (24→24). Defect is a false supporting number, not a wrong gate answer. Does not alone make evidence unfit for disposition.

---

## NONBLOCKING_OBSERVATIONS

1. **Headline `NO_NEW_MATERIAL_DRIFT` vs segment A `MATERIAL_DRIFT_CONTAINED` is honest, not a reclassification dodge.** Standing MA-08 rule separates authority/privacy blockers from contained runtime re-gating. Segment A’s ConPort project wall is re-reviewed and carried forward with an explicit ADR-SB-009 re-gate obligation. Same pattern as prior MA-08 (segment B `NO_NEW_MATERIAL_DRIFT` inside a full window that was `MATERIAL_DRIFT_CONTAINED`). Document states full-window character remains contained material drift in segment A rather than dissolving it.

2. **A31 surface-grounding is substring-based and theoretically defeatable** (e.g. property `only` grounded on incidental word inside ``OpenLoopCandidate.due_at` is advisory display metadata only.`` would pass). **No such invented surface found in the current seven typed artifacts** — every collected assertion maps to a real candidate phrase via clause fragments + normalize. Residual validator hardness gap, not present evidence defect.

3. **`service-capability-receipt.schema.json` property `current`** is a thin one-word extraction from “current service capability receipts.” Traceable, not invented; still a sparse interface if enablement is ever authorized.

4. **FO-01 status `repaired_candidate.sha256` = `946054a4…`** is the FO-01-era candidate, not post-AC#2 `e4b28946…`. Correct as receipt projection; not a claim that AC#2 never happened.

5. **`gates.implementation_planning: AUTHORIZED`** remains on the FO-01 status/receipt. Distinct from `adr_acceptance_authorized: false` and `gates.adr_acceptance: CLOSED`. Not ADR disposition smuggling; operator should still treat planning authorization as a separate plane from ADR acceptance.

6. **Denominator chronology:** original contracts (`2c15d62b`) predated re-freeze (`3e0d8981`); contracts *pinning* the 160-clause inventory were rewritten after (`6e1b4472`). Re-freeze commit itself touches no `schemas/second_brain/` and no validator. Super-set keeps all 97 prior clause IDs and adds 63; sampling shows real candidate decision/consequence content, not easy filler. Defensible census, not contracts-first tailoring of the current binding.

---

## WHAT_I_VERIFIED_FROM_BYTES

### Identity / scope
- `HEAD == 1939640e…`
- Diff `75b4cfc5..1939640e` is **exactly four files** (custody, MA-08, contract-family verification, task packet). No other paths.
- Those four files sit on top of MA08 main; substantive ADR/contract/validator/matrix/FO-01 bytes are main’s.

### §1 Ten ADRs
- All ADR-SB-001..010 present; each `**Status:** PROPOSED`; document `status: CANDIDATE`.
- Token `ACCEPTED` **absent** from candidate.
- Candidate sha256: `e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c` (recomputed).
- AC#2 (all ten ADRs): machine contracts must parse/cover at acceptance; denial fixtures are enablement-time; absence of fixtures ≠ implementation evidence.
- Contract family matches that split: `runtime_claims_permitted: false`, `denial_fixtures: NOT_IMPLEMENTED_IMPLEMENTATION_TIME_GATE` (const-pinned in meta-schema). No contradiction of AC#2 sentences 2–3.

### §2 Denominator
- Inventory sha256: `b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dcd58af7f78a439` (recomputed).
- Const-pinned as `FROZEN_INVENTORY_SHA256` in validator and in both meta-schemas.
- Declared total 160 = actual clause entries (11+14+13+11+14+17+17+36+12+15).
- Re-freeze commit `3e0d8981`: inventory + worksheet + receipt + generators only; **no** `schemas/second_brain/**`, **no** validator.
- All 160 `source_fragments` are exact candidate substrings; none land only in forbidden subsections.
- Sampling (ADR-SB-001 full decision/consequences; ADR-SB-008 PM firewall closed set of 8) matches candidate text.

### §3 Typed contracts
- 20 artifacts under `schemas/second_brain/contracts/**`.
- Validator: **94 checks, 0 failed**, exit 0 → `PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE` + `FO01_STALE_RECORD_RECONCILED`.
- Adversarial suite: pytest green (100%).
- Ten ADR contracts pin candidate, ratification (`a23efdc6…`), and inventory hashes.
- Coverage: 160 entries, unique, `COVERED=160`, `MISSING=0`, `AMBIGUOUS=0`, `NOT_APPLICABLE_PROVEN=0`.
- Layer-B surface audit: every assertion_location grounded; no invented property/enum/const in current set that fails A31.
- No runtime/implementation/enablement truthy claims in contracts.

### §4 FO-01
- Receipt sha256: `d2325fa27a6541fa9b1cbce3032c7f2af31f7a448e81eb80e3b69e57a58705cd` (recomputed).
- Status is receipt projection (validator B02/B11 pass; common authority fields match).
- `adr_acceptance_gate_eligible: true` **and** `adr_acceptance_authorized: false` (both surfaces).
- `gates.adr_acceptance: CLOSED`; `other_adr_acceptance_conditions: STILL_REQUIRED`.

### §5 Traceability
- Contract `sb_dec_references` == matrix `recommended_corrected_decision_ids` for all ten ADRs.
- Live candidate parse: **28** references, **26** distinct (SB-DEC-006 and SB-DEC-019 double-cited).
- SB-DEC-026 in `unlinked_decisions` with intentional unlink; **not** in any contract `sb_dec_references`.
- Operator posture `A_LEAVE_UNLINKED` recorded in AC#2 amendment metadata.

### §6 MA-08 (hardest pass)
Recomputed window base `72af781e` → `75b4cfc5`:

| Claim | Document | Recomputed |
|---|---:|---:|
| Commits | 94 | 94 |
| Files | 823 | 823 |
| +ins / −del | 144356 / 2636 | match |
| Seg A commits | 22 | 22 |
| Seg B commits | 5 | 5 |
| Seg C commits | 67 | 67 |
| 22+5+67 | 94 | 94 |
| Seg C files | 239 | 239 |
| Seg C +ins/−del | 37015 / 1210 | match |

- Segment C class table sums to **239** (deps=12 when `package.json` + `ui-dashboard/package.json` counted with lockfiles).
- Prior MA-08 (on `tp/DMX-SB-ADR-ACCEPTANCE-001`) could truthfully write segment-B zeros for runtime and schema/contract; segment C cannot (4 runtime + 21 schema files) — enumerations complete and correct.
- `compose.yml`: adds volume `conport_supervision_state`, **zero** new services, **zero** new DB services.
- `task-promotion-request` / `TaskPromotionRequest` / `task_promotion`: **no hits** under `src/` or `services/`.
- Authority tree byte-identical across segment C; candidate/FO-01 status changes accounted for.

### §7 Custody / disposition provenance
- All 13 listed custody sha256 values recomputed — **all match**, including contracts aggregate `b2bfcf6f…`.
- Controlling prior disposition: blanket DEFER via supersession lineage + conflict notice Option 1; not a per-ADR DEFER ledger on main.
- `19fa74faa9` exists in this object DB on local branch `tp/DMX-SB-ADR-ACCEPTANCE-001` only; **not** ancestor of main; ledger shows 10× ACCEPT; packet correctly classifies as superseded / not inherited.
- Added four files: **no** ADR disposition recorded; no smuggling of ACCEPT election into disposition fields.
- No `docs/90-adr/adr-sb-*` on main.

---

## WHAT_I_COULD_NOT_VERIFY

1. **Operator conversation that uttered the blanket DEFER** — only repository records (supersession lineage, conflict notice). Those records are on main and consistent; the live utterance is outside this checkout.
2. **That `origin/main` still equals `75b4cfc5` on the remote right now** — custody pins that SHA; this audit is bound to the pin, not a live remote re-fetch at report time.
3. **Runtime behaviour of any system** — correctly out of scope. Nothing here was treated as implementation evidence.
4. **Whether A31 would catch a future invented property built from incidental fragment substrings** — demonstrated as a theoretical gap; not observed in present artifacts.
5. **Worksheet step 04 / operator redisposition** — not present in the four-file delta (by design; awaiting operator).

---

**Bottom line:** Evidence is ready for operator redisposition. Fix the compose service-count parenthetical before treating MA-08 prose as byte-perfect, but do not block the phase on it.
