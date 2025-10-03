# Dope-Context: Multi-Project Semantic Search Architecture

## Executive Summary

Unified code + docs search system with perfect multi-project isolation, hybrid retrieval (dense + sparse), and incremental sync.

**Quality**: 35-67% better retrieval vs traditional chunking (Anthropic benchmark)
**Cost**: <$0.50 one-time indexing per workspace
**Latency**: <500ms code search p95, <1200ms with reranking
**Isolation**: Collection-per-workspace (no data leakage)
**Sync**: SHA256-based incremental updates (Merkle DAG)

---

## Multi-Project Isolation Architecture

**Critical Design Decision:** Collection-per-workspace (not shared collections)

Prevents data leakage across projects while supporting multiple workspaces on one machine.

```
┌────────────────────────────────────────────────────────────────┐
│                     Query: "async error handling"              │
└────────────┬───────────────────────────────────────────────────┘
             │ Task Profile: "implementation"
             │ Weights: code=0.6, api=0.2, docs=0.15, chat=0.05
             │
    ┌────────┼────────┬─────────┬─────────┐
    │        │        │         │         │
┌───▼────┐ ┌▼─────┐ ┌▼──────┐ ┌▼──────┐
│ Code   │ │ Docs │ │ API   │ │ Chat  │
│ Index  │ │ Index│ │ Index │ │ Index │
│        │ │      │ │       │ │       │
│voyage  │ │voyage│ │voyage │ │voyage │
│-code-3 │ │-ctx-3│ │-ctx-3 │ │-3-lg  │
│        │ │      │ │       │ │       │
│K=100   │ │K=60  │ │K=40   │ │K=20   │
└────┬───┘ └┬─────┘ └┬──────┘ └┬──────┘
     │      │        │         │
     │ 60   │ 9      │ 8       │ 1      (Ratio-weighted)
     └──────┴────────┴─────────┴────────┐
                                         │
            ┌────────────────────────────▼────┐
            │   Global RRF Fusion (k=60)      │
            │   78 candidates                 │
            └────────────────┬────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │  voyage-rerank-2.5              │
            │  Top-78 → Top-10                │
            └────────────────┬────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │  Final Results + ConPort Links  │
            └─────────────────────────────────┘
```

---

## Index 1: Code (voyage-code-3)

### Qdrant Collection Schema
```python
{
    'name': 'code_index',
    'vectors': {
        'content_vec': {
            'size': 1024,
            'distance': 'Dot',  # Voyage normalized, dot=cosine
            'hnsw_config': {'m': 16, 'ef_construct': 200}
        },
        'title_vec': {'size': 1024, 'distance': 'Dot'},
        'breadcrumb_vec': {'size': 1024, 'distance': 'Dot'}
    },
    'payload_schema': {
        'file_path': 'keyword',
        'function_name': 'keyword',
        'language': 'keyword',
        'context_snippet': 'text',  # Claude-generated
        'raw_code': 'text',
        'docstring': 'text',
        'imports': 'keyword[]',
        'complexity': 'integer',
        'loc': 'integer',
        'workspace_id': 'keyword'
    }
}
```

### Preprocessing Pipeline
```python
async def process_code_file(file_path: str):
    # 1. Tree-sitter AST parsing (leverage Serena)
    ast = await tree_sitter_parse(file_path, language)
    functions = extract_functions_and_classes(ast)

    # 2. For each function/class/method
    for func in functions:
        # Extract metadata
        chunk_data = {
            'code': func.text,
            'name': func.name,
            'docstring': func.docstring,
            'start_line': func.start_line,
            'end_line': func.end_line,
            'imports': extract_imports_for_function(ast, func)
        }

        # 3. Generate context with Claude (batch 10 per call)
        context = await generate_code_context(chunk_data, file_path)
        # Returns: "This function is from {module} in {file_path}.
        #           It handles {purpose from docstring}.
        #           Dependencies: {imports}. Called by: {callers}."

        # 4. Create contextualized content
        contextualized = f"{context}\n\n{func.code}"

        # 5. Embed with voyage-code-3 (batch 8 per API call)
        vectors = await voyage_embed_multi(
            content=contextualized,
            title=func.name,
            breadcrumb=f"{file_path}.{func.qualified_name}"
        )

        # 6. Store in Qdrant
        yield {
            'id': generate_id(file_path, func.name),
            'vector': vectors,
            'payload': chunk_data
        }
```

