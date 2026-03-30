# Getting Started with Dopemux

Welcome to Dopemux - the world's first comprehensively ADHD-accommodated development platform! This tutorial will guide you through your first steps with Dopemux, from installation to your first AI-assisted coding session.

## What You'll Learn

By the end of this tutorial, you'll be able to:
- Install and configure Dopemux
- Set up your first project with ADHD accommodations
- Use AI assistance for code generation and review
- Navigate the integrated terminal interface
- Customize accommodations for your working style

## Prerequisites

- **Operating System**: macOS, Linux, or Windows WSL
- **Terminal**: xterm-256color or better (iTerm2, Alacritty, Windows Terminal)
- **Dependencies**: Node.js 18+, Git, tmux 3.0+
- **Network**: Internet connection for AI services and MCP servers

## Step 1: Installation

### Quick Installation (Recommended)

The fastest way to get started is with our one-liner installer:

```bash
curl -sSL https://install.dopemux.dev | bash
```

This installer will:
1. Detect your operating system and terminal capabilities
2. Install required dependencies (Node.js, Rust, tmux)
3. Download and build Dopemux core components
4. Set up MCP servers for AI integration
5. Configure initial ADHD accommodation settings

### Manual Installation

If you prefer more control, you can install manually:

```bash
# 1. Clone the repository
git clone https://github.com/dopemux/dopemux.git
cd dopemux

# 2. Install dependencies
./scripts/install-deps.sh

# 3. Build core components
npm run build:core
cargo build --release --bin helix-dopemux

# 4. Set up MCP servers
./scripts/setup-mcp-servers.sh

# 5. Install globally
npm install -g .

# 6. Initialize configuration
dopemux init
```

### Verify Installation

Check that everything is working:

```bash
# Check Dopemux version
dopemux --version

# Verify MCP servers
dopemux mcp list

# Test terminal capabilities
dopemux check-terminal
```

You should see output like:
```
Dopemux v1.0.0
✓ Terminal: 256-color support detected
✓ Mouse: Full mouse support available
✓ MCP Servers: 7 servers configured
✓ AI Services: Connected to Claude and context providers
```

## Step 2: Initial Configuration

### ADHD Assessment and Setup

Dopemux includes an optional ADHD assessment to optimize accommodations for your specific needs:

```bash
# Start the accommodation setup wizard
dopemux setup-adhd
```

The wizard will ask about:
- **Attention patterns**: How you focus best, distraction triggers
- **Information processing**: Visual vs. auditory preferences
- **Task management**: How you break down and track work
- **Energy patterns**: When you're most productive
- **Sensory preferences**: Colors, animations, notification styles

### Configuration Overview

Your configuration is stored in `~/.config/dopemux/config.yaml`:

```yaml
# Example configuration
version: "1.0"

adhd:
  attention_tracking: true
  break_reminders: true
  focus_mode: "adaptive"
  reduced_motion: false
  high_contrast: false

ui:
  layout_preset: "development"
  terminal_theme: "dark"
  status_bar: "rich"

memory:
  provider: "letta"
  retention_days: 90
  auto_backup: true

editor:
  backend: "helix"
  ai_integration: true
  vim_bindings: false
```

## Step 3: Create Your First Project

### Project Creation

Let's create a simple web application project to explore Dopemux features:

```bash
# Create a new project
dopemux new project my-web-app --template=react-typescript

# Navigate to the project
cd my-web-app

# Start Dopemux in the project directory
dopemux start
```

This opens the Dopemux interface:

```
┌──────────────────── Dopemux - my-web-app ────────────────────┐
│ [Sessions] [Agents] [Monitor] [Flow] [Chat]  | ⚡ CPU: 42% │
├────────────┬──────────────────────────────┬─────────────────┤
│            │                              │  📁 Files      │
│  Editor    │     Welcome to Dopemux      │  ├─ src/       │
│            │                              │  │  ├─ App.tsx│
│  Welcome!  │  🤖 I'm here to help you    │  │  └─ ...     │
│            │     build amazing software  │  └─ tests/     │
│            │                              │                 │
│            │  Try typing: /help          │  🤖 Agents     │
│            │                              │  ├─ Ready: 5   │
│            │                              │  └─ Active: 0  │
├────────────┼──────────────────────────────┼─────────────────┤
│ Terminal   │        Project Status       │  💬 Quick Help │
│ $ ls       │   [Init] → [Config] → [Run] │  F1: Help      │
│            │     ✓       ⟳        ⏳     │  F2: Files     │
└────────────┴──────────────────────────────┴─────────────────┘
```

