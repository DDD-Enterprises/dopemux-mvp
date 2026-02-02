---
id: conport-dopemux
title: Conport Dopemux
type: historical
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
---
# Blueprint: ConPort Memory Hub Integration in Dopemux

## Overview
ConPort serves as the **central nervous system** for the Dopemux ADHD-optimized development workflow. It provides persistent memory, decision logging, work queue management, and cross-project knowledge preservation while maintaining real-time synchronization with all workflow components.

## Architecture Position
```
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   ConPort       │◄──►│  Task Orchestrator   │    │   Leantime      │
│   (Memory Hub)  │    │  (Tactical Executor) │    │   (Strategy)     │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
         ▲                       ▲                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│   Knowledge     │    │     Playwright       │    │     Zen MCP     │
│   Graph         │    │    (Validation)      │    │   (Analysis)     │
└─────────────────┘    └──────────────────────┘    └─────────────────┘
```

## Core Capabilities

### Cross-Project Memory Namespaces
ConPort extends beyond single-project memory to provide cross-project knowledge:

#### Decisions Namespace (`decisions/*`)
- **Purpose**: Atomic decision nodes with full context and rationale
- **Schema**: title, rationale, implementation_details, who, when, tags, links
- **Use Cases**: Architecture choices, technology selections, design decisions

#### Work Items Namespace (`work/*`)
- **Purpose**: Unified task queue across projects and contexts
- **Schema**: title, description, status, priority, due_date, source, cognitive_load, energy_required
- **Use Cases**: Upcoming work tracking, progress management, priority assignment

#### Artifacts Namespace (`artifacts/*`)
- **Purpose**: File artifacts with metadata and relationships
- **Schema**: kind, title, path, hash, size, mime_type, links
- **Use Cases**: Screenshots, diffs, logs, validation evidence, documentation

### Knowledge Graph Relationships
- **Entity Linking**: Connect decisions, work items, and artifacts
- **Relationship Types**: implements, validates, depends_on, references, created_by
- **Graph Queries**: Find related entities and understand dependencies

### Semantic Search
- **Vector Embeddings**: Voyage AI embeddings for natural language search
- **Cross-Project Retrieval**: Search across all projects and contexts
- **Context-Aware Results**: Include relevance scores and relationship context

## Integration Points

### With Task Orchestrator (Tactical Execution)
```python
# Work intake from ConPort
upcoming = conport.upcoming_next(limit=3)
selected_task = upcoming[0]

# Status synchronization
conport.work_update_status(selected_task.id, "in_progress")

# Decision logging during execution
conport.decisions_add({
    title: "Selected task for execution",
    rationale: f"Priority: {selected_task.priority}, Due: {selected_task.due_date}",
    tags: ["task-execution", "workflow-start"],
    links: [{"type": "work_item", "id": selected_task.id}]
})

# Completion and validation
conport.decisions_add({
    title: f"Completed: {task.title}",
    rationale: "Successfully implemented with validation",
    links: [{"type": "work_item", "id": task.id}]
})
```

### With Leantime (Strategic PM)
```python
# Sync Leantime tickets to ConPort work items
leantime_tickets = leantime.list_tickets()
for ticket in leantime_tickets:
    conport.work_upcoming_add({
        title: ticket.title,
        description: ticket.description,
        priority: map_leantime_priority(ticket.priority),
        source: "leantime",
        source_ref: ticket.id
    })

# Update Leantime with progress
conport_progress = conport.work_get_status(work_item_id)
leantime.update_ticket(conport_progress.source_ref, {
    status: map_conport_status(conport_progress.status)
})
```

### With Playwright (Validation)
```python
# Attach validation artifacts
conport.artifacts_attach({
    kind: "screenshot",
    title: f"Validation: {task.title}",
    path: screenshot_path,
    work_item_id: task.id
})

# Link validation to work completion
conport.graph_link({
    source_type: "work_item",
    source_id: task.id,
    target_type: "artifact",
    target_id: artifact.id,
    relationship_type: "validated_by"
})
```

### With Zen MCP (Complex Analysis)
```python
# Log escalation decisions
conport.decisions_add({
    title: "Escalated to Zen for complex analysis",
    rationale: f"Task complexity ({task.cognitive_load}) exceeded threshold",
    tags: ["zen-escalation", "complex-analysis"],
    links: [{"type": "work_item", "id": task.id}]
})

# Store Zen consensus results
conport.decisions_add({
    title: "Zen consensus reached",
    rationale: zen_consensus.summary,
    implementation_details: zen_consensus.recommendations,
    tags: ["zen-result", "consensus"],
    links: [{"type": "work_item", "id": task.id}]
})
```

