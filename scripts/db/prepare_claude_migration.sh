#!/bin/bash

# CLAUDE.md Migration Preparation Script
# Version: 2.0.0
# Created: September 27, 2025
# Purpose: Prepare for CLAUDE.md modular architecture migration

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WORKSPACE_ROOT="/Users/hue/code/dopemux-mvp"
BACKUP_DIR="${WORKSPACE_ROOT}/.claude/backups/$(date +%Y%m%d_%H%M%S)"
CHECKPOINT_DIR="${WORKSPACE_ROOT}/CHECKPOINT"

echo -e "${BLUE}📋 CLAUDE.md Migration Preparation${NC}"
echo "=================================================="
echo "Date: $(date)"
echo "Workspace: ${WORKSPACE_ROOT}"
echo ""

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "----------------------------------------"
}

# Function to check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"

    local errors=0

    # Check if in correct directory
    if [[ "$(pwd)" != "${WORKSPACE_ROOT}" ]]; then
        echo -e "${RED}❌ Must run from ${WORKSPACE_ROOT}${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✅ Running from correct directory${NC}"
    fi

    # Check for required tools
    for tool in jq wc find; do
        if ! command -v "$tool" &> /dev/null; then
            echo -e "${RED}❌ Required tool missing: $tool${NC}"
            ((errors++))
        else
            echo -e "${GREEN}✅ Tool available: $tool${NC}"
        fi
    done

    # Check if ConPort is available
    if ! ls context_portal/context.db &> /dev/null; then
        echo -e "${YELLOW}⚠️  ConPort database not found${NC}"
    else
        echo -e "${GREEN}✅ ConPort database found${NC}"
    fi

    if [[ $errors -gt 0 ]]; then
        echo -e "\n${RED}❌ Prerequisites check failed. Please fix errors before proceeding.${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

# Function to analyze current files
analyze_current_files() {
    print_section "Analyzing Current CLAUDE.md Files"

    echo "Discovering CLAUDE.md files..."
    find . -name "CLAUDE.md" -o -name "claude.md" | head -10 | while read -r file; do
        if [[ -f "$file" ]]; then
            local lines=$(wc -l < "$file")
            local size=$(du -h "$file" | cut -f1)
            echo "  📄 $file: $lines lines ($size)"
        fi
    done

    echo ""
    echo "Primary files analysis:"

    # Global file
    local global_file="$HOME/.claude/CLAUDE.md"
    if [[ -f "$global_file" ]]; then
        local global_lines=$(wc -l < "$global_file")
        echo "  🌍 Global CLAUDE.md: $global_lines lines"
    else
        echo -e "  ${YELLOW}⚠️  Global CLAUDE.md not found${NC}"
    fi

    # Project file
    local project_file="./.claude/CLAUDE.md"
    if [[ -f "$project_file" ]]; then
        local project_lines=$(wc -l < "$project_file")
        echo "  📁 Project CLAUDE.md: $project_lines lines"

        # Estimate token count (rough: 1 line ≈ 15 tokens)
        local estimated_tokens=$((project_lines * 15))
        echo "  🔢 Estimated tokens: ~$estimated_tokens"

        if [[ $estimated_tokens -gt 10000 ]]; then
            echo -e "  ${RED}❌ High token usage detected (>10K)${NC}"
        elif [[ $estimated_tokens -gt 5000 ]]; then
            echo -e "  ${YELLOW}⚠️  Moderate token usage (>5K)${NC}"
        else
            echo -e "  ${GREEN}✅ Reasonable token usage (<5K)${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠️  Project CLAUDE.md not found${NC}"
    fi

    # Check for command files
    if [[ -d "./.claude/commands" ]]; then
        local command_count=$(find ./.claude/commands -name "*.md" | wc -l)
        echo "  📋 Slash commands found: $command_count files"
    else
        echo -e "  ${YELLOW}⚠️  No commands directory found${NC}"
    fi
}

