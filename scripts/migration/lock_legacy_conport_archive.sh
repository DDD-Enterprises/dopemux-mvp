#!/bin/bash
# Lock the legacy shared ConPort database (dopemux_knowledge_graph) so normal
# project application roles cannot CONNECT. Superuser / explicit archive role
# retain access for forensics. Source JSON export remains the retained archive
# of the 2025 corpus; this only walls the leftover Postgres DB.
#
# Usage:
#   ./scripts/migration/lock_legacy_conport_archive.sh
#
# Idempotent. Does not delete data.

set -euo pipefail

AGE_CONTAINER="${AGE_CONTAINER:-dopemux-postgres-age}"
SUPERUSER="${AGE_USER:-dopemux_age}"
LEGACY_DB="${LEGACY_CONPORT_DB:-dopemux_knowledge_graph}"
ARCHIVE_ROLE="${CONPORT_ARCHIVE_ROLE:-conport_archive_ro}"

log() { echo "[INFO] $1"; }
success() { echo "✅ $1"; }
fail() { echo "❌ $1" >&2; exit 1; }

docker inspect "$AGE_CONTAINER" >/dev/null 2>&1 || fail "container not running: $AGE_CONTAINER"

psql_su() {
    docker exec -i "$AGE_CONTAINER" psql -U "$SUPERUSER" -d postgres -v ON_ERROR_STOP=1 "$@"
}

log "Creating archive role ${ARCHIVE_ROLE} (login optional; no superuser)"
psql_su <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${ARCHIVE_ROLE}') THEN
    CREATE ROLE ${ARCHIVE_ROLE} NOINHERIT;
  END IF;
END
\$\$;
SQL

log "Revoking CONNECT from PUBLIC and project roles on ${LEGACY_DB}"
psql_su <<SQL
-- Ensure database exists
SELECT 1 FROM pg_database WHERE datname = '${LEGACY_DB}';

REVOKE CONNECT ON DATABASE ${LEGACY_DB} FROM PUBLIC;
REVOKE CONNECT ON DATABASE ${LEGACY_DB} FROM conport_dopemux_mvp;
REVOKE CONNECT ON DATABASE ${LEGACY_DB} FROM conport_adops;

-- Explicit archive access (CONNECT only here; table grants optional)
GRANT CONNECT ON DATABASE ${LEGACY_DB} TO ${ARCHIVE_ROLE};
GRANT CONNECT ON DATABASE ${LEGACY_DB} TO ${SUPERUSER};
SQL

# Table-level: strip any residual privileges project roles may hold.
# CONNECT is the main wall; table grants are defense in depth.
psql_su -d "$LEGACY_DB" <<SQL || true
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM conport_dopemux_mvp;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM conport_adops;
REVOKE ALL ON SCHEMA public FROM conport_dopemux_mvp;
REVOKE ALL ON SCHEMA public FROM conport_adops;
GRANT USAGE ON SCHEMA public TO ${ARCHIVE_ROLE};
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ${ARCHIVE_ROLE};
SQL

log "Verification matrix"
psql_su <<'SQL'
SELECT d.datname,
       has_database_privilege('conport_dopemux_mvp', d.datname, 'CONNECT') AS mvp_connect,
       has_database_privilege('conport_adops', d.datname, 'CONNECT') AS adops_connect,
       has_database_privilege('public', d.datname, 'CONNECT') AS public_connect,
       has_database_privilege('public', d.datname, 'CREATE') AS public_create,
       has_database_privilege('conport_archive_ro', d.datname, 'CONNECT') AS archive_connect
FROM pg_database d
WHERE d.datname IN ('conport_dopemux_mvp','conport_adops','dopemux_knowledge_graph','postgres')
ORDER BY 1;
SQL

success "Legacy archive CONNECT locked for project roles"
