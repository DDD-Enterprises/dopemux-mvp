# Dopemux Installation Guide

**ADHD-Optimized Development Platform - Complete Setup Instructions**

## 🎯 Quick Start

### One-Command Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/dopemux-mvp
cd dopemux-mvp

# Run the installer
./install.sh
```

That's it! The installer handles everything automatically.

## 📋 Installation Options

### Interactive Installation
```bash
./install.sh
```
- Prompts for installation type
- Shows progress and handles errors
- Creates backups of existing configuration

### Quick Setup (Core Services Only)
```bash
./install.sh --quick
```
- Fastest option for first-time users
- Non-interactive run (auto-confirms prompts)
- Boots **core docker-compose stack** (`postgres`, `redis`, `qdrant`, `conport`, `adhd-engine`, `task-orchestrator`)
- Takes ~3-5 minutes depending on image pulls

### Full Setup (All Services)
```bash
./install.sh --full
```
- Installs everything from quick mode **plus** Zen, PAL apilookup, LiteLLM, DopeconBridge, Genetic Agent, coordination plane services, and shared Redis/PostgreSQL infra
- Requires API keys (Anthropic, OpenRouter, PAL apilookup, etc.) stored in a repo-local `.env` file
- Takes ~10-15 minutes
- Use `./install.sh --full --yes` for unattended installs **after** pre-populating `.env`
- Skip the interactive prompt with `./install.sh --stack full`

### Advanced Flags
- `--stack core|full` – Preselect which compose bundle to run (useful for CI or scripted installs)
- `--env-file /path/to/.env` – Override where API keys/secrets are read/written (defaults to repo-root `.env`)
- `--yes` – Auto-confirm every prompt (implied by `--quick` and `--full`)
- `INSTALLER_TEST_MODE=1 ./install.sh ...` – CI-friendly dry-run that skips Docker/pip/shell side effects (used by automated tests)

### Verify Installation
```bash
./install.sh --verify
```
- Checks if Dopemux is properly installed
- Verifies all services are running
- Shows status of each component

## TaskX Kernel Integration (Submodule-First)

Dopemux now consumes TaskX from `vendor/taskx` and executes through `scripts/taskx`.

```bash
git submodule update --init --recursive vendor/taskx
scripts/taskx --version
scripts/taskx doctor --timestamp-mode deterministic
```

Kernel lifecycle commands are available through Dopemux:

```bash
dopemux kernel --help
```

`.taskx-pin` is deprecated for runtime and CI behavior.
See `docs/TASKX_KERNEL_INTEGRATION.md` for contract details, update procedure, and rollback.

## 🧱 Service Bundles

| Mode | Compose File | Services Included |
|------|--------------|-------------------|
| **Canonical (recommended)** | `compose.yml` | All services: PostgreSQL + AGE, Redis (2x), Qdrant, ConPort MCP, PAL, LiteLLM, Dope-Context, Serena, GPT-Researcher, Exa, Desktop Commander, Leantime Bridge, DopeconBridge, Task Orchestrator, ADHD Engine, Genetic Agent |

The canonical `compose.yml` file at the repository root is now the single source of truth for running Dopemux services. Legacy compose files (docker-compose.master.yml, docker-compose.staging.yml, etc.) are deprecated.

### Environment Variables & `.env`

Full installs prompt for the secrets listed below and store them in a git-ignored `.env` at the repo root so Docker Compose can reuse them:

- `AGE_PASSWORD`
- `ANTHROPIC_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY` (optional but recommended)
- `GEMINI_API_KEY` / `XAI_API_KEY` (optional)
- `LEANTIME_URL` / `LEANTIME_TOKEN`
- `TASK_ORCHESTRATOR_API_KEY` / `ADHD_ENGINE_API_KEY`
- `LITELLM_DATABASE_URL` (defaults to the bundled Postgres DSN)

Canonical key policy:
- Set provider keys in repo-root `.env` only.
- For Gemini, use `GEMINI_API_KEY` only as the source of truth.
- Do not set `GOOGLE_API_KEY` in `.env`; Dopemux compatibility layers map from `GEMINI_API_KEY` when needed.

Run a repo-wide key sweep at any time:
```bash
python3 scripts/env_key_sweep.py
```

Running `./install.sh --full --yes` expects these values to be present ahead of time either in `.env` or exported in your shell. The [API Key Setup Guide](#-api-key-setup-guide) below walks through generating each credential.

## 🔧 Complete Installation Tools & Services

### Core Infrastructure (Always Installed)
- **PostgreSQL 16** with AGE extension - Graph database for knowledge relationships
- **Redis 7** - High-performance caching and event streaming
- **Qdrant** - Vector database for semantic search embeddings
- **Docker & Docker Compose** - Container orchestration

### Dopemux Core Services (Always Installed)
- **ADHD Engine** - FastAPI service for real-time cognitive accommodations
  - 6 background monitors (energy, attention, cognitive load, breaks, hyperfocus, context switching)
  - Task assessment API with ML predictions
  - Energy/attention state tracking
  - Break recommendation system
- **ConPort** - Knowledge graph and persistent memory system
  - Decision logging with rationale
  - Progress tracking with ADHD metadata
  - System patterns and coding best practices
  - Semantic search across decisions and patterns
- **Task Orchestrator** - ADHD-aware task coordination
  - Multi-plane architecture (PM + Cognitive)
  - Leantime integration for status authority
  - Cognitive load balancing
- **Dope-Context** - Semantic code and documentation search
  - AST-aware code indexing (Python, JavaScript, TypeScript)
  - Multi-format document indexing (PDF, Markdown, HTML)
  - Autonomous indexing (zero-touch file monitoring)
  - Hybrid search with neural reranking

### Advanced MCP Servers (Full Installation Only)
- **Zen MCP** - Multi-model reasoning suite
  - thinkdeep: Systematic investigation workflow
  - planner: Interactive planning with revision support
  - consensus: Multi-model decision making (2-5 models)
  - debug: Root cause analysis and hypothesis testing
  - codereview: Comprehensive quality/security/performance analysis
- **PAL apilookup** - Official framework documentation
  - React, Vue.js, Next.js, TypeScript, Node.js docs
  - Version-specific API references
  - Best practices and patterns
- **Serena LSP** - Advanced code intelligence
  - Semantic navigation with ADHD optimizations
  - Code complexity scoring (0.0-1.0 scale)
  - Git-aware navigation (predict next files)
  - Test file bidirectional mapping
- **GPT-Researcher** - Deep web research capabilities
  - Multi-engine search (Google, Bing, DuckDuckGo, Exa)
  - Synthesis and report generation
  - Source credibility assessment
- **Exa** - Neural search engine
  - Semantic web search with relevance ranking
  - Related content discovery
  - Documentation and tutorial finding

### Development Tools & Integration
- **Claude Code Router** - Multi-instance Claude Code management
  - LiteLLM proxy integration for cost optimization
  - Model fallback chains (Sonnet → Grok Code Fast → GPT-5)
  - Session isolation and performance monitoring
- **Statusline Integration** - Real-time development HUD
  - Connection status (ConPort, energy levels, attention state)
  - Session time tracking with break warnings
  - Token usage monitoring (prevents autocompact)
  - Model display and context window awareness
- **Git Integration** - Automatic worktree configuration
  - Post-checkout hooks for ConPort workspace detection
  - Multi-worktree support with isolated contexts
  - Automatic MCP server wiring per worktree
- **tmux Integration** - Multi-pane development orchestration
  - Monitor panes for logs, metrics, and status
  - Agent panes for different development roles
  - Session persistence and context restoration
- **Mobile Support** - Cross-device development
  - Happy coder integration for phone/tablet coding
  - QR code session sharing
  - Mobile-optimized UI for development monitoring

### System Tools & Scripts
- **Shell Scripts** (`scripts/` directory)
  - `start-all.sh` - Complete service orchestration
  - `setup.sh` - Comprehensive installation
  - `doctor` - Health checking and diagnostics
  - `status` - Real-time system status
- **Configuration Management**
  - `.claude/settings.json` - Claude Code integration
  - `.dopemux/config.yaml` - Dopemux-specific settings
  - Environment variable management
- **Backup & Recovery**
  - Automatic configuration backup before changes
  - Service health monitoring and auto-restart
  - Log aggregation and troubleshooting tools

## 🖥️ System Requirements

### Minimum Requirements
- **macOS** 12+ or **Linux** (Ubuntu 20.04+, CentOS 8+)
- **Docker** 20.10+ with Docker Compose
- **4GB RAM** (8GB recommended)
- **10GB disk space**
- **Git** 2.30+
- **curl** for health checks

### Recommended Hardware
- **8GB RAM** for full installation
- **SSD storage** for better performance
- **Multi-core CPU** for parallel processing

## 🔑 API Key Setup Guide

Dopemux uses multiple AI services that require API keys. This step-by-step guide will help you create, fund, and configure all necessary API keys.

### Step 1: Anthropic Claude API Key

**Purpose**: Primary AI model for Claude Code integration and LiteLLM proxy

#### Create Account & Get API Key
1. **Go to**: [console.anthropic.com](https://console.anthropic.com/)
2. **Sign up**: Create account with email/password or Google/GitHub
3. **Verify email**: Check your inbox and click verification link
4. **Navigate to API Keys**: Click "API Keys" in left sidebar
5. **Create key**: Click "Create Key" button
6. **Name it**: "Dopemux Development" (or your preferred name)
7. **Copy key**: Save the key that starts with `sk-ant-`

#### Fund Your Account (Minimum $10)
1. **Go to Billing**: Click "Billing" in left sidebar
2. **Add payment method**: Click "Add payment method"
3. **Enter card details**: Add credit/debit card
4. **Set up auto-recharge**: Enable $10 auto-recharge when balance drops below $5
5. **Initial funding**: Add at least $10 to get started

#### Set Environment Variable
```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"

