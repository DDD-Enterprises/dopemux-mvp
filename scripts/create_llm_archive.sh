#!/usr/bin/env bash
set -euo pipefail

#####################################################################
# create_llm_archive.sh
# 
# Creates an LLM-friendly ZIP archive of the dopemux-mvp repository
# for uploading to ChatGPT or other LLM services for code auditing.
#
# Features:
# - Excludes build artifacts, dependencies, and large files
# - Includes source code, docs, and key configuration
# - Generates manifest of included files
# - Reports final archive size
# - Optimized for LLM context windows
#####################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ARCHIVE_NAME="dopemux-mvp-llm-$(date +%Y%m%d-%H%M%S).zip"
MANIFEST_NAME="ARCHIVE_MANIFEST.txt"
TEMP_DIR=$(mktemp -d)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Creating LLM-Friendly Archive of dopemux-mvp          ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Change to repo root
cd "${REPO_ROOT}"

# Create manifest header
cat > "${TEMP_DIR}/${MANIFEST_NAME}" << 'EOF'
╔═══════════════════════════════════════════════════════════════╗
║              DOPEMUX-MVP LLM ARCHIVE MANIFEST                 ║
╚═══════════════════════════════════════════════════════════════╝

This archive contains source code and documentation from the 
dopemux-mvp repository, optimized for LLM code auditing.

## Archive Purpose
- Code review and analysis
- Architecture understanding
- Documentation validation
- Security auditing

## What's Included
- All Python source code (src/, services/)
- All documentation (docs/, *.md)
- Configuration files
- Docker configurations
- Scripts and tooling
- Tests

## What's Excluded
- Build artifacts (.mypy_cache, __pycache__, htmlcov)
- Dependencies (.venv, node_modules)
- Git history (.git)
- Large binaries and logs
- Sensitive data (.env files)
- IDE configurations (.vscode, .idea)

## Repository Structure

EOF

# Add directory tree to manifest
echo "## Directory Tree" >> "${TEMP_DIR}/${MANIFEST_NAME}"
echo '```' >> "${TEMP_DIR}/${MANIFEST_NAME}"
tree -L 2 -I 'node_modules|.venv|__pycache__|.git|.mypy_cache|htmlcov|.pytest_cache|*.pyc' \
  >> "${TEMP_DIR}/${MANIFEST_NAME}" 2>/dev/null || \
  echo "(tree command not available - skipping directory visualization)" >> "${TEMP_DIR}/${MANIFEST_NAME}"
echo '```' >> "${TEMP_DIR}/${MANIFEST_NAME}"
echo "" >> "${TEMP_DIR}/${MANIFEST_NAME}"

# Add file list
echo "## Included Files" >> "${TEMP_DIR}/${MANIFEST_NAME}"
echo "" >> "${TEMP_DIR}/${MANIFEST_NAME}"

echo -e "${YELLOW}📦 Collecting files...${NC}"

# Create temporary file list
FILELIST="${TEMP_DIR}/filelist.txt"

# Include patterns (what to keep)
cat > "${TEMP_DIR}/include_patterns.txt" << 'EOF'
# Documentation
*.md
docs/**
.claude/**/*.md

# Source code
src/**/*.py
services/**/*.py
scripts/**/*.py
scripts/**/*.sh
tests/**/*.py
UPGRADES/**
UPGRADES/**

# Configuration
pyproject.toml
pytest.ini
requirements*.txt
Makefile
*.yaml
*.yml
*.toml
*.json
.gitignore
.dockerignore

# Docker
docker/**
Dockerfile*
docker-compose*.yml

# Shell scripts
*.sh

# Key config directories
config/**
.claude.json.template
mcp-proxy-config*.yaml

# Examples and tools
examples/**
tools/**/*.py
tools/**/*.sh
EOF

# Exclude patterns (what to skip)
cat > "${TEMP_DIR}/exclude_patterns.txt" << 'EOF'
# Build artifacts
**/__pycache__/**
**/*.pyc
**/*.pyo
**/*.pyd
.mypy_cache/**
.pytest_cache/**
htmlcov/**
.coverage
coverage.xml
*.egg-info/**
dist/**
build/**

# Dependencies
.venv/**
venv/**
node_modules/**
.npm/**

# Git
.git/**
.gitmodules
.worktrees/**

# IDE
.vscode/**
.idea/**
*.swp
*.swo
.DS_Store

# Logs and databases
*.log
*.db
*.sqlite
*.sqlite3
logs/**
data/**/*.db
test.db

