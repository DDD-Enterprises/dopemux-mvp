# ADR-006: MCP Server Selection and Priority

## Status
**Accepted** - Selected zen-mcp as primary orchestrator with complementary MCP servers

## Context

Dopemux requires integration with multiple AI models, specialized tools, and external services through the Model Context Protocol (MCP). The selection of MCP servers directly impacts:

- Multi-model AI orchestration capabilities
- Development tool integration (LSP, documentation, UI generation)
- System reliability and performance
- ADHD accommodation effectiveness through optimized tool routing

## Decision

**Primary MCP Server**: zen-mcp for multi-model orchestration
**Supporting MCP Stack**:
- **context7**: Official library documentation and framework patterns
- **serena**: LSP functionality and semantic code operations
- **sequential-thinking**: Structured reasoning for complex analysis
- **morphllm-fast-apply**: Pattern-based code transformations
- **magic**: UI component generation with 21st.dev patterns
- **playwright**: Browser automation and E2E testing

## Rationale

### zen-mcp as Primary Orchestrator
- **Multi-Model Coordination**: Orchestrates Claude, Gemini Pro, OpenAI O3, and Grok models with stateful conversation threading
- **Redis-Backed Persistence**: Maintains conversation context across sessions (ADHD requirement)
- **Specialized Tools**: 14 tools including chat, thinkdeep, planner, consensus, debug, precommit, codereview
- **Model-Specific Routing**:
  - Gemini Pro: 1M token context for large-scale analysis
  - O3: 200K tokens for logical debugging and reasoning
  - Claude: Balanced performance for general development
  - Grok: Alternative perspective for consensus building

### MCP Server Priority Matrix
```yaml
Priority_1_Critical:
  zen-mcp: "Multi-model orchestration, consensus building"
  context7: "Official documentation lookup (MANDATORY before any coding)"

Priority_2_Core:
  serena: "LSP operations, symbol management, project memory"
  sequential-thinking: "Complex reasoning, debugging, analysis"

Priority_3_Enhancement:
  morphllm-fast-apply: "Bulk edits, pattern transformations"
  magic: "UI component generation"
  playwright: "Browser testing, accessibility validation"
```

### Tool Selection Decision Flow
1. **context7 FIRST** - Always check official documentation before coding
2. **zen-mcp** - For complex decisions requiring multiple AI perspectives
3. **sequential-thinking** - For structured reasoning and debugging
4. **serena** - For semantic code operations and project context
5. **specialized tools** - morphllm/magic/playwright for specific tasks

## Implementation

### zen-mcp Configuration
```yaml
models:
  primary: claude-3.5-sonnet
  reasoning: openai-o3
  context: gemini-pro
  alternative: grok

tools_enabled:
  - chat
  - thinkdeep
  - planner
  - consensus
  - debug
  - precommit
  - codereview

tools_disabled:
  - analyze      # Enable when needed
  - refactor     # Enable when needed
  - testgen      # Enable when needed
  - secaudit     # Enable when needed
  - docgen       # Enable when needed
```

### MCP Integration Architecture
```
Dopemux Hub
├── zen-mcp (Primary Orchestrator)
│   ├── Redis Context Store
│   ├── Model Router (Claude/Gemini/O3/Grok)
│   └── Conversation Threading
├── context7 (Documentation)
│   ├── Framework Patterns
│   ├── Library APIs
│   └── Best Practices
├── serena (Code Operations)
│   ├── LSP Integration
│   ├── Symbol Operations
│   └── Project Memory
└── Specialized Tools
    ├── sequential-thinking (Analysis)
    ├── morphllm (Transformations)
    ├── magic (UI Generation)
    └── playwright (Testing)
```

### ADHD Optimization Through MCP
- **Context Preservation**: Redis-backed zen-mcp maintains session state
- **Cognitive Load Reduction**: context7 eliminates documentation search overhead
- **Attention Management**: zen-mcp consensus prevents decision paralysis
- **Task Routing**: Automatic tool selection based on request type

## Consequences

### Positive
- **Multi-Model Intelligence**: Leverages strengths of different AI models
- **Documentation-Driven Development**: context7 ensures adherence to official patterns
- **Persistent Context**: Redis storage prevents context loss (critical for ADHD)
- **Specialized Capabilities**: Each MCP server optimized for specific tasks
- **Quality Assurance**: Built-in precommit and code review workflows

### Negative
- **Complexity**: Multiple MCP servers require coordination
- **Dependencies**: Failure of zen-mcp impacts entire orchestration
- **Resource Usage**: Multiple models consume more compute resources
- **Learning Curve**: Developers must understand tool selection priorities

### Risks and Mitigations
- **zen-mcp Unavailability**: Fallback to direct Claude integration
- **Redis Failure**: Local SQLite backup for context storage
- **Model API Limits**: Round-robin model selection for load balancing
- **MCP Server Conflicts**: Clear priority hierarchy and tool routing

## Related Decisions
- **ADR-001**: Hub-and-spoke architecture enables MCP integration
- **ADR-005**: Letta Framework complements zen-mcp for memory management
- **Future ADR-007**: Task management integration strategy
- **Future ADR-008**: Routing logic for tool selection

## References
- zen-mcp research: `/research/findings/superclaude and zen-mcp research.md`
- MCP Protocol specification: [Model Context Protocol](https://modelcontextprotocol.io/)
- Tool integration patterns: `/research/integrations/`