# Test it works
curl -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" \
  https://api.anthropic.com/v1/messages \
  -d '{"model": "claude-3-haiku-20240307", "max_tokens": 10, "messages": [{"role": "user", "content": "Hello"}]}'
```

### Step 2: OpenRouter API Key (Optional but Recommended)

**Purpose**: Cost-effective model access with fallback chains (Grok, GPT-4, etc.)

#### Create Account & Get API Key
1. **Go to**: [openrouter.ai](https://openrouter.ai/)
2. **Sign up**: Create account (can use same email as Anthropic)
3. **Verify email**: Check inbox and verify
4. **Go to Keys**: Click "Keys" in top navigation
5. **Create key**: Click "Create" button
6. **Name it**: "Dopemux LiteLLM" (or preferred name)
7. **Copy key**: Save the key (usually starts with `sk-or-v1-`)

#### Fund Your Account (Minimum $5)
1. **Go to Billing**: Click "Billing" in top navigation
2. **Add credits**: Click "Add Credits" or "Top Up"
3. **Enter amount**: Start with $5-10
4. **Payment**: Use card or crypto (crypto is often cheaper)
5. **Confirm**: Complete the transaction

#### Set Environment Variable
```bash
# Add to your shell profile
export OPENROUTER_API_KEY="sk-or-v1-your-key-here"

