# RFC-0044: Knowledge Graph RAG System for Code-Centric Context Retrieval

- **Status**: Proposed
- **Author**: Claude Code / Dopemux Team
- **Date**: 2025-09-25
- **Related**: ADR-037 (ADHD Finishing Helpers), RFC-0043 (MetaMCP Orchestration)

## Summary

Implement a hybrid knowledge graph + vector RAG system to provide precise, ADHD-friendly context retrieval for code development tasks. This system will replace traditional keyword search with intelligent graph-based reasoning combined with semantic similarity search.

## Context

Current challenges in the Dopemux codebase context management:

1. **Information Fragmentation**: Decisions, caveats, and code context are scattered across files, ADRs, and ConPort entries
2. **ADHD Cognitive Load**: Traditional search results overwhelm users with too many options and insufficient context
3. **Relationship Blindness**: Existing tools don't surface how code, decisions, and tasks interconnect
4. **Context Switching Cost**: Developers lose mental model when jumping between related but disconnected information

### Current State
- ConPort manages decisions and caveats in isolated documents
- MCP servers provide individual tool functionality without cross-cutting context
- Code understanding requires manual exploration of relationships
- ADHD finishing helpers lack deep contextual awareness

### Desired Future State
- Unified graph of code entities, decisions, tasks, and relationships
- Sub-250ms context retrieval with Top-3 ADHD-friendly results
- Automatic relationship discovery and progressive context disclosure
- Event-driven updates maintaining real-time graph accuracy

## Decision

**Adopt a hybrid knowledge graph RAG system** with the following architecture:

### Core Technology Stack
- **Graph Database**: Neo4j or ArangoDB (multi-model preferred)
- **Vector Store**: Integrated vector indices within graph database
- **Search Strategy**: Hybrid BM25 + dense vector embeddings with RRF fusion
- **Embedding Model**: OpenAI text-embedding-ada-002 or equivalent

### Schema Design

#### Node Types
```
Project, Repo, Directory, File, Symbol, Commit, PullRequest, Build, TestRun,
Decision, ADR, Caveat, FollowUp, Pattern, Task, Milestone, Person, Session,
Error, Artifact, DocPage
```

#### Relationship Types
```
CONTAINS, DECLARES, CALLS, TESTS, MODIFIES, RELATES_TO, BLOCKED_BY,
DERIVES_FROM, CAVEAT_FOR, ASSIGNED_TO, MENTIONS, PRODUCES, OBSERVED_IN
```

### Retrieval Patterns

1. **Pre-Change Briefing**: BM25 + vector search → graph neighborhood expansion
2. **Decision Rationale**: Text + semantic search on ADRs → related symbols/tasks
3. **Next Actions**: Task search → dependency graph traversal

### ADHD-Optimized UX

**Top-3 Contract**: Each result provides:
- `title`: Clear, actionable description
- `why`: One-line relevance explanation
- `link`: Direct resource path
- `actions[]`: Available operations

**Progressive Disclosure**: Essential information first, details on request

## Implementation Plan

### Phase 1: Foundation (Week 1-2)
1. **Database Setup**: Deploy Neo4j/ArangoDB with vector indices
2. **Schema Bootstrap**: Implement core node/edge types
3. **Data Migration**: Export ConPort decisions/caveats to graph format

### Phase 2: Code Integration (Week 3-4)
1. **AST Parsing**: Extract symbols and call graphs from codebase
2. **MCP Event Hooks**: Real-time updates on commits/PRs/tests
3. **Embedding Pipeline**: Generate and store vector representations

### Phase 3: Search Implementation (Week 5-6)
1. **Hybrid Search**: Implement BM25 + vector fusion with RRF
2. **Graph Traversal**: Multi-hop context expansion algorithms
3. **Ranking Logic**: Relevance scoring with recency/impact weighting

### Phase 4: UX Integration (Week 7-8)
1. **Top-3 Interface**: ADHD-friendly result presentation
2. **MetaMCP Integration**: Expose via existing MCP orchestration
3. **Progressive Disclosure**: Expandable context interfaces

### Phase 5: Optimization (Week 9-10)
1. **Performance Tuning**: Achieve <250ms p95 latency target
2. **Cache Strategy**: Precompute common traversal paths
3. **Evaluation Framework**: Implement MRR@3 and helpfulness metrics

## Technical Architecture

### Data Flow
```
Code Changes → AST Parser → Graph Updates
ConPort Events → Decision Nodes → Relationship Links
User Queries → Hybrid Search → Graph Expansion → Top-3 Results
```

### Integration Points

