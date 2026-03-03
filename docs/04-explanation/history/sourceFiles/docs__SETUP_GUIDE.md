# Dopemux Developer Setup Guide

## Quick Start (5 Minutes)

For ADHD developers who need to get started quickly:

### 1. Install Dopemux
```bash
# Clone and install
git clone <dopemux-repo>
cd dopemux-mvp
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -e .
```

### 2. Verify Installation
```bash
dopemux --version
# Should show: Dopemux 0.1.0
```

### 3. Initialize Your First Project
```bash
cd your-project
dopemux init
# Follow prompts, choose template
```

### 4. Start Development
```bash
dopemux start
# Claude Code launches with ADHD optimizations
```

**🎉 You're ready!** Skip to [Usage Examples](#usage-examples) if you want to start immediately.

---

## Detailed Installation

### Prerequisites

#### Required Software

| Software | Version | Purpose | Installation |
|----------|---------|---------|-------------|
| **Python** | 3.9+ | Core runtime | [python.org](https://python.org) |
| **Claude Code** | Latest | AI development environment | [claude.ai/code](https://claude.ai/code) |
| **Git** | 2.0+ | Version control integration | [git-scm.com](https://git-scm.com) |

#### System Requirements

| Requirement | Minimum | Recommended | ADHD Optimization |
|-------------|---------|-------------|------------------|
| **RAM** | 4GB | 8GB+ | More RAM = faster context restoration |
| **Storage** | 500MB | 2GB+ | Room for session history |
| **CPU** | 2 cores | 4+ cores | Better attention monitoring performance |
| **Network** | Any | Stable | For MCP server communication |

### Step-by-Step Installation

#### 1. Python Environment Setup

**Check Python Version:**
```bash
python --version
# Should be 3.9 or higher
```

**If Python is outdated:**
- **macOS:** `brew install python@3.11`
- **Ubuntu/Debian:** `sudo apt update && sudo apt install python3.11`
- **Windows:** Download from [python.org](https://python.org)

#### 2. Clone Dopemux Repository

```bash
# Choose a location for Dopemux
cd ~/code  # or your preferred directory

# Clone repository
git clone <dopemux-repository-url>
cd dopemux-mvp

# Verify structure
ls -la
# Should see: src/, docs/, pyproject.toml, etc.
```

#### 3. Create Virtual Environment

**Why virtual environment?** Isolates Dopemux dependencies from system Python, preventing conflicts.

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Verify activation
which python
# Should show path with .venv
```

#### 4. Install Dopemux

```bash
# Install in development mode
pip install -e .

# Verify dependencies
pip list | grep -E "(click|rich|pyyaml)"
# Should show installed versions
```

#### 5. Verify Installation

```bash
# Test basic functionality
dopemux --version
dopemux --help

# Test configuration loading
dopemux config show 2>/dev/null || echo "Config system working"
```

### Claude Code Installation

#### Download and Install

1. **Visit** [claude.ai/code](https://claude.ai/code)
2. **Download** for your platform (Mac/Windows/Linux)
3. **Install** following platform-specific instructions
4. **Verify** installation:

```bash
# Check if Claude Code is accessible
claude-code --version
# Should show Claude Code version

# If not found, check common locations:
# macOS: /Applications/Claude Code.app/Contents/MacOS/claude-code
# Linux: /usr/local/bin/claude-code or /usr/bin/claude-code
# Windows: C:\Program Files\Claude Code\claude-code.exe
```

#### Custom Installation Path

If Claude Code is installed in a non-standard location:

```bash
# Set custom path
export DOPEMUX_CLAUDE_PATH="/path/to/claude-code"

# Or add to shell profile
echo 'export DOPEMUX_CLAUDE_PATH="/path/to/claude-code"' >> ~/.bashrc
```

### MCP Server Setup

Dopemux requires several MCP servers for optimal ADHD support:

#### Quick Setup (Recommended)

Use the automated installation script:

```bash
# Run the MCP server installation script
./scripts/install-mcp-servers.sh
```

This script will:
- Check prerequisites (Node.js, npm)
- Install TypeScript compiler
- Install all supported MCP servers
- Provide setup instructions for environment variables
- Handle known issues (like Leantime build problems)

#### Manual Setup

#### 1. claude-context (Hybrid Search)

**Automatic Setup:** Dopemux will configure this automatically with cloud embeddings and local Milvus.

**Manual Setup (if needed):**
```bash
# Install Milvus locally (Docker)
docker run -d --name milvus-standalone \
  -p 19530:19530 \
  -v milvus_data:/var/lib/milvus \
  milvusdb/milvus:latest standalone

# Verify connection
curl http://localhost:19530/health
```

#### 2. mas-sequential-thinking (Complex Reasoning)

**Location:** `/Users/hue/code/mcp-server-mas-sequential-thinking`

**Setup:**
```bash
# Clone the server (if not already available)
cd ~/code
git clone <mas-sequential-thinking-repo>
cd mcp-server-mas-sequential-thinking

# Install dependencies
npm install  # or yarn install

# Test server
npm test  # or yarn test
```

#### 3. context7 (Documentation Access)

**Automatic:** Configured automatically by Dopemux for latest documentation access.

#### 4. morphllm-fast-apply (Code Transformations)

**Automatic:** Configured automatically for efficient code editing.

#### 5. leantime (Project Management Integration)

**Purpose:** Enables AI assistants to interact with Leantime project management tasks.

**Setup:**
```bash
# Install TypeScript compiler (required for build)
npm install -g typescript

# Install Leantime MCP server
npm install -g leantime-mcp
```

**Note:** Currently disabled by default due to build issues. Enable manually after installation:

```bash
# Enable Leantime MCP server
dopemux config set mcp_servers.leantime.enabled true

# Set required environment variables
export LEANTIME_URL="https://your-leantime-instance.com"
export LEANTIME_API_KEY="your_api_key_here"
```

**Requirements:**
- Active Leantime instance (self-hosted or cloud)
- Personal Access Token or API Key from Leantime
- Node.js 16+ with npm/yarn

**Troubleshooting:**
- If installation fails, the server may have TypeScript compilation issues
- Check [Leantime MCP GitHub](https://github.com/Leantime/leantime-mcp) for updates
- Alternative: Use direct git installation once issues are resolved

---

## Development Environment Configuration

### Shell Integration

#### Bash/Zsh Completion

Add to your `.bashrc` or `.zshrc`:

```bash
# Dopemux completion
eval "$(_DOPEMUX_COMPLETE=bash_source dopemux)"  # bash
eval "$(_DOPEMUX_COMPLETE=zsh_source dopemux)"   # zsh

# Helpful aliases
alias ds='dopemux status'
alias dsave='dopemux save'
alias drestore='dopemux restore'
alias dtask='dopemux task --list'

# ADHD-friendly function: save with timestamp
dsm() {
    local message="${1:-Auto-save $(date '+%H:%M')}"
    dopemux save --message "$message"
}
```

#### Fish Shell

```fish
# ~/.config/fish/config.fish
# Dopemux completion
eval (dopemux --completion fish)

# Aliases
alias ds='dopemux status'
alias dsave='dopemux save'
alias drestore='dopemux restore'
```

### Editor Integration

#### VSCode Integration

**Recommended Extensions:**
- **Python** - ms-python.python
- **ADHD Focus** - Custom theme for reduced visual complexity
- **Pomodoro Timer** - Focus time management
- **GitLens** - Context-aware git information

**VSCode Settings:**
```json
{
  "editor.fontSize": 14,
  "editor.lineHeight": 1.6,
  "editor.cursorBlinking": "solid",
  "editor.minimap.enabled": false,
  "workbench.colorTheme": "ADHD Friendly Dark",
  "window.title": "${activeEditorShort}${separator}${rootName}",
  "breadcrumbs.enabled": true,
  "python.defaultInterpreterPath": ".venv/bin/python"
}
```

#### Vim/Neovim Integration

```vim
" ~/.vimrc or ~/.config/nvim/init.vim
" ADHD-friendly Vim settings

" Reduce visual complexity
set number
set cursorline
set colorcolumn=88
colorscheme quiet_adhd

" Context preservation
set undofile
set undodir=~/.vim/undo

" Dopemux integration
nnoremap <leader>ds :!dopemux save<CR>
nnoremap <leader>dr :!dopemux restore --list<CR>
nnoremap <leader>dt :!dopemux task --list<CR>
```

### Terminal Configuration

#### ADHD-Friendly Terminal Settings

**Theme:** High contrast, calm colors
```bash
# Example terminal color scheme
export PS1='\[\033[38;5;10m\]\u@\h\[\033[00m\]:\[\033[38;5;12m\]\w\[\033[00m\]\$ '

# Reduce visual noise
set bell-style none
set completion-ignore-case on
set show-all-if-ambiguous on
```

**Font:** Monospace, comfortable size
- **Recommended:** Source Code Pro, Fira Code, JetBrains Mono
- **Size:** 14-16pt for reduced eye strain

---

## Project Setup

### Initialize New Project

#### Interactive Setup

```bash
# Navigate to project directory
cd ~/code/my-new-project

# Initialize with prompts
dopemux init

# Follow interactive prompts:
```

```
🧠 Dopemux Project Initialization

📁 Project Type:
[1] Python (web/api/data science)
[2] JavaScript/TypeScript (web/node)
[3] Rust (systems/cli)
[4] Go (microservices/cli)
[5] Java (enterprise/spring)
[6] Custom template

Select [1-6]: 1

🎯 ADHD Profile:
[1] Gentle (minimal notifications, longer breaks)
[2] Standard (balanced notifications and breaks)
[3] Focused (frequent saves, shorter tasks)

Select [1-3]: 1

⚙️ Claude Models:
[1] Latest models (opus-4.1, sonnet-4)
[2] Fast models (gemini-flash, gpt-mini)
[3] Balanced (mix of speed and capability)

Select [1-3]: 3

✅ Initializing project with:
• Template: Python with ADHD accommodations
• Profile: Gentle notifications, 25-min focus, 5-min breaks
• Models: Balanced selection for different attention states
```

#### Command-Line Setup

```bash
# Quick setup with flags
dopemux init \
  --template python \
  --force \
  ~/code/my-project

# Custom ADHD profile
DOPEMUX_FOCUS_DURATION=30 \
DOPEMUX_NOTIFICATION_STYLE=minimal \
dopemux init --template typescript
```

### Setup Existing Project

#### Add Dopemux to Existing Codebase

```bash
# Navigate to existing project
cd ~/code/existing-project

# Initialize Dopemux (won't overwrite existing files)
dopemux init --template auto-detect

# Dopemux will analyze project and suggest template:
```

```
🔍 Analyzing existing project...

📊 Detected:
• Language: Python (92% confidence)
• Framework: FastAPI
• Testing: pytest
• Linting: black, flake8

🎯 Recommended template: python-web-api

✅ Apply recommended settings? (Y/n): y

📁 Created:
• .dopemux/config.yaml (project settings)
• .claude/claude.md (ADHD-optimized instructions)
• Context database initialized

⚠️  Existing files preserved:
• .gitignore (merged with Dopemux patterns)
• README.md (unchanged)
```

---

## Configuration Customization

### Personal ADHD Profile

Create your personal configuration at `~/.dopemux/config.yaml`:

```yaml
# Personal ADHD accommodations
adhd_profile:
  # Discovered through usage - adjust based on your patterns
  focus_duration: 25              # Your optimal focus time
  break_interval: 5               # Your preferred break length
  notification_style: gentle      # gentle/standard/minimal
  visual_complexity: minimal      # minimal/standard/comprehensive

  # Personal patterns (you'll learn these over time)
  optimal_work_hours:
    - "09:00-11:00"              # Your best focus times
    - "14:00-16:00"

  # What breaks work for you
  effective_breaks:
    - type: nature
      duration: 5
      description: "Look at trees outside"
    - type: movement
      duration: 10
      description: "Walk around block"

# Your preferred models
claude:
  primary_models:
    - claude-opus-4-1-20250805    # For complex thinking
    - claude-sonnet-4-20250514    # For balanced tasks

  fallback_models:
    - gemini-2.5-flash-001       # When scattered/overwhelmed
```

### Team Configuration

For teams with multiple ADHD developers:

```yaml
# .dopemux/team-config.yaml
team_adhd:
  shared_principles:
    - respect_focus_time: true
    - async_first: true
    - meeting_limits: 25          # Max 25 minutes
    - documentation_visual: true   # Prefer diagrams

  collaboration:
    pair_programming:
      max_session: 45             # Longer for pairs
      break_frequency: 15         # Every 15 minutes

    code_reviews:
      max_files: 3                # Don't overwhelm
      time_limit: 30              # Keep focused

  notification_policies:
    focus_hours:
      - "09:00-11:00"             # Team focus time
      - "14:00-16:00"
    urgent_only: true             # During focus hours
```

---

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError

```bash
# Error
ModuleNotFoundError: No module named 'dopemux'

# Solutions
# A) Activate virtual environment
source .venv/bin/activate

# B) Reinstall in development mode
pip install -e .

# C) Check Python path
python -c "import sys; print(sys.path)"
```

#### 2. Claude Code Not Found

```bash
# Error
Error: Claude Code not found. Please install Claude Code first.

# Solutions
# A) Install Claude Code from claude.ai/code
# B) Add to PATH
export PATH="/path/to/claude-code:$PATH"

# C) Set custom path
export DOPEMUX_CLAUDE_PATH="/Applications/Claude Code.app/Contents/MacOS/claude-code"
```

#### 3. MCP Server Connection Failed

```bash
# Error
Error: Failed to connect to MCP server: claude-context

# Solutions
# A) Check server availability
curl http://localhost:19530/health  # For Milvus

# B) Restart Docker services
docker restart milvus-standalone

# C) Check server paths in config
dopemux config show | grep mcp_servers
```

#### 4. Database Locked

```bash
# Error
Error: Context database is locked by another process

# Solutions
# A) Close other Dopemux instances
pkill -f dopemux

# B) Remove lock file
rm .dopemux/.context.db.lock

# C) Restart with clean database
mv .dopemux/context.db .dopemux/context.db.backup
dopemux start  # Will create new database
```

#### 5. Slow Context Restoration

```bash
# Issue: Restoration takes >500ms (ADHD requirement not met)

# Debug
dopemux --debug restore

# Solutions
# A) Vacuum database
sqlite3 .dopemux/context.db "VACUUM;"

# B) Reduce session retention
# Edit .dopemux/config.yaml:
# adhd_profile:
#   session_retention: 25  # Reduce from 50

# C) Check disk space
df -h .dopemux/
```

### Performance Optimization

#### For Low-Resource Systems

```yaml
# .dopemux/config.yaml - Resource-constrained settings
performance:
  # Reduce memory usage
  cache_size_mb: 25              # Reduce from 50
  max_concurrent_operations: 1   # Reduce from 3

adhd_profile:
  # Reduce database activity
  auto_save_interval: 60         # Reduce from 30
  session_retention: 25          # Reduce from 50

# Use faster models for scattered state
claude:
  models:
    scattered: [gpt-4o-mini-2024-07-18]  # Fastest option
```

#### For High-Performance Systems

```yaml
# .dopemux/config.yaml - High-performance settings
performance:
  cache_size_mb: 100             # More caching
  max_concurrent_operations: 5   # More parallelism

adhd_profile:
  auto_save_interval: 15         # More frequent saves
  session_retention: 100         # Keep more history

# Use premium models
claude:
  models:
    focused: [claude-opus-4-1-20250805, o3-pro-reasoning-2024-12-17]
```

### Debugging Tools

#### Debug Mode

```bash
# Enable comprehensive debugging
dopemux --debug --verbose status

# Debug specific components
DOPEMUX_DEBUG_ATTENTION=1 dopemux status --attention
DOPEMUX_DEBUG_CONTEXT=1 dopemux save --force
DOPEMUX_DEBUG_MCP=1 dopemux start
```

#### Log Analysis

```bash
# View logs
tail -f .dopemux/dopemux.log

# Filter for errors
grep ERROR .dopemux/dopemux.log

# Attention metrics logs
grep "attention_state" .dopemux/dopemux.log | tail -10
```

#### Database Inspection

```bash
# Inspect context database
sqlite3 .dopemux/context.db

# Useful queries:
# .tables                              # List tables
# SELECT COUNT(*) FROM sessions;       # Session count
# SELECT id, timestamp, current_goal FROM sessions ORDER BY timestamp DESC LIMIT 5;
```

---

## Advanced Setup

### Custom MCP Server Development

For developers who want to create custom ADHD-optimized MCP servers:

#### Server Template

```python
# custom_adhd_server.py
from mcp import MCPServer
from typing import Dict, Any

class ADHDOptimizedServer(MCPServer):
    def __init__(self):
        super().__init__()
        self.adhd_profile = None

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # Check user's current attention state
        attention_state = request.get('attention_state', 'normal')

        # Adapt response based on ADHD needs
        if attention_state == 'scattered':
            return self._create_minimal_response(request)
        elif attention_state == 'focused':
            return self._create_detailed_response(request)

    def _create_minimal_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Bullet-point responses for scattered attention"""
        return {
            "response": self._bullet_points_only(request),
            "visual_complexity": "minimal",
            "estimated_time": "2 minutes"
        }
```

#### Server Registration

```yaml
# .dopemux/config.yaml
mcp_servers:
  custom-adhd-server:
    enabled: true
    config:
      path: "/path/to/custom_adhd_server.py"
      adhd_aware: true
      response_adaptation: true
```

### Integration Development

#### VSCode Extension

For teams wanting tight VSCode integration:

```typescript
// Extension structure for ADHD developers
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    // ADHD-friendly status bar
    const adhdStatusBar = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );

    // Attention state indicator
    const updateAttentionState = async () => {
        const state = await getDopemuxAttentionState();
        adhdStatusBar.text = `🧠 ${state}`;
        adhdStatusBar.color = getStateColor(state);
    };

    // Gentle break reminders
    setInterval(async () => {
        const sessionDuration = await getDopemuxSessionDuration();
        if (sessionDuration > 25 * 60 * 1000) { // 25 minutes
            vscode.window.showInformationMessage(
                "🌟 Great focus! Consider a 5-minute break?",
                "Take Break", "5 More Minutes"
            );
        }
    }, 5 * 60 * 1000); // Check every 5 minutes
}
```

#### Tmux Integration

For developers using tmux:

```bash
# ~/.tmux.conf - ADHD-optimized tmux
# Gentle colors, clear status
set -g status-bg colour235
set -g status-fg colour250

# ADHD-friendly session names
set -g status-left "🧠 #S "
set -g status-right "#{?client_prefix,⚡,} %H:%M"

# Dopemux integration
set -g status-interval 5
set -g status-right-length 50
set -g status-right "#(dopemux status --attention | grep 'Current State' | cut -d'│' -f3) %H:%M"
```

---

## Usage Examples

### Daily Workflow Examples

#### Morning Startup (ADHD-Optimized)

```bash
#!/bin/bash
# ~/bin/adhd-dev-start.sh
# ADHD-friendly development startup script

echo "🌅 Good morning! Let's set up your development environment..."

# Check energy/attention level
echo "How are you feeling this morning?"
echo "[1] High energy, ready to tackle complex tasks"
echo "[2] Normal energy, standard development work"
echo "[3] Low energy, need gentle start"
read -p "Select [1-3]: " energy_level

# Set ADHD profile based on energy
case $energy_level in
    1)
        export DOPEMUX_FOCUS_DURATION=30
        export DOPEMUX_BREAK_INTERVAL=5
        echo "🚀 High-energy profile activated!"
        ;;
    2)
        export DOPEMUX_FOCUS_DURATION=25
        export DOPEMUX_BREAK_INTERVAL=5
        echo "😊 Standard profile activated!"
        ;;
    3)
        export DOPEMUX_FOCUS_DURATION=15
        export DOPEMUX_BREAK_INTERVAL=10
        echo "🌱 Gentle profile activated!"
        ;;
esac

# Start development session
cd ~/code/current-project
dopemux status
dopemux start

echo "✨ Ready to code! Remember: progress > perfection"
```

#### Context Switch Recovery

```bash
# After interruption (meeting, lunch, etc.)
# Quick script to get back into flow

echo "🔄 Welcome back! Let's restore your context..."

# Show where you left off
dopemux status --context

# Quick task reminder
echo ""
echo "📋 Your active tasks:"
dopemux task --list | head -5

# Restore previous session
dopemux restore

echo "🎯 Context restored! You were working on:"
dopemux status --context | grep "Current Goal"
```

#### End of Day Routine

```bash
#!/bin/bash
# End of day - ADHD-friendly shutdown

echo "🌅 Great work today! Let's wrap up..."

# Save current context
dopemux save --message "End of day - $(date '+%Y-%m-%d %H:%M')"

# Show accomplishments (important for ADHD motivation)
echo ""
echo "🎉 Today's accomplishments:"
dopemux task --list | grep "✅" || echo "Progress made on ongoing tasks!"

# Prepare for tomorrow
echo ""
echo "📋 Ready for tomorrow:"
dopemux task --list | grep "⏳" | head -3

echo ""
echo "✨ Rest well! Your progress is preserved and ready for tomorrow."
```

### Project-Specific Examples

#### Python Web API Project

```bash
# Setup new Python API project with ADHD optimizations
mkdir my-api-project
cd my-api-project

# Initialize with Python template
dopemux init --template python

# Set up API-specific tasks
dopemux task "Set up FastAPI project structure" --priority high --duration 25
dopemux task "Implement user model with Pydantic" --priority high --duration 25
dopemux task "Add authentication endpoints" --priority high --duration 30
dopemux task "Write API documentation" --priority medium --duration 20
dopemux task "Add comprehensive tests" --priority medium --duration 25

# Start development
dopemux start
```

#### Frontend React Project

```bash
# Setup React project with ADHD-friendly task breakdown
mkdir my-react-app
cd my-react-app

# Initialize with JavaScript template
dopemux init --template javascript

# Break down frontend work into ADHD-friendly chunks
dopemux task "Set up React project with TypeScript" --duration 20
dopemux task "Create component structure" --duration 25
dopemux task "Implement routing with React Router" --duration 25
dopemux task "Add state management (Zustand)" --duration 30
dopemux task "Style with Tailwind CSS" --duration 25
dopemux task "Add form handling and validation" --duration 25

# Start with context awareness
dopemux start
```

---

## Best Practices for ADHD Developers

### Focus Management

#### Optimal Focus Sessions
```bash
# 25-minute focused work with 5-minute breaks
# This follows Pomodoro technique adapted for ADHD

# Start session
dopemux save --message "Starting focus session: $(date +%H:%M)"
dopemux task "Current focus task" --duration 25

# Work for 25 minutes...

# End session
dopemux save --message "Focus session complete: $(date +%H:%M)"
echo "🎉 Great work! Take a 5-minute break."
```

#### Break Activities (ADHD-Effective)
```bash
# Nature breaks (most restorative for ADHD)
echo "🌳 Look out the window for 30 seconds"
echo "🚶‍♀️ Walk outside for 5 minutes"

# Movement breaks
echo "🤸‍♀️ Light stretching"
echo "💃 Dance to one song"

# Mindful breaks
echo "🧘‍♀️ 3 deep breaths"
echo "☕ Mindful tea/coffee preparation"
```

### Context Preservation Strategies

#### Frequent Saves with Meaningful Messages
```bash
# Save context with descriptive messages
dopemux save --message "Completed user model, about to start authentication"
dopemux save --message "Debugging login issue - found problem in JWT validation"
dopemux save --message "Breakthrough: realized need async approach"
```

#### Decision Documentation
```bash
# Important for ADHD memory and context switching
dopemux save --message "Decided: PostgreSQL over MongoDB for relational data"
dopemux save --message "Architecture choice: microservices with Docker compose"
dopemux save --message "Testing strategy: pytest with fixtures for database"
```

### Task Management

#### ADHD-Friendly Task Decomposition
```bash
# Instead of: "Build user authentication system" (overwhelming)
# Break into:

dopemux task "Create User model class" --duration 15 --priority high
dopemux task "Add password hashing method" --duration 10 --priority high
dopemux task "Write user validation tests" --duration 20 --priority medium
dopemux task "Create login endpoint" --duration 25 --priority high
dopemux task "Add JWT token generation" --duration 20 --priority high
dopemux task "Test login flow end-to-end" --duration 15 --priority medium

# Each task feels manageable and has clear completion criteria
```

#### Progress Celebration
```bash
# ADHD needs positive reinforcement - celebrate wins!
dopemux task --list | grep "✅" | wc -l
echo "🎉 You've completed $(dopemux task --list | grep -c '✅') tasks today!"
```

---

## Migration Guide

### From Existing Development Setup

#### Migrating from Standard Development

```bash
# If you currently use standard tools without ADHD optimizations

# 1. Backup current setup
cp -r ~/.vscode/settings.json ~/.vscode/settings.json.backup
cp ~/.gitconfig ~/.gitconfig.backup

# 2. Install Dopemux alongside existing tools
# (Dopemux doesn't replace your tools, it enhances them)

# 3. Initialize Dopemux in existing project
cd your-existing-project
dopemux init --template auto-detect

# 4. Start with gentle settings
dopemux save --message "First Dopemux session - migrating from standard setup"
dopemux start
```

#### Migrating Context from Other Tools

```bash
# If you have existing session data from other tools
# (tmux sessions, IDE workspaces, etc.)

# 1. Document current workflow
dopemux save --message "Current workflow: $(describe-your-current-process)"

# 2. Gradually adopt Dopemux features
# Start with just context saving
dopemux save --message "End of coding session"

# Then add task management
dopemux task "Current work in progress" --duration 25

# Finally, full integration
dopemux start  # Full ADHD optimization
```

### Team Migration

#### Gradual Team Adoption

```yaml
# Phase 1: Individual adoption (1-2 weeks)
team_migration:
  phase_1:
    - individual_setup: true
    - shared_config: false
    - team_features: false

# Phase 2: Shared configurations (2-3 weeks)
  phase_2:
    - shared_adhd_principles: true
    - team_meeting_limits: true
    - pair_programming_adaptations: true

# Phase 3: Full team integration (1 month)
  phase_3:
    - shared_context_sessions: true
    - team_attention_awareness: true
    - collaborative_task_management: true
```

---

## FAQ

### Common Questions

#### Q: Will Dopemux slow down my development?
**A:** No! Dopemux is designed with performance targets:
- Context save: <50ms (invisible)
- Context restore: <500ms (barely noticeable)
- Attention monitoring: <2% CPU usage
- Most operations complete faster than standard tools due to ADHD optimizations

#### Q: Can I use Dopemux with my existing IDE?
**A:** Yes! Dopemux works alongside any development environment:
- VSCode: Full integration available
- Vim/Neovim: Configuration templates provided
- JetBrains IDEs: Works with external tools
- Any terminal-based workflow: Perfect integration

#### Q: What if I don't have ADHD?
**A:** Dopemux benefits all developers:
- Context preservation helps with interruptions
- Task decomposition improves focus
- Progress visualization motivates everyone
- Gentle UX reduces stress for all users

#### Q: Is my code/context data secure?
**A:** Absolutely:
- All data stored locally (no cloud by default)
- SQLite database with user-only permissions
- No telemetry or usage tracking
- Open source for transparency

#### Q: Can I customize the ADHD accommodations?
**A:** Yes! Highly customizable:
- Adjust focus durations, break intervals
- Change notification styles
- Customize visual complexity
- Create personal attention profiles
- Configure per-project settings

#### Q: How do I share Dopemux with my team?
**A:** Multiple options:
- Individual setup with shared principles
- Team configuration files
- Collaborative session sharing
- ADHD accommodation documentation for team awareness

---

**🎉 Setup Complete!**

You now have a comprehensive ADHD-optimized development environment with Dopemux. The system is designed to grow with you, learning your patterns and adapting to your needs.

**Next steps:**
1. **Start coding** - `dopemux start`
2. **Save frequently** - `dopemux save --message "your progress"`
3. **Break tasks down** - `dopemux task "specific action"`
4. **Monitor attention** - `dopemux status`
5. **Celebrate progress** - Every small win counts! 🌟

**Remember:** Dopemux is built by and for the ADHD developer community. Your feedback helps make it better for everyone. 🧠💚