# Test it works
curl -X POST https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json"
```

### Step 3: xAI Grok API Key (Optional but Recommended)

**Purpose**: Free tier access to Grok models for cost optimization

#### Create Account & Get API Key
1. **Go to**: [console.x.ai](https://console.x.ai/)
2. **Sign up**: Create account with xAI (free)
3. **Verify**: Complete any verification steps
4. **Go to API Keys**: Navigate to API section
5. **Create key**: Generate new API key
6. **Copy key**: Save the key

#### Funding Note
- xAI provides free credits for development
- No payment required to get started
- Paid tiers available for higher limits

#### Set Environment Variable
```bash
# Add to your shell profile
export XAI_API_KEY="xai-your-key-here"
```

### Step 4: OpenAI API Key (Optional)

**Purpose**: Access to GPT-4 and GPT-3.5-turbo as fallback models

#### Create Account & Get API Key
1. **Go to**: [platform.openai.com](https://platform.openai.com/)
2. **Sign up**: Create OpenAI account
3. **Verify**: Complete phone verification
4. **Go to API Keys**: Click "API Keys" in left sidebar
5. **Create key**: Click "Create new secret key"
6. **Name it**: "Dopemux Development"
7. **Copy key**: Save the key (starts with `sk-`)

#### Fund Your Account (Minimum $5)
1. **Go to Billing**: Click "Billing" in left sidebar
2. **Add payment method**: Add credit card
3. **Set spending limit**: Start with $10-20
4. **Auto-recharge**: Optional but recommended

#### Set Environment Variable
```bash
# Add to your shell profile
export OPENAI_API_KEY="sk-your-key-here"
```

### Step 5: Voyage AI API Key (Required for Dope-Context)

**Purpose**: Vector embeddings for semantic search

#### Create Account & Get API Key
1. **Go to**: [voyageai.com](https://voyageai.com/)
2. **Sign up**: Create account
3. **Verify email**: Check inbox
4. **Go to Dashboard**: Navigate to API keys section
5. **Create key**: Generate new API key
6. **Copy key**: Save the key

#### Funding Note
- Free tier available for development
- Pay-as-you-go for production use

#### Set Environment Variable
```bash
# Add to your shell profile
export VOYAGE_API_KEY="pa-your-key-here"
```

### Step 6: Verify All Keys Are Set

Create a test script to verify all keys work:

```bash
#!/bin/bash
# test_api_keys.sh - Verify all API keys are working

echo "🔑 Testing API Keys..."
echo

# Test Anthropic
if [[ -n "$ANTHROPIC_API_KEY" ]]; then
    echo "Testing Anthropic..."
    if curl -s -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" \
        -d '{"model": "claude-3-haiku-20240307", "max_tokens": 1, "messages": [{"role": "user", "content": "Hi"}]}' \
        https://api.anthropic.com/v1/messages | grep -q "content"; then
        echo "✅ Anthropic: Working"
    else
        echo "❌ Anthropic: Failed"
    fi
