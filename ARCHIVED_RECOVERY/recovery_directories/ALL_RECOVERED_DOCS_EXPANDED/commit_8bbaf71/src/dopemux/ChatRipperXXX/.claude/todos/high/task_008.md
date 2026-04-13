## Task: Multi-vector schema and retrieval enhancements
- **ID**: 20250906-185622
- **Priority**: High
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [2], [5], [6], [7]

### Description
Extend storage schema to support multiple embeddings (e.g., psychology vs general), add Neo4j vector indexes, and optimize similarity retrieval.

### Implementation Details
Implementation:
- Node properties: embedding_psych (List<Float>), embedding_general (List<Float>), embedding_legacy (optional for backward compatibility)
- Backward compatibility: maintain reading from legacy property/index when new vectors absent
- Create indexes:
  CREATE VECTOR INDEX chunk_psych_idx IF NOT EXISTS FOR (c:Chunk) ON (c.embedding_psych)
  OPTIONS { indexConfig: { 'vector.dimensions': $psych_dim, 'vector.similarity_function': 'cosine' } };
  CREATE VECTOR INDEX chunk_general_idx IF NOT EXISTS FOR (c:Chunk) ON (c.embedding_general)
  OPTIONS { indexConfig: { 'vector.dimensions': $gen_dim, 'vector.similarity_function': 'cosine' } };
- Retrieval API:
async def query_similar(space: str, query_vec: list[float], k: int=20):
  index = 'chunk_psych_idx' if space=='psych' else 'chunk_general_idx'
  cy = "CALL db.index.vector.queryNodes($index, $k, $qv) YIELD node, score RETURN node, score"
  res = await neo4j.run(cy, {"index": index, "k": k, "qv": query_vec})
  return await res.data()
- Normalization: ensure provider returns L2-normalized vectors for cosine similarity
- Add re-ranking option: small MLP/cosine with metadata weights (keep simple: optional BM25/text-overlap rerank)
- Migration script: copy existing embedding -> embedding_legacy; leave legacy retrieval path until deprecation


### Test Strategy
- Integration test creates nodes with both psych and general vectors; queries return expected nearest items
- If new vectors missing, retrieval falls back to legacy index/property without error
- Performance test: ensure latency within target and indexes utilized (PROFILE in Cypher)
- Validate cosine similarity monotonicity after normalization

### Migration Notes
- Originally Task ID: 8
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: high
- Status mapping: pending
- Dependencies: [2, 5, 6, 7]

### Related Files
- Original: .taskmaster/tasks/tasks.json
