# DMX-CONPORT-OPTIMAL-100 Migration Foundation Gate Proof

## Result

Status: PASS on targeted local-dev validation and 2026-06-22 live verify.

Scope: migration packaging, explicit migration gate runtime, idempotent migration fixes, packet/proof artifacts, and live local-dev ConPort verify. No migration apply was run during the 2026-06-22 continuation.

## Authority

- User request: resolve packet 100 blocker so downstream ConPort packets can proceed.
- Repo authority: `AGENTS.md`, task packet requirements, runtime code/config/tests.
- Packet: `task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json`.

## Worktree

- Path: `/Users/hue/.codex/worktrees/conport-optimal-100-resolve`
- Branch: `codex/conport-optimal-100-resolve`
- Base observed at creation: `origin/main` `6c7f7e7b444c1f56a88a1231d7846404b1687910`

## Changes

- Added explicit ConPort migration gate: `docker/mcp-servers-source/conport/migrations/conport_migration_gate.py`.
- Added base-schema preflight before ledger mutation so fresh databases fail closed without poisoned failed ledger rows.
- Added adoption of already-applied legacy migrations into the ledger when schema evidence or legacy migration markers indicate prior application; final verification still requires expected schema objects and views.
- Rejected non-`public` schemas explicitly because current ConPort SQL migrations are public-qualified or unqualified.
- Preserved libpq URI options such as `sslmode` and `connect_timeout` for
  migration execution by passing a password-sanitized connection URI to `psql`
  and keeping the password in `PGPASSWORD`, not argv.
- Preserved empty-host libpq URIs such as
  `postgresql:///conport?host=/var/run/postgresql` when invoking `psql`.
- Stripped query-string `password=` credentials from the `psql` argv and moved
  them into `PGPASSWORD`.
- Rejected adoption of migration versions that lack explicit schema evidence
  checks.
- Added the migration 007 workspace/instance unique index to gate evidence and
  final schema verification.
- Aligned fresh `schema.sql` with the active instance/worktree route contract so
  startup-created databases include `instance_id`, `created_by_instance`, and
  required worktree indexes before the operator-gated migration adoption path
  runs.
- Packaged migrations into the ConPort image via `Dockerfile`.
- Removed hidden startup DDL from `enhanced_server.py`; startup now logs the explicit gate path.
- Hardened migration SQL for replay/idempotency:
  - `004_unified_query_indexes.sql` uses `public.*` instead of `ag_catalog.*`.
  - `004_unified_query_indexes.sql` avoids the invalid mixed scalar/vector GIN index.
  - `007_worktree_support_simple.sql` uses idempotent column/index creation.
- Documented gate usage in `migrations/README.md`.
- Added targeted proof tests, research, plan, and local schema backup.
- Rotated the local-dev `AGE_PASSWORD` secret after transcript exposure, reset the `dopemux_age` role password over the trusted local socket, and recreated `postgres`, `conport`, and `dopecon-bridge` from the updated compose env. Secret values are intentionally omitted from proof.

## Validation

PASS:

- `python3 -m pytest -q proof/conport-optimal-100-migration-foundation-gate/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate/test_conport_migration_gate.py`
  - Result before review-thread URI fix: `14 passed`
  - Result after review-thread URI fix: `15 passed`
  - Result after follow-up review fixes: `18 passed`
  - Result after startup schema and 007 index fixes: `20 passed`
- `python3 -m py_compile docker/mcp-servers-source/conport/enhanced_server.py docker/mcp-servers-source/conport/migrations/conport_migration_gate.py`
  - Result: exit 0
- `python3 -m json.tool task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json`
  - Result: exit 0
- `python3 -m jsonschema -i task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
  - Result: exit 0; jsonschema CLI deprecation warning only
- `grep -R 'ag_catalog' docker/mcp-servers-source/conport/migrations/004_unified_query_indexes.sql; test $? -eq 1`
  - Result: exit 0; no `ag_catalog` references remain in migration 004
- `git diff --check`
  - Result: exit 0
- `python3 docker/mcp-servers-source/conport/migrations/conport_migration_gate.py apply --database-url postgresql://user:pass@localhost/db`
  - Result: exit 2 with fail-closed JSON: `refusing to mutate database without DPMX_CONPORT_MIGRATION_APPLY=1`