### Understanding the Interface

The Dopemux interface has several key areas:

1. **Top Status Bar**: Navigation tabs and system status
2. **Left Panel**: Integrated code editor (Helix-based)
3. **Center Panel**: AI assistant chat and workflow visualization
4. **Right Panel**: File browser and agent status
5. **Bottom Row**: Terminal and help information

### Basic Navigation

- **Ctrl+Space**: Open command palette
- **Ctrl+Tab**: Cycle through panes
- **F1**: Help and documentation
- **F2**: File browser
- **F3**: Agent status
- **F4**: Terminal focus

## Step 4: AI-Assisted Development

### Your First AI Interaction

Let's ask the AI to help us build a simple component:

1. Click in the center panel or press `Ctrl+3` to focus the AI chat
2. Type your request:

```
Create a simple user card component that displays:
- User avatar
- Name and email
- Join date
- Status indicator (online/offline)

Use TypeScript and make it accessible.
```

3. Press Enter and watch the AI generate code:

```typescript
// UserCard.tsx
interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl: string;
  joinDate: Date;
  isOnline: boolean;
}

interface UserCardProps {
  user: User;
  className?: string;
}

export const UserCard: React.FC<UserCardProps> = ({
  user,
  className = ''
}) => {
  return (
    <div
      className={`user-card ${className}`}
      role="article"
      aria-label={`User profile for ${user.name}`}
    >
      <img
        src={user.avatarUrl}
        alt={`${user.name}'s avatar`}
        className="user-card__avatar"
        loading="lazy"
      />

      <div className="user-card__info">
        <h3 className="user-card__name">{user.name}</h3>
        <p className="user-card__email">{user.email}</p>
        <time
          className="user-card__join-date"
          dateTime={user.joinDate.toISOString()}
        >
          Joined {user.joinDate.toLocaleDateString()}
        </time>
      </div>

      <div
        className={`user-card__status ${
          user.isOnline ? 'online' : 'offline'
        }`}
        aria-label={`Status: ${user.isOnline ? 'Online' : 'Offline'}`}
      >
        <span className="status-indicator" />
        {user.isOnline ? 'Online' : 'Offline'}
      </div>
    </div>
  );
};
```

### Applying AI Suggestions

The AI will show you a diff preview. You can:

- **Accept All**: Apply the entire suggestion
- **Accept Hunks**: Apply parts of the suggestion
- **Modify**: Edit before applying
- **Reject**: Decline the suggestion

Try clicking "Accept All" to create the file.

### Editor Integration

Now that the file is created, you can:

1. **Edit the code** in the left panel using Helix keybindings
2. **Get AI suggestions** by selecting code and pressing `Ctrl+Space`
3. **Ask for explanations** by highlighting code and typing `/explain`
4. **Generate tests** by typing `/test UserCard`

## Step 5: ADHD Accommodations in Action

### Focus Mode

Dopemux automatically adapts to help you maintain focus:

```bash
# Activate deep focus mode
dopemux focus deep
```

In focus mode:
- Non-essential UI elements are dimmed
- Notifications are minimized
- The interface adapts to reduce cognitive load
- Break reminders appear based on your work patterns

### Attention Tracking

Dopemux learns your attention patterns:

- **Context switching** is tracked and minimized
- **Focus sessions** are measured and optimized
- **Distraction recovery** is assisted with gentle guidance
- **Energy patterns** are recognized and accommodated

### Context Preservation

One of Dopemux's key ADHD accommodations is seamless context preservation:

```bash
# Your session is automatically saved
# Close Dopemux and reopen later:
dopemux restore

