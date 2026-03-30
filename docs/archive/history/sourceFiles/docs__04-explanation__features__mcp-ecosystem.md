# 🔌 MCP Server Ecosystem Hub

Central hub for understanding Dopemux's Model Context Protocol (MCP) integration, orchestration, and server ecosystem.

## Overview

The MCP ecosystem enables Dopemux to integrate with external services and tools through a standardized protocol. This hub consolidates all MCP-related documentation, specifications, and workflows.

## 🏗️ Architecture Documentation

### Core MCP Architecture
- [MCP Routing Matrix](../architecture/mcp/routing-matrix.md) - Request routing and orchestration patterns
- [Server Specifications](../architecture/mcp/server-specifications.md) - Technical specifications for MCP servers
- [Dynamic Discovery System](../architecture/mcp/dynamic-discovery.md) - Automatic server discovery and registration
- [Orchestration Roadmap](../architecture/mcp/orchestration-roadmap.md) - Future development plans

## 📖 Reference Documentation

### Technical References
- [MCP Tools Inventory](../../03-reference/mcp/tools-inventory.md) - Complete catalog of available MCP tools
- [Workflow Mapping](../../03-reference/mcp/workflow-mapping.md) - Tool-to-workflow mapping and triggers

## 🎯 Key Features

### Intelligent Orchestration
- **Dynamic Tool Selection**: Automatically selects appropriate MCP tools based on context
- **Token Optimization**: Keeps MCP tool usage under 10k tokens for efficiency
- **Workflow Automation**: Triggers tools automatically based on user actions

### Server Categories

#### Memory Management
- **ConPort**: Context portal for project memory and decision tracking
- **OpenMemory**: Cross-application memory persistence

#### Code Intelligence
- **Claude-Context**: Semantic code search and indexing
- **Morphllm**: Pattern-aware code editing
- **Desktop Commander**: Comprehensive desktop automation

#### Research & Documentation
- **Exa**: Advanced web research and company analysis
- **Context7**: Official library documentation retrieval

#### AI Coordination
- **MAS Sequential Thinking**: Multi-agent reasoning coordination
- **Task-Master AI**: ADHD-optimized task decomposition

## 🧠 ADHD Optimizations

### Cognitive Load Reduction
- Automatic tool selection reduces decision fatigue
- Context preservation across tool invocations
- Progress tracking through ConPort integration

### Focus Support
- Tools triggered based on attention state
- Minimal context switching between tools
- Clear feedback on tool execution

## 🔧 Configuration

### Server Management
```bash
# Install MCP servers
dopemux mcp install <server-name>

# List available servers
dopemux mcp list

# Check server health
dopemux mcp health
```

### Docker Integration
MCP servers can run in Docker containers for isolation:
```yaml
services:
  mcp-server:
    image: mcp/<server-name>:latest
    environment:
      - API_KEY=${API_KEY}
```

## 📊 Performance Metrics

### Token Usage
- Current MCP tools: ~7,400 tokens (3.7% of context)
- Recommended additions: ~6,300 tokens
- Target: Keep total under 10k tokens (5% of context)

### Response Times
- Tool discovery: <100ms
- Tool invocation: 200-500ms average
- Context retrieval: <1s for most operations

## 🚀 Getting Started

1. **Essential Setup**: Install ConPort for memory management
2. **Index Codebase**: Enable claude-context for code search
3. **Configure Servers**: Set up API keys and credentials
4. **Test Integration**: Verify server connectivity

## 🔗 Related Documentation

- [Claude Integration Hub](claude-integration.md) - AI development workflow
- [Task Management Hub](task-management.md) - Task decomposition and tracking
- [Health Monitoring Hub](health-monitoring.md) - System reliability

## 🛠️ Troubleshooting

### Common Issues
- **Server not responding**: Check Docker container status
- **Token limit exceeded**: Review server configuration
- **Tool not found**: Verify server installation

### Debug Commands
```bash
# Check MCP server logs
dopemux mcp logs <server-name>

# Reset server connection
dopemux mcp restart <server-name>

# View server configuration
dopemux mcp config <server-name>
```

---

*The MCP ecosystem is central to Dopemux's extensibility and integration capabilities, providing a standardized way to connect with external services while maintaining ADHD-friendly workflows.*