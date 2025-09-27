# Technical Analysis: GPT-Researcher Codebase

> **Analysis Date**: 2025-09-26
> **Codebase Version**: 0.14.4
> **Repository**: https://github.com/assafelovic/gpt-researcher

## 🏗️ **Architecture Overview**

### **Core Components**

1. **GPTResearcher** (`gpt_researcher/agent.py`)
   - Main orchestrator class
   - Manages research lifecycle and configuration
   - Integrates all skills and components

2. **Research Skills** (`gpt_researcher/skills/`)
   - `ResearchConductor`: Orchestrates research execution
   - `ReportGenerator`: Handles report writing and formatting
   - `ContextManager`: Manages research context and memory
   - `DeepResearchSkill`: Tree-like exploration with depth/breadth control
   - `SourceCurator`: Manages and validates research sources

3. **MCP Integration** (`gpt_researcher/mcp/`)
   - `MCPClientManager`: Client lifecycle and configuration management
   - `MCPResearchSkill`: LLM-bound tool execution with result formatting
   - `streaming.py`: Real-time research streaming capabilities
   - `tool_selector.py`: Intelligent tool selection for research tasks

### **Research Capabilities**

#### **Deep Research Mode**
```python
# Example from backend/report_type/deep_research/main.py
researcher = GPTResearcher(
    query=task,
    report_type="deep",  # Triggers deep research
)
context = await researcher.conduct_research(on_progress=progress_callback)
```

**Features:**
- Tree-like exploration pattern
- Configurable depth and breadth
- Concurrent processing for speed
- Progress tracking with callbacks
- Runtime: ~5 minutes
- Cost: ~$0.4 (using o3-mini on "high" reasoning)

#### **Multi-Agent Research**
- LangGraph-based agent coordination
- Specialized agents for different research tasks
- STORM paper-inspired multi-agent workflows
- Generates 5-6 page reports in multiple formats

#### **MCP Strategy Options**
- **"fast"**: Single MCP execution with original query (default)
- **"deep"**: MCP execution for all sub-queries (thorough)
- **"disabled"**: Skip MCP entirely, web-only research

### **MCP Implementation Details**

#### **MCPClientManager** Analysis
```python
# From gpt_researcher/mcp/client.py
class MCPClientManager:
    """Sophisticated MCP client management"""

    def convert_configs_to_langchain_format(self):
        # Auto-detects transport type from URL
        # Supports stdio, websocket, streamable_http
        # Handles env vars and authentication
```

**Key Features:**
- Transport auto-detection (stdio/websocket/http)
- Environment variable management
- Authentication token support
- Graceful error handling
- Resource cleanup

#### **MCPResearchSkill** Analysis
```python
# From gpt_researcher/mcp/research.py
async def conduct_research_with_tools(self, query: str, selected_tools: List):
    # Binds tools to LLM
    llm_with_tools = llm_provider.llm.bind_tools(selected_tools)
    # Executes research with bound tools
    # Formats results into standard search format
```

**Key Features:**
- LLM-bound tool execution
- Intelligent result processing
- Error handling and fallbacks
- Standardized output formatting

### **Configuration System**

#### **MCP Configuration Support**
```python
# Example MCP config structure
mcp_configs = [{
    "name": "github",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {"GITHUB_TOKEN": os.getenv("GITHUB_TOKEN")},
    "connection_url": "ws://localhost:8000",
    "connection_type": "websocket",
    "connection_token": "auth_token"
}]
```

**Supported Options:**
- Command-based servers (stdio)
- WebSocket connections
- HTTP/HTTPS endpoints
- Environment variable injection
- Authentication tokens

### **Research Retrievers**

**Available Retriever Types:**
- `tavily` - Primary web search
- `google` - Google Search API
- `bing` - Bing Search API
- `duckduckgo` - DuckDuckGo search
- `arxiv` - Academic paper search
- `pubmed` - Medical research
- `semantic_scholar` - Academic search
- `mcp` - MCP server integration

**Hybrid Research:**
```bash
export RETRIEVER=tavily,mcp  # Combines web + MCP research
```

### **Report Types**

1. **Basic Report** (`basic_report/`)
   - Simple web research
   - Standard report format
   - Fast execution

2. **Detailed Report** (`detailed_report/`)
   - Enhanced research depth
   - More comprehensive sources
   - Structured sections

3. **Deep Research** (`deep_research/`)
   - Tree exploration algorithm
   - Recursive sub-topic investigation
   - Maximum thoroughness

### **Integration Points for Dopemux**

#### **Strengths for Integration**
1. **Modular Architecture**: Easy to extract specific components
2. **Skills-Based Design**: Aligns with Dopemux plugin architecture
3. **MCP Native**: Already designed for MCP integration
4. **Progress Tracking**: Built-in callbacks for progress monitoring
5. **Cost Awareness**: Integrated cost tracking for budget management

#### **Compatibility Analysis**
- **✅ ADHD-Friendly**: Supports chunking, progress visualization
- **✅ Async Architecture**: Non-blocking execution patterns
- **✅ Configuration Driven**: Easy to customize for Dopemux
- **✅ Error Handling**: Robust error management and recovery
- **✅ Resource Management**: Proper cleanup and resource handling

### **Key Classes for Dopemux Integration**

1. **DeepResearchSkill** - For advanced research workflows
2. **MCPResearchSkill** - For MCP tool integration
3. **ResearchConductor** - For orchestrating research tasks
4. **ContextManager** - For managing research context across sessions

### **Performance Characteristics**

- **Deep Research**: 5 minutes average runtime
- **Cost**: ~$0.4 per deep research (o3-mini)
- **Concurrency**: Built-in concurrent processing
- **Memory**: Efficient context management
- **Scalability**: Handles multiple research streams

### **Dependencies**

**Core Dependencies:**
- `langchain` + `langgraph` - Agent framework
- `mcp` + `langchain-mcp-adapters` - MCP integration
- `aiofiles`, `aiohttp` - Async I/O
- `beautifulsoup4`, `lxml` - Web scraping
- Various retriever APIs

**Optional Dependencies:**
- `playwright` - Advanced web scraping
- `selenium` - Browser automation
- Provider-specific packages (anthropic, groq, etc.)

## 🔍 **Security Analysis**

**Strengths:**
- Environment variable configuration
- No hardcoded credentials
- Proper input validation
- Error handling prevents information leakage

**Considerations:**
- API key management required
- Web scraping rate limiting
- MCP server trust requirements

## 📊 **Integration Feasibility**

**High Compatibility Factors:**
- Modern async/await patterns
- Type hints and documentation
- Modular skill-based architecture
- Comprehensive configuration system
- Built-in progress tracking

**Low Risk Integration:**
- Well-defined interfaces
- Extensive error handling
- Resource cleanup patterns
- No global state dependencies

**Recommended Integration Approach:**
1. Start with MCP server (gptr-mcp)
2. Extract core skills for Dopemux plugin
3. Add ADHD-specific optimizations
4. Full CLI integration for advanced workflows