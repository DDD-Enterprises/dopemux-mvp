# MCP Proxy Setup Guide: Connecting Docker MCP Servers to Claude Code

## Overview

This guide provides a comprehensive solution for connecting Docker-containerized MCP (Model Context Protocol) servers to Claude Code using an HTTP proxy bridge. This setup enables seamless integration between locally running Claude Code and MCP servers running in isolated Docker environments.

## Problem Statement

### The Challenge
- **Docker MCP servers** use stdio (standard input/output) for communication
- **Claude Code** runs on the host system and cannot directly access stdio processes inside containers
- **Direct connection attempts** fail because Claude Code expects HTTP/SSE endpoints or stdio processes it can spawn directly

### The Solution
Use `mcp-proxy` to create an HTTP SSE bridge that:
1. Connects to stdio MCP servers inside Docker containers via `docker exec`
2. Exposes them as HTTP Server-Sent Events (SSE) endpoints
3. Allows Claude Code to connect via standard HTTP transport

## Prerequisites

### System Requirements
- Docker and Docker Compose installed and running
- Node.js and npm (for some MCP servers)
- Python 3.10+ with uv package manager
- Claude Code CLI installed and configured

### Running Docker Containers
Ensure your MCP servers are running in Docker containers. Example containers:
- `mcp-mas-sequential-thinking` (port 3001)
- `mcp-claude-context` (port 3007)
- `mcp-exa` (port 3008)
- `mcp-zen` (port 3003)
- `mcp-serena` (port 3006)

Verify containers are healthy:
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

## Installation and Setup

### Step 1: Install mcp-proxy

```bash
# Install mcp-proxy using uv tool manager
uv tool install mcp-proxy
```

This installs two executables:
- `mcp-proxy` - Main proxy server
- `mcp-reverse-proxy` - Reverse proxy functionality

### Step 2: Create Proxy Configuration

Create a proxy configuration file to define your Docker MCP servers:

**File: `mcp-proxy-config.json`**
```json
{
  "mcpServers": {
    "mas-sequential-thinking": {
      "command": "docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking"
    },
    "context7": {
      "command": "docker exec -i mcp-claude-context npx @modelcontextprotocol/server-context7"
    },
    "exa": {
      "command": "docker exec -i mcp-exa python server.py"
    },
    "zen": {
      "command": "docker exec -i mcp-zen python -m zen_mcp_server"
    },
    "serena": {
      "command": "docker exec -i mcp-serena python server.py"
    }
  }
}
```

**Important Notes:**
- Commands must be strings, not arrays
- Use `docker exec -i` for interactive mode
- Container names must match your running Docker containers
- Command paths must match the actual executables inside containers

### Step 3: Start the Proxy Server

#### Option A: Using Configuration File
```bash
mcp-proxy --named-server-config mcp-proxy-config.json --port 8080 --allow-origin '*'
```

#### Option B: Individual Named Servers (Recommended for testing)
```bash
mcp-proxy \
  --named-server mas-sequential-thinking 'docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking' \
  --port 8080 \
  --allow-origin '*'
```

#### Option C: Background Process
```bash
# Start in background for persistent operation
nohup mcp-proxy \
  --named-server mas-sequential-thinking 'docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking' \
  --port 8080 \
  --allow-origin '*' \
  > mcp-proxy.log 2>&1 &
```

### Step 4: Configure Claude Code

Add the proxied servers to Claude Code configuration:

```bash
# Add the proxied MCP server
claude mcp add -t sse mas-sequential-thinking-proxy http://127.0.0.1:8080/servers/mas-sequential-thinking/sse

# Add additional servers as needed
claude mcp add -t sse zen-proxy http://127.0.0.1:8080/servers/zen/sse
claude mcp add -t sse exa-proxy http://127.0.0.1:8080/servers/exa/sse
```

### Step 5: Verify Connection

Test the MCP server connections:

```bash
claude mcp list
```

Look for `✓ Connected` status for your proxied servers.

## Proxy Server Endpoints

When the proxy is running on port 8080, it exposes endpoints in this format:
```
http://127.0.0.1:8080/servers/{server-name}/sse
```

Example endpoints:
- `http://127.0.0.1:8080/servers/mas-sequential-thinking/sse`
- `http://127.0.0.1:8080/servers/zen/sse`
- `http://127.0.0.1:8080/servers/exa/sse`

## Troubleshooting

### Common Issues and Solutions

#### 1. Container Not Found
**Error:** `docker: Error response from daemon: No such container`
**Solution:** Verify container names and ensure containers are running
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

#### 2. Command Not Found in Container
**Error:** `executable file not found in $PATH`
**Solution:** Check the actual command path inside the container
```bash
docker exec -it mcp-mas-sequential-thinking which mcp-server-mas-sequential-thinking
docker exec -it mcp-mas-sequential-thinking ls -la /usr/local/bin/
```

#### 3. Permission Denied
**Error:** `Permission denied`
**Solution:** Ensure the user inside the container has execute permissions
```bash
docker exec -it mcp-mas-sequential-thinking ls -la /usr/local/bin/mcp-server-mas-sequential-thinking
```

#### 4. Connection Refused
**Error:** `Failed to connect` in Claude Code
**Solution:**
- Verify proxy is running: `curl http://127.0.0.1:8080/servers/mas-sequential-thinking/sse`
- Check proxy logs for errors
- Ensure CORS is enabled with `--allow-origin '*'`

#### 5. Proxy Startup Failures
**Common causes:**
- Invalid JSON configuration format
- Missing `mcpServers` key in config file
- Command strings vs arrays confusion
- Docker exec failures