# Function to create backups
create_backups() {
    print_section "Creating Backups"

    mkdir -p "$BACKUP_DIR"
    echo "Backup directory: $BACKUP_DIR"

    # Backup global file
    local global_file="$HOME/.claude/CLAUDE.md"
    if [[ -f "$global_file" ]]; then
        cp "$global_file" "$BACKUP_DIR/global_CLAUDE.md.bak"
        echo -e "${GREEN}✅ Backed up global CLAUDE.md${NC}"
    fi

    # Backup project files
    if [[ -f "./.claude/CLAUDE.md" ]]; then
        cp "./.claude/CLAUDE.md" "$BACKUP_DIR/project_CLAUDE.md.bak"
        echo -e "${GREEN}✅ Backed up project CLAUDE.md${NC}"
    fi

    # Backup commands directory
    if [[ -d "./.claude/commands" ]]; then
        cp -r "./.claude/commands" "$BACKUP_DIR/commands_backup"
        echo -e "${GREEN}✅ Backed up commands directory${NC}"
    fi

    # Backup entire .claude directory
    if [[ -d "./.claude" ]]; then
        tar -czf "$BACKUP_DIR/full_claude_backup.tar.gz" ./.claude
        echo -e "${GREEN}✅ Created full .claude directory archive${NC}"
    fi

    # Create restore script
    cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
# CLAUDE.md Restore Script
echo "🔄 Restoring CLAUDE.md files from backup..."

BACKUP_DIR="$(dirname "$0")"
PROJECT_ROOT="$(cd "$BACKUP_DIR/../../../.." && pwd)"

# Restore global file
if [[ -f "$BACKUP_DIR/global_CLAUDE.md.bak" ]]; then
    cp "$BACKUP_DIR/global_CLAUDE.md.bak" "$HOME/.claude/CLAUDE.md"
    echo "✅ Restored global CLAUDE.md"
fi

# Restore project file
if [[ -f "$BACKUP_DIR/project_CLAUDE.md.bak" ]]; then
    cp "$BACKUP_DIR/project_CLAUDE.md.bak" "$PROJECT_ROOT/.claude/CLAUDE.md"
    echo "✅ Restored project CLAUDE.md"
fi

# Restore commands
if [[ -d "$BACKUP_DIR/commands_backup" ]]; then
    rm -rf "$PROJECT_ROOT/.claude/commands"
    cp -r "$BACKUP_DIR/commands_backup" "$PROJECT_ROOT/.claude/commands"
    echo "✅ Restored commands directory"
fi

echo "🎉 Restore complete!"
EOF

    chmod +x "$BACKUP_DIR/restore.sh"
    echo -e "${GREEN}✅ Created restore script${NC}"

    echo ""
    echo "Backup summary:"
    du -sh "$BACKUP_DIR"/*
}

# Function to analyze token usage patterns
analyze_token_patterns() {
    print_section "Analyzing Token Usage Patterns"

    if [[ -f "./.claude/CLAUDE.md" ]]; then
        local file="./.claude/CLAUDE.md"
        echo "Analyzing content patterns in $file..."

        # Look for major sections
        echo ""
        echo "Major sections found:"
        grep -n "^##" "$file" | head -10 | while read -r line; do
            echo "  📖 $line"
        done

        # Count import statements
        local imports=$(grep -c "@import\|@lazy" "$file" 2>/dev/null || echo "0")
        echo ""
        echo "Import statements: $imports"

        # Look for command patterns
        local commands=$(grep -c "^/\|^\-.*/" "$file" 2>/dev/null || echo "0")
        echo "Command references: $commands"

        # ConPort command analysis
        local conport_lines=$(grep -n "mcp__conport" "$file" | wc -l)
        echo "ConPort command lines: $conport_lines"

        # Sprint template analysis
        local sprint_lines=$(grep -n "sprint\|mem4sprint" "$file" | wc -l)
        echo "Sprint-related lines: $sprint_lines"

    else
        echo -e "${YELLOW}⚠️  No project CLAUDE.md found for analysis${NC}"
    fi
}

