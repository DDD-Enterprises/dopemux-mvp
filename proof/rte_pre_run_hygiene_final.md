# RTE Pre-Run Hygiene Final

Date: 2026-04-23
Packet: `DMX-RTE-PRE-RUN-HYGIENE-GEMINI-001`
Repo: `/Users/hue/code/dopemux-mvp`
Branch: `audit/rte-pre-run-hygiene-gemini-001`

## Change Summary

This pass did not clean architecture or normalize repo truth. It established a preserve-first hygiene boundary, recorded protected surfaces, classified working-tree and ignored-state contamination, defined a bounded first-pass RTE input recommendation, and applied only narrow transient cleanup plus tracked-drift isolation.

Applied hygiene actions:

- stashed `AGENTS.md` twice as unrelated tracked drift
- deleted repo-local `.DS_Store`
- deleted repo-local `__pycache__/`
- deleted repo-local `*.pyc` and `*.pyo`
- deleted `task-packets/.TP-WAVE7-RTE-UI-DESIGN-2026-04-21A.md.swp`

Non-actions:

- preserved `proof/`, `reports/`, truth docs, RTE doctor/latest/runs evidence, and ambiguous hidden local trees in place
- treated ambiguous heavy trees as exclusion-only candidates for the first-pass run input

## Authority Used

- runtime truth:
  - `services/repo-truth-extractor/run_extraction_v5.py`
  - `services/repo-truth-extractor/rte_config.py`
  - `services/repo-truth-extractor/rte_output_layout.py`
  - `services/repo-truth-extractor/reporting.py`
- repo operator docs:
  - `AGENTS.md`
  - `PROJECT.md`
  - `ARCHITECTURE.md`
- derived truth and boundary docs:
  - `docs/03-reference/truth/truth-canonicals.md`
  - `docs/03-reference/truth/truth-gaps.md`
  - `docs/03-reference/truth/truth-scope.md`
  - `docs/03-reference/systems/system-boundaries.md`
  - `docs/03-reference/planes/pm/pm-plane.md`

## Validation Performed

- repo inspection:
  - `git status --short`
  - `git status --short --ignored`
  - `git diff --name-only`
  - `git diff --stat`
  - `git ls-files --others --exclude-standard`
  - `git check-ignore -v ...`
  - `find` inventories for `proof`, `extraction`, `tmp`, `docs`
  - bounded file count:
    - `find . -maxdepth 4 \( -path './.git' -o -path './.venv' -o -path './.dopetask_venv' \) -prune -o -type f | wc -l`
    - result after hygiene snapshot: `5406`
- post-cleanup transient checks outside excluded env roots:
  - `.DS_Store`: `0`
  - `__pycache__`: `0`
  - `*.pyc`, `*.pyo`, `*.swp`: `0`
- PAL layers executed with recorded gaps:
  - `analyze:gpt-4.1`
  - `thinkdeep:gemini-2.5-pro` after requested `gemini-3-pro-preview` was unavailable
  - `planner:gpt-4.1`
  - `consensus` requested with `gpt-4.1` and `claude-opus-4.5`, but both failed due quota/model availability
  - `codereview:gpt-5-codex` after requested `gpt-5.1-codex` was unavailable
  - `precommit:gpt-5-codex` after requested `gpt-5.1-codex` was unavailable
  - `challenge` tool invocations recorded as reassessment prompts

## Remaining Uncertainty / Drift / Risk

- `tracer` was requested in the packet but is not available in the current PAL toolset.
- `gpt-4.1` hit quota limits during analysis/consensus.
- `claude-opus-4.5` and `gemini-3-pro-preview` were unavailable with the active providers.
- one cleanup command ran wider than intended into ignored cache trees because of `find` precedence; observed effect stayed limited to ignored transient caches/bytecode, but this is still a real execution defect
- `AGENTS.md` reappeared as unrelated local drift during validation after being stashed, which means commit or run readiness depends on isolating it again immediately before the final operator action
- ambiguous hidden local trees remain exclusion recommendations only; their truth value was not collapsed into “irrelevant”

## Run-Readiness Recommendation

Repo is ready for a bounded first-pass RTE run if `AGENTS.md` is isolated again immediately before the run and the following boundary is used:

- keep in scope:
  - runtime code/config/tests
  - truth docs and derived boundary docs
  - `proof/`
  - `reports/`
  - extraction doctor/latest/runs evidence
- exclude from first-pass traversal only:
  - `.claude/`
  - `.dopemux/`
  - `.conport/`
  - `.venv/`
  - `.dopetask_venv/`
  - `.pytest_cache/`
  - `.uv-cache/`
  - `.worktrees/`
  - `build/`
  - `node_modules/`
  - transient cache/editor artifacts
