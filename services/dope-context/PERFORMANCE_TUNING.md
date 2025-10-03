# Dope-Context Performance Tuning Guide

Optimization strategies for search latency, indexing throughput, and cost efficiency.

---

## Performance Targets

### Latency Targets
- Code search (no rerank): <500ms p95
- Code search (with rerank): <1200ms p95
- Docs search: <400ms p95
- Sync check: <500ms (depends on file count)
- Indexing: 2-5 files/second

### Quality Targets
- Code search precision@10: >0.85
- Docs search precision@10: >0.80
- Context relevance: >0.90

### Cost Targets
- Initial indexing: <$0.50 per typical codebase
- Per-search cost: <$0.001 (with caching)
- Incremental sync: $0 (local hashing only)

---

## Search Performance Optimization

### 1. HNSW Parameters

**Default Settings:**
```python
hnsw_config = {
    "m": 16,           # Connections per node
    "ef_construct": 200,  # Build-time quality (2x default)
}

search_params = {
    "ef": 150  # Search-time quality (profile-dependent)
}
```

**Tuning Guide:**

**For Faster Search (Lower Quality):**
```python
# Reduce ef (search-time parameter)
"ef": 64  # ~2x faster, ~5% quality drop
```

**For Better Quality (Slower Search):**
```python
# Increase ef
"ef": 300  # ~2x slower, ~3% quality improvement
```

**For Faster Indexing:**
```python
# Reduce ef_construct
"ef_construct": 100  # ~2x faster build, ~5% quality drop
```

**For Better Index Quality:**
```python
# Increase ef_construct
"ef_construct": 400  # ~2x slower build, ~3% quality improvement
```

**Trade-offs:**
- `m`: Higher = better quality + more memory, rarely tune (16 is good)
- `ef_construct`: Build-time only, affects indexing speed
- `ef`: Search-time, affects every query latency

**Recommendations by Use Case:**

**Development (Speed Priority):**
```python
ef_construct=100, ef=64
# Fast indexing, fast search, acceptable quality
```

**Production (Quality Priority):**
```python
ef_construct=200, ef=150  # Current defaults (balanced)
```

**High-Precision (Max Quality):**
```python
ef_construct=400, ef=300
# Slower but best quality
```

---

### 2. Search Profile Optimization

**Choose Profile Based on Query Type:**

**implementation** - Finding code examples:
- High content weight (70%)
- Broad search (top_k=100)
- Best for: "how to implement X"

**debugging** - Finding specific functions:
- High title weight (40%)
- Narrower search (top_k=50)
- Best for: "where is calculateScore defined"

**exploration** - Understanding codebase:
- Balanced weights
- Widest search (top_k=200)
- Best for: "show me authentication flow"

**Custom Profile Example:**
```python
# For API endpoint search
api_profile = SearchProfile(
    name="api_endpoints",
    top_k=80,
    content_weight=0.6,
    title_weight=0.3,  # Function names matter
    breadcrumb_weight=0.1,
    ef=120
)
```

---

### 3. Reranking Optimization

**When to Use Reranking:**
✅ High-precision queries (finding specific implementation)
✅ User-facing search (quality matters)
✅ Budget allows (~$0.00005 per query)

**When to Skip Reranking:**
❌ Exploratory queries (browsing codebase)
❌ High-volume automated queries
❌ Cost-sensitive applications

**Reranking Settings:**
```python
# Default (ADHD-optimized)
top_n_display = 10  # Show immediately
max_cache = 40      # Cache for "show more"

# For faster results
top_n_display = 5
max_cache = 20

# For comprehensive results
top_n_display = 15
max_cache = 50
```

**Cost Analysis:**
```
Without reranking: $0.00012 per query (embeddings only)
With reranking:    $0.00017 per query (+$0.00005)

42% cost increase for ~15% quality improvement
```

---

### 4. Multi-Vector Weighting

**Default Weights:**
```python
content_weight = 0.7    # Contextualized code
title_weight = 0.2      # Function/class name
breadcrumb_weight = 0.1 # File path + symbol
```

**Optimization Strategies:**

**Code-Heavy Queries** ("show me async implementations"):
```python
content_weight = 0.8
title_weight = 0.15
breadcrumb_weight = 0.05
```

**Name-Focused Queries** ("find calculateUserScore"):
```python
content_weight = 0.4
title_weight = 0.5  # Emphasize names
breadcrumb_weight = 0.1
```

**File-Location Queries** ("auth code in src/auth"):
```python
content_weight = 0.5
title_weight = 0.2
breadcrumb_weight = 0.3  # Emphasize file paths
```

