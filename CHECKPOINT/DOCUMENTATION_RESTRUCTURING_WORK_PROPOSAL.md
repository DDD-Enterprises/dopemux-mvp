---
id: docs-restructuring-proposal-2025-09-26
title: Documentation Restructuring - Component+Runbook Architecture
type: work_proposal
status: ready_for_execution
date: 2025-09-26
author: @hue
feature_id: adhd-documentation-system
priority: high
estimated_effort: 3-5 sessions (15-25 hours)
tags: [documentation, adhd-optimization, knowledge-graph, component-architecture]
graph_metadata:
  node_type: Pattern
  relates_to: [docs/, .claude/CLAUDE.md, config/docs/enforcement.yaml]
  impact: high
prelude: "Strategic documentation restructuring from ADR-based to component+runbook architecture for ADHD-optimized developer experience. Requires systematic migration of 485 files while preserving knowledge graph benefits."
---

# 📋 Documentation Restructuring - Strategic Work Proposal

**Project**: dopemux-mvp Documentation Architecture Transformation
**Status**: 🟡 Critical Transition State - Phase 3 Active
**Priority**: High (impacts all future development)
**ADHD Optimization**: Core objective

## 🎯 Executive Summary

Transform dopemux documentation from abstract ADR-based system to **concrete component+runbook architecture** optimized for ADHD developers. This strategic restructuring moves from "decision archaeology" to "implementation cartography" - dramatically improving cognitive accessibility.

**Current State**: Successfully deleted all ADRs, building new structure with 5 component hubs and 13 runbooks. **485 markdown files** remain to be systematically migrated.

## 📊 Strategic Context

### Problem Analysis
- **ADR Cognitive Overhead**: Abstract decisions require mental effort to extract actionable guidance
- **Context Switching Pain**: ADHD developers struggle with historical decision archaeology
- **Navigation Complexity**: Scattered information across chronological ADR structure

### Solution Architecture
- **Component Hubs**: Concrete system parts (metamcp, memory, leantime, security, taskmaster)
- **Operational Runbooks**: Step-by-step implementation guidance (13 created)
- **ADHD Accommodations**: Progressive disclosure, visual hierarchy, actionable steps

### Strategic Benefits
✅ **Reduced Cognitive Load**: Direct component access vs decision digging
✅ **Concrete Navigation**: System parts vs abstract concepts
✅ **Immediate Value**: Runbooks provide operational guidance
✅ **Context Preservation**: Knowledge graph benefits maintained

## 🏗️ Current Architecture State

### ✅ **Completed Structure**
```
docs/03-reference/components/
├── metamcp/           # MCP orchestration hub
├── memory/            # Memory system architecture
├── leantime/          # Project management integration
├── security/          # Security component hub
├── taskmaster/        # Task management system
└── readme.md          # Component navigation

docs/92-runbooks/
├── 13 operational guides (150KB total)
├── Implementation procedures
├── Troubleshooting guides
└── Deployment runbooks
```

### ⚠️ **In-Progress Migration**
- **485 markdown files** need systematic processing
- **ADR context preservation** required (decision rationale, trade-offs)
- **Cross-cutting concerns** need architectural placement
- **Knowledge graph metadata** must be preserved

## 📋 Implementation Plan

### **Phase 1: Content Audit & Mapping** ⏱️ 1 Session (3-5 hours)

**Objective**: Systematic analysis of 485 remaining files

**Tasks**:
1. **File Categorization**
   - Component-specific content → components/
   - Cross-cutting decisions → docs/architecture/
   - Operational procedures → runbooks/
   - Historical content → archive/

2. **ADR Context Extraction**
   - Identify valuable decision rationale
   - Map to component or architectural categories
   - Preserve trade-off analysis and alternatives

3. **Priority Assessment**
   - Critical content (security, core architecture)
   - Operational content (deployment, configuration)
   - Historical content (archival candidates)

**Deliverables**:
- `migration_map.json` - File categorization mapping
- `adr_context_analysis.md` - Decision rationale preservation plan
- `priority_matrix.md` - Processing order recommendations

### **Phase 2: Systematic Migration** ⏱️ 2-3 Sessions (8-15 hours)

**Objective**: Execute distill-and-embed content migration

**Sub-Phase 2A: Component Migration**
- Process component-specific files by hub
- Embed ADR context in component READMEs
- Maintain graph metadata compliance
- Update cross-references

**Sub-Phase 2B: Architectural Consolidation**
- Create `docs/architecture/` for cross-cutting concerns
- Consolidate system-wide decisions (observability, security strategy)
- Preserve decision rationale and alternatives
- Link to affected components

**Sub-Phase 2C: Runbook Enhancement**
- Migrate operational content to runbooks/
- Standardize procedure formats
- Add troubleshooting guidance
- Create navigation indexes

**Success Criteria**:
- All 485 files processed or archived
- Zero content loss (valuable context preserved)
- New structure fully navigable
- Knowledge graph compliance maintained

