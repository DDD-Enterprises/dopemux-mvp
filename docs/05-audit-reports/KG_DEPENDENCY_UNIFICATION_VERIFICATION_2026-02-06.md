---
id: KG_DEPENDENCY_UNIFICATION_VERIFICATION_2026_02_06
title: Kg Dependency Unification Verification 2026 02 06
type: explanation
owner: '@hu3mann'
author: Codex
date: '2026-02-06'
last_review: '2026-02-06'
next_review: '2026-02-20'
status: draft
prelude: Evidence-based verification of the kg dependency unification live backlog cluster with implemented and residual gaps.
---
# KG Dependency Unification Verification (2026-02-06)

## Scope

This verification covers the `kg_dependency_unification` cluster (`7` items) from:

- `docs/05-audit-reports/CONPORT_LIVE_BACKLOG_EXECUTION_PACKET_2026-02-06.md`

## Verification Commands

1. `pytest -q --no-cov services/serena/intelligence/integration_test.py tests/regression/test_serena_enhancements.py tests/regression/test_fnew5_code_graph_enrichment.py`

## Runtime/Testability Fixes Applied During Verification

1. `services/serena/intelligence/database.py`: fixed collection-time `NameError` for `asyncpg` annotations.
2. `services/serena/tree_sitter_analyzer.py`: fixed collection-time `NameError` for `Node` annotations when tree-sitter bindings are unavailable.
3. `pytest.ini`: set `asyncio_mode = auto` so async regression tests execute without per-test markers.

## Status Matrix

| Item | Classification | Evidence | Residual gap |
|---|---|---|---|
| `3.2.2: Test semantic similarity & ADHD disclosure` | `partial` | `tests/regression/test_serena_enhancements.py`, `tests/regression/test_fnew5_code_graph_enrichment.py` | test depth is still mostly smoke-level; no explicit ADHD-disclosure assertion matrix |
| `3.2.1: Integrate dope-context in Serena, add Find Similar command` | `implemented` | `services/serena/mcp_server.py`, `services/serena/claude_context_integration.py` | none for integration path |
| `3.1.1: Design & populate conport_integration_links` | `implemented_in_code` | `services/serena/intelligence/schema.sql`, `services/serena/intelligence/conport_bridge.py`, `services/serena/intelligence/integration_test.py` | runtime population density not yet measured on prod-like dataset |
| `2.2.3: Validate embedding quality & schema` | `partial` | `src/dopemux/extraction/consensus_validator.py`, `services/dope-context/src/pipeline/indexing_pipeline.py` | no dedicated conport decision embedding regression benchmark |
| `2.2.2: Write & run migration script (re-embed decisions)` | `partial` | `scripts/deploy/migration/backfill_embeddings.py` | script exists; no current-wave run artifact against target dataset |
| `2.2.1: Remove ConPort embedding_service, import from core` | `partial` | `services/conport/http_server.py`, `src/dopemux/mcp/conport_mcp_tools.py` | legacy semantic-search stubs still present |
| `2.1.2: Update docs & add deprecation warnings` | `partial` | `docs/04-explanation/architecture/ARCHITECTURE-CONSOLIDATION-SYNTHESIS.md`, `docs/03-reference/serena-v2-mcp-tools.md` | active code-truth docs still contain non-deprecated semantic-search references |

## Summary

1. Implemented: `1`
2. Implemented in code (runtime population pending): `1`
3. Partial: `5`
4. Open with no evidence: `0`

## Recommended Next Focus

1. Strengthen semantic-similarity and ADHD-disclosure assertions from smoke to deterministic regression checks.
2. Run `backfill_embeddings.py` against target decision dataset and capture success/failure artifact.
3. Remove or hard-deprecate ConPort semantic-search placeholder paths and align active docs to code truth.

## Artifact

- `reports/strict_closure/kg_dependency_unification_verification_2026-02-06.json`