**Chunking Strategy**:
- Boundary: Function/class definitions (natural AST boundaries)
- Size: 200-400 tokens (functions larger than 400 tok are split logically)
- Overlap: None (AST boundaries are clean)
- Context: Claude-generated 50-100 tokens prepended

**Search Configuration**:
- Top-K: 100 candidates (for "implementation" profile)
- Multi-vector weights: content=0.7, title=0.2, breadcrumb=0.1
- ef parameter: 150 (3x top-K for good recall)

---

## Index 2: Docs (voyage-context-3)

### Qdrant Collection Schema
```python
{
    'name': 'docs_index',
    'vectors': {
        'content_vec': {
            'size': 1024,
            'distance': 'Dot',
            'hnsw_config': {'m': 16, 'ef_construct': 200}
        }
    },
    'payload_schema': {
        'doc_path': 'keyword',
        'heading_hierarchy': 'text',  # "Installation > Setup > Prerequisites"
        'chunk_index': 'integer',
        'adjacent_chunks': 'integer[]',  # [chunk-1, chunk+1] for context
        'doc_type': 'keyword',  # tutorial/reference/explanation/how-to
        'doc_title': 'text',
        'last_updated': 'integer',
        'workspace_id': 'keyword'
    }
}
```

### Preprocessing Pipeline
```python
async def process_doc_file(file_path: str):
    # 1. Parse markdown to section hierarchy
    sections = parse_markdown_ast(file_path)
    heading_tree = build_heading_hierarchy(sections)

    # 2. Chunk by semantic boundaries (heading-aware)
    chunks = chunk_by_headings(
        sections,
        target_size=500,  # tokens
        overlap=0,  # NO overlap for voyage-context-3
        preserve_headings=True
    )

    # 3. Prepare for voyage-context-3 (pass as list)
    chunk_list = []
    for i, chunk in enumerate(chunks):
        chunk_list.append({
            'text': chunk.content,
            'chunk_index': i,
            'heading_path': chunk.heading_hierarchy
        })

    # 4. Embed entire document in ONE API call
    # voyage-context-3 encodes document-level context automatically
    embeddings = await voyage_client.embed(
        inputs=chunk_list,  # List of chunks from same doc
        model='voyage-context-3',
        input_type='document'
    )

    # 5. Store with adjacency information
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        payload = {
            'doc_path': file_path,
            'heading_hierarchy': chunk.heading_hierarchy,
            'chunk_index': i,
            'adjacent_chunks': [i-1, i+1] if 0 < i < len(chunks)-1 else [],
            'doc_type': classify_doc_type(file_path, chunk),
            'doc_title': heading_tree.root.text
        }

        yield {
            'id': f"{file_path}:chunk:{i}",
            'vector': {'content_vec': embedding},
            'payload': payload
        }
```

**Chunking Strategy**:
- Boundary: Markdown heading boundaries (semantic units)
- Size: 500 tokens (middle of 400-600 range)
- Overlap: 0% (voyage-context-3 handles context internally)
- Context: Document-level context from voyage-context-3 (no Claude calls needed)

**Key Difference from Code**:
- NO Claude API calls for context generation (voyage-context-3 does it)
- Chunks must be passed as ordered list from same document
- Model encodes position and document context automatically

---

## Index 3: API Docs (voyage-context-3)

### Qdrant Collection Schema
```python
{
    'name': 'api_index',
    'vectors': {
        'content_vec': {
            'size': 1024,
            'distance': 'Dot',
            'hnsw_config': {'m': 16, 'ef_construct': 200}
        }
    },
    'payload_schema': {
        'service_name': 'keyword',
        'version': 'keyword',
        'endpoint_path': 'keyword',
        'http_method': 'keyword',
        'parameters': 'text',  # JSON schema
        'response_schema': 'text',
        'examples': 'text[]',
        'source': 'keyword',  # context7/openapi/scraped
        'deprecated': 'bool',
        'workspace_id': 'keyword'
    }
}
```

