---
id: rte-branch-integration-audit-2026-04-23
title: RTE Branch Integration Audit 2026-04-23
type: reference
owner: codex
date: 2026-04-23
status: complete
author: '@hu3mann'
last_review: '2026-04-23'
next_review: '2026-07-22'
prelude: Evidence-backed classification of RTE-related branches and bounded pre-audit staging integration.
---
# RTE Branch Integration Audit 2026-04-23

**Task packet**: `TP-DMX-RTEINT-001`
**Execution branch**: `codex/rte-integration-staging-audit`
**Execution date**: `2026-04-23`

## Scope

This packet refreshed current git and PR authority for RTE-related lines, classified each line by observed graph and diff evidence, and integrated only the still-current bounded runtime delta required to make the staging branch suitable for the GPT-5.4 Pro pre-live audit.

It did **not** merge any branch into `main` directly.

## Authority Used

Observed directly during this packet:

- repo root resolves to `/Users/hue/code/dopemux-mvp`
- `.dopetaskroot` exists
- `origin` matches `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- repo-hygiene survivor reports:
  - `docs/05-audit-reports/repo-branch-worktree-cleanup-phase2.md`
  - `proof/repo-branch-worktree-cleanup-phase2.proof.json`
  - `docs/05-audit-reports/repo-branch-worktree-cleanup-phase3.md`
  - `proof/repo-branch-worktree-cleanup-phase3.proof.json`
- current git graph, `git cherry`, `git diff --stat`, and `gh pr list --state all`
- runtime code and tests under `services/repo-truth-extractor/` and `src/dopemux/commands/`

Drift observed:

- the truth-doc paths named in `AGENTS.md` (`TRUTH_SYSTEMS.md`, `TRUTH_CANONICALS.md`, `TRUTH_GAPS.md`, `SYSTEM_RepoTruthExtractor.md`, `TRUTH_INTERFACES.md`, `PAL_EXECUTION_RULES.md`) were not present in this checkout at the expected paths
- classification therefore fell back to runtime code, tests, git graph, and PR state as the active authority set

## Branch Classification

### Already merged / patch-equivalent / no re-integration

| Branch | Current PR state | Evidence | Classification | Action |
| --- | --- | --- | --- | --- |
| `tp/rte-full-run-hygiene-and-launch-readiness` | PR `#461` merged on `2026-04-17` | `git cherry -v origin/main` shows all runtime-bearing commits as `-`; only `3af380e42` remains `+` and is CI-only | merged with non-runtime tail | exclude CI tail |
| `codex/rte-seam-extraction-foundation-v2` | PR `#444` merged on `2026-04-13` | `git cherry -v origin/main` shows the seam extraction/runtime commits as `-` | already merged / superseded on main | exclude |
| `codex/rte-intelligence-routing-proof` | PR `#451` merged on `2026-04-15` | `git cherry -v origin/main` shows all commits as `-` | already merged | exclude |
| `extractor/prompt-governance-gtm` | PR `#435` merged on `2026-04-13` | `git cherry -v origin/main` shows all prompt-governance commits as `-` | already landed on main despite non-main original base | exclude |

### Proof-only / mixed / out-of-scope lines

| Branch | Current PR state | Evidence | Classification | Action |
| --- | --- | --- | --- | --- |
| `packet/rte-07-post-v1-deferred` | PR `#440` merged on `2026-04-13` | multiple merge bases, mixed docs/prompt/workflow stack, not a bounded runtime line | mixed branch | exclude |
| `codex/rte-adapter-smoke` | PR `#437` closed-unmerged on `2026-04-13` | only `smoke_test_integration.py` and `src/dopemux/adhd/rte_adapter.py`; not canonical RTE runtime authority | reference-only / other plane | exclude |
| `codex/rte-benchmark-r1-first-campaign` | no PR proven in this packet | mixed RTE + Serena + CLI diff; not a bounded mergeable runtime line | mixed branch / incomplete | exclude wholesale |
| `feat/rte-structured-outputs-all-providers` | merged line includes current `main` commit `b241d427b` | wide structured-output stack; not replayed wholesale in this packet | divergent mixed stack | exclude wholesale |

### Branch families with overlapping prescan/runtime work

