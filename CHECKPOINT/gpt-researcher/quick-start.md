# Quick Start: Immediate Research Capability

> **Goal**: Get deep research running in Dopemux within 1 hour

## 🚀 **Phase 1: Immediate Deployment**

### **Prerequisites**
- OpenAI API key
- Tavily API key (sign up at https://tavily.com)
- Dopemux with MCP support

### **Step 1: Install gptr-mcp Server**

#### **Option A: pip install (Recommended)**
```bash
# Install the MCP server
pip install gptr-mcp

# Verify installation
gptr-mcp --help
```

#### **Option B: Docker**
```bash
# Pull the Docker image
docker pull gptresearcher/gptr-mcp

# Test run
docker run --rm gptresearcher/gptr-mcp --help
```

### **Step 2: Configure Environment**

Create `.env` file for API keys:
```bash
# Required API keys
export OPENAI_API_KEY="your-openai-api-key-here"
export TAVILY_API_KEY="your-tavily-api-key-here"

# Optional: Custom OpenAI endpoint
export OPENAI_BASE_URL="https://api.openai.com/v1"

# Optional: Research configuration
export RETRIEVER="tavily"  # Default search engine
export DOC_PATH="./docs"   # For local document research
```

### **Step 3: Add to Dopemux MCP Configuration**

Add this to your Dopemux MCP settings:

#### **For pip installation:**
```json
{
  "name": "gpt-researcher",
  "command": "gptr-mcp",
  "args": [],
  "env": {
    "OPENAI_API_KEY": "${OPENAI_API_KEY}",
    "TAVILY_API_KEY": "${TAVILY_API_KEY}"
  }
}
```

#### **For Docker:**
```json
{
  "name": "gpt-researcher",
  "command": "docker",
  "args": [
    "run", "--rm",
    "-e", "OPENAI_API_KEY=${OPENAI_API_KEY}",
    "-e", "TAVILY_API_KEY=${TAVILY_API_KEY}",
    "gptresearcher/gptr-mcp"
  ]
}
```

### **Step 4: Test the Integration**

#### **Basic Test**
```bash
# In Dopemux, test MCP connection
dopemux mcp test gpt-researcher
```

#### **Quick Search Test**
Use the `quick_search` tool for immediate results:
```json
{
  "tool": "quick_search",
  "arguments": {
    "query": "latest AI developments 2024"
  }
}
```

#### **Deep Research Test**
Use the `deep_research` tool for comprehensive analysis:
```json
{
  "tool": "deep_research",
  "arguments": {
    "query": "Impact of AI on software development workflows",
    "report_type": "detailed"
  }
}
```

---

## 🔧 **Available Research Tools**

### **1. quick_search**
Fast web search with relevant snippets
```json
{
  "tool": "quick_search",
  "arguments": {
    "query": "your search query",
    "max_results": 10
  }
}
```

### **2. deep_research**
Comprehensive research with tree exploration
```json
{
  "tool": "deep_research",
  "arguments": {
    "query": "your research topic",
    "report_type": "detailed",
    "depth": 3,
    "breadth": 5
  }
}
```

### **3. research_resource**
Retrieve specific web resources
```json
{
  "tool": "research_resource",
  "arguments": {
    "url": "https://example.com/article",
    "extract_content": true
  }
}
```

### **4. write_report**
Generate formatted reports from research
```json
{
  "tool": "write_report",
  "arguments": {
    "context": "research context here",
    "report_type": "markdown",
    "tone": "professional"
  }
}
```

### **5. get_research_sources**
Access research sources and citations
```json
{
  "tool": "get_research_sources",
  "arguments": {
    "research_id": "research-session-id"
  }
}
```

### **6. get_research_context**
Retrieve full research context
```json
{
  "tool": "get_research_context",
  "arguments": {
    "research_id": "research-session-id",
    "include_sources": true
  }
}
```

---

## 📋 **Common Research Workflows**

### **Workflow 1: Quick Information Gathering**
```bash
# 1. Quick search for overview
quick_search: "AI safety regulations 2024"

# 2. Get specific resource if needed
research_resource: "https://relevant-article.com"

# 3. Generate summary report
write_report: "combine findings into executive summary"
```

### **Workflow 2: Deep Research Analysis**
```bash
# 1. Start deep research
deep_research: "quantum computing commercial applications"
# Takes ~5 minutes, costs ~$0.40

# 2. Get full context
get_research_context: "research-session-id"

# 3. Access sources for citations
get_research_sources: "research-session-id"
```

### **Workflow 3: Competitive Analysis**
```bash
# 1. Research each competitor
deep_research: "Company A AI strategy 2024"
deep_research: "Company B AI strategy 2024"

# 2. Generate comparative report
write_report: "compare AI strategies of Company A vs Company B"
```

---

## ⚡ **Performance Characteristics**

### **Response Times**
- `quick_search`: 5-10 seconds
- `research_resource`: 3-5 seconds
- `deep_research`: 3-7 minutes
- `write_report`: 30-60 seconds

### **Costs (using OpenAI GPT-4)**
- `quick_search`: ~$0.05 per query
- `deep_research`: ~$0.40 per research
- `write_report`: ~$0.10 per report

### **Rate Limits**
- Respect OpenAI rate limits
- Tavily: 1000 requests/month (free tier)
- Built-in rate limiting and retries

---

## 🐛 **Troubleshooting**

### **Common Issues**

#### **"MCP server not responding"**
```bash
# Check if server is running
ps aux | grep gptr-mcp

# Test server directly
gptr-mcp --test-connection

# Check logs
tail -f ~/.dopemux/logs/mcp-gpt-researcher.log
```

#### **"API key errors"**
```bash
# Verify environment variables
echo $OPENAI_API_KEY
echo $TAVILY_API_KEY

# Test API keys directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

#### **"Research taking too long"**
- Deep research normally takes 3-7 minutes
- Use `quick_search` for faster results
- Check API rate limits and quotas

#### **"Poor research quality"**
- Verify Tavily API key is working
- Try different search terms
- Use more specific queries

### **Debug Mode**
```bash
# Run server in debug mode
GPTR_DEBUG=true gptr-mcp

# Verbose logging
GPTR_LOG_LEVEL=DEBUG gptr-mcp
```

---

## 📊 **Success Validation**

### **Checklist: Ready for Production**
- [ ] MCP server responds to health checks
- [ ] All 6 research tools work correctly
- [ ] API keys are properly configured
- [ ] Research results are high quality
- [ ] Response times are acceptable
- [ ] Error handling works properly

### **Performance Benchmarks**
```bash
# Test search speed
time dopemux mcp call gpt-researcher quick_search '{"query": "test"}'

# Test deep research
time dopemux mcp call gpt-researcher deep_research '{"query": "AI trends", "report_type": "basic"}'
```

### **Quality Checks**
- Research results are relevant and current
- Sources are credible and diverse
- Reports are well-structured and comprehensive
- Citations are accurate and accessible

---

## 🎯 **Next Steps**

Once Phase 1 is working:

1. **Document team workflows** - Create examples for common research tasks
2. **Gather user feedback** - Track what works well and pain points
3. **Plan Phase 2** - Begin ADHD-optimized plugin development
4. **Monitor usage** - Track API costs and performance metrics

**Estimated Setup Time**: 30-60 minutes
**Team Readiness**: Immediate research capability
**ROI**: High-quality research reports in minutes vs. hours