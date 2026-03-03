# ADR-004: Visual Workflow UI in Terminal Environment

**Status**: Accepted
**Date**: 2025-09-17
**Deciders**: Architecture Team, UX Team, ADHD Advisory Board
**Technical Story**: Implementation strategy for visual workflow representation in terminal multiplexer

## Context

ClaudeFlow orchestration requires visual workflow representation to support:

1. **Pipeline Building**: Drag & drop node-based workflow creation
2. **Execution Monitoring**: Real-time status and progress visualization
3. **Debugging**: Visual inspection of workflow state and data flow
4. **ADHD Accommodation**: Visual processing aids for neurodivergent users
5. **Terminal Constraints**: Must work within terminal character grid limitations

The challenge is providing sophisticated visual programming capabilities while maintaining terminal-native operation and accessibility.

## Decision

We will implement **ASCII Art Pipeline Visualization with Terminal-Native Interaction** for ClaudeFlow workflow UI.

### Visual Representation:

```
┌─────────────────── ClaudeFlow Pipeline ───────────────────┐
│                                                            │
│  [📥 Input] ──> [🤖 Agent-1] ──> [⚙️ Process] ──> [✅ Output] │
│       │             │              │                       │
│       └──────> [🤖 Agent-2] ──────┘                       │
│                                                            │
│  Status: ● Running  | Progress: ████████░░ 75%           │
└────────────────────────────────────────────────────────────┘
```

### Interaction Model:

```yaml
Input Methods:
  Keyboard Navigation:
    - hjkl: Move between nodes
    - Enter: Select/edit node
    - Tab: Cycle through properties
    - Space: Toggle node state

  Mouse Support (where available):
    - Click: Select nodes
    - Drag: Reposition nodes (terminal grid-aligned)
    - Scroll: Pan large workflows

  Command Palette:
    - /add-node: Add new workflow node
    - /connect: Create node connections
    - /template: Load workflow templates
```

## Rationale

### Advantages of ASCII Art Approach:

1. **Terminal Native**:
   - No external dependencies or GUI frameworks
   - Works in SSH, tmux, screen environments
   - Consistent with Dopemux terminal-first philosophy

2. **ADHD-Friendly Visual Processing**:
   - Clear visual hierarchy with boxes and connections
   - Color coding for status and node types
   - Reduced cognitive load vs text-only representation

3. **Accessibility**:
   - Screen reader compatible
   - High contrast terminal-friendly
   - Keyboard-only operation possible

4. **Development Efficiency**:
   - Leverage existing terminal UI libraries (Ratatui)
   - No complex graphics engine required
   - Rapid prototyping and iteration

### Trade-offs Accepted:

1. **Visual Complexity Limitations**:
   - Cannot achieve GUI-level visual sophistication
   - Grid-aligned positioning constraints
   - **Mitigation**: Progressive disclosure, zooming/panning

2. **Terminal Size Dependencies**:
   - Large workflows may not fit on small terminals
   - **Mitigation**: Scrolling, minimap, focus modes

3. **Mouse Support Variability**:
   - Not all terminals support mouse well
   - **Mitigation**: Full keyboard accessibility

## Implementation Components

### 1. Node Types and Visualization

```rust
enum NodeType {
    Input,      // 📥 Data input source
    Agent,      // 🤖 AI agent processing
    Tool,       // 🔧 External tool execution
    Decision,   // ❓ Conditional branching
    Loop,       // 🔄 Iterative processing
    Output,     // ✅ Result destination
    Error,      // ❌ Error handling
}

struct VisualNode {
    id: NodeId,
    node_type: NodeType,
    position: (u16, u16),  // Terminal grid coordinates
    size: (u16, u16),      // Width, height in characters
    status: NodeStatus,
    connections: Vec<ConnectionId>,
}

enum NodeStatus {
    Idle,        // ⚪ Not started
    Running,     // 🟡 In progress
    Success,     // 🟢 Completed successfully
    Error,       // 🔴 Failed
    Waiting,     // 🔵 Waiting for dependencies
}
```

### 2. Layout and Rendering Engine

```rust
struct WorkflowRenderer {
    canvas: TerminalCanvas,
    viewport: Rectangle,
    zoom_level: f32,
    grid_size: (u16, u16),
}

impl WorkflowRenderer {
    fn render_node(&mut self, node: &VisualNode) {
        let symbol = match node.node_type {
            NodeType::Input => "📥",
            NodeType::Agent => "🤖",
            NodeType::Tool => "🔧",
            // ... etc
        };

        self.draw_box(node.position, node.size, symbol);
        self.draw_status_indicator(node.status);
        self.draw_connections(node.connections);
    }

    fn handle_interaction(&mut self, event: InputEvent) {
        match event {
            KeyPress(Key::Char('h')) => self.move_selection(-1, 0),
            KeyPress(Key::Char('j')) => self.move_selection(0, 1),
            MouseClick(x, y) => self.select_node_at(x, y),
            // ... etc
        }
    }
}
```

### 3. Template and Preset System

