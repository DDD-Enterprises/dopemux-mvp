# Packet 100 Research

## Observed Authority

- Active blocker: task-orchestrator item `dcf66b56-8fbf-426f-a6d6-826f0caa5822`, `DMX-CONPORT-OPTIMAL-100-migration-foundation-gate`, role `blocked`.
- Existing fail-closed proof: `/Users/hue/.codex/worktrees/4ecf/dopemux-mvp/proof/conport-optimal-100-migration-foundation-gate/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate/proof.md`.
- Current clean worktree: `/Users/hue/.codex/worktrees/conport-optimal-100-resolve`, branch `codex/conport-optimal-100-resolve`, base `origin/main` at `6c7f7e7b444c1f56a88a1231d7846404b1687910`.

## Runtime Findings

- `docker/mcp-servers-source/conport/Dockerfile` copies `schema.sql` and runtime modules, but not `docker/mcp-servers-source/conport/migrations/`.
- `docker/mcp-servers-source/conport/enhanced_server.py` `_ensure_schema()` only applies `/app/schema.sql` when `public.workspace_contexts` is absent.
- `_ensure_schema()` also silently runs `ALTER TABLE ... ADD COLUMN IF NOT EXISTS instance_id/created_by_instance` during normal startup, which conflicts with packet 100's no-silent-startup-migration invariant.
- `docker/mcp-servers-source/conport/schema.sql` creates baseline public tables including `entity_relationships`, but not enhanced objects such as `decision_relationships`, `adhd_metrics`, `review_reminders`, `decision_patterns`, `users`, `workspaces`, or `user_workspace_access`.
- `docker/mcp-servers-source/conport/migrations/004_unified_query_indexes.sql` still targets `ag_catalog.*`; current ConPort runtime and packet 102 use `public`.
- Migration 004's first GIN index combines `user_id` and `to_tsvector(...)`, which is not safe without a btree GIN operator class. A separate public full-text GIN index plus existing btree indexes is safer.

## Risks

- Applying migrations to a live database mutates schema and must remain explicitly operator-gated.
- Ledger/checksum drift must fail closed; silently accepting existing enhanced objects without ledger state would mask unmanaged drift.
- Removing startup-time optional ALTERs can expose databases that have not run migration 007; the migration gate must make this state visible instead of hiding it.
- Live DB validation may be unavailable; if not run, record NOT_RUN instead of claiming live readiness.

## Candidate Verification Commands

- `python3 -m py_compile docker/mcp-servers-source/conport/enhanced_server.py docker/mcp-servers-source/conport/migrations/conport_migration_gate.py`
- `python3 -m pytest -q proof/conport-optimal-100-migration-foundation-gate/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate/test_conport_migration_gate.py`
- `python3 -m json.tool task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json >/dev/null`
- `python3 -m jsonschema -i task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- `grep -R "ag_catalog" docker/mcp-servers-source/conport/migrations/004_unified_query_indexes.sql`
- `git diff --check`
