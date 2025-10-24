# GPT-Researcher Langchain Compatibility Fix

## Problem

gpt-researcher 0.14.4 is incompatible with langchain 1.0+ due to deprecated import paths:
- `langchain.docstore.document` → Removed in langchain 1.0
- `langchain.vectorstores` → Removed in langchain 1.0

**Symptoms**:
- Container `mcp-gptr-mcp` exits with `ModuleNotFoundError`
- Port 3009 shows "upstream_exit_code: 1"
- Container status: UNHEALTHY

## Solution

Downgrade langchain stack to versions compatible with gpt-researcher 0.14.4:

```dockerfile
# In docker/mcp-servers/gptr-mcp/Dockerfile
RUN pip install --no-cache-dir --force-reinstall \
    'langchain==0.0.354' \
    'langchain-community==0.0.20' \
    'langchain-core==0.1.23' \
    'langsmith==0.0.87' \
    'numpy<2'
```

### Version Compatibility Matrix

| Package | Version | Reason |
|---------|---------|--------|
| langchain | 0.0.354 | Last version with old import structure |
| langchain-community | 0.0.20 | Compatible with langsmith 0.0.87 |
| langchain-core | 0.1.23 | Works with langchain 0.0.354 |
| langsmith | 0.0.87 | Compatible with langchain-community 0.0.20 |
| numpy | <2 | Avoid numpy 2.0 breaking changes |

## Rebuild Instructions

```bash
# Rebuild the container
cd docker/mcp-servers
docker-compose up -d --build mcp-gptr-mcp

# Verify health
docker ps --filter "name=gptr" --format "{{.Names}}: {{.Status}}"

# Check logs for successful startup
docker logs mcp-gptr-mcp
```

## Testing

```bash
# Test MCP connection
curl -X POST http://localhost:3009/research \
  -H "Content-Type: application/json" \
  -d '{"query": "test query"}'

# Or via Claude Code MCP
# gpt-researcher should appear in available MCP tools
```

## Alternative: Local stdio MCP

If Docker container remains problematic, use the local stdio MCP server (Decision #169):

```json
// In .claude.json
{
  "mcpServers": {
    "gpt-researcher": {
      "type": "stdio",
      "command": "python3",
      "args": ["/Users/hue/code/dopemux-mvp/scripts/gpt-researcher/mcp_server.py"]
    }
  }
}
```

## Related Decisions

- **Decision #189**: Original diagnosis of langchain incompatibility
- **Decision #169**: Temporary stdio MCP workaround
- **Decision #190**: Complete MCP investigation results
- **Decision #214**: This Docker fix approach

## Future Considerations

Monitor gpt-researcher releases for langchain 1.0 compatibility. When available:
1. Remove version pins from Dockerfile
2. Update to latest gpt-researcher version
3. Rebuild container
4. Test thoroughly

## ADHD Note

**Quick Fix**: Use local stdio MCP (Decision #169) - works immediately, no Docker rebuild needed.

**Proper Fix**: This Docker approach - requires rebuild, but provides containerized isolation and port 3009 SSE interface for other tools.
