#!/bin/bash
# Dopemux ConPort Knowledge Graph Backup Script
# ADHD-Optimized: Clear progress indicators and status messages
#
# Usage:
#   ./scripts/backup-conport-kg.sh              # Full backup (all databases)
#   ./scripts/backup-conport-kg.sh --age-only   # PostgreSQL AGE only
#   ./scripts/backup-conport-kg.sh --postgres-only # PostgreSQL Primary only
#   ./scripts/backup-conport-kg.sh --redis-only # Redis only
#
# Cron Example (daily at 2 AM):
#   0 2 * * * /path/to/dopemux-mvp/scripts/backup-conport-kg.sh >> /var/log/dopemux-backup.log 2>&1

set -euo pipefail

# ===================================================================
# CONFIGURATION
# ===================================================================

# Backup directory (create if doesn't exist)
BACKUP_ROOT="${BACKUP_ROOT:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Retention policy (days)
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# Docker container names
AGE_CONTAINER="dopemux-postgres-age"
POSTGRES_CONTAINER="dopemux-postgres-primary"
REDIS_PRIMARY_CONTAINER="dopemux-redis-primary"
REDIS_LEANTIME_CONTAINER="dopemux-redis-leantime"

# Database credentials (from .env or defaults)
AGE_USER="${AGE_USER:-dopemux_age}"
AGE_DB="${AGE_DB:-dopemux_knowledge_graph}"
POSTGRES_USER="${POSTGRES_USER:-dopemux}"
POSTGRES_DB="${POSTGRES_DB:-dopemux_unified}"

# ADHD-friendly color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

log() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

progress() {
    echo -e "${BLUE}🔄 $1${NC}"
}

# Check if container is running
check_container() {
    local container=$1
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        error "Container '${container}' is not running"
        return 1
    fi
    return 0
}

# Create backup directory
create_backup_dir() {
    local dir=$1
    mkdir -p "$dir"
    if [ $? -eq 0 ]; then
        success "Backup directory ready: $dir"
    else
        error "Failed to create backup directory: $dir"
        exit 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    local backup_dir=$1
    local retention=$2

    log "Cleaning up backups older than ${retention} days in ${backup_dir}"

    if [ -d "$backup_dir" ]; then
        local deleted_count=$(find "$backup_dir" -type f -name "*.sql*" -mtime +${retention} -delete -print | wc -l | tr -d ' ')
        local rdb_deleted=$(find "$backup_dir" -type f -name "*.rdb" -mtime +${retention} -delete -print | wc -l | tr -d ' ')
        total_deleted=$((deleted_count + rdb_deleted))

        if [ $total_deleted -gt 0 ]; then
            success "Deleted ${total_deleted} old backup(s)"
        else
            log "No old backups to delete"
        fi
    fi
}

# ===================================================================
# BACKUP FUNCTIONS
# ===================================================================

# Backup PostgreSQL AGE (ConPort Knowledge Graph)
backup_age() {
    progress "Starting PostgreSQL AGE backup..."

    local backup_dir="${BACKUP_ROOT}/dopemux-age"
    create_backup_dir "$backup_dir"

    if ! check_container "$AGE_CONTAINER"; then
        return 1
    fi

    local backup_file="${backup_dir}/age_backup_${TIMESTAMP}.sql"
    local backup_compressed="${backup_file}.gz"

    log "Dumping database: ${AGE_DB}"
    docker exec "$AGE_CONTAINER" pg_dump -U "$AGE_USER" -d "$AGE_DB" > "$backup_file"

    if [ $? -eq 0 ]; then
        # Compress backup
        gzip "$backup_file"
        local size=$(du -h "$backup_compressed" | cut -f1)
        success "PostgreSQL AGE backup complete: ${backup_compressed} (${size})"

        # Cleanup old backups
        cleanup_old_backups "$backup_dir" "$RETENTION_DAYS"
        return 0
    else
        error "PostgreSQL AGE backup failed"
        return 1
    fi
}

# Backup PostgreSQL Primary (Unified Database)
backup_postgres() {
    progress "Starting PostgreSQL Primary backup..."

    local backup_dir="${BACKUP_ROOT}/dopemux-postgres"
    create_backup_dir "$backup_dir"

    if ! check_container "$POSTGRES_CONTAINER"; then
        return 1
    fi

    local backup_file="${backup_dir}/postgres_backup_${TIMESTAMP}.sql"
    local backup_compressed="${backup_file}.gz"

    log "Dumping database: ${POSTGRES_DB}"
    docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$backup_file"

    if [ $? -eq 0 ]; then
        # Compress backup
        gzip "$backup_file"
        local size=$(du -h "$backup_compressed" | cut -f1)
        success "PostgreSQL Primary backup complete: ${backup_compressed} (${size})"

        # Cleanup old backups
        cleanup_old_backups "$backup_dir" "$RETENTION_DAYS"
        return 0
    else
        error "PostgreSQL Primary backup failed"
        return 1
    fi
}

