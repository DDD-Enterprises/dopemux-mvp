---
id: AUTHORITY_MAP
title: Authority Map
type: reference
owner: '@hu3mann'
last_review: '2026-02-23'
next_review: '2026-05-23'
author: '@hu3mann'
date: '2026-02-23'
prelude: Authority hierarchy and conflict resolution rules for Dopemux MVP.
---

# Dopemux Authority Map

This document defines the hierarchy of authority sources in the Dopemux MVP project and establishes rules for resolving conflicts between different types of documentation and code.

## Authority Hierarchy

### CANON (Highest Authority)

These sources define the definitive behavior of the system:

- **Runtime Behavior**: Repository code and CI workflows
  - Source code in `src/`, `services/`, and `scripts/` directories
  - CI workflows, especially `ci-complete.yml`
  - Docker compose files and service definitions
  - Python package definitions (`pyproject.toml`, `setup.py`)

- **Operational Invariants**: Architecture Decision Records (ADRs)
  - Documents in `docs/90-adr/` directory
  - ADRs freeze design decisions and override other documentation when conflicts arise
  - ADRs may explicitly override code behavior in documented cases

- **Reference Documentation**: Technical specifications describing current behavior
  - Documents in `docs/03-reference/` directory
  - API specifications and service contracts
  - Configuration schemas and validation rules
  - Initially marked as "UNKNOWN until verified" - must be validated against runtime behavior

### SUPPORT (Helpful but Non-Binding)

These sources provide guidance but do not define authoritative behavior:

- **Tutorials and How-To Guides**: Practical usage instructions
  - Documents in `docs/01-tutorials/` and `docs/02-how-to/` directories
  - Getting started guides and workflow examples
  - Best practices and recommended approaches

- **Research Notes**: Investigative findings and analysis
  - Documents in `docs/04-explanation/` directory
  - Technical deep dives and system analysis
  - Research reports and experimental findings

- **Audit Reports**: Historical assessments and evaluations
  - Documents in `reports/` and `docs/archive/` directories
  - Performance audits and system evaluations
  - Historical context and decision rationale

### LEGACY (Non-Authoritative)

These sources provide historical context but should not be relied upon for current behavior:

- **Archived Documentation**: Outdated or superseded materials
  - Documents in `docs/archive/` directory
  - Deprecated features and approaches
  - Historical session notes and completed project documentation

- **Old Plans and Screenshots**: Historical artifacts
  - Old design documents and roadmaps
  - Screenshots and UI mockups from previous versions
  - Aspirational documentation that was never implemented

## Conflict Resolution Rules

### Primary Conflict Rule

**If documentation conflicts with code or CI workflows, the code and CI win unless an ADR explicitly overrides.**

This means:
- Runtime behavior defined by code takes precedence over documentation
- CI workflows define what "verify" means for the project
- Documentation must be updated to match actual behavior, not the other way around
- Exceptions must be documented in ADRs with clear justification

### Secondary Conflict Rules

1. **Between Canon Sources**:
   - ADRs override reference documentation
   - CI workflows override individual service behavior when conflicts arise
   - Code behavior is authoritative for implementation details

2. **Between Support Sources**:
   - More recent documentation takes precedence
   - Tutorials should align with how-to guides
   - Research notes are informative but not binding

3. **Between Legacy Sources**:
   - No precedence - legacy sources are for reference only
   - Should not be used to justify current behavior
   - May be updated or removed without formal deprecation process

## Documentation Lifecycle

### Verification Process

1. **UNKNOWN State**: New reference documentation starts as UNKNOWN
2. **Verification**: Must be validated against runtime behavior
3. **OBSERVED State**: Confirmed to match actual system behavior
4. **INFERRED State**: Plausible but not yet verified
5. **Conflict Resolution**: Discrepancies resolved via ADR process

### Maintenance Responsibilities

- **Code Owners**: Responsible for keeping documentation in sync with code
- **ADR Authors**: Must ensure ADRs accurately reflect design decisions
- **Documentation Owners**: Must validate reference materials against runtime
- **Reviewers**: Should flag documentation-code conflicts during PR review

## Examples

### Example 1: Documentation vs Code Conflict

**Scenario**: `docs/03-reference/services/task-orchestrator.md` describes an endpoint that behaves differently than the actual implementation in `services/task-orchestrator/main.py`.

**Resolution**: The code behavior is authoritative. The documentation must be updated to match the actual implementation.

### Example 2: ADR vs Code Conflict

**Scenario**: `docs/90-adr/ADR-123-service-discovery.md` specifies a discovery protocol that differs from the current implementation.

**Resolution**: The ADR takes precedence. The code should be updated to match the ADR, or the ADR should be amended through the formal ADR process.

### Example 3: CI vs Documentation Conflict

**Scenario**: `ci-complete.yml` defines a verification process that differs from `docs/02-how-to/verification-guide.md`.

**Resolution**: The CI workflow is authoritative. The how-to guide should be updated to reflect the actual CI process.

## Governance Process

### Adding New Authority Sources

1. Propose via ADR process
2. Define verification requirements
3. Establish maintenance ownership
4. Document in this authority map

### Resolving Authority Conflicts

1. Identify conflict via documentation audit or issue report
2. Determine applicable resolution rule
3. Create ADR if exception to primary rule is needed
4. Update documentation to reflect resolution
5. Verify resolution with stakeholders

### Updating This Document

- Changes require PR review and approval
- Significant changes may require ADR
- Keep in sync with actual governance practices
- Review quarterly or when major conflicts arise