#### With Existing Systems
- **ConPort**: Decision/caveat nodes with symbol relationships
- **MCP Servers**: Event-driven graph updates from tool operations
- **ADHD Helpers**: Context-aware finishing task recommendations
- **MetaMCP**: Orchestrated access to graph search capabilities

#### New Components
- **Graph ETL Pipeline**: Continuous data ingestion and updates
- **Hybrid Search Engine**: BM25 + vector fusion with graph expansion
- **Context API**: Top-3 results with progressive disclosure interface

## Consequences

### Benefits
1. **Reduced Context Switching**: Related information discoverable in one query
2. **ADHD Accommodation**: Cognitive load reduction through Top-3 + progressive disclosure
3. **Relationship Discovery**: Automatic surfacing of code/decision connections
4. **Real-time Accuracy**: Event-driven updates maintain current state
5. **Semantic Understanding**: Vector embeddings capture conceptual similarity

### Trade-offs
1. **Implementation Complexity**: Multi-component system with graph + vector concerns
2. **Resource Requirements**: Higher memory/compute for graph database and embeddings
3. **Dependency Risk**: Additional infrastructure component to maintain
4. **Learning Curve**: New query patterns and result interpretation
5. **Data Consistency**: Complex synchronization between multiple data sources

### Risk Mitigation
- **Gradual Rollout**: Implement alongside existing search, migrate incrementally
- **Performance Monitoring**: Continuous latency tracking with alerting
- **Fallback Strategy**: Traditional search available if graph system fails
- **Backup/Recovery**: Regular graph database snapshots and restoration procedures

## Evaluation Criteria

### Success Metrics
- **MRR@3**: >0.7 (70% of relevant results in top-3 positions)
- **P95 Latency**: <250ms for interactive developer workflows
- **Helpfulness Rate**: >80% of users report Top-3 results unblock tasks
- **Adoption Rate**: >60% of context queries use graph system within 30 days

### Test Scenarios
- **File Onboarding**: Retrieve symbols, patterns, decisions for new file
- **Decision Understanding**: Find ADR with linked affected code/tasks
- **Test Failure Analysis**: Context gathering for failing tests and related bugs
- **Feature Implementation**: Task dependencies and affected file discovery

## Alternative Approaches Considered

### Pure Vector Search
**Rejected**: Lacks structural relationship reasoning capability

### Traditional Full-Text Search
**Rejected**: Doesn't surface implicit connections between code and decisions

### RDF/OWL Triple Store
**Rejected**: Overhead too high for code-centric queries, limited tooling ecosystem

### Document-Only RAG
**Rejected**: Misses fine-grained symbol-level relationships and call graphs

## References

- [Knowledge Graph RAG Research Analysis](../research/knowledge-graph-rag-analysis.md)
- [Neo4j: Knowledge Graph vs Vector RAG](https://neo4j.com/blog/developer/knowledge-graph-vs-vector-rag/)
- [Microsoft: Hybrid Search with RRF](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking)
- [ConPort Integration Patterns](../03-reference/conport-integration-patterns.md)
- [ADR-037: ADHD Finishing Helpers System](../90-adr/037-adhd-finishing-helpers-system.md)

## Appendix: Sample Implementations

### Graph Query Examples

```cypher
-- Find decisions affecting a specific symbol
MATCH (d:Decision)-[:RELATES_TO]->(s:Symbol {fqname: 'dopemux.auth.User'})
RETURN d.title, d.impact, d.date
ORDER BY d.date DESC;

-- Discover task dependencies
MATCH (t:Task {id: 'ADHD-123'})-[:BLOCKED_BY*1..3]->(dep:Task)
RETURN dep.title, dep.status, dep.priority;

-- Pre-change briefing for file modification
MATCH (f:File {path: 'src/auth/user.py'})
MATCH (f)-[:DECLARES]->(s:Symbol)
OPTIONAL MATCH (s)<-[:RELATES_TO]-(d:Decision)
OPTIONAL MATCH (s)<-[:CAVEAT_FOR]-(c:Caveat)
RETURN s.fqname, d.title, c.description;
```

### API Interface Design

```python
@dataclass
class ContextResult:
    title: str
    why: str  # One-line explanation
    link: str
    actions: List[str]

class GraphRAGService:
    async def get_context(
        self,
        query: str,
        context_type: str = "general"
    ) -> List[ContextResult]:
        """Return Top-3 context results with progressive disclosure"""
        pass

    async def expand_context(
        self,
        result_id: str
    ) -> Dict[str, Any]:
        """Get detailed context for specific result"""
        pass
```

---
*RFC-0044 Status: Proposed*
*Next Review: 2025-10-02*
*Implementation Target: Q4 2025*