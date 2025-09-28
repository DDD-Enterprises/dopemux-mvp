## Task: Optimize Graph Update Operations with MERGE-based Upserts
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [13], [14]

### Description
Replace inefficient DETACH DELETE/CREATE patterns with MERGE-based upsert operations for graph updates.

### Implementation Details
Refactor Cypher queries in src/chatx/storage/graph.py (lines 54-55, 425-429) to use MERGE for upserts. Example:

```cypher
MERGE (n:Label {id: $id})
ON CREATE SET n.prop = $value
ON MATCH SET n.prop = $value
```
Ensure all graph update operations avoid unnecessary deletes and re-creations. Validate that MERGE logic preserves data integrity and avoids race conditions in async contexts.

### Test Strategy
Write unit tests for all upsert operations. Use integration tests to verify data consistency and idempotency. Benchmark update throughput before and after refactor.

### Migration Notes
- Originally Task ID: 15
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [13, 14]

### Related Files
- Original: .taskmaster/tasks/tasks.json
