# Terminal Semantic Census — R3

Scan command (from TP-DMX-PR-PREP-SPECIALIST-V2-001-R3-SUPERVISOR-RULING.md):

```bash
rg -n 'GO_SUPERVISED_FINAL|SUPERVISED_FINAL_CREATION|CREATE_FINAL_PR|CREATE_READY|CLEAN_CREATE_READY|DRAFT_RECOMMENDED|HIGH_RISK_ESCALATE|MERGE_READY|merge-ready|risk_hint|LOW|MEDIUM|HIGH|mandatory.*7|seven.*artifact|BRANCH_STATE\.json|PR_HANDOFF_BUNDLE\.json' docs/03-reference/pr-pipeline/prep docs/pr_prep
```

205 raw matches across 49 files. Classified below.

## RETIRED_PROSE — in R1/R2/R3 allowlist, correctly converted, no action needed

Canonical (17): `skill-model.md`, `operator-contract.md`, `workflow-sequence.md`,
`deterministic-gate-rules.md`, `go-no-go-criteria.md`, `handoff-to-prms-contract.md`,
`pr-creation-policy.md`, `high-risk-handoff-rules.md`, `branch-state-schema.md`,
`consensus-gate-rules.md`, `handoff-contract.md`, `operational-posture-options.md`,
`layered-validation-model.md`, `creation-mode-rules.md`, `pr-drafting-rules.md`,
`live-pilot-protocol.md`, `stash-and-branch-safety-rules.md`.