### **Phase 3: System Integration** ⏱️ 1 Session (2-4 hours)

**Objective**: Update enforcement and guidance systems

**Tasks**:
1. **Enforcement System Updates**
   - Modify `.claude/CLAUDE.md` documentation rules
   - Update `config/docs/enforcement.yaml`
   - Adapt pre-commit hooks for new structure

2. **Documentation Guidelines**
   - Create component documentation standards
   - Establish runbook creation procedures
   - Define cross-cutting concern handling

3. **Navigation & Discovery**
   - Update main README.md with new structure
   - Create component index pages
   - Establish search and discovery patterns

**Deliverables**:
- Updated enforcement configuration
- Formal documentation guidelines
- Navigation and discovery systems

## ⚠️ Risk Management

### **Critical Risks**

**1. Information Loss** 🚨
- **Risk**: Valuable ADR context deleted without preservation
- **Mitigation**: Systematic distill-and-embed approach before deletion
- **Rollback**: Archive preservation enables full restoration

**2. Cross-Cutting Confusion** ⚡
- **Risk**: System-wide decisions lack clear placement
- **Mitigation**: Create `docs/architecture/` for architectural concerns
- **Example**: observability, security strategy, deployment patterns

**3. Knowledge Graph Breakage** 🔗
- **Risk**: New structure breaks semantic search capabilities
- **Mitigation**: Preserve graph metadata, update enforcement system
- **Validation**: Test search and discovery after migration

**4. Migration Incompleteness** 📊
- **Risk**: Partial migration leaves system fragmented
- **Mitigation**: Systematic tracking with completion checklists
- **Monitoring**: Progress dashboards and completion metrics

### **Contingency Plans**

**If Overwhelmed**:
- Break into smaller component-focused sessions
- Process highest-priority components first (security, metamcp)
- Use visual progress tracking for motivation

**If Context Lost**:
- Comprehensive session checkpoints every 2 hours
- Decision logging in ConPort system
- Archive preservation enables rollback

## 📈 Success Metrics

### **Quantitative Targets**
- ✅ **485 files processed** (100% completion)
- ✅ **Zero content loss** (valuable context preserved)
- ✅ **5 component hubs** fully documented
- ✅ **13+ runbooks** operational
- ✅ **<3 clicks** to find any information

### **Qualitative Outcomes**
- 🧠 **Cognitive Accessibility**: ADHD developers find info quickly
- 🎯 **Implementation Focus**: Concrete guidance over abstract decisions
- 🔄 **Maintenance Ease**: Clear creation and update procedures
- 🔍 **Discovery**: Intuitive navigation and search

## 🛠️ Resource Requirements

### **Tools & Systems**
- ✅ Documentation validator (`scripts/docs_validator.py`)
- ✅ Pre-commit hooks for validation
- ✅ Knowledge graph enforcement system
- ⏳ Migration tracking scripts (to be created)

### **Dependencies**
- Archive system preservation (rollback capability)
- ConPort integration for session management
- Git workflow for incremental commits
- ADHD accommodation patterns maintained

## 🚀 Getting Started

### **Immediate Next Steps** (Resume Here)
1. **File Audit**: `find docs/ -name "*.md" | sort > remaining_files.txt`
2. **Categorization**: Use migration mapping script
3. **Priority Processing**: Start with security component
4. **Progress Tracking**: Update todo list and ConPort

### **Session Restoration Commands**
```bash
# Check current state
find docs/ -name "*.md" | wc -l
ls -la docs/03-reference/components/
ls -la docs/92-runbooks/

# Begin migration
python scripts/create_migration_map.py
```

## 📚 Related Documentation

### **Previous Work**
- `.claude/SESSION_STATE_DOC_ENFORCEMENT.md` - Enforcement system creation
- `DOCUMENTATION_CLEANUP_SUMMARY_2025-09-25.md` - Phase 1 & 2 completion
- `archive/2025-09-25-cleanup/` - Preserved content for reference

### **Templates & Standards**
- `docs/templates/` - RFC, ADR, Caveat templates
- `config/docs/enforcement.yaml` - Validation configuration
- `.pre-commit-config.yaml` - Automated validation hooks

---

## 💾 Project Handoff Summary

**What's Been Done**: Strategic restructuring from ADRs to component+runbook architecture. Enforcement system created, major cleanup completed, new structure scaffolded.

**What's Next**: Systematic migration of 485 remaining files using distill-and-embed approach while preserving valuable context.

**Why This Matters**: Transforms documentation from cognitive burden to implementation asset. Perfect for ADHD developers who need concrete, actionable guidance over abstract decision archaeology.

**Ready to Execute**: All tools, templates, and frameworks in place. Clear phases with defined success criteria. Can be resumed immediately or delegated with full context.

---
*Work proposal created: 2025-09-26*
*Session checkpoint: CHECKPOINT/DOCUMENTATION_RESTRUCTURING_SESSION_CHECKPOINT.md*