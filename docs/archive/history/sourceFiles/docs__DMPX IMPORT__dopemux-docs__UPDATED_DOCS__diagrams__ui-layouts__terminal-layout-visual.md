# Dopemux Terminal Layout - Visual Specification

## Main Development Layout (Default)

```
┌──────────────────── Dopemux v1.0.0 ─ Project: my-app ────────────────────┐
│ [Dev] [Life] [Social] [Research] [Monitor]     ⚡ CPU: 42% 🧠 Focus: High │
├─────────────┬─────────────────────────────────┬──────────────────────────┤
│             │                                 │  📁 Files               │
│             │     Welcome to Dopemux         │  ├─ src/                 │
│   Editor    │                                 │  │  ├─ App.tsx          │
│             │  🤖 AI: I'm here to help you   │  │  ├─ auth.ts           │
│  auth.ts    │     build amazing software     │  │  └─ utils/            │
│             │                                 │  └─ tests/              │
│  function   │  💡 Suggestion: Consider using │                          │
│  login() {  │     async/await for this       │  🤖 Agents              │
│    // ...   │     authentication flow        │  ├─ Code: Ready         │
│  }          │                                 │  ├─ Review: Busy        │
│             │  [Apply] [Explain] [Modify]    │  ├─ Test: Ready          │
│             │                                 │  └─ Research: Idle      │
├─────────────┼─────────────────────────────────┼──────────────────────────┤
│  Terminal   │       Workflow Status          │  💬 Quick Actions       │
│  $ npm test │  ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐ ┌─┐  │  F1  Help               │
│  ✅ 15 pass │  │1│→│2│→│3│→│4│⟲│5│ │6│ │7│  │  F2  Files              │
│  ❌ 2 fail  │  └─┘ └─┘ └─┘ └─┘ └─┘ └─┘ └─┘  │  F3  Agents             │
│             │    Code→Test→Review→Deploy     │  F4  Terminal           │
└─────────────┴─────────────────────────────────┴──────────────────────────┘
```

## Layout Sections

### Top Status Bar
- **Left**: Navigation tabs for 5 core subsystems (Dev/Life/Social/Research/Monitor)
- **Center**: Project name and current context
- **Right**: System status (CPU, memory) and ADHD indicators (focus level, energy)

### Main Content Area (3-Column Layout)

#### Left Panel: Integrated Editor (33% width)
- **Primary Function**: Code editing with Helix keybindings
- **AI Integration**: Inline suggestions and context-aware help
- **Features**:
  - Syntax highlighting with tree-sitter
  - Real-time error detection
  - Git integration indicators
  - Diff preview capabilities

#### Center Panel: AI Assistant & Workflow (45% width)
- **Upper Section**: AI chat and interaction
  - Contextual suggestions based on current code
  - Natural language queries and explanations
  - Quick action buttons (Apply/Explain/Modify)
- **Lower Section**: Visual workflow representation
  - ASCII art pipeline showing current stage
  - Progress indicators for multi-step tasks
  - Real-time status updates

#### Right Panel: Context & Navigation (22% width)
- **Upper Section**: File browser and project navigation
  - Tree view of project structure
  - Recently modified files
  - Quick access to frequently used files
- **Lower Section**: Agent status and system information
  - Active agents and their current state
  - Queue of pending tasks
  - Quick action shortcuts (F1-F12)

### Bottom Status Strip
- **Left**: Terminal output and command execution
- **Center**: Workflow progress and current task status
- **Right**: Context-sensitive help and keyboard shortcuts

## ADHD-Optimized Features

### Visual Hierarchy
```
Priority 1 (Highest Contrast):
├─ Current cursor position
├─ AI suggestions requiring attention
├─ Error messages and warnings
└─ Active workflow step

Priority 2 (Medium Contrast):
├─ File browser current selection
├─ Terminal output
├─ Agent status indicators
└─ Progress bars

Priority 3 (Low Contrast):
├─ Background text and comments
├─ Inactive UI elements
├─ Secondary navigation
└─ System status information
```

### Attention Management
- **Focus Mode**: Dims non-essential elements, enlarges current work area
- **Distraction Shield**: Reduces visual noise and unnecessary animations
- **Context Preservation**: Maintains visual state across interruptions
- **Progress Indicators**: Always visible current task status

### Cognitive Load Reduction
- **Information Chunking**: Related information grouped visually
- **Progressive Disclosure**: Details shown only when needed
- **Consistent Layout**: Predictable element placement
- **Visual Anchors**: Key landmarks always in same position

## Responsive Layout Adaptation

