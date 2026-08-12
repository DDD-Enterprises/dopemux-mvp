# COMMAND_LOG — TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001

Packet: `TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001`
Program: `SECOND_BRAIN`
Repository: `DDD-Enterprises/dopemux-mvp`
Mode: `ARCHITECTURE_ACCEPTANCE_EVIDENCE_REPAIR`
Risk lane: `L2`

Every command below was executed. Outputs are transcribed from the real run.

---

## S0 — Fresh identity and drift preflight

```bash
git fetch origin --prune
git rev-parse origin/main
git status --short
git remote get-url origin
```

```text
origin            = https://github.com/DDD-Enterprises/dopemux-mvp.git
EXECUTION_MAIN    = 6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
ISSUE_BASELINE    = 6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
DRIFT             = NONE (EXECUTION_MAIN == ISSUE_BASELINE_MAIN)
```

Delta since the AC#2 merge (`dc279256fedf63c9a799c8eeea249c0a7fd83d14`) is a single
unrelated commit, inspected for Second Brain overlap:

```bash
git log --oneline dc279256fedf63c9a799c8eeea249c0a7fd83d14..6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
git diff --name-only dc279256fedf63c9a799c8eeea249c0a7fd83d14 6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
```

```text
6153bd4fb3 fix(mcp): fail-closed resolver provenance + gate required-tool-glob enforcement (F018/F019)

28 paths, all under:
  proof/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001/**
  proof/pr_merge/embedded-audit/pr-1226/**
  src/dopemux/mcp/{gate.py,resolver.py}
  task-packets/TP-DMX-MCP-CAPABILITY-FAIL-CLOSED-001.{json,md}
  tests/mcp/{test_discovery_gate_strict.py,test_resolver.py}

docs/03-reference/architecture/second-brain/**   0 paths
schemas/second_brain/**                          0 paths
proof/TP-DMX-SECOND-BRAIN-*/**                   0 paths

CLASSIFICATION = UNRELATED_REPOSITORY_MOVEMENT
VERDICT        = no BLOCKED_NEW_SECOND_BRAIN_DRIFT
```

