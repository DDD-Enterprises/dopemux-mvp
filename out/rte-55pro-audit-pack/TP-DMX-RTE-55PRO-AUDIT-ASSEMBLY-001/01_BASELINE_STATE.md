# Baseline State

## Repository

- OBSERVED repo worktree path: `~/code/dopemux-mvp/.worktrees/tp-dmx-rte-55pro-audit-assembly-001`
- OBSERVED primary checkout path during preflight: `~/code/dopemux-mvp`
- OBSERVED remotes: `origin` and `mvp` both point to `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- OBSERVED current branch: `codex/tp-dmx-rte-55pro-audit-assembly-001`
- OBSERVED starting HEAD: `a4214ca5bf431e1b59791661e2b664a6cd24c1da`
- OBSERVED base branch: `main` because `origin/HEAD` resolves to `origin/main`
- OBSERVED marker files in worktree: `.git`, `.dopemux`, `.dopetaskroot`, `.dopetask-pin`, `AGENTS.md`, `pyproject.toml`
- OBSERVED worktree status before writes: clean on `codex/tp-dmx-rte-55pro-audit-assembly-001`
- OBSERVED primary checkout status before worktree creation: `main...origin/main` with untracked `services/genetic_agent/`, `services/session-manager/uv.lock`, and `services/task-orchestrator/dopemux-vscode/package-lock.json`

## Required Authority Files

Present and inspected: `AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`, `docs/03-reference/systems/system-boundaries.md`, `PM_PLANE.md`, `SERVICE_CATALOG.md`, `task-packets/INDEX.md`, the tracked truth docs under `docs/03-reference/truth/`, RTE system docs under `docs/03-reference/systems/repo-truth-extractor/`, and proof contract docs under `docs/03-reference/governance/`.

UNKNOWN or absent at requested root paths: `RULES.md`, `SYSTEM_BOUNDARIES.md`, `TRUTH_SCOPE.md`, `TRUTH_SYSTEMS.md`, `TRUTH_INTERFACES.md`, `TRUTH_DATA_EVENTS.md`, `TRUTH_CANONICALS.md`, `TRUTH_GAPS.md`, `SYSTEM_RepoTruthExtractor.md`, `PAL_EXECUTION_RULES.md`, `PAL_CHAINING_DOCTRINE.md`, `PAL_PACKET_TEMPLATE.md`, `dopetask-cannonical-spec.json`, `dopetask-canonical-spec.json`.

OBSERVED schema path used for task-packet validation: `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`. The requested root spellings `dopetask-cannonical-spec.json` and `dopetask-canonical-spec.json` were not present at repo root.

## Recent RTE PR Evidence

OBSERVED via `gh pr list` and git log:

- PR #617 merged on 2026-05-14: `docs(rte): canonicalize rte operator path`
- PR #616 merged on 2026-05-14: `fix(rte): ground strict attestations in runtime evidence`
- PR #615 merged on 2026-05-14: `fix(rte): wire strict batch response_format`
- PR #614 merged on 2026-05-14: `fix(rte): repair batch result and strict handling`
- PR #606 merged on 2026-05-10: `fix(rte): exclude generated artifacts from prescan`
- PR #605 merged on 2026-05-10: `fix(rte): gate legacy v3 execution and reject unknown pipeline versions`
- PR #603 merged on 2026-05-10: `fix(rte): make introspection commands readonly`

## Current Audit Status

CLAIMED by `proof/rte-gemini-deep-pal-audit-2026-04-23.proof.json`: verdict `CONDITIONAL_GO` for a Gemini PAL audit of RTE across UX, prompts, routing, sidefill, repair, validator gates, and operator readiness.

UNKNOWN: no current GitHub PR explicitly matching `Opus audit RTE repo-truth-extractor` was found beyond unrelated results. A Phase S file named `services/repo-truth-extractor/PHASE_S_SYSTEM_TRUTHS_GPT52.md` claims `Opus (2 runs)`, but this pack did not prove that file as current audit authority.
