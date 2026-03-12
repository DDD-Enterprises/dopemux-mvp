---
name: pr-merge-specialist
description: Deterministic PR queue specialist for rebase-first queue draining with comment/thread resolution, conflict-deep analysis, and fail-closed validation gates.
---

# PR Merge Specialist

Use this skill to drain PR queues safely with a dry-run-first workflow.

## Quick Start

```bash
PYTHONPATH=templates/skills/pr-merge-specialist/scripts \
python3 -m dopemux_pr_merge_specialist.cli queue-scan --strategy hybrid --out-dir proof/pr_merge

PYTHONPATH=templates/skills/pr-merge-specialist/scripts \
python3 -m dopemux_pr_merge_specialist.cli queue-drain --strategy hybrid --max-prs 0 --out-dir proof/pr_merge

PYTHONPATH=templates/skills/pr-merge-specialist/scripts \
python3 -m dopemux_pr_merge_specialist.cli queue-drain --execute --strategy hybrid --max-prs 0 --out-dir proof/pr_merge
```

## Execution Rules

1. Dry-run is the default; pass `--execute` for remote mutations.
2. Rebase-first policy is mandatory for branch updates and merge attempts.
3. Unresolved active review threads block merge.
4. Outdated threads may auto-resolve only after green verification and no newer objections.
5. Conflict handling must be semantic and evidence-backed; no blanket `-X ours/-X theirs` strategies.
6. Validation is fail-closed:
   - `pre-commit run --all-files`
   - `python scripts/docs_frontmatter_guard.py --fix`
   - `python scripts/docs_validator.py`
   - `python scripts/check_docs_hygiene.py --check --all-files`
   - `python scripts/check_docs_filename_hygiene.py --check --all-files`
   - `python scripts/check_root_hygiene.py`

## Output Contract

Each queue-drain run writes:

- `QUEUE_SNAPSHOT.json`
- `ORDERING_PLAN.json`
- `BASE_REBASE_UPDATES.json`
- `QUEUE_REPORT.json`
- Per PR:
  - `INTAKE.json`
  - `REVIEW_THREADS.json`
  - `THREAD_DISPOSITIONS.json`
  - `VALIDATION_REPORT.md`
  - `MERGE_DECISION.json`
  - `RESULT.json`
  - `CONFLICT_ANALYSIS.md` (when conflicts occur)

All artifacts are written under the run directory in `proof/pr_merge/` unless overridden.
