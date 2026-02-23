# Vibe Configuration Summary for Dopemux

## ✅ Configuration Complete

Vibe has been successfully configured to work with Dopemux MCP servers.

## 📁 Files Created

- `.vibe/config.toml` - Main Vibe configuration with 8 MCP servers
- `.vibe/README.md` - Documentation and usage guide
- `.vibe/SUMMARY.md` - This summary file

## 🔌 MCP Servers Configured (8 total)

### HTTP Servers (3)
1. **dopemux_conport** - `http://localhost:3004`
   - Context and decision logging
   - ADHD-optimized workflow tracking

2. **dopemux_serena** - `http://localhost:3006`
   - ADHD-optimized code navigation
   - LSP-enhanced development

3. **dopemux_claude_context** - `http://localhost:3010`
   - Semantic code search
   - Context-aware documentation

### STDIO Servers (5)
4. **dopemux_pal** - API lookup and documentation
5. **dopemux_exa** - Neural web search
6. **dopemux_gpt_researcher** - Deep research capabilities
7. **dopemux_desktop_commander** - Desktop automation
8. **task_orchestrator** - ADHD task coordination

## 🎛️ Configuration Details

### Model Configuration
- **Active Model**: `devstral-2` (via Dopemux LiteLLM)
- **Provider**: `dopemux_litellm` (local LiteLLM proxy)
- **Temperature**: 0.2 for focused responses

### Tool Permissions
All MCP tools are configured with `"ask"` permission, meaning Vibe will:
- Prompt for confirmation before using MCP tools
- Show available tools in the tool palette
- Allow selective tool usage

### Session Management
- **Session Logging**: Enabled (100 session history)
- **Auto Updates**: Enabled

## 🚀 Usage

### Starting Vibe
```bash
# From project root (uses ./.vibe/config.toml)
vibe

# Or specify explicitly
vibe --workdir /path/to/dopemux-mvp
```

### Using MCP Tools
Vibe will automatically discover the MCP servers. You can:
- List available tools: `/tools`
- Use specific MCP tools: `dopemux_conport_*`, `dopemux_serena_*`, etc.
- Get tool help: `/help dopemux_conport_query`

### Environment Setup
Create `.vibe/.env` for API keys:
```bash
# Required API keys
echo "MISTRAL_API_KEY=your_key" > .vibe/.env
echo "OPENAI_API_KEY=your_key" >> .vibe/.env
echo "OPENROUTER_API_KEY=your_key" >> .vibe/.env
```

## 🔧 Customization

### Adding More MCP Servers
Add new `[[mcp_servers]]` sections to `config.toml`:
```toml
[[mcp_servers]]
name = "new_server"
transport = "http"
url = "http://localhost:8000"

[mcp_servers.headers]
Content-Type = "application/json"
```

### Adjusting Permissions
Modify the `[tools]` section:
```toml
[tools]
"dopemux_conport_*" = "always"  # Auto-approve
"dopemux_serena_*" = "ask"      # Prompt before use
"dangerous_tool" = "never"     # Disable completely
```

## 📋 Next Steps

1. **Start MCP servers**: `dopemux mcp start-all`
2. **Launch Vibe**: `vibe` from project root
3. **Verify tools**: `/tools` to see available MCP tools
4. **Test connectivity**: Try using `dopemux_conport_query` or similar

## 💡 Tips

- Vibe looks for config in `./.vibe/config.toml` first, then `~/.vibe/config.toml`
- Project-specific config ensures compatibility with Dopemux architecture
- All paths are absolute for reliability across worktrees
- Environment variables use `${VAR:-}` syntax for optional values

## 🔍 Troubleshooting

**Issue**: MCP servers not showing in Vibe
- **Check**: `dopemux mcp status` to verify servers are running
- **Check**: Configuration file permissions
- **Check**: Vibe version supports MCP server discovery

**Issue**: Connection errors to MCP servers
- **Check**: Docker containers are running
- **Check**: Ports 3004, 3006, 3010 are accessible
- **Check**: Environment variables are set

## 📚 References

- [Vibe Documentation](https://docs.mistral.ai/vibe/)
- [Dopemux MCP Architecture](../../docs/04-explanation/architecture/)
- [MCP Server Registry](../../src/dopemux/mcp/registry.yaml)