# Everything returns exactly as you left it:
# - Open files and cursor positions
# - AI conversation history
# - Task progress and mental models
# - Project context and decisions
```

## Step 6: Working with Agents

### Available Agents

Dopemux includes several specialized AI agents:

```bash
# List available agents
dopemux agents list
```

You'll see agents like:
- **CodeGen**: Code generation and implementation
- **Reviewer**: Code review and quality analysis
- **Tester**: Test generation and validation
- **Architect**: System design and planning
- **Security**: Security analysis and recommendations

### Using Agents

Try using different agents:

```bash
# Generate tests for your component
/agent tester "Create tests for UserCard component"

# Get a security review
/agent security "Review UserCard for vulnerabilities"

# Ask for architecture advice
/agent architect "How should I structure a user management system?"
```

### Agent Workflows

You can create workflows that combine multiple agents:

```bash
# Start a comprehensive code review workflow
dopemux workflow start code-review

# This typically runs:
# 1. Security scan
# 2. Quality analysis
# 3. Test coverage check
# 4. Performance review
# 5. Accessibility audit
```

## Step 7: Customizing Your Experience

### Layout Customization

Dopemux supports multiple layout presets:

```bash
# Switch to review mode for code review
dopemux layout review

# Switch to monitoring mode for debugging
dopemux layout monitor

# Create a custom layout
dopemux layout save my-custom-layout
```

### ADHD Accommodation Tuning

Fine-tune accommodations based on your experience:

```bash
# Adjust attention tracking sensitivity
dopemux config set adhd.attention_sensitivity 0.8

# Change break reminder frequency
dopemux config set adhd.break_interval 25m

# Enable high contrast mode
dopemux config set ui.high_contrast true
```

### Keyboard Shortcuts

Customize keyboard shortcuts:

```yaml
# In ~/.config/dopemux/keybindings.yaml
keybindings:
  global:
    "ctrl+space": "command_palette"
    "ctrl+shift+p": "project_switcher"
    "ctrl+/": "ai_assist"

  editor:
    "ctrl+.": "ai_suggest"
    "ctrl+shift+.": "ai_explain"

  ai_chat:
    "ctrl+enter": "send_message"
    "ctrl+r": "regenerate_response"
```

## Next Steps

Congratulations! You've completed your first Dopemux session. Here's what to explore next:

### Advanced Tutorials
- [Working with ClaudeFlow Workflows](./workflows.md)
- [Advanced ADHD Accommodations](./adhd-advanced.md)
- [Team Collaboration Setup](./team-setup.md)
- [Enterprise Deployment](./enterprise.md)

### Feature Deep Dives
- [Memory System and Context Management](./memory-system.md)
- [Custom Agent Creation](./custom-agents.md)
- [Integration with External Tools](./integrations.md)
- [Performance Optimization](./performance.md)

### Community Resources
- [Dopemux Community Forum](https://community.dopemux.dev)
- [ADHD Developer Support Group](https://adhd.dopemux.dev)
- [Feature Requests and Feedback](https://feedback.dopemux.dev)

## Troubleshooting

### Common Issues

**Terminal not displaying correctly:**
```bash
# Check terminal capabilities
dopemux check-terminal

# Try forcing color mode
TERM=xterm-256color dopemux start
```

**AI services not responding:**
```bash
# Check MCP server status
dopemux mcp status

# Restart MCP servers
dopemux mcp restart
```

**Performance issues:**
```bash
# Check system resources
dopemux status

# Enable performance mode
dopemux config set performance.mode optimized
```

### Getting Help

- **In-app help**: Press `F1` or type `/help`
- **Documentation**: [docs.dopemux.dev](https://docs.dopemux.dev)
- **Community support**: [community.dopemux.dev](https://community.dopemux.dev)
- **Professional support**: [support.dopemux.dev](https://support.dopemux.dev)

## Welcome to Dopemux!

You're now ready to experience AI-powered development with comprehensive ADHD accommodations. Remember:

- **Trust the process**: Dopemux learns your patterns and gets better over time
- **Customize freely**: Every accommodation can be adjusted to your needs
- **Ask for help**: The AI and community are here to support you
- **Share feedback**: Your experience helps improve Dopemux for everyone

Happy coding! 🚀