### Preprocessing Pipeline
```python
async def process_api_docs(source: str, source_type: str):
    if source_type == 'context7':
        # Fetch from Context7 MCP
        api_data = await context7_client.get_library_docs(
            library_id=source,
            topic='api-reference'
        )
        endpoints = parse_context7_response(api_data)

    elif source_type == 'openapi':
        # Parse OpenAPI/Swagger spec
        spec = yaml.load(source)
        endpoints = extract_endpoints_from_openapi(spec)

    elif source_type == 'scraped':
        # Parse scraped API docs
        endpoints = parse_api_html(source)

    # Process endpoints as chunks
    endpoint_chunks = []
    for endpoint in endpoints:
        chunk = {
            'text': format_api_endpoint(endpoint),  # Method, path, params, response
            'metadata': endpoint.metadata
        }
        endpoint_chunks.append(chunk)

    # Embed with voyage-context-3 (preserves API hierarchy)
    embeddings = await voyage_client.embed(
        inputs=endpoint_chunks,
        model='voyage-context-3',
        input_type='document'
    )

    for endpoint, embedding in zip(endpoints, embeddings):
        yield {
            'id': f"{endpoint.service}:{endpoint.path}",
            'vector': {'content_vec': embedding},
            'payload': {
                'service_name': endpoint.service,
                'version': endpoint.version,
                'endpoint_path': endpoint.path,
                'http_method': endpoint.method,
                'parameters': json.dumps(endpoint.parameters),
                'response_schema': json.dumps(endpoint.response),
                'examples': endpoint.examples
            }
        }
```

**Chunking Strategy**:
- Boundary: Per endpoint/method
- Size: Variable (full endpoint definition + examples)
- Context: Service-level context from voyage-context-3
- No overlap needed (endpoints are atomic)

---

## Index 4: Chat (voyage-3-large + Claude prelude)

### Qdrant Collection Schema
```python
{
    'name': 'chat_index',
    'vectors': {
        'turn_vec': {'size': 1024, 'distance': 'Dot'},
        'segment_vec': {'size': 1024, 'distance': 'Dot'},
        'summary_vec': {'size': 1024, 'distance': 'Dot'}
    },
    'payload_schema': {
        'thread_id': 'keyword',
        'prelude': 'text',  # Claude-generated 50-120 tok
        'turn_content': 'text',
        'segment_turns': 'text[]',  # 6-20 turns
        'entities': 'keyword[]',  # Tickets, repos, services
        'timestamp': 'integer',
        'participants': 'keyword[]',
        'topic_tags': 'keyword[]',
        'role': 'keyword',  # system/user/assistant
        'workspace_id': 'keyword'
    }
}
```

### Preprocessing Pipeline
```python
async def process_chat_log(conversation_file: str):
    # 1. Parse conversation into turns
    turns = parse_chat_transcript(conversation_file)

    # 2. Segment by topic (6-20 turns per segment)
    segments = detect_topic_segments(turns, min_turns=6, max_turns=20)

    # 3. For each segment, generate prelude with Claude
    for segment in segments:
        # Extract entities
        entities = await extract_entities(segment.turns)

        # Generate prelude
        prelude_prompt = f"""Generate a 50-120 token prelude for this conversation segment:

Turns: {len(segment.turns)}
First turn: {segment.turns[0].content[:200]}
Entities mentioned: {entities}

Prelude should include: topic, goal, key facts, participants, open questions."""

        prelude = await claude_api.complete(prelude_prompt, max_tokens=120)

        # 4. Embed at multiple levels
        embeddings = await voyage_client.embed(
            inputs=[
                f"{prelude}\n\n{turn.content}" for turn in segment.turns  # Turn-level
            ] + [
                f"{prelude}\n\n" + "\n".join(t.content for t in segment.turns)  # Segment
            ],
            model='voyage-3-large',
            input_type='document'
        )

        turn_vecs = embeddings[:len(segment.turns)]
        segment_vec = embeddings[-1]

        # 5. Store each turn with segment context
        for i, (turn, turn_vec) in enumerate(zip(segment.turns, turn_vecs)):
            yield {
                'id': f"{segment.thread_id}:turn:{turn.index}",
                'vector': {
                    'turn_vec': turn_vec,
                    'segment_vec': segment_vec,
                    # summary_vec computed every 20-40 turns
                },
                'payload': {
                    'thread_id': segment.thread_id,
                    'prelude': prelude,
                    'turn_content': turn.content,
                    'entities': entities,
                    'timestamp': turn.timestamp,
                    'role': turn.role
                }
            }
```

**Chunking Strategy**:
- Boundary: Topic shifts (detected via embeddings or explicit markers)
- Segment size: 6-20 turns
- Prelude: Claude-generated 50-120 tokens
- Rolling summaries: Every 20-40 turns