# Environment and secrets
.env
.env.local
.env.*
!.env.example
!.env.smoke
config/env/cookies.txt

# Large/generated files
wma_build.log
ml_test_output.log
*.pkl
*.pickle
*.h5
*.model

# Temporary
tmp/**
temp/**
*.tmp
.sessions/**

# Archive/backup directories
TRASH/**
SYSTEM_ARCHIVE/**
.backup_location
conport_export/**
test_trash/**

# Reports (keep in docs/archive only)
reports/**/*.html
reports/**/*.json
EOF

# Build find command with excludes
echo -e "${YELLOW}🔍 Scanning repository...${NC}"

# Use git ls-files to get tracked files (more reliable than find)
git ls-files > "${FILELIST}.all"

# Filter based on exclude patterns
python3 << PYTHON_EOF > "${FILELIST}"
import sys
import re
from pathlib import Path

# Read exclude patterns
exclude_patterns = []
with open('${TEMP_DIR}/exclude_patterns.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#'):
            # Convert glob patterns to regex
            pattern = line.replace('**/', '.*/')
            pattern = pattern.replace('**', '.*')
            pattern = pattern.replace('*', '[^/]*')
            pattern = pattern.replace('?', '[^/]')
            pattern = '^' + pattern + '$'
            exclude_patterns.append(re.compile(pattern))

# Read all files
with open('${FILELIST}.all', 'r') as f:
    all_files = [line.strip() for line in f if line.strip()]

# Filter files
included_files = []
for filepath in all_files:
    # Check if file matches any exclude pattern
    excluded = False
    for pattern in exclude_patterns:
        if pattern.match(filepath):
            excluded = True
            break
    
    if not excluded:
        # Additional checks
        path = Path(filepath)
        
        # Skip if in excluded directories
        parts = path.parts
        if any(part in ['.venv', 'node_modules', '__pycache__', '.git', 
                       'TRASH', 'SYSTEM_ARCHIVE', '.mypy_cache', 'htmlcov',
                       '.pytest_cache', 'logs', 'test_trash'] for part in parts):
            continue
            
        # Skip large log files
        if filepath.endswith('.log') and path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb > 1:
                continue
        
        # Skip database files
        if filepath.endswith(('.db', '.sqlite', '.sqlite3')):
            continue
            
        included_files.append(filepath)

# Write included files
for filepath in sorted(included_files):
    print(filepath)

# Stats
print(f"# Total files included: {len(included_files)}", file=sys.stderr)
print(f"# Total files scanned: {len(all_files)}", file=sys.stderr)
PYTHON_EOF

# Get file count
FILE_COUNT=$(wc -l < "${FILELIST}")
echo -e "${GREEN}✓ Found ${FILE_COUNT} files to include${NC}"

# Add file list to manifest
cat "${FILELIST}" >> "${TEMP_DIR}/${MANIFEST_NAME}"
echo "" >> "${TEMP_DIR}/${MANIFEST_NAME}"

# Add size analysis
echo "## Size Analysis" >> "${TEMP_DIR}/${MANIFEST_NAME}"
echo "" >> "${TEMP_DIR}/${MANIFEST_NAME}"

# Calculate sizes
echo -e "${YELLOW}📊 Calculating sizes...${NC}"

python3 << PYTHON_EOF >> "${TEMP_DIR}/${MANIFEST_NAME}"
from pathlib import Path
from collections import defaultdict

sizes = defaultdict(int)
total_size = 0

with open('${FILELIST}', 'r') as f:
    for line in f:
        filepath = line.strip()
        if not filepath or filepath.startswith('#'):
            continue
        
        path = Path(filepath)
        if path.exists():
            size = path.stat().st_size
            total_size += size
            
            # Categorize by directory
            if len(path.parts) > 0:
                category = path.parts[0]
                sizes[category] += size

