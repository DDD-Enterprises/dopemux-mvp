# TP-DMX-PR-PREP-SPECIALIST-V2-001 — Supervisor R3 Terminal Semantic Closure

## Decision

`PREP_V2_NEEDS_IMPLEMENTER`

Do not run S4 against C1-R2.

The reported C1-R2:

`f0877721059c30d611db44521d0020603806076e`

is now:

`SUPERSEDED_NOT_AUDITED`

## Why R2 is not audit-ready

The implementer correctly disclosed six out-of-scope `docs/pr_prep/` files with legacy vocabulary. Supervisor inspection of current main proves that this is behavioral contradiction, not harmless terminology.

Examples include:

- `operational-posture-options.md`: authorizes `GO_SUPERVISED_FINAL_CREATION` and "PR creation (merge-ready)".
- `creation-mode-rules.md`: defines `CREATE_FINAL_PR` and non-draft creation.
- `pr-drafting-rules.md`: emits `CREATE_READY`.
- `layered-validation-model.md`: emits `CLEAN_CREATE_READY`, `DRAFT_RECOMMENDED`, and `HIGH_RISK_ESCALATE`.
- `live-pilot-protocol.md`: permits `SUPERVISED_FINAL_CREATION` of non-draft PRs.
- `stash-and-branch-safety-rules.md`: retains pre-V2 posture/risk vocabulary.

The six corresponding canonical files under `docs/03-reference/pr-pipeline/prep/` are byte-identical or substantively equivalent stale contracts on current main.

That directly conflicts with the R1 ruling that:

- `docs/03-reference/pr-pipeline/prep/**` is the canonical reference-contract family;
- `docs/pr_prep/**` is compatibility-only;
- compatibility surfaces may not carry independent behavioral authority.

## R3 allowlist amendment

Add exactly these canonical files:

- `docs/03-reference/pr-pipeline/prep/operational-posture-options.md`
- `docs/03-reference/pr-pipeline/prep/layered-validation-model.md`
- `docs/03-reference/pr-pipeline/prep/creation-mode-rules.md`
- `docs/03-reference/pr-pipeline/prep/pr-drafting-rules.md`
- `docs/03-reference/pr-pipeline/prep/live-pilot-protocol.md`
- `docs/03-reference/pr-pipeline/prep/stash-and-branch-safety-rules.md`

And exactly these compatibility counterparts:

- `docs/pr_prep/operational-posture-options.md`
- `docs/pr_prep/layered-validation-model.md`
- `docs/pr_prep/creation-mode-rules.md`
- `docs/pr_prep/pr-drafting-rules.md`
- `docs/pr_prep/live-pilot-protocol.md`
- `docs/pr_prep/stash-and-branch-safety-rules.md`

No other scope expansion is authorized.

## Repair rule

For canonical files, prefer concise V2 pointer/deprecation stubs instead of inventing another policy body.

Useful non-conflicting operational guidance may remain, but all normative state, risk, creation, audit, readiness, and authority semantics must defer to the V2 canonical contract.

For compatibility files, use pointer stubs to their canonical counterparts.

Specifically remove as governing current behavior:

- `CREATE_READY`
- `CLEAN_CREATE_READY`
- `DRAFT_RECOMMENDED`
- `HIGH_RISK_ESCALATE`
- `GO_SUPERVISED_FINAL_CREATION`
- `SUPERVISED_FINAL_CREATION`
- PR Prep "merge-ready" creation authority
- PR Prep non-draft final-creation authority
- legacy LOW/MEDIUM/HIGH PR-prep risk classification

Retirement-describing prose is allowed only when unmistakably non-normative.

## Terminal semantic census

Before freezing another head, scan **every non-archive file** under:

- `docs/03-reference/pr-pipeline/prep/**`
- `docs/pr_prep/**`

for legacy PR-prep semantics.

At minimum search:

```bash
rg -n   'GO_SUPERVISED_FINAL|SUPERVISED_FINAL_CREATION|CREATE_FINAL_PR|CREATE_READY|CLEAN_CREATE_READY|DRAFT_RECOMMENDED|HIGH_RISK_ESCALATE|MERGE_READY|merge-ready|risk_hint|LOW|MEDIUM|HIGH|mandatory.*7|seven.*artifact|BRANCH_STATE\.json|PR_HANDOFF_BUNDLE\.json'   docs/03-reference/pr-pipeline/prep docs/pr_prep
```

Classify every match:

- `RETIRED_PROSE`
- `NON_PR_PREP_DOMAIN`
- `ACTIVE_CONTRADICTION`

The gate is:

`ACTIVE_CONTRADICTION_COUNT=0`

If an `ACTIVE_CONTRADICTION` appears outside the R3 allowlist, stop with `PREP_V2_NEEDS_SUPERVISOR`. Do not auto-expand scope again.

## Full deterministic validation

After the repair, rerun:

1. repository/worktree/branch identity;
2. current origin/main and merge-base/drift classification;
3. exact base-to-head changed-file allowlist;
4. `git diff --check`;
5. Task Packet schema/frontmatter;
6. focused V2 governance test;
7. complete relevant governance/docs suite;
8. changed-file pre-commit, clean second pass if hooks edit;
9. secret scan;
10. open-PR overlap refresh;
11. terminal semantic census.

The pre-existing `docs/runbooks/ddd-release-gate-app.md` hygiene defect remains non-blocking only if unchanged and proven unrelated.

## Freeze

If every gate passes, freeze:

`C1-R3=<exact full SHA>`

Record:

- prior C1 = `SUPERSEDED_NOT_AUDITED`;
- C1-R2 = `SUPERSEDED_NOT_AUDITED`;
- C1-R3;
- parent;
- current origin/main;
- merge base/drift;
- exact changed paths;
- allowlist;
- terminal semantic census;
- tests/pre-commit/secret scan;
- open-PR overlap.

Then stop and report.

## S4 authorization gate

S4 is authorized only when C1-R3 is reported with:

- all deterministic gates PASS;
- `ACTIVE_CONTRADICTION_COUNT=0`;
- no conflicting or materially unknown main/PR overlap;
- no new substantive change after C1-R3.

The independent auditor must review **exact C1-R3**, not any prior head.

No merge, close, mark-ready, force-push, history rewrite, branch deletion, signer/permission change, release, migration, or production authority is granted.
