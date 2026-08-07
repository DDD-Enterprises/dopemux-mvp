#!/bin/bash
# Provision a per-project ConPort database inside the shared Postgres+AGE server.
#
# WHY THIS EXISTS
# ---------------
# Until 2026-08-02 every ConPort container on the host — across every project
# and worktree — wrote into ONE database (dopemux_knowledge_graph). Isolation
# was a bare `workspace_id VARCHAR` column with no FK and no enforcement, so a
# client could read or write any project's rows just by passing a different
# string. That is the condition ADR adr-conport-canonical-record-service-v2
# calls out as unsafe, and it is how /Users/hue/code/adOps progress entries
# ended up in the dopemux store.
#
# This script builds the "project wall" by configuration rather than by the
# full CRS v2 rewrite: one database per project, owned by its own LOGIN role,
# with CONNECT revoked from PUBLIC. Credentials then bind the tenant — a
# ConPort container holding the adOps role literally cannot reach dopemux-mvp's
# rows, whatever workspace_id it sends.
#
# The Postgres SERVER stays a host singleton. It is an RDBMS; N copies of it
# is waste. It is the DATABASE that is per project.
#
# NOTE ON schema.sql
# ------------------
# docker/mcp-servers-source/conport/ is sealed by red lane
# DCP-RED-MERGE-SEAM-0001, so schema.sql cannot be edited. It does not need to
# be: it ends with three sample INSERTs hardcoding the short-form alias
# 'dopemux-mvp' (lines ~263-292), which is the origin of the
# dopemux-mvp vs /Users/hue/code/dopemux-mvp alias split and which would seed
# fake decisions into every new project database. We strip that block at APPLY
# time instead of editing the sealed file. Verified 2026-08-02: the live DB's
# "Implement hybrid database backend for ConPort persistence" decision is this
# sample data, not user content.
#
# Usage:
#   ./scripts/migration/provision_conport_project_db.sh \
#       --slug dopemux_mvp --workspace-id /Users/hue/code/dopemux-mvp
#
#   --slug          identifier suffix; DB and role both become conport_<slug>
#   --workspace-id  canonical workspace_id to register (use the PATH form)
#   --password      role password (generated if omitted)
#   --dry-run       print what would happen, touch nothing

set -euo pipefail

AGE_CONTAINER="${AGE_CONTAINER:-dopemux-postgres-age}"
CONPORT_CONTAINER="${CONPORT_CONTAINER:-mcp-conport}"
SUPERUSER="${AGE_USER:-dopemux_age}"
SCHEMA_FILE="${SCHEMA_FILE:-docker/mcp-servers-source/conport/schema.sql}"

SLUG=""
WORKSPACE_ID=""
ROLE_PASSWORD=""
DRY_RUN=false

log()     { echo "[INFO] $1"; }
success() { echo "✅ $1"; }
fail()    { echo "❌ $1" >&2; exit 1; }
step()    { echo ""; echo "🔄 $1"; }

while [[ $# -gt 0 ]]; do
    case $1 in
        --slug)         SLUG="$2"; shift 2 ;;
        --workspace-id) WORKSPACE_ID="$2"; shift 2 ;;
        --password)     ROLE_PASSWORD="$2"; shift 2 ;;
        --dry-run)      DRY_RUN=true; shift ;;
        --help)         sed -n '1,40p' "$0"; exit 0 ;;
        *)              fail "Unknown option: $1" ;;
    esac
done

[ -n "$SLUG" ]         || fail "--slug is required"
[ -n "$WORKSPACE_ID" ] || fail "--workspace-id is required"

# Slug goes into SQL identifiers. Keep it to a safe charset rather than trying
# to quote our way out of injection.
if ! [[ "$SLUG" =~ ^[a-z][a-z0-9_]{0,40}$ ]]; then
    fail "--slug must match ^[a-z][a-z0-9_]{0,40}\$ (got: '$SLUG')"
fi

DB_NAME="conport_${SLUG}"
DB_ROLE="conport_${SLUG}"

if [ -z "$ROLE_PASSWORD" ]; then
    # Deliberately NOT `tr -dc ... < /dev/urandom | head -c 32`: head closes the
    # pipe early, tr dies on SIGPIPE, and `set -o pipefail` turns that into a
    # 141 exit that kills this script before it prints anything.
    if command -v openssl >/dev/null 2>&1; then
        ROLE_PASSWORD="$(openssl rand -hex 24)"
    else
        ROLE_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
    fi
    GENERATED_PW=true
else
    GENERATED_PW=false
fi

[ -f "$SCHEMA_FILE" ] || fail "schema file not found: $SCHEMA_FILE"

echo ""
log "═══════════════════════════════════════════════════════════"
log "  ConPort project database provisioning"
log "  Database / role : ${DB_NAME}"
log "  workspace_id    : ${WORKSPACE_ID}"
log "  Postgres server : ${AGE_CONTAINER} (shared host singleton)"
log "  Dry run         : ${DRY_RUN}"
log "═══════════════════════════════════════════════════════════"

