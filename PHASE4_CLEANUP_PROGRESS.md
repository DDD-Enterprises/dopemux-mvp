# Documentation Cleanup - Phase 4 Progress Report

**Date**: 2026-02-02  
**Status**: Phase 4 Ready to Execute (Phases 1-3 Complete)  
**Next Session**: Run Phase 4a & 4b scripts, then continue with 4c-4e

---

## ✅ Completed Work (Phases 1-3)

### Phase 1: Initial Consolidation (40 files moved)
- Moved historical completion docs to `archive/implementation-history/`
- Consolidated how-to guides, reference docs, explanation docs
- Extracted features from completion reports before archiving

### Phase 2: Directory Consolidation (9 directories merged)
- Merged architecture/, 94-architecture/, guides/, deployment/
- Merged engineering/, operations/, audit/, systems/
- Archived implementation-plans/ (69 files) and development/ (11 files)

### Phase 3: Deduplication (34 files reduced)
- **3a**: Removed 2 clear duplicates
- **3b**: Archived 14 implementation docs (COMPONENT_*, session summaries)
- **3c**: Consolidated multi-file docs (18 → 4)
  - LEANTIME guides (3 → 1)
  - Claude Code integration (4 → 1)
  - ADHD Engine deep dive (4 parts → 1)
  - Worktree docs (5 → 1)

**Result**: 214 canonical files → 180 canonical files (16% reduction)

---

## 🔍 Phase 4 Audit Findings

### Issue 1: Inconsistent Naming (108 files)
- **50 ALL_CAPS files**: `ADHD_ENGINE.md`, `HAPPY_CODER_*.md`, etc.
- **58 Mixed_Case files**: `START-HERE.md`, `ADR-207-*.md`, etc.
- **Solution**: Convert all to kebab-case

### Issue 2: Misplaced Files (8 files)
**Consolidation reports in docs root** (4 files):
- `CONSOLIDATION_COMPLETION_REPORT.md`
- `CONSOLIDATION_FINAL_REPORT.md`
- `CONSOLIDATION_MIGRATION_MAP.md`
- `PHASE3_DEDUPLICATION_RECOMMENDATIONS.md`
→ Move to `archive/consolidation-reports/`

