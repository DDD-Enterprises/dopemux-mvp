# Vibe Configuration Summary for Dopemux

## ✅ Configuration Complete

Vibe has been successfully configured to work with Dopemux MCP servers.

## 📁 Files Created

- `.vibe/config.toml` - Main Vibe configuration with MCP servers
- `.vibe/README.md` - Documentation and usage guide
- `.vibe/SUMMARY.md` - This summary file

## 🔌 MCP Servers Configured

Vibe is configured to connect to one or more Dopemux MCP servers as defined in `.vibe/config.toml`.

The exact set of HTTP and STDIO MCP servers, along with their ports and capabilities, is controlled by that config file.
Refer to `.vibe/config.toml` for the authoritative list of:
- Enabled MCP servers
- Connection types (HTTP / STDIO)
- Endpoints and ports

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