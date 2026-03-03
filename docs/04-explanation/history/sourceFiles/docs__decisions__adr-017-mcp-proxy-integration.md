# ADR-017: MCP Proxy Integration for Docker Container Connectivity

## Status

**Accepted** - September 22, 2025

## Context

Dopemux MVP includes Docker-containerized MCP (Model Context Protocol) servers that provide advanced AI capabilities like sequential thinking, web search, and multi-model orchestration. However, Claude Code running on the host system cannot directly connect to stdio-based MCP servers running inside Docker containers.

### Problem Statement

1. **Connectivity Gap**: Claude Code expects MCP servers to be either:
   - Local stdio processes it can spawn directly
   - HTTP/SSE endpoints it can connect to

2. **Docker Isolation**: MCP servers in containers use stdio internally but are isolated from the host system's process space

3. **Development Experience**: The `/mcp` command in Claude Code fails, breaking the intended AI-assisted development workflow

4. **Integration Complexity**: Manual workarounds require complex Docker exec commands that don't integrate well with Claude Code's MCP client

### Previous Approaches Attempted

- **Direct Docker Exec**: `claude mcp add server-name docker exec container command`
  - Result: Failed due to stdio protocol mismatch

- **HTTP Port Mapping**: Exposing container ports directly
  - Result: MCP servers use stdio, not HTTP protocols

- **SSE Configuration**: Attempting direct SSE connections to container ports
  - Result: Containers don't expose SSE endpoints, only health checks

## Decision

We will implement an **MCP Proxy Bridge** using the `mcp-proxy` tool that:

1. **Bridges Protocol Gap**: Converts stdio MCP protocol to HTTP Server-Sent Events (SSE)
2. **Enables Docker Integration**: Uses `docker exec` to connect to containerized stdio servers
3. **Maintains Protocol Compliance**: Preserves full MCP protocol compatibility
4. **Provides Transparent Access**: Claude Code connects via standard SSE transport

### Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Claude Code   │    │   MCP Proxy     │    │ Docker Container│
│   (Host)        │◄──►│   (Bridge)      │◄──►│ (MCP Server)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
     SSE/HTTP              stdio/HTTP               stdio/internal
   Transport              Bridge Process          MCP Server Process
```

### Implementation Components

1. **MCP Proxy Server** (`mcp-proxy`):
   - Runs on host system (port 8080)
   - Manages multiple named MCP servers
   - Provides SSE endpoints for each server
   - Handles protocol translation and session management

2. **Configuration Management**:
   - JSON configuration file for server definitions
   - Docker exec command specifications
   - Automated setup scripts

3. **Claude Code Integration**:
   - SSE transport configuration
   - Named proxy endpoints
   - Standard MCP client connectivity

4. **Monitoring and Health Checks**:
   - Proxy health monitoring
   - Container connectivity verification
   - Automatic reconnection handling

## Implementation Details

### Proxy Configuration

```json
{
  "mcpServers": {
    "mas-sequential-thinking": {
      "command": "docker exec -i mcp-mas-sequential-thinking mcp-server-mas-sequential-thinking"
    },
    "exa": {
      "command": "docker exec -i mcp-exa python server.py"
    }
  }
}
```

### Claude Code Configuration

```bash
claude mcp add -t sse mas-sequential-thinking-proxy \
  http://127.0.0.1:8080/servers/mas-sequential-thinking/sse
```

### Automated Setup

```bash
# Complete setup with one command
./scripts/mcp-proxy-setup.sh setup

