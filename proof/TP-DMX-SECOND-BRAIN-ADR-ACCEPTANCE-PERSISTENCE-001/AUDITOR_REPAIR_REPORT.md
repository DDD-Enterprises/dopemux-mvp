Independent repair-round audit. Working from bytes only — rechecking round-1 findings, not treating them as fact.Checkout at audited head. Running scope diffs, loading staleness artifacts, and reading fo-01 status.Repair scope clean. Next: attack the generator, re-derive staleness independently, and re-run the full R1 checklist.Validator still running. Attacking the generator and rechecking the rest of the R1 surface.Continuing generator regeneration, worksheet provenance, validator guards, and slug checks.Independent re-derivation complete. Assembling the final audit report.# Independent audit — ADR acceptance persistence (repair round)

**Audited content head:** `0defe1cab46a9e6d02e88d3aa94a9edf195b4b84`
**Round-1 head:** `5f9f38acd465ea9a30df0a6251b6e4960704f5cc`
**MA08 main:** `75b4cfc581786a53445e412bfc8e25a6e0fdb978`
**Checkout HEAD matches audited head:** yes (detached)

Round-1 report treated as prior claims only; every material claim rechecked from bytes.

---

## VERDICT

```text
PASS_ADR_ACCEPTANCE_PERSISTENCE_FAITHFUL_AND_ADDITIVE
```

```text
BLOCKERS: 0
MUST_FIX: 0
```

Repair of MF-1 is correct, complete, and non-widening. Independent re-derivation of the staleness set matches the declared seven. No eighth stale leaf found. Full R1 checklist still holds.

---

## BLOCKERS

None.

| Class | Result |
|---|---|
| Pre-amendment AC#2 in accepted ADRs | Absent in all 10 |
| Write to declared read-only surface | Zero (incl. `fo-01-repair-status.json` blob-identical to MA08) |
| Repair-round path outside persistence proof | Zero |
| Weakened/removed validator guard | Validator byte-identical to main; A34–A37, B05–B07 present and asserting |
| Implementation / runtime / enablement claim | Not found as positive claims |
| Disposition not operator-traceable | Ledger + worksheet separate fields; operator election recorded |
| Decision text not candidate byte-slice | All 10 carried bodies are candidate substrings (independent recompute) |
| Uncovered changed path (main..head allowlist union) | 0 / 50 |

---

## MUST_FIX

None.

### MF-1 (round 1) — rechecked closed

Independent walk of all **103** leaves of `fo-01-repair-status.json` (not using the generator’s classifications as authority):

| # | Path | Observed | Independent call |
|---|---|---|---|
| 1 | `/adr_acceptance_authorized` | `false` | **STALE** — operator authorized ACCEPT 2026-08-14 |
| 2 | `/other_adr_acceptance_conditions` | `STILL_REQUIRED` | **STALE** — acceptance persisted; outstanding-conditions claim false as present-tense |
| 3 | `/gates/adr_acceptance` | `CLOSED` | **STALE** — file’s own gloss ties CLOSED to outstanding conditions |
| 4 | `/adr_statuses/promoted_to_accepted` | `0` | **STALE** — ten accepted records under `docs/90-adr/` |
| 5 | `/stale_record_reconciliation/still_forbidden/[0]` | `"ADR acceptance"` | **STALE** — acceptance no longer forbidden |
| 6 | `/gate_field_semantics/gates.adr_acceptance` | prose | **STALE** — see prose judgment below |
| 7 | `/gate_field_semantics/adr_acceptance_authorized` | prose | **STALE** — see prose judgment below |

**No eighth.** Extra-suspect heuristic over all leaves returned empty beyond these.
`/adr_statuses/all_remain = "PROPOSED (candidate)"` remains **NOT_STALE** when read with its parenthetical scope (candidate untouched); correctly recorded as `not_stale_but_arguable`, not quietly dropped.

Declared set in `FO01_STALENESS_DECLARATION.json` / binding pin matches this set (path notation `/[0]` vs `/0` is indexing style only).

---

## NONBLOCKING_OBSERVATIONS

1. **Rules enforce coverage, not judgment correctness.** Both generator rules fail closed on missing classification and on acceptance-touching category defaults. A wrong `EXPLICIT` verdict (`NOT_STALE` on a truly stale leaf) would still pass both rules. Residual structural risk; not realized on current leaves (manual judgment agrees with all seven).

2. **Constructed slip class (not present today):** a future leaf under a broad category prefix (e.g. `/authority/…`) whose path and string value contain no acceptance token could be category-defaulted `NOT_STALE` while actually stale. Rule 2’s token is necessary but not semantic. Current 103 leaves: no such slip found.

3. **Token miss on `all_remain`:** path/value do not match `ACCEPTANCE_TOKEN`; protection is via explicit entry, not rule 2. Honest.

4. **Title level:** accepted records use `# ADR-SB-NNN` (H1); candidate uses `##`. Identifiers and contracts still match. Not a defect.

5. **`C1_CONTENT_HEAD.txt` names R1 head** `5f9f38ac…` — expected for freeze/prompt lifecycle; not a finding.

6. **Worksheet custody (unchanged bound):** first committed at `fa48fcd201`; never covered by Phase B audit head `f7326b1839`. This remains first independent look at worksheet evidence/recommendations. Quantitative spot-check matched contracts.

---

## WHAT_I_VERIFIED_FROM_BYTES

### Repair scope (this round’s hard attack surface)

```text
git diff --name-only 5f9f38ac..0defe1cab4
→ 10 paths, ALL under proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-PERSISTENCE-001/
→ outside that prefix: []
→ docs/90-adr unchanged in repair round
→ fo-01-repair-status.json blob 62c462db… identical main ↔ HEAD
```

### Full scope main..head

```text
50 paths; allowlist union (PERSISTENCE-001 + ACCEPTANCE-002) → uncovered = 0
All declared read-only surfaces: CLEAN
```

### Generator rules

- Re-ran `gen_staleness_declaration.py`: exit 0; output **byte-identical** to committed declaration; `stale_count=7`.
- Attack rule 1 (drop `/schema_version` category): exits with unclassified `['/schema_version']`.
- Attack rule 2 (remove EXPLICIT for `still_forbidden/[0]`): exits with acceptance-defaulted that path.
- Binding pin `authoritative_record_sha256` = `495eb5096a3653…` matches declaration bytes.

### Prose glosses — honest stale, not over-correction

**`/gate_field_semantics/gates.adr_acceptance`:**
> “Unchanged and still CLOSED. The overall ADR-acceptance gate remains shut **because** the other acceptance conditions … **are still outstanding**.”

Present-tense causal claim is false after operator ACCEPT + persistence. Classifying as STALE is required honesty, not padding. (R1 observation that these were “only glosses of already-declared fields” understated completeness: they are separate leaves making checkable claims.)

**`/gate_field_semantics/adr_acceptance_authorized`:**
> “Unchanged and **still false**. Only the human operator may authorize ADR acceptance.”

Second sentence remains true; first is false. Mixed prose with a falsified half is still STALE as a present-tense status gloss.

### Validator

```text
PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
checks_total: 94  checks_failed: 0
pytest: 63/63 passed
validator vs MA08_MAIN_SHA: BYTE_IDENTICAL
```

Guards still assert:

- **A34** — contracts `adr_status_at_contract_authoring == PROPOSED`
- **A35** — candidate contains `\nstatus: CANDIDATE\n`
- **A36** — no forbidden value tokens (incl. ACCEPTED) in **contract** docs
- **A37** — no truthy runtime/implementation authority keys in contracts
- **B05** — `adr_acceptance_authorized` false on status **and** FO01 receipt; receipt `accepts_any_adr` false
- **B06** — FO-01 CLOSED, eligibility true, `gates.adr_acceptance` CLOSED
- **B07** — merge NOT_AUTHORIZED on status and receipt

Passes because persistence is additive outside the validator’s read surface — not because guards were weakened. B05/B06 still pin pre-acceptance fo-01; that is why stale fields cannot be edited away here.

### Accepted records / candidate

- Candidate sha256 `e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c`; still `status: CANDIDATE`
- Amended AC#2 present 10× in candidate and each accepted ADR
- Pre-amendment string **nowhere** in the 10 accepted files
- `gen_accepted_adrs.py` re-run: **byte-identical** regeneration of all 10
- Independent: each carried body (post-`**Status:** PROPOSED` slice) is substring of candidate **and** of accepted file
- Contracts `schemas/second_brain/contracts/ADR-SB-00N.contract.json` match
- Slug rule `re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")` uniform; 009 keeps full `…-identity-dependencies` (not superseded hand-shortening)
- Each record: acceptance confers **no** implementation/runtime/production/enablement authority; gates NOT_IMPLEMENTED / NOT_RUN / ABSENT

### Authority non-inflation

- Binding: `confers: []`; implementation/runtime/slice_0 NOT_AUTHORIZED; denial_fixtures NOT_IMPLEMENTED
- Receipt: explicit non-authorizations for implementation, Slice 0, runtime, denial fixtures, benchmarks/purge/isolation/split-brain, encryption, push/PR/merge; `merge_authorized: false`
- Search of added surfaces: no positive claim that those gates ran or exist (only NOT_* / ABSENT / “does not authorize”)

### Disposition provenance

- Ledger: 10× `operator_disposition: ACCEPT`; `facilitator_authored_dispositions: false`; `inherited_from_superseded_attempt: false`; recommendations in separate `facilitator_recommendation` field
- Worksheet vs `fa48fcd201`: `FACILITATOR_RECOMMENDATION` values unchanged (10× RECOMMEND_ACCEPT); dispositions PENDING_OPERATOR → ACCEPT only; plus allowed header / summary disposition cells / terminal-state block
- Per-ADR evidence/reasoning otherwise stable
- Clause counts vs contracts: 11/14/13/11/14/17/17/36/12/15 = **160**; typed `required_artifacts`: 0/0/0/0/0/2/0/3/2/0 = **7** (006/008/009 = 2/3/2)

### R2 correction

- `R2_AUDITOR_IDENTITY_REASONING_CORRECTION.json`: new vs main
- `R2_AUDITOR_IDENTITY_RECONCILIATION.json`: byte-identical to main
- `identity_conclusion_changed: false`; conclusion remains `grok-4.5`

---

## WHAT_I_COULD_NOT_VERIFY

1. **Live human operator intent** beyond ledger/worksheet bytes (verbatim election + reasoning).
2. **Provider-side cryptographic attestation** of prior auditor model (`UNKNOWN` in correction record).
3. **Full qualitative re-audit of every worksheet prose sentence** beyond quantitative clause/artifact spot-checks — outside persistence faithfulness; worksheet never Phase-B-audited.
4. **Live re-fetch of `origin/main`** — compared to given `MA08_MAIN_SHA` pin only.
5. **Future fo-01 reconciliation packet** — declared required and not authorized; not verified beyond that.

---

## Summary integers

```text
BLOCKERS: 0
MUST_FIX: 0
```

**Clearance:** granted for this content head. Persistence remains faithful, additive, and non-inflationary; MF-1 repair is complete (seven-field derived declaration, generator fail-closed on the two stated rules, no scope widening, fo-01 still unmodified).
