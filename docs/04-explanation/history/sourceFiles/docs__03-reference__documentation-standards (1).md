# Documentation Standards: RFC/ADR/arc42 Reference Guide

*Complete guide for writing, reviewing, and maintaining architectural documentation in Dopemux*

## Overview

This reference covers the three core documentation frameworks used in Dopemux:

- **arc42**: Comprehensive system architecture documentation template
- **ADR/MADR**: Individual architectural decision records
- **RFC**: Proposals and exploration documents before decisions

## Part 1: arc42 Architecture Documentation

arc42 is a widely-used, pragmatic template for full-system architecture documentation.

### The 12 Sections of arc42

| Section | Purpose | ADHD-Optimized Tips |
|---------|---------|-------------------|
| **1. Introduction & Goals** | Business/functional goals, quality goals, stakeholders | Keep high-level; limit quality goals to 3-5; make them measurable |
| **2. Constraints** | Technical, regulatory, organizational limitations | Be explicit about what you must NOT do |
| **3. Context & Scope** | System boundaries, external interfaces, environment | Use diagrams for clarity; delimit boundary explicitly |
| **4. Solution Strategy** | Fundamental decisions, patterns, tech choices | Link to ADRs; use summary tables; avoid duplicating details |
| **5. Building Block View** | Structural decomposition, components, responsibilities | Use C4 L1/L2; describe interfaces and responsibilities |
| **6. Runtime View** | Dynamic scenarios, interactions, error cases | Pick representative scenarios; use sequence diagrams |
| **7. Deployment View** | Infrastructure, topology, environments | Document where things run; capture environment configs |
| **8. Cross-cutting Concepts** | Shared patterns: security, logging, naming | Document patterns once to prevent duplication |
| **9. Architectural Decisions** | List of ADRs with status and rationale | Keep minimal; link to ADR files; include status |
| **10. Quality Requirements** | Non-functional requirements and scenarios | Use measurable benchmarks; map to design decisions |
| **11. Risks & Technical Debt** | Known issues, potential problems | Be honest; include mitigations; help future developers |
| **12. Glossary** | Key terms with consistent definitions | Avoid ambiguity; essential for multi-person teams |

### ADHD-Specific arc42 Adaptations

- **Progressive Disclosure**: Start with sections 1-4 for overview, then dive deeper
- **Visual Focus**: Use diagrams extensively in sections 3, 5, 6, 7
- **Context Anchoring**: Always link decisions back to business goals (section 1)
- **Gentle Complexity**: Break complex sections into subsections with clear headers

## Part 2: ADR (Architectural Decision Records)

ADRs capture individual significant decisions using the MADR (Markdown ADR) template.

### MADR Template Structure

```yaml
---
id: adr-XXXX
title: <Title of Decision>
type: adr
status: proposed   # proposed | accepted | rejected | superseded
date: YYYY-MM-DD
author: @<your-handle>
derived_from: rfc-XXXX   # if following an RFC
tags: [tag1, tag2]
feature_id: <dopemux-feature>
---
```

### Required Sections

1. **Context & Problem Statement**
   - What situation requires a decision?
   - What are the constraints and drivers?

2. **Decision Drivers**
   - Requirements that influence the decision
   - Quality goals and constraints
   - Risk factors

3. **Considered Options**
   - List of possible approaches
   - Brief description of each

4. **Decision Outcome**
   - Chosen option with clear justification
   - Why this option over others

5. **Consequences**
   - Positive impacts
   - Negative impacts and trade-offs
   - What must change as a result

6. **Validation** (Optional)
   - How to verify correct implementation
   - Tests, reviews, monitoring approaches

### Writing ADRs Well

1. **One Decision Per ADR**: Keep scope narrow and focused
2. **Ground the Decision**: Use Context and Drivers sections thoroughly
3. **Link Related Artifacts**: Connect to RFCs, diagrams, code, tests
4. **Be Precise**: Clear status, ownership, and timeline
5. **Document Consequences**: Include negatives, not just positives

### ADHD-Friendly ADR Practices

- **Template Consistency**: Always use the same YAML front-matter
- **Clear Progression**: Context → Drivers → Options → Decision → Consequences
- **Visual Aids**: Use tables for option comparison when helpful
- **Bite-sized Decisions**: Break large decisions into multiple focused ADRs

## Part 3: RFC (Request for Comments)

RFCs are proposals written before making decisions, enabling exploration and consensus.

### RFC Template Structure

