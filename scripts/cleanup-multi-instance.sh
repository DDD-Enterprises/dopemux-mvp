#!/bin/bash
# Phase 1 Cleanup Script for Dopemux Architecture Simplification
#
# This script safely removes multi-instance Docker components and other
# unused configurations while preserving single-instance functionality.
#
# Safety features:
# - Tests single-instance Docker first
# - Archives before deletion
# - Creates rollback point
# - Dry-run mode available

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ARCHIVE_DIR="$PROJECT_ROOT/.archive/multi-instance-$(date +%Y%m%d-%H%M%S)"
DRY_RUN=false
FORCE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            echo -e "${YELLOW}🔍 DRY RUN MODE - No changes will be made${NC}"
            shift
            ;;
        --force|-f)
            FORCE=true
            shift
            ;;
        --help|-h)
            echo "Dopemux Multi-Instance Cleanup Script"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --dry-run, -n    Preview changes without making them"
            echo "  --force, -f      Skip confirmation prompts"
            echo "  --help, -h       Show this help message"
            echo ""
            echo "This script removes multi-instance Docker components and unused"
            echo "configurations while preserving single-instance functionality."
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print status messages
print_status() {
    echo -e "${CYAN}$1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to execute or simulate commands based on dry-run mode
execute_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] Would execute: $@${NC}"
    else
        "$@"
    fi
}

# Function to test single-instance Docker
test_single_instance_docker() {
    print_status "📋 Testing single-instance Docker functionality..."

    # Check if docker-compose.yml exists
    if [ ! -f "$PROJECT_ROOT/docker/mcp-servers/docker-compose.yml" ]; then
        print_error "Single-instance docker-compose.yml not found!"
        exit 1
    fi

    # Test docker-compose config
    cd "$PROJECT_ROOT/docker/mcp-servers"
    if docker-compose -f docker-compose.yml config > /dev/null 2>&1; then
        print_success "Single-instance docker-compose.yml is valid"
    else
        print_error "Single-instance docker-compose.yml validation failed!"
        echo "Please fix the configuration before running cleanup"
        exit 1
    fi

    # Check if any services are currently running
    if docker-compose -f docker-compose.yml ps --services --filter "status=running" 2>/dev/null | grep -q .; then
        print_warning "Docker services are currently running"
        if [ "$FORCE" = false ]; then
            read -p "Continue with cleanup? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Cleanup cancelled"
                exit 0
            fi
        fi
    else
        print_status "No Docker services currently running"
    fi

    cd "$PROJECT_ROOT"
}

# Function to create archive directory
create_archive() {
    print_status "📦 Creating archive directory..."

    if [ "$DRY_RUN" = false ]; then
        mkdir -p "$ARCHIVE_DIR"
        print_success "Archive directory created: $ARCHIVE_DIR"
    else
        print_warning "[DRY RUN] Would create archive at: $ARCHIVE_DIR"
    fi
}

# Function to archive multi-instance components
archive_multi_instance() {
    print_status "🗄️  Archiving multi-instance Docker components..."

    # List of files to archive
    local files_to_archive=(
        "docker/mcp-servers/docker-compose.multi-instance.yml"
        "docker/mcp-servers/launch-instance.sh"
        "docker-compose.unified.yml"
    )

    for file in "${files_to_archive[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            if [ "$DRY_RUN" = false ]; then
                # Create directory structure in archive
                local dir=$(dirname "$file")
                mkdir -p "$ARCHIVE_DIR/$dir"
                cp "$PROJECT_ROOT/$file" "$ARCHIVE_DIR/$file"
                print_success "Archived: $file"
            else
                print_warning "[DRY RUN] Would archive: $file"
            fi
        else
            print_status "Not found (skipping): $file"
        fi
    done
}

