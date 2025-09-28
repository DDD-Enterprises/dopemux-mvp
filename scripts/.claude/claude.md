# Scripts and Automation Context

**Scope**: Automation scripts, utilities, and development tools
**Inherits**: Two-Plane Architecture from project root
**Focus**: Reliable automation with ADHD-friendly scripting patterns and clear feedback

## 🛠️ Script Categories

### Development Automation
- **Setup Scripts**: Environment initialization and dependency management
- **Build Scripts**: Compilation, packaging, and deployment automation
- **Test Scripts**: Automated testing and quality assurance workflows
- **Maintenance Scripts**: Database migrations, cleanup, and system maintenance

### ADHD-Optimized Scripting
- **Clear Output**: Verbose, informative feedback during execution
- **Error Handling**: Graceful failure with helpful error messages
- **Progress Indicators**: Visual progress for long-running operations
- **Idempotent Operations**: Safe to run multiple times without side effects

## 🎯 Scripting Standards

### Shell Script Standards
```bash
#!/bin/bash

# Script: setup-development-environment.sh
# Purpose: Initialize development environment for new developers
# Usage: ./scripts/setup-development-environment.sh
# ADHD-Friendly: Clear progress indicators and error messages

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color codes for visual feedback
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Progress tracking
show_progress() {
    local current=$1
    local total=$2
    local description=$3
    echo -e "${BLUE}[${current}/${total}]${NC} ${description}"
}
```

### Python Script Standards
```python
#!/usr/bin/env python3
"""
Script: migrate_database.py
Purpose: Handle database migrations with rollback support
Usage: python scripts/migrate_database.py --version 001
ADHD-Friendly: Clear progress and detailed error information
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Configure logging for clear feedback
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_argument_parser() -> argparse.ArgumentParser:
    """Configure command-line arguments with clear help text."""
    parser = argparse.ArgumentParser(
        description="Database migration tool with ADHD-friendly output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/migrate_database.py --version 001
  python scripts/migrate_database.py --rollback --version 001
  python scripts/migrate_database.py --list
        """
    )

    parser.add_argument(
        "--version",
        help="Migration version to apply (e.g., 001, 002)"
    )

    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Rollback to specified version instead of applying"
    )

    return parser

def main() -> int:
    """Main script execution with error handling."""
    try:
        parser = setup_argument_parser()
        args = parser.parse_args()

        logger.info("🚀 Starting database migration process")

        # Script logic here

        logger.info("✅ Migration completed successfully")
        return 0

    except KeyboardInterrupt:
        logger.warning("⚠️ Migration cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## 🚀 Agent Coordination

### Developer Agent (Primary)
**For Script Development**:
- Create reliable automation scripts with proper error handling
- Ensure scripts follow project coding standards
- Implement clear progress feedback and logging
- Test scripts thoroughly before deployment

### Researcher Agent (Support)
**For Script Patterns**:
- Research automation best practices and tools
- Find solutions for complex scripting challenges
- Validate scripting approaches against industry standards
- Provide examples of effective automation patterns

### Script Quality Standards
- **Reliability**: Scripts should handle edge cases and failures gracefully
- **Usability**: Clear help text and intuitive command-line interfaces
- **Maintainability**: Well-documented code with clear variable names
- **Performance**: Efficient execution appropriate for the task

## 🔧 Common Script Patterns

### Environment Setup
```bash
# scripts/setup-mcp-servers.sh
setup_mcp_server() {
    local server_name=$1
    local server_path=$2

    log_info "Setting up MCP server: ${server_name}"

    if [ -d "${server_path}" ]; then
        log_warning "Server directory already exists: ${server_path}"
        return 0
    fi

    # Setup logic here

    log_success "MCP server ${server_name} setup complete"
}

