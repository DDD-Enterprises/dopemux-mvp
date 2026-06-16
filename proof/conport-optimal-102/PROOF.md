# DMX-CONPORT-OPTIMAL-102 Proof

## Scope

TP: `task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-102-route-bugfixes-500s.json`

Branch/PR: existing `fix/conport-coldstart-grant` branch for PR #894, bundled with the ConPort 101 cold-start grant fix to reduce review surface.

## Changes

- `docker/mcp-servers-source/conport/enhanced_server.py`
  - Initializes `UnifiedQueryAPI` with `schema="public"` instead of `ag_catalog`.
  - Serializes `search_content` UUID ids and Decimal ranks before JSON cache/response.
  - Passes relationship `decision_id` through as text so UUID/text route ids do not force integer casting.
- `docker/mcp-servers-source/conport/unified_queries.py`
  - Defaults to `public`.
  - Keeps cold-start compatibility when `user_id` columns are absent, but restores user-scoped predicates when migration 003 user columns are present.
  - Uses UUID/text decision ids and active `entity_relationships.source_id` / `target_id` columns.
- `docker/mcp-servers-source/conport/Dockerfile`
  - Copies `unified_queries.py` into the image so `enhanced_server.py` can import it at runtime.
- `task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-102-route-bugfixes-500s.json`
  - Adds the Dockerfile to the allowlist after runtime tracing proved the image did not include `unified_queries.py`.

## Validation

PASS:
- RED/GREEN proof regression:
  - `python -m pytest -q proof/conport-optimal-102/test_conport_102_regression.py`
  - Final result: `14 passed`.
- Syntax:
  - `python -m py_compile docker/mcp-servers-source/conport/enhanced_server.py docker/mcp-servers-source/conport/unified_queries.py`
- Task packet JSON parse:
  - `python -m json.tool task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-102-route-bugfixes-500s.json >/dev/null`
- Canonical task-packet schema:
  - `python -m jsonschema -i task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-102-route-bugfixes-500s.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
  - Exit 0; emitted only `jsonschema` CLI deprecation warning.
- Runtime grep:
  - `grep -n 'ag_catalog' docker/mcp-servers-source/conport/enhanced_server.py | grep -v '#' || true`
  - `grep -n 'ag_catalog' docker/mcp-servers-source/conport/unified_queries.py | grep -v '#' || true`
  - No uncommented runtime output.
- Whitespace:
  - `git diff --check`
- Rebuild/recreate:
  - `docker compose build conport && docker compose up -d conport`
  - Build output includes `COPY docker/mcp-servers-source/conport/unified_queries.py .`
- Health:
  - `GET http://localhost:3004/health` -> HTTP 200 with `database=healthy`, `redis=healthy`.
- Final route smoke:
  - `GET /api/search/test-ws?q=test` -> HTTP 200.
  - `GET /api/unified-search?user_id=test-user&query=test` -> HTTP 200.
  - `GET /api/workspace-relationships?decision_id=1&user_id=test-user` -> HTTP 200.

## Notes / Drift Found

- The packet's original route-smoke examples for unified search and relationships were stale:
  - `/api/unified-search` expects `query`, not `q`.
  - `/api/workspace-relationships` expects `decision_id` and `user_id`, not `workspace_id`.
- First rebuilt runtime failed before smoke because the local dev DB role password had drifted from compose env. Repaired local-only with:
  - `ALTER ROLE dopemux_age PASSWORD 'dopemux_age_dev_password';`
  - No schema reset or data deletion was performed.

## Residual Risk

- This verifies empty-result route behavior, the serialization/schema failure modes, cold-start no-`user_id` compatibility, migrated-schema user predicates, cached timestamp rehydration, and same-workspace relationship filtering when cross-workspace traversal is disabled. It does not seed live decision/relationship rows for non-empty graph traversal.
- The public schema is the active runtime schema observed in the local container. Migration 003 user-column compatibility is covered by SQL-shape regression tests, not by a live migrated database smoke.
