# Packet 100 Implementation Plan

## Goal

Resolve `DMX-CONPORT-OPTIMAL-100-migration-foundation-gate` by adding an explicit, operator-gated ConPort migration runner/verifier with deterministic file ordering, ledger/checksum drift detection, and fail-closed verification.

## Steps

1. Add packet 100 JSON to `task-packets/generated/DMX-CONPORT-OPTIMAL/`.
2. Package ConPort migrations in the image by copying `docker/mcp-servers-source/conport/migrations/` to `/app/migrations`.
3. Remove normal-startup silent optional schema ALTERs from `_ensure_schema()` in `enhanced_server.py`.
4. Add `docker/mcp-servers-source/conport/migrations/conport_migration_gate.py`:
   - discover forward SQL migrations deterministically,
   - exclude rollback SQL,
   - verify required migration files,
   - maintain `public.conport_schema_migrations`,
   - require both `apply` command and `DPMX_CONPORT_MIGRATION_APPLY=1` for mutation,
   - fail closed on missing files, checksum mismatch, failed ledger rows, missing ledger, missing enhanced objects, or missing required columns/indexes.
5. Correct migration SQL so the gate can target the active public schema:
   - change migration 004 from `ag_catalog` to `public`,
   - split the unsafe mixed-column GIN FTS index into a public tsvector GIN index plus existing btree indexes,
   - make migration 007 idempotent enough for deterministic runner semantics.
6. Add proof tests under the packet proof path for discovery, apply gating, checksum drift, Dockerfile packaging, no startup ALTERs, and migration 004 public schema use.
7. Refresh proof with PASS/FAIL/NOT_RUN evidence.

## Verification Commands

- `python3 -m py_compile docker/mcp-servers-source/conport/enhanced_server.py docker/mcp-servers-source/conport/migrations/conport_migration_gate.py`
- `python3 -m pytest -q proof/conport-optimal-100-migration-foundation-gate/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate/test_conport_migration_gate.py`
- `python3 -m json.tool task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json >/dev/null`
- `python3 -m jsonschema -i task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `grep -R "ag_catalog" docker/mcp-servers-source/conport/migrations/004_unified_query_indexes.sql`
- `git diff --check`

## Rollback

Revert the branch commit. Runtime mutation remains separately operator-gated by the migration script and is not performed by normal startup.
