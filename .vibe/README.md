# Vibe Configuration for Dopemux

This directory contains Vibe-specific configuration for working with Dopemux MCP servers.

## Configuration Files

- `config.toml` - Main Vibe configuration with MCP server definitions
- `.env` - (Optional) API keys and environment variables

## MCP Servers Configured

The following Dopemux MCP servers are configured for Vibe:

1. **dopemux_conport** - Context and decision logging (HTTP)
2. **dopemux_serena** - ADHD-optimized code navigation (HTTP)  
3. **dopemux_claude_context** - Semantic code search (HTTP)
4. **dopemux_pal** - API lookup and documentation (STDIO)
5. **dopemux_exa** - Neural web search (STDIO)
6. **dopemux_gpt_researcher** - Deep research (STDIO)
7. **dopemux_desktop_commander** - Desktop automation (STDIO)
8. **task_orchestrator** - Task coordination (STDIO)

## Usage

Vibe will automatically discover this configuration when run from the project directory.

To use a specific MCP tool, reference it by name:
- `dopemux_conport_*` tools
- `dopemux_serena_*` tools  
- etc.

## Environment Variables

### Quick Setup
Run the setup script to create your `.env` file:
```bash
./.vibe/setup_env.sh
```

### Manual Setup
Create a `.env` file in this directory for API keys:

```bash
cp .vibe/.env.example .vibe/.env
# Then edit .vibe/.env and fill in your actual API keys
```

### Required API Keys

**Core Keys:**
- `MISTRAL_API_KEY` - Required for Vibe core functionality
- `OPENAI_API_KEY` - Used by multiple MCP servers
- `OPENROUTER_API_KEY` - Used by PAL and other servers

**Optional Keys (for specific MCP servers):**
- `EXA_API_KEY` - For dopemux_exa neural search
- `ANTHROPIC_API_KEY` - For some MCP servers
- `TAVILY_API_KEY` - For gpt-researcher
- `PERPLEXITY_API_KEY` - For gpt-researcher
- `GEMINI_API_KEY` - For some MCP servers
- `VOYAGEAI_API_KEY` - For claude-context
- `XAI_API_KEY` - For PAL

**Auto-generated Keys:**
- `DOPEMUX_LITELLM_MASTER_KEY` - Automatically generated when you run `dopemux start`

## Customization

You can customize the configuration by:

1. **Adding new MCP servers** - Add new `[[mcp_servers]]` sections
2. **Adjusting tool permissions** - Modify the `[tools]` section
3. **Changing models** - Update the `[[models]]` section
4. **Adding providers** - Add new `[[providers]]` sections

## Notes

- Vibe looks for configuration in `./.vibe/config.toml` first, then falls back to `~/.vibe/config.toml`
- This project-specific configuration ensures Vibe works seamlessly with Dopemux's MCP architecture
- The configuration maps Dopemux's MCP servers to Vibe's expected TOML format