else
    echo "⚠️ Anthropic: Not set"
fi

# Test OpenRouter
if [[ -n "$OPENROUTER_API_KEY" ]]; then
    echo "Testing OpenRouter..."
    if curl -s https://openrouter.ai/api/v1/auth/key \
        -H "Authorization: Bearer $OPENROUTER_API_KEY" | grep -q "data"; then
        echo "✅ OpenRouter: Working"
    else
        echo "❌ OpenRouter: Failed"
    fi
else
    echo "⚠️ OpenRouter: Not set"
fi

# Test Voyage
if [[ -n "$VOYAGE_API_KEY" ]]; then
    echo "Testing Voyage AI..."
    if curl -s -X POST https://api.voyageai.com/v1/embeddings \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $VOYAGE_API_KEY" \
        -d '{"input": ["test"], "model": "voyage-code-2"}' | grep -q "data"; then
        echo "✅ Voyage AI: Working"
    else
        echo "❌ Voyage AI: Failed"
    fi
else
    echo "⚠️ Voyage AI: Not set"
fi

echo
echo "💡 Tip: Add these exports to ~/.bashrc or ~/.zshrc to persist across sessions"
```

### Step 7: Cost Optimization Strategy

#### Recommended Key Priority (Cost-Effective)
1. **Anthropic** (Primary): Claude Sonnet 3.5 - Best quality/cost ratio
2. **OpenRouter** (Fallback): xAI Grok Code Fast - FREE for development
3. **OpenRouter** (Heavy lifting): GPT-4 via OpenRouter - Cheaper than direct
4. **xAI** (Free tier): Grok models - Good for experimentation

#### Monthly Budget Guidelines
- **Development**: $10-25/month (Anthropic + OpenRouter)
- **Light production**: $25-50/month
- **Full production**: $50-100+/month

#### Cost Monitoring
```bash
# Check usage (run periodically)
dopemux status  # Shows current session costs
openrouter.ai   # Usage dashboard
console.anthropic.com  # Billing dashboard
```

### Step 8: Security Best Practices

#### Key Management
- **Never commit API keys** to version control
- **Use environment variables** instead of hardcoding
- **Rotate keys regularly** (every 3-6 months)
- **Use different keys** for development vs production

#### Environment Setup
```bash
# Create .env file (add to .gitignore)
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-your-key
OPENROUTER_API_KEY=sk-or-v1-your-key
XAI_API_KEY=xai-your-key
OPENAI_API_KEY=sk-your-key
VOYAGE_API_KEY=pa-your-key
EOF

# Load environment variables
source .env
```

#### Troubleshooting API Issues
- **Rate limits**: OpenRouter has generous limits, Anthropic has lower limits
- **Invalid keys**: Double-check key format and no extra spaces
- **Network issues**: Try different regions or VPN
- **Billing problems**: Check account status and payment method

## 🖥️ **Terminal & CLI Tools Setup**

Dopemux is optimized for ADHD-friendly development workflows using advanced terminal tools. This section covers recommended CLI tools, shell configurations, and terminal optimizations.

### **Step 1: Choose Your Terminal**

#### **Kitty (Recommended)**
**ADHD Benefits**: GPU acceleration, fast rendering, smooth scrolling, excellent tmux integration

**Installation**:
```bash
# macOS
brew install kitty

# Ubuntu/Debian
curl -L https://sw.kovidgoyal.net/kitty/installer.sh | sh /dev/stdin

# Arch Linux
sudo pacman -S kitty

# Fedora/CentOS
sudo dnf install kitty
```

**Configuration** (`~/.config/kitty/kitty.conf`):
```bash
# ADHD-optimized Kitty config
font_family      Fira Code
font_size        12
scrollback_lines 10000

# Smooth scrolling for ADHD focus
enable_audio_bell no
visual_bell_duration 0.1

# GPU acceleration
linux_display_server auto

# Window management
remember_window_size  yes
initial_window_width  1400
initial_window_height 900

# Gruvbox-inspired colors (ADHD-friendly contrast)
background #282828
foreground #ebdbb2
color0     #282828  # black
color1     #cc241d  # red
color2     #98971a  # green
color3     #d79921  # yellow
color4     #458588  # blue
color5     #b16286  # magenta
color6     #689d6a  # cyan
color7     #a89984  # white
```

#### **Alternative Terminals**
- **Alacritty**: Fast GPU-accelerated terminal
- **WezTerm**: Lua-configurable with ADHD plugins
- **iTerm2**: macOS with tmux integration
- **GNOME Terminal/Konsole**: If you prefer desktop integration

### **Step 2: Install tmux**

**Purpose**: Multi-pane terminal sessions for ADHD workflow orchestration

**Installation**:
```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt install tmux