# Individual operations
./scripts/mcp-proxy-setup.sh start
./scripts/mcp-proxy-setup.sh claude
./scripts/mcp-proxy-setup.sh status
```

## Consequences

### Positive

1. **Seamless Integration**: Claude Code `/mcp` commands work transparently with Docker servers
2. **Protocol Compliance**: Full MCP specification compatibility maintained
3. **Development Experience**: Smooth AI-assisted development workflow
4. **Scalability**: Easy to add new containerized MCP servers
5. **Monitoring**: Built-in health checks and status monitoring
6. **Automation**: Scripts handle complex setup and maintenance
7. **Documentation**: Comprehensive guides for setup and troubleshooting

### Negative

1. **Additional Dependency**: Requires `mcp-proxy` tool installation
2. **Process Overhead**: Additional proxy process running on host
3. **Network Latency**: Small overhead from protocol translation (minimal on localhost)
4. **Debugging Complexity**: Additional layer for troubleshooting connectivity issues

### Neutral

1. **Resource Usage**: Proxy itself is lightweight (~50MB memory)
2. **Port Management**: Uses single port (8080) with multiple endpoints
3. **Security**: Localhost-only by default, configurable for external access

## Alternatives Considered

### 1. Native HTTP MCP Servers
**Description**: Modify MCP servers to expose HTTP/SSE directly
- **Pros**: No proxy needed, direct connectivity
- **Cons**: Requires modifying multiple server implementations, breaks container portability
- **Decision**: Rejected - too invasive and breaks existing server architecture

### 2. Claude Code Docker Plugin
**Description**: Extend Claude Code to support Docker exec directly
- **Pros**: Native integration, no additional processes
- **Cons**: Requires Claude Code modification, not available to us
- **Decision**: Rejected - not within our control

### 3. stdio-over-TCP Bridges
**Description**: Custom TCP bridges for each MCP server
- **Pros**: Lower level control, potentially faster
- **Cons**: Complex to implement, maintain multiple bridges
- **Decision**: Rejected - reinventing existing solutions

### 4. Docker Compose Networks
**Description**: Complex networking to expose stdio as network services
- **Pros**: Pure Docker solution
- **Cons**: Stdio protocol not network-native, complex setup
- **Decision**: Rejected - architecturally misaligned

## Implementation Plan

### Phase 1: Core Functionality ✅
- [x] Install and configure `mcp-proxy`
- [x] Basic stdio-to-SSE bridge for one server
- [x] Claude Code integration and testing
- [x] Verify `/mcp` command functionality

### Phase 2: Automation and Documentation ✅
- [x] Setup automation scripts
- [x] Comprehensive documentation
- [x] Health monitoring integration
- [x] Troubleshooting guides

### Phase 3: Multiple Server Support
- [ ] Add all containerized MCP servers to proxy
- [ ] Load balancing for high-traffic scenarios
- [ ] Advanced configuration options
- [ ] Performance optimization

### Phase 4: Production Readiness
- [ ] Systemd service configuration
- [ ] Docker Compose integration
- [ ] Security hardening
- [ ] Monitoring and alerting

## Success Metrics

1. **Functional**: `/mcp` commands work reliably with Docker servers
2. **Performance**: <100ms latency for MCP operations
3. **Reliability**: 99%+ uptime for proxy bridge
4. **Usability**: One-command setup for new environments
5. **Maintainability**: Clear documentation and automated health checks

## Security Considerations

1. **Network Exposure**: Proxy runs on localhost by default
2. **Docker Access**: Requires Docker socket access for exec commands
3. **CORS Configuration**: Configurable origin restrictions
4. **Container Security**: Maintains existing container isolation

## Monitoring and Observability

1. **Health Endpoints**: Built-in proxy health checks
2. **Connection Status**: Claude Code MCP connection monitoring
3. **Log Aggregation**: Centralized logging for troubleshooting
4. **Performance Metrics**: Response time and throughput monitoring

## Future Enhancements

1. **Authentication**: Add authentication layer for external access
2. **Rate Limiting**: Implement request throttling
3. **Load Balancing**: Multiple proxy instances for scaling
4. **WebSocket Support**: Alternative transport protocols
5. **Hot Reloading**: Configuration updates without restart

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [mcp-proxy GitHub Repository](https://github.com/sparfenyuk/mcp-proxy)
- [Claude Code Documentation](https://claude.ai/docs/code)
- [Docker Exec Reference](https://docs.docker.com/engine/reference/commandline/exec/)
- [Server-Sent Events Specification](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-09-22 | Claude Code | Initial ADR creation |

---

**Keywords**: MCP, Docker, Proxy, Claude Code, Architecture, Integration
**Category**: Infrastructure, Integration, AI/ML