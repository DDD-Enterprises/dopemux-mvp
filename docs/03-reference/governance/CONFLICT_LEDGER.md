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
