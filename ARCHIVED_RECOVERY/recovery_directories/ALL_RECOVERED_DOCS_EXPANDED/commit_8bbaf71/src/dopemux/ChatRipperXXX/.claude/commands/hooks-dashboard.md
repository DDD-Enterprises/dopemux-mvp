# Hooks Performance Dashboard

Display current token usage, patterns, and optimization opportunities from Smart Hooks Phase 1.1.

## Usage

```bash
# Show all dashboard information
python .claude/hooks/dashboard.py

# Show current session usage
python .claude/hooks/dashboard.py --current

# Show usage patterns
python .claude/hooks/dashboard.py --patterns

# Show optimization suggestions
python .claude/hooks/dashboard.py --suggestions
```

## Enable Smart Optimization

To start tracking patterns, set the environment variable:

```bash
export HOOKS_ENABLE_SMART_OPTIMIZATION=1
```

This enables:
- Pattern tracking across Claude Code sessions
- Token usage estimation and monitoring
- Automatic optimization suggestions
- Historical usage analysis

The smart optimization system learns from your tool usage patterns and provides contextual suggestions to reduce token consumption.