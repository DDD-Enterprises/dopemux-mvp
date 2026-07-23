# Task Packet: TP-DOPECONTEXT-VOYAGE4-0001 · Dope-Context · Voyage 4 and Index Safety

## Objective

Modernize the canonical dope-context Voyage integration to current models and
make document indexing token-aware, dimension-safe, deterministic, and
failure-preserving without replacing the Python/FastMCP/Qdrant architecture.

## Status

`IMPLEMENTATION_CANDIDATE`

Final completion requires repository CI, embedded audit, and PR Steward proof
against the final PR head.

## Risk

`MEDIUM-HIGH`

Reason: model and vector-schema behavior changes can invalidate or contaminate
derived Qdrant indexes even though source files remain authoritative.

## Base

- Repo: `DDD-Enterprises/dopemux-mvp`
- Base branch: `main`
- Base SHA inspected:
  `b2ee5f11de04861c202d31241f909d83d85fbe41`

## Scope

### IN

- Voyage embedding model registry and defaults
- model-specific token accounting
- contextualized embedding cache correctness
- standard embedding cache correctness
- Voyage request partitioning
- reranker token pricing and request limits
- docs index payload version/fingerprint
- deterministic docs point IDs
- failure-safe docs replacement
- exact-source stale cleanup
- focused tests
- current implementation audit/reference note
- dope-context container constraint for Voyage SDK 0.5

### OUT

- replacing Qdrant with Milvus
- wholesale upstream Claude Context import
- broad `mcp/server.py` refactor
- code-index chunker redesign
- code collection migration or deletion
- production collection cutover
- network/live Voyage calls
- Qdrant data deletion outside deterministic stale replacement
- unrelated dependency or Docker hardening
- PM, memory, bridge, or workflow-plane changes

## Invariants

- Source code and documents remain upstream authority.
- Qdrant indexes remain derived retrieval artifacts.
- dope-context remains code/docs retrieval authority only.
- Existing collection data must not be deleted before replacement vectors are
  successfully generated and inserted.
- Model/dimension/dtype changes must be visible in derived index metadata.
- Existing `voyage-context-3` remains an explicit rollback option.
- Code embeddings continue to default to `voyage-code-3`.
- Output budgeting remains separate from embedding token accounting.
- No secrets or API keys enter source, tests, logs, or proof.
- No live Voyage request is required for unit validation.

## Allowed Files

- `services/dope-context/Dockerfile`
- `services/dope-context/constraints.txt`
- `services/dope-context/src/embeddings/model_registry.py`
- `services/dope-context/src/embeddings/voyage_embedder.py`
- `services/dope-context/src/embeddings/contextualized_embedder.py`
- `services/dope-context/src/utils/model_tokenizer.py`
- `services/dope-context/src/utils/token_budget.py`
- `services/dope-context/src/rerank/voyage_reranker.py`
- `services/dope-context/src/pipeline/docs_pipeline.py`
- `services/dope-context/tests/test_docs_pipeline_invariants.py`
- `services/dope-context/tests/test_voyage_modernization.py`
- `docs/03-reference/systems/dope-context/modernization-audit-2026-07-22.md`
- `task-packets/dope-context/TP-DOPECONTEXT-VOYAGE4-0001.md`

## Required Chain

`analyze -> apilookup -> thinkdeep -> challenge -> planner -> challenge -> implement -> testgen -> codereview -> precommit -> embedded-audit -> PR-Steward`

## Implementation Slices

### Slice 1 — Model and token contract

- Add one Voyage model registry.
- Add model-specific token counting with deterministic fallback.
- Replace stale model literals through configurable defaults.
- Correct current pricing/accounting.
- Make cache identity include vector shape.

Validation:
- model registry tests
- cache-key tests
- token partition/allocation tests
- syntax compilation

### Slice 2 — Document index safety

- Persist model/dimension/dtype/schema/fingerprint.
- Generate deterministic UUIDv5 point IDs.
- Upsert replacements before stale deletion.
- Remove basename-based deletion.

Validation:
- metadata invariant test
- deterministic ID test
- embedding-failure preservation test
- exact-source stale cleanup test

### Slice 3 — Container and evidence