# psql as the bootstrap superuser, against an arbitrary database.
psql_super() {
    local db="$1"; shift
    docker exec -i "$AGE_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$SUPERUSER" -d "$db" "$@"
}

# psql as the project role, against the project database.
psql_project() {
    docker exec -i -e PGPASSWORD="$ROLE_PASSWORD" "$AGE_CONTAINER" \
        psql -v ON_ERROR_STOP=1 -U "$DB_ROLE" -h 127.0.0.1 -d "$DB_NAME" "$@"
}

# Strip the sample-data block (see NOTE ON schema.sql above) without touching
# the sealed source. Everything from the "INITIAL DATA MIGRATION" banner up to
# (but not including) the GRANT section is dropped; the GRANTs are kept.
filtered_schema() {
    awk '
        /^-- INITIAL DATA MIGRATION/            { skipping = 1 }
        /^-- Grant permissions to the ConPort/  { skipping = 0 }
        !skipping                                { print }
    ' "$SCHEMA_FILE"
}

if $DRY_RUN; then
    step "DRY RUN — would create role ${DB_ROLE} and database ${DB_NAME}"
    kept=$(filtered_schema | grep -c '^INSERT INTO' || true)
    log "Sample INSERT statements surviving the filter: ${kept} (expected 0)"
    filtered_schema | grep -n "INITIAL DATA MIGRATION" >/dev/null 2>&1 \
        && log "WARNING: seed banner still present" \
        || log "Seed block correctly stripped"
    log "Schema lines: $(wc -l < "$SCHEMA_FILE") -> $(filtered_schema | wc -l) after filtering"
    exit 0
fi

# --- 1. role + database (superuser) ---------------------------------------
step "Creating role and database"

psql_super postgres <<SQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${DB_ROLE}') THEN
        CREATE ROLE ${DB_ROLE} LOGIN PASSWORD '${ROLE_PASSWORD}';
    ELSE
        ALTER ROLE ${DB_ROLE} LOGIN PASSWORD '${ROLE_PASSWORD}';
    END IF;
END
\$\$;
SQL
success "Role ${DB_ROLE} ready"

if psql_super postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1; then
    log "Database ${DB_NAME} already exists — leaving it in place"
else
    psql_super postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_ROLE};"
    success "Database ${DB_NAME} created"
fi

# The wall itself: no PUBLIC connect, so only the owning role (and superusers)
# can reach this database at all.
psql_super postgres -c "REVOKE CONNECT ON DATABASE ${DB_NAME} FROM PUBLIC;"
psql_super postgres -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_ROLE};"
success "CONNECT revoked from PUBLIC on ${DB_NAME}"

# --- 2. extensions (superuser-only) ---------------------------------------
step "Installing extensions"
psql_super "$DB_NAME" -c 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'
psql_super "$DB_NAME" -c 'CREATE EXTENSION IF NOT EXISTS "pg_trgm";'
psql_super "$DB_NAME" -c 'CREATE EXTENSION IF NOT EXISTS age;' || log "AGE extension unavailable — continuing (ConPort core does not require it)"
success "Extensions installed"

# --- 3. schema, applied AS the project role so it owns its tables ---------
# schema.sql is NOT idempotent (7 bare CREATE TABLE, 24 bare CREATE INDEX), so
# re-running it against a provisioned database would abort under
# ON_ERROR_STOP=1. Detect and skip instead, which keeps this script safe to
# re-run.
SCHEMA_PRESENT=false
if psql_project -tAc "SELECT to_regclass('public.decisions') IS NOT NULL" 2>/dev/null | grep -q '^t$'; then
    SCHEMA_PRESENT=true
fi

if $SCHEMA_PRESENT; then
    step "Schema already present — skipping schema and migration apply"
    log "public.decisions exists; going straight to ledger verification"
else
    step "Applying filtered schema as ${DB_ROLE}"
    remaining=$(filtered_schema | grep -c '^INSERT INTO' || true)
    [ "$remaining" -eq 0 ] || fail "seed filter failed: ${remaining} INSERT statements survived"

    filtered_schema | psql_project >/dev/null
    success "Schema applied with alias seed block stripped"
fi

