#!/bin/bash
# Re-home one workspace's ConPort rows from the legacy shared database into its
# own project-walled database.
#
# CONTEXT
# -------
# Until 2026-08-02 every project wrote into dopemux_knowledge_graph, separated
# only by an unenforced workspace_id string. provision_conport_project_db.sh
# builds the per-project databases; this script moves the rows.
#
# "Move" here means the authoritative home moves. Rows are COPIED and verified,
# and the source is deliberately left intact: dopemux_knowledge_graph becomes
# the archived origin database rather than being mutated or dropped. That keeps
# the operation fully reversible — if anything is wrong, stop using the new
# database and nothing has been lost.
#
# COLUMN ORDER IS NOT ASSUMED
# ---------------------------
# The legacy database was built from an older schema.sql, so although it has
# the same column SET as a freshly provisioned database, the ordinal ORDER
# differs (e.g. decisions.created_by_instance is position 25 in the legacy DB
# and position 9 in a new one). A bare `COPY table TO STDOUT` would therefore
# silently write values into the wrong columns. Every COPY below enumerates
# columns explicitly, sorted by name on both sides, and the script refuses to
# run if the two column sets are not identical.
#
# Usage:
#   ./scripts/migration/rehome_conport_rows.sh \
#       --slug dopemux_mvp --workspace-id /Users/hue/code/dopemux-mvp \
#       --password "$CONPORT_DB_PASSWORD" [--dry-run]

set -euo pipefail

AGE_CONTAINER="${AGE_CONTAINER:-dopemux-postgres-age}"
SUPERUSER="${AGE_USER:-dopemux_age}"
SOURCE_DB="${SOURCE_DB:-dopemux_knowledge_graph}"

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
        --help)         sed -n '1,32p' "$0"; exit 0 ;;
        *)              fail "Unknown option: $1" ;;
    esac
done

[ -n "$SLUG" ]          || fail "--slug is required"
[ -n "$WORKSPACE_ID" ]  || fail "--workspace-id is required"
[ -n "$ROLE_PASSWORD" ] || fail "--password is required"

[[ "$SLUG" =~ ^[a-z][a-z0-9_]{0,40}$ ]] || fail "invalid --slug: $SLUG"

TARGET_DB="conport_${SLUG}"
TARGET_ROLE="conport_${SLUG}"

# Copy order respects foreign keys: decisions before anything referencing them.
TABLES=(
    decisions
    progress_entries
    workspace_contexts
    custom_data
    entity_relationships
    session_snapshots
    search_cache
    decision_patterns
    decision_relationships
    adhd_metrics
    review_reminders
)

src_psql() { docker exec -i "$AGE_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$SUPERUSER" -d "$SOURCE_DB" "$@"; }
dst_psql() { docker exec -i -e PGPASSWORD="$ROLE_PASSWORD" "$AGE_CONTAINER" \
                 psql -v ON_ERROR_STOP=1 -U "$TARGET_ROLE" -h 127.0.0.1 -d "$TARGET_DB" "$@"; }

# Escape single quotes for safe SQL literal embedding.
sql_lit() { printf "%s" "$1" | sed "s/'/''/g"; }
WS_LIT="$(sql_lit "$WORKSPACE_ID")"

echo ""
log "═══════════════════════════════════════════════════════════"
log "  ConPort row re-homing"
log "  workspace_id : ${WORKSPACE_ID}"
log "  ${SOURCE_DB} ──▶ ${TARGET_DB}"
log "  Dry run      : ${DRY_RUN}"
log "═══════════════════════════════════════════════════════════"

# macOS ships bash 3.2, which has no associative arrays, and this script must
# run under /bin/bash there. Per-table state goes in a tab-separated temp file
# (table, source row count, column list) instead of `declare -A`.
STATE_FILE="$(mktemp -t conport_rehome)"
trap 'rm -f "$STATE_FILE"' EXIT

state_cols()  { awk -F'\t' -v t="$1" '$1==t {print $3}' "$STATE_FILE"; }
state_count() { awk -F'\t' -v t="$1" '$1==t {print $2}' "$STATE_FILE"; }