### Small Terminal (80x24)
```
┌─────────────── Dopemux ────────────────┐
│ [D][L][S][R][M]     Focus: High       │
├─────────────────┬──────────────────────┤
│     Editor      │    AI Assistant      │
│                 │                      │
│  auth.ts        │  💡 Suggestion...    │
│  function...    │                      │
│                 │  [Apply] [Explain]   │
├─────────────────┼──────────────────────┤
│ $ npm test      │  Files: auth.ts ↑    │
│ ✅ 15 pass      │  Agent: Code Ready   │
└─────────────────┴──────────────────────┘
```

### Large Terminal (120x40+)
```
┌───────────────────────── Dopemux v1.0.0 ─ Project: my-app ─────────────────────────┐
│ [Development] [Life] [Social] [Research] [Monitor]    ⚡CPU: 42% 🧠Focus: High 🔋89% │
├─────────────────┬─────────────────────────────────┬─────────────────────────────────┤
│                 │                                 │  📁 Project Files               │
│     Editor      │         AI Assistant           │  ├─ 📂 src/                     │
│                 │                                 │  │  ├─ 📄 App.tsx               │
│  auth.ts        │  🤖 I can help you improve     │  │  ├─ 📄 auth.ts ← current     │
│                 │     this authentication code   │  │  ├─ 📂 components/           │
│  function       │                                 │  │  └─ 📂 utils/               │
│  authenticateUser│  💡 Consider adding:           │  ├─ 📂 tests/                  │
│  (credentials) {│     • Input validation         │  └─ 📂 docs/                   │
│    if (!creds   │     • Rate limiting            │                                 │
│      .email) {  │     • Audit logging            │  🤖 AI Agents                   │
│      throw new  │                                 │  ├─ 🟢 Code Generator (Ready)   │
│      Error(...) │  Would you like me to:         │  ├─ 🟡 Code Reviewer (Busy)     │
│    }            │  [Implement] [Explain] [Skip]  │  ├─ 🟢 Test Writer (Ready)      │
│                 │                                 │  └─ 🔵 Security Scan (Idle)    │
│  Ln 24, Col 15  │  ┌─────── Workflow ──────┐     │                                 │
│                 │  │ 1→2→3→4→[5]→6→7       │     │  📊 Session Stats               │
├─────────────────┤  │ Analyze→Code→Test→... │     │  ⏱️  Focus: 32 min             │
│ Terminal Output │  └───────────────────────┘     │  🎯 Tasks: 3 complete          │
│ $ npm run test  │                                 │  🧠 Load: Medium               │
│ > jest --coverage│  🔄 Currently: Adding auth    │                                 │
│                 │     validation logic           │  💡 Suggestions                 │
│ ✅ auth.test.js │                                 │  • Take a break in 8 min       │
│ ✅ utils.test.js│  Next: Generate comprehensive  │  • Commit current changes       │
│ ❌ app.test.js  │        test cases              │  • Review security patterns     │
│   - Login fail  │                                 │                                 │
└─────────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

## Color Schemes

### High Contrast Mode (ADHD-Friendly)
```yaml
primary_text: "#FFFFFF"      # Pure white for maximum readability
secondary_text: "#B0B0B0"    # Light gray for secondary information
background: "#000000"        # Pure black background
accent_positive: "#00FF00"   # Bright green for success/ready states
accent_warning: "#FFAA00"    # Orange for warnings and busy states
accent_error: "#FF0000"      # Red for errors and critical alerts
accent_info: "#00AAFF"       # Blue for informational elements
focus_highlight: "#FFFF00"   # Yellow for current focus/selection
```

### Standard Mode
```yaml
primary_text: "#E0E0E0"      # Light text on dark background
secondary_text: "#A0A0A0"    # Medium gray for secondary info
background: "#1A1A1A"        # Dark gray background
accent_positive: "#4CAF50"   # Material green
accent_warning: "#FF9800"    # Material orange
accent_error: "#F44336"      # Material red
accent_info: "#2196F3"       # Material blue
focus_highlight: "#FFC107"   # Material amber
```

## Accessibility Features

### Keyboard Navigation
- **Tab**: Move between major sections
- **Ctrl+1-5**: Switch between main subsystems
- **F1-F12**: Quick actions and context help
- **Alt+Arrow**: Navigate between panes
- **Ctrl+Space**: Open command palette

### Screen Reader Support
- Semantic HTML structure for terminal content
- ARIA labels for all interactive elements
- Keyboard-accessible alternatives for all mouse actions
- Audio feedback for ADHD attention management (optional)

### Motor Accessibility
- Large click targets (minimum 44px)
- Generous spacing between interactive elements
- Support for switch navigation
- Customizable keyboard shortcuts

This layout specification ensures Dopemux provides a terminal-native, ADHD-accommodated development environment that maximizes productivity while minimizing cognitive load.