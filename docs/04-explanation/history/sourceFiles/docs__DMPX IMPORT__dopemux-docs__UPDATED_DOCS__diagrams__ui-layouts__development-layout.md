# Development Layout - Primary Coding Interface

## Full Terminal Layout

```
┌──────────────────────────────────────────────────────────────────┐
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

## Pane Specifications

### Top Status Bar
- **Width**: 100% terminal width
- **Height**: 1 line
- **Content**: Tab navigation + system metrics
- **Shortcuts**: `Ctrl+1-5` for tab switching

### Left Column - Editor (40% width)
- **Content**: Helix-based code editor
- **Features**:
  - Tree-sitter syntax highlighting
  - AI suggestion overlays
  - Multi-file buffer management
- **Shortcuts**:
  - `Ctrl+Space` - AI assist mode
  - `Ctrl+D` - Show diff preview

### Center Column - AI Assistant (35% width)
- **Top Half**: Claude Code chat window
  - Real-time conversation
  - Code block rendering
  - Token usage display
- **Bottom Half**: ClaudeFlow workflow
  - ASCII pipeline visualization
  - Real-time status updates
  - Progress indicators

### Right Column - Context Panel (25% width)
- **Top Half**: File tree browser
  - Project file navigation
  - Git status indicators
  - Quick file switching
- **Bottom Half**: Agent status
  - Active agent monitoring
  - Task queue display
  - Performance metrics

### Bottom Row - Terminal & Chat
- **Left**: Terminal session
  - Shell command execution
  - Build/test output
  - Git operations
- **Right**: Team communication
  - Channel messages
  - Notifications
  - Status updates

## Responsive Breakpoints

### Small Terminal (< 80x24)
```
┌─────────────────────────────────┐
│ [Editor] [AI] [Term] | CPU: 42%│
├─────────────────────────────────┤
│                                 │
│           Editor                │
│           Focus                 │
│                                 │
├─────────────────────────────────┤
│ > AI: Quick response here...    │
│ > $ build command               │
└─────────────────────────────────┘
```

### Medium Terminal (80x24 to 120x40)
```
┌────────────────────────────────────────────────┐
│ [Sess] [Agents] [Monitor] | CPU: 42% RAM: 67% │
├─────────────────┬──────────────────────────────┤
│                 │                              │
│     Editor      │      AI Assistant           │
│                 │                              │
│                 │                              │
├─────────────────┼──────────────────────────────┤
│ Terminal        │ ClaudeFlow Status           │
└─────────────────┴──────────────────────────────┘
```

## Keyboard Navigation

### Global Shortcuts
- `Ctrl+Space` - Command palette
- `Ctrl+Tab` - Cycle through panes
- `Ctrl+Shift+P` - Project switcher
- `Ctrl+~` - Toggle terminal

### Pane-Specific
- **Editor**: Helix keybindings + AI extensions
- **AI**: Chat navigation + diff controls
- **File Tree**: vim-style navigation
- **Terminal**: Standard shell shortcuts

## ADHD Accommodations

### Visual Clarity
- High contrast borders between panes
- Clear focus indicators
- Status symbols with color coding
- Minimal visual clutter

### Attention Management
- Single active pane highlighting
- Dimmed inactive areas
- Progress indicators for long operations
- Gentle transition animations

### Cognitive Load Reduction
- Consistent layout across sessions
- Predictable information placement
- Clear action feedback
- Context preservation on pane switching