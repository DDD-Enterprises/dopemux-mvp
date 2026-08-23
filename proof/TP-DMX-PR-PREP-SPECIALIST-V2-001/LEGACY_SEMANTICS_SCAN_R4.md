# Terminal Semantic Census — R4

Scan command (same as R3):

```bash
rg -n 'GO_SUPERVISED_FINAL|SUPERVISED_FINAL_CREATION|CREATE_FINAL_PR|CREATE_READY|CLEAN_CREATE_READY|DRAFT_RECOMMENDED|HIGH_RISK_ESCALATE|MERGE_READY|merge-ready|risk_hint|LOW|MEDIUM|HIGH|mandatory.*7|seven.*artifact|BRANCH_STATE\.json|PR_HANDOFF_BUNDLE\.json' docs/03-reference/pr-pipeline/prep docs/pr_prep
```

Run after the R4 repair of the frozen 19 paths (see `R4_ACTIVE_CONTRADICTION_PATHS.txt`).

## RETIRED_PROSE

Two groups, all retirement-describing prose, no `ACTIVE_CONTRADICTION`:

**R1/R2/R3 allowlist (17 canonical + 17 compat)**: unchanged from the R3
census — `skill-model.md`, `operator-contract.md`, `workflow-sequence.md`,
`deterministic-gate-rules.md`, `go-no-go-criteria.md`,
`handoff-to-prms-contract.md`, `pr-creation-policy.md`,
`high-risk-handoff-rules.md`, `branch-state-schema.md`,
`consensus-gate-rules.md`, `handoff-contract.md`,
`operational-posture-options.md`, `layered-validation-model.md`,
`creation-mode-rules.md`, `pr-drafting-rules.md`, `live-pilot-protocol.md`,
`stash-and-branch-safety-rules.md`.

**R4 frozen 19-path set (9 canonical + 10 compat)**: all 19 files listed in
`R4_ACTIVE_CONTRADICTION_PATHS.txt`, converted this round to deprecation
stubs (canonical) or pointer stubs (compat), all pointing to
`operator-contract.md`. Every remaining match in these files is inside
retirement-framing prose ("previously defined...retired",
"Superseded by...").

## NON_BLOCKING_LOCAL_MEASUREMENT (new category this round)

Same 7 files identified as SUPERVISOR_JUDGMENT in the R3 census, formally
adjudicated against the R4 ruling's five-part test. All pass (namespaced
local scale; not the V2 risk lane; cannot authorize/prohibit PR creation;
cannot determine audit requirement; cannot accept proof or declare
readiness). None edited this round — verified untouched
(`git status --short` empty for all 14 canonical+compat paths).

- `base-branch-detection-rules.md` (+ compat) — base-branch-detection
  confidence grade (`HIGH/MEDIUM/LOW`), not PR risk.
- `obligation-model.md` (+ compat) — obligation severity grade.
- `obligation-severity-rules.md` (+ compat) — per-obligation-type severity
  table.
- `evaluation-model.md` (+ compat) — pilot audit/draft quality bands
  (`HIGH_SIGNAL`, `HIGHLY_USEFUL`, etc.), historical-pilot evaluation
  metric.
- `section-fill-policy.md` (+ compat) — one `HIGH or CRITICAL` gate on
  PR-body section requirement, not creation/merge authority.
- `pilot-case-selection-rules.md` (+ compat) — `PILOT_READY_HIGH_RISK`
  names a historical pilot branch-selection category, not a live decision
  state.
- `operator-review-form.md` (top-level canonical + top-level compat; the
  *distinct* `adapters/vibe/operator-review-form.md` files are in the
  frozen-19 repaired set, not this one) — `Severity of Override:
  INFO|LOW|MEDIUM|HIGH|CRITICAL` grades a human operator's override, not an
  automated creation/risk decision.

No `MISCLASSIFIED_ACTIVE_CONTRADICTION` findings — all 7 independently
re-checked against the five-part test and confirmed non-blocking.

## Envelope-only paths (not in frozen 19, proven byte-unchanged)

`docs/03-reference/pr-pipeline/prep/adapters/vibe/readme.md` and
`docs/pr_prep/adapters/vibe/readme-2.md` — zero legacy-vocabulary matches in
either file (pre-existing), confirmed byte-unchanged via SHA256 (see
`R4_SCOPE_FREEZE.md`) and `git status --short` (empty).

## ACTIVE_CONTRADICTION

None found outside the R1+R2+R3+R4 allowlist.

**`ACTIVE_CONTRADICTION_COUNT = 0`**
