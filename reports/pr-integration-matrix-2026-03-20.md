# PR Integration Matrix - 2026-03-20

## Scope

This report classifies all open GitHub pull requests for `DDD-Enterprises/dopemux-mvp` against the current local `dev` branch.

Authority order used:
1. GitHub open PR metadata from the repository API
2. Fetched remote refs from `upstream/*`
3. Local git ancestry checks against `dev`

This is an analysis artifact. No merge actions were performed.

## Local Preconditions

- Current branch: `dev`
- Local `dev` state: `ahead 12` vs `upstream/dev`
- Local worktree: dirty
- `gh` CLI: not installed in this shell

These conditions block a safe queue-drain execute run from this checkout.

## Classification Rules

- `already_in_dev`: PR head is reachable from local `dev`
- `not_in_dev`: PR head is not reachable from local `dev`
- `dev_target_drift`: PR targets `dev` but local `dev` already contains an older merge or divergent integration
- `duplicate_family`: multiple open PRs touch the same feature surface with overlapping intent
- `main_only_candidate`: PR currently targets `main`; integrating to `dev` would require an explicit strategy change

## Summary

- Total open PRs inspected: 20
- Targets `dev`: 1
- Targets `main`: 19
- Already contained in local `dev`: 6
- Not contained in local `dev`: 14
- Clear duplicate families:
  - Palette task sequencer / duration / accessibility: `#233 #232 #230 #222 #220 #219 #217 #209`
  - Jules AI completion detection: `#218 #206`

## Decision Matrix

| PR | Base | Head | In local `dev` | Recommendation | Evidence |
| --- | --- | --- | --- | --- | --- |
| #234 | `dev` | `feat/branding-expansion` | No | Reconcile first, then merge or close stale branch | `dev` already contains merge commit `69d4e4626`, but `upstream/feat/branding-expansion` has newer commit `ed98a511a` not in `dev` |
| #233 | `main` | `palette-micro-ux-enhancement-task-duration-a11y-fix-1218073056001778443` | No | Do not bulk-integrate to `dev`; choose one Palette winner | Same file family as `#232/#230/#222/#220/#219/#217/#209`; touches `ui-dashboard/src/App.tsx`, `TaskSequencer.tsx`, accessibility test |
| #232 | `main` | `palette-ux-duration-a11y-12288626049886972970` | No | Do not bulk-integrate to `dev`; choose one Palette winner | Same file family as above; includes `pnpm-lock.yaml` |
| #230 | `main` | `palette/task-sequencer-ux-improvement-12700409259532471563` | No | Do not bulk-integrate to `dev`; choose one Palette winner | Same file family as above |
| #228 | `main` | `dev` | Yes | Treat as the current integration vehicle from `dev` to `main` | PR head is `dev`; local `dev` contains it by definition |
| #227 | `main` | `feat/core-cli-updates` | No | Keep on `main` queue unless you explicitly adopt `dev` as staging for main-target PRs | Distinct branch, not contained in `dev` |
| #226 | `main` | `docs/master-reorg` | No | Keep on `main` queue unless docs staging through `dev` is now policy | Distinct branch, not contained in `dev` |
| #225 | `main` | `feat/install-overhaul` | No | Keep on `main` queue unless compose/installer work is intentionally staged through `dev` | Distinct branch, not contained in `dev` |
| #224 | `main` | `feat/v5-truth-extractor` | Yes | Do not merge separately into `dev`; already present there | PR head is ancestor of local `dev` |
| #223 | `main` | `feat/pr-merge-refactor` | No | Keep separate; not safe to bulk-integrate while `dev` is dirty and ahead | Distinct branch, not contained in `dev` |
| #222 | `main` | `palette/task-sequencer-remaining-duration-9048409209723803455` | Yes | Mark superseded for `dev`; already integrated there | PR head is ancestor of local `dev`; overlaps Palette family |
| #221 | `main` | `dependabot/uv/docker/mcp-servers-source/pal/pal-mcp-server/uv-5abb2dfbbd` | Yes | Do not re-integrate to `dev`; already present there | PR head is ancestor of local `dev` |
| #220 | `main` | `palette/task-duration-ux-12491915458240005406` | Yes | Mark superseded for `dev`; already integrated there | PR head is ancestor of local `dev`; overlaps Palette family |
| #219 | `main` | `palette-task-duration-enhancement-8701576098574772613` | Yes | Mark superseded for `dev`; already integrated there | PR head is ancestor of local `dev`; overlaps Palette family |
| #218 | `main` | `jules-fix-naive-ai-completion-detection-15157724221306005655` | No | Choose between `#218` and `#206`; do not integrate both | Single-file AI completion fix; separate from `#206` broad branch |
| #217 | `main` | `palette-task-sequencer-enhancement-11559017549983090508` | No | Do not bulk-integrate to `dev`; choose one Palette winner | Same file family as Palette set |
| #216 | `main` | `dependabot/npm_and_yarn/npm_and_yarn-5441a9a3ec` | No | Keep on `main` queue unless dependency updates are intentionally staged via `dev` | Distinct branch, not contained in `dev` |
| #215 | `main` | `performance-optimize-dict-mapping-db-rows-15519291369247728771` | No | Keep separate; validate independently before any integration branch work | Distinct branch, not contained in `dev` |
| #214 | `main` | `codex/main-drain-20260314` | No | High-risk integration branch; inspect before any `dev` import | 31 commits ahead of `main`; not contained in `dev` |
| #213 | `main` | `feat/extraction-wizard-cli` | No | Keep separate; branch has diverged materially from local `main` and `dev` | `20 44` left/right count vs `main`; not contained in `dev` |
| #212 | `main` | `feat/tp-authority-boundaries-and-adr-set` | No | Keep separate; doc/authority work should not be bulk-integrated blindly | 18 commits ahead of `main`; not contained in `dev` |
| #210 | `main` | `fix/v5-phase-recovery-hardening-0001` | No | Candidate for targeted cherry-pick only if needed; not bulk integration | 12 commits ahead of `main`; not contained in `dev` |
| #209 | `main` | `palette/task-sequencer-duration-17211128289057214961` | No | Do not bulk-integrate to `dev`; choose one Palette winner | Palette family, plus unrelated files in `redis_pool.py` and `tests/security/test_cors.py` |
| #206 | `main` | `jules/fix-naive-ai-completion-detection-15157724221306005655` | No | Likely superseded by a narrower fix branch; inspect before merging | 1042 changed files vs 1 file in `#218`; same problem theme |
| #205 | `main` | `codex/feat-pr-merge-specialist-v2` | No | Keep separate; do not bulk-integrate while local merge tooling is being modified | 10 commits ahead of `main`; not contained in `dev` |