# --- 4. migrations --------------------------------------------------------
# We apply the migration SQL ourselves and then let the gate ADOPT it, rather
# than calling `gate apply` on an empty database.
#
# Why: conport_migration_gate.apply_migrations() opens a psycopg2 transaction,
# runs preflight_base_schema()/table_exists() probes (which take AccessShareLock
# on custom_data et al), and THEN shells out to psql to run the migration —
# without committing first. Migration 003 does
# `ALTER TABLE custom_data ADD COLUMN user_id`, which needs AccessExclusiveLock
# and therefore blocks forever on the gate's own uncommitted transaction.
# Reproduced 2026-08-02: pg_stat_activity showed the gate's backend
# `idle in transaction` while its psql child waited on AccessExclusiveLock.
# The gate can never bootstrap a fresh database. It only works on one where the
# objects already exist, because then `migration_already_applied()` short-circuits
# and psql is never invoked.
#
# That is exactly the path we take here: apply the SQL with psql (no competing
# open transaction), then `gate apply` adopts all five and authors the ledger
# rows with its own checksums, and `gate verify` proves the result.
#
# The gate lives under the red-lane-sealed docker/mcp-servers-source/conport/
# tree, so fixing it in place needs its own ADR + task packet.
if $SCHEMA_PRESENT; then
    log "Skipping migration SQL (schema already present)"
else
    step "Applying migrations"
    MIGRATIONS_DIR="$(dirname "$SCHEMA_FILE")/migrations"
    for m in 001_enhanced_decision_model 002_decision_patterns_table \
             003_multi_tenancy_foundation 004_unified_query_indexes \
             007_worktree_support_simple; do
        printf '  %-38s' "$m"
        if psql_project -q < "${MIGRATIONS_DIR}/${m}.sql" >/dev/null 2>&1; then
            echo "OK"
        else
            echo "FAIL"
            fail "migration ${m} failed"
        fi
    done
    success "Migration SQL applied"
fi

step "Recording ledger via conport_migration_gate (adopt path)"
GATE_URL="postgresql://${DB_ROLE}:${ROLE_PASSWORD}@${AGE_CONTAINER}:5432/${DB_NAME}"
docker exec -e DPMX_CONPORT_MIGRATION_APPLY=1 "$CONPORT_CONTAINER" \
    python migrations/conport_migration_gate.py apply --database-url "$GATE_URL"
success "Ledger recorded"

step "Verifying migration ledger"
docker exec "$CONPORT_CONTAINER" \
    python migrations/conport_migration_gate.py verify --database-url "$GATE_URL"
success "Ledger verified"

# --- 5. register the workspace -------------------------------------------
# workspaces / user_workspace_access carry REAL foreign keys to users, unlike
# the data tables. Seed them so the registry does not silently drift the way
# the shared database's did (1 registered workspace vs 6+ in use).
step "Registering canonical workspace"
psql_project >/dev/null <<SQL
INSERT INTO users (id, email, display_name)
VALUES ('default', 'default@localhost', 'Default User')
ON CONFLICT (id) DO NOTHING;

INSERT INTO workspaces (id, owner_user_id, name, description)
VALUES ('${WORKSPACE_ID}', 'default', '${WORKSPACE_ID}',
        'Canonical workspace for ${DB_NAME} (project-walled ${DB_NAME})')
ON CONFLICT (id) DO NOTHING;

INSERT INTO user_workspace_access (user_id, workspace_id, role)
VALUES ('default', '${WORKSPACE_ID}', 'owner')
ON CONFLICT (user_id, workspace_id) DO NOTHING;
SQL
success "Workspace ${WORKSPACE_ID} registered"

# --- 6. verification ------------------------------------------------------
step "Verification"
tables=$(psql_project -tAc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
seeded=$(psql_project -tAc "SELECT count(*) FROM decisions" )
progress=$(psql_project -tAc "SELECT count(*) FROM progress_entries")
registered=$(psql_project -tAc "SELECT count(*) FROM workspaces")

echo "  tables in public       : ${tables}"
echo "  decisions (expect 0)   : ${seeded}"
echo "  progress   (expect 0)  : ${progress}"
echo "  workspaces (expect 1)  : ${registered}"

# The zero-row assertions prove the alias seed block was stripped. They only
# hold on a freshly provisioned database — on a re-run against a database that
# has since been loaded with real data, non-zero is expected and correct.
if $SCHEMA_PRESENT; then
    log "Pre-existing database: skipping zero-row seed assertions"
else
    [ "$seeded" -eq 0 ]   || fail "expected 0 seeded decisions, found ${seeded} (alias seed block leaked)"
    [ "$progress" -eq 0 ] || fail "expected 0 seeded progress entries, found ${progress}"
fi
[ "$registered" -ge 1 ] || fail "expected the canonical workspace to be registered, found ${registered}"

echo ""
success "═══════════════════════════════════════════════════════════"
success "  ${DB_NAME} provisioned and empty, ready for data re-homing"
success "═══════════════════════════════════════════════════════════"
echo ""
echo "Add to the project's .envrc.dopemux-mcp:"
echo "  export CONPORT_DB_NAME=${DB_NAME}"
echo "  export CONPORT_DB_USER=${DB_ROLE}"
if $GENERATED_PW; then
    echo "  export CONPORT_DB_PASSWORD=${ROLE_PASSWORD}    # generated, store it now"
else
    echo "  export CONPORT_DB_PASSWORD=<the password you supplied>"
fi
echo ""