- `docker compose build conport`
  - Result: exit 0; build log included `COPY docker/mcp-servers-source/conport/migrations /app/migrations`
  - Re-run after review fix: exit 0
- `docker compose up -d conport`
  - Result: exit 0; `mcp-conport` recreated and started
  - Re-run after review fix: exit 0; `mcp-conport` recreated and started
- `curl -sS -o /tmp/conport_health.out -w '%{http_code}' http://localhost:3004/health`
  - Result: `200`
- `docker exec mcp-conport sh -lc 'python /app/migrations/conport_migration_gate.py verify --database-url "$DATABASE_URL"'`
  - Result: pass; verified migrations `001`, `002`, `003`, `004`, and `007`
- 2026-06-22 credential rotation and live verify continuation:
  - `docker exec mcp-conport ... psycopg2.connect(os.environ["DATABASE_URL"])`
    - Result: exit 0; connected to `dopemux_knowledge_graph` as `dopemux_age`
  - `docker exec dopemux-postgres-age ... PGPASSWORD="$POSTGRES_PASSWORD" psql -h <bridge-ip> ...`
    - Result: exit 0; TCP SCRAM auth succeeded as `dopemux_age`
  - `docker compose -f compose.yml ps --format json`
    - Result: `postgres`, `conport`, and `dopecon-bridge` running healthy after recreation
  - `docker exec mcp-conport sh -lc 'python /app/migrations/conport_migration_gate.py verify --database-url "$DATABASE_URL"'`
    - Result: exit 0; pass; verified `001_enhanced_decision_model.sql`, `002_decision_patterns_table.sql`, `003_multi_tenancy_foundation.sql`, `004_unified_query_indexes.sql`, and `007_worktree_support_simple.sql`
- `pre-commit run --files <changed packet files>`
  - Result: exit 0; applicable hooks passed, unrelated file-pattern hooks skipped
- PR CI after review fix:
  - Result before review fix: all checks passed on head `19c1db99e752c1a58570d787db1ce6f435fde115`; GitHub still blocked merge because unresolved review conversations remained.

Local-dev apply evidence:

- Captured schema-only backup before apply: `proof/conport-optimal-100-migration-foundation-gate/DMX-CONPORT-OPTIMAL-100-migration-foundation-gate/live/pre_apply_schema.sql`
- Read-only verify failed closed before ledger existed.
- Explicit local-dev apply was run inside `mcp-conport` with `DPMX_CONPORT_MIGRATION_APPLY=1`.
- Post-apply in-container verify passed.

NOT_RUN:

- Production/staging database mutation: not authorized and not run.
- Full repository test suite: not run; packet blast radius was ConPort migration gate and packaging.
- PAL external codereview: attempted, but PAL returned `files_required_to_continue` and did not produce a review result.
- PAL precommit: initial continuation existed, but two follow-up calls failed with `Transport closed`.
- PAL final challenge: attempted after PAL precommit transport failure, but the call failed with `Transport closed`.

## Residual Risk

- Local dev database volume was intentionally mutated by the explicit apply gate. The schema-only pre-apply backup is retained for rollback evidence.
- The validation proves package/install/verify behavior and required schema objects, not all downstream ConPort feature workflows.
- Host Python lacks `psycopg2`; host-side database verification fails closed unless dependency is installed. The Docker image path has `psycopg2` available and passed.
- Packet governance still has PAL codereview/precommit/challenge gaps because the PAL tool path failed. Local precommit evidence is captured, but PAL completion is not claimed.

## Rollback

- Code rollback: revert the branch commit or remove the PR branch.
- Local dev database rollback: restore from `live/pre_apply_schema.sql` or recreate the local compose volume from a clean baseline.
- Runtime rollback: rebuild/recreate `conport` from the previous image/source state.
