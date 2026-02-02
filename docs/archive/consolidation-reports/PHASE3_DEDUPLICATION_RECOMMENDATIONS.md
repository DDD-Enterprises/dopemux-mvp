---
id: PHASE3_DEDUPLICATION_RECOMMENDATIONS
title: Phase3_Deduplication_Recommendations
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Phase 3 Deduplication - Recommendations

**Date**: 2026-02-02
**Status**: Phase 3 Complete - Further review recommended

---

## Completed Actions

### ✅ Duplicates Removed (2 files)
- `04-explanation/service_env_contract.md` (duplicate - kept in 03-reference/)
- `03-reference/F001-untracked-work-detection.md` (base version - kept ENHANCED)

###  📦 Archived (14 files)
- **11 COMPONENT_* files** → `archive/component-implementations/`
  - These were implementation progress docs, not canonical reference
- **3 session summaries** → `archive/session-notes/`
  - SESSION_SUMMARY_20251024-25.md
  - SESSION_COMPLETE.md
  - SESSION_FINAL_SUMMARY.md

### 🗑️ Empty Directories Removed
- `04-explanation/session-summaries/`
- `04-explanation/reports/`

---

## Remaining Consolidation Opportunities

### 1. LEANTIME Setup Guides (3 files)

**Location**: `02-how-to/integrations/`

Files:
- `LEANTIME_DEPLOYMENT_RECOMMENDATION.md`
- `LEANTIME_API_SETUP_GUIDE.md`
- `LEANTIME_SETUP_INSTRUCTIONS.md`

**Recommendation**: Review content and potentially merge into single `leantime-integration-guide.md`
- Keep if they cover different aspects (deployment vs API vs setup)
- Merge if they're redundant

**Action**: Manual review needed - check for content overlap

### 2. CLAUDE CODE Integration (4 files)

**Location**: `02-how-to/` and `02-how-to/integrations/`

Files:
- `CLAUDE_CODE_CCR_INTEGRATION.md`
- `CLAUDE_CODE_HOOKS_README.md`
- `CLAUDE_CODE_MODEL_DISPLAY.md`
- `integrations/CLAUDE_CODE_INTEGRATION.md`

**Recommendation**: Consolidate into `claude-code-integration-guide.md`
- These likely cover related topics that should be in one guide

**Action**: Review and merge into comprehensive guide

### 3. Deployment Guides (6 files)

**Location**: `02-how-to/`

Files:
- `deployment-instructions.md`
- `deployment-checklist.md`
- `deployment-worktree.md`
- `production-deployment-checklist.md`
- `serena-v2-deployment.md`
- `serena-v2-production-deployment.md`

**Recommendation**: Keep deployment-checklist separate, consolidate instructions:
- **Keep**: `deployment-checklist.md` and `production-deployment-checklist.md` (checklists are useful standalone)
- **Merge**: deployment-instructions + deployment-worktree → `deployment-guide.md`
- **Evaluate**: Are serena-v2 deployment docs still needed or can they merge into main guide?

**Action**: Review serena-v2 deployment docs for consolidation

### 4. ADHD Features Guides (2 files)

**Location**: `02-how-to/`

Files:
- `adhd-features-quick-reference.md`
- `adhd-features-user-guide.md`

**Recommendation**: Likely complementary (quick ref vs detailed guide)
- **Keep both** if quick-reference is truly condensed
- **Merge** if they're redundant

**Action**: Check if quick-reference is actually a subset or separate content

### 5. MetaMCP Guides (3 files)

**Location**: `02-how-to/`

Files:
- `metamcp-setup.md`
- `metamcp-quickstart.md`
- `metamcp-debugging.md`

**Recommendation**: Keep all three - they serve different purposes
- Setup = installation/configuration
- Quickstart = getting started tutorial
- Debugging = troubleshooting guide

**Action**: ✅ No consolidation needed

### 6. Serena v2 Documentation (4 files)

**Locations**: `03-reference/` and `04-explanation/`

Files:
- `03-reference/serena-v2-test-summary.md`
- `03-reference/serena-v2-validation-report.md`
- `03-reference/serena-v2-mcp-tools.md`
- `04-explanation/serena-v2-technical-deep-dive.md`