## Workflow Patterns

### Hello-Flow Integration
1. **Pick Work**: `conport.upcoming_next()` provides next task
2. **Plan & Execute**: Task Orchestrator updates progress in ConPort
3. **Validate**: Playwright attaches evidence to ConPort artifacts
4. **Close Loop**: Final status and decisions logged in ConPort

### Decision Documentation Protocol
**MANDATORY**: Every non-trivial choice logged with complete context:

```python
conport.decisions_add({
    workspace_id: current_workspace,
    title: "[Specific, actionable decision title]",
    rationale: "[Why this choice] - Technical reasoning, trade-offs, constraints",
    implementation_details: "[How implemented] - Specific steps, tools used",
    tags: ["architecture|implementation|security|performance", ...],
    links: [
        {type: "work_item", id: task_id},
        {type: "artifact", id: validation_screenshot},
        {type: "decision", id: related_previous_decision}
    ]
})
```

### Cross-Project Knowledge Reuse
```python
# Search across projects for similar decisions
similar_decisions = conport.semantic_search({
    query: "authentication implementation patterns",
    entity_types: ["decision"],
    top_k: 5
})

// Find related work patterns
related_work = conport.graph_query({
    entity_type: "decision",
    entity_id: decision_id,
    relationship_filter: "implements"
})
```

## ADHD Optimizations

### Cognitive Load Management
- **Progressive Disclosure**: Essential info first, details on demand
- **Complexity Scoring**: 0.0-1.0 scale for ADHD-safe content assessment
- **Energy Matching**: Tasks tagged with required energy levels
- **Context Preservation**: Seamless resumption after interruptions

### Memory Reliability
- **Atomic Operations**: All changes committed transactionally
- **Failure Recovery**: Spool operations when unavailable, replay on recovery
- **Version History**: Complete audit trail with timestamps
- **Backup Safety**: Point-in-time recovery capabilities

### Performance Optimizations
- **Query Caching**: Redis caching for frequent lookups
- **Batch Operations**: Bulk updates and queries supported
- **Vector Indexing**: HNSW indexes for fast semantic search
- **Lazy Loading**: Progressive result loading for large datasets

## Configuration

### Database Schema
```sql
-- Core namespaces
CREATE TABLE decisions (...);     -- decisions/*
CREATE TABLE work_items (...);    -- work/*
CREATE TABLE artifacts (...);     -- artifacts/*

-- Knowledge graph
CREATE TABLE knowledge_edges (...);    -- Entity relationships
CREATE TABLE semantic_chunks (...);    -- Vector embeddings

-- Performance indexes
CREATE INDEX CONCURRENTLY idx_decisions_workspace_created ON decisions(workspace_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_work_items_status_priority ON work_items(workspace_id, status, priority DESC);
```

### MCP Server Configuration
```json
{
  "conport": {
    "command": "docker",
    "args": ["exec", "-i", "mcp-conport_main", "python", "/app/conport_mcp_stdio.py"],
    "env": {
      "CONPORT_URL": "http://localhost:3004",
      "DOPEMUX_WORKSPACE_ID": "/Users/hue/code/dopemux-mvp",
      "CONPORT_DB_URL": "postgres://localhost:5432/conport",
      "CONPORT_GRAPH_DIR": "./.conport/graph"
    }
  }
}
```

### Environment Variables
- `CONPORT_DB_URL`: PostgreSQL connection string
- `CONPORT_GRAPH_DIR`: Local graph storage directory
- `VOYAGE_API_KEY`: Vector embedding service key
- `REDIS_URL`: Caching layer connection (optional)

## Tool Interface

### Decision Management
- `conport_decisions_add`: Log new decision with full context
- `conport_decisions_get`: Retrieve decisions with filtering
- `conport_decisions_search`: Semantic search across decisions

### Work Management
- `conport_work_upcoming_add`: Add work item to queue
- `conport_work_upcoming_next`: Get next priority work items
- `conport_work_update_status`: Update work item progress

### Artifact Management
- `conport_artifacts_attach`: Attach file artifact with metadata
- `conport_artifacts_list`: Query artifacts with filtering