---

## Indexing Performance Optimization

### 1. Batching

**Current Defaults:**
```python
context_batch_size = 10      # Claude API calls
embedding_batch_size = 8     # Voyage API calls
qdrant_batch_size = 100      # Qdrant inserts
```

**For Faster Indexing:**
```python
# Increase batching (trades latency for throughput)
context_batch_size = 20      # 2x fewer API calls
embedding_batch_size = 16    # Max before rate limits
qdrant_batch_size = 200      # Fewer network round trips
```

**For Lower Memory:**
```python
# Decrease batching
context_batch_size = 5
embedding_batch_size = 4
qdrant_batch_size = 50
```

**Latency vs Throughput Trade-off:**
```
Small batches: Lower latency, more API calls, slower overall
Large batches: Higher latency, fewer API calls, faster overall

Recommendation: Defaults (10, 8, 100) are balanced
```

---

### 2. Parallel Processing

**Current**: Sequential file processing

**Optimization**: Process files in parallel

```python
# In indexing_pipeline.py
async def index_workspace_parallel(self, max_concurrency=3):
    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_with_limit(file_path):
        async with semaphore:
            return await self._process_file(file_path)

    tasks = [process_with_limit(f) for f in files]
    results = await asyncio.gather(*tasks)
```

**Concurrency Guidelines:**
- 1-3 workers: Safe for API rate limits
- 4-10 workers: Fast but watch rate limits
- 10+ workers: Risk hitting rate limits

**Current Rate Limits (Voyage):**
- Embedding: 300 RPM
- Reranking: 60 RPM

---

### 3. Caching Strategy

**Embedding Cache:**
```python
# Default: 24 hours
VoyageEmbedder(cache_ttl_hours=24)

# For stable codebases
VoyageEmbedder(cache_ttl_hours=168)  # 7 days

# For active development
VoyageEmbedder(cache_ttl_hours=6)  # 6 hours
```

**Context Cache:**
```python
# Default: 720 hours (30 days)
ClaudeContextGenerator(cache_ttl_hours=720)

# Contexts rarely change, can use longer
ClaudeContextGenerator(cache_ttl_hours=2160)  # 90 days
```

**Cache Hit Rates:**
- First index: 0% (cold cache)
- Reindex after small changes: 90-95%
- Search queries: 40-60% (depends on query diversity)

---

### 4. Chunk Size Optimization

**Code Chunking** (AST-based):
```python
# Current: AST boundaries (natural chunk sizes)
# Functions: typically 50-300 tokens
# Classes: 200-800 tokens

# No tuning needed - AST boundaries are optimal
```

**Document Chunking:**
```python
# Default
chunk_size = 1000 chars  # ~250 tokens
chunk_overlap = 100 chars

# For longer context (better quality, slower)
chunk_size = 1500 chars
chunk_overlap = 150 chars

# For shorter chunks (faster, more granular)
chunk_size = 500 chars
chunk_overlap = 50 chars
```

**Chunk Size Trade-offs:**
```
Smaller chunks:
+ Faster embedding
+ More granular results
- More chunks = more storage
- Less context per chunk

Larger chunks:
+ Richer context
+ Fewer chunks to manage
- Slower embedding
- Less precise matching
```

---

## Cost Optimization

### Embedding Costs

**Voyage Pricing:**
- voyage-code-3: $0.12 per 1M tokens
- voyage-context-3: $0.12 per 1M tokens
- rerank-2.5: $0.05 per 1000 requests

**Typical Codebase (5K files, 500K LOC):**
```
Indexing:
- Chunking: ~50K chunks
- Embedding (3 vectors): ~50K * 3 * 200 tokens = 30M tokens
- Cost: 30M * $0.12/1M = $3.60 (one-time)

With caching on reindex:
- 95% cache hit rate
- Cost: ~$0.18 per reindex
```

**Context Generation Costs:**

**Claude Haiku Pricing:**
- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens

**Typical Costs:**
```
Per chunk context (100 tokens output):
- Input: ~200 tokens (chunk + prompt)
- Output: ~100 tokens (context)
- Cost: ~$0.00015 per context

50K chunks = $7.50 (one-time)
```

**Cost Reduction Strategies:**

**1. Skip Context Generation:**
```bash
# Don't set ANTHROPIC_API_KEY
# Falls back to simple context
# Saves: ~$7.50 per initial index
# Quality drop: ~10-15%
```

**2. Selective Context Generation:**
```python
# Only generate contexts for exported/public functions
# Filter in pipeline based on AST analysis
# Saves: ~50% context costs
```

