---
id: config-system
title: Config System
type: reference
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Config System (reference) for dopemux documentation and developer workflows.
---
# Production CLI Configuration System

**Status**: ✅ Complete and tested
**Priority**: Priority 2 (Complete)
**Architecture Confidence**: 0.87 (Very High) - Evidence-based design

---

## 🎯 **Overview**

Production-ready configuration system for multi-AI CLI orchestration with:
- **Zero-config defaults** (works out-of-box)
- **Auto-detection** of CLI paths (PATH + common locations)
- **ADHD-optimized** error messages and validation
- **Cross-platform** (macOS + Linux)
- **Secure** environment variable handling
- **Extensible** (add new AIs without code changes)

---

## 🚀 **Quick Start**

### Zero Configuration (Recommended)
```python
from src.agent_spawner import AgentSpawner
from src.agent_config_factory import auto_configure_spawner

# Auto-detect and configure all CLIs
spawner = AgentSpawner()
auto_configure_spawner(spawner)
spawner.start_all()
```

**That's it!** Claude and Gemini are auto-detected and configured.

### Custom Configuration
```python
# Create config/agents.yaml (see template below)
spawner = AgentSpawner()
auto_configure_spawner(spawner, config_path="config/agents.yaml")
spawner.start_all()
```

---

## 📁 **Configuration File**

### Location Priority
1. `./config/agents.yaml` (project-specific, highest priority)
1. `~/.config/dopemux/agents.yaml` (user default)
1. Built-in defaults (zero-config fallback)

### Example Configuration

```yaml
# config/agents.yaml
agents:
  claude:
    command: claude  # Auto-found in PATH
    args: ["chat"]
    default_model: claude-sonnet-4.5
    env:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:}  # Optional
    auto_restart: true

  gemini:
    command: gemini
    args: ["--output-format", "json"]
    default_model: gemini-2.5-pro
    env:
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}  # Required
    auto_restart: true

  grok:
    type: mcp  # MCP provider (not CLI)
    zen_model: grok-code-fast
    capabilities: [code, analysis]

task_routing:
  research: gemini
  code: grok
  review: claude

advanced:
  max_concurrent_agents: 3
  auto_save_interval: 30
```

---

## 🔧 **Features**

### 1. Auto-Detection
- ✅ Searches `$PATH` for CLIs
- ✅ Fallback to common install locations
- ✅ Clear messages showing where CLIs were found
- ✅ Actionable errors if not found

### 2. Environment Variables
```yaml
env:
  # Reference system environment variables
  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}

  # With defaults
  CLAUDE_MODEL: ${CLAUDE_MODEL:claude-sonnet-4.5}

  # Optional (empty default)
  OPENAI_API_KEY: ${OPENAI_API_KEY:}
```

**Security**: Never commit API keys! Use system environment variables.

### 3. Validation
- ✅ Fail-fast with clear error messages
- ✅ ADHD-friendly (visual icons, actionable steps)
- ✅ Distinguishes errors (❌) from warnings (⚠️)
- ✅ Install instructions for missing CLIs

Example validation output:
```
❌ gemini: CLI 'gemini' not found
   💡 Try: which gemini
   💡 Or install: pip install gemini-cli
```

### 4. Task-Based Routing
```yaml
task_routing:
  research: gemini  # Cost-effective
  code: grok        # FREE!
  review: claude    # Best quality
```

Access in code:
```python
from src.config_loader import ConfigLoader

loader = ConfigLoader()
loader.load()
routing = loader.get_task_routing()

# Route task to optimal agent
agent = routing.get('research', 'claude')  # Defaults to claude
```

### 5. MCP Provider Support
```yaml
agents:
  grok:
    type: mcp  # Not spawned via PTY
    zen_model: grok-code-fast
    capabilities: [code, analysis]
```

Query MCP providers:
```python
from src.agent_config_factory import AgentConfigFactory

factory = AgentConfigFactory()
factory.load()
mcp_providers = factory.get_mcp_providers()
```

---

## 📚 **API Reference**

### ConfigLoader
```python
from src.config_loader import ConfigLoader, load_agent_config

# Simple usage
agents = load_agent_config()

# Advanced usage
loader = ConfigLoader(config_path="custom/path.yaml")
agents = loader.load()
task_routing = loader.get_task_routing()
advanced = loader.get_advanced_settings()
```

