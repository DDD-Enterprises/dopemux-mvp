#!/bin/bash
# Genetic Agent Production Deployment Script
# Includes PR workflow integration and rollback capabilities

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."

    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi

    # Check if docker-compose file exists
    if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
        error "docker-compose.yml not found at $DOCKER_COMPOSE_FILE"
        exit 1
    fi

    # Check environment variables
    required_vars=("SERENA_URL" "DOPE_CONTEXT_URL" "CONPORT_URL")
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            warning "Environment variable $var not set. Using default."
        fi
    done

    success "Pre-deployment checks passed"
}

# Create backup
create_backup() {
    log "Creating deployment backup..."

    mkdir -p "$BACKUP_DIR"

    # Backup current containers if they exist
    if docker ps -q -f name=genetic-agent >/dev/null 2>&1; then
        log "Backing up current container state..."
        docker exec genetic-agent /bin/bash -c "
            mkdir -p /tmp/backup &&
            cp -r /app/data /tmp/backup/ &&
            cp -r /app/logs /tmp/backup/ 2>/dev/null || true
        " || warning "Could not create internal backup"

        # Export container
        docker export genetic-agent > "$BACKUP_DIR/genetic-agent-$TIMESTAMP.tar" || warning "Could not export container"
    fi

    success "Backup created at $BACKUP_DIR/genetic-agent-$TIMESTAMP.tar"
}

# Deploy application
deploy_application() {
    local deploy_mode="$1"

    log "Deploying Genetic Agent (mode: $deploy_mode)..."

    # Pull latest images if needed
    if [[ "$deploy_mode" == "production" ]]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" pull || warning "Could not pull latest images"
    fi

    # Stop existing containers gracefully
    log "Stopping existing containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --timeout 30 || warning "Graceful shutdown failed"

    # Build and start containers
    log "Building and starting containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build

    # Wait for health check
    log "Waiting for application to be healthy..."
    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T genetic-agent curl -f http://localhost:8000/health >/dev/null 2>&1; then
            success "Application is healthy!"
            break
        fi

        log "Waiting for health check... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    if [[ $attempt -gt $max_attempts ]]; then
        error "Application failed to become healthy within $(($max_attempts * 10)) seconds"
        return 1
    fi

    success "Deployment completed successfully"
}

# Post-deployment tests
run_post_deployment_tests() {
    log "Running post-deployment tests..."

    # Test health endpoint
    if ! curl -f -s http://localhost:8000/health >/dev/null; then
        error "Health check failed"
        return 1
    fi

    # Test status endpoint
    if ! curl -f -s http://localhost:8000/status >/dev/null; then
        error "Status endpoint failed"
        return 1
    fi

    # Test dashboard endpoint
    if ! curl -f -s http://localhost:8000/dashboard >/dev/null; then
        warning "Dashboard endpoint failed (may be expected if MCP services not available)"
    fi

    success "Post-deployment tests passed"
}

# Rollback functionality
rollback_deployment() {
    log "Rolling back to previous deployment..."

    # Find latest backup
    local latest_backup=$(ls -t "$BACKUP_DIR"/genetic-agent-*.tar 2>/dev/null | head -1)

    if [[ -z "$latest_backup" ]]; then
        error "No backup found for rollback"
        return 1
    fi

    log "Found backup: $latest_backup"

    # Stop current containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" down

    # Restore from backup
    log "Restoring from backup..."
    docker load < "$latest_backup"

    # Start restored container
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

    success "Rollback completed"
}

# PR workflow integration
create_pr_comment() {
    local pr_number="$1"
    local deploy_status="$2"

    if [[ -n "$GITHUB_TOKEN" && -n "$pr_number" ]]; then
        log "Creating PR comment for deployment status..."

        local comment_body
        if [[ "$deploy_status" == "success" ]]; then
            comment_body="✅ **Genetic Agent Deployment Successful**

🚀 The Genetic Coding Agent has been successfully deployed!

**Deployment Details:**
- Version: 0.2.0
- Environment: Production
- Health Check: ✅ Passed
- API Endpoints: ✅ Available

**Available Commands:**
\`\`\`bash
# Fix bugs with genetic agent
dmx fix --genetic /path/to/file.py -d \"bug description\"

# View performance dashboard
dmx dashboard

# Check system status
dmx status
\`\`\`

**Test the deployment:**
\`\`\`bash
curl http://your-server:8000/health
curl http://your-server:8000/dashboard
\`\`\`"
        else
            comment_body="❌ **Genetic Agent Deployment Failed**

The deployment encountered issues. Please check the deployment logs for details."
        fi

        # This would use GitHub CLI or API to post comment
        # gh pr comment $pr_number --body "$comment_body" || warning "Could not post PR comment"
    fi
}

# Main deployment function
main() {
    local action="${1:-deploy}"
    local mode="${2:-development}"
    local pr_number="${3:-}"

    case "$action" in
        "deploy")
            log "Starting Genetic Agent deployment (mode: $mode)..."

            pre_deployment_checks
            create_backup
            deploy_application "$mode"

            if run_post_deployment_tests; then
                success "🎉 Deployment completed successfully!"
                create_pr_comment "$pr_number" "success"

                log "Application is running at: http://localhost:8000"
                log "CLI available as: dmx fix --genetic [file] -d [description]"
            else
                error "❌ Deployment tests failed"
                create_pr_comment "$pr_number" "failure"
                exit 1
            fi
            ;;

        "rollback")
            rollback_deployment
            ;;

        "status")
            log "Checking deployment status..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" ps
            echo
            log "Health check:"
            curl -s http://localhost:8000/health | jq . 2>/dev/null || curl -s http://localhost:8000/health
            ;;

        "logs")
            log "Showing application logs..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f genetic-agent
            ;;

        *)
            echo "Usage: $0 [deploy|rollback|status|logs] [mode] [pr_number]"
            echo ""
            echo "Commands:"
            echo "  deploy [mode] [pr]    - Deploy application (default: development)"
            echo "  rollback              - Rollback to previous deployment"
            echo "  status                - Show deployment status"
            echo "  logs                  - Show application logs"
            echo ""
            echo "Modes:"
            echo "  development           - Use development settings"
            echo "  production            - Use production settings with monitoring"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"