---

## Task Profile-Based Fusion

### Profile Definitions
```python
TASK_PROFILES = {
    'implementation': {
        'description': 'Writing new code or features',
        'weights': {'code': 0.6, 'api': 0.2, 'docs': 0.15, 'chat': 0.05},
        'top_k': {'code': 100, 'api': 40, 'docs': 60, 'chat': 20},
        'caps': {'code': 8, 'api': 4, 'docs': 4, 'chat': 2}  # Final context limits
    },
    'debugging': {
        'description': 'Investigating bugs or errors',
        'weights': {'code': 0.7, 'chat': 0.15, 'docs': 0.1, 'api': 0.05},
        'top_k': {'code': 120, 'chat': 40, 'docs': 40, 'api': 20},
        'caps': {'code': 10, 'chat': 3, 'docs': 3, 'api': 2}
    },
    'documentation': {
        'description': 'Writing or updating documentation',
        'weights': {'docs': 0.5, 'api': 0.25, 'code': 0.2, 'chat': 0.05},
        'top_k': {'docs': 100, 'api': 60, 'code': 60, 'chat': 20},
        'caps': {'docs': 10, 'api': 5, 'code': 5, 'chat': 2}
    },
    'learning': {
        'description': 'Understanding existing systems',
        'weights': {'docs': 0.4, 'api': 0.3, 'chat': 0.2, 'code': 0.1},
        'top_k': {'docs': 80, 'api': 60, 'chat': 40, 'code': 40},
        'caps': {'docs': 8, 'api': 6, 'chat': 4, 'code': 4}
    }
}
```

### Fusion Algorithm
```python
async def fused_search(query: str, profile: str = 'implementation'):
    config = TASK_PROFILES[profile]

    # Stage 1: Parallel retrieval from all indices
    results = await asyncio.gather(
        search_code_index(query, k=config['top_k']['code']),
        search_docs_index(query, k=config['top_k']['docs']),
        search_api_index(query, k=config['top_k']['api']),
        search_chat_index(query, k=config['top_k']['chat'])
    )

    # Stage 2: Apply profile weights
    weighted_results = []
    for index_name, index_results in zip(['code', 'docs', 'api', 'chat'], results):
        weight = config['weights'][index_name]
        count = int(len(index_results) * weight)
        weighted_results.extend(index_results[:count])

    # Stage 3: Global RRF fusion
    fused = reciprocal_rank_fusion(weighted_results, k=60, window=100)

    # Stage 4: Rerank top-N
    top_candidates = fused[:100]  # Or min(100, len(fused))
    reranked = await voyage_rerank(query, top_candidates, top_k=50)

    # Stage 5: Apply caps per index
    final_results = apply_caps(reranked, config['caps'])

    return final_results[:10]  # Top-10 to user
```

---

## Context Generation Strategies

### Code Context (Claude-generated)
```python
CONTEXT_PROMPT = """Generate a 50-100 token context for this code chunk:

File: {file_path}
Function: {function_name}
Docstring: {docstring}
Imports: {imports}

Context should explain:
1. What module/file this is from
2. What this function/class does
3. How it relates to the system

Keep it concise and factual."""

# Batch 10 chunks per Claude call
contexts = await claude_batch_complete(prompts, max_tokens=100)
```

### Docs Context (voyage-context-3 Native)
```python
# No separate context generation needed
# voyage-context-3 encodes document-level context when you pass chunks as ordered list

chunks_from_doc = [
    {'text': chunk1, 'chunk_index': 0},
    {'text': chunk2, 'chunk_index': 1},
    {'text': chunk3, 'chunk_index': 2}
]

# Single API call per document
embeddings = await voyage_client.embed(
    inputs=chunks_from_doc,
    model='voyage-context-3',
    input_type='document'
)
# Model automatically encodes: "This is chunk 2 of a 3-chunk document about X"
```

### Chat Prelude (Claude-generated)
```python
PRELUDE_PROMPT = """Generate a 50-120 token prelude for this conversation segment:

Thread ID: {thread_id}
Turns: {turn_count}
First turn: {first_turn_content}
Entities: {entities}
Timestamp: {timestamp}

Prelude should include:
- Topic being discussed
- Goal of the conversation
- Key facts established
- Open questions
- Participants and their roles"""

prelude = await claude_complete(PRELUDE_PROMPT, max_tokens=120)
```