**Recommendation**: Consolidate test/validation reports
- **Merge**: test-summary + validation-report → `serena-v2-testing.md` (or archive if historical)
- **Keep**: mcp-tools (reference) and technical-deep-dive (explanation)

**Action**: Check if test/validation reports are current or historical

### 7. ADHD Engine Deep Dive (6 files)

**Location**: `03-reference/systems/adhd-intelligence/`

Files:
- `ADHD-ENGINE-DEEP-DIVE-PART1.md`
- `ADHD-ENGINE-DEEP-DIVE-PART2.md`
- `ADHD-ENGINE-DEEP-DIVE-PART3.md`
- `ADHD-ENGINE-DEEP-DIVE-PART4.md`
- `ADHD_COMPLETE_DOCUMENTATION.md`
- `overview.md`

**Recommendation**: Consolidate DEEP-DIVE parts
- **Merge**: PART1-4 → `adhd-engine-deep-dive.md` (single comprehensive doc)
- **Evaluate**: Is ADHD_COMPLETE_DOCUMENTATION redundant with merged deep-dive?
- **Keep**: overview.md (directory index)

**Action**: Merge multi-part deep-dive into single document

### 8. Dashboard Documentation (6 files)

**Location**: `03-reference/systems/dashboard/`

Files:
- `TMUX_METRICS_INVENTORY.md`
- `DASHBOARD_ENHANCEMENTS.md`
- `TMUX_DASHBOARD_DESIGN.md`
- `TMUX_DASHBOARD_README.md`
- `overview.md`
- `DASHBOARD_IMPLEMENTATION_TRACKER.md`

**Recommendation**: Consolidate design/implementation docs
- **Keep**: TMUX_DASHBOARD_README.md (main reference)
- **Keep**: overview.md (directory index)
- **Archive**: IMPLEMENTATION_TRACKER (if historical)
- **Evaluate**: Merge DESIGN + ENHANCEMENTS into README or keep separate?

**Action**: Review for consolidation into comprehensive dashboard guide

### 9. Worktree Documentation (5 files)

**Location**: `04-explanation/concepts/`

Files:
- `WORKTREES_AND_DECISION_GRAPH.md`
- `WORKTREE_USE_CASES.md`
- `WORKTREE_SWITCHING_GUIDE.md`
- `WORKTREE_SYSTEM_V2.md`
- `ADVANCED_WORKTREE_WORKFLOWS.md`

**Recommendation**: Consolidate into comprehensive guide
- **Merge**: All 5 → `worktree-comprehensive-guide.md`
- Or keep 2 docs: `worktree-guide.md` (basics) + `worktree-advanced.md` (advanced workflows)

**Action**: Consolidate worktree documentation

### 10. Architecture Documentation (3 files)

**Location**: `04-explanation/architecture/`

Files:
- `ARCHITECTURE_3.0_IMPLEMENTATION.md`
- `ARCHITECTURE_3.0_COMPLETE.md`
- `ARCHITECTURE-CONSOLIDATION-SYNTHESIS.md`

**Recommendation**: Check if these are historical or current
- If historical: Archive all three
- If current: Keep COMPLETE, archive IMPLEMENTATION

**Action**: Review and potentially archive

---

## Summary Statistics

### Phase 3 Results
- **Duplicates removed**: 2 files
- **Files archived**: 14 files
- **Empty dirs removed**: 2 directories

### Remaining Opportunities
- **High priority** (likely duplicates): LEANTIME (3), Claude Code (4), COMPONENT files
- **Medium priority** (consolidate multi-part): ADHD Deep Dive (4 parts), Worktree (5 files)
- **Low priority** (review for consolidation): Deployment, Dashboard, Serena v2

### Estimated Further Reduction
- Removing/consolidating duplicates: ~20-30 files could be reduced
- Final canonical structure: ~160-180 core docs (down from 214 currently)

---

## Next Steps

1. **User review**: Go through recommendations above
2. **Manual consolidation**: Merge files where appropriate
3. **Final cleanup**: Remove any remaining empty directories
4. **Update indices**: Update 00-MASTER-INDEX.md and docs_index.yaml

---

**Session workspace**: `/Users/hue/.copilot/session-state/2a924450-03f8-44a7-9bdd-7ee125699882/files/`
