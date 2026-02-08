---
id: mcp-updates
title: Mcp Updates
type: how-to
owner: '@hu3mann'
last_review: '2026-02-02'
next_review: '2026-05-03'
author: '@hu3mann'
date: '2026-02-05'
prelude: Mcp Updates (how-to) for dopemux documentation and developer workflows.
---
# MCP Server Update Tools

Automated tools for checking and updating MCP servers in the dopemux project.

## Quick Start

### Check for Updates
```bash
python3 scripts/check-mcp-updates.py
```

### Update a Specific Server
```bash
./scripts/update-mcp.sh zen
```

### Update All Servers
```bash
./scripts/update-mcp.sh --all
```

## Available Commands

### 1. Check for Updates (`check-mcp-updates.py`)

**Purpose**: Check all MCP servers for available updates

**Usage**:
```bash
python3 scripts/check-mcp-updates.py
```

**Output**:
```
🔍 Checking MCP server versions...

================================================================================
MCP SERVER UPDATE STATUS
================================================================================

🚀 ZEN
   Current:  7.0.1
   Latest:   7.0.2
   Status:   UPDATE AVAILABLE
   Upstream: https://github.com/BeehiveInnovations/zen-mcp-server
   Container: mcp-zen

✅ CONPORT
   Current:  0.3.4
   Latest:   0.3.4
   Status:   Up to date
   Upstream: Local service (no upstream)

================================================================================

✨ 1 update(s) available!
Run './scripts/update-mcp.sh <server-name>' to update
Example: ./scripts/update-mcp.sh zen
```

**Exit Codes**:
- `0`: All servers up to date
- `1`: Updates available or check failed

### 2. Update MCP Servers (`update-mcp.sh`)

**Purpose**: Easily update one or all MCP servers

**Usage**:
```bash
# Update single server
./scripts/update-mcp.sh zen
./scripts/update-mcp.sh conport
./scripts/update-mcp.sh serena

# Update all servers
./scripts/update-mcp.sh --all
```

**What It Does**:
1. Downloads latest version from upstream (for Zen)
2. Backs up your configuration files (.env)
3. Copies new files
4. Restores your configuration
5. Cleans Python cache
6. Rebuilds Docker container (if applicable)
7. Verifies the update

**Important**: After updating, you MUST restart Claude Code for changes to take effect.

## Supported MCP Servers

| Server | Type | Location | Update Source |
|--------|------|----------|---------------|
| zen | Docker | docker/mcp-servers/zen | GitHub: BeehiveInnovations/zen-mcp-server |
| conport | Local venv | services/conport | Local (no upstream) |
| serena | Docker | services/serena | Local (no upstream) |

## Update Process for Each Server

### Zen MCP

Zen MCP is an upstream open-source project. Updates come from GitHub.

**Update Process**:
1. Fetch latest from https://github.com/BeehiveInnovations/zen-mcp-server
2. Backup `.env` file
3. Copy new files
4. Restore `.env`
5. Rebuild Docker container
6. Verify new version

**Rollback**: If update fails, the backup .env is in `/tmp/zen-mcp-env-backup`

### ConPort MCP

ConPort is a local dopemux service with no upstream.

**Update Process**:
1. Activate venv
2. Reinstall with `pip install --upgrade -e .`

### Serena MCP

Serena is a local dopemux service with no upstream.

**Update Process**:
1. Rebuild Docker container from local source
2. Restart container

## After Updating

### 1. Verify Update (Optional)
```bash
# Check Zen version in Docker
docker exec mcp-zen python -c "from config import __version__; print(__version__)"

# Check ConPort version
cd services/conport && source venv/bin/activate && python -c "import conport; print(conport.__version__)"
```

### 2. Restart Claude Code (REQUIRED)

Claude Code caches MCP server connections. You MUST restart Claude Code for updates to take effect:

1. Quit Claude Code completely (Cmd+Q on macOS)
2. Reopen Claude Code
3. Verify new version: Use `/zen:version` or equivalent

### 3. Test MCP Servers

```bash
# Test Zen MCP
mcp__zen__version

# Test ConPort
mcp__conport__get_active_context --workspace_id "/Users/hue/code/dopemux-mvp"

# Test Serena
mcp__serena__get_workspace_status
```

## Troubleshooting

### Update Failed

**Check Docker containers**:
```bash
docker ps -a | grep mcp
docker logs mcp-zen
```

**Rebuild manually**:
```bash
cd docker/mcp-servers
docker-compose stop zen
docker-compose rm -f zen
docker-compose build --no-cache zen
docker-compose up -d zen
```

### Version Still Shows Old

**Cause**: Claude Code hasn't reconnected to updated server

**Solution**:
1. Quit Claude Code completely
2. Wait 5 seconds
3. Reopen Claude Code

### Configuration Lost

**Check backup**:
```bash
ls -la /tmp/zen-mcp-env-backup
```

**Restore manually**:
```bash
cp /tmp/zen-mcp-env-backup docker/mcp-servers/zen/zen-mcp-server/.env
```

## Automation

### Daily Update Checks

Add to cron (runs daily at 9 AM):
```bash
0 9 * * * cd /Users/hue/code/dopemux-mvp && python3 scripts/check-mcp-updates.py && [ $? -eq 1 ] && osascript -e 'display notification "MCP updates available!" with title "Dopemux"'
```

### Pre-Session Update Check

Add to your shell profile (~/.zshrc or ~/.bashrc):
```bash
alias dopemux-check="cd /Users/hue/code/dopemux-mvp && python3 scripts/check-mcp-updates.py"
```

## Development

### Adding New MCP Servers

1. Edit `scripts/check-mcp-updates.py`:
   - Add `get_<server>_version()` function
   - Add to `check_all_mcp_servers()` list

2. Edit `scripts/update-mcp.sh`:
   - Add `update_<server>()` function
   - Add to case statement

### Version Detection Methods

**Docker-based servers**:
```bash
docker exec <container> python -c "from config import __version__; print(__version__)"
```

**Local Python packages**:
```bash
python -c "import <package>; print(<package>.__version__)"
```

**Reading from files**:
```python
import re
with open("pyproject.toml") as f:
    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', f.read())
    version = match.group(1)
```

## Best Practices

1. **Always check before updating**: Run `check-mcp-updates.py` first
2. **Read changelogs**: Check upstream for breaking changes
3. **Test after update**: Verify MCP servers work correctly
4. **Backup configurations**: Script does this automatically, but be aware
5. **Restart Claude Code**: ALWAYS restart after updating

## Future Enhancements

- [ ] Automatic changelog display
- [ ] Version pinning support
- [ ] Rollback functionality
- [ ] Slack/Discord notifications
- [ ] CI/CD integration
- [ ] Update scheduling
- [ ] Dependency conflict detection

---

**Last Updated**: 2025-10-05
**Author**: Dopemux Development Team
**Related**: See ADR-012 for MCP integration architecture
