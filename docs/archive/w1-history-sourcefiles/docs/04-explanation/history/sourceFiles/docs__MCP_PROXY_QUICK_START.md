# MCP Proxy Quick Start Guide

## TL;DR - Get Running in 2 Minutes

```bash
# 1. Install proxy
uv tool install mcp-proxy

# 2. Start proxy (single server for testing)
mcp-proxy --named-server mas-sequential-thinking 'docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking' --port 8080 --allow-origin '*' &

# 3. Configure Claude Code
claude mcp add -t sse mas-sequential-thinking-proxy http://127.0.0.1:8080/servers/mas-sequential-thinking/sse

# 4. Test connection
claude mcp list

# 5. Use in Claude Code
# Now you can use /mcp commands!
```

## What This Solves

❌ **Before**: `/mcp` command fails because Claude Code can't connect to Docker MCP servers
✅ **After**: `/mcp` command works seamlessly with containerized servers

## Automated Setup

Use the provided script for full automation:

```bash
# Complete setup with one command
./scripts/mcp-proxy-setup.sh setup

# Or step by step
./scripts/mcp-proxy-setup.sh install
./scripts/mcp-proxy-setup.sh check
./scripts/mcp-proxy-setup.sh start
./scripts/mcp-proxy-setup.sh claude
```

## Verify Working Setup

```bash
# Check status
./scripts/mcp-proxy-setup.sh status

# Should show:
# ✓ Proxy is running
# ✓ Containers are healthy
# ✓ Connected servers in Claude Code
```

## Common Commands

```bash
# Start/stop proxy
./scripts/mcp-proxy-setup.sh start
./scripts/mcp-proxy-setup.sh stop
./scripts/mcp-proxy-setup.sh restart

# View logs
./scripts/mcp-proxy-setup.sh logs

# Test connections
claude mcp list
```

## Available Proxied Servers

After setup, these servers are available in Claude Code:

- **mas-sequential-thinking-proxy** - Advanced reasoning and analysis
- **exa-proxy** - Web search and research
- **zen-proxy** - Multi-model orchestration
- **serena-proxy** - Enhanced code navigation

## Troubleshooting

### Quick Fixes

```bash
# Proxy not starting?
./scripts/mcp-proxy-setup.sh check

# Connection failed?
./scripts/mcp-proxy-setup.sh test

# Claude Code issues?
claude mcp list
```

### Common Issues

1. **"Failed to connect"** → Check if containers are running: `docker ps`
2. **"Connection refused"** → Restart proxy: `./scripts/mcp-proxy-setup.sh restart`
3. **"Command not found"** → Check container health: `docker logs mcp-mas-sequential-thinking`

## Advanced Usage

### Multiple Servers
```bash
mcp-proxy \
  --named-server server1 'docker exec -i container1 command1' \
  --named-server server2 'docker exec -i container2 command2' \
  --port 8080 --allow-origin '*'
```

### Background Process
```bash
nohup mcp-proxy \
  --named-server mas-sequential-thinking 'docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking' \
  --port 8080 --allow-origin '*' \
  > mcp-proxy.log 2>&1 &
```

### Health Monitoring
```bash
# Check proxy health
curl http://127.0.0.1:8080/servers/mas-sequential-thinking/sse

# Monitor logs
tail -f mcp-proxy.log
```

---

**Need more details?** See the [complete setup guide](./MCP_PROXY_SETUP_GUIDE.md)