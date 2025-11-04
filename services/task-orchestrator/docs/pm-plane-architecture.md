# PM Plane Architecture Documentation

## Overview

The PM Plane represents a sophisticated two-plane architecture designed to seamlessly integrate human project management with AI-powered coordination and ADHD-optimized workflows.

## Core Architecture

### Two-Plane Design

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Leantime      │◄──►│ Task Orchestrator │◄──►│   ConPort-KG    │
│ (Human PM Tool) │    │ (Coordination Hub)│    │ (Knowledge Graph)│
└─────────┬───────┘    └─────────┬─────────┘    └─────────┬───────┘
         │                         │                         │
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   ▼
                    ┌──────────────────┐
                    │ Taskmaster AI    │
                    │ (Intelligent     │
                    │  Analysis)       │
                    └──────────────────┘
```

### Component Roles

#### Leantime (Human Interface Plane)
- **Purpose**: Human-facing project management and task creation
- **API**: JSON-RPC with `x-api-key` authentication
- **Data Model**: Projects, tickets, milestones, assignments
- **Integration**: MCP bridge provides tools for project/ticket management

#### ConPort (Knowledge Graph Plane)
- **Purpose**: Central knowledge storage and semantic search
- **API**: MCP protocol with progress logging and decision tracking
- **Data Model**: Progress entries, decisions, patterns, relationships
- **Integration**: Storage authority for all project knowledge

#### Task Orchestrator (Coordination Hub)
- **Purpose**: Intelligent task routing and ADHD optimization
- **Components**: Agent dispatch, ADHD accommodations, sync management
- **Integration**: Connects all components with event-driven architecture

#### Taskmaster AI (Intelligent Analysis)
- **Purpose**: AI-powered task decomposition and complexity assessment
- **Features**: PRD analysis, strategic planning, confidence scoring
- **Integration**: Bridge interface for AI task management

## Data Flow Architecture

### Primary Task Flow

```
1. Human creates task in Leantime
2. Task Orchestrator receives update via sync
3. ADHD optimization calculates cognitive load/energy requirements
4. Task stored in ConPort with metadata tags
5. Optimal AI agent assigned (Serena/Zen/Taskmaster)
6. Agent executes task with human oversight
7. Results synced back to all systems
```

### Synchronization Mechanisms

#### Event-Driven Sync
- **SyncEvent Objects**: Standardized event format for cross-system communication
- **Target Systems**: Specify which components should receive updates
- **Event Types**: task_updated, decision_logged, progress_changed

#### Conflict Resolution
- **Timestamp Priority**: Latest update wins for simple conflicts
- **Intelligent Merging**: Field-level conflict resolution
- **Human Override**: Critical decisions flagged for manual review

#### Caching Strategy
- **Redis**: Fast access for frequently used data
- **ConPort**: Persistent storage for all project knowledge
- **Local Cache**: Fallback for offline operation

## ADHD Optimization Framework

### Cognitive Load Management

#### Task Assessment
- **Complexity Scoring**: 0.0-1.0 scale based on task characteristics
- **Energy Requirements**: low/medium/high based on complexity
- **Context Switching**: Penalty calculation for task changes

#### User State Tracking
- **Energy Levels**: Real-time monitoring with trend analysis
- **Attention State**: focused/scattered/transitioning detection
- **Break Management**: 25-minute session enforcement

### Progressive Disclosure

#### Information Hierarchy
- **Essential First**: Critical task information displayed immediately
- **On-Demand Details**: Additional context available when requested
- **Cognitive Load Reduction**: Prevents information overwhelm

#### Decision Simplification
- **Agent Routing**: Automatic AI agent selection
- **Option Reduction**: Limited choices to prevent analysis paralysis
- **Context Preservation**: Maintain mental model across sessions

## Integration Patterns

### MCP Protocol Usage

#### Tool Standardization
- **Leantime Bridge**: `create_project`, `list_projects`, `create_ticket`, `list_tickets`
- **ConPort**: `log_progress`, `update_progress`, `semantic_search`, `get_decisions`
- **Taskmaster**: `analyze_complexity`, `decompose_task`, `generate_prd_analysis`

#### Authentication
- **Leantime**: `x-api-key` header with API key from settings
- **ConPort**: MCP client authentication via workspace tokens
- **Taskmaster**: Bridge authentication with provider credentials

### Agent Routing Logic

#### Decision Tree
```
1. Check user readiness (energy + complexity match)
2. High complexity (>0.8) → Zen (multi-model analysis)
3. Implementation tasks → Serena (code intelligence)
4. Research tasks → Taskmaster (AI analysis)
5. Default → ConPort (decision logging)
```

#### Performance Tracking
- **Success Rates**: Agent performance monitoring and learning
- **User Preferences**: Override patterns influence future routing
- **Load Balancing**: Distribute work across available agents

## Technical Specifications

### API Endpoints

#### Leantime JSON-RPC
```json
{
  "jsonrpc": "2.0",
  "method": "leantime.rpc.projects.getAll",
  "params": {"state": "0"},
  "id": 1
}
```

#### ConPort MCP Calls
```python
# Log progress entry
await conport_client.log_progress(
    workspace_id="project_id",
    status="IN_PROGRESS",
    description="Task description",
    tags=["energy-medium", "complexity-3"]
)
```

### Data Models

#### OrchestrationTask
```python
{
  "id": "task_123",
  "leantime_id": 456,
  "conport_id": 789,
  "title": "Implement user authentication",
  "description": "Add JWT token validation",
  "status": "in_progress",
  "complexity_score": 0.7,
  "energy_required": "high",
  "cognitive_load": 0.6,
  "break_frequency_minutes": 25
}
```

#### SyncEvent
```python
{
  "source_system": "leantime",
  "target_systems": ["conport", "task_orchestrator"],
  "event_type": "task_updated",
  "task_id": "task_123",
  "data": {...},
  "timestamp": "2025-11-04T08:00:00Z",
  "adhd_metadata": {
    "cognitive_load": 0.6,
    "energy_required": "high"
  }
}
```

## Error Handling & Resilience

### Failure Modes
- **Network Issues**: Retry with exponential backoff
- **API Rate Limits**: Queue management and backoff
- **Data Conflicts**: Intelligent merge strategies
- **Agent Failures**: Fallback to alternative agents

### Monitoring
- **Sync Health**: Track success rates and latency
- **Error Rates**: Alert on elevated failure rates
- **Performance**: Response time monitoring
- **Resource Usage**: Memory and CPU tracking

## Security Considerations

### Authentication
- **API Keys**: Secure storage and rotation
- **User Sessions**: Proper session management
- **Access Control**: Role-based permissions

### Data Protection
- **Encryption**: Data at rest and in transit
- **Audit Logging**: All system actions tracked
- **Compliance**: GDPR and privacy protection

## Future Enhancements

### Advanced Features
- **Predictive Analytics**: ML-based task estimation
- **Collaborative Filtering**: Team preference learning
- **Real-time Collaboration**: Multi-user task coordination
- **Integration APIs**: Third-party tool connections

### Performance Optimizations
- **Edge Caching**: Reduce latency with global distribution
- **Batch Processing**: Optimize bulk operations
- **Async Operations**: Non-blocking task processing
- **Load Balancing**: Horizontal scaling support

## Conclusion

The PM Plane architecture provides a robust foundation for ADHD-optimized project management, seamlessly integrating human workflows with AI coordination while maintaining data consistency and user cognitive health. The two-plane design ensures clear separation of concerns while enabling sophisticated cross-system intelligence.