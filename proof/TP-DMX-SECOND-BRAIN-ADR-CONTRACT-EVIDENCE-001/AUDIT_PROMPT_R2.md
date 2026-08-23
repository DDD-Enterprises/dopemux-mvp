# Independent audit — round 2

You are an independent auditor. You did not produce this work and you have none of
the producer's conversation history. Your job is to try to break it.

**Read-only.** Do not edit, create, stage, commit or push anything. Do not run any
command that writes to the repository. You are in a throwaway detached worktree;
even so, changing files would invalidate the audit.

## What you are auditing

```text
repository        DDD-Enterprises/dopemux-mvp
branch            tp/DMX-SB-ADR-CONTRACT-EVIDENCE-001   (PR #1227, DRAFT)
frozen head       6e1b4472ba626df2a5d7724e87c5ec77c9c46043
base              6153bd4fb30ed3d038e51b371ad9ebfb4916bfac
```

Confirm first that `git rev-parse HEAD` is `6e1b4472ba626df2a5d7724e87c5ec77c9c46043`.
If it is not, stop and report that instead of auditing whatever is there.

## Context you need

This is a **second** audit. The first one, of head `7955ef33d7`, returned FAIL with
3 blockers and 5 must-fix. Its report is at
`proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/AUDITOR_REPORT.md` and is
unedited — read it, because your job includes checking whether the repairs are real
rather than cosmetic.

The operator then authorized re-freezing the coverage denominator and repairing the
whole finding class in one wave. The authorization is reproduced verbatim inside
`proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/DENOMINATOR_REFREEZE_RECEIPT.json`.

The packet produces **architecture-time evidence only**. It accepts no ADR, changes
no disposition, and implements nothing. All ten ADRs must still be `PROPOSED`.

## The supersession chain, which you should verify yourself

```text
a9397e5630  first freeze,   97 clauses, sha256 f073ca28…  SUPERSEDED
3e0d89815c  second freeze, 160 clauses, sha256 b164fc0b…  CURRENT
6e1b4472ba  contracts, validator, tests written against the second freeze
```

Your worktree shares the repository's object database, so `git show
a9397e5630:proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json`
works and lets you check the supersession claims against the actual bytes of the
superseded denominator.

Two ordering claims are worth testing directly:

- `git show --stat --name-only 3e0d89815c` should contain **no** file under
  `schemas/` and no validator change. The freeze must precede the artifacts written
  against it; a hash recorded alongside them would prove nothing.
- The producer claims `removed_clause_ids` is empty because every superseded
  requirement still has a home. Check that against `modified_clauses`.

## Attack these seven areas

The operator named these explicitly. Attack each one; do not merely confirm the
producer's description of it.

```text
denominator completeness
bilateral inventory+contract mutation
closed-set shrinking and widening
invented authority values
invented typed surface
label-only pseudo-contracts
FO-01 receipt lock
```

Concretely, at minimum:

1. **Denominator completeness.** Read the candidate at
   `docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md`
   yourself, sentence by sentence. Is any normative assertion, closed set, limit,
   default, deny rule, authority target, state distinction, required receipt or
   required interface missing from the 160 clauses? The census worksheet
   (`DENOMINATOR_CENSUS_WORKSHEET.json`) disposes of every unit and records the
   judgment calls by name — attack those judgments directly. Exclusions are governed
   by the operator's DO-NOT-INCLUDE list, quoted in that file.
2. **Bilateral mutation.** Edit a clause value in `ADR_CLAUSE_INVENTORY.json` *and*
   the matching `ADR-SB-00N.contract.json` consistently, then run the validator. It
   must fail. Then also rewrite `FROZEN_INVENTORY_SHA256` in a **copy** of the
   validator (do not modify the repository copy — copy it to /tmp) and re-run: which
   guards still catch it? Is any load-bearing decision left unprotected in that
   mode?
3. **Closed sets.** Take every `SET_EQUALS` clause. Drop a member; add a member.
   Both must fail. Find one where they do not.
4. **Invented authority.** `grep -rn dopeTask` across
   `schemas/second_brain/contracts/`. Then check whether any `AUTHORITY_TARGET`
   value is absent from the candidate.
5. **Invented typed surface.** For each of the seven Layer B artifacts, take every
   property name, enum member and const string and find the candidate sentence that
   authorises it. Anything that is this repository's invention rather than the
   architecture's decision is a finding.
6. **Label-only rules.** Is there any clause whose `machine_value` states that
   something is *named* rather than that something must be *true*?
7. **FO-01 lock.** Change a field in
   `docs/03-reference/architecture/second-brain/adr-candidates/fo-01-repair-status.json`
   that is derived from
   `proof/TP-DMX-SECOND-BRAIN-ADR-TRACEABILITY-REPAIR-001/FO01_RESOLUTION_RECEIPT.json`.
   The validator must fail. Try a field the producer might have missed.

Also worth attacking, because the producer claims them:

- Every clause fragment must be a verbatim substring of the candidate **and** fall
  inside its own ADR's Context / Proposed decision / Consequences span. Find a
  clause grounded in a rejected alternative.
- `FALSE_GREEN_MATRIX.json` claims ten mutations fail via their *intended* guard.
  Re-run `python3 -m pytest tests/governance/test_second_brain_adr_contracts.py`
  and check the tests assert a named guard rather than merely a nonzero exit.
- The bundle claims the change-contract and pre-commit gates fail for a single
  embedded-audit representation cause. Verify that is the only cause, and that no
  substantive failure is hiding behind it.

## Commands you will want

```bash
git rev-parse HEAD
python3 scripts/governance/validate_second_brain_adr_contracts.py
python3 scripts/governance/validate_second_brain_adr_contracts.py --json
python3 -m pytest tests/governance/test_second_brain_adr_contracts.py -q
sha256sum proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json
git show --stat --name-only 3e0d89815c
git show a9397e5630:proof/TP-DMX-SECOND-BRAIN-ADR-CONTRACT-EVIDENCE-001/ADR_CLAUSE_INVENTORY.json | head -40
```

## What must be true for a PASS

```text
VERDICT=PASS
BLOCKERS=0
MUST_FIX=0
```

Anything less is a FAIL and the packet does not progress. Do not soften a finding to
reach PASS, and do not manufacture a finding to look rigorous. If the evidence holds,
say so and say what you actually did to try to break it.

An audit that only restates the producer's own claims is worthless. Every conclusion
you report must come from bytes you read or a command you ran.

## Report format

Return a Markdown report with exactly these sections:

```markdown
# VERDICT
PASS | FAIL

BLOCKERS: <n>
MUST_FIX: <n>

# WHAT I VERIFIED
<what you actually executed and read, with the results>

# FINDINGS
<id, severity (BLOCKING | HIGH | MEDIUM | LOW), title, body — or "none">

# WHAT I COULD NOT VERIFY
<anything you could not check from these bytes, stated plainly>
```
