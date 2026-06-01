Quick install TaskMaster globally if not already installed.

Execute this streamlined installation:

```bash
# Check and install in one command
TaskMaster --version 2>/dev/null || npm install -g TaskMaster-ai

# Verify installation
TaskMaster --version

# Quick setup check
TaskMaster models --status || echo "Note: You'll need to set up an AI provider API key"
```

If you see "command not found" after installation, you may need to:
1. Restart your terminal
2. Or add npm global bin to PATH: `export PATH=$(npm bin -g):$PATH`

Once installed, you can use all the TaskMaster commands!

Quick test: Run `/project:help` to see all available commands.