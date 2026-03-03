# Dopemux System Architecture

## Overview

Dopemux implements a **hub-and-spoke architecture** with a central orchestrator managing specialized subsystems. This design ensures scalability, maintainability, and comprehensive ADHD accommodations while supporting complex multi-agent AI coordination.

## Core Architecture Pattern

```yaml
Architecture_Pattern: Hub-and-Spoke
Central_Hub: Core Orchestrator (Node.js + tmux)
Spoke_Services:
  - Integrated Editor (Rust/Helix fork)
  - AI Assistant Windows (Ratatui)
  - ClaudeFlow UI (ASCII Art)
  - Memory Manager (Letta Framework)
  - Task Synchronizer (MCP)
  - Agent Router (Multi-provider)
```

## System Context

The Dopemux platform operates within a broader ecosystem of development and productivity tools:

### Primary Users
- **ADHD Developers**: Neurodivergent software developers requiring specialized accommodations
- **Team Leads**: Development managers overseeing projects and team coordination
- **Enterprise Admins**: Organization administrators managing development platforms

### External Integrations
- **AI Systems**: Claude Code, Claude-flow (64-agent orchestration), Letta Framework
- **Project Management**: Leantime PM, task management systems
- **Development Tools**: Git providers, CI/CD systems, monitoring platforms
- **Productivity**: Calendar systems, communication tools, life automation

## Container Architecture

### Core Orchestrator
**Technology**: Node.js with tmux integration
**Responsibilities**:
- Session lifecycle management
- Component coordination and routing
- ADHD accommodation orchestration
- Performance monitoring and optimization

### Integrated Editor
**Technology**: Rust (Helix fork with custom AI integration)
**Key Features**:
- Tree-sitter AST integration
- AI-powered code suggestions
- Diff preview and application
- Context-aware symbol navigation

### AI Assistant Windows
**Technology**: Ratatui terminal UI framework
**Components**:
- Chat interface for AI interactions
- Diff preview and merge tools
- Code generation and explanation
- Context management panels

### ClaudeFlow UI
**Technology**: ASCII art visualization with Ratatui
**Capabilities**:
- Visual workflow representation
- Pipeline execution monitoring
- Agent status and coordination
- Real-time progress tracking

### Memory Manager
**Technology**: Letta Framework client
**Functions**:
- Session state persistence
- Context preservation across interruptions
- Cross-session learning and adaptation
- Memory block management

### Task Synchronizer
**Technology**: MCP (Model Context Protocol) client
**Integration**:
- Bidirectional sync with Leantime PM
- Claude-Task-Master coordination
- Project milestone tracking
- ADHD-optimized task decomposition

### Agent Router
**Technology**: Multi-provider MCP orchestration
**Routing Logic**:
- zen-mcp for multi-model coordination
- context7 for documentation lookup
- serena for semantic code operations
- Provider-agnostic fallback strategies

## Hub-and-Spoke Benefits

### Scalability
- **Independent Scaling**: Each spoke service scales based on demand
- **Resource Optimization**: Allocate resources where needed most
- **Load Distribution**: Distribute workload across specialized components

### Maintainability
- **Service Isolation**: Changes to one service don't affect others
- **Technology Diversity**: Each service uses optimal technology stack
- **Clear Boundaries**: Well-defined interfaces and responsibilities

### ADHD Accommodations
- **Attention Management**: Central orchestration prevents cognitive overload
- **Context Preservation**: Unified state management across all components
- **Graceful Degradation**: System continues functioning if individual services fail

## Communication Patterns

### Message Routing
```typescript
interface MessageRoute {
  source: ComponentId;
  destination: ComponentId;
  messageType: MessageType;
  payload: any;
  priority: 'low' | 'medium' | 'high' | 'adhd_critical';
  maxLatency: number; // milliseconds
}

// ADHD-critical operations must complete within 50ms
const ADHD_CRITICAL_LATENCY = 50;
```

### Event-Driven Architecture
- **Asynchronous Processing**: Non-blocking operations for responsive UI
- **Event Sourcing**: Complete audit trail for debugging and learning
- **Pub/Sub Patterns**: Loose coupling between components

## Quality Attributes

### Performance Targets
- **ADHD-Critical Operations**: <50ms latency
- **AI Response Streaming**: <200ms per chunk
- **Context Restoration**: <500ms
- **System Startup**: <2s to ready state

### Reliability Requirements
- **Availability**: 99.9% uptime
- **Fault Tolerance**: Graceful degradation on component failure
- **Recovery**: <30 seconds MTTR for critical components
- **Data Integrity**: Zero session data loss

### Security Considerations
- **Authentication**: OAuth 2.0 with JWT tokens
- **Authorization**: Role-based access control
- **Data Protection**: AES-256 encryption at rest
- **Network Security**: TLS 1.3 for all communications

## Technology Stack

### Backend Services
```yaml
Languages:
  - Node.js: Core orchestration and coordination
  - Rust: Editor implementation for performance
  - Python: AI integration and memory management

Frameworks:
  - tmux: Session and window management
  - Ratatui: Terminal UI components
  - Letta: Memory and context management

Protocols:
  - MCP: Model Context Protocol for AI services
  - JSON-RPC: Inter-service communication
  - WebSocket: Real-time updates
```

### Storage Systems
```yaml
Primary_Storage:
  - SQLite: Local session and configuration data
  - Redis: High-performance caching and pub/sub

External_Storage:
  - Letta: Persistent memory blocks
  - PostgreSQL: Enterprise data (optional)
  - File System: Project files and artifacts
```

## Deployment Architecture

### Local Development
- Single-user deployment
- All services on localhost
- SQLite for data persistence
- Direct file system access

### Team Deployment
- Multi-user support
- Shared Redis cache
- PostgreSQL for team data
- Container orchestration

### Enterprise Deployment
- Kubernetes-native scaling
- Multi-tenant isolation
- Enterprise authentication
- Compliance and auditing

## ADHD-Specific Optimizations

### Architecture-Level Accommodations
- **Low-Latency Design**: Sub-50ms response times for attention preservation
- **Context Preservation**: Automatic state saving and restoration
- **Graceful Interruption**: Support for task switching without data loss
- **Predictable Behavior**: Consistent response patterns to reduce cognitive load

### Memory-Friendly Patterns
- **External Memory**: Persistent context and decision history
- **Progressive Disclosure**: Show information in digestible chunks
- **Visual Hierarchy**: Clear information organization and prioritization
- **Attention Guidance**: UI elements guide focus to important items

## Future Architecture Evolution

### Planned Enhancements
- **Custom Agent Framework**: Gradual migration from Claude-flow
- **Advanced Memory Tiers**: Hierarchical memory optimization
- **Enhanced Visualization**: 3D terminal interfaces
- **AI Model Integration**: Support for emerging AI capabilities

### Scalability Roadmap
- **Phase 1**: Single-user optimization (Weeks 1-8)
- **Phase 2**: Multi-user support (Weeks 9-16)
- **Phase 3**: Enterprise features (Weeks 17-24)
- **Phase 4**: Advanced AI integration (Weeks 25-32)

This architecture provides a solid foundation for the world's first comprehensively ADHD-accommodated development platform while maintaining enterprise-grade scalability and reliability.