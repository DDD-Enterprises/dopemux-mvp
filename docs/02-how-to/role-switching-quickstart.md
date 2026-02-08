---
id: role-switching-quickstart
title: Role Switching Quickstart
type: how-to
owner: '@hu3mann'
last_review: '2026-02-06'
next_review: '2026-05-06'
author: '@hu3mann'
date: '2026-02-05'
prelude: Role Switching Quickstart (how-to) for dopemux documentation and developer
  workflows.
---
# Role Switching Quickstart

## Goal
Switch Dopemux agent roles quickly using the built-in CLI role system.

## Prerequisites
- Dopemux installed
- MCP services running (`dopemux mcp status`)

## Switch Roles (Primary Workflow)
```bash
# Preview what changes (safe)
dopemux start --role quickfix --dry-run

# Apply role and launch
dopemux start --role quickfix
```

Common roles:
- `quickfix`
- `act`
- `plan`
- `research`
- `all`

## Switch Roles In Tmux Agent Panes
```bash
# Primary pane
dopemux tmux agent switch-role act

# Secondary pane
dopemux tmux agent switch-role plan --target secondary

# Explicit pane id
dopemux tmux agent switch-role research --pane %27
```

## Legacy Script (Optional)
```bash
~/.claude/switch-role.sh quickfix
~/.claude/switch-role.sh act
```

## Verify Active Role
```bash
echo "$DOPEMUX_AGENT_ROLE"
```

Or inspect generated Claude MCP config:
```bash
cat ~/.claude/config/mcp_servers.json
```

## Troubleshooting
- Role switch fails:
  - Run `dopemux mcp status`
  - Start required services shown by the CLI warning
- Tools missing after switch:
  - Restart Claude Code session
  - Re-run `dopemux start --role <role>`
- Role mismatch across panes:
  - Re-target pane explicitly with `--pane` or `--target`

## Notes
- Prefer focused roles (`quickfix`, `act`, `plan`, `research`) over `all` to reduce tool noise.
- Use `--dry-run` when changing roles mid-task.
