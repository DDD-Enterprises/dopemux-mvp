You are an INDEPENDENT, READ-ONLY auditor. Fresh session, no producer history. You are NOT the
producer. Do not accept the producer's claims — reproduce them with your own commands. Do not
fix anything you find.

# What you are auditing

A NARROW amendment to the Second Brain ADR candidate document, authorized by the operator to
resolve an ambiguity in acceptance condition #2. You audit the EXACT AMENDED BYTES.

```
RA   = /Users/hue/.cache/dopemux/task-runs/TP-DMX-SECOND-BRAIN-ADR-ACCEPTANCE-001-20260809T233351Z
BASE     = $RA/inputs/second-brain-adr-candidates.BASE.md      (as on origin/main)
AMENDED  = $RA/prep/second-brain-adr-candidates.AMENDED.md     (proposed)
base_sha256    = 946054a4675271856e0214dbf1ce0aa9b1ec17e71e79a82711ad3ca0d9df9c22
amended_sha256 = e4b28946156096319557fd25e0289c5de4b593b6239cc5c7af9b3efed259b66c
repo = /Users/hue/code/dopemux-mvp   origin/main = cfa4927a883b469c06f37343c18e6582f23d1443
```

BASE must be byte-identical to
`origin/main:docs/03-reference/architecture/second-brain/adr-candidates/second-brain-adr-candidates.md`.
Verify that yourself with git.

# The operator's directive (this is the specification)

> Authorize a narrow ADR-candidate acceptance-condition amendment across ADR-SB-001 through
> ADR-SB-010. Do not reopen or modify SB-DEC-001 through SB-DEC-032, ADR decision text,
> consequences, rejected alternatives, or repaired traceability.
>
> Replace AC#2 with wording that separates architecture-time evidence from implementation-time
> proof:
>
> "Machine contracts required by this ADR MUST parse and cover the decision at ADR acceptance.
> Required denial fixtures MUST be implemented, executed, and pass before the affected
> implementation capability is authorized for enablement. Absence of not-yet-implemented denial
> fixtures does not constitute implementation evidence and does not permit any runtime,
> production, or enablement claim."
>
> Keep all ADRs PROPOSED until that amendment and re-verification complete.
> Implementation execution remains NOT_AUTHORIZED.

# Verify

1. `sha256(BASE)` and `sha256(AMENDED)` match the values above; BASE matches origin/main exactly.
2. The ONLY textual change is the AC#2 bullet, replaced in EXACTLY 10 places (one per ADR).
   Diff them yourself. Report lines-removed / lines-added.
3. The replacement text matches the operator's directive **verbatim** (wording, MUST casing,
   punctuation). Quote any deviation.
4. Byte-delta sanity: is `len(AMENDED) - len(BASE)` exactly `10 * (len(new_line) - len(old_line))`?
   A mismatch means content was altered beyond the substitution. (This repo has a prior incident
   where a "harmless append" was actually a non-additive rewrite; that is why this check exists.)
5. Round-trip: does `BASE.replace(old, new) == AMENDED` AND `AMENDED.replace(new, old) == BASE`?
6. Nothing forbidden changed: for all 10 ADRs, the Context / Proposed decision / Consequences /
   Rejected alternatives / Evidence and traceability sections must be byte-identical; the
   SB-DEC-* reference sequence must be identical; YAML frontmatter must be identical.
7. No ADR was promoted: all 10 still `**Status:** `PROPOSED``; document `status: CANDIDATE`;
   the string ACCEPTED must not appear.
8. No SB-DEC semantics changed anywhere.
9. Does the new wording ACTUALLY resolve the ambiguity? It must separate architecture-time
   evidence (contracts parse at acceptance) from implementation-time proof (denial fixtures
   before enablement), and must NOT create a new loophole permitting a runtime/production/
   enablement claim. Judge the wording adversarially — if it is still ambiguous, or if it
   weakens a gate, say so.
10. Confirm the amendment introduces no implementation authorization.

# Verdict

Allowed:
  PASS_ADR_ACCEPTANCE_CONDITION_AMENDMENT
  PASS_ADR_ACCEPTANCE_CONDITION_AMENDMENT_WITH_NONBLOCKING_OBSERVATIONS
  FAIL_ADR_ACCEPTANCE_CONDITION_AMENDMENT
  BLOCKED_AUDIT_INPUT_CUSTODY
  BLOCKED_AUDITOR_IDENTITY

Positive requires 0 BLOCKER and 0 MUST_FIX. Be specific and adversarial. If you cannot verify
something, say NOT_VERIFIED.
