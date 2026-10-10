# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the Dopemux MVP project.

## Active ADRs

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-017](adr-017-mcp-proxy-integration.md) | MCP Proxy Integration for Docker Container Connectivity | Accepted | 2025-09-22 |

## ADR Format

Our ADRs follow the standard format:
- **Status**: Proposed, Accepted, Deprecated, Superseded
- **Context**: Problem statement and background
- **Decision**: What we decided to do
- **Consequences**: Positive and negative outcomes

## Creating New ADRs

Use the provided Claude Code command:
```bash
/adr-new "Title of Decision"
```

This will create a new ADR with the correct numbering and template structure.

## Related Documentation

- [MCP Proxy Quick Start](../MCP_PROXY_QUICK_START.md)
- [MCP Proxy Setup Guide](../MCP_PROXY_SETUP_GUIDE.md)
- [System Architecture](../ARCHITECTURE.md)