# Backup Redis (Primary + Leantime)
backup_redis() {
    progress "Starting Redis backup..."

    local backup_dir="${BACKUP_ROOT}/dopemux-redis"
    create_backup_dir "$backup_dir"

    # Backup Redis Primary
    if check_container "$REDIS_PRIMARY_CONTAINER"; then
        local primary_backup="${backup_dir}/redis_primary_${TIMESTAMP}.rdb"

        log "Creating Redis Primary snapshot..."
        docker exec "$REDIS_PRIMARY_CONTAINER" redis-cli BGSAVE > /dev/null
        sleep 2  # Wait for background save

        docker cp "${REDIS_PRIMARY_CONTAINER}:/data/dump.rdb" "$primary_backup" 2>/dev/null

        if [ $? -eq 0 ]; then
            local size=$(du -h "$primary_backup" | cut -f1)
            success "Redis Primary backup complete: ${primary_backup} (${size})"
        else
            error "Redis Primary backup failed"
        fi
    fi

    # Backup Redis Leantime
    if check_container "$REDIS_LEANTIME_CONTAINER"; then
        local leantime_backup="${backup_dir}/redis_leantime_${TIMESTAMP}.rdb"

        log "Creating Redis Leantime snapshot..."
        docker exec "$REDIS_LEANTIME_CONTAINER" redis-cli BGSAVE > /dev/null
        sleep 2  # Wait for background save

        docker cp "${REDIS_LEANTIME_CONTAINER}:/data/dump.rdb" "$leantime_backup" 2>/dev/null

        if [ $? -eq 0 ]; then
            local size=$(du -h "$leantime_backup" | cut -f1)
            success "Redis Leantime backup complete: ${leantime_backup} (${size})"
        else
            error "Redis Leantime backup failed"
        fi
    fi

    # Cleanup old backups
    cleanup_old_backups "$backup_dir" "$RETENTION_DAYS"
}

# ===================================================================
# MAIN EXECUTION
# ===================================================================

main() {
    echo ""
    log "═══════════════════════════════════════════════════════════"
    log "  Dopemux ConPort Knowledge Graph Backup"
    log "  Timestamp: ${TIMESTAMP}"
    log "  Retention: ${RETENTION_DAYS} days"
    log "═══════════════════════════════════════════════════════════"
    echo ""

    # Parse command-line arguments
    AGE_ONLY=false
    POSTGRES_ONLY=false
    REDIS_ONLY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --age-only)
                AGE_ONLY=true
                shift
                ;;
            --postgres-only)
                POSTGRES_ONLY=true
                shift
                ;;
            --redis-only)
                REDIS_ONLY=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --age-only       Backup PostgreSQL AGE (ConPort KG) only"
                echo "  --postgres-only  Backup PostgreSQL Primary only"
                echo "  --redis-only     Backup Redis instances only"
                echo "  --help           Show this help message"
                echo ""
                echo "Environment Variables:"
                echo "  BACKUP_ROOT      Backup directory (default: ./backups)"
                echo "  RETENTION_DAYS   Days to keep backups (default: 30)"
                echo ""
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    # Execute backups based on flags
    local exit_code=0

    if [ "$AGE_ONLY" = true ]; then
        backup_age || exit_code=$?
    elif [ "$POSTGRES_ONLY" = true ]; then
        backup_postgres || exit_code=$?
    elif [ "$REDIS_ONLY" = true ]; then
        backup_redis || exit_code=$?
    else
        # Full backup (all databases)
        backup_age || exit_code=$?
        backup_postgres || exit_code=$?
        backup_redis || exit_code=$?
    fi

    echo ""
    if [ $exit_code -eq 0 ]; then
        success "═══════════════════════════════════════════════════════════"
        success "  Backup Complete! All systems backed up successfully."
        success "═══════════════════════════════════════════════════════════"
    else
        warn "═══════════════════════════════════════════════════════════"
        warn "  Backup completed with some errors. Check logs above."
        warn "═══════════════════════════════════════════════════════════"
    fi
    echo ""

    exit $exit_code
}

# Run main function
main "$@"
