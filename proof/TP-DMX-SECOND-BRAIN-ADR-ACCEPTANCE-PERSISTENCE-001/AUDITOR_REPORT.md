Independent audit of ADR acceptance persistence. Working from checkout bytes only — starting with scope, allowlist, and content-head verification.Content head matches. Gathering allowlist, AC#2 wording, validator state, and key authority files in parallel.Validator still running. Continuing allowlist coverage, generator re-run, and authority-claim checks.Digging into validator guards, fo-01 staleness completeness, worksheet provenance, and authority-inflation searches.Checking PINNED fields and worksheet claim accuracy; verifying whether a fourth stale field was missed.# Independent audit — ADR acceptance persistence

**Audited content head:** `5f9f38acd465ea9a30df0a6251b6e4960704f5cc`
**MA08 main:** `75b4cfc581786a53445e412bfc8e25a6e0fdb978`
**Checkout HEAD matches content head:** yes (detached)

---

## VERDICT

```text
FAIL
```

Does **not** clear:

```text
PASS_ADR_ACCEPTANCE_PERSISTENCE_FAITHFUL_AND_ADDITIVE
```

No blockers that invalidate the acceptance records themselves. One **MUST_FIX**: incomplete staleness declaration presented as complete. Per packet control, remaining MUST_FIX stops clearance.

```text
BLOCKERS: 0
MUST_FIX: 1
```

---

## BLOCKERS

None.

Checked blocker classes and found none:

| Class | Result |
|---|---|
| Pre-amendment AC#2 in accepted ADRs | Absent in all 10 |
| Write to declared read-only surface | Zero |
| Weakened/removed validator guard | Validator byte-identical to main; A34–A37, B05–B07 present |
| Implementation / runtime / enablement claim | Not found as positive claims |
| Disposition not operator-traceable | Ledger + worksheet separate fields; operator election recorded |
| Decision text not candidate byte-slice | All 10 carried bodies are candidate substrings |
| Uncovered changed path | 0 / 42 |

---

## MUST_FIX

### MF-1 — Incomplete staleness declaration (presented as complete)

`ADR_ACCEPTANCE_BINDING.json` asserts this persistence leaves **exactly three** stale fields in `fo-01-repair-status.json`, and names them. That inventory is incomplete.

**Declared stale (verified correct as stale):**

| Field | Value now | Why stale |
|---|---|---|
| `adr_acceptance_authorized` | `false` | Operator authorized acceptance 2026-08-14. Gloss: only human operator may authorize. |
| `gates.adr_acceptance` | `CLOSED` | Acceptance persisted. Binding itself says other conditions “are not” still outstanding. |
| `adr_statuses.promoted_to_accepted` | `0` | Ten accepted records exist under `docs/90-adr/`. |

**Declared not-stale (verified):**

| Field | Value | Why still true |
|---|---|---|
| `adr_statuses.document_status` | `CANDIDATE` | Candidate file untouched; frontmatter still `status: CANDIDATE`. |
| `FO01_RESOLUTION_RECEIPT.accepts_any_adr` | `false` | Receipt unmodified vs main; permanently true of that historical record. |

**Missed stale field (at least one fourth):**

| Field | Value now | Why this persistence makes it stale |
|---|---|---|
| `other_adr_acceptance_conditions` | `STILL_REQUIRED` | Binding’s own reason for stale `gates.adr_acceptance`: other acceptance conditions “were still outstanding. **They are not.**” That directly falsifies `STILL_REQUIRED`. Field is also validator-PINNED to `STILL_REQUIRED` (B03), same “cannot fix without validator change” class as the three named fields. |

**Related miss (same defect class, same declaration):**

| Field | Value now | Why stale |
|---|---|---|
| `stale_record_reconciliation.still_forbidden` | includes `"ADR acceptance"` | After operator ACCEPT + persistence, “ADR acceptance” is not still forbidden. Other entries (implementation execution, runtime enablement, merge) remain correct. |

Incomplete declaration presented as complete is the programme defect class called out in the audit brief. Does not by itself invalidate the ten accepted records; it is still MUST_FIX before authority clearance.

---

## NONBLOCKING_OBSERVATIONS

1. **`adr_statuses.all_remain: "PROPOSED (candidate)"`** — Still true if scoped to the candidate document (parallel to declared-not-stale `document_status`). Easy to misread as “no ADRs accepted in the programme.” Not counted as MUST_FIX given the parenthetical scope, but a later reconciliation packet should make that scope explicit.

2. **`gate_field_semantics` prose** for `adr_acceptance_authorized` and `gates.adr_acceptance` still says “unchanged and still false/CLOSED.” Those are glosses of already-declared-stale fields, not additional undeclared status fields.

3. **Slug rule is uniform.** Superseded attempt used hand-shortened `adr-sb-009-single-project-safety-and-identity.md`; rebuilt chain uses full rule: `…-identity-dependencies.md`. All ten match `re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")`.

4. **Worksheet custody (honest bound on weight):** worksheet absent at Phase B audit head `f7326b1839`; first committed at `fa48fcd201`. This audit is first independent look at worksheet evidence/recommendations. Spot-check of clause counts and required_artifacts **matched contracts** (11/14/13/11/14/17/17/36/12/15 = 160; typed artifacts 0/0/0/0/0/2/0/3/2/0 = 7; “2 / 3 / 2” correct for 006/008/009).

5. **Validator honesty:** passes because persistence is additive and outside the validator’s read surface (contracts + candidate + fo-01 + FO01 receipt + inventory). A36 forbids `ACCEPTED` tokens **inside contract JSON**, not under `docs/90-adr/`. Guards not weakened.