# Arch Linux
sudo pacman -S tmux

# Fedora/CentOS
sudo dnf install tmux
```

**Dopemux tmux Configuration** (`~/.tmux.conf`):
```bash
# Dopemux ADHD-optimized tmux config
set -g default-terminal "screen-256color"
set -g history-limit 10000
set -g status-interval 10  # ADHD-friendly refresh rate

# ADHD energy indicators in status bar
set -g status-left "#[bg=colour4,fg=colour15] #S #[bg=colour0,fg=colour4]#{?TMUX_ADHD_ENERGY, 🟢#{TMUX_ADHD_ENERGY}, ⚠️unknown} "
set -g status-right "#[bg=colour0,fg=colour3] Load: #{TMUX_ADHD_LOAD:-N/A} Dec: #{TMUX_CONPORT_DECISIONS:-0} #[bg=colour4,fg=colour15] #{TMUX_MODEL:-Model} (#{TMUX_CTX:-Ctx}) 🧠"

# Colors (Gruvbox-inspired)
set -g status-style bg=colour0,fg=colour7
setw -g window-status-style fg=colour4
setw -g window-status-current-style bg=colour4,fg=colour15,bold

# ADHD-friendly keybindings
bind-key r source-file ~/.tmux.conf \; display-message "Config reloaded"
bind-key h split-window -h  # Horizontal split
bind-key v split-window -v  # Vertical split
bind-key x kill-pane        # Close pane
bind-key & kill-window      # Close window

# Mouse support for ADHD workflow flexibility
set -g mouse on
```

**Quick tmux Commands**:
```bash
# Start new session
tmux new -s dopemux

# Attach to session
tmux a -t dopemux

# Split panes (from within tmux)
Ctrl-b %  # Vertical split
Ctrl-b "  # Horizontal split
Ctrl-b x  # Close pane

# Dopemux tmux integration
dopemux tmux start  # Launch Dopemux tmux layout
```

### **Step 3: Zsh + Oh My Zsh Setup**

**Purpose**: Advanced shell with plugins for ADHD workflow optimization

**Installation**:
```bash
# macOS (zsh comes pre-installed)
# Just install Oh My Zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Ubuntu/Debian
sudo apt install zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Set as default shell
chsh -s $(which zsh)
```

**Dopemux Zsh Configuration** (`~/.zshrc`):
```bash
# Oh My Zsh
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="agnoster"  # Clean, ADHD-friendly theme
plugins=(git docker tmux python node npm)

source $ZSH/oh-my-zsh.sh

# Dopemux environment variables
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENROUTER_API_KEY="your-openrouter-key"
export VOYAGE_API_KEY="your-voyage-key"
export XAI_API_KEY="your-xai-key"
export OPENAI_API_KEY="your-openai-key"

# ADHD-friendly aliases
alias d="dopemux"
alias ds="dopemux start"
alias dd="dopemux doctor"
alias dm="dopemux mobile start"
alias dl="dopemux status"

# Git shortcuts for ADHD workflow
alias gs="git status --short"
alias ga="git add"
alias gc="git commit -m"
alias gp="git push"
alias gl="git log --oneline -10"

# Python virtual environment helpers
alias venv="python -m venv"
alias act="source venv/bin/activate"
alias deact="deactivate"

# Tmux session management
alias tmd="tmux new -s dopemux"
alias tma="tmux a -t dopemux"
alias tmk="tmux kill-session -t dopemux"

# Directory navigation (ADHD-friendly)
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."

# Colorized output for better ADHD scanning
export CLICOLOR=1
export LSCOLORS=ExFxBxDxCxegedabagacad
```

### **Step 4: Starship Prompt**

**Purpose**: Fast, customizable shell prompt with ADHD-optimized information display

**Installation**:
```bash
# Install via package manager
curl -sS https://starship.rs/install.sh | sh

# Or via brew/npm
brew install starship
# npm install -g starship
```

**Configuration** (`~/.config/starship.toml`):
```toml
# Dopemux ADHD-optimized Starship config
format = """
[](color_orange)\
$os\
$username\
[](bg:color_yellow fg:color_orange)\
$directory\
[](fg:color_yellow bg:color_aqua)\
$git_branch\
$git_status\
[](fg:color_aqua bg:color_blue)\
$c\
$rust\
$golang\
$nodejs\
$php\
$java\
$kotlin\
$scala\
$haskell\
$python\
[](fg:color_blue bg:color_bg3)\
$docker_context\
$conda\
[](fg:color_bg3 bg:color_green)\
$time\
[ ](fg:color_green)\
"""