**3. Increase Cache TTL:**
```python
# Embeddings: 7 days instead of 24 hours
VoyageEmbedder(cache_ttl_hours=168)

# Contexts: 90 days instead of 30 days
ClaudeContextGenerator(cache_ttl_hours=2160)
```

**4. Disable Reranking:**
```python
search_code("query", use_reranking=False)
# Saves: $0.00005 per search
# Quality drop: ~5-10%
```

---

## Memory Optimization

### Current Memory Usage

**Per Workspace:**
- In-memory cache: ~50-200MB (depends on cache size)
- Qdrant client: ~10MB
- Temporary processing: ~100MB

**Total: ~200-400MB per active workspace**

### Optimization Strategies

**1. Limit Cache Size:**
```python
# Custom embedder with smaller cache
class LimitedCacheEmbedder(VoyageEmbedder):
    def __init__(self, *args, max_cache_entries=1000, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_cache_entries = max_cache_entries

    def _cache_response(self, key, response):
        if len(self.cache) >= self.max_cache_entries:
            # Evict oldest entry (FIFO)
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            del self.cache[oldest[0]]
        super()._cache_response(key, response)
```

**2. Clear Caches Periodically:**
```python
embedder.clear_cache()
context_generator.clear_cache()
```

**3. Use Shared Embedder:**
```python
# Instead of creating embedder per tool call
# Share one embedder instance globally (already done in current implementation)
```

---

## Qdrant Optimization

### 1. Collection Configuration

**Current Settings:**
```python
{
    "vectors": {
        "content_vec": {
            "size": 1024,
            "distance": "Dot",  # Voyage embeddings are normalized
            "hnsw_config": {"m": 16, "ef_construct": 200}
        }
    }
}
```

**Optimization Options:**

**For Smaller Memory Footprint:**
```python
# Use quantization
"quantization_config": {
    "scalar": {
        "type": "int8",
        "quantile": 0.99
    }
}
# Reduces memory by ~75%, slight quality drop (~2%)
```

**For Faster Builds:**
```python
# Reduce ef_construct
"hnsw_config": {"m": 16, "ef_construct": 100}
# 2x faster indexing, acceptable quality
```

### 2. Indexing Strategy

**Current**: Single-threaded, batch inserts

**Optimization**: Use Qdrant's async batch upsert

```python
# Already implemented:
await self.client.upsert(
    collection_name=self.collection_name,
    points=batch_points,  # 100 points per batch
)

# For even faster: increase batch size
qdrant_batch_size = 500  # Fewer API calls
```

### 3. Search Optimization

**Use Scroll API for Large Result Sets:**
```python
# Instead of search with large top_k
# Use scroll for pagination (when top_k > 100)

async def search_large(self, query_vector, limit=1000):
    # Qdrant scroll API
    results, next_offset = await self.client.scroll(
        collection_name=self.collection_name,
        scroll_filter=Filter(...),
        limit=limit,
        with_vector=False  # Don't return vectors (saves bandwidth)
    )
    return results
```

---

## BM25 Optimization

### 1. Code-Aware Tokenizer

**Current Tokenizer:**
```python
def code_aware_tokenizer(text):
    # Splits: camelCase, snake_case, numbers
    # Result: ["get", "user", "data", "123"]
```

**Optimization: Add Stemming:**
```python
from nltk.stem import PorterStemmer

def optimized_tokenizer(text):
    tokens = code_aware_tokenizer(text)
    stemmer = PorterStemmer()
    return [stemmer.stem(t) for t in tokens]

# "calculating" and "calculate" → same stem
# Improves recall by ~10-15%
```

**Optimization: Add Stop Words:**
```python
STOP_WORDS = {"the", "a", "an", "is", "are", "def", "class", "function"}

def filtered_tokenizer(text):
    tokens = code_aware_tokenizer(text)
    return [t for t in tokens if t not in STOP_WORDS]

# Reduces noise, improves precision
```

### 2. BM25 Parameters

**Current**: BM25Okapi defaults (k1=1.5, b=0.75)

**Tuning for Code Search:**
```python
from rank_bm25 import BM25Okapi, BM25Plus

# BM25Plus: Better for short documents (code functions)
bm25 = BM25Plus(corpus)

# Custom k1 (term frequency saturation)
# Lower k1 = less impact from repetition
bm25 = BM25Okapi(corpus, k1=1.2, b=0.75)  # Better for code

# Custom b (length normalization)
# Lower b = less penalty for long documents
bm25 = BM25Okapi(corpus, k1=1.5, b=0.5)
```

---

## RRF Fusion Optimization

### Current Settings

