# 01_INPUT_CUSTODY — TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-002

```text
PROGRAM = SECOND_BRAIN
PHASE   = POST_MERGE_ACCEPTANCE_READINESS
```

This packet is read-only with respect to Second Brain architecture and runtime. It
records no ADR disposition, accepts no ADR, and authorizes no implementation.

## Base resolution — resolved at execution time, not assumed

```text
git fetch origin --prune          executed this run
origin/main resolved to:          75b4cfc581786a53445e412bfc8e25a6e0fdb978
operator-stated merge commit:      75b4cfc581786a53445e412bfc8e25a6e0fdb978
match:                            YES

MA08_MAIN_SHA = 75b4cfc581786a53445e412bfc8e25a6e0fdb978
```

`MA08_MAIN_SHA` is the pinned governing SHA for this entire phase. Every downstream
artifact — the drift recheck, the contract-family verification, the independent audit,
and the worksheet — is bound to it. Concurrent sessions are demonstrably active in this
repository (see the provenance note below), so if `origin/main` has advanced by the time
this packet is read, the pin governs and the delta is the operator's call, not a reason
to silently re-run against a moving head.

```text
verification worktree:  detached, created fresh at 75b4cfc581 from the object store
branch for artifacts:   tp/DMX-SB-ADR-ACCEPTANCE-002  (cut from 75b4cfc581)
worktree status at creation: clean (0 entries)
pushed: NO      PR: NONE      merge: NOT_AUTHORIZED
```

## Why this is a new packet directory

`proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001/` is a prior run's bundle, bound to head
`cfa4927a88`, and its `06_ADR_OPERATOR_DECISION_LEDGER.yaml` is a controlling historical
record of a superseded attempt. Writing into that directory would edit controlling
evidence. This phase therefore mirrors its file shape in a fresh directory and inherits
nothing from it by reference.

## Prior operator dispositions — the exact controlling record

The operator's Phase B block states `PRIOR_OPERATOR_DISPOSITIONS = 10x DEFER`. The
repository record behind that is more specific than a per-ADR ledger, and the difference
matters for the worksheet:

```text
There is NO per-ADR ledger on main recording ten individual DEFER dispositions.
The DEFER is a single blanket operator directive covering ADR-SB-001..010.
```

Established from records that are on `main` at `MA08_MAIN_SHA`:

| Record | Path | What it establishes |
|---|---|---|
| Supersession lineage | `proof/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-AC2-AMENDMENT/SUPERSESSION_LINEAGE.md` | Operator directed, later in time, "DEFER ADR DISPOSITIONS PENDING AC#2 CLARIFICATION"; the later directive controls |
| Conflict notice | `…/CONFLICT_NOTICE_CONCURRENT_ACCEPTANCE.md` | Operator selected Option 1, honour the later DEFER |
| AC#2 amendment receipt | `docs/…/adr-candidates/ac2-acceptance-condition-amendment.json` | `adr_dispositions_recorded: false`, `adr_acceptance_authorized: false` |
| Candidate document | `docs/…/adr-candidates/second-brain-adr-candidates.md` | `status: CANDIDATE`; all ten ADRs `PROPOSED` (observed count 10) |
| Accepted ADR files | `docs/90-adr/adr-sb-*.md` | ABSENT on main (observed: no such files) |

A **separate**, earlier ledger recording `10x ACCEPT` exists at commit `19fa74faa9` on the
unpushed local branch `tp/DMX-SB-ADR-ACCEPTANCE-001`. It is classified
`SUPERSEDED_PRE_AMENDMENT_ACCEPTANCE_ATTEMPT` with `operator_provenance: UNKNOWN`, is
not on `main`, and is **not** the prior disposition state. It is named here only so a
reader who finds it does not mistake it for the controlling record. Nothing in this
packet touches that branch or its worktree.

The supersession lineage also states the replacement chain that must follow, and this
phase is steps 2 and 5 of it:

```text
1. AC#2 amendment merges to main                        DONE (#1214, dc279256fe, on main)
2. fresh MA-08 against the resulting merged-main SHA     THIS PACKET, 02_MA08_DRIFT_RECHECK.md
3. operator supplies FRESH explicit dispositions         AWAITING OPERATOR (worksheet 04 enables it)
4. ledger/binding/ADR files rebuilt                      NOT AUTHORIZED
5. fresh independent acceptance-integrity audit          THIS PACKET, AUDITOR_REPORT.md
6. only that rebuilt chain may become authoritative      NOT REACHED
```

Step 3 is explicit that the earlier ACCEPT dispositions are **not** inherited, copied, or
inferred. The worksheet in this packet accordingly carries recommendations only, with
every disposition field `PENDING_OPERATOR`.

## Source custody at `MA08_MAIN_SHA` (observed SHA-256, computed this run)

