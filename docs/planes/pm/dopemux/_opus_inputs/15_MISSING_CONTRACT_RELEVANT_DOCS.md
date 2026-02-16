---
id: 15_MISSING_CONTRACT_RELEVANT_DOCS
title: 15 Missing Contract Relevant Docs
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: 15 Missing Contract Relevant Docs (explanation) for dopemux documentation
  and developer workflows.
---
# 15_MISSING_CONTRACT_RELEVANT_DOCS

The following documents should be represented in the Opus bundle for a complete contract grounding but are currently missing, thin, or undocumented in the `docs/` tree.

- **Search Plane freshness and re-index invariants**
  - **Path**: `docs/spec/search-plane/01_invariants.md` (MISSING)
  - **Influences**: Search
  - **Why**: Current docs (`09_SEARCH_PLANE_SURFACES.md`) describe the API but not the "Contract of Freshness" (e.g., how long after a PM write should a search result appear?).
  - **Recommended Action**: Extract existing `SearchManager` docstrings or synthesize from `09_SEARCH_PLANE_SURFACES.md`.

- **Identity Plane & Workspace Authority**
  - **Path**: `docs/spec/identity/01_workspace_mapping.md` (MISSING)
  - **Influences**: Identity / Authority
  - **Why**: No clear contract on which service owns the canonical mapping of `workspace_id` to local filesystem paths vs remote IDs.
  - **Recommended Action**: Audit `src/dopemux/core/workspace.py` and extract into a spec.

- **Deterministic CLI Contract**
  - **Path**: `docs/spec/cli/01_determinism_gate.md` (MISSING)
  - **Influences**: CLI / Authority
  - **Why**: Opus needs to know which CLI commands are safe to run autonomously (deterministic) vs which require user terminal interaction.
  - **Recommended Action**: Scan `src/dopemux/cli.py` for `@click.command` vs interactive prompts.

- **Dope-Memory v1 Implementation Gap Audit**
  - **Path**: `docs/planes/pm/_evidence/DOPE_MEMORY_V1_DRIFT_ANALYSIS.md` (MISSING)
  - **Influences**: Stores / Determinism
  - **Why**: We have `docs/spec/dope-memory/v1/`, but no evidence of how much the current Postgres/SQLite implementation deviates from this spec.
  - **Recommended Action**: Run a schema comparison between `v1` docs and actual `pg_dump` / `sqlite3 .schema` output.

- **Task-Orchestrator Decision Provenance**
  - **Path**: `docs/systems/task-orchestrator/decision_architecture.md` (THIN)
  - **Influences**: TaskX / Determinism
  - **Why**: Existing `coordination.md` is high-level. Missing the exact JSON schema of a "Decision Packet" used by the orchestrator.
  - **Recommended Action**: Extract `DecisionPacket` dataclass structure from `src/task_orchestrator/models.py`.