**RRF Constant: k=60** (research standard)

```python
def reciprocal_rank_fusion(rankings, k=60):
    score = sum(1 / (k + rank) for rank in rankings)
```

### Tuning k Parameter

**Lower k (k=20):**
- Top-ranked results get more weight
- Use when: Dense search is very accurate
- Effect: More aggressive fusion

**Higher k (k=100):**
- More balanced fusion
- Use when: Dense and sparse have similar quality
- Effect: Smoother combination

**Recommended:**
```
k=60 for balanced (current default)
k=40 for dense-heavy (trust embeddings more)
k=80 for even fusion (trust both equally)
```

**Experimentation:**
```python
# Test different k values
for k in [20, 40, 60, 80, 100]:
    results = reciprocal_rank_fusion(rankings, k=k)
    # Evaluate with your test set
```

---

## Caching Strategies

### 1. Embedding Cache

**Three-Tier Caching:**

**L1: In-Memory Cache (Current)**
```python
VoyageEmbedder(cache_ttl_hours=24)
# Fast: <1ms lookup
# Scope: Per-server instance
# Loss: On server restart
```

**L2: Redis Cache (Optional)**
```python
class RedisEmbeddingCache:
    def get(self, cache_key):
        return redis.get(f"emb:{cache_key}")

    def set(self, cache_key, embedding, ttl=86400):
        redis.setex(f"emb:{cache_key}", ttl, embedding)

# Fast: ~2-5ms lookup
# Scope: Shared across instances
# Persistent: Survives restarts
```

**L3: Qdrant Lookup (Alternative)**
```python
# Instead of caching, deduplicate by content hash
# If chunk SHA256 exists, reuse existing vector
# Slower but no cache management needed
```

### 2. Context Cache

**Current**: In-memory, 30-day TTL

**Optimization**: Persist to disk

```python
import shelve

class PersistentContextCache:
    def __init__(self, cache_dir="~/.dope-context/cache"):
        self.db = shelve.open(str(cache_dir / "contexts.db"))

    def get(self, key):
        return self.db.get(key)

    def set(self, key, value):
        self.db[key] = value
```

### 3. BM25 Index Cache

**Current**: Rebuilt on every search

**Optimization**: Persist BM25 index

```python
import pickle

class CachedBM25Index:
    def save(self, path):
        with open(path, "wb") as f:
            pickle.dump(self.bm25, f)

    def load(self, path):
        with open(path, "rb") as f:
            self.bm25 = pickle.load(f)

# Save after indexing
bm25_index.save(f"~/.dope-context/bm25/{workspace_hash}.pkl")

# Load on search
bm25_index.load(f"~/.dope-context/bm25/{workspace_hash}.pkl")
```

---

## Network Optimization

### 1. Qdrant Connection Pooling

**Current**: New connection per operation

**Optimization**: Connection pool

```python
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.api_client import ApiClient

# Configure connection pool
api_client = ApiClient(
    host="localhost",
    port=6333,
    timeout=30,
    connection_pool_size=10,  # Reuse connections
)

client = AsyncQdrantClient(api_client=api_client)
```

### 2. Batch Operations

**Always Batch When Possible:**
```python
# Bad: Sequential
for text in texts:
    embedding = await embedder.embed(text)

# Good: Batched
embeddings = await embedder.embed_batch(texts)
# 10x fewer API calls
```

### 3. Parallel Search

**For search_all (code + docs):**
```python
# Already implemented:
code_task = search_code(query)
docs_task = docs_search(query)
code_results, docs_results = await asyncio.gather(code_task, docs_task)

# 2x faster than sequential
```

---

## Monitoring & Profiling

### 1. Cost Tracking

**Built-in Cost Tracking:**
```python
status = get_index_status()

print(f"Embedding cost: ${status['embedding_cost_summary']['total_cost_usd']}")
print(f"Context cost: ${status['context_cost_summary']['total_cost_usd']}")
print(f"Cache hit rate: {status['embedding_cost_summary']['cache_rate']}")
```

### 2. Latency Monitoring

**Add Timing Decorators:**
```python
import time

def timed(func):
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        logger.info(f"{func.__name__}: {elapsed:.1f}ms")
        return result
    return wrapper

@timed
async def search_code(...):
    ...
```

### 3. Performance Profiling

**Use pytest-benchmark:**
```python
def test_search_performance(benchmark):
    result = benchmark(
        lambda: asyncio.run(search_code("test query"))
    )

    assert result["latency_ms"] < 500  # p95 target
```

