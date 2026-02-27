---
id: CONFLICT_LEDGER
title: Conflict Ledger
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-25'
last_review: '2026-02-25'
next_review: '2026-05-26'
prelude: Conflict Ledger (reference) for dopemux documentation and developer workflows.
---
# Conflict Ledger

## Known Conflicts

| Conflict ID | Claim | Sources | Status | Resolution | Owner | Date |
|-------------|-------|---------|--------|-------------|-------|------|
| CONFLICT-001 | Single verify entrypoint is authoritative | CI workflow, local verify script | UNKNOWN | Pending investigation | N/A | N/A |
| CONFLICT-002 | Timestamp determinism is required | CI workflow, DopeTask Doctor | UNKNOWN | Pending investigation | N/A | N/A |
| CONFLICT-003 | DopeTask pin version is enforced | CI workflow, requirements | UNKNOWN | Pending investigation | N/A | N/A |
| CONFLICT-004 | Documentation vs. Code | Docs, Code | UNKNOWN | Pending investigation | N/A | N/A |
| CONFLICT-005 | CI vs. Local Verification | CI workflow, local verify script | UNKNOWN | Pending investigation | N/A | N/A |
| CONFLICT-006 | Environment Configuration | .env, .env.example | UNKNOWN | Pending investigation | N/A | N/A |

## Resolution Process
1. **Identify**: Document the conflict in the ledger.
2. **Investigate**: Gather evidence and context.
3. **Resolve**: Update the relevant documentation or code.
4. **Close**: Mark the conflict as resolved with a reference to the resolution.

## References
- **Authority Map**: See [AUTHORITY_MAP.md](AUTHORITY_MAP.md) for conflict resolution guidelines.

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