# Progress tracking for multiple operations
servers=("conport" "task-master" "serena")
total=${#servers[@]}

for i in "${!servers[@]}"; do
    show_progress $((i+1)) ${total} "Setting up ${servers[i]}"
    setup_mcp_server "${servers[i]}" "services/${servers[i]}"
done
```

### Database Operations
```python
# scripts/database_utils.py
class DatabaseMigrator:
    """Handle database migrations with ADHD-friendly feedback."""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    def apply_migration(self, version: str) -> bool:
        """Apply migration with clear progress reporting."""
        try:
            logger.info(f"📄 Loading migration {version}")
            migration_sql = self._load_migration_file(version)

            logger.info(f"🔄 Applying migration {version}")
            self._execute_migration(migration_sql)

            logger.info(f"📝 Recording migration {version}")
            self._record_migration(version)

            logger.info(f"✅ Migration {version} completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Migration {version} failed: {e}")
            return False
```

### System Maintenance
```bash
# scripts/cleanup-docker.sh
cleanup_docker_resources() {
    log_info "🧹 Cleaning up Docker resources"

    # Remove stopped containers
    stopped_containers=$(docker ps -aq --filter "status=exited")
    if [ -n "$stopped_containers" ]; then
        log_info "Removing stopped containers"
        docker rm $stopped_containers
        log_success "Stopped containers removed"
    else
        log_info "No stopped containers to remove"
    fi

    # Remove unused images
    log_info "Removing unused Docker images"
    docker image prune -f
    log_success "Unused images removed"

    # Remove unused volumes
    log_info "Removing unused Docker volumes"
    docker volume prune -f
    log_success "Unused volumes removed"

    log_success "🎉 Docker cleanup completed"
}
```

## 📁 Script Organization

### Directory Structure
```
scripts/
├── setup/            # Environment and system setup scripts
├── database/         # Database-related operations
├── deployment/       # Deployment and packaging scripts
├── maintenance/      # System maintenance and cleanup
├── testing/          # Test automation and validation
├── utils/            # Shared utilities and helper functions
└── templates/        # Script templates for new automation
```

### Script Naming Conventions
- **Descriptive Names**: `setup-development-environment.sh`
- **Action-Oriented**: `deploy-to-staging.sh`
- **Clear Purpose**: `migrate-database-to-version.py`
- **Consistent Format**: `[action]-[target]-[context].[ext]`

## 🎯 ADHD-Friendly Features

### Visual Progress Feedback
```bash
# Progress bar implementation
show_progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local filled=$((current * width / total))
    local empty=$((width - filled))

    printf "\r["
    printf "%*s" $filled | tr ' ' '█'
    printf "%*s" $empty | tr ' ' '░'
    printf "] %d%% (%d/%d)" $percentage $current $total
}
```

### Clear Error Messages
```python
def handle_script_error(error: Exception, context: str) -> None:
    """Provide clear, actionable error messages."""
    error_type = type(error).__name__

    logger.error(f"❌ {error_type} in {context}")
    logger.error(f"📝 Error details: {str(error)}")

    # Provide helpful suggestions based on error type
    if isinstance(error, FileNotFoundError):
        logger.error("💡 Suggestion: Check if the required file exists")
    elif isinstance(error, PermissionError):
        logger.error("💡 Suggestion: Check file permissions or run with appropriate privileges")

    logger.error("🔍 For more help, check the script documentation or contact support")
```

### Execution Summaries
```bash
# End-of-script summary
print_execution_summary() {
    local success_count=$1
    local failure_count=$2
    local total_time=$3

    echo
    echo "🎯 Execution Summary"
    echo "===================="
    echo "✅ Successful operations: ${success_count}"
    echo "❌ Failed operations: ${failure_count}"
    echo "⏱️ Total execution time: ${total_time}s"

    if [ $failure_count -eq 0 ]; then
        echo "🎉 All operations completed successfully!"
    else
        echo "⚠️ Some operations failed. Check the log above for details."
    fi
}
```

---

**Automation Excellence**: Reliable, well-tested scripts with comprehensive error handling
**ADHD Integration**: Clear feedback, progress indicators, and user-friendly interfaces
**Maintainability**: Well-organized, documented automation that's easy to understand and modify