# Print size breakdown
print("| Category | Size | Files |")
print("|----------|------|-------|")

for category in sorted(sizes.keys()):
    size_mb = sizes[category] / (1024 * 1024)
    print(f"| {category} | {size_mb:.2f} MB | - |")

print(f"| **TOTAL** | **{total_size / (1024 * 1024):.2f} MB** | **${FILE_COUNT}** |")
PYTHON_EOF

echo "" >> "${TEMP_DIR}/${MANIFEST_NAME}"

# Add metadata
cat >> "${TEMP_DIR}/${MANIFEST_NAME}" << EOF

## Archive Metadata

- **Created**: $(date -u +"%Y-%m-%d %H:%M:%S UTC")
- **Repository**: dopemux-mvp
- **Branch**: $(git rev-parse --abbrev-ref HEAD)
- **Commit**: $(git rev-parse --short HEAD)
- **Archive Name**: ${ARCHIVE_NAME}

## Usage Instructions

1. Extract the archive
2. Review ARCHIVE_MANIFEST.txt (this file)
3. Start with README.md for project overview
4. Explore docs/ for documentation
5. Review src/ and services/ for source code
6. Check docker/ for deployment configuration

## Key Entry Points

- README.md - Project overview
- docs/00-MASTER-INDEX.md - Documentation index
- src/dopemux/ - Core library
- services/ - Microservices
- docker/mcp-servers/ - MCP server integrations
- tests/ - Test suites

## LLM Analysis Suggestions

When analyzing this codebase, consider:
- Architecture patterns and design decisions
- ADHD-optimized features and accommodations
- Service integration and communication patterns
- Documentation quality and completeness
- Security practices and potential vulnerabilities
- Code quality and maintainability
- Test coverage and quality

---
Generated by scripts/create_llm_archive.sh
EOF

# Copy manifest to repo root for inclusion
cp "${TEMP_DIR}/${MANIFEST_NAME}" ./

# Create the ZIP archive
echo ""
echo -e "${YELLOW}📦 Creating ZIP archive...${NC}"

# Create zip from file list
zip -q -r "${ARCHIVE_NAME}" -@ < "${FILELIST}"
zip -q -u "${ARCHIVE_NAME}" "${MANIFEST_NAME}"

# Get final size
ARCHIVE_SIZE=$(ls -lh "${ARCHIVE_NAME}" | awk '{print $5}')
ARCHIVE_SIZE_MB=$(du -m "${ARCHIVE_NAME}" | cut -f1)

echo -e "${GREEN}✓ Archive created: ${ARCHIVE_NAME}${NC}"
echo -e "${GREEN}✓ Archive size: ${ARCHIVE_SIZE} (${ARCHIVE_SIZE_MB} MB)${NC}"

# Check if size is reasonable for LLM upload
if [ "${ARCHIVE_SIZE_MB}" -lt 100 ]; then
    echo -e "${GREEN}✓ Size is optimal for LLM upload (< 100 MB)${NC}"
elif [ "${ARCHIVE_SIZE_MB}" -lt 200 ]; then
    echo -e "${YELLOW}⚠ Size is acceptable but large (< 200 MB)${NC}"
else
    echo -e "${RED}⚠ Size may be too large for some LLM services (> 200 MB)${NC}"
    echo -e "${YELLOW}  Consider creating a smaller archive with --minimal flag${NC}"
fi

# Show what's inside
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Archive Contents Summary:${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
unzip -l "${ARCHIVE_NAME}" | head -20
echo "..."
echo ""

# Cleanup
rm -rf "${TEMP_DIR}"
rm -f "${MANIFEST_NAME}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  Archive Created Successfully! ✅           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Archive: ${YELLOW}${ARCHIVE_NAME}${NC}"
echo -e "Size: ${YELLOW}${ARCHIVE_SIZE}${NC}"
echo -e "Files: ${YELLOW}${FILE_COUNT}${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Review the archive content: unzip -l ${ARCHIVE_NAME}"
echo "2. Extract and verify: unzip ${ARCHIVE_NAME} -d /tmp/verify"
echo "3. Upload to ChatGPT or other LLM service"
echo "4. Review ARCHIVE_MANIFEST.txt in the archive for details"
echo ""
