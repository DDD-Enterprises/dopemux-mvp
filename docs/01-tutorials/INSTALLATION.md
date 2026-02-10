---
id: INSTALLATION
title: Installation
type: tutorial
date: '2025-11-15'
author: '@hu3mann'
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
prelude: Tutorial for Installation.
---
# Dopemux Installation Guide

**Quick Start**: `git clone` → `setup.sh` → `dopemux init` → ready! ✅

---

## 📋 Prerequisites

Before installing dopemux, ensure you have:

- **Docker Desktop** - For MCP server containers
- **Python 3.11+** - Core dopemux runtime
- **Git** - For cloning and submodules

**Check your versions:**
```bash
docker --version    # Any recent version
python3 --version   # 3.11 or higher
git --version       # Any recent version
```

---

## ⚡ Quick Installation (Recommended)

```bash
# 1. Clone dopemux
git clone https://github.com/DDD-Enterprises/dopemux-mvp.git
cd dopemux-mvp

# 2. Run setup script (creates ~/.dopemux/, installs deps, starts Docker)
./scripts/setup.sh

# 3. Generate per-workspace config + env file
python3 scripts/render_workspace_configs.py --set-default

# 4. Load your workspace env (add to shell profile for convenience)
source "$(python3 scripts/workspace_env_path.py)"

# 5. Edit .env with your API keys
nano .env
# Required: OPENAI_API_KEY, VOYAGEAI_API_KEY
# Optional: ANTHROPIC_API_KEY, GEMINI_API_KEY, CONTEXT7_API_KEY

# 6. Verify installation
dopemux health

# 5. Initialize your first project
cd ~/my-project
dopemux init              # Wizard prompts for profile
dopemux profile show      # Verify configuration
dopemux start             # Launch dopemux!
```

**That's it!** Dopemux is now running with your selected profile.

---

## 📖 Detailed Installation Steps

### **Step 1: Clone Repository**

```bash
git clone https://github.com/DDD-Enterprises/dopemux-mvp.git
cd dopemux-mvp
```

### **Step 2: Run Setup Script**

The setup script automates the entire installation:

```bash
./scripts/setup.sh
```

**What it does**:
1. ✅ Checks prerequisites (docker, git, python 3.11+)
2. ✅ Creates `~/.dopemux/` directory structure
3. ✅ Installs default profiles (python-ml, web-dev, adhd-default)
4. ✅ Generates `.env` from template
5. ✅ Installs dopemux package (`pip install -e .`)
6. ✅ Initializes git submodules (Zen MCP)
7. ✅ Creates Docker network
8. ✅ Starts MCP services
9. ✅ Runs health check

**Options**:
```bash
./scripts/setup.sh --skip-docker  # Skip Docker services (for testing)
```

### **Step 3: Configure API Keys**

Edit `.env` and add your API keys:

```bash
nano .env
```

**Required Keys** (minimum functionality):
- `OPENAI_API_KEY` - For GPT models (Zen MCP, GPT-Researcher)
- `VOYAGEAI_API_KEY` - For embeddings (ConPort knowledge graph)

**Optional Keys** (enhanced functionality):
- `ANTHROPIC_API_KEY` - Claude models (Zen MCP)
- `GEMINI_API_KEY` - Google Gemini (Zen MCP)
- `CONTEXT7_API_KEY` - Documentation access
- `EXA_API_KEY` - Neural web search
- `TAVILY_API_KEY` - Research (GPT-Researcher)

**Get API Keys**:
- OpenAI: https://platform.openai.com/
- Voyage AI: https://www.voyageai.com/
- Anthropic: https://console.anthropic.com/
- Google Gemini: https://makersuite.google.com/app/apikey
- Context7: https://context7.com/

### **Step 4: Verify Installation**

```bash
dopemux health
```

**Expected Output**:
```
✅ ConPort: Healthy
✅ Zen MCP: Healthy
✅ Context7: Healthy
...
```

