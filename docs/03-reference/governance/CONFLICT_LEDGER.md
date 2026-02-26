---
id: CONFLICT_LEDGER
title: Conflict Ledger
type: reference
owner: '@hu3mann'
last_review: '2026-02-23'
next_review: '2026-05-23'
author: '@hu3mann'
date: '2026-02-23'
prelude: Tracking ledger for authority conflicts and their resolution status.
---

# Dopemux Conflict Ledger

This document tracks known or potential conflicts between authority sources in the Dopemux MVP project. Each entry documents the nature of the conflict, its current status, and resolution path.

## Ledger Format

| ID | Claim | Sources | Status | Resolution | Owner | Date |
|----|-------|---------|--------|------------|-------|------|

**Status Values:**
- `OBSERVED`: Conflict confirmed to exist
- `INFERRED`: Plausible conflict needing verification
- `UNKNOWN`: Potential conflict identified but not investigated
- `RESOLVED`: Conflict addressed with resolution implemented
- `DEFERRED`: Conflict acknowledged but resolution postponed

## Active Conflicts

| ID | Claim | Sources | Status | Resolution | Owner | Date |
|----|-------|---------|--------|------------|-------|------|
| CL-001 | "Single verify entrypoint is authoritative" | `ci-complete.yml`, various how-to guides | UNKNOWN | Verify if single entrypoint exists and is consistently used | @hu3mann | 2026-02-23 |
| CL-002 | "Timestamp determinism is required" | Code comments, CI workflows, some service implementations | UNKNOWN | Audit services for consistent timestamp handling | @hu3mann | 2026-02-23 |
| CL-003 | "dopetask pin version is enforced" | `pyproject.toml`, CI workflows, installation scripts | UNKNOWN | Verify dopetask version pinning consistency | @hu3mann | 2026-02-23 |
| CL-004 | "Service health checks follow consistent pattern" | Various service READMEs, monitoring documentation | INFERRED | Standardize health check endpoints and responses | @hu3mann | 2026-02-23 |
| CL-005 | "Documentation frontmatter schema is enforced" | Docs validator scripts, existing documentation | UNKNOWN | Verify frontmatter validation consistency | @hu3mann | 2026-02-23 |
| CL-006 | "MCP server configurations are canonical" | `.claude/claude_config.json`, service configurations | INFERRED | Audit MCP configurations for consistency | @hu3mann | 2026-02-23 |

## Resolution Process

### Investigation Workflow

1. **Identify**: Document potential conflict in ledger with `UNKNOWN` status
2. **Gather Evidence**: Collect references to conflicting sources
3. **Verify**: Determine if actual conflict exists (`OBSERVED` or `INFERRED`)
4. **Analyze**: Determine applicable authority resolution rule
5. **Resolve**: Implement fix according to authority hierarchy
6. **Update**: Change status to `RESOLVED` with resolution details

### Resolution Patterns

1. **Code Wins**: Update documentation to match implementation
2. **ADR Override**: Create ADR to document intentional divergence
3. **Standardization**: Align multiple implementations to common pattern
4. **Deprecation**: Mark legacy approaches as deprecated
5. **Clarification**: Improve documentation to eliminate ambiguity

## Conflict Resolution Examples

### Example: Service Health Check Standardization (CL-004)

**Investigation:**
- Some services use `/health`, others use `/status`
- Response formats vary between services
- Monitoring documentation assumes consistent pattern

**Resolution Approach:**
1. Audit all services for current health check implementations
2. Create ADR defining standard health check contract
3. Update services to conform to standard
4. Update monitoring documentation
5. Add health check validation to CI

**Expected Outcome:**
- Consistent `/health` endpoint across all services
- Standardized JSON response format
- Automated health check validation
- Updated documentation reflecting actual behavior

## Maintenance

### Adding New Entries

1. Assign unique ID (CL-XXX format)
2. Provide clear, concise claim description
3. List specific sources involved
4. Set initial status (`UNKNOWN` or `INFERRED`)
5. Assign owner for investigation
6. Add current date

### Updating Entries

1. Update status as investigation progresses
2. Add resolution details when addressed
3. Include references to ADRs, PRs, or commits that resolve conflict
4. Mark as `RESOLVED` when complete
5. Keep historical entries for audit trail

### Review Cycle

- Review ledger monthly during governance meetings
- Prioritize `OBSERVED` conflicts for resolution
- Investigate `INFERRED` conflicts to confirm/deny
- Audit `UNKNOWN` entries for continued relevance
- Archive resolved conflicts after 6 months

## Governance Integration

This ledger integrates with the broader governance system:

- **Authority Map**: Defines resolution rules applied to conflicts
- **ADR Process**: Formal mechanism for resolving complex conflicts
- **CI Workflows**: Enforcement mechanism for resolved conflicts
- **Documentation Standards**: Prevention mechanism for future conflicts

## Historical Context

The conflict ledger was introduced as part of the governance documentation initiative to:
- Make authority conflicts visible and trackable
- Provide systematic resolution process
- Prevent recurring conflicts through documentation
- Improve overall system consistency

As the project matures, the ledger will evolve to reflect:
- Fewer `UNKNOWN` entries as documentation is verified
- More `RESOLVED` entries as conflicts are addressed
- Clearer authority boundaries through documented resolutions
