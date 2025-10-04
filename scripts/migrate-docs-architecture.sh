#!/bin/bash
# Migrate dopemux documentation to new multi-project architecture
# Run from: /Users/hue/code/dopemux-mvp
# Safe: Creates backup, validates before removing

set -e

WORKSPACE="/Users/hue/code/dopemux-mvp"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="$WORKSPACE/claudedocs.backup.$TIMESTAMP"

cd "$WORKSPACE"

echo "=========================================="
echo "Dopemux Documentation Migration v2.0"
echo "Multi-Project Architecture"
echo "=========================================="
echo ""

# Pre-flight check
if [ ! -d ".git" ]; then
    echo "ERROR: Not in a git repository"
    exit 1
fi

# Step 1: Backup (Safety First)
echo "Step 1: Creating safety backup..."
if [ -d "claudedocs" ]; then
    cp -r claudedocs "$BACKUP_DIR"
    echo "  ✓ Backup created: $BACKUP_DIR"
    echo "    (Restore with: mv $BACKUP_DIR claudedocs)"
else
    echo "  • No claudedocs/ to backup"
fi

# Step 2: Create new structure
echo ""
echo "Step 2: Creating new directory structure..."
mkdir -p docs/features
mkdir -p .claude/scratch/{analyses,plans,reports,summaries}
mkdir -p .claude/templates
echo "  ✓ docs/features/ (platform feature specifications)"
echo "  ✓ .claude/scratch/ (conversation artifacts)"
echo "  ✓ .claude/templates/ (external project templates)"

# Step 3: Migrate feature specifications
echo ""
echo "Step 3: Migrating feature specifications to docs/features/..."
migrated_count=0

if [ -f "claudedocs/feature-1-untracked-work-final-spec.md" ]; then
    mv claudedocs/feature-1-untracked-work-final-spec.md \
       docs/features/F001-untracked-work-detection.md
    echo "  ✓ F001-untracked-work-detection.md"
    ((migrated_count++))
fi

if [ -f "claudedocs/feature-2-multi-session-final-spec.md" ]; then
    mv claudedocs/feature-2-multi-session-final-spec.md \
       docs/features/F002-multi-session-support.md
    echo "  ✓ F002-multi-session-support.md"
    ((migrated_count++))
fi

echo "  → Migrated $migrated_count feature specification(s)"

# Step 4: Migrate planning documents
echo ""
echo "Step 4: Migrating planning documents to scratch/plans/..."
plan_count=0

if [ -f "claudedocs/implementation-roadmap-features-1-2.md" ]; then
    mv claudedocs/implementation-roadmap-features-1-2.md \
       .claude/scratch/plans/2025-10-04-features-1-2-roadmap.md
    echo "  ✓ 2025-10-04-features-1-2-roadmap.md"
    ((plan_count++))
fi

echo "  → Migrated $plan_count planning document(s)"

# Step 5: Migrate remaining files
echo ""
echo "Step 5: Migrating remaining files to scratch/analyses/..."
remaining_count=0