# Function to check readiness
check_implementation_readiness() {
    print_section "Implementation Readiness Check"

    echo "Checking system dependencies..."

    # Check ConPort status
    if [[ -f "context_portal/context.db" ]]; then
        echo -e "${GREEN}✅ ConPort database present${NC}"
    else
        echo -e "${RED}❌ ConPort database missing${NC}"
    fi

    # Check MCP servers
    if [[ -f "docker/mcp-servers/docker-compose.yml" ]]; then
        echo -e "${GREEN}✅ MCP server configuration found${NC}"
    else
        echo -e "${YELLOW}⚠️  MCP server configuration not found${NC}"
    fi

    # Check task management
    if [[ -d "scripts" ]]; then
        echo -e "${GREEN}✅ Scripts directory present${NC}"
    else
        echo -e "${YELLOW}⚠️  Scripts directory not found${NC}"
    fi

    echo ""
    echo "Readiness assessment:"
    echo "- Task management system: [MANUAL CHECK REQUIRED]"
    echo "- Memory systems stable: [MANUAL CHECK REQUIRED]"
    echo "- MCP ecosystem operational: [MANUAL CHECK REQUIRED]"
    echo "- Team consensus: [MANUAL CHECK REQUIRED]"

    echo ""
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo "1. Verify all systems are stable and locked in"
    echo "2. Review implementation tracker: CHECKPOINT/CLAUDE_MD_IMPLEMENTATION_TRACKER.md"
    echo "3. When ready, begin Phase 1 implementation"
    echo "4. Use backup restore script if rollback needed: $BACKUP_DIR/restore.sh"
}

# Function to create token measurement baseline
create_token_baseline() {
    print_section "Creating Token Usage Baseline"

    local baseline_file="$CHECKPOINT_DIR/token_usage_baseline.md"

    cat > "$baseline_file" << EOF
# Token Usage Baseline

**Date**: $(date)
**Measurement Type**: Pre-migration baseline

## Current File Sizes

EOF

    # Add file measurements
    if [[ -f "$HOME/.claude/CLAUDE.md" ]]; then
        local lines=$(wc -l < "$HOME/.claude/CLAUDE.md")
        local tokens=$((lines * 15))  # Rough estimate
        echo "- Global CLAUDE.md: $lines lines (~$tokens tokens)" >> "$baseline_file"
    fi

    if [[ -f "./.claude/CLAUDE.md" ]]; then
        local lines=$(wc -l < "./.claude/CLAUDE.md")
        local tokens=$((lines * 15))  # Rough estimate
        echo "- Project CLAUDE.md: $lines lines (~$tokens tokens)" >> "$baseline_file"
    fi

    cat >> "$baseline_file" << EOF

## Estimated Current Usage
- Total tokens per interaction: ~20,000
- Loading pattern: Everything loads globally
- Efficiency: Low (high redundancy)

## Target Metrics
- Total tokens per interaction: ~2,000 (90% reduction)
- Loading pattern: Context-specific lazy loading
- Efficiency: High (bounded contexts)

## Measurement Notes
- Token estimates based on ~15 tokens per line
- Actual usage may vary based on interaction type
- Target measurements to be taken during implementation

EOF

    echo -e "${GREEN}✅ Token baseline created: $baseline_file${NC}"
}

# Main execution
main() {
    echo "Starting CLAUDE.md migration preparation..."

    check_prerequisites
    analyze_current_files
    create_backups
    analyze_token_patterns
    create_token_baseline
    check_implementation_readiness

    echo ""
    echo -e "${GREEN}🎉 Migration preparation complete!${NC}"
    echo ""
    echo "Summary:"
    echo "- Backups created in: $BACKUP_DIR"
    echo "- Analysis complete"
    echo "- Ready for implementation when systems are stable"
    echo ""
    echo "Next steps:"
    echo "1. Wait for task management and memory systems to be locked in"
    echo "2. Review CHECKPOINT/CLAUDE_MD_IMPLEMENTATION_TRACKER.md"
    echo "3. Begin Phase 1 when ready"
    echo ""
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi