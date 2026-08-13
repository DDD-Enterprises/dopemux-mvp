Independent round-2 acceptance-integrity audit. Starting from bytes at `AUDITED_CONTENT_HEAD`, re-verifying the MF-1 repair and re-running the full round-1 checklist.Diff scope clean: only proof packet paths changed between heads. Recomputing MF-1 repair and full evidence chain from bytes.Compose count script failed on short SHA / structure — recomputing correctly and running the rest of the checklist.MF-1 numbers match. Continuing inventory coverage, FO-01, custody, MA-08 enumerations, and sibling-number scan.Repair verified honest. Writing round-2 report from recomputed evidence.# Round-2 audit complete

**Audited head:** `f7326b18397a4381df88ec4dc933eeb3f0011288`
**Report written:** `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/AUDITOR_REPORT.md`
(R1 report remains in git history at `1939640e…`)

---

## VERDICT

```text
PASS_ADR_ACCEPTANCE_EVIDENCE_READY_FOR_OPERATOR_REDISPOSITION
```

```text
BLOCKERS: 0
MUST_FIX: 0
```

---

## MF-1 repair (attack result)

**Honest repair. Numbers recompute. Defect stated plainly, not re-worded away.**

| Measure | base `72af781e` | head `75b4cfc5` |
|---|---:|---:|
| `services:` | **24** | **24** (same names) |
| `volumes:` | **15** | **16** (`+ conport_supervision_state` @ line 45) |
| `networks:` | **1** | **1** |
| sum of those keys | **40** | **41** ← what original “41 services” measured |

- Live hard-gate row uses 24/24 services + volume 15→16.
- New “Repair after independent audit round 1 (MF-1)” quotes original bad line, names mislabel **and** false equality, tables the recount.
- Gate answer still correct: named volume only; no new DB service; mount `/var/lib/conport-supervision`.
- Repair-round diff is **only** under `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002/` — no out-of-scope change.
- Sibling scan: no second mislabelled/false-equality integer of the MF-1 class.

---

## Full re-run (summary)

| Area | Result |
|---|---|
| Identity: 11 paths on MA08 main only | PASS |
| 10 ADRs PROPOSED / CANDIDATE / no ACCEPTED / sha `e4b28946…` | PASS |
| 160-clause inventory + pin + re-freeze predates contract rewrite | PASS |
| Contracts: validator 94/0, pytest 63/0, coverage 160 COVERED | PASS |
| FO-01: receipt `d2325fa2…`, eligible true, authorized **false** | PASS |
| Traceability maps equal; SB-DEC-026 unlinked; 28/26 refs | PASS |
| MA-08 window 94/823; seg C class sum 239; consumers zero | PASS |
| Custody 13/13 sha match; blanket DEFER; no ACCEPT smuggle | PASS |

Round-1 PASS findings recomputed and **agree**, except MF-1 (now fixed).

**Nonblocking:** A31 theoretically soft; `implementation_planning: AUTHORIZED` ≠ ADR acceptance; hard-gate “zero classification/privacy policy paths” is overbroad path-name wording (substantive answer still holds; not an MF-1-class false integer).

**Could not verify:** live operator DEFER utterance; live remote `origin/main`; any runtime behaviour (correctly out of scope).

---

**Bottom line:** Repair correct. Evidence ready for operator redisposition. Phase gate `MUST_FIX: 0` clears.
