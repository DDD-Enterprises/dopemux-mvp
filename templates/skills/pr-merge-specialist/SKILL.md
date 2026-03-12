---
name: pr-merge-specialist
description: Reusable Unix-first PR queue specialist with explicit phase APIs, schema-validated policy, honest dry-runs, resumable artifacts, and rebase-first merge safety rails.
---

# PR Merge Specialist

Use this skill when we need to inspect or drain many open PRs with explicit blockers, policy-backed validation, review-thread handling, and rebase-first merge orchestration.

## Platforms

Supported in this version:
- macOS
- Linux

Not supported in this version:
- Windows native

## Prerequisites

- `git`
- `gh` with a valid authenticated session
- `python`
- `pre-commit` when the active policy requires it
- A clean repo root for execute-mode runs unless `--allow-dirty` is explicitly set

## Command Model

```bash
PYTHONPATH=templates/skills/pr-merge-specialist/scripts \
python3 -m dopemux_pr_merge_specialist.cli preflight --out-dir proof/pr_merge

PYTHONPATH=templates/skills/pr-merge-specialist/scripts \
python3 -m dopemux_pr_merge_specialist.cli queue-scan --strategy hybrid --out-dir proof/pr_merge

PYTHONPATH=templates/skills/pr-merge-specialist/scripts \
python3 -m dopemux_pr_merge_specialist.cli pr-plan --id 205 --out-dir proof/pr_merge

PYTHONPATH=templates/skills/pr-merge-specialist/scripts \
python3 -m dopemux_pr_merge_specialist.cli pr-apply --id 205 --execute --out-dir proof/pr_merge

PYTHONPATH=templates/skills/pr-merge-specialist/scripts \
python3 -m dopemux_pr_merge_specialist.cli pr-merge --id 205 --execute --out-dir proof/pr_merge

PYTHONPATH=templates/skills/pr-merge-specialist/scripts \
python3 -m dopemux_pr_merge_specialist.cli queue-drain --execute --strategy hybrid --prioritize 190,191 --out-dir proof/pr_merge
```

## Operating Rules

1. Dry-run is the default; `--execute` is required for repo or GitHub mutations.
2. Dry-run does not claim local validation passed. Validation is reported as `not_executed` unless it truly ran.
3. Rebase-first is mandatory for base updates and default merge selection.
4. `queue-drain` orchestrates the same internal phases used by `queue-scan`, `pr-plan`, `pr-apply`, and `pr-merge`.
5. Active unresolved review threads block merge.
6. Outdated or resolution-signaled threads may auto-resolve only after green verification and no newer objection.
7. Conflict handling must be semantic and evidence-backed; blanket `-X ours/-X theirs` strategies are disallowed.
8. Execute-mode runs acquire a single-worker queue lock.
9. Execute-mode runs fail closed on dirty worktrees unless `--allow-dirty` is used.
10. Repo-specific validation commands belong in policy, not in the engine.

## Artifact Contract

Each run writes versioned artifacts with policy and tool metadata. Expected artifacts include:

- `RUN_MANIFEST.json`
- `PRECHECK.json`
- `ENVIRONMENT.json`
- `QUEUE_SNAPSHOT.json`
- `ORDERING_PLAN.json`
- `POLICY_EFFECTIVE.json`
- `CHECK_WAIT_REPORT.json`
- `BASE_REBASE_UPDATES.json`
- `RUN_SUMMARY.md`
- queue artifacts under `queue/`
- per-PR state and phase artifacts under `pr/<id>/`

## Safety Boundaries

- The engine is reusable, but the active repo policy remains authoritative.
- Merge readiness comes from explicit truth precedence:
  1. effective policy
  2. GitHub protection and review state
  3. local validation on the exact SHA
  4. local rebase or merge simulation
  5. heuristics
- Sensitive file classes should remain blocked from auto-apply or auto-merge unless policy permits them.
