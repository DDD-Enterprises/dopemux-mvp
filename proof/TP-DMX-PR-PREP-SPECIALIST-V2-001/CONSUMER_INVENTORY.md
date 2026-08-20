# Consumer Inventory — TP-DMX-PR-PREP-SPECIALIST-V2-001

Search: `rg -n "pr-prep-specialist|PR-PREP-SPECIALIST|INSPECT_BRANCH_STATE|GO_DRAFT_FIRST|GO_DIRECT|MERGE_READY|BRANCH_STATE\.json|PR_HANDOFF_BUNDLE\.json" docs .claude .github src tools scripts tests`
(worktrees and `docs/archive/` excluded from classification below; both left untouched per invariant.)

## CANONICAL (this packet's ruling)
- `docs/03-reference/pr-pipeline/prep/**`
- `docs/03-reference/pr-pipeline/merge/**`

## COMPATIBILITY (this packet's ruling)
- `docs/pr_prep/**`
- `docs/pr_merge/**`

## DOWNSTREAM (real runtime code, independent of the above two doc trees)
- `src/dopemux_pr_merge_specialist/*.py` (mirrored under `.claude/skills/pr-merge-specialist/scripts/` and `.github/skills/pr-merge-specialist/scripts/`)
- `tests/pr_merge_specialist/*.py`, `tests/unit/test_pr_merge_specialist_merge_strategy.py`

  This is the actual wired `pr-merge-specialist` implementation (WSEMT-scored
  merge-train orchestration). Verified by direct grep: it does **not**
  reference `source_skill`, `handoff_id`, or any PRPS handoff-bundle field
  from either doc tree. Its own `PRState.MERGE_READY = "merge_ready"` is an
  independent internal lifecycle enum, not the PRPS-side `MERGE_READY`
  next-step token either doc tree's contract forbids PR Prep from emitting.
  Confirmed non-consumer of both `docs/pr_prep/` and
  `docs/03-reference/pr-pipeline/prep/` — this packet does not touch it.

## GENERATED / DERIVED (reports, not authority)
- `reports/docs-hygiene/audit.json`, `reports/docs-hygiene/filename_audit.json`
  — docs-hygiene tooling output; references paths, carries no behavioral
  contract, no duplicate-resolution verdict between the two trees.

## HISTORICAL (excluded, not touched)
- `docs/archive/unclassified-top-level/pr_prep/**`, `docs/archive/unclassified-top-level/governance/**`
- `docs/04-explanation/root-relocated/*-summary.md` (relocated-root historical summaries, incidental keyword hits)
- `.claude/worktrees/**`, `.github/skills/**` mirror of `.claude/skills/**` (build/CI mirror, not a distinct source of truth)

## UNKNOWN
- none remaining after this pass.

## Open-PR overlap
`gh pr list --state open --limit 200` (48 open PRs) and a title/path search
for `pr_prep`, `pr-pipeline`, `pr-prep-specialist` found **zero** open PRs
touching either doc tree or the `src/dopemux_pr_merge_specialist` package.
No CONFLICTING or materially UNKNOWN overlap.