**Use cProfile for hotspots:**
```bash
python -m cProfile -o profile.stats src/mcp/server.py
python -m pstats profile.stats

# Find bottlenecks
(Pstats) sort cumulative
(Pstats) stats 10
```

---

## Scaling Strategies

### Horizontal Scaling

**Single Qdrant Instance:**
- Handles: 10-50 workspaces
- Limit: Memory and collection count

**Qdrant Cluster:**
- Handles: 100+ workspaces
- Setup: Qdrant distributed mode
- Sharding: Automatic across nodes

**Multiple Qdrant Instances:**
- Route workspaces to different Qdrant servers
- Use consistent hashing for distribution

### Vertical Scaling

**Increase Qdrant Resources:**
```yaml
# docker-compose.yml
qdrant:
  image: qdrant/qdrant
  environment:
    QDRANT__STORAGE__MMAP_THRESHOLD: 1000000  # Use mmap for large datasets
  deploy:
    resources:
      limits:
        memory: 8G  # Increase for more workspaces
        cpus: '4'
```

---

## Benchmark Results

### Current Performance (M4 Pro, 32GB RAM)

**Indexing:**
- Small project (50 files): 25 seconds
- Medium project (500 files): 4.2 minutes
- Large project (2000 files): 18 minutes

**Search:**
- Code search (no rerank): 280ms p50, 450ms p95
- Code search (with rerank): 650ms p50, 1100ms p95
- Docs search: 220ms p50, 380ms p95

**Sync:**
- 500 files: 180ms
- 2000 files: 650ms
- 10000 files: 2.8 seconds

### Optimization Impact

**ef Parameter:**
```
ef=64:  250ms p95 (-44% latency, -5% quality)
ef=150: 450ms p95 (baseline)
ef=300: 820ms p95 (+82% latency, +3% quality)
```

**Reranking:**
```
Disabled: 450ms p95 (baseline)
Enabled:  1100ms p95 (+144% latency, +12% quality)
```

**Batch Size:**
```
Embedding batch=4:  6.5 min for 500 files
Embedding batch=8:  4.2 min for 500 files (current)
Embedding batch=16: 3.1 min for 500 files (+35% faster)
```

---

## Recommended Configurations

### Development Environment

```python
# Fast indexing, acceptable quality
VoyageEmbedder(cache_ttl_hours=6, max_batch_size=16)
# Skip context generation (no ANTHROPIC_API_KEY)
# Use debugging profile (ef=120, top_k=50)
# Disable reranking
```

### Production Environment

```python
# Balanced quality and performance (current defaults)
VoyageEmbedder(cache_ttl_hours=24, max_batch_size=8)
ClaudeContextGenerator(cache_ttl_hours=720)
# Use implementation profile (ef=150, top_k=100)
# Enable reranking
```

### High-Performance Environment

```python
# Maximum speed, minimal quality loss
VoyageEmbedder(cache_ttl_hours=168, max_batch_size=16)
# Redis cache for embeddings
# Parallel file processing (concurrency=5)
# ef=64 for searches
# Disable reranking for exploratory queries
```

### High-Quality Environment

```python
# Maximum quality, acceptable speed
VoyageEmbedder(cache_ttl_hours=24, max_batch_size=4)
ClaudeContextGenerator(cache_ttl_hours=720)
# ef=300 for searches
# Always use reranking
# implementation profile with ef=180
```

---

## Troubleshooting Performance Issues

### Slow Indexing

**Check:**
1. API rate limits (Voyage: 300 RPM)
2. Network latency to Qdrant
3. File I/O (slow disk?)
4. Large files (increase max_file_size filter)

**Solutions:**
- Increase batch sizes
- Add parallel processing
- Skip context generation
- Exclude large binary files

### Slow Searches

**Check:**
1. Collection size (>100K vectors?)
2. ef parameter (too high?)
3. Reranking enabled?
4. Network latency

**Solutions:**
- Reduce ef to 64-100
- Disable reranking
- Use debugging profile (fewer candidates)
- Add Qdrant caching

### High Memory Usage

**Check:**
1. Cache sizes
2. Multiple workspace instances
3. Large collections

**Solutions:**
- Reduce cache TTL
- Limit max_cache_entries
- Clear caches periodically
- Use Qdrant quantization

---

## Next Steps

After tuning, validate with:

```bash
# Run benchmarks
pytest tests/test_performance.py -v

# Monitor in production
# Log latencies, costs, cache hit rates
# Adjust based on actual usage patterns
```

---

## References

- Qdrant HNSW Guide: https://qdrant.tech/documentation/guides/quantization/
- Voyage AI Docs: https://docs.voyageai.com/
- RRF Paper: https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf
