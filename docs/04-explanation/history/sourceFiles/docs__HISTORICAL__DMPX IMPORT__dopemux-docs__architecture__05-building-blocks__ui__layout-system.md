# UI Layout System Architecture

## Overview

The Dopemux layout system provides a flexible, terminal-native interface supporting multiple workflow types through adaptive pane arrangements and modal interactions.

## Layout Components

### Pane Types

```rust
enum PaneContent {
    Editor(EditorState),
    AIAssistant(AssistantType),
    Terminal(ShellSession),
    Monitor(MetricsDashboard),
    Flow(WorkflowEngine),
    Chat(ChannelList),
    FileTree(DirectoryBrowser),
    AgentStatus(AgentMonitor),
}

struct PaneConfig {
    content: PaneContent,
    size: Size,
    position: Position,
    shortcuts: Vec<Keybind>,
    resizable: bool,
    closable: bool,
}

enum Size {
    Fixed(u16),
    Percentage(f32),
    Remaining,
    MinMax(u16, u16),
}
```

### Layout Presets

#### 1. Development Layout
```
┌────────────────────────────────────────────────────────────────┐
│ [Sessions] [Agents] [Monitor] [Flow] [Chat]  | ⚡ CPU: 42% 🔥 3 │
├────────────┬──────────────────────────────┬─────────────────────┤
│            │                              │  📁 Files          │
│  Editor    │     Claude Code Window       │  ├─ src/           │
│            │  ┌────────────────────────┐  │  │  ├─ main.rs    │
│  main.rs   │  │ Q: Refactor this func  │  │  │  └─ lib.rs     │
│  ┌───────┐ │  │ A: I'll help you...    │  │  └─ tests/        │
│  │fn main│ │  │ ```rust                │  │                    │
│  │  ...  │ │  │ fn improved() { ... }  │  │  🤖 Active Agents  │
│  └───────┘ │  │ ```                    │  │  ├─ CodeGen-1 ✓   │
│            │  └────────────────────────┘  │  ├─ Tester-2  ⟳   │
│            │                              │  └─ Reviewer-3 ⟳  │
├────────────┼──────────────────────────────┼─────────────────────┤
│ Terminal 1 │        ClaudeFlow           │  💬 Team Chat      │
│ $ cargo run│   [Parse]→[Build]→[Test]    │  alice: deployed   │
│            │     ✓      ⟳      ✗         │  bob: LGTM         │
└────────────┴──────────────────────────────┴─────────────────────┘
```

#### 2. Review Layout
```
┌──────────────────────────────────────────────────────────┐
│ Review Mode | PR #123 | Files: 15 | +234 -67           │
├──────────────────────┬───────────────────────────────────┤
│                      │                                   │
│    Original Code     │       Proposed Changes           │
│                      │                                   │
│ fn calculate_tax() { │ fn calculate_tax() {              │
│   // old impl        │   // improved implementation      │
│   ...                │   ...                             │
│ }                    │ }                                 │
│                      │                                   │
├──────────────────────┴───────────────────────────────────┤
│ 💬 Comments & Suggestions                                │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 🤖 AI Review: This change improves performance... │ │
│ │ 👤 Human: LGTM, please add tests                 │ │
│ └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

#### 3. Monitoring Layout
```
┌──────────────────────────────────────────────────────────┐
│ System Status | All Services Operational | 🟢          │
├────────────┬────────────┬────────────┬─────────────────┤
│   CPU      │   Memory   │  Network   │    Alerts       │
│ ████░░ 73% │ ███░░░ 45% │ ▲ 1.2MB/s  │ 🟡 High CPU     │
│            │            │ ▼ 0.8MB/s  │ 🟢 All OK       │
├────────────┴────────────┴────────────┼─────────────────┤
│        Agent Performance              │  Recent Logs    │
│ ┌──────────────────────────────────┐ │ 12:34 INFO: ... │
│ │ Agent-1: ████████░░ 84% success │ │ 12:35 WARN: ... │
│ │ Agent-2: ██████░░░░ 67% success │ │ 12:36 ERROR: ..│
│ │ Agent-3: ██████████ 95% success │ │                 │
│ └──────────────────────────────────┘ │                 │
└────────────────────────────────────────┴─────────────────┘
```

#### 4. Orchestration Layout
```
┌──────────────────────────────────────────────────────────┐
│ ClaudeFlow Studio | Pipeline: code-review-v3            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [📥 PR] ──> [🔍 Scan] ──> [🤖 Review] ──> [✅ Approve]    │
│       │                        │                         │
│       └──> [🧪 Test] ─────────┘                         │
│                                                          │
│  Status: 🟡 Running | Stage: Security Scan | 2/4 Complete│
├──────────────────────────────────────────────────────────┤
│ Pipeline Library     │ Execution Logs        │ Controls │
│ • Code Review        │ 12:34 Starting scan   │ ⏸️ Pause  │
│ • Deployment         │ 12:35 Found 3 issues  │ ⏹️ Stop   │
│ • Testing            │ 12:36 Review agent... │ ⏭️ Skip   │
└──────────────────────┴───────────────────────┴──────────┘
```

## Adaptive Layout Engine

### Layout Rules

```rust
struct LayoutEngine {
    rules: Vec<LayoutRule>,
    constraints: LayoutConstraints,
    preferences: UserPreferences,
}