6. **`AUDIT_PROMPT.md` / `C1_CONTENT_HEAD.txt` absent at audited head** — expected; not a finding.

---

## WHAT_I_VERIFIED_FROM_BYTES

### 1. Scope — additive

```text
git diff --name-only 75b4cfc..5f9f38ac → 42 paths
allowlist union (persistence + ACCEPTANCE-002 + depends_on packets) → uncovered = 0
```

Read-only surfaces (candidate, fo-01, traceability matrix, authority/**, FO01 receipt, R2 reconciliation, schemas/contracts/**, validator script): **all clean** (zero diff).

### 2. Validator

```text
validate_second_brain_adr_contracts.py --json
  result: PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
  checks_total: 94  checks_failed: 0

pytest tests/governance/test_second_brain_adr_contracts.py
  63 collected / 63 passed

validator vs MA08_MAIN_SHA: BYTE_IDENTICAL
```

Guards still present and asserting:

- **A34** — contracts `adr_status_at_contract_authoring == PROPOSED`
- **A35** — candidate contains `\nstatus: CANDIDATE\n`
- **A36** — no forbidden value tokens (incl. `ACCEPTED`) in contract docs
- **A37** — no truthy runtime/implementation authority keys in contracts
- **B05** — `adr_acceptance_authorized` false on status **and** receipt; receipt `accepts_any_adr` false
- **B06** — FO-01 gate CLOSED, eligibility true, `gates.adr_acceptance` CLOSED
- **B07** — merge NOT_AUTHORIZED on status and receipt

### 3. Accepted records derive from amended candidate

- Candidate sha256: `e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c` (matches pin)
- Candidate status: still `CANDIDATE` (not promoted)
- Amended AC#2: 10× in candidate; 1× each in all 10 accepted ADRs
- Pre-amendment string `Machine contracts and denial fixtures parse and cover the decision.`: **nowhere** in the 10 accepted files (present in superseded commit `19fa74faa9` sample)
- Generator re-run: **byte-identical** regeneration of all 10 (sha256 match binding pins)
- Independent recomputation: each carried decision body is substring of candidate; each present in accepted file
- Titles `## ADR-SB-001`…`010` and contract paths `schemas/second_brain/contracts/ADR-SB-NNN.contract.json` match
- Each record states acceptance confers **no** implementation/runtime/production/enablement authority; gates remain NOT_IMPLEMENTED / NOT_RUN / ABSENT

### 4. No authority inflation

- Receipt lists explicit non-authorizations: implementation, Slice 0, runtime, denial fixtures, benchmarks, purge, isolation, split-brain, encryption, push/PR/merge
- Binding: `confers: []`, implementation/runtime/slice_0 NOT_AUTHORIZED, denial_fixtures NOT_IMPLEMENTED
- Search of added acceptance surfaces: no positive claim that fixtures/conformance/benchmarks/purge/isolation/split-brain/encryption were run or exist (only explicit NOT_* / ABSENT / “does not authorize”)

### 5. Disposition provenance

Ledger:

- 10× `operator_disposition: ACCEPT`
- `facilitator_authored_dispositions: false`
- `inherited_from_superseded_attempt: false`
- Recommendations in separate `facilitator_recommendation` field

Worksheet vs first commit `fa48fcd201`:

- Diff limited to: header STATUS, new operator-election block, 10 disposition fields, summary disposition cells, “how to read” framing, terminal-state block
- Evidence tables, per-ADR reasoning, FACILITATOR_RECOMMENDATION values: unchanged
- Disposition field never held facilitator recommendation

### 6. R2 correction record

- `R2_AUDITOR_IDENTITY_REASONING_CORRECTION.json`: **new** (absent on MA08 main)
- `R2_AUDITOR_IDENTITY_RECONCILIATION.json`: **byte-identical** to main
- Correction pin matches current recon sha `27c6c14a…`
- `identity_conclusion_changed: false`; original conclusion remains `grok-4.5`

### 7. Binding hash integrity (spot-check)

Ledger / worksheet / acceptance head / generator sha256s match binding pins; receipt’s binding and ledger pins match.

---

## WHAT_I_COULD_NOT_VERIFY

1. **Live human operator intent** beyond bytes in ledger/worksheet (verbatim election block + reasoning). No separate out-of-band operator channel in this checkout.
2. **Provider-side cryptographic attestation** of any prior auditor model (`UNKNOWN` in correction record) — not claimed here; not re-proven.
3. **Whether every worksheet prose claim beyond clause/artifact counts** (e.g. MA-08 narrative, per-ADR qualitative reasoning) is true — spot-checked quantitative claims against contracts; full qualitative re-audit of worksheet prose not in scope of persistence faithfulness, and worksheet was never Phase-B-audited.
4. **Remote `origin/main` live fetch** at audit time — compared to given `MA08_MAIN_SHA` pin and ancestry only; did not re-fetch network remote.
5. **Whether a later packet will reconcile fo-01** — binding says follow-up required and not authorized; not verified beyond that declaration.

---

## Summary integers

```text
BLOCKERS: 0
MUST_FIX: 1
```

**Clearance:** not granted. Fix MF-1 by amending the staleness declaration to name at least `other_adr_acceptance_conditions` (and the still-forbidden “ADR acceptance” entry), without editing the read-only fo-01 file or validator — then re-freeze and re-audit. The ten accepted ADR files, generator provenance, AC#2 amendment fidelity, allowlist scope, and non-inflation posture are sound; the incomplete “complete” staleness inventory is the sole clearance stopper.