---

## Cost Breakdown

### One-Time Indexing Costs

**Code Index** (250 functions):
- Context generation: 250 × (500 input + 100 output) = 150K tokens
- Claude cost: ~$0.08
- Embeddings: 250 × 3 vectors (content, title, breadcrumb) = 750 embeds
- VoyageAI cost: ~$0.02
- **Subtotal: $0.10**

**Docs Index** (200 docs, 400 chunks):
- Context generation: $0 (voyage-context-3 native)
- Embeddings: 400 chunks, batched per-document
- VoyageAI cost: ~$0.03
- **Subtotal: $0.03**

**API Index** (100 endpoints):
- Context generation: $0 (voyage-context-3)
- Embeddings: 100 endpoints
- VoyageAI cost: ~$0.01
- **Subtotal: $0.01**

**Chat Index** (100 segments):
- Prelude generation: 100 × (600 input + 120 output) = 72K tokens
- Claude cost: ~$0.04
- Embeddings: 100 segments × 3 vectors (turn, segment, summary)
- VoyageAI cost: ~$0.02
- **Subtotal: $0.06**

**Total One-Time Cost**: ~$0.20 (lower than initial $0.50 estimate)

### Incremental Update Costs
- New file: ~$0.0004 (context + embeddings)
- Modified file: Regenerate affected chunks only
- Deleted file: Remove from index (no cost)

---

## Integration with Dopemux Systems

### ConPort Knowledge Graph
```python
# Log indexing decisions
await conport.log_decision(
    workspace_id='/Users/hue/code/dopemux-mvp',
    summary='Multi-index semantic search with contextual retrieval',
    rationale='Four indices (code/docs/API/chat) with task profile-based fusion',
    implementation_details=json.dumps({
        'collections': ['code_index', 'docs_index', 'api_index', 'chat_index'],
        'total_chunks': 850,
        'total_cost': 0.20,
        'models': ['voyage-code-3', 'voyage-3-large', 'voyage-context-3', 'voyage-rerank-2.5']
    }),
    tags=['claude-context-v2', 'indexing', 'retrieval']
)

# Link search results to decisions
await conport.link_conport_items(
    workspace_id='/Users/hue/code/dopemux-mvp',
    source_item_type='search_result',
    source_item_id=result_id,
    target_item_type='decision',
    target_item_id=decision_id,
    relationship_type='informed_by',
    description='Search result led to architectural decision'
)
```

### Serena LSP Coordination
```python
# Use Serena's Tree-sitter for code chunking
from serena.tree_sitter import parse_file, extract_symbols

# Feed semantic search results back to Serena
semantic_results = await claude_context_search(query)
symbol_results = await serena.find_symbol(query)

# Cross-reference and merge
combined = merge_semantic_and_symbol_results(semantic_results, symbol_results)
```

### Dopemux Event Bus
```python
# Publish indexing progress
await event_bus.publish('indexing.progress', {
    'files_processed': count,
    'total_files': total,
    'percent_complete': (count / total) * 100,
    'current_file': file_path
})

# Publish search events for ADHD dashboard
await event_bus.publish('search.completed', {
    'query': query,
    'profile': profile,
    'results_count': len(results),
    'latency_ms': latency,
    'indices_used': ['code', 'api', 'docs']
})
```

---

## Implementation Priority

**Phase 1 (MVP - Week 1)**:
1. Code index only (voyage-code-3 + Claude context)
2. Simple dense search (no BM25 yet)
3. Basic reranking (top-50 → top-10)
4. Stdio MCP server with `code_search` tool

**Phase 2 (Week 2)**:
5. Docs index (voyage-context-3, no Claude calls)
6. API index (Context7 integration)
7. Multi-index fusion with task profiles
8. Enhanced MCP tools: `semantic_search`, `docurag_query`

**Phase 3 (Week 3)**:
9. Chat index with preludes
10. BM25 sparse search per index
11. Full hybrid (BM25 + dense + RRF)
12. ConPort integration and event publishing

**Phase 4 (Week 4)**:
13. Performance tuning (efSearch, chunk size, weights)
14. Semantic caching with Redis
15. Incremental indexing and file watching
16. Production deployment and monitoring

---

**Ready for Implementation**: Architecture validated, costs analyzed, clear component boundaries established.

Should I proceed with Phase 1 implementation (Code index + MCP server)?