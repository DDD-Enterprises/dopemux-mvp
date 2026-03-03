# Knowledge Graph RAG Analysis for Code-Centric Context Retrieval

## Executive Summary

This research analyzes different knowledge graph approaches for implementing a code-centric RAG (Retrieval-Augmented Generation) system optimized for ADHD developers. The analysis focuses on graph schemas that link code entities (files, symbols, tasks) with project context, enabling precise context retrieval.

**Key Findings:**
- Property graphs (e.g., Neo4j) naturally model code and decision relationships; adding vector search boosts semantic retrieval
- Hybrid BM25 + dense-vector search with RRF fusion provides optimal ranking performance
- ADHD-friendly UX with Top-3 results and progressive disclosure reduces cognitive load
- Target performance: <250ms p95 latency for interactive development workflows

## Model Comparison Analysis

### Property Graph Model ⭐⭐⭐⭐⭐ (Fit Score: 5/5)

**Why it fits:** Well-suited to representing code entities and relationships with rich properties (e.g., Symbol CALLS Symbol). Natural fit for static code analysis and linked decision tracking.

**Best for:**
- Static code analysis integration
- Tracking linked decisions and tasks
- Low-latency graph traversals

**Gotchas:**
- Vendor-specific semantics (no standard ontology)
- Binary-edge limitation (can't natively do n-ary relations)
- Potential vendor lock-in

**References:**
- [Daytona: Building a Knowledge Graph of Your Codebase](https://www.daytona.io/dotfiles/building-a-knowledge-graph-of-your-codebase)
- [Neo4j: Knowledge Graph vs Vector RAG](https://neo4j.com/blog/developer/knowledge-graph-vs-vector-rag/)

### RDF/OWL Model ⭐⭐⭐ (Fit Score: 3/5)

**Why it fits:** Offers standardized semantic model (triples with URIs, OWL reasoning) which aids interoperability, but is heavier and less common for code-centric data.

**Best for:**
- Integration with external RDF/OWL data
- Need for formal ontology and inference
- Data exchange across systems

**Gotchas:**
- Slower deep traversals (triple store overhead)
- Strict triple structure limits expressivity
- Fewer native tools for code analysis

### Hypergraph Model ⭐⭐⭐⭐ (Fit Score: 4/5)

**Why it fits:** Hyperedges can connect many vertices (n-ary relations) with roles, ideal for modeling complex multi-entity relationships (e.g., multi-part task or decision involving many symbols).

**Best for:**
- Encoding multi-party relations (tasks/meetings)
- When relationships need attributes or roles
- Knowledge representation requiring high expressivity

**Gotchas:**
- Less mainstream (e.g., TypeDB/Vaticle) with specialized query (TypeQL)
- Higher complexity for developers
- Smaller ecosystem

### Multi-Model Database ⭐⭐⭐⭐⭐ (Fit Score: 5/5)

**Why it fits:** Unifies graph, document, and vector storage (e.g., ArangoDB), enabling queries that span structured graphs and full-text/vector search in one engine.

**Best for:**
- Need to combine graph relationships with text or vector search
- Projects requiring flexibility (graph + JSON + search)

**Gotchas:**
- Increased database complexity and configuration
- Must decide which data model to use for each query
- Potential performance tuning across modes

### Graph Over Vectors (Hybrid RAG) ⭐⭐⭐⭐⭐ (Fit Score: 5/5)

**Why it fits:** Link graph nodes to embedding vectors, enabling BM25/dense retrieval plus multi-hop graph reasoning (Graph RAG). Best of both worlds approach.

**Best for:**
- High recall needs with contextual linking
- Query scenarios requiring both semantic similarity and relational context

**Gotchas:**
- Most complex setup (graph DB + vector store + fusion logic)
- Requires tuning of fusion weights and cutoffs
- Higher resource usage

## Reference Schema

### Core Node Types

```json
{
  "nodes": [
    {"type":"Project","props":["name","description","lastActivity"]},
    {"type":"Repo","props":["url","branch","lastCommitId"]},
    {"type":"Directory","props":["path"]},
    {"type":"File","props":["path","language","commitHash","prelude"]},
    {"type":"Symbol","props":["fqname","kind","file","lineNo","popularity","prelude","emb"]},
    {"type":"Commit","props":["id","author","date","message"]},
    {"type":"PullRequest","props":["id","title","author","status"]},
    {"type":"Build","props":["id","status","artifact"]},
    {"type":"TestRun","props":["id","status","duration"]},
    {"type":"Decision","props":["id","title","date","impact","prelude","emb"]},
    {"type":"ADR","props":["id","title","date","status","prelude","emb"]},
    {"type":"Caveat","props":["id","description","severity","impact","prelude","emb"]},
    {"type":"FollowUp","props":["id","note","date"]},
    {"type":"Pattern","props":["name","description","prelude","emb"]},
    {"type":"Task","props":["id","title","status","priority","dueDate"]},
    {"type":"Milestone","props":["id","title","dueDate"]},
    {"type":"Person","props":["username","name","skills"]},
    {"type":"Session","props":["id","startTime","endTime"]},
    {"type":"Error","props":["id","message","severity","timestamp"]},
    {"type":"Artifact","props":["id","name","type","uri"]},
    {"type":"DocPage","props":["id","title","content","url","emb"]}
  ]
}
```

### Relationship Types

```json
{
  "edges": [
    {"type":"CONTAINS","from":"Repo","to":"Directory","props":[]},
    {"type":"CONTAINS","from":"Directory","to":"File","props":[]},
    {"type":"DECLARES","from":"File","to":"Symbol","props":[]},
    {"type":"CALLS","from":"Symbol","to":"Symbol","props":["weight"]},
    {"type":"TESTS","from":"TestRun","to":"Symbol","props":[]},
    {"type":"MODIFIES","from":"Commit","to":"File","props":[]},
    {"type":"RELATES_TO","from":"Decision","to":"Symbol","props":[]},
    {"type":"BLOCKED_BY","from":"Task","to":"Task","props":[]},
    {"type":"DERIVES_FROM","from":"ADR","to":"Decision","props":[]},
    {"type":"CAVEAT_FOR","from":"Caveat","to":"Symbol","props":[]},
    {"type":"ASSIGNED_TO","from":"Task","to":"Person","props":[]},
    {"type":"MENTIONS","from":"DocPage","to":"Symbol","props":[]},
    {"type":"PRODUCES","from":"Build","to":"Artifact","props":[]},
    {"type":"OBSERVED_IN","from":"Error","to":"Session","props":[]}
  ]
}
```

### Indexing Strategy

```cypher
-- Core entity indexes
INDEX ON :Project(name)
INDEX ON :File(path)
INDEX ON :Symbol(fqname)
INDEX ON :Task(id)
INDEX ON :Decision(id)

-- Full-text search indexes
FULLTEXT INDEX ON :DocPage(title, content)

-- Vector indexes for semantic search
VECTOR INDEX ON :Symbol(emb)
VECTOR INDEX ON :Decision(emb)
VECTOR INDEX ON :Pattern(emb)
VECTOR INDEX ON :Caveat(emb)
VECTOR INDEX ON :DocPage(emb)
```

## Retrieval Recipes

### Pre-Change Briefing Pattern

**Stage 1:** BM25 + dense-vector embedding search (k=50)
**Stage 2:** Graph-neighborhood expansion (symbols→decisions/caveats)
**Scoring:** Weighted RRF fusion of BM25 and vector ranks
**Reranker:** Semantic re-ranker (LLM or transformer)
**Target Latency:** <250ms

### Decision Rationale Pattern

**Stage 1:** Full-text + vector search on ADR/Decision summaries
**Stage 2:** Graph hops (Decision→related symbols/tasks)
**Scoring:** RRF of text and dense queries; boost recent/high-impact decisions
**Target Latency:** <250ms

### Next Actions Pattern

**Stage 1:** Keyword + embedding search on Task descriptions
**Stage 2:** Graph expansion (Task→BLOCKED_BY tasks, Task→Symbol context)
**Scoring:** Lexical + semantic hybrid scoring, weighted by urgency
**Target Latency:** <250ms

## ADHD-Optimized UX Design

### Top-3 Contract

Each result includes:
- **title**: Clear, actionable description
- **why**: 1-line explanation of relevance
- **link**: Direct path to resource
- **actions[]**: Available actions (view, edit, run tests)

**Example Output:**
```json
[
  {
    "title": "Adopt MVC pattern for Auth module",
    "why": "Decision ADR#5 emphasized maintainability",
    "link": "conport/adr/5.md",
    "actions": ["view ADR", "open file"]
  },
  {
    "title": "Fix null-check in PaymentService",
    "why": "Caveat filed after test failure",
    "link": "conport/caveat/12.md",
    "actions": ["view caveat", "run tests"]
  }
]
```

### Progressive Disclosure Principles

- **Essential First**: Show most critical information in initial view
- **Context on Demand**: Detailed explanations available on request
- **Visual Indicators**: Use clear visual cues for different content types
- **Empty State Guidance**: Helpful prompts when no results found

## Migration Strategy

### Phase 1: Data Export and Schema Bootstrap
1. Export existing ConPort data (decisions, caveats, patterns)
2. Transform into new graph schema (scripts to create nodes/edges)
3. Bootstrap with code symbol graph using AST/call graph parsing

### Phase 2: MCP Integration
1. Set up MCP event hooks for real-time updates
2. Link commit/PR/test events to graph updates
3. Create Decision/Caveat nodes from new ADRs with RELATES_TO edges

### Phase 3: Batch Processing
1. Schedule nightly jobs for full-text index refresh
2. Re-compute embeddings for modified content
3. Update popularity scores and relationship weights

### Phase 4: Validation
1. Sample queries to verify key decisions/tasks appear in results
2. Performance testing to meet <250ms latency targets
3. A/B testing with existing ConPort interface

## Evaluation Framework

### Test Tasks
- **Onboard a file**: Retrieve related symbols, patterns, and decisions
- **Understand a decision**: Fetch ADR/Caveat with linked symbols/files
- **Fix failing test**: Gather context on test, related code, and known bugs
- **Implement feature**: List next tasks and affected files from task graph

### Success Metrics
- **MRR@3**: Mean Reciprocal Rank at 3 (higher = relevant results appear earlier)
- **Time-to-First-Snippet**: Latency until first useful context returned
- **P95 Latency**: 95th percentile query latency (target ≤250ms)
- **Helpfulness Rate**: Percent of sessions where Top-3 results unblocked task

## Implementation Examples

### Sample Cypher Queries

```cypher
-- Find all symbols called by a specific function
MATCH (s:Symbol {fqname:'com.example.auth.User'})-[:CALLS]->(t:Symbol)
RETURN t.fqname;

-- Find decisions related to a specific service
MATCH (d:Decision)-[:RELATES_TO]->(sym:Symbol {fqname:'com.example.payment.PaymentService'})
RETURN d.id, d.title;

-- Find blocking tasks for a specific task
MATCH (task:Task {id:'T123'})-[:BLOCKED_BY]->(prev)
RETURN prev.title, prev.status;
```

### ETL Pipeline Patterns

```python
# AST → Graph: Extract symbols and call relationships
def extract_code_graph(file_path):
    tree = tree_sitter.parse(file_path)
    symbols = extract_symbols(tree)
    calls = extract_call_relationships(tree)
    return create_nodes_and_edges(symbols, calls)

# CI/VC → Graph: Update on commits
def handle_commit_event(commit_id, files_changed):
    for file in files_changed:
        update_file_node(file, commit_id)
        update_symbol_nodes(file)
        create_commit_edges(commit_id, files_changed)

# ConPort → Graph: Create decision nodes
def handle_decision_event(decision_data):
    decision_node = create_decision_node(decision_data)
    referenced_symbols = extract_symbol_references(decision_data.content)
    create_relates_to_edges(decision_node, referenced_symbols)
```

## Conclusion

The hybrid approach combining property graphs with vector embeddings provides the optimal balance for Dopemux's code-centric RAG needs. This solution enables both structural reasoning (through graph traversals) and semantic search (through embeddings) while maintaining ADHD-friendly UX principles with progressive disclosure and cognitive load reduction.

**Recommended Architecture:**
- **Primary Store**: Neo4j or ArangoDB for graph + vectors
- **Search Strategy**: Hybrid BM25 + dense vector with RRF fusion
- **UX Pattern**: Top-3 results with progressive disclosure
- **Integration**: Event-driven updates via MCP system
- **Performance Target**: <250ms p95 latency

---
*Research compiled: September 2025*
*Status: Ready for RFC implementation*