Worktree created from the fresh baseline (not from the session's checked-out branch):

```bash
git worktree add -b tp/DMX-SB-ADR-CONTRACT-EVIDENCE-001 \
  /Users/hue/code/.worktrees/DMX-SB-ADR-CONTRACT-EVIDENCE-001 \
  6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
```

Frozen authority re-verified from repository bytes rather than carried from notes:

```bash
git show 6153bd4fb3:docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md | shasum -a 256
```

```text
e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c   == CANDIDATE_SHA256   PASS
375 lines
```

---

## S1 — Reproduce the current evidence gap

```bash
for t in LocalSpoolPort CustodyPort OpenLoopCandidate TaskProposal TaskPromotionRequest; do
  git grep -n -I "$t" -- .
done
git grep -n -I -i "project.identity.envelope" -- .
git grep -n -I -i "service.capability.receipt" -- .
ls schemas/
```

Emitted by the S1 generator (`proof/.../generators/gen_s1_s2.py`):

```text
S1: NO_SUFFICIENT_SECOND_BRAIN_MACHINE_CONTRACT_SET
    machine_contract_hits          = 0
    runtime_implementation_hits    = 0
    test_only_hits                 = 0
    prose_only_hits                = 29
    schemas/second_brain exists    = False
```

Every occurrence of every ADR-named type is narrative prose (`*.md`) or a free-form
explanatory string field inside a structured file (`traceability-matrix.json`
`semantic_relationship` / `decision_title`, `OPERATOR_DECISION_LEDGER.yaml` `title`).
Packet §3 excludes both from counting as machine contracts. `project identity envelope`
has **zero** hits in any form.

Artifact: `BASELINE_CONTRACT_INVENTORY.json`

---

## S2 — Freeze clause inventory BEFORE contract authoring

The denominator is derived from packet §5 mandatory coverage and bound to exact
fragments of the ratified candidate. Generation fails closed if any fragment is not a
verbatim substring of the candidate at `e4b28946…`.

```bash
python3 gen_s1_s2.py
```

```text
S2: 10 ADRs / 97 clauses
    ADR-SB-001:  6   sb_dec=['SB-DEC-001','SB-DEC-002','SB-DEC-027']
    ADR-SB-002:  8   sb_dec=['SB-DEC-003','SB-DEC-004','SB-DEC-005','SB-DEC-006']
    ADR-SB-003:  8   sb_dec=['SB-DEC-016','SB-DEC-017']
    ADR-SB-004:  7   sb_dec=['SB-DEC-010','SB-DEC-011','SB-DEC-012']
    ADR-SB-005:  9   sb_dec=['SB-DEC-018','SB-DEC-019']
    ADR-SB-006: 14   sb_dec=['SB-DEC-014','SB-DEC-015']
    ADR-SB-007: 11   sb_dec=['SB-DEC-019','SB-DEC-029']
    ADR-SB-008: 16   sb_dec=['SB-DEC-006','SB-DEC-007','SB-DEC-008','SB-DEC-030']
    ADR-SB-009:  8   sb_dec=['SB-DEC-009','SB-DEC-013','SB-DEC-022','SB-DEC-024']
    ADR-SB-010: 10   sb_dec=['SB-DEC-020','SB-DEC-021']
    total sb_dec references = 28          == SB_DEC_REFERENCE_COUNT   PASS
    SB-DEC-026 present in any ADR evidence list = False   (A_LEAVE_UNLINKED preserved)
```

**FROZEN DENOMINATOR**

```text
ADR_CLAUSE_INVENTORY.json
sha256 = f073ca28802e6b140dd5789d5fad5839962635f7b287cac589ec704efc663288
clause_total = 97
```

This hash is frozen **in its own commit, before any contract artifact exists**. Git
history — not a self-asserted field — is what proves the freeze preceded authoring.
`ADR_CONTRACT_COVERAGE.json` must carry this exact value in `clause_inventory_sha256`,
and the deterministic validator enforces three-way agreement between the inventory
file's live hash, the coverage matrix's recorded hash, and every per-clause fragment
hash recomputed from the candidate.

---

## S3 — Author machine contracts

Generated from the frozen denominator, which is read and never re-derived — the
generator cannot widen or narrow the coverage denominator.

```bash
python3 gen_contracts.py
```

```text
S3: wrote 20 artifacts into schemas/second_brain/contracts/
    clause_inventory_sha256 = f073ca28802e6b140dd5789d5fad5839962635f7b287cac589ec704efc663288
    clause_total            = 97
    coverage counts         = {'COVERED': 97, 'NOT_APPLICABLE_PROVEN': 0, 'MISSING': 0, 'AMBIGUOUS': 0}
```

Layer A: `adr-machine-contract.schema.json`, `interface-contract.schema.json`,
`ADR-SB-001..010.contract.json`. Layer B: `local-spool-port.contract.json`,
`custody-port.contract.json`, `open-loop-candidate.schema.json`,
`task-proposal.schema.json`, `task-promotion-request.schema.json`,
`project-identity-envelope.schema.json`, `service-capability-receipt.schema.json`.
Plus `ADR_CONTRACT_COVERAGE.json`.

`AMBIGUOUS` was never needed: no clause required an interpretation the candidate
does not state. `NOT_APPLICABLE_PROVEN` is used **zero** times — it is not a
shortcut taken anywhere in this packet.

---

## S4 — Deterministic validation and the false-green defence

```bash
python3 scripts/governance/validate_second_brain_adr_contracts.py
```

```text
checks: 113  failed: 0
PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
FO01_STALE_RECORD_RECONCILED
```

A validator that only reports PASS on happy-path files proves nothing, so the
matrix runs the **real** validator against mutated repository copies:

```bash
python3 -m pytest -q tests/governance/test_second_brain_adr_contracts.py
```

```text
..............................................                           [100%]
46 passed
```

Matrix coverage against packet §9, with the guard each row exercises:

| §9 row | guard asserted |
|---|---|
| valid frozen contract set → PASS | exit 0, 113 checks, both groups PASS |
| delete one ADR contract | `A01-ten-adr-contracts-exist` |
| change candidate SHA binding | `A04-contracts-bind-candidate` |
| remove one coverage clause | `A08-every-clause-covered-once` |
| mark one clause MISSING | `A10-missing-zero` |
| point coverage at nonexistent rule | `A09-pointers-resolve` |
| corrupt one SB-DEC reference | `A07-sb-dec:ADR-SB-009` |
| change ADR status PROPOSED → ACCEPTED | `A16-ten-proposed`, `A18-no-accepted-token` |
| delete LocalSpoolPort contract | `A13-named-typed-artifacts-exist` |
| allow restricted spool without encryption | `S01-restricted-spool-requires-encryption` |
| give OpenLoopCandidate an assignee | `S02-open-loop-no-pm-properties` |
| enable TaskPromotionRequest by default | `S03-task-promotion-disabled` |
| allow UNKNOWN policy eligibility | `S04-unknown-eligibility-denies` |
| allow wrong-project write | `S05-envelope-denies-wrong-project` |
| raise UX visible queue max above 7 | `S06-visible-queue-max-7` |
| permit surprise write | `S07-no-surprise-writes` |
| claim denial fixtures implemented | `A15-no-denial-fixture-claim` + `A14` |

Beyond §9: mutated candidate document, coverage pointing at prose, rule
disagreeing with its clause, linking SB-DEC-026, deleting OpenLoopCandidate,
redefining the frozen denominator, forged source fragment, open-shaped
OpenLoopCandidate, dropped promotion proofs, confidential semantic indexing,
multi-project capture, >1 active capture project, non-zero searchable residual,
runtime-authority claim, port claiming implementation, Second Brain as authority
target, five FO-01 regressions, and four fail-closed cases (unparseable
contract, missing candidate, missing inventory, empty root, bad root → exit 2).

Two design points that make this matrix load-bearing rather than decorative:

1. **Each negative test asserts the specific guard responsible fires**, not
   merely `exit != 0`. Asserting only nonzero exit lets an unrelated check take
   the credit while the intended guard sits silently dead.
2. **Semantic mutations are applied consistently across inventory and
   contract.** Mutating one side only would trip the cross-file agreement guard
   and prove nothing about the semantic invariant. Mutating both sides is the
   real false-green attempt, and the hard-coded value invariants are what stop it.

One real defect was found and fixed by running this suite: the validator crashed
with an opaque traceback on a malformed clause node instead of reporting the
guard. It was still fail-closed (exit 2), but a crash discards the whole report,
so the affected passes were hardened to skip malformed nodes and still emit a
diagnostic.

---

## S5 — FO-01 stale-record reconciliation

Round-trip pre-check **for this specific file** before any mutation (a sibling
file in this tree does not round-trip, so one file's result licenses nothing
about another):

```text
round_trips_exactly = True
before sha256 = 0e0258e0dc3e524fc2a01e6b3f17875c3969d3266fd5e727c2ff03a84cf4fb3a
after  sha256 = bc2decd1eec9660c9889059cacf41e6ca3333f5cb809516dcb5b0b38e6c99687
```

Exact-string edits were used regardless, for minimality and auditability.

Group B of the validator failed 8/8 before the reconciliation and passes 8/8
after — the defect was reproduced by machine before it was repaired, not merely
asserted.

Semantic trap handled explicitly: `gates.adr_acceptance: "CLOSED"` means the
acceptance gate is **shut**, while §10's required "FO01 gate condition = CLOSED"
means the FO-01 **blocker** is closed. Opposite senses of one word. Neither
field was overloaded; eligibility went into separately named keys
(`fo01_gate_condition`, `adr_acceptance_gate_eligible`,
`other_adr_acceptance_conditions`) and the distinction is written into
`gate_field_semantics` in the file itself. `adr_acceptance_authorized` remains
`false` and `gates.adr_acceptance` remains `CLOSED`.

---

## S6 — Repository gates

```bash
git diff --check
```

```text
clean
```

```bash
python3 scripts/governance/validate_change_contract.py \
  --base 6153bd4fb30ed3d038e51b371ad9ebfb4916bfac --head HEAD
```

```text
status=PASS
max_lane=L2
paths=29
```

The base is pinned to the frozen execution baseline; `--head` is deliberately
left unpinned, because pinning the head invalidates the step on every successor
commit — the exact recursion that commit-bound receipts exist to break. Both
endpoints are pinned only in recorded receipts, which describe a run that has
already happened.

```bash
python3 -c "<jsonschema validation of the packet against dopetask-canonical-spec.json>"
```

```text
S6 PASSED: task packet validates against dopetask-canonical-spec.json
```

First run of this gate FAILED with nine errors — `steps[].validation` must be an
array, not a string. Corrected and re-run.

```bash
pre-commit run --files $(git diff --name-only 6153bd4fb3 HEAD | tr '\n' ' ') \
  task-packets/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001.json
```

```text
18 hooks: 4 Passed / 14 Skipped
  Evidence-economy change-contract preflight ........ Passed
  Enforce markdown file locations for changed files . Passed
  Audit docs filename hygiene ....................... Passed
  Enforce repository root hygiene ................... Passed
```

The 14 skips were **verified, not assumed**: `trailing-whitespace`,
`end-of-file-fixer` and `markdownlint` are scoped by
`files: ^(docs/|task-packets/).*\.md$` and `check-yaml` by `^config/.*\.ya?ml$`;
this slice contains no matching file. pre-commit reports a hook with no matching
files as `Skipped` rather than omitting it, so a changed skip count is not by
itself a defect.

---

## S4 (continued) — a real false-green found by the producer, and closed

The §9 matrix passed 46/46, so I attacked the validator directly rather than
trusting that result. Group S pins ~37 of 97 clauses; the other ~60 have no pinned
semantic guard. The question is whether anything else stops them being weakened.

Attack: edit the inventory **and** the contract consistently, so cross-file
agreement still holds, and leave the cited source fragment untouched, so it remains
a genuine candidate substring with a matching hash.

```bash
# reroute ADR-SB-002-C01 canonical capture: Dope-Memory -> ConPort, on both sides
python3 scripts/governance/validate_second_brain_adr_contracts.py --repo-root /tmp/fg-probe
```

```text
checks: 113  failed: 0
PASS_SECOND_BRAIN_ADR_MACHINE_CONTRACT_COVERAGE
```

**That is a real false-green.** The architecture decision "captured events go to
Dope-Memory" had been silently rerouted to a different canonical authority, and
every guard passed: the fragment check passed (fragment unchanged), the cross-file
agreement check passed (both sides edited), and `ConPort` is a legitimate member of
the closed authority set, so the A20 check passed too.

Fix — check **A21, value grounding**: for the rule classes where a silent swap does
the most damage, the machine value must itself appear in the decision text the
clause cites.

```text
AUTHORITY_TARGET / EQUALS    value must appear in the cited fragments
ENUM / SET_EQUALS            every member must appear
numeric bounds               digit or English number word must appear
```

Deliberately narrow: `SUPERSET_OF` is excluded because a contract may legitimately
normalise a term the prose abbreviates (`class` → `classification` in ADR-SB-006-C04),
and a grounding rule that is sometimes wrong is worse than none.

```bash
python3 scripts/governance/validate_second_brain_adr_contracts.py --repo-root /tmp/fg-probe --json
```

```text
result: FAIL | failed: 1
  A21-machine-values-grounded-in-cited-text
    ungrounded=["ADR-SB-002-C01: authority target 'ConPort' not in cited text"]
```

Six tests now cover this class, including `ADR-SB-009-C03` (max one active
automatic-capture project) and `ADR-SB-002-C07` (promotion receipt target), which
have **no** pinned Group-S guard and are caught by grounding alone.

Final: **114 checks / 0 failed; 52 adversarial tests / 0 failed.**

The lesson worth carrying: a green adversarial matrix proves the mutations you
thought of are caught. It says nothing about the ones you did not. The matrix had to
be attacked separately from the artifacts it guards.
