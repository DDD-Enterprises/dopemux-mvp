## Task: Migrate Graph Storage to Neo4j AsyncDriver with proper lifecycle
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [1]

### Description
Replace synchronous driver with neo4j AsyncDriver, implement connection lifecycle, pooling, health checks, and vector index utilities.

### Implementation Details
Implementation:
- Use neo4j>=5.23 AsyncGraphDatabase
- Create async connection manager with startup/shutdown hooks and health checks
- Configure pooling & timeouts; implement retry-on-transient failures
- Provide vector index helpers for multi-vector properties
Pseudocode:
from neo4j import AsyncGraphDatabase, AsyncDriver
class Neo4jClient:
  def __init__(self, uri, auth, max_pool=50, fetch_size=1000):
    self._driver: AsyncDriver | None = None
    self._uri, self._auth = uri, auth
    self._max_pool = max_pool
  async def start(self):
    self._driver = AsyncGraphDatabase.driver(
      self._uri, auth=self._auth,
      max_connection_pool_size=self._max_pool,
      connection_timeout=15,
      max_transaction_retry_time=15,
    )
    await self._driver.verify_connectivity()
  async def close(self):
    if self._driver: await self._driver.close()
  async def run(self, cypher, params=None, db=None):
    assert self._driver
    async with self._driver.session(database=db) as session:
      return await session.run(cypher, params or {})
# Vector index creation (Neo4j 5.x vector indexes)
CREATE VECTOR INDEX chunk_psych_idx IF NOT EXISTS FOR (c:Chunk) ON (c.embedding_psych)
OPTIONS { indexConfig: { 'vector.dimensions': $dim, 'vector.similarity_function': 'cosine' } };
- Retrieval example:
CALL db.index.vector.queryNodes($index, $k, $qv) YIELD node, score RETURN node, score;
- Add docker-compose/testcontainers for local Neo4j with APOC if needed
- Ensure graceful shutdown on SIGINT/SIGTERM
- Add backpressure consideration: limit concurrent sessions via semaphore in higher-level service
Security:
- Don’t log credentials; pull from settings


### Test Strategy
- Integration tests with Testcontainers Neo4j 5: start container, apply indexes, run basic create/query, assert async flow
- Simulate transient errors and verify retry behavior
- Verify vector index can be created and queried; assert cosine similarity ordering
- Health check tests using verify_connectivity

### Migration Notes
- Originally Task ID: 2
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [1]

### Related Files
- Original: .taskmaster/tasks/tasks.json
