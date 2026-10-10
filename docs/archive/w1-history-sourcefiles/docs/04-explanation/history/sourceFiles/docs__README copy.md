# 🧠 Dopemux - ADHD-Optimized Development Platform

> **Dopemux MVP**: Complete ADHD-optimized development platform with health monitoring, MCP server integration, and comprehensive Claude Code support.

Dopemux is a specialized development platform designed for neurodivergent developers, particularly those with ADHD. It provides context preservation, attention monitoring, task decomposition, and comprehensive health monitoring to enhance productivity and reduce cognitive load.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![ADHD](https://img.shields.io/badge/ADHD-Optimized-purple.svg)](docs/ADHD_FEATURES.md)
[![Health](https://img.shields.io/badge/Health-Monitoring-orange.svg)](docs/HEALTH_MONITORING.md)

## 🎯 Key Features

### **🧠 ADHD-First Design**
- **Context Preservation**: Automatic session state management across interruptions
- **Attention Monitoring**: Real-time focus state tracking and adaptive responses
- **Task Decomposition**: Complex tasks broken into manageable 25-minute chunks
- **Gentle Guidance**: Non-judgmental, encouraging feedback and clear next steps
- **Decision Reduction**: Maximum 3 options presented to reduce cognitive overwhelm

### **🏥 Comprehensive Health Monitoring**
- **Real-time Health Checks**: Monitor Dopemux core, Claude Code, MCP servers, and system resources
- **Slash Command Integration**: Instant health status from Claude Code with `/health`, `/mcp-status`, `/health-fix`
- **Auto-remediation**: Automatic service restart and problem resolution
- **ADHD-Friendly Interface**: Clear visual indicators (🟢🟡🔴) and minimal cognitive load
- **Docker MCP Support**: Ready for comprehensive Docker-based MCP server ecosystem

### **🔧 Claude Code Integration**
- **MCP Server Management**: Integrated sequential thinking and reasoning capabilities
- **Auto-responder**: Intelligent confirmation handling with attention-aware features
- **Configuration Management**: ADHD-optimized Claude Code setup and maintenance
- **Project Templates**: Pre-configured setups for common development scenarios

### **⚡ Advanced MCP Ecosystem**
- **Sequential Thinking Server**: Multi-agent reasoning with DeepSeek/GitHub Models
- **MCP Proxy Integration**: Seamless Docker-to-Claude Code connectivity
- **Leantime Integration**: Project management with ADHD accommodations
- **Docker Orchestration**: Scalable MCP server architecture
- **Health Monitoring**: Comprehensive service monitoring and auto-recovery

## ✨ Features

### 🧠 ADHD-First Design
- **Attention State Management**: Automatic focus duration tracking and break recommendations
- **Cognitive Load Balancing**: Smart task scheduling based on complexity and mental capacity
- **Context Preservation**: Never lose your place with automatic session saves and restoration
- **Executive Function Support**: Clear next steps and decision reduction to minimize overwhelm
- **ADHD Metadata**: Every task includes cognitive load (1-10), focus level, break reminders, and optimal timing
- **Attention-Aware Filtering**: Get tasks by attention level, cognitive capacity, and current state

### 🚀 AI-Powered Workflow
- **PRD-to-Tasks**: Transform Product Requirements Documents into actionable task breakdowns
- **Intelligent Scheduling**: Optimal task sequencing based on attention patterns and complexity
- **Bidirectional Sync**: Seamless data flow between Leantime project management and Task-Master AI
- **Claude Auto Responder**: Automatic Claude Code confirmation responses with ADHD accommodations
- **Real-time Optimization**: Continuous workflow adaptation based on performance metrics

### 🐳 Self-Hosted Infrastructure
- **Docker-Based Deployment**: One-command setup with docker-compose
- **Leantime Integration**: Neurodiversity-focused project management platform
- **Task-Master AI**: Advanced PRD parsing and task decomposition via MCP
- **Health Monitoring**: Comprehensive system checks and automated recovery

## 🎯 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.8+
- Node.js 18+
- 4GB+ RAM (8GB recommended)

### Installation
```bash
# Clone repository
git clone https://github.com/your-repo/dopemux-mvp.git
cd dopemux-mvp

# Automated installation (recommended)
python installers/leantime/install.py --interactive

# Manual installation
cd docker/leantime
docker-compose up -d

# MCP Proxy Setup for Claude Code Integration
./scripts/mcp-proxy-setup.sh setup
npm install -g claude-task-master
pip install -r requirements.txt
```

### First Use
1. **Access Leantime**: http://localhost:8080 (admin/admin)
2. **Verify Health**: `python installers/leantime/health_check.py`
3. **Create Project**: Start with a simple PRD document
4. **Enable ADHD Mode**: Configure attention tracking preferences
5. **Test MCP Integration**: Use `/mcp` in Claude Code to access containerized servers

### 🔗 MCP Proxy Integration

Dopemux includes an innovative MCP proxy solution that bridges Docker-containerized MCP servers with Claude Code:

```bash
# Quick setup
./scripts/mcp-proxy-setup.sh setup

# Verify connection
claude mcp list  # Should show ✓ Connected servers

# Use in Claude Code
/mcp tools list  # See available MCP tools
```

**Available MCP Servers:**
- **Sequential Thinking** - Advanced multi-agent reasoning
- **Exa Search** - Web research and data gathering
- **Zen Orchestration** - Multi-model coordination
- **Serena Navigation** - Enhanced code exploration

📖 **Detailed guides:**
- [Quick Start](docs/MCP_PROXY_QUICK_START.md) - Get running in 2 minutes
- [Complete Setup Guide](docs/MCP_PROXY_SETUP_GUIDE.md) - Comprehensive documentation

## 📊 System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Leantime      │◄──►│  Sync Manager    │◄──►│ Task-Master AI  │
│   (Projects)    │    │ (Bidirectional)  │    │ (PRD Analysis)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         ▲                        ▲                       ▲
         │              ┌─────────▼─────────┐             │
         │              │ ADHD Optimizations │             │
         │              │ - Attention Mgmt   │             │
         │              │ - Context Preserve │             │
         │              │ - Cognitive Load   │             │
         │              └────────────────────┘             │
         │                                                 │
         ▼                                                 ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Docker Services │    │     MCP Bridge   │    │  Health Checks  │
│ - MySQL         │    │   (Protocol)     │    │   & Monitoring  │
│ - Redis         │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🔧 Core Components

### Leantime Bridge (`src/integrations/leantime_bridge.py`)
- **MCP Client**: Protocol-based integration with Leantime API
- **Project Management**: Create, read, update, delete operations for projects and tasks
- **ADHD Features**: Attention-level filtering, cognitive load assessment, break reminders

### Task-Master Bridge (`src/integrations/taskmaster_bridge.py`)
- **PRD Processing**: Intelligent analysis of Product Requirements Documents
- **Task Decomposition**: Break complex features into manageable chunks
- **Complexity Assessment**: Cognitive load scoring for optimal scheduling

### Sync Manager (`src/integrations/sync_manager.py`)
- **Bidirectional Sync**: Real-time data synchronization between systems
- **Conflict Resolution**: Intelligent handling of concurrent updates
- **Event Sourcing**: Complete audit trail of all changes

### ADHD Optimizations (`src/utils/adhd_optimizations.py`)
- **Attention Tracking**: Monitor focus states and recommend optimal work patterns
- **Context Management**: Preserve mental models across interruptions
- **Schedule Optimization**: Balance cognitive load and task complexity

## 📚 Documentation

- **[Installation Guide](docs/INSTALLATION.md)**: Complete setup instructions
- **[User Guide](docs/USER_GUIDE.md)**: ADHD-optimized workflows and features
- **[API Documentation](docs/API.md)**: Complete technical reference

## 🧪 Testing

### Run Test Suite
```bash
# Full test coverage
python -m pytest tests/ --cov=src --cov-report=html

# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Specific test
python -m pytest tests/unit/test_adhd_optimizations.py -v
```

### Test Coverage
- **Unit Tests**: 100% coverage for all modules
- **Integration Tests**: Complete workflow validation
- **Health Checks**: System monitoring and recovery
- **Performance Tests**: Load testing and optimization

## 🎨 ADHD-Friendly Features

### Attention Management
- **Focus Sessions**: 25-minute blocks with automatic break reminders
- **Attention Detection**: Real-time assessment of cognitive state
- **Context Switching**: Minimal disruption with preserved mental models
- **Progress Visualization**: Clear indicators of completion and remaining work

### Cognitive Load Optimization
- **Task Complexity**: 1-10 scoring system for mental effort estimation
- **Schedule Balancing**: Mix of high/medium/low complexity tasks
- **Energy Matching**: Align challenging work with peak attention periods
- **Break Integration**: Regular rest periods built into workflow

### Executive Function Support
- **Decision Reduction**: Maximum 3 options presented at once
- **Clear Next Steps**: Always know what to do next
- **Prerequisites Tracking**: Dependencies clearly identified
- **Completion Celebration**: Positive reinforcement for task completion

## 🤝 Contributing

### Development Setup
```bash
# Development installation
git clone https://github.com/your-repo/dopemux-mvp.git
cd dopemux-mvp
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
pip install -r requirements-dev.txt
```

### ADHD-Friendly Contributions
- **Any format welcome**: Bullet points, voice notes, rough ideas
- **No judgment**: All questions and suggestions valued
- **Flexible participation**: Contribute when attention allows
- **Clear guidelines**: Specific steps for each contribution type

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Leantime Team**: For creating neurodiversity-focused project management
- **Task-Master AI**: For intelligent task decomposition capabilities
- **ADHD Community**: For insights into attention-friendly development workflows
- **MCP Protocol**: For enabling seamless AI service integration

---

**Built with ❤️ for the ADHD developer community**

*Making development accessible, one focused session at a time.*