```text
1e8f8dcbd52e62b6d29cb5d2655d1793a4bddb0b181fddc82b41a654f147b7f4  docs/03-reference/architecture/second-brain/authority/ARCHITECTURE_AUTHORITY_HEAD.json
a23efdc676c499cc56b76c5fe321acd0bcf60871be18a33c7539e2350ba07b34  docs/03-reference/architecture/second-brain/authority/RATIFICATION_BINDING.json
8e0380eb1d49c10ac7ecca38fdd06e6fe9755bf607f389bdf91479981cb93b93  docs/03-reference/architecture/second-brain/authority/OPERATOR_DECISION_LEDGER.yaml
e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c  docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md
6d106302c3c942dfcc63c73226a1141b2a4ecf028e64aa9f653c25842d741153  docs/03-reference/architecture/second-brain/adr-candidates/ac2-acceptance-condition-amendment.json
468939f6ac256178faea4f4daf6f636ba70926d31aebe79d91846f06cea823b5  docs/03-reference/architecture/second-brain/adr-candidates/ADR_CANDIDATE_AMENDMENT_HEAD.json
7ce481011a2da98d6840d0c300fcd27f1f52e4b0713f4e073d628de00337c9cc  docs/03-reference/architecture/second-brain/adr-candidates/traceability-matrix.json
bc2decd1eec9660c9889059cacf41e6ca3333f5cb809516dcb5b0b38e6c99687  docs/03-reference/architecture/second-brain/adr-candidates/fo-01-repair-status.json
d2325fa27a6541fa9b1cbce3032c7f2af31f7a448e81eb80e3b69e57a58705cd  proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/FO01_RESOLUTION_RECEIPT.json
b164fc0b44597a5805aaa7a3f0c6eee047404121bc13bc7a2dcd58af7f78a439  proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json
8f75a967a1e10fb794817c050f1e8a284c247bf25aeca67e786ef3eec845098c  proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/DENOMINATOR_REFREEZE_RECEIPT.json
58dae6be052d5173732a6abf9ca45a770729ad01c8c28688962e351650c3fbb4  schemas/second_brain/contracts/ADR_CONTRACT_COVERAGE.json
3777d33dc02048ef3587bd0324c7fe7acbba979054f6de2946c5a7ce5f58161e  scripts/governance/validate_second_brain_adr_contracts.py

schemas/second_brain/contracts/   20 files
aggregate sha256 of `shasum -a 256 *` output:
b2bfcf6f92281a2e6fa85f1e5d1429c3f8557ceffc001985d7b7f9208da1f3fa
```

### Custody continuity against the prior run's recorded values

| File | Prior run @ `cfa4927a` | Now @ `75b4cfc5` | Result |
|---|---|---|---|
| `RATIFICATION_BINDING.json` | `a23efdc6…` | `a23efdc6…` | UNCHANGED |
| `OPERATOR_DECISION_LEDGER.yaml` (32 SB-DEC) | `8e0380eb…` | `8e0380eb…` | UNCHANGED |
| `traceability-matrix.json` | `7ce48101…` | `7ce48101…` | UNCHANGED |
| `FO01_RESOLUTION_RECEIPT.json` | `d2325fa2…` | `d2325fa2…` | UNCHANGED |
| `ARCHITECTURE_AUTHORITY_HEAD.json` | `1e8f8dcb…` | `1e8f8dcb…` | UNCHANGED |
| `second-brain-adr-candidates.md` | `946054a4…` | `e4b28946…` | CHANGED — AC#2 amendment (#1214), operator-authorized, independently audited PASS |
| `fo-01-repair-status.json` | `0e0258e0…` | `bc2decd1…` | CHANGED — FO-01 reconciliation (#1227), receipt-projected and validator-checked (group B) |

Two files changed and both changes are accounted for by a merged, operator-authorized,
independently audited PR. The entire `authority/` directory is byte-identical: zero files
under it appear in `git diff cfa4927a..75b4cfc5`.

## Contract-family verification (operator step 1)

Executed from the clean worktree at `MA08_MAIN_SHA`. Full record in
`03_CONTRACT_FAMILY_VERIFICATION.json`; headline:

```text
python3 scripts/governance/validate_second_brain_adr_contracts.py     exit 0
result            PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
ADR coverage      10/10
clause coverage   160/160
MISSING           0
AMBIGUOUS         0
```

## Provenance note carried forward at operator instruction

```text
UNEXPECTED_CONCURRENT_BRANCH_WRITE
IMPACT=PROOF_METADATA_ONLY
FINAL_HEAD_REVALIDATED=true
```

Commit `da2523aafb` was authored and committed under the GitHub account `hu3mann` during
PR #1227's merge window but was **not** made by the operator in the conversation that
drove that merge. Its diff was confined to
`proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/VALIDATION.json`. Because the actual
final head was revalidated before merging — the 36-file audited-byte check and all gates
were re-run at `da2523aafb` itself rather than at the previously pushed head — it does not
reopen #1227. It is recorded here in the Phase B chronology because an unexplained write to
a proof branch is the kind of fact that must survive into the next phase rather than be
noticed once and dropped.

## Verdict

```text
INPUT_CUSTODY: PASS
BLOCKED_ADR_ACCEPTANCE_INPUT_CUSTODY: NOT TRIGGERED
```
