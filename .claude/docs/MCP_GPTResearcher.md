# GPT-Researcher MCP - Comprehensive Research Engine

**Provider**: Dopemux / GPT-Researcher
**Purpose**: Deep, multi-source research with synthesis and report generation
**Type**: Complex research requiring comprehensive analysis

## Overview

GPT-Researcher coordinates multiple search engines (Google, Bing, DuckDuckGo, Exa) to perform thorough research on complex topics. It gathers information from diverse sources, synthesizes findings, and generates comprehensive reports with citations. Use for investigations that require depth and breadth.

## When to Use GPT-Researcher vs Exa

**Use GPT-Researcher when**:
- Complex research questions requiring multiple sources
- Need comprehensive analysis and synthesis
- Want structured reports with citations
- Multi-step research workflows
- Deep-dive investigations (5+ minutes acceptable)

**Use Exa when**:
- Quick fact-checking or simple lookups
- Finding specific documentation
- Need fast results (< 5 seconds)
- Single-query research

## Available Tools

### `gpt-researcher/deep_research` - Comprehensive Investigation
**Purpose**: Perform thorough multi-source research with synthesis

**Parameters**:
- `query`: Research question or topic

**Features**:
- Coordinates 4 search engines (Google, Bing, DuckDuckGo, Exa)
- Scrapes and analyzes multiple web sources
- Synthesizes findings into coherent narrative
- Provides citations and source links
- Generates research ID for follow-up

**Returns**:
- `research_id`: Unique ID for accessing results
- `status`: Research completion status
- `context`: Synthesized research findings
- `sources`: List of consulted sources with URLs

**Example**:
```
gpt-researcher/deep_research:
  query: "What are the trade-offs between microservices and monolithic architecture for a SaaS product with 10-person team?"

Returns:
  research_id: "abc-123-def"
  context: "Comprehensive analysis of architecture patterns..."
  sources: [{title, url, relevance}, ...]
```

### `gpt-researcher/quick_search` - Fast Multi-Source Search
**Purpose**: Quick search across multiple engines without deep analysis

**Parameters**:
- `query`: Search query

**Features**:
- Parallel search across multiple engines
- Returns raw results without synthesis
- Faster than deep_research (< 30 seconds)
- Good for exploratory research

**Use Case**: Initial exploration before deep research

### `gpt-researcher/write_report` - Generate Research Report
**Purpose**: Create formatted report from completed research

**Parameters**:
- `research_id`: ID from deep_research
- `custom_prompt`: Optional formatting instructions

**Features**:
- Multiple formats (markdown, PDF, HTML)
- Structured sections (Summary, Findings, Analysis, Recommendations)
- Proper citations
- Customizable templates

**Example**:
```
gpt-researcher/write_report:
  research_id: "abc-123-def"
  custom_prompt: "Focus on cost implications and team size considerations"
```

### `gpt-researcher/get_research_sources` - Retrieve Source List
**Purpose**: Get detailed source information from research

**Parameters**:
- `research_id`: ID from deep_research

**Returns**: Array of sources with titles, URLs, relevance scores, excerpts

### `gpt-researcher/get_research_context` - Retrieve Synthesis
**Purpose**: Get the synthesized research context

**Parameters**:
- `research_id`: ID from deep_research

**Returns**: Full synthesized research findings

## Research Workflow

### Complete Research Process
```
1. deep_research(query)
   → Returns research_id + initial findings

2. Review sources and context

3. Optional: write_report(research_id)
   → Generates formatted report

4. Use findings in decision-making
```

### Iterative Research
```
1. quick_search(broad query)
   → Get overview quickly

2. Refine based on results

3. deep_research(refined query)
   → Comprehensive analysis

4. get_research_sources(research_id)
   → Examine specific sources
```

## Best Practices

### Query Formulation
```
# Good queries are specific and focused:
✅ "What are the security best practices for JWT authentication in Node.js applications?"

# Avoid overly broad queries:
❌ "Tell me about web security"
```

### Multi-Step Research
```
# Break complex topics into phases:
1. Quick search for overview
2. Deep research on key subtopics
3. Synthesize findings
4. Generate report
```

### Source Validation
```
# Always review sources for:
- Authority (official docs, reputable sites)
- Recency (check publication dates)
- Relevance (matches your specific question)
- Consistency (cross-reference findings)
```

## Integration with SuperClaude Commands

GPT-Researcher enables deep research in SuperClaude workflows:

- `/sc:research` → Primary tool for complex research questions
- `/sc:brainstorm` → Research market trends and competitive analysis
- `/sc:workflow` → Research best practices for implementation approach
- `/sc:design` → Research design patterns and architectural approaches

## Performance

- **Deep Research**: 2-10 minutes depending on query complexity
- **Quick Search**: 10-30 seconds
- **Report Generation**: 30-60 seconds
- **Source Count**: Typically 10-20 sources per research
- **Quality**: High - synthesizes multiple perspectives

## ADHD Optimizations

### Progress Indicators
- Shows research stages: "Searching...", "Analyzing...", "Synthesizing..."
- Provides partial results during long research
- Can interrupt and resume with research_id

### Cognitive Load Management
- Structured output reduces information overwhelm
- Citations allow selective deep-dives
- Summary-first approach (TL;DR at top)
- Customizable report formats

### Break-Friendly
- Research runs asynchronously
- Save research_id for later review
- Results persist for session duration
- Can generate multiple report formats from same research

## Example Use Cases

### Technology Evaluation
```
deep_research:
  query: "Comparison of PostgreSQL vs MongoDB for e-commerce application with complex queries and ACID requirements"

Output: Detailed analysis with performance benchmarks, use cases, migration considerations
```

### Best Practices Research
```
deep_research:
  query: "React Server Components best practices for data fetching and caching in Next.js 14"

Output: Official recommendations, community patterns, performance tips, gotchas
```

### Competitive Analysis
```
deep_research:
  query: "How do competitors like Linear and Asana handle real-time collaboration features?"

Output: Feature analysis, technical approach insights, UX patterns
```

### Problem Investigation
```
deep_research:
  query: "Common causes and solutions for Node.js memory leaks in production environments"

Output: Root causes, debugging techniques, preventive measures, case studies
```

## Limitations

- Requires internet connectivity
- API rate limits apply (based on search engine quotas)
- Longer response time than simple search (trade-off for quality)
- May miss very recent information (< 24 hours old)
- Quality depends on availability of online sources

## Output Format

```json
{
  "research_id": "unique-id",
  "status": "complete",
  "context": "Synthesized research findings with analysis...",
  "sources": [
    {
      "title": "Source Title",
      "url": "https://example.com",
      "relevance": 0.95,
      "excerpt": "Key excerpt..."
    }
  ],
  "metadata": {
    "query": "Original research query",
    "engines_used": ["google", "bing", "duckduckgo", "exa"],
    "sources_consulted": 15,
    "duration": "3.5 minutes"
  }
}
```

---

**Status**: ✅ Operational in Dopemux
**Replaces**: SuperClaude's Tavily MCP (for complex research)
**Enhancement**: Multi-engine coordination, synthesis, report generation
**Partner Tool**: Exa (for simple/fast searches)
**Best For**: Complex research requiring 10+ minutes and multiple sources
