# ConPort System Documentation

ConPort is Dopemux's context portal and knowledge graph system for managing development context, session intelligence, and cross-component queries.

## Quick Links

- **[Executive Summary](CONPORT_EXECUTIVE_SUMMARY.md)** - High-level overview of all ConPort systems
- **[Integration Quickstart](CONPORT_INTEGRATION_QUICKSTART.md)** - Get started using ConPort
- **[Systems Analysis](CONPORT_SYSTEMS_ANALYSIS.md)** - Complete technical analysis

## Overview

You have **three interconnected ConPort systems**:

1. **ConPort-KG (Knowledge Graph)** - AGE-based graph database for deep context
2. **ConPort HTTP API** - RESTful API for programmatic access
3. **ConPort MCP** - Model Context Protocol integration for AI tools

## Documentation Index

### Getting Started
- [Integration Quickstart](CONPORT_INTEGRATION_QUICKSTART.md) - How to integrate ConPort into your workflow
- [ConPort README](CONPORT_README.md) - Main system documentation

### Architecture & Design
- [Executive Summary](CONPORT_EXECUTIVE_SUMMARY.md) - Three systems explained
- [Systems Analysis](CONPORT_SYSTEMS_ANALYSIS.md) - Deep technical dive
- [Comparison Matrix](CONPORT_COMPARISON_MATRIX.md) - Feature comparison
- [Deep Analysis](CONPORT_DEEP_ANALYSIS.md) - Detailed system analysis

### Implementation
- [Execution Plan](CONPORT_EXECUTION_PLAN.md) - Deployment and integration plan
- [Implementation Paths](CONPORT_IMPLEMENTATION_PATHS.md) - Development roadmap
- [KG Status](CONPORT_KG_STATUS.md) - Current knowledge graph state

## System Capabilities

### ConPort-KG (Knowledge Graph)
- Session and epic tracking
- Cross-component relationship mapping
- Pattern learning and insight generation
- Deep context queries

### ConPort HTTP API
- RESTful endpoints for all operations
- Session management
- Context retrieval
- Real-time updates

### ConPort MCP
- AI tool integration (Claude, Cursor, etc.)
- Natural language context queries
- Automated session tracking
- Intelligent suggestions

## Common Use Cases

### 1. Session Intelligence
Track work sessions, link to epics, analyze patterns.

### 2. Context Retrieval
Get relevant context for current work across components.

### 3. Cross-Component Queries
Find relationships between dashboard, ADHD engine, and orchestrator.

### 4. Pattern Learning
Identify productivity patterns, blockers, and opportunities.

## Integration Points

ConPort integrates with:
- **Dashboard** - Context display and session tracking
- **ADHD Engine (Serena)** - Break suggestions based on patterns
- **Task Orchestrator** - Epic and task management
- **MCP Servers** - AI tool access to context

## Related Documentation

- [ConPort MCP Queries](../../COMPONENT_5_CONPORT_MCP_QUERIES.md)
- [Integration Bridge](../../COMPONENT_3_INTEGRATION_BRIDGE_WIRING.md)
- [Architecture Overview](../../04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md)

## Development Status

✅ **ConPort-KG**: Production-ready, fully implemented  
✅ **ConPort HTTP API**: Complete, needs deployment  
✅ **ConPort MCP**: Integrated and functional

See [KG Status](CONPORT_KG_STATUS.md) for current state and roadmap.

---

**Maintained by:** Dopemux Core Team  
**Last Updated:** 2025-10-29