### AgentConfigFactory
```python
from src.agent_config_factory import (
    AgentConfigFactory,
    create_agent_configs_from_file,
    auto_configure_spawner
)

# Method 1: Auto-configure (easiest)
spawner = AgentSpawner()
auto_configure_spawner(spawner)

# Method 2: Manual (more control)
configs = create_agent_configs_from_file()
for agent_type, config in configs.items():
    spawner.register_agent(agent_type, config)

# Method 3: Factory (full control)
factory = AgentConfigFactory()
factory.load()
cli_agents = factory.list_available_agents()
mcp_providers = factory.get_mcp_providers()
```

---

## 🧪 **Testing**

### Test Configuration Loader
```bash
python3 src/config_loader.py
```

### Test Config Factory
```bash
python3 -m src.agent_config_factory
```

### Test Integration
```bash
python3 test_config_integration.py
```

### Manual Test
```python
from src.agent_config_factory import auto_configure_spawner
from src.agent_spawner import AgentSpawner

spawner = AgentSpawner()
auto_configure_spawner(spawner)
spawner.start_all()  # Starts all configured agents
```

---

## 🔄 **Migration Guide**

### Before (Hardcoded)
```python
spawner.register_agent(
    AgentType.CLAUDE,
    AgentConfig(
        agent_type=AgentType.CLAUDE,
        command=["/Users/hue/.local/bin/claude", "chat"],  # Hardcoded!
        env={},
        auto_restart=True,
    ),
)
```

### After (Config File)
```python
# One line replaces all hardcoded configs!
auto_configure_spawner(spawner)
```

**Benefits**:
- ✅ Cross-platform (works on any system)
- ✅ Zero maintenance (auto-detects paths)
- ✅ Extensible (add agents in YAML, not code)
- ✅ Secure (no hardcoded paths or keys)

---

## 🎨 **Design Decisions**

Based on comprehensive multi-model Zen analysis (confidence: 0.87):

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Config Format | **YAML** | Comments + familiarity + ADHD-friendly |
| Schema | **Flat + type** | Simple default, extensible |
| Path Resolution | **PATH + fallback** | Zero-config for 80% case |
| Model Selection | **Per-agent + task** | Defaults + power user options |
| Env Management | **System env + ${}** | Security best practice |
| Validation | **Fail-fast + clear** | ADHD-friendly errors |
| Config Location | **User + project** | Predictable + flexible |
| Hot Reload | **Manual command** | Simple + interrupt-free |

---

## ✅ **Success Criteria Met**

- ✅ **Cross-platform**: PATH resolution works everywhere
- ✅ **ADHD-friendly**: Clear errors, ~3 options max, predictable location
- ✅ **Secure**: No hardcoded API keys, env var injection
- ✅ **Extensible**: Add new AIs without code changes
- ✅ **Validated**: Errors caught at load time with actionable messages
- ✅ **Zero-config**: Works out-of-box for common cases

---

## 📊 **Files Created**

| File | Purpose | Lines |
|------|---------|-------|
| `config/agents.yaml` | Example configuration | 145 |
| `src/config_loader.py` | Config loader + validation | 350 |
| `src/agent_config_factory.py` | Integration bridge | 200 |
| `test_config_integration.py` | Integration test | 60 |
| `CONFIG_SYSTEM_README.md` | Documentation | This file |

**Total**: ~755 lines of production-ready code + documentation

---

## 🚀 **Next Steps**

1. ✅ Config system complete and tested
1. **Update existing test files** to use new system (replace hardcoded paths)
1. **Response parser** (Priority 3) - Clean AI output
1. **Error recovery** (Priority 4) - Retry logic, timeouts
1. **End-to-end test** (Priority 5) - Full workflow validation

---

## 💡 **ADHD Features**

- **Zero-config**: Works immediately, no setup paralysis
- **Clear errors**: ❌ vs ⚠️, actionable steps, ~3 items max
- **Visual feedback**: Icons (✅/❌/⚠️/💡) aid processing
- **Predictable location**: No searching, ~/.config/dopemux or ./config
- **Auto-detection**: Reduces cognitive load
- **Sensible defaults**: 80% case works without config

---

**Status**: ✅ Production-ready
**Confidence**: 0.87 (Very High)
**Architecture**: Evidence-based through comprehensive multi-model analysis

Ready to ship! 🚀