[directory]
style = "bg:color_yellow"
format = "[ $path ]($style)"
truncation_length = 3
truncation_symbol = "…/"

[git_branch]
symbol = ""
style = "bg:color_aqua"
format = '[[ $symbol $branch ](bg:color_aqua)]($style)'

[git_status]
style = "bg:color_aqua"
format = '[[($all_status$ahead_behind )](bg:color_aqua)]($style)'

[time]
disabled = false
time_format = "%R"  # Hour:Minute Format
style = "bg:color_green"
format = '[[ ♥ $time ](bg:color_green)]($style)'

# ADHD energy indicator (custom module)
[custom.adhd_energy]
disabled = false
command = "echo ${TMUX_ADHD_ENERGY:-medium} | tr '[:lower:]' '[:upper:]'"
when = true
style = "bg:color_purple"
format = '[[ ⚡ $output ](bg:color_purple)]($style)'

# Colors (Gruvbox-inspired)
[palette]
color_orange = "#fe8019"
color_yellow = "#fabd2f"
color_aqua = "#8ec07c"
color_blue = "#83a598"
color_green = "#b8bb26"
color_purple = "#d3869b"
color_bg3 = "#665c54"
```

**Add to your shell profile** (`~/.zshrc` or `~/.bashrc`):
```bash
# Starship prompt
eval "$(starship init zsh)"  # or bash
```

### **Step 5: Additional CLI Tools**

#### **fzf - Fuzzy Finder**
**ADHD Benefits**: Fast file/command finding, reduces decision paralysis

```bash
# Install
brew install fzf  # macOS
sudo apt install fzf  # Ubuntu

# Configure (add to ~/.zshrc)
source <(fzf --zsh)

# Usage examples
Ctrl-R    # Fuzzy command history
Ctrl-T    # Fuzzy file finder
Alt-C     # Fuzzy directory navigation
```

#### **ripgrep - Fast Text Search**
**ADHD Benefits**: Lightning-fast code search, instant results

```bash
# Install
brew install ripgrep  # macOS
sudo apt install ripgrep  # Ubuntu

# Usage (Dopemux uses this internally)
rg "function.*auth"  # Search for auth functions
rg --type py "class"  # Search Python classes only
```

#### **bat - Syntax Highlighted cat**
**ADHD Benefits**: Beautiful file viewing with syntax highlighting

```bash
# Install
brew install bat  # macOS
sudo apt install bat  # Ubuntu

# Configure as default cat replacement
alias cat="bat --theme=gruvbox-dark"

# Usage
bat README.md        # Syntax highlighted markdown
bat -l python main.py # Force Python syntax highlighting
```

#### **exa/lsd - Modern ls**
**ADHD Benefits**: Colorful, informative directory listings

```bash
# Install exa
brew install exa  # macOS
sudo apt install exa  # Ubuntu

# Or lsd (alternative)
brew install lsd

# Configure (add to ~/.zshrc)
alias ls="exa --icons --group-directories-first"
alias ll="exa --icons --group-directories-first -l"
alias la="exa --icons --group-directories-first -la"
```

#### **zoxide - Smart Directory Navigation**
**ADHD Benefits**: Learn your navigation patterns, jump to frequently used dirs

```bash
# Install
brew install zoxide  # macOS
sudo apt install zoxide  # Ubuntu

# Configure (add to ~/.zshrc)
eval "$(zoxide init zsh)"
alias cd="z"

# Usage
z dopemux    # Jump to most frequently used dir with "dopemux"
z -i dopemux # Interactive selection if multiple matches
```

#### **tldr - Simplified man pages**
**ADHD Benefits**: Quick, practical command examples instead of overwhelming man pages

```bash
# Install
brew install tldr  # macOS
sudo apt install tldr  # Ubuntu

# Usage
tldr curl      # Quick curl examples
tldr docker    # Practical docker commands
tldr git       # Essential git operations
```

### **Step 6: ADHD Workflow Optimization**

#### **Shell Functions** (`~/.zshrc` additions):
```bash
# ADHD-friendly work session management
function start_session() {
    echo "🧠 Starting ADHD-optimized development session..."
    tmux new -s "dopemux-$(date +%H%M)" -d
    dopemux start --role act
    tmux a -t dopemux
}

function end_session() {
    echo "💾 Saving session state..."
    dopemux save
    echo "✅ Session saved. Take a break! ☕"
}