### Debugging Commands

```bash
# Check proxy status
curl -v http://127.0.0.1:8080/servers/mas-sequential-thinking/sse

# Test Docker exec command directly
docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking

# Check container processes
docker exec mcp-mas-sequential-thinking ps aux

# View proxy logs (if running in background)
tail -f mcp-proxy.log

# Test MCP server health directly
docker logs mcp-mas-sequential-thinking
```

## Advanced Configuration

### Environment Variables
Pass environment variables to Docker containers:
```bash
mcp-proxy \
  --named-server myserver 'docker exec -i mycontainer env VAR=value mycommand' \
  --port 8080
```

### Custom Working Directory
```bash
mcp-proxy \
  --cwd /path/to/workdir \
  --named-server myserver 'docker exec -i mycontainer mycommand' \
  --port 8080
```

### Debug Mode
Enable detailed logging:
```bash
mcp-proxy \
  --debug \
  --named-server myserver 'docker exec -i mycontainer mycommand' \
  --port 8080
```

### Multiple Proxy Instances
Run multiple proxy instances on different ports:
```bash
# Proxy 1: Core servers
mcp-proxy --port 8080 --named-server server1 'docker exec -i container1 cmd1'

# Proxy 2: Additional servers
mcp-proxy --port 8081 --named-server server2 'docker exec -i container2 cmd2'
```

## Production Deployment

### Docker Compose Integration

Add proxy service to your `docker-compose.yml`:

```yaml
services:
  mcp-proxy:
    image: python:3.10-slim
    container_name: mcp-proxy
    ports:
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./mcp-proxy-config.json:/app/config.json
    command: >
      sh -c "
      pip install mcp-proxy &&
      mcp-proxy --named-server-config /app/config.json --port 8080 --host 0.0.0.0 --allow-origin '*'
      "
    depends_on:
      - mcp-mas-sequential-thinking
      - mcp-zen
      - mcp-exa
    restart: unless-stopped
```

### Systemd Service

Create a systemd service for automatic startup:

**File: `/etc/systemd/system/mcp-proxy.service`**
```ini
[Unit]
Description=MCP Proxy Server
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/your/project
ExecStart=/usr/local/bin/mcp-proxy --named-server-config mcp-proxy-config.json --port 8080 --allow-origin '*'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mcp-proxy
sudo systemctl start mcp-proxy
sudo systemctl status mcp-proxy
```

## Performance Optimization

### Resource Limits
- Proxy itself is lightweight (~50MB memory)
- Main resource usage comes from underlying MCP servers
- Consider Docker resource limits for containers

### Scaling Considerations
- Single proxy can handle multiple MCP servers
- Each MCP server connection is independent
- Network latency is minimal (localhost)
- Consider load balancing for high-traffic scenarios

## Security Considerations

### Network Security
- Proxy runs on localhost by default (127.0.0.1)
- Use `--host 0.0.0.0` only if external access needed
- Configure firewall rules appropriately
- Consider reverse proxy (nginx) for external exposure

### Docker Security
- Proxy needs access to Docker socket
- Use least-privilege container configurations
- Regularly update base images and dependencies
- Monitor container logs for security events

### CORS Configuration
- Current setup uses `--allow-origin '*'` for development
- Production should specify allowed origins
- Example: `--allow-origin https://your-domain.com`

## Monitoring and Maintenance

### Health Checks
```bash
# Proxy health
curl http://127.0.0.1:8080/health

# Individual server health via Claude Code
claude mcp list

# Container health
docker ps --filter "status=running"
```

### Log Monitoring
```bash
# Proxy logs
tail -f mcp-proxy.log

# Container logs
docker logs -f mcp-mas-sequential-thinking

# System logs
journalctl -u mcp-proxy -f
```

### Maintenance Tasks
- Regular container updates
- Proxy dependency updates: `uv tool upgrade mcp-proxy`
- Log rotation and cleanup
- Performance monitoring

## Integration Examples

### Claude Code Usage
Once configured, use MCP servers through Claude Code:

```bash
# List available MCP tools
/mcp tools list

# Use a specific tool
/mcp tool sequentialthinking "Analyze this complex problem..."

# Check server status
/mcp status
```

### API Integration
Direct HTTP access to proxy endpoints:
```bash
# Initialize connection
curl -X POST http://127.0.0.1:8080/servers/mas-sequential-thinking/sse \
  -H "Content-Type: application/json" \
  -d '{"method": "initialize", "params": {}}'
```

## Backup and Recovery

### Configuration Backup
```bash
# Backup proxy config
cp mcp-proxy-config.json mcp-proxy-config.backup.json

# Backup Claude Code config
cp ~/.claude.json ~/.claude.json.backup
```

### Disaster Recovery
1. Restore Docker containers
2. Restart proxy with backed up configuration
3. Restore Claude Code configuration
4. Verify connections

## Future Enhancements

### Planned Improvements
- Health check endpoints for monitoring
- Authentication and authorization
- Rate limiting and throttling
- WebSocket transport support
- Configuration hot-reloading

### Contributing
- Report issues with specific error messages
- Include Docker and proxy versions
- Provide minimal reproduction cases
- Test solutions in isolated environments

## References

- [MCP Proxy GitHub Repository](https://github.com/sparfenyuk/mcp-proxy)
- [Model Context Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Claude Code Documentation](https://claude.ai/docs/code)
- [Docker Exec Documentation](https://docs.docker.com/engine/reference/commandline/exec/)

---

**Last Updated:** September 22, 2025
**Version:** 1.0
**Tested With:** mcp-proxy 0.8.2, Claude Code latest, Docker 24.0+