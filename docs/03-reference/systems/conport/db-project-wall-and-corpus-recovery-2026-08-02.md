---
id: db-project-wall-and-corpus-recovery-2026-08-02
title: ConPort Project Wall And Corpus Recovery 2026-08-02
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-08-02'
last_review: '2026-08-02'
next_review: '2026-11-01'
prelude: Record of the 2026-08-02 ConPort remediation — the silent data-plane outage, recovery of a 294-decision corpus orphaned since 2025-10-25, per-project database walls, and the test-suite-to-production write leak.
---
# ConPort Project Wall And Corpus Recovery (2026-08-02)

## Why

ConPort had been "having lots of issues" and the working hypothesis was that
per-project data stores had mixed up decisions between projects. The
investigation found something different and worse.

Three independent problems, one of which masked the other two:

1. **The REST data plane was dead and the container reported healthy.**
   `start_with_info.sh` launches three servers under a bare
   `wait $INFO_PID $REST_PID $PROXY_PID`. When the data plane on port 3004
   died, PID 1 kept waiting on the two survivors, so the container stayed
   "Up", `restart: unless-stopped` never fired (Docker restarts on *process
   exit*, not on healthcheck failure), and every ConPort write failed against a
   dead backend. Evidence: no 3004 socket in the container's `/proc/net/tcp`,
   and `State.Health.Log` showing `curl: (7) Failed to connect to localhost
   port 3004` on every probe for 7+ hours. Because the MCP tool layer calls
   `raise_for_status()` with no `except`, writes surfaced as tool errors rather
   than being silently swallowed.

2. **The real decision corpus was never migrated.** 294 decisions, 209 progress
   entries, 111 context links and 3 system patterns — dated 2025-10-05 to
   2025-10-25 — sat in `docs/archive/generated/conport-migration/conport_export.json`,
   exported from the since-deleted SQLite `context_portal/context.db`. The
   bundle's own `active_context` reads *"Migration scripts complete - ready to
   migrate ConPort to PostgreSQL AGE."* It was never run.

3. **The test suite wrote into the live database.** 238 `custom_data` rows
   across 197 distinct `workspace_id` values, ~236 of them pytest temp
   directories.

The "mixing" was real but small, and was a symptom of the missing project wall
rather than the cause of the emptiness. Root cause chain: **dead data plane →
no writes land → database looks empty → looks like data loss.**

## What was NOT true

Worth recording, because these were the starting assumptions:

- **There were never multiple ConPort databases.** One Postgres
  (`dopemux-postgres-age` / `dopemux_knowledge_graph`) served every project and
  worktree. The other six `*_pg_age_data` volumes were **0 bytes** — created by
  per-worktree compose projects, never initialised. Confirmed by mounting each
  read-only: 0 entries.
- **There was no genuine `workspace_id` alias split.** Both the short form
  `dopemux-mvp` and the path form `/Users/hue/code/dopemux-mvp` appeared in the
  data, but every short-form row is byte-for-byte the sample data seeded by
  `schema.sql` lines 267-292 — including the decision "Implement hybrid database
  backend for ConPort persistence". No user data was ever written under the
  short form, so the planned 11-table alias merge was unnecessary.

## Before / after

