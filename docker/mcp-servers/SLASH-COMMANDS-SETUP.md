# Dopemux Slash Commands Setup

Enable `/dopemux` slash commands in Claude Code for seamless ADHD-optimized development.

## Quick Setup

### 1. Enable Global Commands
Add dopemux to your PATH:

```bash
# Add to your ~/.bashrc, ~/.zshrc, or ~/.profile
export PATH="$HOME/.local/bin:$PATH"

# Reload your shell
source ~/.bashrc  # or ~/.zshrc
```

### 2. Configure Claude Code MCP
Update your Claude Code settings (`~/.claude/settings.json`) to include dopemux commands:

```json
{
  "mcpServers": {
    "cli": {
      "type": "stdio",
      "command": "uvx",
      "args": ["shell-command-mcp"],
      "env": {
        "ALLOWED_COMMANDS": "git,gh,ls,cat,pwd,dopemux,docker",
        "COMMAND_TIMEOUT": "30",
        "ALLOW_SHELL_OPERATORS": "false"
      }
    }
  }
}
```

### 3. Test Installation
In Claude Code, try:
```
/dopemux help
```

You should see the available dopemux commands.

Tip: To start Claude and the MCP servers in one step from a terminal (outside Claude), run:
```
dopemux start --mcp-up
```

## Available Slash Commands

### Session Management
- `/dopemux save` - Save current session state
- `/dopemux restore [session]` - Restore session (latest if not specified)

### Instance Management
- `/dopemux status` - Show all running instances
- `/dopemux start [instance] [branch]` - Start instance (auto-detect if not specified)
- `/dopemux stop <instance>` - Stop specific instance
- `/dopemux switch <instance>` - Switch to instance worktree
- `/dopemux list` - List all available instances

### MCP Server Control
- `/dopemux servers up` - Start all MCP servers (docker compose)
- `/dopemux servers down` - Stop all MCP servers
- `/dopemux servers status` - Show server status
- `/dopemux servers logs [service]` - Tail logs for a service

Examples:
```
/dopemux servers up                 # same as: dopemux mcp up --all
/dopemux servers status             # same as: dopemux mcp status
/dopemux servers logs gptr-mcp      # same as: dopemux mcp logs --service gptr-mcp
```

## ADHD-Optimized Workflow

### 🎯 Focus Session Pattern
```
/dopemux save                    # Save current state
/dopemux start focus feature/ui  # Start focused work instance
# ... 25 minutes of focused work ...
/dopemux save                    # Save progress
/dopemux stop focus             # Take break
```

### 🔄 Context Switching Pattern
```
/dopemux status                 # See current state
/dopemux switch dev            # Switch to dev instance
# ... work on development ...
/dopemux switch staging        # Switch to staging for testing
# ... test changes ...
/dopemux switch prod           # Switch to production deployment
```

### 🌳 Branch-Based Development
```
/dopemux start dev feature/new-ui        # Work on feature branch
/dopemux start staging develop           # Test integration
/dopemux start prod release/v1.2.0      # Production deployment
```

## Benefits for ADHD Developers

### 🧠 Cognitive Load Reduction
- **No manual branch switching** - Each instance has its own worktree
- **Preserved context** - Session state maintained across switches
- **Visual separation** - Clear workspace organization per instance

### ⚡ Flow State Protection
- **No interruptions** to switch environments
- **Parallel work streams** - Multiple instances running simultaneously
- **Quick recovery** - Saved sessions for easy restoration

### 🎯 Executive Function Support
- **Clear commands** - Simple slash command interface
- **Auto-detection** - Smart port and instance management
- **Progress tracking** - Session saves with timestamps

## Troubleshooting

### Command Not Found
```bash
# Check if dopemux is in PATH
which dopemux

# If not found, add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Claude Code Integration Issues
1. Restart Claude Code after updating settings
2. Check MCP server configuration in settings
3. Ensure `shell-command-mcp` is installed: `uvx --from shell-command-mcp`

### Session Files Not Found
```bash
# Check session directory exists
ls ~/.dopemux/sessions/

# If missing, the directory will be created on first save
/dopemux save
```

## Advanced Configuration

### Custom Session Directory
Set environment variable in your shell:
```bash
export DOPEMUX_SESSIONS_DIR="/path/to/custom/sessions"
```

### Auto-Save Integration
Add to your shell profile for automatic session saves:
```bash
# Auto-save every 30 minutes (requires cron or similar)
*/30 * * * * /Users/hue/.local/bin/dopemux --claude-slash save >/dev/null 2>&1
```

---

**🧠 Built for ADHD developers** - Reduce context switching stress and maintain flow state!

*Making development accessible, one focused session at a time.*
