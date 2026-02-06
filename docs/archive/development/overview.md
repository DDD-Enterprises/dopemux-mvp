---
id: README
title: Readme
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
author: '@hu3mann'
date: '2026-02-05'
prelude: Readme (explanation) for dopemux documentation and developer workflows.
---
# Development Documentation

This section contains active development documentation, planning, and ongoing work tracking.

## Quick Navigation

- [Active Projects](#active-projects)
- [Planning](#planning)
- [Implementation Plans](#implementation-plans)
- [Research](#research)

---

## Active Projects

**Location:** `active-projects/`

Currently active development initiatives:

### Dashboard Development
- [Dashboard Implementation Tracker](active-projects/DASHBOARD_IMPLEMENTATION_TRACKER.md) - Current progress

### ConPort Development
- [ConPort HTTP Planning](active-projects/CONPORT_HTTP_DEEP_PLANNING.md) - HTTP API development

*Note: Completed projects are moved to `../archive/completed-projects/`*

---

## Planning

**Location:** `planning/`

Active plans and roadmaps:

### Strategic Plans
- [Master Action Plan](planning/ACTION-PLAN-MASTER.md) - Overall project roadmap
- [DDDPG Kickoff](planning/DDDPG_KICKOFF.md) - Development planning

### Design Plans
- [Layout Modular Plan](planning/DOPE_LAYOUT_MODULAR_PLAN.md) - UI/layout planning
- [Neon Layout Zen Plan](planning/NEON_LAYOUT_ZEN_PLAN.md) - UI enhancement planning

---

## Implementation Plans

**Location:** `../implementation-plans/`

Detailed implementation documentation:

### Master Index
- [Implementation Plans Master Index](../implementation-plans/00-MASTER-INDEX.md)

### Recent Implementations
- Component audits and summaries
- Dashboard deep planning
- ConPort event schema design
- Infrastructure consolidation

*Note: This directory maintains its own structure and index*

---

## Research

**Location:** `research/`

Exploratory work and technical investigations:

*To be organized: Research notes, spikes, proof-of-concepts*

---

## Workflow

### Starting New Work

1. **Create a tracking doc** in `active-projects/`
2. **Link from planning** if part of larger initiative
3. **Update regularly** with progress notes
4. **Move to archive** when complete

### Implementation Plans

1. **Major features** get detailed plans in `implementation-plans/`
2. **Follow naming convention:** `NN-FEATURE-NAME.md` or descriptive names
3. **Update master index** when adding new plans
4. **Cross-reference** with ADRs for decisions

### Research Work

1. **Spike/POC work** goes in `research/`
2. **Document findings** even if not implemented
3. **Link to issues/decisions** that result from research
4. **Archive or promote** to implementation when concluded

---

## Relationship to Other Docs

### vs. ADRs (90-adr/)
- **ADRs**: Architectural *decisions* (what was decided and why)
- **Development**: Active *work* (what's being built)

### vs. How-To Guides (02-how-to/)
- **How-To**: User-facing guides (how to use features)
- **Development**: Internal tracking (how features are built)

### vs. Archive (archive/)
- **Archive**: Historical records (what was completed)
- **Development**: Active work (what's in progress)

---

## Status Tracking

Use these status markers in tracking docs:

- 🎯 **Planned** - Defined but not started
- 🚧 **In Progress** - Active development
- ✅ **Complete** - Done (ready to archive)
- ⏸️ **Paused** - On hold
- ❌ **Cancelled** - Not pursuing

---

## Contributing

When working on active development:

1. **Keep tracking docs updated** - Don't let them go stale
2. **Link commits/PRs** in tracking docs
3. **Document blockers** and dependencies
4. **Celebrate milestones** in summaries
5. **Archive when done** - Keep this area clean

---

**Maintained by:** Dopemux Core Team
**Last Updated:** 2025-10-29