| Measure | Before | After |
|---|---|---|
| ConPort databases | 1, shared by all projects | 2, one per project, credential-walled |
| Decisions (dopemux-mvp) | 1 real (+1 schema sample) | **295** |
| Progress entries | 1 sample, 14 belonging to adOps | 209 (adOps' 14 moved to its own DB) |
| Entity relationships | 0 | 219 (110 context links + 109 `parent_of`) |
| ConPort containers | 4 (3 dead/never-started) | 1 |
| `pg_age` volumes | 7 (6 empty) | 1 |
| pytest rows in live DB | ~236 | 0 |
| Data-plane outage recovery | never (7h+ and counting) | ~80 s, automatic |
| ConPort backups ever taken | 0 (`backups/` was 0 bytes) | 1, verified |

## What was done

### Project wall (`scripts/migration/provision_conport_project_db.sh`)

One database and one LOGIN role per project inside the **shared** Postgres
server — the server stays a host singleton because it is an RDBMS and N copies
is waste; it is the *database* that is per project. `CONNECT` is revoked from
`PUBLIC`, so credentials bind the tenant. This reaches the "project wall" of
ADR `adr-conport-canonical-record-service-v2` by configuration, without the CRS
v2 rewrite. Verified:

```
adOps role  -> conport_adops        : connects
adOps role  -> conport_dopemux_mvp  : FATAL: permission denied ... no CONNECT privilege
mvp role    -> conport_adops        : FATAL: permission denied
adOps role  -> legacy shared DB     : ERROR: permission denied for table decisions
```

`compose.yml` now takes `CONPORT_DB_NAME` / `CONPORT_DB_USER` /
`CONPORT_DB_PASSWORD`, set per project in the (gitignored)
`.envrc.dopemux-mcp`, and defaults to the legacy shared store for projects not
yet provisioned.

### Corpus recovery (`scripts/migration/import_conport_export.py`)

Idempotent loader with a ledger in `custom_data` under category
`_migration_ledger` (742 rows), which doubles as the `old_id -> new_uuid` map.
Relationships resolve through that map rather than by content-matching
summaries, so there is no collision risk. Timestamps verified preserved:
earliest imported decision is `2025-10-05 12:50:55+00`, not the import date.
Re-running produces zero inserts.

`progress_entries.parent_id` has no column in the Postgres schema; its 109 rows
became `entity_relationships` with `relationship_type='parent_of'` rather than
being dropped. One context link (id 33) targets
`custom_data 'python-tmux-research'`, a row absent from the export — a dangling
reference in the *source* data. It is quarantined in the ledger rather than
inserted half-formed or silently discarded.

### Outage prevention (autoheal)

The compose healthcheck already detected the dead data plane correctly; nothing
acted on it. An `autoheal` service now restarts any container whose healthcheck
fails and that carries `labels: [autoheal=true]`. Regression-tested by killing
the data plane:

| t | port 3004 | container |
|---|---|---|
| 0 s | killed | `Up (healthy)` — the bug |
| 60 s | dead | `Up (unhealthy)` |
| ~78 s | dead | autoheal restarts it |
| ~98 s | serving | `Up (healthy)` |

### Test-to-production leak (`tests/conftest.py`)

An autouse fixture patches `InstanceStateManager.save_instance_state` — the
method that performs the POST. It deliberately sets **no** environment
variables.

**Environment variables alone are not sufficient**, which is worth recording
because it is the obvious fix and it does not work: `cli.py` passes
`conport_port=3004` explicitly at four call sites, and an explicit argument is
candidate #1 in `resolve_conport_port`'s precedence order, ahead of every env
override. Proven with a three-way probe against a live ConPort:

| Guard | `resolve_conport_port(3004)` returned | Wrote a row? |
|---|---|---|
| none | **3019** (probed and found production) | **yes** |
| env vars only | 3004 | no — but only because 3004 was not published at the time |
| method patch (shipped) | 3019 | **refused** |

Under compose's default `${CONPORT_HTTP_PORT:-3004}` the env-only guard would
have leaked. Full-suite run after the fix: **0 rows created**.

Setting those variables also caused two real regressions, which is the second
reason the shipped fixture avoids them: `DOPEMUX_CONPORT_PORT` feeds
`port_config.get_conport_port()` and `CONPORT_URL` is candidate #3 in
`resolve_conport_port`, so forcing either to an unreachable value broke
`test_get_conport_port_multi_instance` (expected 3034) and
`test_startup_flow_calls_recovery_menu` (expected 3004). Guarding the write
itself avoids both.

`pytest.ini` gains a `database` marker, and marked tests are skipped unless
`--run-database-tests` is passed — the supported way to test against a
throwaway database rather than the shared store.

## Latent bugs found, not fixed

Both live under `docker/mcp-servers-source/conport/`, which is sealed by red
lane `DCP-RED-MERGE-SEAM-0001`. Fixing them in place requires an ADR plus a
task packet; they are recorded here rather than worked around silently.

1. **`conport_migration_gate.py apply` self-deadlocks on any fresh database.**
   `apply_migrations()` opens a psycopg2 transaction, runs
   `preflight_base_schema()` probes that take `AccessShareLock` on
   `custom_data`, then shells out to `psql` to run migration 003, which does
   `ALTER TABLE custom_data ADD COLUMN user_id` and needs `AccessExclusiveLock`
   — blocking forever on the gate's own uncommitted transaction. Reproduced:
   `pg_stat_activity` showed the gate's backend `idle in transaction` while its
   `psql` child waited on the lock. It only ever worked because on an
   already-migrated database `migration_already_applied()` short-circuits and
   `psql` is never invoked. Workaround used here: apply the migration SQL with
   `psql` first, then let `gate apply` *adopt* it — the gate authors the ledger
   with its own checksums and `gate verify` passes.

2. **`schema.sql` seeds the `dopemux-mvp` alias into every new database.** Lines
   267-292 insert three sample rows. Any freshly initialised ConPort database
   inherits them. The provisioner strips that block at apply time via `awk`
   rather than editing the sealed file, and asserts zero surviving
   `INSERT INTO` statements before applying.

3. **The info server binds 4005 inside the container while `compose.yml`
   publishes 4004**, so the service-discovery endpoint has never been reachable
   from the host. Pre-existing; unrelated to the outage.

## Reproduce / verify

```bash
# Corpus present and timestamps preserved
docker exec -e PGPASSWORD=$CONPORT_DB_PASSWORD dopemux-postgres-age \
  psql -U conport_dopemux_mvp -h 127.0.0.1 -d conport_dopemux_mvp \
  -c "select count(*) from decisions;" \
  -c "select min(created_at) from decisions where tags @> ARRAY['legacy-import:conport-2025-10-25'];"
# expect 295 and 2025-10-05 12:50:55+00

# Ledger / idempotency: re-running the importer must change nothing
python3 scripts/migration/import_conport_export.py --json-path ... --db-url ... --workspace-id ...

# The wall holds
docker exec -e PGPASSWORD=$ADOPS_PW dopemux-postgres-age \
  psql -U conport_adops -h 127.0.0.1 -d conport_dopemux_mvp -c "select 1"
# expect: FATAL: permission denied for database "conport_dopemux_mvp"

# Autoheal regression test
docker exec mcp-conport sh -c 'kill -9 $(pidof python | cut -d" " -f2)'  # kill the REST plane
# expect the container to go unhealthy then restart within ~90s
```

## Test-suite impact

Full suite run against `b457505ddd` with and without these changes, the
baseline executed in a detached `git worktree` so the working tree was never
disturbed:

| | failing tests |
|---|---|
| baseline (no changes) | 22 |
| with these changes | 22 |

The two failure sets are **identical** — zero regressions. All 22 are
pre-existing and unrelated (dcp contract-derivation, dx surface manifest,
orchestrator transitions, pr_merge template contracts, pm source events). Note
`test_dcp_0002_contract_derivation::test_16_no_forbidden_files_modified` fails
because `.github/workflows/*` appear in the branch's committed diff; it reads
`git diff base...HEAD`, so uncommitted work cannot affect it either way.

Two regressions *were* introduced and then fixed during this work, both from
the first version of the conftest fixture setting port environment variables —
see the note above on why the shipped fixture sets none.

## Not done

- `dopemux_knowledge_graph` is retained intact as the archived origin database.
  Nothing was deleted from it; the re-homing copied rows and verified them. It
  still holds the ~236 pytest rows, the `packet-105-live` test decision, and the
  `schema.sql` sample rows.
- `dope-decision-graph-bridge` still points at the legacy shared database and
  assumes a single DSN. Its `ddg_*` tables have always been empty (it has never
  mirrored anything). Per-project wiring for it is unresolved.
- Only `dopemux-mvp` and `adOps` are provisioned. The ~10 other projects with a
  `.envrc.dopemux-mcp` still fall back to the shared store.
- ChatRipperXXX's legacy SQLite (24 decisions / 63 progress entries) was not
  imported, by choice.
- The full CRS v2 rewrite (per-request instance identity, RLS) remains queued.