struct LayoutRule {
    condition: LayoutCondition,
    action: LayoutAction,
    priority: u8,
}

enum LayoutCondition {
    TerminalSize(u16, u16),
    PaneCount(usize),
    ContentType(PaneContent),
    UserMode(WorkflowMode),
    TimeOfDay(TimeRange),
}

enum LayoutAction {
    ResizePane(PaneId, Size),
    MovePanePanel(PaneId, Position),
    HidePane(PaneId),
    ShowPane(PaneId),
    SwitchPreset(LayoutPreset),
}
```

### Responsive Behavior

```yaml
layout_breakpoints:
  small_terminal:  # < 80x24
    - hide_secondary_panes: true
    - minimize_status_bars: true
    - single_focus_mode: true

  medium_terminal:  # 80x24 to 120x40
    - limit_panes: 4
    - stack_vertically: true
    - compact_mode: true

  large_terminal:  # > 120x40
    - full_layout: true
    - side_panels: true
    - rich_status: true
```

### Focus Management

```rust
enum FocusMode {
    Normal,          // All panes visible
    Focused(PaneId), // One pane highlighted, others dimmed
    Maximized(PaneId), // One pane full-screen
    Split(Vec<PaneId>), // Specific panes only
}

struct FocusManager {
    current_mode: FocusMode,
    focus_stack: Vec<PaneId>,
    attention_tracking: AttentionMetrics,
}

impl FocusManager {
    fn enter_focus_mode(&mut self, pane: PaneId) {
        self.dim_other_panes();
        self.highlight_pane(pane);
        self.track_focus_change();
    }

    fn smart_focus_suggestion(&self) -> Option<PaneId> {
        // AI-powered focus recommendations based on:
        // - Current task context
        // - Historical attention patterns
        // - Workflow stage
        // - ADHD accommodation needs
    }
}
```

## Keyboard Navigation

### Modal Navigation System

```yaml
navigation_modes:
  normal_mode:
    prefix: "Ctrl+Space"
    bindings:
      h/j/k/l: move_focus
      o: open_command_palette
      p: switch_to_project_mode
      f: switch_to_file_mode
      a: switch_to_agent_mode

  command_mode:
    trigger: ":"
    autocomplete: true
    history: true
    examples:
      - "layout dev"
      - "focus editor"
      - "split vertical"

  quick_access:
    bindings:
      F1: help
      F2: file_tree
      F3: agent_status
      F4: terminal
      F5: refresh
```

### Keybinding Layers

```rust
struct KeybindingLayer {
    name: String,
    active: bool,
    bindings: HashMap<KeyCombination, Action>,
    conditions: Vec<ActivationCondition>,
}

enum ActivationCondition {
    PaneType(PaneContent),
    Mode(OperationMode),
    Context(ContextType),
    TimeRange(Duration),
}

// Example layers:
// - Global: Always active
// - Editor: Active when editor pane focused
// - AI: Active during AI interactions
// - Flow: Active in workflow builder
// - ADHD: Attention management shortcuts
```

## ADHD-Specific Adaptations

### Attention Management

```rust
struct AttentionSupport {
    distraction_shield: bool,
    focus_timer: Option<Duration>,
    break_reminders: bool,
    context_preservation: bool,
}

enum AttentionMode {
    Deep,       // Minimal distractions, single focus
    Scanning,   // Multiple panes, quick navigation
    Break,      // Rest mode, limited interactions
    Transition, // Gentle mode switching
}
```

### Visual Accommodations

```yaml
adhd_visual_support:
  reduced_clutter:
    - hide_non_essential_ui: true
    - minimize_status_text: true
    - simplify_borders: true

  attention_guidance:
    - highlight_active_area: true
    - dim_inactive_panes: true
    - progress_indicators: prominent

  cognitive_load_management:
    - limit_simultaneous_tasks: 3
    - clear_completion_signals: true
    - gentle_transitions: true
```

## Implementation Strategy

### Core Layout Components

1. **Pane Manager**: Core pane lifecycle and arrangement
2. **Layout Engine**: Rule-based adaptive layouts
3. **Focus Manager**: Attention and navigation control
4. **Keybinding System**: Modal and contextual shortcuts
5. **Theme Engine**: Visual styling and ADHD accommodations

### Integration Points

- **Terminal Detection**: Capabilities and size adaptation
- **User Preferences**: Saved layouts and customizations
- **Context Awareness**: Task-specific layout suggestions
- **Performance Monitoring**: Layout impact on system resources

### Quality Targets

- **Response Time**: <50ms for all layout operations
- **Memory Usage**: <20MB for layout system overhead
- **Customization**: 100% user-configurable layouts
- **Accessibility**: Full keyboard navigation support