# Function to remove multi-instance files
remove_multi_instance_files() {
    print_status "🗑️  Removing multi-instance Docker files..."

    local files_to_remove=(
        "docker/mcp-servers/docker-compose.multi-instance.yml"
        "docker/mcp-servers/launch-instance.sh"
        "docker-compose.unified.yml"
    )

    for file in "${files_to_remove[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            execute_cmd rm -f "$PROJECT_ROOT/$file"
            if [ "$DRY_RUN" = false ]; then
                print_success "Removed: $file"
            fi
        fi
    done
}

# Function to remove MetaMCP directory
remove_metamcp() {
    print_status "🗑️  Removing MetaMCP directory..."

    if [ -d "$PROJECT_ROOT/docker/metamcp" ]; then
        # Archive first
        if [ "$DRY_RUN" = false ]; then
            mkdir -p "$ARCHIVE_DIR/docker"
            cp -r "$PROJECT_ROOT/docker/metamcp" "$ARCHIVE_DIR/docker/"
            print_success "Archived MetaMCP directory"
        else
            print_warning "[DRY RUN] Would archive MetaMCP directory"
        fi

        # Then remove
        execute_cmd rm -rf "$PROJECT_ROOT/docker/metamcp"
        if [ "$DRY_RUN" = false ]; then
            print_success "Removed MetaMCP directory"
        fi
    else
        print_status "MetaMCP directory not found (already removed)"
    fi
}

# Function to remove broker configurations
remove_broker_configs() {
    print_status "🗑️  Removing broker configurations..."

    local broker_files=(
        "config/mcp/broker.yaml"
        "config/mcp/broker-minimal.yaml"
    )

    for file in "${broker_files[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            # Archive first
            if [ "$DRY_RUN" = false ]; then
                local dir=$(dirname "$file")
                mkdir -p "$ARCHIVE_DIR/$dir"
                cp "$PROJECT_ROOT/$file" "$ARCHIVE_DIR/$file"
            else
                print_warning "[DRY RUN] Would archive: $file"
            fi

            # Then remove
            execute_cmd rm -f "$PROJECT_ROOT/$file"
            if [ "$DRY_RUN" = false ]; then
                print_success "Removed: $file"
            fi
        fi
    done
}

# Function to remove migration scripts
remove_migration_scripts() {
    print_status "🗑️  Removing obsolete migration scripts..."

    local scripts_to_remove=(
        "scripts/configure-metamcp-phase1a.sh"
        "scripts/migrate-to-unified.sh"
    )

    for script in "${scripts_to_remove[@]}"; do
        if [ -f "$PROJECT_ROOT/$script" ]; then
            # Archive first
            if [ "$DRY_RUN" = false ]; then
                local dir=$(dirname "$script")
                mkdir -p "$ARCHIVE_DIR/$dir"
                cp "$PROJECT_ROOT/$script" "$ARCHIVE_DIR/$script"
            else
                print_warning "[DRY RUN] Would archive: $script"
            fi

            # Then remove
            execute_cmd rm -f "$PROJECT_ROOT/$script"
            if [ "$DRY_RUN" = false ]; then
                print_success "Removed: $script"
            fi
        fi
    done
}

# Function to clean up references in scripts
cleanup_script_references() {
    print_status "🧹 Cleaning up references in remaining scripts..."

    # Update start-all-mcp-servers.sh to remove multi-instance mentions
    local start_script="$PROJECT_ROOT/docker/mcp-servers/start-all-mcp-servers.sh"
    if [ -f "$start_script" ]; then
        if [ "$DRY_RUN" = false ]; then
            # Create backup
            cp "$start_script" "$start_script.bak"

            # Remove references to multi-instance
            sed -i.tmp '/multi-instance/d' "$start_script" 2>/dev/null || \
            sed -i '' '/multi-instance/d' "$start_script" 2>/dev/null || true

            # Clean up temp files
            rm -f "$start_script.tmp"

            print_success "Cleaned references in start-all-mcp-servers.sh"
        else
            print_warning "[DRY RUN] Would clean references in start-all-mcp-servers.sh"
        fi
    fi
}

