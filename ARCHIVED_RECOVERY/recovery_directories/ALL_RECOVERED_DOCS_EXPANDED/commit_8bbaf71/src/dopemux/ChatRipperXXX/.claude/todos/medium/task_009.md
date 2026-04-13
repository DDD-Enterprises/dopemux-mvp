## Task: Deterministic embedding cache (disk, async-safe)
- **ID**: 20250906-185622
- **Priority**: Medium
- **Status**: PENDING
- **Context**: taskmaster_migration
- **Dependencies**: [5], [6], [7]

### Description
Implement an on-disk cache to avoid recomputing embeddings, keyed by text+provider+model+params, with TTL/invalidations.

### Implementation Details
Implementation:
- Storage: SQLite via aiosqlite (privacy-first, local); table schema:
  CREATE TABLE IF NOT EXISTS embed_cache (
    key TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    dim INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    vector BLOB NOT NULL
  );
- Key derivation: blake3(hash(text) + provider + model_id + input_type + norm + version)
- Encoding: numpy float32 array -> bytes via .tobytes(); store dim to reconstruct; normalize vectors before caching to ensure retrieval consistency
- API:
class EmbeddingCache:
  async def get(self, key) -> list[float] | None: ...
  async def set(self, key, vec: list[float], dim: int): ...
  async def invalidate_model(self, model_id: str): ...
- Integrate into provider chain wrapper:
async def cached_embed(texts):
  miss_idx, results = [], [None]*len(texts)
  for i,t in enumerate(texts):
    k = make_key(t, provider)
    v = await cache.get(k)
    if v is None: miss_idx.append(i)
    else: results[i]=v
  if miss_idx:
    new_vecs = await provider.embed([texts[i] for i in miss_idx])
    for j, i in enumerate(miss_idx):
      await cache.set(make_key(texts[i], provider), new_vecs[j], provider.dim)
      results[i] = new_vecs[j]
  return results
- Concurrency: use aiosqlite with WAL mode; add asyncio.Lock per key to prevent thundering herd


### Test Strategy
- Unit tests for cache hit/miss, binary roundtrip accuracy (np.allclose)
- Concurrency test: many coroutines request same text; only one provider call occurs
- Invalidate tests by model_id remove rows and cause recomputation
- Performance test on large batch shows reduced provider invocations

### Migration Notes
- Originally Task ID: 9
- Migrated from taskmaster on: 2025-09-06 18:56:22
- Priority mapping: medium
- Status mapping: pending
- Dependencies: [5, 6, 7]

### Related Files
- Original: .taskmaster/tasks/tasks.json