if [ -d "claudedocs" ] && [ "$(ls -A claudedocs 2>/dev/null)" ]; then
    shopt -s nullglob  # Handle no matches gracefully
    for file in claudedocs/*.md claudedocs/*.txt; do
        if [ -f "$file" ]; then
            filename=$(basename "$file")
            mv "$file" ".claude/scratch/analyses/2025-10-04-${filename}"
            echo "  → 2025-10-04-${filename}"
            ((remaining_count++))
        fi
    done
    shopt -u nullglob
fi

echo "  → Migrated $remaining_count additional file(s)"

# Step 6: Create documentation
echo ""
echo "Step 6: Creating index and README files..."

# docs/features/_index.md
cat > docs/features/_index.md << 'EOF'
# Dopemux Platform Features

Feature specifications for dopemux platform development.

**Scope:** dopemux platform only (NOT copied to external projects)

## Active Features

| ID | Feature | Status | ADHD-Critical |
|----|---------|--------|---------------|
| F001 | Untracked Work Detection | In Development | Yes |
| F002 | Multi-Session Support | In Development | Yes |

## Naming Convention

- Format: `F###-descriptive-name.md`
- Sequential: F001, F002, F003, ...
- Never reuse numbers

## Frontmatter Template

```yaml
---
feature_id: F###
title: Feature Name
status: in_development | production | deprecated
adhd_critical: true | false
version: 1.0
created: YYYY-MM-DD
owner: name
tags: [tag1, tag2]
---
```

## See Also

- [Architecture Decisions](../90-adr/) - Major architectural choices
- [RFCs](../91-rfc/) - Proposals under discussion
EOF
echo "  ✓ docs/features/_index.md"

# .claude/scratch/README.md
cat > .claude/scratch/README.md << 'EOF'
# Claude Scratch Directory

**Purpose:** Temporary conversation artifacts from Claude Code sessions

**Scope:** ALL dopemux projects (dopemux-mvp AND external projects)

**Retention:** 30 days recommended

## Subdirectories

- `analyses/` - Deep analysis reports (thinkdeep, debug, consensus outputs)
- `plans/` - Implementation roadmaps, planning documents
- `reports/` - Session summaries, status reports
- `summaries/` - Quick notes, meeting summaries

## Naming Convention

Date-based: `YYYY-MM-DD-descriptive-name.md`

**Examples:**
- `2025-10-04-features-analysis.md` (analyses/)
- `2025-10-04-serena-roadmap.md` (plans/)
- `2025-10-04-session-summary.md` (reports/)

## Git Ignore

This directory is gitignored - conversation artifacts are local, not committed.

## Cleanup

Remove files older than 30 days:
```bash
find .claude/scratch -name "*.md" -mtime +30 -delete
```
EOF
echo "  ✓ .claude/scratch/README.md"

# Step 7: Remove claudedocs
echo ""
echo "Step 7: Removing claudedocs directory..."
if [ -d "claudedocs" ]; then
    remaining=$(ls -A claudedocs 2>/dev/null | wc -l | tr -d ' ')
    if [ "$remaining" = "0" ]; then
        rmdir claudedocs
        echo "  ✓ claudedocs/ removed (empty)"
    else
        echo "  ⚠ WARNING: claudedocs/ has $remaining file(s)"
        echo "    Review: ls -la claudedocs/"
        echo "    Remove manually: rm -rf claudedocs/"
    fi
else
    echo "  • claudedocs/ already removed"
fi

# Step 8: Update .gitignore
echo ""
echo "Step 8: Updating .gitignore..."
if ! grep -q "^\.claude/scratch/$" .gitignore 2>/dev/null; then
    cat >> .gitignore << 'EOF'

# ===================================================================
# Dopemux: Multi-Project Documentation Architecture
# ===================================================================

# Claude conversation artifacts (temporary, per-session)
.claude/scratch/

# ConPort local state (per-developer, not committed)
context_portal/*.db
context_portal/*.db-*
context_portal/*.db-shm
context_portal/*.db-wal

# Keep committed structure
!context_portal/.gitkeep
!context_portal/migrations/

# Keep committed .claude config
!.claude/CLAUDE.md
!.claude/statusline.sh
!.claude/modules/
!.claude/templates/
EOF
    echo "  ✓ .gitignore updated with dopemux patterns"
else
    echo "  • .gitignore already has dopemux patterns"
fi

# Step 9: Validation
echo ""
echo "Step 9: Validating migration..."
echo ""

# Check features
feature_count=$(ls docs/features/*.md 2>/dev/null | grep -v "_index" | wc -l | tr -d ' ')
echo "  ✓ docs/features/ has $feature_count specification(s)"

# Check scratch
scratch_count=$(find .claude/scratch -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
echo "  ✓ .claude/scratch/ has $scratch_count file(s)"

# Check claudedocs
if [ ! -d "claudedocs" ]; then
    echo "  ✓ claudedocs/ removed"
else
    echo "  ⚠ claudedocs/ still exists"
fi

# Check .gitignore
if git check-ignore .claude/scratch/test.md >/dev/null 2>&1; then
    echo "  ✓ .gitignore works (scratch/ is ignored)"
else
    echo "  ⚠ .gitignore may need manual check"
fi

echo ""
echo "=========================================="
echo "Migration Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  • Feature specs: $migrated_count → docs/features/"
echo "  • Planning docs: $plan_count → .claude/scratch/plans/"
echo "  • Other files: $remaining_count → .claude/scratch/analyses/"
echo "  • Backup: $BACKUP_DIR"
echo ""
echo "Next steps:"
echo "  1. Review migrated files: ls -la docs/features/"
echo "  2. Check .gitignore: git status"
echo "  3. Commit: git add -A && git commit -m 'feat: Multi-project docs architecture'"
echo "  4. Clean backup: rm -rf $BACKUP_DIR (after verification)"
echo ""