| Branch / family | Current PR state | Evidence | Classification | Action |
| --- | --- | --- | --- | --- |
| `feat/rte-v5-full-prescan-integration` | PR `#464` merged on `2026-04-21` | `main` already exposes Stage 0 flags and `run_integrated_prescan_stage`; raw cherry-pick conflicted across current runner and CLI surfaces | merged line with stale non-ancestor head | do not replay whole commit |
| `tp/serena-audit-runtime-io-tools`, `tp/serena-runtime-fix` | no independent PR; both point at `76dfeb6e2` | alias heads for the `feat/rte-v5-full-prescan-integration` commit | alias / duplicate line | exclude |
| `feat/rte-v5-prescan-contract-unification` | PR `#470` closed-unmerged on `2026-04-18` | `main` already contains `candidate_routes`, `ExecutionEvidence`, `RoutingExhausted`, `prescan_llm_attempts.json`, and `test_prescan_hardening.py`; raw cherry-pick still conflicted across engine/grok/models/provider catalog | closed-unmerged, semantically overlapped, no isolated missing delta proven | exclude wholesale |
| `tp/serena-upstream-contract-diff` | no independent PR; points at `bf3a9244d` | alias head for `feat/rte-v5-prescan-contract-unification` | alias / duplicate line | exclude |
| `feat/rte-prescan-first-live-hardening` | PR `#467` closed-unmerged on `2026-04-22` | `main` already contains most hardening surfaces and `test_prescan_hardening.py`; missing `test_prescan_online_gate.py` alone did not prove a required runtime delta | partially overlapped / incomplete line | exclude wholesale |
| `feat/rte-prescan-stage0-live-lane-proving` | PR `#480` merged on `2026-04-22` | targeted validation on clean staging branch failed on `test_prescan_live_lane.py` because `prescan_live_lane_success.json` was not written and non-batch runs still bypassed attempt evidence | still-current bounded delta survives on this line | integrate bounded behavior only |

## Integrated Delta

The packet did **not** replay any whole historical branch.

Raw cherry-pick attempts against the older prescan commits conflicted with the current `main` line on the canonical Stage 0 surfaces. That made full commit replay non-localized and therefore fail-closed for this packet.

Instead, this packet integrated the smallest still-current runtime delta proven by the failing targeted test:

1. add `write_live_lane_success_artifact(...)` to `services/repo-truth-extractor/lib/prescan/provider_catalog.py`
2. record `selected_live_routes` in Stage 0 metadata
3. write `prescan_live_lane_success.json` when an authorized live lane is selected
4. route non-batch live prescan runs through `run_passes(...)` instead of forcing the batched path

During validation, this packet also found a current `main` blocker unrelated to the preserved branch survivors but still inside RTE scope:

- `services/repo-truth-extractor/run_extraction_v5.py` had an `IndentationError` at line `11083`
- `git blame` traced the malformed indentation to commit `b241d427b` on `2026-04-23`
- the staging branch fixes that indentation so the audit target compiles and the targeted operator-safety suite can run

## Validation

### Git / repo identity

Observed during execution:

- `git rev-parse --show-toplevel`
- `test -f .dopetaskroot`
- `git remote -v`
- `git branch --show-current`
- `git status --short --branch`
- `git worktree list --porcelain`
- `git branch -vv`

### Branch / PR refresh

Observed during execution:

- `gh auth status`
- `gh pr list --state all --limit 200 --json ...`
- `git merge-base --is-ancestor ... origin/main`
- `git cherry -v origin/main <branch>`
- `git diff --stat origin/main...<branch>`

### Runtime validation on staging branch

`python -m py_compile services/repo-truth-extractor/lib/prescan/engine.py services/repo-truth-extractor/lib/prescan/provider_catalog.py services/repo-truth-extractor/run_extraction_v5.py`

Passed after the `run_extraction_v5.py` indentation repair.

`uv run --with pytest python -m pytest -q services/repo-truth-extractor/tests/test_prescan_hardening.py services/repo-truth-extractor/tests/test_prescan_live_lane.py services/repo-truth-extractor/tests/test_prescan_provider_catalog.py services/repo-truth-extractor/tests/test_run_extraction_v5_operator_safety.py`

Final result: passed.

Important intermediate evidence:

- first run on clean staging branch failed in `test_prescan_live_lane.py::test_authorized_live_lane_writes_success_artifact_and_uses_selected_route`
- a broader follow-up also exposed the `run_extraction_v5.py` syntax blocker already present on `main`
- after the bounded Stage 0 patch and the indentation repair, the same targeted suite passed

## Result

The staging branch now reflects the intended most-up-to-date RTE implementation for the bounded pre-audit scope covered by this packet:

- no broad historical branch replay was justified
- the only still-current missing survivor-branch behavior that was concretely proven has been integrated
- the current mainline syntax blocker in `run_extraction_v5.py` has been repaired on the staging branch
- excluded branches remain explicitly classified rather than silently normalized into the staging line

## Residual Risk

- The absent truth-doc paths referenced by `AGENTS.md` remain documentation drift.
- Several historical prescan branches still differ from `main`, but this packet did not prove any additional bounded missing delta beyond the live-lane success/evidence path.
- Validation was intentionally narrow. No full live-provider end-to-end run was executed in this packet.
