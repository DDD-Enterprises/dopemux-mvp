# GPT-Researcher MCP Server

An MCP (Model Context Protocol) server wrapper for GPT-Researcher, providing ADHD-optimized research capabilities through a standardized interface.

## Features

- **6 Research Tools**: Quick search, deep research, documentation search, code examples, trend analysis, and research summarization
- **ADHD Optimizations**: Built-in break intervals, focus duration management, and gentle notifications
- **Session Management**: Track active research tasks and maintain history
- **Multi-Engine Support**: Integrates with Exa, Tavily, Perplexity, and Context7 search engines

## Installation

1. Ensure GPT-Researcher is installed:
```bash
pip install gpt-researcher
```

2. Set up environment variables (optional, for full functionality):
```bash
export EXA_API_KEY="your-exa-key"
export TAVILY_API_KEY="your-tavily-key"
export PERPLEXITY_API_KEY="your-perplexity-key"
export CONTEXT7_API_KEY="your-context7-key"
```

## Usage

### Standalone Testing

Test the server with the provided test script:
```bash
python test_server.py
```

### Integration with Claude

Add the following to your Claude configuration (`.claude/claude_config.json`):

```json
{
  "mcpServers": {
    "gpt-researcher": {
      "command": "python",
      "args": [
        "/path/to/mcp-server/server.py"
      ],
      "env": {
        "WORKSPACE_PATH": "/your/workspace/path",
        "EXA_API_KEY": "${EXA_API_KEY}",
        "TAVILY_API_KEY": "${TAVILY_API_KEY}",
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}",
        "CONTEXT7_API_KEY": "${CONTEXT7_API_KEY}"
      }
    }
  }
}
```

### Available Tools

1. **quick_search**: Fast searches for immediate answers
   - Parameters: `query` (string), `max_results` (number, default: 5)
   - ADHD-optimized with 10-minute focus duration

2. **deep_research**: Comprehensive research with multiple sources
   - Parameters: `topic` (string), `research_type` (general/technical/academic), `max_time_minutes` (number, default: 25)
   - Full Pomodoro session with break reminders

3. **documentation_search**: Search technical documentation
   - Parameters: `technology` (string), `query` (string), `version` (optional string)
   - Focused on official docs and API references

4. **code_examples**: Find code examples and implementations
   - Parameters: `language` (string), `concept` (string), `framework` (optional string)
   - Returns practical, runnable examples

5. **trend_analysis**: Analyze trends and recent developments
   - Parameters: `domain` (string), `timeframe` (day/week/month/year)
   - Identifies emerging patterns and technologies

6. **summarize_research**: Summarize previous research results
   - Parameters: `task_id` (string), `format` (brief/detailed/bullets)
   - ADHD-friendly formatting options

### Resources

The server provides access to:
- `research://active-tasks`: List of currently active research tasks
- `research://history`: Previous research results and summaries

## Architecture

The server integrates with the existing GPT-Researcher components:
- `ResearchTaskOrchestrator`: Manages research workflows
- `SearchOrchestrator`: Coordinates multiple search engines
- `QueryClassificationEngine`: Intelligently routes queries
- `ADHDConfiguration`: Applies neurodivergent-friendly optimizations

## Development

### Running in Debug Mode

Enable debug logging:
```bash
DEBUG=true python server.py
```

### Testing

Run the test suite:
```bash
python test_server.py
```

Expected output:
- ✅ Initialization successful
- ✅ 6 tools available
- ✅ 2 resources available
- ⚠️ Search tools require API keys for full functionality

## Phase 1 Implementation Status

- ✅ MCP server implementation complete
- ✅ All 6 research tools implemented
- ✅ ADHD optimizations integrated
- ✅ Stdio protocol support
- ✅ Resource management
- ⏳ API key configuration needed for production use

## Next Steps

1. **Phase 2**: Continue development of ADHD-optimized SearchOrchestrator
2. **Integration**: Add to Dopemux MCP broker configuration
3. **Testing**: Validate with real API keys and production workloads
4. **Documentation**: Create user guides for research workflows