

# Dopemux MVP — Cognitive Ops Stack
![Version](https://img.shields.io/badge/version-0.1.0-blue) ![Python](https://img.shields.io/badge/python-3.10+-green) ![License](https://img.shields.io/badge/license-MIT-lightgrey) ![PyPI](https://img.shields.io/badge/pypi-dopemux-blue) ![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey)

---

## Table of Contents

- [Why Dopemux?](#why-dopemux)
- [Project Name and Description](#project-name-and-description)
- [Quick Start](#quick-start)
- [dopeTask Kernel Integration](#dopetask-kernel-integration)
- [Technology Stack](#technology-stack)
- [Project Architecture](#project-architecture)
- [Project Structure](#project-structure)
- [Key Features](#key-features)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Contributing](#contributing)
- [Security](#security)
- [Community & Support](#community--support)
- [License](#license)
- [FAQ & Troubleshooting](#faq--troubleshooting)
- [Further Reading](#further-reading)

---

## Why Dopemux?

Dopemux is built for developers who want to maximize focus, context retention, and productivity—especially those with ADHD or who thrive on ritualized workflows. It provides:

- Persistent, context-rich development sessions
- Real-time cognitive and project state awareness
- Seamless multi-workspace management
- Adaptive accommodations for energy and attention
- A consent-first, developer-centric experience

If you want your terminal, services, and dashboard to work together to keep you in flow, Dopemux is for you.

---


## Project Name and Description

**Dopemux MVP** is an ADHD-aware cognitive ops stack for developers. It unifies a Python CLI/library, FastAPI service fleet, Next.js dashboard, and multi-workspace architecture to deliver persistent context, adaptive workflows, and real-time statusline awareness. Dopemux is designed for focus, context retention, and developer ritual.

> See the [DØPEMÜX Brand System](docs/branding/DØPEMUX_BRAND_SYSTEM.md) for the full aesthetic and UX contract.

---

## Quick Start

**For detailed installation instructions, see [docs/04-installation.md](docs/04-installation.md).**

```bash
# 1. Clone repository
git clone https://github.com/DDD-Enterprises/dopemux-mvp
cd dopemux-mvp

# 2. Install dependencies (single source of truth)
python -m pip install --upgrade pip
pip install -e ".[dev]"
pre-commit install --install-hooks

# 3. Generate workspace configs and set up environment
python scripts/render_workspace_configs.py --set-default
source "$(python scripts/workspace_env_path.py)"

# 4. Start services
docker compose -f docker-compose.smoke.yml up --build -d
python tools/ports_health_audit.py --mode runtime --services conport,task-orchestrator,dopecon-bridge

# 5. Run CLI
dopemux --help
```

See [docs/04-installation.md](docs/04-installation.md), [INSTALL.md](INSTALL.md), and [QUICK_START.md](QUICK_START.md) for more.

---

## dopeTask Kernel Integration

Dopemux consumes dopeTask via pip installation and wrapper (`scripts/dopetask`).

```bash
scripts/dopetask --version
dopemux kernel doctor --timestamp-mode deterministic
```

- Runtime and CI use pip installation.
- `.dopetask-pin` is used for runtime/CI behavior.
- Use `dopemux kernel <lifecycle-command>` for kernel lifecycle operations.

See [docs/DOPETASK_KERNEL_INTEGRATION.md](docs/DOPETASK_KERNEL_INTEGRATION.md) for the full contract and update/rollback process.

---


## Technology Stack

- **Python** 3.10+ ([pyproject.toml](pyproject.toml))
- **FastAPI** (service APIs)
- **Next.js** (dashboard UI, [ui-dashboard/](ui-dashboard/))
- **Docker Compose** (service orchestration)
- **PostgreSQL AGE** (graph backend)
- **Redis** (event bus)
- **tmux, jq, curl, sqlite3** (tooling)
- **Pytest, Ruff, Black, isort, mypy** (testing/linting)

See [pyproject.toml](pyproject.toml), [requirements.txt](requirements.txt), and [package.json](package.json) for full dependency details.

---


## Project Architecture

Dopemux uses a two-plane architecture:

- **Project Management Plane**: Leantime, Task-Master, Task-Orchestrator (task/project authority)
- **Cognitive Plane**: Serena LSP, ConPort Knowledge Graph, ADHD Engine (context, reasoning, energy)
- **DopeconBridge**: Integration gateway for cross-plane event routing and authority enforcement

All cross-service communication is event-driven (Redis PubSub), and shared schemas are reused from [services/shared/src/dopemux_services_shared](services/shared/src/dopemux_services_shared). Service registry and entrypoints are defined in [services/registry.yaml](services/registry.yaml).

> **Diagram:**
> ![Architecture Diagram Placeholder](docs/04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md)

See [Architecture Overview](docs/04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md) and [System Bible](docs/94-architecture/system-bible.md) for diagrams and details.

---

## Getting Started

### Prerequisites
- Python 3.10+
- Git 2.30+
- Docker 20.10+ (recommended)
- tmux, jq, curl, sqlite3

### Installation

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .[dev]
pre-commit install --install-hooks
```

Generate workspace configs and set up your environment:

```bash
python scripts/render_workspace_configs.py --set-default
source "$(python scripts/workspace_env_path.py)"
```

Start the smoke stack and audit services:

```bash
docker compose -f docker-compose.smoke.yml up --build -d
python tools/ports_health_audit.py --mode runtime --services conport,task-orchestrator,dopecon-bridge
```

See [INSTALL.md](INSTALL.md) and [QUICK_START.md](QUICK_START.md) for more.

---


## Project Structure

- **src/dopemux/**: Core CLI, library, canonical clients
- **services/**: FastAPI services (task orchestrator, working-memory-assistant, etc.)
- **ui-dashboard/**: Next.js dashboard UI
- **tools/**: Build, audit, and migration scripts
- **docs/**: Architecture, engineering rituals, branding
- **tests/**: Unit, contract, and smoke tests
- **reports/**: Coverage, build matrix, inventories
- **docker-compose.*.yml**: Stack definitions
- **pyproject.toml, requirements.txt**: Python dependencies

See [docs/03-reference/00-repo-map.md](docs/03-reference/00-repo-map.md) for a full map.

---


## Key Features

- **CLI**: Python-based, terminal-native, ADHD-optimized statusline
- **Services**: FastAPI microservices for context, orchestration, and knowledge graph
- **Dashboard**: Next.js UI for visualizing context, energy, and project state
- **Persistent ConPort knowledge graph** and decision log
- **DopeconBridge** for cross-plane event routing
- **Adaptive energy and attention tracking** (ADHD Engine)
- **Smart break reminders and hyperfocus protection**
- **Multi-workspace support** with complete data isolation
- **Autonomous code/docs semantic search** (dope-context)
- **Unified ConPort client and multi-session support**
- **Mobile mode with Happy client**

> **Screenshot/Diagram Placeholder:**
> ![Dashboard Screenshot Placeholder](docs/SCREENSHOT_DASHBOARD_PLACEHOLDER.png)

---


## Development Workflow


**Contributor Checklist:**

- [ ] Use `dopemux worktree` for isolated git worktrees (no direct edits to main branches)
- [ ] Install requirements and pre-commit hooks before running lint/tests
- [ ] Run `python tools/quick_checks.py fast|ci|contracts|smoke` for tiered validation
- [ ] Ensure 80%+ coverage (see pytest.ini)
- [ ] Use workflows in `.github/workflows/` for CI, security, and coverage
- [ ] Update `services/registry.yaml` and compose files together for service changes
- [ ] Run `python tools/docker_build_matrix.py --mode build --scoreboard` after Docker/service edits
- [ ] Update reports/docs after tool outputs change
- [ ] Never commit secrets or env files

See [docs/engineering/refactor_gates.md](docs/engineering/refactor_gates.md) for migration/refactor checklists.

---


## Coding Standards

- Mirror style and structure from `src/dopemux/`, `services/*`, and `tests/`
- Preserve architectural boundaries: core logic in `src/dopemux/`, services in `services/`, UI in `ui-dashboard/`
- Use canonical clients from `src/dopemux/clients/`
- Follow event-driven patterns and shared schemas
- No cross-layer imports; respect boundaries enforced by `tests/arch/`
- Run `pre-commit run --all-files` before PRs

See [copilot-instructions.md](.github/copilot-instructions.md) for more.

---


## Testing

- **Unit tests**: `pytest -q` (see `tests/unit/`)
- **Contract tests**: `pytest tests/contracts/`
- **Smoke tests**: `python tools/quick_checks.py smoke`
- **Coverage**: 80% minimum enforced by `pytest.ini`
- **Linting/Typecheck**: `pre-commit run --all-files` (includes ruff, black, isort, mypy)

See [docs/03-reference/03-testing.md](docs/03-reference/03-testing.md) for full details.

---


## Contributing

Contributions are welcome. Start with the repository contribution guide:

- [Contributing Guide](.github/CONTRIBUTING.md)
- [Pull Request Template](.github/pull_request_template.md)
- [Code Owners](.github/CODEOWNERS)

Follow code exemplars in `src/dopemux/`, `services/`, and `tests/`. For repository-specific AI/automation instructions, see [copilot-instructions.md](.github/copilot-instructions.md).

---

## Security

Use private disclosure for vulnerabilities:

- [Security Policy](.github/SECURITY.md)
- [Report a Vulnerability](https://github.com/DDD-Enterprises/dopemux-mvp/security/advisories/new)

---

## Community & Support

- [Support Guide](.github/SUPPORT.md)
- [GitHub Issues](https://github.com/DDD-Enterprises/dopemux-mvp/issues) — Bug reports and feature requests
- [Issue Templates](.github/ISSUE_TEMPLATE/) — Standardized bug/feature intake
- [Code of Conduct](.github/CODE_OF_CONDUCT.md)

---


## License

MIT License — see [LICENSE](LICENSE) for details.

---

## FAQ & Troubleshooting

**Q: Statusline shows 📴 disconnected?**
A: ConPort database not accessible. Check `context_portal/context.db` exists, or initialize with `mcp__conport__get_active_context --workspace_id $(pwd)`.

**Q: Session time not showing?**
A: Invalid session_start timestamp. Reset with `mcp__conport__update_active_context --workspace_id $(pwd) --patch_content '{"session_start": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"}'`.

**Q: ADHD Engine shows 💤?**
A: Service not running. Start with `cd services/adhd-engine && uvicorn main:app --port 8095 --reload`.

**Q: Coverage below 80%?**
A: Rerun tests with `pytest -q` and check `coverage.xml` for gaps.

**Q: Docker build hangs?**
A: Run `docker builder prune` before `python tools/docker_build_matrix.py --mode build --scoreboard`.

For more, see [Troubleshooting Guide](docs/troubleshooting/workspaces.md).

---


## Further Reading

- [Documentation Index](docs/INDEX.md)
- [Architecture Overview](docs/04-explanation/architecture/DOPEMUX_ARCHITECTURE_OVERVIEW.md)
- [ConPort Technical Deep Dive](docs/04-explanation/conport-technical-deep-dive.md)
- [Serena LSP Deep Dive](docs/04-explanation/serena-v2-technical-deep-dive.md)
- [ADHD Engine](docs/ADHD-ENGINE-DEEP-DIVE-PART1.md)
- [Multi-Workspace Guide](MULTI_WORKSPACE_IMPLEMENTATION_GUIDE.md)
- [Changelog](CHANGELOG.md)

### Quick Multi-Workspace Setup

```bash
# Set your default workspace
export DEFAULT_WORKSPACE_PATH=~/code/dopemux-mvp

# Work with a specific workspace
dopemux --workspace ~/code/my-project init

# Query across multiple workspaces
dopemux query --workspaces ~/code/project1,~/code/project2 "recent decisions"

# Switch workspaces in active session
dopemux workspace switch ~/code/another-project
```

### Workspace Isolation Features

✅ **Complete Data Isolation**
- Cognitive state tracked separately per workspace
- Knowledge graphs don't cross-contaminate
- Session history isolated by workspace

✅ **Cross-Workspace Queries**  
- Search decisions across all your projects
- Aggregate insights from multiple workspaces
- Compare patterns between workspaces

✅ **Smart Context Switching**
- Auto-detect workspace from current directory
- Visual workspace indicator in statusline
- Gentle reminders when switching workspaces

See [Multi-Workspace Guide](#multi-workspace-usage) for detailed usage.

---

## 📐 Engineering Rituals

Every migration PR must tick the [Refactor Gates](docs/engineering/refactor_gates.md) checklist before reviewers are invited. It freezes the HTTP contract, verifies containers, and defends the boundary layers so refactors stay predictable.

### Testing

Dopemux uses a tiered testing approach for fast feedback and CI parity:

**Quick testing commands:**
```bash
python tools/quick_checks.py fast        # Tier 0: Fast checks (< 2 min) - arch + unit
python tools/quick_checks.py ci          # Tier 1: CI parity (5-10 min) - full validation
python tools/quick_checks.py contracts   # Tier 2: Contract tests (requires services)
python tools/quick_checks.py smoke       # Tier 3: Full smoke stack (10-15 min)
```

**See [Testing Guide](docs/03-reference/03-testing.md) for complete tier definitions, CI workflow stages, and troubleshooting.**

---

## 📦 Installation

### Quick Install (Recommended)

**PyPI (Python Package)**
```bash
pip install dopemux
```

**Homebrew (macOS)**
```bash
brew install dopemux/tap/dopemux
```

**Universal Installer (All Platforms)**
```bash
curl -fsSL https://raw.githubusercontent.com/dopemux/dopemux-mvp/main/install.sh | bash
```

### Requirements

- **Python:** 3.10 or higher (3.8+ supported in package)
- **Git:** 2.30 or higher
- **Docker:** 20.10 or higher (optional but recommended)
- **tmux, jq, curl, sqlite3**

### Platform Support

| Platform | Status | Installation Method |
|----------|--------|---------------------|
| macOS (Apple Silicon) | ✅ Tested | Homebrew, PyPI, Installer |
| macOS (Intel) | ✅ Supported | Homebrew, PyPI, Installer |
| Ubuntu 22.04+ | ✅ Tested | PyPI, Installer |
| Arch Linux | ✅ Supported | PyPI, Installer |
| Fedora 39+ | ✅ Supported | PyPI, Installer |

**Quick Start:**
```bash
dopemux --version    # Verify installation
dopemux doctor       # Run health check
dopemux init         # Initialize in project
```

### 🎨 Terminal Environment Setup (Optional)

Get an ADHD-optimized terminal with Kitty, zsh, Starship, and productivity tools:

```bash
./install.sh --terminal
```

Includes: GPU-accelerated terminal, modern shell, beautiful prompt, fzf, ripgrep, bat, and more.  
See [Terminal Setup Guide](docs/TERMINAL_SETUP.md) for details.

For detailed instructions, see [INSTALL.md](INSTALL.md)

---

## 🖥️ The Statusline - Your Development HUD

The Dopemux statusline provides instant visibility into your development context without requiring mental effort:

### 🌟 Complete Statusline Display (All Fields)

```
dopemux-mvp main | ✅ Implementing auth system [2h 15m] | 🧠 ⚡= 👁️● 🛡️ ☕ | 128K/200K (64%) | Sonnet 4.5
```

**Full breakdown with ALL possible fields:**

| Position | Component | Example | What It Shows | Why It Matters |
|----------|-----------|---------|---------------|----------------|
| 1️⃣ | **Directory** 📁 | `dopemux-mvp` | Current working directory | Quick context anchor |
| 2️⃣ | **Git Branch** 🌿 | `main` or `feature/auth` | Active git branch | Know what branch you're on |
| 3️⃣ | **Connection** 🔗 | 📊 or 📴 | ConPort knowledge graph status | Your context is (not) preserved |
| 4️⃣ | **Current Focus** 🎯 | `Implementing auth system` | What you're working on right now | No need to remember your task |
| 5️⃣ | **Session Time** ⏱️ | `[2h 15m]` | Time since session start | Gentle time awareness |
| 6️⃣ | **Energy Level** ⚡ | `High ↑` or `Medium •` | Current cognitive energy state | Match tasks to your energy |
| 7️⃣ | **Attention State** 👁️ | `Focused 👁️` or `Scattered 👁️🌀` | How focused you are right now | Self-awareness support |
| 8️⃣ | **Accommodations** 🛡️ | `🛡️` (optional) | Hyperfocus protection active | Flow state protected |
| 9️⃣ | **Break Warning** ☕ | ☕ or ☕! (optional) | Break needed (soon/urgently) | Prevent burnout |
| 🔟 | **Token Usage** 📊 | `128K/200K (64%)` | Context window usage (raw + %) | Avoid surprise autocompact |
| 1️⃣1️⃣ | **Active Model** 🤖 | `Sonnet 4.5` | Which Claude model is active | Context window awareness |

### 🎨 What Each Component Looks Like

#### 📁 Directory & 🌿 Branch

```
dopemux-mvp main
dopemux-mvp feature/auth-system
my-project bugfix/login-redirect
```

#### 🔗 Connection Status

| Display | Meaning | Your Action |
|---------|---------|-------------|
| 📊 | **Connected** - ConPort active | ✅ Work freely, context preserved |
| 📴 | **Disconnected** - ConPort offline | ⚠️ Fix ConPort, context at risk |

#### 🎯 Current Focus (max 35 chars)

```
📊 Implementing JWT tokens
📊 Debugging production login i...
📊 Code review - auth module
```

#### ⏱️ Session Time

```
[15m]           → Under 1 hour
[1h 23m]        → Over 1 hour
[3h 45m]        → Long session (watch for breaks!)
```

#### ⚡ Energy Levels

| Display | State | Best For 🎯 |
|---------|-------|-------------|
| **⚡⚡** | Hyperfocus - Peak energy | 🔥 Complex architecture, deep debugging, system design |
| **⚡↑** | High - Above baseline | 🚀 New features, challenging problems, learning |
| **⚡=** | Medium - Balanced/level | 💻 Regular development, bug fixes, testing |
| **⚡↓** | Low - Below baseline | 📝 Documentation, simple edits, code review |
| **⚡⇣** | Very Low - Depleted | 🛑 **TAKE A BREAK!** |

#### 👁️ Attention States

| Display | State | What It Means | Your Action 💡 |
|---------|-------|---------------|----------------|
| **👁️✨** | Hyperfocused - Deep flow | 🎉 Celebrate! Protect this precious state |
| **👁️●** | Focused - On task | ✅ Keep going, you're productive |
| **👁️~** | Transitioning - Shifting | 🌊 Be gentle, allow the shift |
| **👁️🌀** | Scattered - Fragmented | 🎯 Simplify current task, reduce complexity |
| **👁️💥** | Overwhelmed - Overload | 🚨 **STOP! Break time NOW** |

#### 🛡️ Accommodations (Optional)

| Symbol | Meaning | Effect |
|--------|---------|--------|
| 🛡️ | Hyperfocus protection | 🔕 Interruptions minimized, warnings delayed |

#### ☕ Break Warnings (Optional)

| Display | Urgency | What To Do 🎯 |
|---------|---------|----------------|
| ☕ (yellow) | **Soon** - within 10-15 min | ✋ Finish current task, then 5-min break |
| ☕! (red) | **NOW** - immediately | 🛑 **STOP EVERYTHING** - 15-min break minimum |

### Token Usage Tracking

**Never lose work to surprise autocompact:**

- 🟢 **0-60%** (Green) - Plenty of context, work freely
- 🟡 **60-80%** (Yellow) - Context filling up, wrap up soon
- 🔴 **80-100%** (Red) - Near autocompact, save decisions now

**Real-time calculation:**

- Parses Claude Code transcript file for actual usage
- Shows both raw tokens and percentage: `128K/200K (64%)`
- Auto-adapts to all Claude models (Opus 200K, Sonnet 200K/1M, Haiku 200K)

[📖 Full Statusline Documentation](./docs/INDEX.md)

---

## 🚀 Quick Start

### Prerequisites

- **Claude Code** - CLI interface for Claude AI
- **Python 3.11+** - For ADHD Engine and services
- **Docker** - For ConPort and MCP servers
- **jq, sqlite3** - For statusline parsing

### Installation

```bash
# 1. Clone repository
git clone https://github.com/DDD-Enterprises/dopemux-mvp
cd dopemux-mvp

# 2. Generate workspace-aware configs (one-time per clone)
python3 scripts/render_workspace_configs.py --set-default

# 3. Load the env for this shell (or add to your shell profile)
source "$(python3 scripts/workspace_env_path.py)"

# 4. Start core services (reads DOPEMUX_* from the sourced env)
docker-compose -f docker-compose.unified.yml up -d

# 5. Configure statusline in Claude Code settings
{
  "statusline": {
    "command": "bash $(pwd)/.claude/statusline.sh"
  }
}

# 6. Initialize your first session
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{
    \"current_focus\": \"Setting up Dopemux\",
    \"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
  }"
```

### Claude Code Router integration

```bash
# Install claude-code-router and Claude Code CLIs globally
./scripts/install_claude_code_router.sh

# Start Dopemux with LiteLLM routing (Claude → grok-code-fast-1 → gpt-5)
dopemux start --litellm

# Start Dopemux with Claude OAuth (default; no LiteLLM)
dopemux start
```

- Dopemux automatically provisions a dedicated Claude Code Router home under
  `.dopemux/claude-code-router/<instance>` so multi-instance sessions never
  fight over a shared `~/.claude-code-router` directory.
- If you are routing to a custom upstream without LiteLLM, export the following
  before `dopemux start`:
  - `CLAUDE_CODE_ROUTER_UPSTREAM_URL` – full `/v1/chat/completions` endpoint
  - `CLAUDE_CODE_ROUTER_UPSTREAM_KEY` – API key if required
- `CLAUDE_CODE_ROUTER_MODELS` – comma-separated model names (e.g. `deepseek-chat,deepseek-reasoner`)
- Use `--no-claude-router` if you need to fall back to direct Anthropics access.

💡 **Multi-workspace tip:** running `python3 scripts/render_workspace_configs.py` inside any clone creates `~/.dopemux/workspaces/<slug>/env`. Source that file before starting Dopemux so Docker containers, MCP proxies, and scripts share the correct `DOPEMUX_WORKSPACE_*` variables per clone.

### Role-aware launch

Trim Claude’s tool set to match your attention state:

```bash
# Preview the QUICKFIX mode (scattered attention, 3 tools)
dopemux start --role quickfix --dry-run

# Launch in implementation mode (ACT)
dopemux start --role act

# Strategic planning dashboard
dopemux start --role plan

# Retarget the primary agent pane from the orchestrator session
dopemux tmux agent switch-role act
```

The CLI rewrites `~/.claude/settings.json`, sets `DOPEMUX_AGENT_ROLE`, and warns if any required MCP services are offline (with suggested `dopemux mcp ...` commands to start them). Inside the orchestrator tmux session you can retarget agent panes on demand with `dopemux tmux agent switch-role ...`.

Supported personas: `quickfix`, `act`, `plan`, `research`, `all`, `developer`, `architect`, `reviewer`, `debugger`, and `ops` (legacy aliases such as `orchestrator`/`agent` continue to work).

Note on authentication modes:
- Default (`dopemux start`): Claude Code uses OAuth (Claude Pro/Max). No API key passed to the app.
- With `--litellm`: Dopemux runs a local LiteLLM proxy and sets `ANTHROPIC_API_BASE`/`ANTHROPIC_API_KEY`
  for Claude Code to talk to the proxy. Requests try `claude-sonnet-4.5` first and automatically
  fall back to `xai/grok-code-fast-1` (and `openai/gpt-5` if configured). Set `XAI_API_KEY` (recommended)
  and/or `OPENAI_API_KEY` in your shell before starting.

### ConPort + Dope Decision Graph (Automatic Wiring)

- Project‑level ConPort is auto‑wired into `.claude/claude_config.json` on `dopemux start` and on `scripts/stack_up_all.sh`.
- A git `post-checkout` hook is installed to wire new worktrees automatically.
- ConPort uses stdio via `docker exec` targeting the instance container `mcp-conport[_<instance>]`.
- Global MCP servers (Zen, MAS, Context7, Exa, Serena, Leantime Bridge, Task Orchestrator, GPT Researcher) are wired into Claude Desktop globally.

Read more: `docs/WORKTREES_AND_DECISION_GRAPH.md`.

### Verify Setup

Your statusline should now show:

- 📊 Connected to ConPort
- 🎯 "Setting up Dopemux" as current focus
- ⏱️ Session time counting up
- 🧠 Energy and attention indicators (if ADHD Engine running)
- 📈 Token usage tracking

---

## 📚 Core Components

### DopeconBridge - Integration Gateway

**Single coordination point for all cross-plane communication:**

- **Event Streaming** - Redis-backed EventBus for real-time updates
- **Cross-Plane Routing** - PM ↔ Cognitive plane coordination
- **KG Access** - Centralized ConPort/Decision Graph gateway
- **Custom Data** - Workspace-scoped key-value persistence
- **Security** - Token-based auth, plane isolation

**Architecture:**
- PM Plane: Leantime, Task-Master, Taskmaster → Owns tasks/projects
- Cognitive Plane: ADHD Engine, Serena, GPT-Researcher → Owns context/reasoning
- DopeconBridge: Single choke point between planes

**No service** should access ConPort DB or Redis directly - all via DopeconBridge.

[📖 DopeconBridge Documentation](./DOPECONBRIDGE_COMPLETE_INTEGRATION.md)

### ConPort Knowledge Graph

**Persistent memory system for development context (accessed via DopeconBridge):**

- **Product Context** - Project goals, architecture, tech stack
- **Active Context** - Current focus, session state, recent changes
- **Decision Log** - Architectural decisions with rationale
- **Progress Tracking** - Task hierarchies with ADHD metadata
- **System Patterns** - Reusable coding patterns and best practices
- **Knowledge Graph** - Relationships between decisions, tasks, patterns

**Key Features:**

- PostgreSQL AGE backend for graph operations
- Full-text and semantic search
- Session continuity across interruptions
- Decision genealogy tracking
- All access via DopeconBridge for consistency

[📖 ConPort Documentation](./docs/04-explanation/conport-technical-deep-dive.md)

### ADHD Engine - 11 Cognitive Accommodation Features

**Complete ADHD support system with ML-powered insights:**

#### Core Features (Phase 3)
1. **ML Energy Pattern Learning** - Predicts optimal work times from 2+ weeks of data
2. **Context Preservation** - Auto-saves mental model before breaks for effortless resume
3. **Attention Calibration** - Learns YOUR focus patterns through feedback
4. **Correlation Engine** - Discovers hidden productivity patterns across all services
5. **Voice Assistant** - Hands-free status queries ("How's my focus?")
6. **Mobile Push** - Break reminders on phone (Ntfy free, Pushover paid)

#### Quick Win Features (NEW)
7. **Overwhelm Circuit Breaker** - 5 overwhelm signals → scaled interventions (check-in → forced break)
8. **Hyperfocus Protection** - Auto-saves every 5min, gentle reminders at 90/120min, crash detection
9. **End-of-Day Wind Down** - 7-step ritual: stats → wins → thoughts → tomorrow prep → recovery
10. **Weekly Pattern Report** - Friday analysis with best focus windows + personalized recommendations
11. **Procrastination Detection** - Detects 5 patterns (research rabbit holes, task switching, etc.) → gentle micro-tasks

**How it helps:**

- Prevents overwhelm cascades and burnout crashes
- Protects deep work while preventing exhaustion
- Reduces next-day anxiety with structured closures
- Data-driven improvements from weekly insights
- Non-judgmental procrastination interventions
- Learns and adapts to your unique patterns

[📖 ADHD Features User Guide](./docs/02-how-to/adhd-features-user-guide.md) | [📖 API Reference](./docs/03-reference/adhd-engine-api.md) | [📖 Technical Documentation](./services/adhd_engine/README.md)

### Dope-Context - Semantic Search (NEW in v2.1)

**AST-aware code + docs search with autonomous indexing:**

- **Autonomous Indexing** - Zero-touch operation (MAJOR UPDATE)
  - File system monitoring with 5s debouncing
  - Background worker with 3-retry logic
  - Periodic 10-minute fallback sync
  - **ADHD Win**: Never manually sync or index again!
- **Hybrid Search** - Dense (semantic) + BM25 (keyword) with Voyage reranking
- **Multi-Vector** - Content + title + breadcrumb embeddings (Voyage)
- **Context Generation** - gpt-5-mini 2-3 sentence descriptions
- **Complexity Scoring** - 0.0-1.0 cognitive load assessment per chunk
- **Progressive Disclosure** - Top-10 display + 40 cached (ADHD-safe)
- **Multi-Format Docs** - PDF, Markdown, HTML, DOCX, plain text
- **Perfect Workspace Isolation** - Collection-per-workspace in Qdrant

[📖 Dope-Context Documentation](./services/dope-context/README.md)
[📖 Autonomous Indexing Guide](./services/dope-context/AUTONOMOUS_INDEXING.md)

### MCP Servers

**Specialized AI reasoning and tooling:**

- **Zen MCP** - Multi-model reasoning (thinkdeep, planner, consensus, debug, codereview)
- **Context7** - Official library documentation (React, Vue, Next.js, etc.)
- **GPT-Researcher** - Deep multi-source web research
- **Exa** - Neural semantic search
- **Serena LSP** - Semantic code intelligence with unified ConPort client (NEW)

[📖 MCP Documentation](./docs/INDEX.md)

---

## 💡 Usage Patterns

### Starting a Work Session

```bash
# Set your focus and start the timer
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{
    \"current_focus\": \"Implementing user authentication\",
    \"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\",
    \"mode\": \"ACT\"
  }"

# Statusline now shows:
# dopemux-mvp main | 📊 Implementing user authentication [0m] | 🧠•·👁️ 5K/200K (2%) | Sonnet 4.5
```

### Changing Focus Mid-Session

```bash
# Update focus without resetting timer
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{\"current_focus\": \"Fixing login redirect bug\"}"

# Session timer continues, focus updates immediately
```

### Logging Decisions

```bash
# Record important decisions for future reference
mcp__conport__log_decision \
  --workspace_id $(pwd) \
  --summary "Use JWT for session management" \
  --rationale "Stateless, scalable, widely supported" \
  --implementation_details "HS256 algorithm, 1h expiry, refresh tokens" \
  --tags "auth,security,architecture"
```

### Managing Context Window

**Watch your statusline token percentage:**

🟢 **Green Zone (0-60%)**

```bash
# Work freely, context plenty
# Log decisions as you make them
# No urgency
```

🟡 **Yellow Zone (60-80%)**

```bash
# Wrap up current subtask
# Log key decisions now
# Prepare for potential autocompact

mcp__conport__log_decision \
  --workspace_id $(pwd) \
  --summary "Completed auth middleware implementation" \
  --rationale "..." \
  --tags "auth,milestone"
```

🔴 **Red Zone (80-100%)**

```bash
# SAVE IMMEDIATELY
# Log all important context
# Consider starting new session

# Your context is about to autocompact!
```

### Respecting Break Warnings

**When statusline shows ☕ (yellow):**

- Finish current task (5-10 min)
- Log progress to ConPort
- Take 5-minute break

**When statusline shows ☕! (red):**

- Stop immediately
- Save all work
- Take 10-15 minute break
- Trust the system - it's protecting you

### Using Energy States

**Match tasks to energy level:**

⚡ **Hyperfocus** → Complex architecture, deep debugging, system design

↑ **High Energy** → New features, challenging problems, learning

• **Medium Energy** → Regular development, bug fixes, testing

↓ **Low Energy** → Documentation, code review, simple edits

⇣ **Very Low** → Take a break, don't push through

---

## 🏗️ Architecture

Dopemux uses a **two-plane architecture** for separation of concerns:

### Project Management Plane

- **Leantime** - Status authority (planned → active → blocked → done)
- **Task-Master** - PRD parsing, AI task decomposition
- **Task-Orchestrator** - 37 specialized tools, dependency analysis

### Cognitive Plane

- **Serena LSP** - Code intelligence with ADHD accommodations
- **ConPort** - Knowledge graph, decision logging, memory
- **ADHD Engine** - Energy tracking, attention management

### DopeconBridge

- Cross-plane event routing
- Authority enforcement
- Conflict resolution

[📖 Architecture Documentation](./docs/94-architecture/system-bible.md)

---

## 🎖️ Performance Metrics

**ADHD Targets vs Actual:**

| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| Token reduction | 77% | ✅ 77% | **Met** |
| Context switch | < 2s | ✅ 0.37ms | **257x faster** |
| ConPort queries | < 50ms | ✅ 2ms | **25x faster** |
| Statusline refresh | < 1s | ✅ 150ms | **6.6x faster** |
| ADHD task completion | 85% | 🎯 In progress | **Tracking** |

---

## 🛠️ Troubleshooting

### Statusline shows 📴 disconnected

**Cause:** ConPort database not accessible

**Fix:**

```bash
# Check database exists
ls -la context_portal/context.db

# Initialize if missing
mcp__conport__get_active_context --workspace_id $(pwd)
```

### Statusline shows 0K/200K (0%)

**Cause:** Transcript file not accessible

**Fix:**

```bash
# Enable debug mode
# Edit .claude/statusline.sh, uncomment debug lines

# Check logs
cat /tmp/statusline_debug.json | jq .
tail -20 /tmp/statusline_debug.log
```

### Session time not showing

**Cause:** Invalid session_start timestamp

**Fix:**

```bash
# Reset session start to now
mcp__conport__update_active_context \
  --workspace_id $(pwd) \
  --patch_content "{\"session_start\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}"
```

### ADHD Engine shows 💤

**Cause:** Service not running

**Fix:**

```bash
# Start ADHD Engine
cd services/adhd-engine
uvicorn main:app --port 8095 --reload
```

[📖 Full Troubleshooting Guide](./docs/INDEX.md)

---

## 📖 Documentation

- **[Documentation Index](./docs/INDEX.md)** - Complete documentation overview
- **[ConPort Memory System](./docs/04-explanation/conport-technical-deep-dive.md)** - Knowledge graph and decision logging
- **[Serena Code Intelligence](./docs/04-explanation/serena-v2-technical-deep-dive.md)** - LSP-based semantic navigation
- **[System Architecture](./docs/94-architecture/system-bible.md)** - Two-plane architecture overview
- **[ADHD Engine](./docs/ADHD-ENGINE-DEEP-DIVE-PART1.md)** - Cognitive load management system

---

## 🤝 Contributing

Dopemux is designed by and for developers with ADHD. Contributions welcome!

**Areas of focus:**

- ADHD accommodation patterns
- Statusline improvements
- Energy/attention tracking
- Break management strategies
- Context preservation techniques

---

## 📝 Changelog

### Version 2.1 (2025-10-23)

**Major Infrastructure Upgrades:**

- ✅ **Autonomous Indexing**: dope-context zero-touch operation (1,611 lines)
  - File system monitoring with 5s debouncing
  - Background indexing worker with retry logic
  - Periodic 10-minute sync fallback
  - Never think about indexing again!

- ✅ **ConPort-KG 2.0 Foundation**: Multi-tenant architecture (11,381 lines)
  - RS256 JWT authentication with refresh tokens
  - Argon2id password hashing + breach detection
  - PostgreSQL RLS multi-tenancy (in progress)
  - Security: 2/10 → 7/10 (target: 9/10)

- ✅ **Unified ConPort Client**: Single canonical interface (800+ lines)
  - Consolidated 3 different ConPort implementations
  - Backend adapters (PostgreSQL AGE, SQLite, MCP RPC)
  - Serena v2 migrated to unified client
  - ADHD Engine migrated to PostgreSQL backend
  - 725 lines tech debt eliminated

- ✅ **Multi-Session Support**: Parallel Claude Code sessions
  - Serena ConPort schema migration complete
  - Session isolation and context preservation
  - Foundation for multi-user workflows

**Cross-System Synergies:**

- ✅ 5 major synergies identified and analyzed (1,083 line report)
  - Synergy A: Unified Complexity Intelligence (designed)
  - Synergy B: Unified ConPort Client (implemented)
  - Synergy C: Code Graph + Search Enrichment (designed)
  - Synergy D: Multi-Session Support (implemented)
  - Synergy E: Decision-Agent Linking (planned)

**Performance:**

- ✅ ConPort: 2ms queries (25x faster than target)
- ✅ Statusline: 150ms refresh (6.6x faster)
- ✅ Token calc: 30ms (3x faster)
- ✅ Autonomous indexing: Zero mental overhead

**Bug Fixes:**

- ✅ gpt-researcher langchain compatibility (Decision #214)
- ✅ Worktree consolidation improvements (Decision #217)
- ✅ OpenRouter + Grok Code Fast integration for LiteLLM

## 📱 Mobile Mode with Happy

Bring Claude Code to your phone with the Happy mobile client.

### Prerequisites

- Install Claude CLI and log in: `brew install claude-cli` then `claude login`
- Install Happy CLI globally: `npm i -g happy-coder`
- Optional: configure a self-hosted Happy relay and webapp

### Configuration

Add the following keys to `~/.config/dopemux/config.yaml` or `.dopemux/config.yaml`:

```yaml
mobile:
  enabled: true
  default_panes: primary  # "primary", "all", or list of pane titles
  happy_server_url: https://happy.yourdomain.tld  # optional
  happy_webapp_url: https://happyweb.yourdomain.tld  # optional
```

### Quick Start

1. `dopemux start`
2. `dopemux mobile start`
3. Scan the QR code with the Happy app (iOS, Android, or web)
4. Code from your phone while Claude stays in sync

Helpful commands:

- `dopemux mobile start --all` – mirror all Claude panes
- `dopemux mobile notify "✅ Tests passed"` – push a status notification
- `dopemux mobile detach --all` – stop all Happy sessions
- `dopemux mobile status --watch` – keep an eye on Happy health and sessions in real time

Automation-friendly helpers:

- `dopemux run-tests` (or pass your own command) broadcasts mobile notifications when test suites finish
- `dopemux run-build` does the same for build pipelines

The tmux status line now shows a 📱 indicator whenever Happy is enabled—green when sessions are active, amber when idle, and red when attention is needed.

Use `dopemux status -m` to see Happy readiness alongside the rest of your Dopemux metrics.

For dashboards or custom tooling, read `~/.cache/dopemux/status/mobile_status.json` for the latest Happy snapshot (same data that powers the status line).

Run `dopemux doctor` to verify Happy/Claude CLI availability and optional relay reachability.

### Version 2.0 (2025-10-04)

**Statusline Improvements:**

- ✅ Real token usage tracking from transcript files
- ✅ Auto-detect context window for all Claude models
- ✅ Raw token counts: `128K/200K (64%)`
- ✅ Better energy symbol: `•` for medium
- ✅ Intuitive time: `[2h 15m]` format
- ✅ Attention state indicators
- ✅ Break warning system
- ✅ Hyperfocus protection

**Performance:**

- ✅ ConPort: 2ms queries (25x faster than target)
- ✅ Statusline: 150ms refresh (6.6x faster)
- ✅ Token calc: 30ms (3x faster)

**New Features:**

- ✅ Direct SQLite access for ConPort
- ✅ Progressive disclosure based on terminal width
- ✅ Context window optimization guidance

### Version 1.0 (2025-09-26)

- Initial release
- ConPort knowledge graph
- ADHD Engine integration
- Basic statusline

[📖 Full Changelog](./CHANGELOG.md)

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

Built with insights from the ADHD development community and powered by Claude AI.

**Special thanks to:**

- The ADHD developer community for sharing their experiences
- Anthropic for Claude Code and Claude API
- Contributors to ADHD accommodation research

---

**Made with ❤️ and ☕ by developers with ADHD, for developers with ADHD**

---

## 🗂️ Multi-Workspace Usage

### Working with Multiple Projects

**Scenario: You're working on 3 different projects**

```bash
# Configure your workspaces
export DEFAULT_WORKSPACE_PATH=~/code/dopemux-mvp
export WORKSPACE_PATHS=~/code/client-app,~/code/api-backend,~/code/mobile-app

# Start dopemux (uses DEFAULT_WORKSPACE_PATH)
dopemux start

# Switch to another workspace
dopemux workspace switch ~/code/client-app

# Check workspace status
dopemux workspace status
# Output:
# Current Workspace: ~/code/client-app
# Energy Level: Medium
# Attention: Focused
# Session Duration: 45 minutes
# Uncommitted Changes: 3 files
```

### Cross-Workspace Queries

**Find decisions across all projects:**

```bash
# Search decisions in all configured workspaces
dopemux query decisions --all-workspaces "authentication"

# Compare energy patterns across workspaces
dopemux analyze energy --workspaces ~/code/project1,~/code/project2

# View today's work across all projects
dopemux sessions today --all-workspaces
```

### Workspace-Specific Configuration

**Each workspace can have custom settings:**

```bash
# Initialize workspace with custom config
cd ~/code/my-project
dopemux init --workspace-config .dopemux/workspace.yaml

# Example workspace.yaml:
# break_interval: 30  # Minutes between break reminders
# complexity_threshold: 0.7  # When to warn about complexity
# energy_tracking: true  # Enable energy monitoring
# preferred_models: ["claude-sonnet-4.5", "gpt-5"]
```

### Statusline Workspace Indicator

The statusline shows your current workspace:

```
[client-app] main | ✅ Implementing auth [1h 30m] | 🧠 ⚡● 👁️● | Sonnet 4.5
└─────┬────┘
      └─ Current workspace name
```

### Multi-Workspace Best Practices

**✅ Do:**
- Set `DEFAULT_WORKSPACE_PATH` in your shell profile
- Use workspace switching when context switching between projects
- Leverage cross-workspace queries for insights
- Keep workspace-specific configs in `.dopemux/workspace.yaml`

**❌ Don't:**
- Mix workspace data manually (let Dopemux handle isolation)
- Forget to commit before switching workspaces
- Override workspace auto-detection without good reason

### Environment Variables Reference

```bash
# Core workspace configuration
DEFAULT_WORKSPACE_PATH=~/code/main-project  # Default workspace
WORKSPACE_PATHS=~/code/p1,~/code/p2         # Additional workspaces
ENABLE_WORKSPACE_ISOLATION=true             # Isolate data per workspace
ENABLE_CROSS_WORKSPACE_QUERIES=true         # Allow cross-workspace queries
WORKSPACE_CACHE_TTL=3600                    # Cache TTL in seconds
```

### API Usage with Workspaces

**Services automatically detect workspace from context:**

```python
# Python - Auto-detect workspace
from dopemux import DopemuxClient

client = DopemuxClient()  # Uses current directory as workspace
state = await client.get_adhd_state()

# Python - Explicit workspace
client = DopemuxClient(workspace_path="~/code/my-project")
state = await client.get_adhd_state()

# Python - Multi-workspace query
results = await client.query_decisions(
    query="refactoring",
    workspace_paths=["~/code/project1", "~/code/project2"]
)
```

**MCP Tools with workspace parameters:**

```javascript
// Use serena in specific workspace
await use_mcp_tool("serena", "find_symbol", {
  symbol: "authenticate",
  workspace_path: "~/code/api-backend"
});

// Query ConPort across workspaces
await use_mcp_tool("conport", "search_decisions", {
  query: "database migration",
  workspace_paths: ["~/code/frontend", "~/code/backend"]
});
```

### Performance Considerations

**Workspace isolation is highly optimized:**
- Single workspace queries: <50ms (cached: <5ms)
- Multi-workspace queries: <200ms for 5 workspaces
- Database indexed on workspace_id for fast lookups
- Redis caching with workspace-scoped keys

### Troubleshooting

**Workspace not detected:**
```bash
# Check current workspace detection
dopemux workspace detect

# Force workspace path
dopemux --workspace ~/code/my-project start
```

**Data showing in wrong workspace:**
```bash
# Verify workspace isolation
dopemux doctor --check-isolation

# Re-initialize workspace
dopemux workspace reset
```

For more details, see:
- [Multi-Workspace Implementation Guide](MULTI_WORKSPACE_IMPLEMENTATION_GUIDE.md)
- [Workspace API Reference](docs/api/workspace.md)
- [Troubleshooting Guide](docs/troubleshooting/workspaces.md)