# Quick status check
function dev_status() {
    echo "🔋 Energy Level: ${TMUX_ADHD_ENERGY:-unknown}"
    echo "🧠 Cognitive Load: ${TMUX_ADHD_LOAD:-unknown}"
    echo "📊 ConPort Decisions: ${TMUX_CONPORT_DECISIONS:-0}"
    echo "🤖 Active Model: ${TMUX_MODEL:-unknown}"
}

# ADHD break reminders
function break_timer() {
    local minutes=${1:-25}
    echo "⏰ ${minutes}-minute focus session starting..."
    sleep ${minutes}m
    echo "☕ Break time! Stretch, hydrate, look away from screen."
    echo "🔔 Reminder: ${minutes} minutes of focused work completed."
}
```

#### **Tmux ADHD Integration**:
```bash
# Environment variables for tmux status bar
export TMUX_ADHD_ENERGY="high"      # Set your current energy level
export TMUX_MODEL="Sonnet 4.5"      # Active AI model
export TMUX_CTX="1M"               # Context window size
```

### **Step 7: Testing Your Setup**

**Test Script** (`test_cli_setup.sh`):
```bash
#!/bin/bash
# Test CLI tools setup

echo "🧪 Testing CLI Tools Setup..."

# Test zsh
if command -v zsh &> /dev/null; then
    echo "✅ Zsh installed"
    if [[ "$SHELL" == *"zsh"* ]]; then
        echo "✅ Zsh is default shell"
    else
        echo "⚠️ Zsh not default shell (run: chsh -s $(which zsh))"
    fi
else
    echo "❌ Zsh not installed"
fi

# Test tmux
if command -v tmux &> /dev/null; then
    echo "✅ Tmux installed"
    if tmux list-sessions &> /dev/null; then
        echo "✅ Tmux working"
    else
        echo "⚠️ Tmux installed but may need configuration"
    fi
else
    echo "❌ Tmux not installed"
fi

# Test kitty
if command -v kitty &> /dev/null; then
    echo "✅ Kitty installed"
else
    echo "⚠️ Kitty not installed (optional but recommended)"
fi

# Test fzf
if command -v fzf &> /dev/null; then
    echo "✅ fzf installed"
else
    echo "⚠️ fzf not installed (optional)"
fi

# Test ripgrep
if command -v rg &> /dev/null; then
    echo "✅ ripgrep installed"
else
    echo "⚠️ ripgrep not installed (optional)"
fi

# Test bat
if command -v bat &> /dev/null; then
    echo "✅ bat installed"
else
    echo "⚠️ bat not installed (optional)"
fi

echo ""
echo "💡 Tip: Run 'exec zsh' to reload your shell configuration"
```

### **Troubleshooting CLI Setup**

#### **Tmux Issues**
```bash
# Check tmux version
tmux -V

# Reload config
tmux source-file ~/.tmux.conf

# Kill all sessions and restart
tmux kill-server
tmux new -s test
```

#### **Zsh Issues**
```bash
# Check zsh version
zsh --version

# Reload configuration
source ~/.zshrc

# Debug Oh My Zsh
zsh -c "source ~/.oh-my-zsh/oh-my-zsh.sh"
```

#### **Starship Issues**
```bash
# Test starship
starship --version

# Debug prompt
starship explain
```

#### **Kitty Issues**
```bash
# Test kitty
kitty --version

# Check config syntax
kitty --config ~/.config/kitty/kitty.conf
```

### **ADHD Benefits of This Setup**

- **Reduced Cognitive Load**: Tools present information progressively, not overwhelming
- **Visual Hierarchy**: Color coding and symbols for quick scanning
- **Session Persistence**: tmux maintains context across interruptions
- **Smart Navigation**: zoxide and fzf learn your patterns
- **Status Awareness**: Real-time energy and load indicators
- **Flexible Workflows**: Multiple terminal layouts for different focus states

This terminal environment transforms raw command-line work into an ADHD-optimized development experience! 🚀

## 🚀 Post-Installation Setup

### Start Your Development Session

```bash
# Start Dopemux development environment
dopemux start

# Or start with specific role
dopemux start --role act        # Implementation mode
dopemux start --role plan       # Planning mode
dopemux start --role research   # Research mode
```

### Verify Everything Works

```bash
# Check system status
dopemux status

# Run health checks
dopemux doctor

# Your statusline should show:
# dopemux-mvp main | 📊 Ready for development | 🧠 ⚡= 👁️● 🛡️ | 0K/200K (0%) | Sonnet 4.5
```

### Configure Your First Session

```bash
# Set your current focus
mcp__conport__update_active_context \
  --workspace_id "$(pwd)" \
  --patch_content '{
    "current_focus": "Getting started with Dopemux",
    "session_start": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'