**Architecture docs outside architecture/** (4 files):
- `03-reference/systems/adhd-intelligence/ADHD_ARCHITECTURE_DIAGRAM.md`
- `04-explanation/design-decisions/UI-DESIGN-RESEARCH-SYNTHESIS.md`
- `05-audit-reports/architecture-audit-2025-10-16.md`
→ Move to `04-explanation/architecture/` or archive

### Issue 3: Duplicate Topics (19 files)
**Happy Coder** (4 files in 04-explanation/):
- `HAPPY_CODER_ENHANCEMENTS.md`
- `HAPPY_CODER_INTEGRATION.md`
- `HAPPY_CODER_USAGE_GUIDE.md`
- `HAPPY_CODER_V2_RESEARCH_VALIDATED.md`
→ Consolidate to single comprehensive guide

**Deployment guides** (7 files with overlap):
- `deployment-checklist.md`
- `deployment-instructions.md`
- `production-deployment-checklist.md`
- `serena-v2-deployment.md`
- `serena-v2-production-deployment.md`
- `F-NEW-7_DEPLOYMENT_GUIDE.md`
- `DEPLOYMENT-READY-SUMMARY.md` (audit report)
→ Consolidate general deployment (3 files) → single guide
→ Review serena-specific (2 files) for duplication
→ Archive audit summary

**ADHD Engine** (5 files - review for overlap):
- `02-how-to/operations/adhd-engine-rollout.md` (keep - operational)
- `03-reference/adhd-engine-api.md` (keep - API reference)
- `03-reference/systems/adhd-intelligence/adhd-engine-deep-dive.md` (keep - comprehensive)
- `04-explanation/ADHD_ENGINE.md` (likely duplicate - review & archive)
- `05-audit-reports/phase3_adhd_engine_feature_analysis.md` (archive)

### Issue 4: Missing READMEs (41 total)
**MCP Servers** (17 missing):
- claude-context, context7, desktop-commander, exa, leantime-bridge
- mcp-server-mas-sequential-thinking, morphllm-fast-apply, pal
- serena, task-master-ai
- (7 more)

**Services** (24 missing):
- adhd-dashboard, adhd-notifier, dopecon-bridge
- monitoring-dashboard, session-intelligence, workspace-watcher
- (18 more)

---

## 📋 Phase 4 Execution Plan

### Phase 4a: Move Consolidation Reports ⏳ READY
**Script**: `~/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/phase4a_execute.sh`

```bash
bash ~/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/phase4a_execute.sh
```

**Actions**:
- Creates `docs/archive/consolidation-reports/`
- Moves 4 consolidation reports from docs root to archive

**Expected output**: "Phase 4a Complete: 4 files moved to archive"

---

### Phase 4b: Kebab-Case Conversion ⏳ READY
**Script**: `~/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/phase4b_kebab_execute.py`

```bash
python3 ~/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/phase4b_kebab_execute.py
```

**Actions**:
- Renames 108 files to kebab-case
- Preserves ADR-XXX- prefix format
- Keeps README.md and INDEX.md as-is

**Expected output**: "PHASE 4b COMPLETE: 108 files renamed"

**Sample conversions**:
- `ADHD_ENGINE.md` → `adhd-engine.md`
- `HAPPY_CODER_INTEGRATION.md` → `happy-coder-integration.md`
- `START-HERE.md` → `start-here.md`
- `ADR-207-LEANTIME-API-RESEARCH.md` → `ADR-207-leantime-api-research.md`

---

### Phase 4c: Consolidate Duplicate Topics 📝 TODO

#### 4c.1: Happy Coder Consolidation
**Create**: `docs/04-explanation/systems/happy-coder-comprehensive-guide.md`

Merge these 4 files:
1. `04-explanation/HAPPY_CODER_ENHANCEMENTS.md`
2. `04-explanation/HAPPY_CODER_INTEGRATION.md`
3. `04-explanation/HAPPY_CODER_USAGE_GUIDE.md`
4. `04-explanation/HAPPY_CODER_V2_RESEARCH_VALIDATED.md`

**Sections**:
- Overview (from INTEGRATION)
- Features & Enhancements (from ENHANCEMENTS)
- Usage Guide (from USAGE_GUIDE)
- Research & Validation (from V2_RESEARCH_VALIDATED)

#### 4c.2: Move Architecture Docs
- `adhd-architecture-diagram.md` → `04-explanation/architecture/`
- `ui-design-research-synthesis.md` → `04-explanation/architecture/`
- `architecture-audit-2025-10-16.md` → `archive/audit-reports/`

#### 4c.3: ADHD Engine Cleanup
- Archive `phase3_adhd_engine_feature_analysis.md` → `archive/audit-reports/`
- Review `04-explanation/ADHD_ENGINE.md` vs. `adhd-engine-deep-dive.md`
  - If duplicate → archive
  - If unique content → keep both or merge

#### 4c.4: Deployment Guide Consolidation
**Create**: `docs/02-how-to/deployment-guide.md`

Merge general deployment guides:
- `deployment-checklist.md`
- `deployment-instructions.md`
- `production-deployment-checklist.md`

**Sections**:
- Development Deployment
- Staging Deployment
- Production Deployment Checklist
- Rollback Procedures

**Keep separate**:
- `serena-v2-deployment.md` (if significantly different)
- Or merge into main guide as "Service-Specific Deployments" section

**Archive**:
- `DEPLOYMENT-READY-SUMMARY.md` → `archive/audit-reports/`

**Review for archival**:
- `F-NEW-7_DEPLOYMENT_GUIDE.md` (feature-specific, may be outdated)

---

### Phase 4d: Create Missing READMEs 📝 TODO

**Standard README Template**:
```markdown
# [Service/MCP Server Name]

**Port**: [port number]  
**Category**: infrastructure|cognitive|coordination|mcp  
**Status**: production|development|experimental  
**Health Check**: `GET /health` or N/A for MCP servers

## Overview
Brief description (2-3 sentences) of what this service/MCP does.

## Quick Start
```bash
# Installation
docker-compose up -d [service-name]

# Configuration
export SERVICE_API_KEY=...
```

## Configuration
Key environment variables:
- `VAR_NAME` - description

## Documentation
See `docs/03-reference/services/[service-name].md` for detailed reference.
See `docs/02-how-to/integrations/[service-name].md` for integration guide.

## Development
```bash
# Run tests
pytest tests/

# Run locally
python main.py
```
```

**Priority MCP Servers** (10 most critical):
1. `docker/mcp-servers/serena/README.md`
2. `docker/mcp-servers/context7/README.md`
3. `docker/mcp-servers/desktop-commander/README.md`
4. `docker/mcp-servers/exa/README.md`
5. `docker/mcp-servers/leantime-bridge/README.md`
6. `docker/mcp-servers/claude-context/README.md`
7. `docker/mcp-servers/task-master-ai/README.md`

**Priority Services** (6 production services):
1. `services/dopecon-bridge/README.md`
2. `services/monitoring-dashboard/README.md`
3. `services/adhd-dashboard/README.md`
4. `services/adhd-notifier/README.md`
5. `services/session-intelligence/README.md`
6. `services/workspace-watcher/README.md`

---

### Phase 4e: Final Validation 📝 TODO

#### Update Indexes
- [ ] Update `docs/00-MASTER-INDEX.md` with new file paths
- [ ] Update `docs/docs_index.yaml` with renamed files
- [ ] Regenerate any auto-generated indexes

#### Verification Checks
- [ ] Run link checker to find broken internal links
- [ ] Verify all architecture docs in `04-explanation/architecture/`
- [ ] Confirm all canonical docs use kebab-case
- [ ] Ensure no files in docs root except:
  - `00-MASTER-INDEX.md`
  - `docs_index.yaml`
  - `INDEX.md`

#### Git Commit
```bash
cd /Users/hue/code/dopemux-mvp

# Review changes
git status
git diff --stat

# Commit Phase 4a & 4b
git add docs/
git commit -m "docs: phase 4a-4b cleanup - archive reports, kebab-case conversion

- Moved 4 consolidation reports to archive/consolidation-reports/
- Converted 108 files to kebab-case naming
- No content changes, only file organization

See docs/archive/consolidation-reports/ for consolidation history"

# Commit Phase 4c (after execution)
git commit -m "docs: phase 4c - consolidate duplicate topics

- Merged 4 Happy Coder docs → comprehensive guide
- Moved architecture docs to proper location
- Consolidated deployment guides (7 → 3 files)
- Archived outdated audit reports"

# Commit Phase 4d (after execution)
git commit -m "docs: phase 4d - create missing service READMEs

- Added READMEs for 10 priority MCP servers
- Added READMEs for 6 production services
- Standardized README format across all services"
```

---

## 📊 Expected Final State

### File Count
| Phase | Canonical Files | Archived Files | Change |
|-------|----------------|----------------|--------|
| Phase 3 End | 180 | 291 | Baseline |
| Phase 4a | 176 | 295 | -4 (moved to archive) |
| Phase 4b | 176 | 295 | 0 (renames only) |
| Phase 4c | ~164 | ~307 | -12 consolidated, +12 archived |
| Phase 4d | ~164 | ~307 | 0 (only creates READMEs) |
| **Final** | **~164** | **~307** | **-16 from Phase 3** |

### Quality Improvements
✅ **100% kebab-case naming** for canonical docs  
✅ **No loose files in docs root**  
✅ **All architecture docs in architecture/**  
✅ **All duplicate topics consolidated**  
✅ **All production services have READMEs**  
✅ **All priority MCP servers have READMEs**

---

## 🚀 Next Session Quick Start

### Step 1: Run Phase 4a & 4b Scripts
```bash
cd /Users/hue/code/dopemux-mvp

# Phase 4a: Move consolidation reports
bash ~/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/phase4a_execute.sh

# Phase 4b: Kebab-case conversion
python3 ~/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/phase4b_kebab_execute.py

# Verify
ls -la docs/archive/consolidation-reports/
git status | head -20
```

### Step 2: Tell Claude to Continue
```
Phase 4a & 4b complete. Continue with Phase 4c (consolidate duplicates).
```

### Step 3: Review & Commit
After each phase, review changes and commit:
```bash
git diff --stat
git add docs/
git commit -m "docs: phase 4[x] - [description]"
```

---

## 📁 Script Locations

All Phase 4 scripts are in session workspace:
```
~/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/

- phase4a_execute.sh              # Move consolidation reports
- phase4b_kebab_execute.py        # Kebab-case conversion
- consolidation_script.py         # Phase 1-2 (already executed)
- phase3_remove_duplicates.py     # Phase 3a (already executed)
- phase3c_consolidate_multifile.py # Phase 3c (already executed)
- extract_features.py             # Feature extraction (already executed)
```

---

## 🔧 Troubleshooting

### If Phase 4a/4b Scripts Fail
The scripts are simple - you can run commands manually:

**Phase 4a Manual**:
```bash
cd /Users/hue/code/dopemux-mvp
mkdir -p docs/archive/consolidation-reports
mv docs/CONSOLIDATION_*.md docs/archive/consolidation-reports/
mv docs/PHASE3_*.md docs/archive/consolidation-reports/
```

**Phase 4b Manual** (use Python script or ask Claude to generate individual mv commands)

### If Files Already Moved
Scripts handle missing files gracefully - they'll report "not found" but continue.

---

## 📖 Reference Documentation

**Completed consolidation reports** (now in archive):
- `docs/archive/consolidation-reports/CONSOLIDATION_FINAL_REPORT.md` - Complete Phase 1-3 summary
- `docs/archive/consolidation-reports/CONSOLIDATION_MIGRATION_MAP.md` - Detailed file migration map
- `docs/archive/consolidation-reports/PHASE3_DEDUPLICATION_RECOMMENDATIONS.md` - Phase 3 analysis

**Original audit** (from this session):
- See terminal output from first audit script run
- 108 files need kebab-case conversion
- 4 Happy Coder files to consolidate
- 17 MCP servers + 24 services missing READMEs

---

**Last Updated**: 2026-02-02 08:30 UTC  
**Session ID**: 2a924450-03f8-44a7-9bdd-7ee125699882  
**Ready to Continue**: Yes - run scripts in Step 1 above
