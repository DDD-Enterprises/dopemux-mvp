# TP-DMX-PR-PREP-SPECIALIST-V2-001 — Supervisor R2 Closure

## Decision

`PREP_V2_NEEDS_IMPLEMENTER`

The reported C1 is **not audit-ready** because the implementer disclosed active canonical PR-prep files that still contain legacy V1 semantics.

The prior frozen head:

`1ab5d6c1cc56e85557776b37b0ffa0594858aa02`

is now:

`SUPERSEDED_NOT_AUDITED`

Do not audit it.

## Evidence

Current `main` contains the six residual files and search evidence confirms `risk_hint` content in all six families:

Canonical:
- `docs/03-reference/pr-pipeline/prep/branch-state-schema.md`
- `docs/03-reference/pr-pipeline/prep/consensus-gate-rules.md`
- `docs/03-reference/pr-pipeline/prep/handoff-contract.md`

Compatibility:
- `docs/pr_prep/branch-state-schema.md`
- `docs/pr_prep/consensus-gate-rules.md`
- `docs/pr_prep/handoff-contract.md`

Under the R1 ruling, the first three are canonical PR-pipeline reference surfaces. Their remaining V1 semantics therefore block a coherent V2 audit target.

## R2 allowlist amendment

Authorize exactly the six files listed above in addition to the R1 allowlist.

Purpose is narrow:

1. remove links to deleted `docs/pr_prep/contract-v2.md`;
2. eliminate independent legacy PR-prep `LOW/MEDIUM/HIGH` risk semantics;
3. eliminate obsolete V1 seven-step/fixed-artifact/readiness authority if present;
4. convert canonical files to concise pointers where their standalone content is superseded;
5. convert `docs/pr_prep/*` counterparts to compatibility-only pointer stubs.

Do not edit archive copies.
Do not expand to unrelated LOW/MEDIUM/HIGH terminology belonging to other domains.

## Required repair

### Canonical files

The three files under:

`docs/03-reference/pr-pipeline/prep/`

must not contradict:

`docs/03-reference/pr-pipeline/prep/operator-contract.md`

Where the old standalone contract is obsolete, prefer a short pointer identifying the canonical V2 owner rather than maintaining another manually synchronized policy body.

For `handoff-contract.md`, point to the V2 handoff authority (`handoff-to-prms-contract.md` and/or `operator-contract.md`) rather than recreating another schema.

### Compatibility files

The three corresponding files under:

`docs/pr_prep/`

must be compatibility pointer stubs to the canonical `docs/03-reference/pr-pipeline/prep/` files.

## Validation

After repair, rerun the full deterministic gate already required by R1, plus:

```bash
rg -n 'contract-v2\.md|risk_hint.*(LOW|MEDIUM|HIGH)|"(LOW|MEDIUM|HIGH)"|\bLOW\b|\bMEDIUM\b|\bHIGH\b'   docs/03-reference/pr-pipeline/prep/branch-state-schema.md   docs/03-reference/pr-pipeline/prep/consensus-gate-rules.md   docs/03-reference/pr-pipeline/prep/handoff-contract.md   docs/pr_prep/branch-state-schema.md   docs/pr_prep/consensus-gate-rules.md   docs/pr_prep/handoff-contract.md
```

Interpret matches semantically. The target is absence of **legacy PR-prep risk/readiness semantics**, not a blind ban on English words.

Also rerun the broader active-surface legacy scan required by R1.

## Freeze rule

After all gates pass, freeze a **new** substantive head:

`C1-R2=<exact SHA>`

Record:

- prior C1 = `SUPERSEDED_NOT_AUDITED`;
- C1-R2 full SHA;
- parent;
- current `origin/main`;
- merge base and drift classification;
- exact base-to-C1-R2 changed paths;
- allowlist result;
- targeted residual scan;
- full active-surface legacy scan;
- governance tests;
- pre-commit;
- secret scan.

Then stop.

## Audit gate

Do **not** run S4 against the old C1.

S4 becomes authorized only after C1-R2 is reported with all deterministic gates PASS and no remaining active semantic contradiction.

No merge, close, mark-ready, force-push, history rewrite, branch deletion, signer/permission change, release, migration, or production authority is granted.