```

## 🎨 Statusline Features

Once installed, your Claude Code statusline shows:

```
dopemux-mvp main | 📊 current_task | 🧠 ⚡level 👁️state 🛡️ | tokens% | model
```

### Statusline Components

| Component | Meaning | ADHD Benefit |
|-----------|---------|--------------|
| **Directory** | Current project | Quick orientation |
| **Git Branch** | Active branch | Avoid confusion |
| **Connection** | ConPort status | Context preservation |
| **Focus** | Current task | Stay on track |
| **Time** | Session duration | Break awareness |
| **Energy** | Cognitive energy | Match tasks to energy |
| **Attention** | Focus state | Self-awareness |
| **Token Usage** | Context window | Prevent autocompact |
| **Model** | Active AI model | Context awareness |

## 🔧 Manual Setup (Alternative)

If the installer doesn't work, you can set up manually:

### 1. Install Prerequisites

```bash
# macOS
brew install docker docker-compose curl git

# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose curl git

# Start Docker
sudo systemctl start docker  # Linux
# Or launch Docker Desktop  # macOS
```

### 2. Start Core Services

```bash
# Start all platform services and infrastructure
./scripts/start-all-mcp-servers.sh

# Or via Dopemux CLI
dopemux mcp up --all
```

### 3. Initialize Services

```bash
# Initialize ConPort
mcp__conport__get_active_context --workspace_id "$(pwd)"

# Start ADHD Engine
cd services/adhd_engine/services/adhd_engine
ADHD_ENGINE_API_KEY=dev-key-123 ALLOWED_ORIGINS=http://localhost:3000 \
  nohup python -m uvicorn main:app --host 0.0.0.0 --port 8095 &
cd -

# Index code and docs
mcp__dope-context__index_workspace --workspace_path "$(pwd)"
```

### 4. Configure Claude Code

```bash
# Install Claude Code Router
./scripts/install_claude_code_router.sh

# Configure statusline
mkdir -p ~/.claude
cat > ~/.claude/settings.json << EOF
{
  "statusline": {
    "command": "bash $(pwd)/.claude/statusline.sh"
  }
}
EOF
```

## 🐛 Troubleshooting

### Common Issues

#### Docker Services Won't Start
```bash
# Check Docker status
docker info

# Restart Docker
sudo systemctl restart docker  # Linux
# Or restart Docker Desktop  # macOS

# Clean up and retry
docker-compose -f docker-compose.unified.yml down
docker system prune -f
docker-compose -f docker-compose.unified.yml up -d
```

#### Port Conflicts
```bash
# Check what's using ports
lsof -i :8095  # ADHD Engine
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Change ports in docker-compose.unified.yml if needed
```

#### Permission Issues
```bash
# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
# Log out and back in, or run: newgrp docker

# Fix script permissions
chmod +x install.sh
chmod +x scripts/*.sh
```

#### Statusline Not Showing
```bash
# Check statusline script exists
ls -la .claude/statusline.sh

# Verify Claude Code settings
cat ~/.claude/settings.json

# Restart Claude Code
# The statusline should appear after next command
```

#### Services Not Responding
```bash
# Check service health
curl http://localhost:8095/health  # ADHD Engine
curl http://localhost:3004/health  # ConPort

# Restart services
docker-compose -f docker-compose.unified.yml restart

# Check logs
docker logs dopemux-adhd-engine
docker logs mcp-conport
```

### Getting Help

```bash
# Run diagnostic
dopemux doctor

# Check system status
dopemux status

# View logs
tail -f install.log
docker-compose -f docker-compose.unified.yml logs -f
```

## 🔄 Updating Dopemux

```bash
# Pull latest changes
git pull origin main

# Update services
docker-compose -f docker-compose.unified.yml pull
docker-compose -f docker-compose.unified.yml up -d

# Re-index if needed
mcp__dope-context__sync_workspace --workspace_path "$(pwd)"
```

## 🧹 Uninstalling

```bash
# Stop and remove services
docker-compose -f docker-compose.unified.yml down -v

# Remove configurations (optional)
rm -rf ~/.claude ~/.dopemux

# Remove repository
cd ..
rm -rf dopemux-mvp
```

## 📚 Additional Resources

- **[README.md](README.md)** - Feature overview and usage guide
- **[docs/INDEX.md](docs/INDEX.md)** - Complete documentation index
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates
- **[scripts/](scripts/)** - Additional utility scripts

## 🙏 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run `dopemux doctor` for diagnostics
3. Check the [GitHub Issues](https://github.com/your-org/dopemux-mvp/issues) for known problems
4. Create a new issue if your problem isn't documented

---

**Made with ❤️ for developers with ADHD, by developers with ADHD**</content>
</xai:function_call name="Write">
<parameter name="file_path">.claude/statusline.sh
