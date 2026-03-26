# Dev Integration Shortlist - 2026-03-20

## Purpose

This shortlist narrows the open PR queue to the branches that are defensible candidates for staging through `dev`.

It is derived from:
- open PR metadata from GitHub
- remote-ref ancestry checks against local `dev`
- changed-file blast radius
- duplicate-family overlap

This is still analysis only. No PRs were merged, rebased, retargeted, or closed.

## Preconditions Before Any Integration

Current local state blocks safe execution:

- local `dev` is ahead of `upstream/dev`
- local worktree is dirty
- `gh` CLI is not installed

Before mutating the queue:

1. clean or park local work
2. sync `dev` with `upstream/dev`
3. decide whether `dev` is now the staging branch for selected `main` PRs
4. only then begin branch-by-branch integration

## Ranked Shortlist

### Tier 0 - Resolve First

#### PR #234 - `feat/branding-expansion -> dev`

Status:
- only open PR already targeting `dev`
- not fully contained in local `dev`
- local `dev` already contains an older merge of this branch

Evidence:
- local `dev` contains merge commit `69d4e4626`
- upstream PR branch has newer commit `ed98a511a`
- GitHub file list shows broad docs + workflow + compose churn, including:
  - `compose.adhd-stack.yml`
  - `QUICK_START.md`
  - docs indexes
  - workflow personas and profile config

Recommendation:
- do not merge anything else into `dev` until `#234` is reconciled
- either:
  - merge the new branding delta cleanly into `dev`, or
  - close `#234` and open a fresh branch from current `dev`

Risk:
- high, because it modifies canonical operator surfaces and the compose contract while `dev` already diverged

### Tier 1 - Best Candidates To Stage Through `dev`

These are the strongest candidates if you want `dev` to act as a true integration branch for selected `main` PRs.

#### PR #218 - `jules-fix-naive-ai-completion-detection-15157724221306005655 -> main`

Evidence:
- 1 changed file
- file: `services/session-manager/src/agent_spawner.py`
- not contained in `dev`
- narrower than duplicate `#206`

Recommendation:
- shortlist this one
- prefer it over `#206`

Risk:
- low

#### PR #215 - `performance-optimize-dict-mapping-db-rows-15519291369247728771 -> main`

Evidence:
- 1 changed file
- file: `src/conport/memory_server.py`
- focused performance change
- not contained in `dev`

Recommendation:
- shortlist this one for isolated validation

Risk:
- low to medium

#### PR #233 - `palette-micro-ux-enhancement-task-duration-a11y-fix-1218073056001778443 -> main`

Evidence:
- 4 changed files
- UI-only blast radius
- latest and narrowest of the not-yet-integrated Palette branches
- touches:
  - `ui-dashboard/src/App.tsx`
  - `ui-dashboard/src/components/TaskSequencer.tsx`
  - accessibility test

Recommendation:
- if one Palette branch is staged through `dev`, use `#233` as the candidate
- do not stage the other Palette variants in parallel

Risk:
- medium, because it is a duplicate family winner rather than a uniquely isolated branch

### Tier 2 - Integrate Only After Tier 1 Is Stable

#### PR #216 - `dependabot/npm_and_yarn/npm_and_yarn-5441a9a3ec -> main`

Evidence:
- 3 lockfile changes
- root `package-lock.json`
- `ui-dashboard/package-lock.json`
- `ui-dashboard/pnpm-lock.yaml`

Recommendation:
- stage after app-level changes if dependency refresh is still needed

Risk:
- medium, because lockfile churn can complicate the selected Palette branch

#### PR #210 - `fix/v5-phase-recovery-hardening-0001 -> main`

Evidence:
- 32 files
- mostly `services/repo-truth-extractor/**` and extraction proofs
- substantial contract and model-map churn

Recommendation:
- stage only if extraction work is actively being validated in `dev`
- otherwise keep on `main`

Risk:
- medium to high

#### PR #227 - `feat/core-cli-updates -> main`

Evidence:
- 86 files under `src/**`
- broad CLI surface changes

Recommendation:
- stage only if `dev` is explicitly becoming the integration branch for CLI work

Risk:
- medium to high

### Tier 3 - Keep On `main` Or Inspect Separately

#### PR #223 - `feat/pr-merge-refactor -> main`

Evidence:
- 63 files
- broad changes across `src/dopemux_pr_merge_specialist/**` and Claude integration

Recommendation:
- keep separate until the merge workflow itself is stable

Risk:
- high

#### PR #225 - `feat/install-overhaul -> main`

Evidence:
- 41 files
- changes compose/install/operator surfaces

Recommendation:
- keep on `main` unless installer work is explicitly part of `dev` scope

Risk:
- high

#### PR #212 - `feat/tp-authority-boundaries-and-adr-set -> main`

Evidence:
- 200 files
- docs, services, reports, proofs

Recommendation:
- keep separate

Risk:
- high

#### PR #213 - `feat/extraction-wizard-cli -> main`

Evidence:
- 270 files
- wide repo churn across services, docs, reports, extraction, and proofs

Recommendation:
- keep separate

Risk:
- very high

#### PR #214 - `codex/main-drain-20260314 -> main`

Evidence:
- 245 files
- broad mixed branch across reports, services, docs, proofs, extraction

Recommendation:
- inspect independently; do not stage through `dev` blindly

Risk:
- very high

#### PR #205 - `codex/feat-pr-merge-specialist-v2 -> main`

Evidence:
- 46 files
- directly changes queue tooling, docs, tests, and templates

Recommendation:
- keep separate while deciding queue policy

Risk:
- high

## Explicit Exclusions

### Already In `dev`

Do not re-stage these:

- `#228` `dev -> main`
- `#224` `feat/v5-truth-extractor`
- `#222` Palette variant
- `#221` Dependabot PAL pyasn1 bump
- `#220` Palette variant
- `#219` Palette variant

### Duplicate Families To Collapse Before Integration

Do not stage all of these into `dev`:

- Palette family: `#233 #232 #230 #222 #220 #219 #217 #209`
- Jules family: `#218 #206`

Specific recommendation:

- choose `#233` as the only Palette candidate
- choose `#218` instead of `#206`

### Branches To Keep Off `dev` For Now

- `#206` because it carries 1069 changed files against the same topic covered narrowly by `#218`
- `#226` because it changes 983 files, mostly docs, and should not be bulk-imported
- `#209` because it mixes Palette UI work with unrelated extractor and service changes

## Proposed Integration Order

If you want me to execute the staging sequence later, the order should be:

1. resolve `#234`
2. shortlist `#218`
3. shortlist `#215`
4. pick `#233` as the only Palette candidate
5. optionally add `#216`
6. reconsider `#210` and `#227` only after the above are stable

## Bottom Line

The queue should not be integrated wholesale into `dev`.

The defensible shortlist is:

- required first: `#234`
- best next candidates: `#218`, `#215`, `#233`
- optional second wave: `#216`
- defer unless policy changes: `#210`, `#227`
