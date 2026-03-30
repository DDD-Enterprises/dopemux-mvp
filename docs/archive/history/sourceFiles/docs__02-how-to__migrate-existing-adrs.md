# Migrating Existing ADRs to MADR Format

*Guide for updating existing ADRs to the new MADR template standard*

## Migration Strategy

**Approach**: Incremental migration when ADRs are updated, rather than mass conversion.

**Priority**: Focus on frequently referenced or recently changed ADRs first.

## What Needs to Change

### Add YAML Front-Matter

**Before:**
```markdown
# ADR-001: Hub-and-Spoke Architecture Pattern

**Status**: Accepted
**Date**: 2025-09-20
**Deciders**: @hu3mann, DOPEMUX architecture team
**Tags**: #critical #architecture #core
```

**After:**
```yaml
---
id: adr-001-hub-spoke-architecture
title: Hub-and-Spoke Architecture Pattern
type: adr
status: accepted
date: 2025-09-20
author: @hu3mann
tags:
  - critical
  - architecture
  - core
  - hub-spoke
feature_id: orchestration
adhd_metadata:
  cognitive_load: medium
  attention_state: focused
  implementation_complexity: high
  context_switching_impact: low
---
```

### Restructure Content Sections

**Map existing content to MADR sections:**

| Existing Section | MADR Section | Notes |
|------------------|--------------|-------|
| 🎯 Context | Context & Problem Statement | Keep the context, add problem statement |
| Options Considered | Considered Options | Expand with brief descriptions |
| 🎪 Decision | Decision Outcome | Add justification if missing |
| 🔄 Consequences | Consequences | Restructure as positive/negative/neutral |
| (missing) | Decision Drivers | Add requirements and constraints |
| (missing) | Validation & Confirmation | Add implementation verification |

### Enhance ADHD Accommodations

Add missing ADHD-specific sections:
- ADHD impact analysis in consequences
- Implementation complexity assessment
- Context switching considerations

## Step-by-Step Migration

### 1. Identify ADR for Migration
Prioritize ADRs that are:
- [ ] Recently modified or under discussion
- [ ] Frequently referenced by other documentation
- [ ] Critical to current development work
- [ ] Missing important context or justification

### 2. Backup Original
```bash
cp docs/90-adr/XXX-original.md docs/90-adr/XXX-original.md.backup
```

### 3. Add YAML Front-Matter
- Convert existing metadata to structured YAML
- Add missing fields (feature_id, adhd_metadata)
- Ensure ID follows naming convention

### 4. Restructure Content
- Map existing sections to MADR template
- Add missing sections (especially Decision Drivers)
- Enhance consequences with positive/negative structure
- Add ADHD impact analysis

### 5. Enhance with Missing Information
- Add implementation requirements if missing
- Include validation criteria
- Document any follow-up actions
- Link to related ADRs or documentation

### 6. Review Against Checklist
Use the [documentation review checklist](documentation-review-checklist.md) to ensure quality.

## Quick Conversion Template

For rapid migration of simpler ADRs:

```yaml
---
id: adr-XXX-[existing-title-kebab-case]
title: [Existing Title]
type: adr
status: [convert existing status to lowercase]
date: [existing date]
author: [existing decider/author]
tags:
  - [convert #tags to array]
feature_id: [infer from content]
adhd_metadata:
  cognitive_load: medium  # assess based on complexity
  attention_state: focused  # most ADRs require focus
  implementation_complexity: [low/medium/high]
  context_switching_impact: [low/medium/high]
---

# [Title]

## Context & Problem Statement
[Extract from existing context section + add problem statement]

## Decision Drivers
[Infer from context or add common drivers]:
- [Functional requirement 1]
- [Quality goal 1]
- [Constraint 1]

## Considered Options
[Extract from "Options Considered"]

## Decision Outcome
**Selected: "[Option Name]"**

[Extract justification from decision section]

## Consequences

### Positive Consequences
[Extract positive items from existing consequences]

### Negative Consequences
[Extract negative items or trade-offs]

### ADHD Impact Analysis
- **Cognitive Load:** [assess impact]
- **Context Switching:** [assess impact]
- **Implementation Complexity:** [assess impact]

## Implementation Requirements
[Extract or infer from existing content]

## Validation & Confirmation
[Add if missing - how to verify implementation]
```

## Migration Progress Tracking

### High Priority (Migrate Soon)
- [ ] ADR-001: Hub-and-Spoke Architecture
- [ ] ADR-002: Context7-First Philosophy
- [ ] ADR-003: Multi-Level Memory Architecture

### Medium Priority (Migrate When Updated)
- [ ] ADR-101: ADHD-Centered Design
- [ ] ADR-102: Auto-Save Strategy
- [ ] ADR-103: Attention State Classification

### Low Priority (Migrate If Time Permits)
- [ ] ADR-501: Vector Database (Milvus)
- [ ] ADR-502: Cache Layer (Redis)
- [ ] ADR-503: Relational Storage (PostgreSQL)

## Automated Migration Support

### Potential Script Features
- YAML front-matter generation from existing metadata
- Section mapping and restructuring
- Link validation and updates
- Consistency checking

### Manual Review Required
- ADHD impact assessment
- Implementation complexity evaluation
- Decision drivers inference
- Validation criteria creation

---

*Migrate gradually to maintain quality while adopting new standards*