If any services show unhealthy:
```bash
docker ps                              # Check container status
docker logs mcp-<service-name>         # View logs
docker-compose -f docker/mcp-servers/docker-compose.yml restart <service>
```

---

## 🚀 Using Dopemux in Your Projects

### **Initialize New Project**

```bash
cd ~/my-awesome-project
dopemux init
```

**The wizard will**:
1. Auto-detect project type (Python ML, web dev, etc.)
2. Suggest appropriate profile
3. Prompt for confirmation or selection
4. Create `.dopemux/` directory
5. Set active profile
6. Display next steps

**Manual profile selection**:
```bash
dopemux init -p python-ml    # Use specific profile
dopemux init -p web-dev
dopemux init -p adhd-default
```

### **Verify Configuration**

```bash
dopemux profile show         # Show active profile
dopemux profile show -v      # Show full merged config
```

### **Start Dopemux**

```bash
dopemux start
```

This launches Claude Code with your profile's MCP server configuration.

---

## 👥 Multiple Projects

Dopemux supports multiple projects with different profiles!

```bash
# ML Project
cd ~/ml-research
dopemux init -p python-ml
dopemux start

# Web Project
cd ~/web-app
dopemux init -p web-dev
dopemux start
```

**Shared ConPort Knowledge**:
- All projects contribute to shared decision pattern learning
- Patterns detected in one project benefit all projects
- Energy tracking and insights shared across workspace

**Project Isolation**:
- Each project has its own `.dopemux/` directory
- Local databases for code context (privacy)
- Independent profile configurations

---

## 🔧 Troubleshooting

### **dopemux command not found**

```bash
# Ensure package installed
pip install -e .

# Or use module form
python -m dopemux --help
```

### **Docker services not starting**

```bash
# Check Docker is running
docker ps

# Restart services
cd dopemux-mvp
docker-compose -f docker/mcp-servers/docker-compose.yml restart

# View logs
docker-compose -f docker/mcp-servers/docker-compose.yml logs
```

### **No profiles available**

```bash
# Manually install default profiles
cd dopemux-mvp
python3 -c "from src.dopemux.profile_manager import ProfileManager; ProfileManager().install_default_profiles()"

# Verify
dopemux profile list
```

### **API key errors**

Check your `.env` file has valid keys:
```bash
cat .env | grep API_KEY
```

Test keys individually:
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## 🎯 What's Next?

After installation:

1. **Explore commands**: `dopemux --help`
2. **List profiles**: `dopemux profile list`
3. **Initialize project**: `dopemux init`
4. **Start working**: `dopemux start`

**ConPort Decision Support**:
```bash
dopemux decisions stats                    # View decision statistics
dopemux decisions energy log high          # Track energy levels
dopemux decisions patterns tags            # See auto-detected patterns
```

**Advanced Usage**:
- See `MULTI_PROJECT.md` for multi-project workflows
- See `PROFILES.md` for profile customization
- See [CONTRIBUTING_ZEN.md](../CONTRIBUTING_ZEN.md) for Zen MCP development

---

## 📚 Additional Resources

- **User Guide**: [MULTI_PROJECT.md](MULTI_PROJECT.md)
- **Profile Reference**: [PROFILES.md](PROFILES.md)
- **Architecture**: [System Bible](../94-architecture/system-bible.md)
- **Troubleshooting**: [Troubleshooting Playbook](../troubleshooting-playbook.md)

---

## 🆘 Getting Help

- **Issues**: https://github.com/DDD-Enterprises/dopemux-mvp/issues
- **Support**: https://github.com/DDD-Enterprises/dopemux-mvp/issues
- **Documentation**: https://github.com/DDD-Enterprises/dopemux-mvp/tree/main/docs

---

**Installation Time**: ~5 minutes
**Difficulty**: Easy (one command + API keys)
**Requirements**: Docker, Python 3.11+, Git

🚀 **Happy coding with ADHD-optimized development!**
