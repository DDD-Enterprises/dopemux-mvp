# R6 scope freeze — TP-DMX-PR-PREP-SPECIALIST-V2-001-R6

## Why R6 exists

The R5 scoped audit PASS was revoked by operator decision. Fresh
repository truth exposed defects that outrank the prior audit/Steward
claims:

1. `main` had advanced 9 commits past the R5 head (an independently
   audited change to the embedded-audit schema/acceptance tests among
   them), staling the R5 exact-head readiness.
2. **Four live unresolved review threads** (all `copilot-pull-request-reviewer`)
   reported broken compatibility relative links under
   `docs/pr_prep/adapters/{vibe,codex}/**`.
3. **A false-negative census.** The R3/R4 terminal semantic census scanned
   for fixed-artifact/risk-hint/GO_* vocabulary but never for
   `TP-PRPS-000` or `7-step`. Six adapter README families (claude, cursor,
   gemini, jules, copilot, vibe — codex was already correctly repaired at
   R4) still actively declared `Contract: TP-PRPS-000-1.0.0`, a "7-step
   canonical workflow", and `Status: IMPLEMENTED AND COMPLIANT`, in both
   canonical and compatibility form.

## R6 census (expanded pattern set)

Ran against the unchanged content this branch already carried, before any
R6 edit, across `docs/03-reference/pr-pipeline/prep/**` and
`docs/pr_prep/**` (non-archive):

```
TP-PRPS-000, 7-step, seven-step, Exact 7-step sequence,
IMPLEMENTED AND COMPLIANT, BRANCH_STATE.json, PR_HANDOFF_BUNDLE.json,
CREATE_READY, DRAFT_RECOMMENDED, MERGE_READY, GO_DIRECT,
GO_SUPERVISED_FINAL_CREATION, risk_hint,
plus the prior R4 patterns (GO_SUPERVISED_FINAL, SUPERVISED_FINAL_CREATION,
CREATE_FINAL_PR, CLEAN_CREATE_READY, HIGH_RISK_ESCALATE, merge-ready)
```

32 files matched at least one pattern. Every match was read in full and
classified:

- **20 files: `RETIRED_PROSE`** — already correctly written in
  retrospective/forbidden framing ("This file previously defined/
  documented/claimed...", "...are retired", "Superseded by...", "...is
  forbidden"). No live active claim. Left unedited. Full list:
  `operational-posture-options.md`, `layered-validation-model.md`,
  `handoff-contract.md`, `workflow-sequence.md`,
  `handoff-to-prms-contract.md`, `go-no-go-criteria.md`,
  `creation-mode-rules.md`, `pr-creation-policy.md`, `pr-drafting-rules.md`,
  `live-pilot-protocol.md`, `post-pilot-go-no-go-criteria.md`,
  `post-eval-governance-options.md`, `operator-contract.md`, and the
  already-R4-repaired `adapters/vibe/{agent-spec,checkpoint-sequence,
  guardrails,operator-review-form}.md`, `branch-state-schema.md`,
  `adapters/codex/readme.md`.
- **12 files: `ACTIVE_CONTRADICTION`** — frozen in
  `R6_ACTIVE_CONTRADICTION_PATHS.txt`. The 6 non-codex adapter families'
  canonical `readme.md` and compatibility `readme-2.md` files, all
  containing live `**Contract**: TP-PRPS-000-1.0.0` /
  `✅ 7-step canonical workflow` / `**Status**: ✅ IMPLEMENTED AND
  COMPLIANT` claims, not retrospective prose.

Do not guess the count: this is exactly 12, verified by direct read of
every matched file, not inferred from the grep hit count (32).

## Separately: broken-link defect (not a semantic contradiction)

The R4 compat-stub template's canonical link used two `../` hops from
`docs/pr_prep/adapters/{platform}/`, but three are required to reach
`docs/03-reference/pr-pipeline/prep/**`. Affected 6 files (verified via
`grep -rl '\.\./\.\./03-reference' docs/pr_prep/`):
`docs/pr_prep/adapters/vibe/{template-agent,operator-review-form,
agent-blueprint,guardrails-2,checkpoint-sequence}.md` and
`docs/pr_prep/adapters/codex/readme-2.md`. Four of these six were flagged
live by `copilot-pull-request-reviewer` on PR #1224; the other two
(`template-agent.md`, `agent-blueprint.md`) were found by directly
grepping every compat file for the same broken pattern, not by trusting
the reviewer's file list as exhaustive. All six fixed:
`../../03-reference` → `../../../03-reference`, verified to resolve on
disk.

## Repair

- 12 `ACTIVE_CONTRADICTION` files converted to deprecation/pointer stubs,
  matching the established R4 `codex` pattern (canonical: "Superseded by
  operator-contract.md" + retrospective quoting of the retired claim +
  current-behavior/platform-notes section; compat: "compatibility surface
  only" pointer stub referencing the canonical file).
- 6 broken relative links repaired (see above).
- Regression tests added to
  `tests/governance/test_pr_prep_contract_v2.py`: no live V1 contract
  markers in any of the 12 R6-repaired files (canonical or compat); every
  R6 compat stub declares itself compatibility-surface-only; every
  relative link in every non-archive `docs/pr_prep/**` markdown file
  resolves on disk (a general regression test, not scoped to only the
  files already known to be broken).

## Verification after repair

Re-ran the full expanded R6 census against the repaired tree: zero
remaining `ACTIVE_CONTRADICTION` hits. All 32 originally-matched files
either use retrospective/forbidden framing or (for the 12 repaired files)
now quote the retired claim only inside single-backtick retrospective
prose, never as a live bold/checkmarked claim.