```yaml
---
id: rfc-XXXX
title: <Title here>
type: rfc
status: draft   # draft | review | accepted | rejected | superseded
author: @<your-handle>
created: YYYY-MM-DD
last_review: YYYY-MM-DD
sunset: YYYY-MM-DD   # optional expiry
feature_id: <feature-id>
tags: [tag1, tag2]
links:
  related_adrs: []
  related_rfc: []
reviewers:
  - @reviewer1
  - @reviewer2
---
```

### Required Sections

1. **Problem**: Core issue you're solving and why it matters
2. **Context**: Background, constraints, dependencies, existing research
3. **Options**: Table comparing approaches with pros/cons
4. **Proposed Direction**: Recommended option with reasoning
5. **Open Questions**: Unresolved issues needing feedback
6. **Risks**: Potential problems, trade-offs, complexity
7. **Timeline/Phases**: Steps from proposal to implementation
8. **Reviewers**: People who need to provide input

### RFC → ADR Workflow

1. **Draft RFC**: Explore problem space and options
2. **Review & Iterate**: Gather feedback, refine proposal
3. **Decision**: Choose option (may happen in RFC or separately)
4. **Create ADR**: Document the final decision
5. **Update arc42**: Reflect decision in relevant sections
6. **Archive RFC**: Mark as accepted/rejected, keep for history

## Part 4: Integration Workflow

### How They Work Together

```
Problem Identified → RFC (Explore) → ADR (Decide) → arc42 (Document) → Implementation
```

1. **RFC Phase**: Explore problem, research options, build consensus
2. **ADR Phase**: Make decision, document rationale and consequences
3. **arc42 Phase**: Update relevant sections to reflect new decisions
4. **Implementation**: Build according to documented decisions

### Quality Checklist

#### When Writing RFC
- [ ] YAML front-matter with all required fields
- [ ] Clear one-sentence problem statement
- [ ] Background/context with links to research
- [ ] At least 2-3 options with pros/cons table
- [ ] Proposed direction clearly stated
- [ ] Open questions identified
- [ ] Risks enumerated
- [ ] Timeline and next steps defined
- [ ] Reviewers assigned

#### When Converting RFC → ADR
- [ ] ADR front-matter includes `derived_from: rfc-XXXX`
- [ ] Decision and consequences clearly documented
- [ ] arc42 sections updated (Solution Strategy, Building Blocks, Decisions)
- [ ] Links added from feature hubs or main docs

#### When Reviewing
- [ ] All required sections present and non-empty
- [ ] Terminology consistent with glossary
- [ ] Feedback from intended reviewers received
- [ ] Risks and dependencies visible
- [ ] Timeline realistic and achievable

#### When Maintaining
- [ ] Stale RFCs reviewed and resolved
- [ ] Metadata completeness verified
- [ ] arc42 alignment with current ADRs
- [ ] Diagrams and documentation updated for architecture changes

## Part 5: Dopemux-Specific Guidelines

### Numbering Schemes

- **ADRs**: Follow existing pattern
  - 001-099: Core architecture
  - 100-199: ADHD optimizations
  - 200-299: Integration decisions
  - 300-399: Development workflow
  - 400-499: User experience
  - 500-599: Data security
  - 600-699: Orchestration & deployment

- **RFCs**: Use year-based numbering
  - Format: `rfc-2025-001-feature-name`

### Required Tags

All documentation must include relevant tags:
- `adhd-accommodation`: ADHD-specific features
- `mcp-integration`: MCP server related
- `memory-architecture`: Memory system changes
- `task-management`: Task decomposition features
- `ui-ux`: User interface decisions
- `security`: Security-related decisions
- `performance`: Performance-related decisions

### ADHD Accommodation Standards

- **Cognitive Load Indicators**: Mark documents as low/medium/high cognitive load
- **Attention State Guidance**: Indicate best attention state for reading
- **Visual Structure**: Use tables, bullet points, and diagrams extensively
- **Progressive Disclosure**: Essential info first, details on request
- **Context Preservation**: Include "where you left off" indicators

### Review Process

1. **Self-Review**: Use automated checklist (see templates)
2. **Peer Review**: At least one technical reviewer
3. **ADHD Review**: Verify accommodation compliance
4. **Documentation Review**: Check integration with existing docs

## Templates and Tools

### Ready-to-Use Templates

- [RFC Template](../templates/rfc-template.md)
- [ADR Template](../templates/adr-template.md)
- [arc42 Section Templates](../templates/arc42/)

### Automation Tools

- Documentation linting with ADHD compliance checking
- Automated cross-reference validation
- Template generation scripts
- Stale document detection

---

*This guide supports the Dopemux commitment to ADHD-accommodating development practices while maintaining rigorous architectural documentation standards.*