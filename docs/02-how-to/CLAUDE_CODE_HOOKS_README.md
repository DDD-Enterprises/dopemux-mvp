---
id: CLAUDE_CODE_HOOKS_README
title: Claude_Code_Hooks_Readme
type: how-to
owner: '@hu3mann'
last_review: '2026-02-01'
next_review: '2026-05-02'
---
# Claude Code Hooks Integration

This document explains how to set up and use Dopemux's external hook system for Claude Code integration. These hooks monitor Claude Code activity and trigger Dopemux workflows implicitly, without interfering with your Claude Code usage.

## Overview

The Claude Code hooks provide external monitoring that detects:
- Claude Code session starts
- File modifications made by Claude Code
- Git commits created by Claude Code
- Shell commands executed through Claude Code

## Quick Setup

### 1. Install Shell Hooks (Recommended)
```bash
# Automatically install shell hooks in your shell config
dopemux hooks --install-shell-hooks

# Follow the prompts to activate (restart shell or source config)
# This enables pre/post command monitoring for enhanced Claude Code detection
```

### 2. Start Hook Monitoring
```bash
# Start monitoring Claude Code activity
dopemux hooks --setup

# Monitor specific workspace
dopemux hooks --setup --workspace /path/to/project

# Stop monitoring
dopemux hooks --teardown
```

### 3. Check Status
```bash
# View current hook configuration
dopemux hooks --status

# Enable/disable specific hooks
dopemux hooks --enable git-commit
dopemux hooks --disable file-change
```

### 4. Manual Shell Integration (Alternative)
```bash
# Generate shell hook scripts for manual installation
dopemux hooks --shell-scripts

# Copy the output to your ~/.bashrc or ~/.zshrc
```

## Hook Types

### session-start (Enabled by default)
- **Triggers**: When Claude Code process starts
- **Action**: Prepares Dopemux environment, loads workspace context
- **Use Case**: Seamless session transitions

### file-change (Enabled by default)
- **Triggers**: Files modified in last 10 seconds in watched paths
- **Action**: Triggers background file indexing via Dope-Context
- **Use Case**: Automatic codebase indexing after Claude Code edits

### git-commit (Disabled by default - High risk)
- **Triggers**: Recent git commits (last 2 minutes)
- **Action**: Validates commit and updates tracking
- **Use Case**: Commit validation and workflow tracking
- **Warning**: Only enable if you want commit-time processing

### shell-command (Enabled by default)
- **Triggers**: Recent shell history containing Claude/Dopemux commands
- **Action**: Logs command patterns for workflow analysis
- **Use Case**: Command pattern analysis and optimization

## Uninstallation

### Remove Shell Hooks
```bash
# Automatically remove shell hooks
dopemux hooks --uninstall-shell-hooks

# Restart your shell to complete removal
```

### Stop Monitoring
```bash
# Stop Claude Code activity monitoring
dopemux hooks --teardown
```

## Troubleshooting

### Hooks Not Working
```bash
# Check hook status
dopemux hooks --status

# Verify monitoring is active
dopemux hooks --setup

# Check logs for errors
# Logs are written to console in verbose mode
```

### Performance Issues
```bash
# Disable resource-intensive hooks
dopemux hooks --disable file-change

# Limit watched paths
dopemux hooks --setup --workspace /current/project
```

### Conflicts with Other Tools
- Hooks are passive observers only
- No modification of Claude Code behavior
- Can be safely disabled if conflicts occur

## Safety Features

### Non-Blocking Design
- All hooks run asynchronously with timeouts (<500ms)
- Never blocks Claude Code operations
- Silent failures - won't interrupt your workflow
- Background processing for heavy operations

### Configurable Controls
- Enable/disable individual hooks
- Quiet mode (no notifications by default)
- Workspace-specific monitoring
- Easy opt-out at any time

### Error Isolation
- Hook failures don't affect Claude Code
- Comprehensive logging for debugging
- Graceful degradation when services unavailable

## Integration Points

### With Dopemux Workflows
- **Session Start**: Triggers context loading and environment preparation
- **File Changes**: Updates search indexes and triggers validation
- **Git Commits**: Updates progress tracking and validation
- **Commands**: Analyzes usage patterns for optimization

### With ConPort/Leantime
- Automatic progress logging for detected activities
- Decision tracking for workflow patterns
- Task status updates based on Claude Code actions

## Troubleshooting

### Hooks Not Triggering
```bash
# Check hook status
dopemux hooks --status

# Verify monitoring is active
dopemux hooks --setup

# Check logs for errors
# Logs are written to console in verbose mode
```

### Performance Issues
```bash
# Reduce monitoring frequency (modify source code)
# Disable high-overhead hooks
dopemux hooks --disable file-change

# Limit watched paths
dopemux hooks --setup --workspace /current/project
```

### Conflicts with Other Tools
- Hooks are passive observers only
- No modification of Claude Code behavior
- Can be safely disabled if conflicts occur

## Advanced Configuration

### Custom Workspace Paths
```python
# In Python code
from dopemux.hooks.claude_code_hooks import claude_hooks
claude_hooks.watched_paths = ['/path/to/project1', '/path/to/project2']
```

### Custom Timeouts
```python
# Adjust polling intervals (modify source code)
claude_hooks._check_interval = 5.0  # Check every 5 seconds
```

### Hook Event Filtering
```python
# Add custom filtering logic in _trigger_hook method
# Example: Only trigger for Python files
if not file_path.endswith('.py'):
    return
```

## Architecture Notes

### External Monitoring Approach
Unlike VS Code extensions that integrate directly, Claude Code hooks use external monitoring to:
- Avoid dependencies on Claude Code internals
- Work with any shell/editor combination
- Provide system-level observability
- Maintain separation of concerns

### Event Flow
```
Claude Code Activity → File System/Git Monitoring → Hook Detection → Dopemux Trigger → Background Processing → ConPort/Leantime Updates
```

### Performance Considerations
- Polling-based (2-second intervals) to balance responsiveness vs overhead
- File change detection uses `find` command for accuracy
- Background processing prevents UI blocking
- Configurable monitoring scope reduces resource usage

This hook system provides seamless Claude Code integration while maintaining the safety and non-blocking principles essential for ADHD-friendly development tools.
