# ADR-003: Integrated Code Editor Implementation Strategy

**Status**: Accepted
**Date**: 2025-09-17
**Deciders**: Architecture Team, Development Experience Team
**Technical Story**: Selection of code editor implementation approach for integrated development environment

## Context

Dopemux requires an integrated code editor that operates within the terminal multiplexer environment while providing:

1. **AI Integration**: First-class support for AI coding assistants (Claude Code/Codex)
2. **Multi-file Operations**: Workspace-aware editing with symbol indexing
3. **Performance**: <50ms keystroke latency for ADHD accommodation
4. **Tree-sitter Integration**: Modern syntax highlighting and AST access
5. **Seamless Handoff**: Between editor, agents, and AI assistants

The editor must be a first-class citizen within Dopemux, not an external dependency that breaks the integrated workflow.

## Decision

We will **fork/embed Helix editor core with custom UI layer** for Dopemux integration.

### Implementation Approach:

```rust
struct DopemuxEditor {
    // Core editing (from Helix)
    buffers: Vec<Buffer>,
    syntax_trees: HashMap<BufferId, Tree>,  // Tree-sitter AST

    // AI Integration (custom)
    ai_suggestions: SuggestionOverlay,
    diff_preview: DiffRenderer,
    inline_chat: ChatWidget,

    // Multi-file awareness (custom)
    workspace: WorkspaceGraph,
    symbol_index: LSPSymbolCache,
}

enum EditorMode {
    Normal,
    Insert,
    Visual,
    AIAssist,    // New mode for AI interactions
    Diff,        // Review AI changes
    Chat,        // Inline chat with AI
}
```

### AI Integration Features:
- **Inline Suggestions**: AI-powered code completion and refactoring
- **Diff Preview**: Side-by-side review of AI-generated changes
- **Chat Integration**: Inline conversations with AI assistants
- **Context Awareness**: Automatic file and symbol context for AI

## Rationale

### Advantages of Helix Fork:

1. **Proven Architecture**:
   - Based on Kakoune design principles
   - Tree-sitter built-in for syntax and AST
   - Modern text editing foundation

2. **ADHD-Friendly Performance**:
   - Rust implementation for speed
   - 60fps smooth scrolling capability
   - <50ms keystroke latency achievable

3. **Extensibility**:
   - Clean separation of concerns
   - Plugin system for AI integration
   - Custom rendering layer possible

4. **Development Efficiency**:
   - Mature editing core
   - Focus on AI integration, not text editing basics
   - Strong community and documentation

### Trade-offs Accepted:

1. **Rust Codebase Maintenance**:
   - Requires Rust expertise on team
   - Fork maintenance overhead
   - **Mitigation**: Selective cherry-picking from upstream

2. **Kakoune-style Keybindings**:
   - Different from vim/emacs conventions
   - Learning curve for users
   - **Mitigation**: Progressive disclosure and customization

## Alternatives Considered

### Custom Mini-Editor (Rejected)
- **Pros**: Complete control, minimal footprint
- **Cons**: Significant development effort (6-12 months), reinventing solved problems
- **Verdict**: Resource allocation inefficient

### Xi-editor Backend (Rejected)
- **Pros**: Modern CRDT architecture, plugin system
- **Cons**: Project discontinued, no active maintenance
- **Verdict**: Too risky for production dependency

### Ropey + Custom UI (Rejected)
- **Pros**: Efficient rope data structure, flexible
- **Cons**: Must build all editor features from scratch
- **Verdict**: Similar issues to custom mini-editor

### External Editor Integration (Rejected)
- **Pros**: Leverage existing tools (vim, emacs, vscode)
- **Cons**: Breaks integrated workflow, context switching overhead
- **Verdict**: Conflicts with seamless AI integration goal

## Implementation Strategy

### Phase 1: Core Integration (Weeks 1-2)
- Fork Helix editor core
- Create Dopemux-specific rendering layer
- Implement basic buffer management
- Integrate with tmux layout system

### Phase 2: AI Integration (Weeks 3-4)
- Add AI suggestion overlay system
- Implement diff preview renderer
- Create inline chat widget
- Build context sharing with AI assistants

### Phase 3: Advanced Features (Weeks 5-6)
- Multi-file workspace awareness
- Symbol indexing and navigation
- Language server protocol integration
- Performance optimization

### Phase 4: ADHD Optimizations (Weeks 7-8)
- Attention management features
- Cognitive load indicators
- Distraction reduction
- Focus assistance tools

## Success Metrics

### Performance Targets:
- **Keystroke Latency**: <50ms for all operations
- **Scrolling**: 60fps smooth scrolling
- **Memory Usage**: <100MB for typical workspace
- **Startup Time**: <500ms to first render

### AI Integration Effectiveness:
- **Response Time**: <2s for AI suggestions
- **Context Accuracy**: >90% relevant context selection
- **User Adoption**: >80% use AI features regularly
- **Flow Preservation**: <200ms context switching

### ADHD Accommodation:
- **Focus Metrics**: Reduced context switching frequency
- **Cognitive Load**: Simplified interface complexity
- **Error Recovery**: Clear visual feedback for all operations

## Risks and Mitigations

### High Risk: Fork Maintenance Burden
- **Risk**: Keeping fork updated with Helix upstream
- **Probability**: High
- **Impact**: Medium (technical debt accumulation)
- **Mitigation**:
  - Selective cherry-picking strategy
  - Automated merge testing
  - Regular upstream evaluation

### Medium Risk: Rust Expertise Requirement
- **Risk**: Team lacks sufficient Rust knowledge
- **Probability**: Medium
- **Impact**: High (development velocity)
- **Mitigation**:
  - Rust training program
  - External Rust consultants
  - Gradual skill development

### Low Risk: User Keybinding Resistance
- **Risk**: Users reject Kakoune-style bindings
- **Probability**: Low
- **Impact**: Medium (adoption rates)
- **Mitigation**:
  - Customizable keybinding system
  - Migration guides from vim/emacs
  - Progressive disclosure of features

## Validation Approach

### Technical Validation:
1. **Performance Benchmarking**: Validate latency and throughput targets
2. **AI Integration Testing**: Confirm seamless context sharing
3. **Memory Profiling**: Ensure resource usage within limits
4. **Stress Testing**: Large files and complex workspaces

### User Validation:
1. **ADHD Developer Testing**: Focus and cognitive load measurement
2. **Workflow Efficiency**: Time-to-task completion metrics
3. **Feature Adoption**: Usage analytics for AI integration
4. **Satisfaction Surveys**: Regular user feedback collection

## Consequences

### Positive Consequences:
- **Integrated Development Experience**: Seamless AI-assisted coding
- **Performance Excellence**: ADHD-accommodated response times
- **Modern Foundation**: Tree-sitter and Rust advantages
- **Focused Development**: Effort on AI integration, not editor basics

### Negative Consequences:
- **Maintenance Overhead**: Fork management complexity
- **Learning Curve**: Kakoune-style interaction model
- **Resource Requirements**: Rust development expertise needed
- **Feature Parity Timeline**: Gradual achievement of full editor features

### Monitoring and Review:
- **Performance Review**: Weekly latency and memory monitoring
- **User Feedback**: Monthly developer satisfaction surveys
- **Technical Review**: Quarterly fork maintenance assessment
- **Strategy Review**: Semi-annual editor approach evaluation

---

**ADR Status**: Accepted and Implementation Ready
**Review Date**: 2025-12-17 (Quarterly Review)
**Implementation Priority**: Critical Path - Phase 1 Dependency