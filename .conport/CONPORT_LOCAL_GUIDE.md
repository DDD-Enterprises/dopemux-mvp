# ConPort Local Service Guide

## Quick Reference for ADHD Session Memory

### 🎯 Service Status
```bash
# Check if ConPort is running
./scripts/conport/status.sh

# Quick status for scripts
./scripts/conport/status.sh --quick
# Returns: healthy:3007 | unhealthy:3007 | running:unknown_port | stopped
```

### 🚀 Service Management
```bash
# Start ConPort (auto-detects port)
./scripts/conport/start.sh

# Start on specific port
./scripts/conport/start.sh --port 3008

# Stop ConPort gracefully
./scripts/conport/stop.sh

# Restart with validation
./scripts/conport/restart.sh
```

### 📊 Current Installation Details

**Service Endpoint**: `http://127.0.0.1:3007/mcp`
**Health Check**: `http://127.0.0.1:3007/`
**Process ID**: 50757
**Status**: ✅ FULLY OPERATIONAL

**Data Locations**:
- Database: `context_portal/context.db` (112K)
- Vector Data: `context_portal/conport_vector_data/`
- Session Files: `.conport/sessions/`
- Service Logs: `.conport/logs/conport.log`

### 🧠 ADHD Workflow Integration

**Session Persistence**: ConPort automatically preserves:
- Active development context
- Decision history with rationale
- Progress milestones and visual feedback
- Project knowledge graph relationships

**MCP Integration**: Available in Claude Code via:
- Server name: `conport`
- Transport: HTTP via mcp-proxy
- Tools: Context management, decision logging, progress tracking

### 🔧 Configuration Files

**MCP Config**: `.claude/claude_config.json`
```json
"conport": {
  "command": "uvx",
  "args": ["mcp-proxy", "--transport", "streamablehttp", "http://127.0.0.1:3007/mcp"]
}
```

**Environment**: `.env.conport` (ADHD-optimized settings)
- Session timeout: 2 hours for deep work
- Context retention: 30 days
- Vector search: enabled with sentence-transformers

### 📋 Troubleshooting

**Service Won't Start**:
1. Check if port 3007+ is available: `lsof -i :3007`
2. Verify virtual environment: `services/conport/venv/bin/activate`
3. Check startup logs: `tail -f .conport/logs/startup.log`

**MCP Not Connecting**:
1. Restart Claude Code to pick up config changes
2. Verify service health: `./scripts/conport/status.sh --quick`
3. Check mcp-proxy is installed: `uvx --help`

**Data Issues**:
- Database locked: Stop all ConPort processes, then restart
- Vector data missing: Rebuilds automatically on first query
- Session files corrupted: Located in `.conport/sessions/` for manual recovery

### 🎉 Success Indicators

✅ **Healthy Status**: `./scripts/conport/status.sh` shows "FULLY OPERATIONAL"
✅ **MCP Available**: ConPort appears in Claude Code MCP servers
✅ **Data Preserved**: Existing 112K database and vector embeddings intact
✅ **ADHD Ready**: Session memory works across interruptions

---
*Generated: 2025-09-26 - ConPort Local Installation Complete*