step "Comparing schemas and counting source rows"
for t in "${TABLES[@]}"; do
    src_cols=$(src_psql -tAc "SELECT string_agg(quote_ident(column_name), ',' ORDER BY column_name)
                              FROM information_schema.columns
                              WHERE table_schema='public' AND table_name='${t}'")
    dst_cols=$(dst_psql -tAc "SELECT string_agg(quote_ident(column_name), ',' ORDER BY column_name)
                              FROM information_schema.columns
                              WHERE table_schema='public' AND table_name='${t}'")

    if [ -z "$src_cols" ]; then
        log "  ${t}: absent in source — skipping"
        continue
    fi
    if [ "$src_cols" != "$dst_cols" ]; then
        echo "    source: $src_cols"
        echo "    target: $dst_cols"
        fail "column set mismatch for ${t}; refusing to copy"
    fi

    n=$(src_psql -tAc "SELECT count(*) FROM ${t} WHERE workspace_id = '${WS_LIT}'")
    printf '%s\t%s\t%s\n' "$t" "$n" "$src_cols" >> "$STATE_FILE"
    printf '  %-24s %6s rows\n' "$t" "$n"
done
success "Column sets identical for every table copied"

if $DRY_RUN; then
    echo ""
    log "DRY RUN — no rows copied"
    exit 0
fi

step "Copying rows"
for t in "${TABLES[@]}"; do
    c="$(state_cols "$t")"
    [ -n "$c" ] || continue
    n="$(state_count "$t")"
    [ "$n" -gt 0 ] || continue

    printf '  %-24s ' "$t"
    docker exec -i "$AGE_CONTAINER" psql -q -v ON_ERROR_STOP=1 -U "$SUPERUSER" -d "$SOURCE_DB" \
        -c "COPY (SELECT ${c} FROM ${t} WHERE workspace_id = '${WS_LIT}') TO STDOUT" \
      | docker exec -i -e PGPASSWORD="$ROLE_PASSWORD" "$AGE_CONTAINER" \
        psql -q -v ON_ERROR_STOP=1 -U "$TARGET_ROLE" -h 127.0.0.1 -d "$TARGET_DB" \
        -c "COPY ${t} (${c}) FROM STDIN"
    echo "copied ${n}"
done
success "Copy complete"

step "Verifying row counts and UUID identity"
FAILED=0
for t in "${TABLES[@]}"; do
    [ -n "$(state_cols "$t")" ] || continue
    src="$(state_count "$t")"
    dst=$(dst_psql -tAc "SELECT count(*) FROM ${t} WHERE workspace_id = '${WS_LIT}'")
    if [ "$src" = "$dst" ]; then
        [ "$src" -gt 0 ] && printf '  %-24s %s == %s ✅\n' "$t" "$src" "$dst"
    else
        printf '  %-24s %s != %s ❌\n' "$t" "$src" "$dst"
        FAILED=1
    fi
done

# Primary keys must survive the move: a re-homed row is the SAME row, not a copy
# with a new identity. Anything that referenced these UUIDs stays valid.
for t in decisions progress_entries; do
    [ -n "$(state_cols "$t")" ] || continue
    [ "$(state_count "$t")" -gt 0 ] || continue
    missing=$(src_psql -tAc "COPY (SELECT id FROM ${t} WHERE workspace_id='${WS_LIT}') TO STDOUT" \
              | while read -r uuid; do
                    found=$(dst_psql -tAc "SELECT count(*) FROM ${t} WHERE id='${uuid}'")
                    [ "$found" = "1" ] || echo "$uuid"
                done | wc -l | tr -d ' ')
    if [ "$missing" = "0" ]; then
        printf '  %-24s all UUIDs preserved ✅\n' "$t"
    else
        printf '  %-24s %s UUIDs missing ❌\n' "$t" "$missing"
        FAILED=1
    fi
done

[ "$FAILED" -eq 0 ] || fail "verification failed — target left in place for inspection"

echo ""
success "═══════════════════════════════════════════════════════════"
success "  ${WORKSPACE_ID} re-homed into ${TARGET_DB}"
success "  Source rows left intact in ${SOURCE_DB} (archived origin)"
success "═══════════════════════════════════════════════════════════"
echo ""
