# RTE Pre-Run Hygiene Stage 3 Input Boundary

Date: 2026-04-23

## Goal

Define a bounded first-pass RTE input set that reduces scan cost without hiding canonical runtime truth, launch evidence, or split-authority signals.

## Keep In Scope

- runtime code under `src/` and `services/`
- runtime wrappers under `scripts/`
- tests under `tests/`
- compose, registry, routing, and profile/config surfaces
- `PROJECT.md`, `ARCHITECTURE.md`, `AGENTS.md`
- `docs/03-reference/truth/**`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/03-reference/planes/pm/pm-plane.md`
- `proof/**`
- `reports/**`
- `extraction/doctor/**`
- `extraction/v4/doctor/**`
- `extraction/repo-truth-extractor/v5/doctor/**`
- `extraction/repo-truth-extractor/v5/runs/**`
- `extraction/repo-truth-extractor/v5/latest_run_id.txt`

## Exclude From First-Pass Input

These exclusions are run-boundary controls only. They are not deletion approvals.

- `.claude/**`
- `.dopemux/**`
- `.conport/**`
- `.venv/**`
- `.dopetask_venv/**`
- `.pytest_cache/**`
- `.uv-cache/**`
- `.worktrees/**`
- `build/**`
- `services/conport_kg_ui/node_modules/**`
- `services/conport_kg_ui/dist/**`
- `**/__pycache__/**`
- `**/*.pyc`
- `**/*.pyo`
- `**/*.swp`

## Special Handling

- `tmp/**`
  - exclude from first-pass input unless a specific upcoming run needs a known temp artifact
- `task-packets/**`
  - keep in scope generally
  - exclude editor residue only

## Boundary Rationale

- keep operator evidence and drift evidence visible
- cut obviously derived/cache-only surfaces first
- do not hide contradictions by excluding messy but potentially relevant proof/report trees