```yaml
workflow_templates:
  code_review:
    name: "Code Review Pipeline"
    nodes:
      - type: input
        id: "pr_input"
        position: [2, 4]

      - type: agent
        id: "security_scan"
        agent: "security-engineer"
        position: [8, 2]

      - type: agent
        id: "quality_check"
        agent: "quality-engineer"
        position: [8, 6]

      - type: decision
        id: "approval_gate"
        condition: "security_scan.success && quality_check.success"
        position: [16, 4]

    connections:
      - from: "pr_input"
        to: ["security_scan", "quality_check"]
      - from: ["security_scan", "quality_check"]
        to: "approval_gate"
```

## Alternatives Considered

### Web-based GUI Dashboard (Rejected)
- **Pros**: Rich visual capabilities, modern UX patterns
- **Cons**: Breaks terminal-native workflow, requires browser dependency
- **Verdict**: Conflicts with integrated development philosophy

### PlantUML/Graphviz Integration (Rejected)
- **Pros**: Powerful diagram generation, text-based source
- **Cons**: Static output, no interactive editing, external dependencies
- **Verdict**: Lacks real-time interaction requirements

### Simple Text Lists (Rejected)
- **Pros**: Minimal implementation, universal compatibility
- **Cons**: Poor visual processing for ADHD users, difficult to understand complex flows
- **Verdict**: Fails ADHD accommodation requirements

### ncurses Complex UI (Rejected)
- **Pros**: Rich terminal UI capabilities
- **Cons**: Platform compatibility issues, complex implementation
- **Verdict**: Ratatui provides better cross-platform support

## Implementation Strategy

### Phase 1: Basic Visualization (Weeks 1-2)
- ASCII art node rendering
- Simple keyboard navigation
- Static workflow display
- Basic connection visualization

### Phase 2: Interactive Editing (Weeks 3-4)
- Node addition/removal
- Connection creation/editing
- Property panel for node configuration
- Template loading system

### Phase 3: Execution Integration (Weeks 5-6)
- Real-time status updates
- Progress indicators
- Log streaming integration
- Error highlighting

### Phase 4: Advanced Features (Weeks 7-8)
- Workflow templates and presets
- Import/export capabilities
- Collaborative editing support
- Performance optimization

## Success Metrics

### Usability Targets:
- **Learning Curve**: <30 minutes to create first workflow
- **Navigation Speed**: <3 keystrokes to reach any node
- **Visual Clarity**: >90% user comprehension of workflow state
- **ADHD Effectiveness**: Reduced cognitive load vs text-only

### Performance Targets:
- **Rendering Speed**: <100ms full workflow redraw
- **Responsiveness**: <50ms input reaction time
- **Memory Usage**: <50MB for complex workflows
- **Terminal Compatibility**: 95% across common terminals

### Feature Adoption:
- **Template Usage**: >70% use workflow templates
- **Interactive Editing**: >80% create workflows visually
- **Real-time Monitoring**: >90% use execution visualization

## Risks and Mitigations

### High Risk: Terminal Size Limitations
- **Risk**: Complex workflows don't fit on small screens
- **Probability**: High
- **Impact**: Medium (usability issues)
- **Mitigation**:
  - Scrolling and panning support
  - Minimap for large workflows
  - Focus mode for specific sections
  - Responsive layout adaptation

### Medium Risk: Unicode Compatibility
- **Risk**: Emoji and special characters don't render correctly
- **Probability**: Medium
- **Impact**: Low (visual consistency)
- **Mitigation**:
  - Fallback ASCII character set
  - Terminal capability detection
  - User-configurable symbol sets

### Low Risk: Mouse Support Inconsistency
- **Risk**: Mouse interaction varies across terminals
- **Probability**: Low
- **Impact**: Low (alternative keyboard navigation)
- **Mitigation**:
  - Keyboard-first design
  - Mouse as enhancement, not requirement
  - Clear keyboard shortcut documentation

## Validation Approach

### Technical Validation:
1. **Cross-terminal Testing**: Validate across major terminal emulators
2. **Performance Profiling**: Measure rendering and interaction speeds
3. **Unicode Testing**: Verify character rendering compatibility
4. **Workflow Complexity**: Test with large, complex pipelines

### User Validation:
1. **ADHD Developer Testing**: Cognitive load assessment
2. **Workflow Creation**: Time-to-completion for common tasks
3. **Visual Comprehension**: Understanding of workflow state
4. **Accessibility Testing**: Screen reader and keyboard-only usage

## Consequences

### Positive Consequences:
- **Terminal-Native Workflow Management**: Integrated visual programming
- **ADHD Accommodation**: Visual processing aids for complex workflows
- **Universal Accessibility**: Works in all terminal environments
- **Development Efficiency**: Faster workflow creation and debugging

### Negative Consequences:
- **Visual Limitations**: Cannot match GUI sophistication
- **Terminal Dependencies**: Rendering quality varies by terminal
- **Learning Curve**: New interaction paradigm for users
- **Implementation Complexity**: Custom rendering engine required

### Monitoring and Review:
- **Usage Analytics**: Track feature adoption and user patterns
- **Performance Monitoring**: Continuous rendering performance assessment
- **User Feedback**: Regular surveys on visual workflow effectiveness
- **Technical Review**: Quarterly evaluation of rendering improvements

---

**ADR Status**: Accepted and Implementation Ready
**Review Date**: 2025-12-17 (Quarterly Review)
**Implementation Priority**: High - Core UX Feature