### Knowledge Graph
- `conport_graph_link`: Create entity relationships
- `conport_graph_query`: Find related entities
- `conport_semantic_search`: Natural language search across all content

## Performance Characteristics

### Response Times
- **Simple Operations**: < 100ms (status updates, basic queries)
- **Complex Queries**: < 500ms (filtered searches, graph queries)
- **Semantic Search**: < 2s (vector similarity + reranking)

### Scalability Limits
- **Concurrent Users**: Unlimited (PostgreSQL connection pooling)
- **Data Volume**: Tested with 100K+ decisions and work items
- **Search Performance**: Sub-second for typical queries

### Resource Usage
- **Memory**: ~200MB base + 50MB per active workspace
- **Storage**: ~1GB per 10K entities (with embeddings)
- **CPU**: Minimal for typical workloads

## Quality Assurance

### Data Integrity
- **Transaction Safety**: All operations wrapped in database transactions
- **Referential Integrity**: Foreign key constraints maintain relationships
- **Audit Trail**: Complete history of all changes

### Backup & Recovery
- **Point-in-Time Recovery**: PostgreSQL WAL-based recovery
- **Export/Import**: Markdown export for portability
- **Cross-Platform**: Works across different Dopemux instances

### Monitoring & Health
- **Health Checks**: Automatic service availability monitoring
- **Performance Metrics**: Query latency and throughput tracking
- **Storage Analytics**: Data volume and growth monitoring

## Deployment Patterns

### Development Environment
- **Local PostgreSQL**: Docker container for development
- **Auto-Migration**: Schema updates applied on startup
- **Debug Logging**: Detailed operation logging for troubleshooting

### Production Deployment
- **Managed PostgreSQL**: Cloud database service (RDS, Cloud SQL)
- **High Availability**: Read replicas for query scaling
- **Backup Automation**: Daily snapshots with retention policies

### Multi-Workspace Support
- **Workspace Isolation**: Complete data separation between workspaces
- **Cross-Workspace Search**: Optional federation for enterprise deployments
- **Permission Model**: Workspace-level access control

## Failure Recovery

### Service Outage Handling
1. **Detection**: Automatic health check failures
2. **Spooling**: Queue operations to local NDJSON files
3. **Background Recovery**: Monitor for service restoration
4. **Replay**: Automatically replay queued operations

### Data Consistency
1. **Transaction Rollback**: Failed operations don't corrupt state
2. **Idempotent Operations**: Safe to replay operations multiple times
3. **Conflict Resolution**: Last-write-wins with timestamp ordering

### Manual Recovery
1. **Export Data**: Markdown export for backup
2. **Service Restart**: Clean startup with data integrity checks
3. **Import Verification**: Validate imported data against backups

## Future Extensions

### Planned Enhancements
- **Multi-Modal Content**: Support for images, audio, video artifacts
- **Advanced Graph Analytics**: Path finding, centrality analysis
- **Collaborative Features**: Multi-user decision workflows

### Integration Opportunities
- **IDE Plugins**: Direct ConPort integration in development environments
- **Mobile Companion**: Decision and work tracking on mobile devices
- **API Gateway**: REST API for external tool integrations

## Troubleshooting

### Common Issues
1. **Connection Failures**: Check PostgreSQL connectivity and credentials
2. **Search Performance**: Rebuild vector indexes for improved query speed
3. **Storage Growth**: Archive old artifacts to manage disk usage

### Debug Tools
- **Schema Inspection**: Check table structures and index health
- **Query Profiling**: Identify slow queries and optimization opportunities
- **Data Export**: Generate reports for data consistency verification

## Success Metrics

### Effectiveness Measures
- **Decision Coverage**: Percentage of decisions properly documented
- **Work Completion**: Tasks completed with full audit trails
- **Search Effectiveness**: User satisfaction with semantic search results

### Quality Indicators
- **Data Integrity**: Zero data corruption incidents
- **Recovery Success**: Percentage of failed operations successfully recovered
- **Performance**: P95 query latency under 500ms

### User Experience
- **Context Preservation**: Zero user context lost due to system failures
- **Search Relevance**: Average semantic search result relevance > 0.8
- **Recovery Transparency**: Users informed of automatic recovery actions

This blueprint positions ConPort as the reliable memory foundation that enables the entire Dopemux ecosystem to function cohesively while providing exceptional support for ADHD-optimized development workflows.