- Constrain the service image to `voyageai>=0.5.0,<0.6`.
- Set explicit model defaults.
- Add implementation audit and this packet.
- Run focused and service-level validation.

## Exact Commands

```bash
git status --short --branch
git diff --stat
git diff --check

python -m compileall -q services/dope-context/src
python -m py_compile \
  services/dope-context/tests/test_docs_pipeline_invariants.py \
  services/dope-context/tests/test_voyage_modernization.py

PYTHONPATH=services/dope-context \
python -m pytest -q \
  services/dope-context/tests/test_docs_pipeline_invariants.py \
  services/dope-context/tests/test_voyage_modernization.py

PYTHONPATH=services/dope-context \
python -m pytest -q services/dope-context/tests

docker build -f services/dope-context/Dockerfile \
  -t dope-context:tp-voyage4 .

git diff --stat
git diff
git status --short --branch
```

## Validation Gates

### Local focused gate

Required:

- focused tests pass
- Python compilation passes
- no live API calls
- no source outside allowlist

### Service gate

Required:

- all `services/dope-context/tests` pass
- Docker image resolves Voyage SDK constraint
- health entrypoint remains `python -m src.mcp.server`

### Embedded audit

Required fields:

- `auditor_tool`
- `auditor_model`
- `invocation`
- `exit_code`
- `auditor_verdict`
- `auditor_findings`
- `fixes_applied_from_audit`
- `remaining_risks`

Preferred route:

1. AGY / Google Antigravity with Sonnet
2. Claude Code CLI Sonnet
3. Claude Code CLI Opus
4. Gemini CLI independent review

### PR Steward

A PR is not READY until PR Steward has harvested:

- changed files
- commits and current head SHA
- reviews and review threads
- issue comments and bot comments
- required checks
- proof current to final head
- classification of every review item

## Acceptance Criteria

- Default contextualized model is `voyage-context-4`.
- Code model remains `voyage-code-3`.
- Default reranker is `rerank-2.5`.
- Voyage model/dimension/dtype affect cache identity.
- Token counts use model-aware Voyage tokenization when available.
- Fallback token counts are explicitly approximate and conservative.
- Request batching respects model count/token ceilings.
- Reranker cost uses processed tokens.
- Docs payload records actual model, dimension, dtype, schema, and fingerprint.
- Docs Qdrant point IDs are deterministic.
- Failed embedding does not pre-delete the last good docs index.
- Stale cleanup cannot delete another document solely because its basename
  matches.
- Focused tests and compilation pass.
- Final PR head passes required repository checks.
- Embedded auditor is PASS or non-blocking PASS_WITH_RISKS.
- PR Steward emits READY before merge.

## Proof Requirements

Return verbatim:

- `git status` before/after
- base and final head SHA
- `git diff --stat`
- `git diff`
- every validation command
- stdout/stderr
- exit codes
- Docker build receipt
- embedded audit report
- PR metadata/checks
- PR Steward `MERGE_READINESS.json`

## Rollback

1. Revert the packet commits.
2. Set `DOPE_CONTEXT_DOC_EMBED_MODEL=voyage-context-3` only for bounded rollback.
3. Keep old Qdrant collections untouched until a separately approved migration.
4. Do not mix context-3 and context-4 vectors in one collection.
5. If a v2 shadow collection exists, restore the previous collection pointer
   rather than rewriting source data.

## Stop Conditions

Stop and report if:

- current branch/worktree is not dedicated to this packet
- base SHA moved and overlapping dope-context changes exist
- a file outside the allowlist is required
- installed SDK cannot support context-4/dimension parameters
- existing collection vector size differs from configured dimension
- tests imply current contracts require context-3
- any operation would delete a full collection
- live API validation would expose an API key
- embedded audit returns FAIL or NEEDS_SUPERVISOR
- CI/proof is stale relative to PR head

## Current Evidence

### OBSERVED

- Focused local reconstruction:
  - `15 passed`
  - Python compilation passed
- No live Voyage request was made.
- No production Qdrant collection was touched.

### UNKNOWN until repository execution

- complete dope-context test suite
- Docker build
- repository pre-commit
- embedded auditor verdict
- GitHub CI
- PR Steward readiness
