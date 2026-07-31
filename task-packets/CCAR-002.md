---
id: CCAR-002
title: Ccar 002
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-31'
last_review: '2026-07-31'
next_review: '2026-10-29'
prelude: Ccar 002 (explanation) for dopemux documentation and developer workflows.
---
# CCAR-002 — Normalized Agent/Persona Catalog

**Packet**: CCAR-002
**Project**: dopemux-mvp
**Series**: CCAR-SERIES-001
**Status**: Implementation in progress

## Target

Compile the merged Dopemux agent and persona fleet into a strict, deterministic, model-free, advisory CommandCode catalog without generating agents, activating routing, or granting new authority.

## Key Invariants

- 9 base agents, all resolving through `src/dopemux/roles/catalog.py`
- 43 personas covering every active source
- No model IDs in catalog or schema
- All persona authority booleans = false
- No route_eligible personas (advisory only)
- `general-purpose-dopemux` never automatic write fallback
- Deterministic generation; `--check` passes

## Files

| File | Purpose |
|---|---|
| `schemas/commandcode/normalized_agent_persona_catalog.schema.json` | Strict JSON Schema |
| `config/commandcode/normalized_agent_persona_catalog.yaml` | Generated catalog |
| `scripts/commandcode_router/build_normalized_catalog.py` | Deterministic builder |
| `tests/commandcode_router/test_normalized_catalog.py` | 21 tests |

## Validation

- Source SHA-256 verification: PASS
- Role resolution through catalog.py: PASS
- Schema validation (jsonschema): PASS
- Builder --check determinism: PASS
- All 21 tests pass
- No generated CommandCode agent, skill, hook, MCP, or runtime activation