## Duplicate Families

### Palette task sequencer family

Observed overlap from `git diff --name-only upstream/main...upstream/<branch>`:

- `#233`: `.Jules/palette.md`, `ui-dashboard/src/App.tsx`, `ui-dashboard/src/components/TaskSequencer.tsx`, `ui-dashboard/src/components/__tests__/Accessibility.test.ts`
- `#232`: same core files as `#233` plus `ui-dashboard/pnpm-lock.yaml`
- `#230`: same core files as `#233`
- `#222`: `TaskSequencer.tsx` and accessibility test
- `#220`: `TaskSequencer.tsx` and accessibility test
- `#219`: same core files as `#222` plus `.Jules/palette.md`
- `#217`: same core files as `#222` plus `.Jules/palette.md`
- `#209`: same core UI files plus unrelated `redis_pool.py` and `tests/security/test_cors.py`

Conclusion:
- These are not branch ancestors of each other.
- They are parallel variants over the same UX surface.
- They should not all be integrated to `dev`.
- One branch should be selected as the canonical Palette candidate; the rest should be closed or superseded.

### Jules AI completion family

Observed overlap:

- `#218`: 1 changed file, `services/session-manager/src/agent_spawner.py`
- `#206`: 1042 changed files, including `services/session-manager/src/agent_spawner.py` plus broad repo churn

Conclusion:
- These should not both be integrated to `dev`.
- `#218` is the narrower candidate if the goal is only the agent spawner completion fix.
- `#206` needs explicit justification because it carries broad unrelated changes.

## Recommended Integration Strategy

If the goal is to use `dev` as the integration branch, the defensible order is:

1. Clean local `dev` and sync it with `upstream/dev`.
2. Resolve PR `#234` first, because it is the only open PR already targeting `dev` and it has branch drift.
3. Treat `#228` as the current `dev -> main` integration vehicle.
4. Do not mass-import all `main` PRs into `dev`.
5. For `main` PRs, create an explicit shortlist of candidates to stage through `dev`.
6. Collapse duplicates before any integration:
   - choose one Palette PR
   - choose `#218` or `#206`, not both
7. Re-run mergeability, review-thread, and CI checks on the shortlisted set before any mutation.

## Bottom Line

Based on current repo and PR truth, the answer to "can we integrate all of them to `dev`" is no.

What can be done safely:

- reconcile `#234`
- keep using `#228` as the `dev -> main` path
- choose a small explicit subset of `main` PRs to stage through `dev`
- close or supersede duplicate families before integration