# Function to create git tag for rollback
create_rollback_tag() {
    print_status "🏷️  Creating Git tag for rollback point..."

    if [ "$DRY_RUN" = false ]; then
        # Check if we're in a git repository
        if git rev-parse --git-dir > /dev/null 2>&1; then
            local tag_name="pre-simplification-$(date +%Y%m%d-%H%M%S)"
            git tag -a "$tag_name" -m "Before architecture simplification (multi-instance removal)" || true
            print_success "Created Git tag: $tag_name"
            echo "To rollback: git checkout $tag_name"
        else
            print_warning "Not in a git repository, skipping tag creation"
        fi
    else
        print_warning "[DRY RUN] Would create Git tag: pre-simplification-$(date +%Y%m%d-%H%M%S)"
    fi
}

# Function to update CHANGELOG
update_changelog() {
    print_status "📝 Updating CHANGELOG..."

    local changelog="$PROJECT_ROOT/CHANGELOG.md"
    local date=$(date +%Y-%m-%d)
    local entry="## Architecture Simplification - $date

### Removed
- Multi-instance Docker support (docker-compose.multi-instance.yml)
- MetaMCP broker configurations
- Unified Docker compose configuration
- Legacy migration scripts

### Changed
- Simplified to single-instance Docker architecture
- Enhanced Git worktree support for parallel development

### Preserved
- Single-instance Docker functionality
- All MCP server configurations
- Core dopemux features
"

    if [ "$DRY_RUN" = false ]; then
        if [ -f "$changelog" ]; then
            # Create temp file with new entry
            echo "$entry" > /tmp/changelog_entry.tmp
            echo "" >> /tmp/changelog_entry.tmp
            cat "$changelog" >> /tmp/changelog_entry.tmp
            mv /tmp/changelog_entry.tmp "$changelog"
            print_success "Updated CHANGELOG.md"
        else
            echo "$entry" > "$changelog"
            print_success "Created CHANGELOG.md"
        fi
    else
        print_warning "[DRY RUN] Would update CHANGELOG.md"
    fi
}

# Function to display summary
display_summary() {
    echo ""
    print_status "📊 Cleanup Summary"
    echo "=================="

    if [ "$DRY_RUN" = true ]; then
        echo "This was a DRY RUN - no actual changes were made"
        echo ""
        echo "Files that would be removed:"
        echo "  • docker/mcp-servers/docker-compose.multi-instance.yml"
        echo "  • docker/mcp-servers/launch-instance.sh"
        echo "  • docker-compose.unified.yml"
        echo "  • docker/metamcp/ (entire directory)"
        echo "  • config/mcp/broker*.yaml"
        echo "  • scripts/configure-metamcp-phase1a.sh"
        echo "  • scripts/migrate-to-unified.sh"
        echo ""
        echo "To perform actual cleanup, run without --dry-run flag"
    else
        echo "✅ Cleanup completed successfully!"
        echo ""
        echo "Archive created at: $ARCHIVE_DIR"
        echo ""
        echo "Next steps:"
        echo "1. Test single-instance Docker: cd docker/mcp-servers && ./start-all-mcp-servers.sh"
        echo "2. Test worktree commands: dopemux worktree list"
        echo "3. If issues arise, rollback using the Git tag created"
    fi
}

# Main execution
main() {
    echo -e "${CYAN}🚀 Dopemux Architecture Simplification - Phase 1 Cleanup${NC}"
    echo "========================================================="
    echo ""

    # Confirm with user unless forced
    if [ "$FORCE" = false ] && [ "$DRY_RUN" = false ]; then
        print_warning "This script will remove multi-instance Docker components"
        echo "Single-instance Docker functionality will be preserved"
        echo ""
        read -p "Continue with cleanup? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Cleanup cancelled"
            exit 0
        fi
    fi

    # Execute cleanup steps
    test_single_instance_docker
    create_archive
    create_rollback_tag
    archive_multi_instance
    remove_multi_instance_files
    remove_metamcp
    remove_broker_configs
    remove_migration_scripts
    cleanup_script_references
    update_changelog

    # Display summary
    display_summary
}

# Run main function
main