All matches in these files are either retirement-describing prose (e.g. "This
file previously defined a `risk_hint: LOW|MEDIUM|HIGH` field... retired") or,
in `stash-and-branch-safety-rules.md`, non-normative read-only discovery
constraints that defer risk/posture language to `operator-contract.md` §4/§5.
Compat counterparts (17) are pure pointer stubs into these canonical files.
No `ACTIVE_CONTRADICTION` in this set.

## SUBSTRING_FALSE_POSITIVE

- `workflow-sequence.md` — `id: WORKFLOW_SEQUENCE` matches `LOW` as a
  substring of "WORKF**LOW**". Not a semantic hit.
- `evaluation-model.md`, `post-pilot-go-no-go-criteria.md` — `HIGHLY_USEFUL`,
  `HIGH_SIGNAL` match `HIGH` as a substring of a distinct token. Listed here
  once; the files themselves are separately classified below on their own
  merits (they also contain unambiguous non-substring hits).

## ACTIVE_CONTRADICTION — outside the R1+R2+R3 allowlist (STOP CONDITION)

These files are **not** in the packet's allowlist at any round and actively
govern current behavior using retired V1 vocabulary, with no retirement
framing:

**Canonical** (`docs/03-reference/pr-pipeline/prep/`):
1. `adapters/codex/readme.md` — documents the exact 7-step
   `INSPECT_BRANCH_STATE → ... → HANDOFF_TO_PRMS` sequence and
   `BRANCH_STATE.json` / `PR_HANDOFF_BUNDLE.json` as current required
   artifacts, including a live `validate_handoff(PR_HANDOFF_BUNDLE.json, ...)`
   call.
2. `adapters/vibe/agent-spec.md` — instructs emission of `BRANCH_STATE.json`,
   `PR_HANDOFF_BUNDLE.json`, `Draft Posture: {CREATE_READY/DRAFT_RECOMMENDED/BLOCKED}`,
   `Risk Hint: {LOW/MEDIUM/HIGH}` as current agent behavior.
3. `adapters/vibe/checkpoint-sequence.md` — same pattern (required artifacts,
   Draft Posture, Risk Hint) as a checkpoint table.
4. `adapters/vibe/guardrails.md` — same required-artifact pattern.
5. `adapters/vibe/operator-review-form.md` — checklist items for
   `BRANCH_STATE.json (INTAKE)` / `PR_HANDOFF_BUNDLE.json (CREATION)`, and
   `Ambiguity Level: [LOW / MEDIUM / HIGH]`.
6. `final-prep-decision-model.md` — defines `CREATE_READY`,
   `DRAFT_RECOMMENDED`, `BLOCKED_ADJACENT_WORK_AMBIGUITY`,
   `HIGH_RISK_HANDOFF_REQUIRED` as the current governing decision states.
7. `post-pilot-go-no-go-criteria.md` — defines `GO_SUPERVISED_FINAL_CREATION`
   as a current, reachable governance outcome with confidence/evidence
   thresholds.
8. `post-eval-governance-options.md` — lists `GO_SUPERVISED_FINAL_CREATION`,
   `GO_DRAFT_FIRST`, `GO_PACKAGE_ONLY` as current favorable outcomes.
9. `ambiguity-scoring.md` — maps `LOW/MEDIUM/HIGH` ambiguity bands to
   `PROCEED_WITH_CAUTION`/`DRAFT_ONLY`/`BLOCK_PENDING_REVIEW` as a standalone,
   currently governing risk-classification table competing with the L0-L3
   risk lanes.

**Compatibility** (`docs/pr_prep/`), same contradictions, independent copies
(not pointer stubs):
10. `adapters/codex/readme-2.md`
11. `adapters/vibe/agent-blueprint.md`
12. `adapters/vibe/template-agent.md`
13. `adapters/vibe/checkpoint-sequence.md`
14. `adapters/vibe/guardrails-2.md`
15. `adapters/vibe/operator-review-form.md`
16. `final-prep-decision-model.md`
17. `post-pilot-go-no-go-criteria.md`
18. `post-eval-governance-options.md`
19. `ambiguity-scoring.md`

**`ACTIVE_CONTRADICTION_COUNT (outside R1+R2+R3 allowlist) = 19 files`**

Per the R3 ruling: *"If an ACTIVE_CONTRADICTION appears outside the R3
allowlist, stop with `PREP_V2_NEEDS_SUPERVISOR`. Do not auto-expand scope
again."* This condition is met. No C1-R3 is frozen. None of the 19 files
above were touched.

## SUPERVISOR_JUDGMENT — borderline, not self-evidently contradiction, flagged rather than resolved

These use `LOW/MEDIUM/HIGH`-shaped vocabulary but for a narrower, arguably
non-PR-creation-authority purpose. Left unclassified as PASS/FAIL and
un-edited pending supervisor direction; each appears in both the canonical
file and its `docs/pr_prep/` copy:

- `base-branch-detection-rules.md` — `HIGH/MEDIUM/LOW` grades *confidence in
  a base-branch-detection heuristic*, not PR risk or creation authority.
- `obligation-model.md` — `LOW/MEDIUM/HIGH` grades *obligation severity*
  ("HIGH: ... missing will likely block PR creation"); ties into creation
  blocking but is a distinct axis from `risk_hint`.
- `obligation-severity-rules.md` — same obligation-severity pattern, more
  detailed per-obligation-type table.
- `evaluation-model.md` — `HIGH_SIGNAL`/`CONSERVATIVE_USEFUL`/`HIGHLY_USEFUL`
  grade *audit/draft quality bands* for pilot evaluation, not PR risk.
- `section-fill-policy.md` — one `HIGH or CRITICAL` gate on whether a PR-body
  section is required, not a creation/merge authority state.
- `pilot-case-selection-rules.md` — `PILOT_READY_HIGH_RISK` names a category
  of *branch selected for a historical pilot*, not a live decision state.
- `operator-review-form.md` (canonical + both `docs/pr_prep/` and
  `docs/pr_prep/adapters/vibe/` copies) — `INFO|LOW|MEDIUM|HIGH|CRITICAL`
  grades *severity of a human operator's override*, not an automated
  creation/risk decision.

None of these were counted toward `ACTIVE_CONTRADICTION_COUNT` above, and
none were edited. They are called out explicitly so a future round does not
have to re-derive the same regex sweep.

## Disclosure

`tests/governance/test_pr_prep_contract_v2.py` was **not** extended with R3
coverage this round, because the freeze this round did not happen — R4 (or
a supervisor decision on the 19-file finding) will determine which files are
actually in scope for repair, and adding tests now would test files whose
final disposition is not yet decided.
