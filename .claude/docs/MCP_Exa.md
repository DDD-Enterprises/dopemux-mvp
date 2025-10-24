# Exa MCP - Neural Search Engine

**Provider**: Dopemux / Exa AI
**Purpose**: Fast, high-quality web search using neural ranking
**Type**: Simple research and quick information retrieval

## Overview

Exa provides neural search capabilities that go beyond traditional keyword matching. It understands semantic meaning and context to find highly relevant results quickly. Best for simple searches where you need fast, accurate web results.

## When to Use Exa vs GPT-Researcher

**Use Exa when**:
- Quick fact-checking or simple information lookup
- Finding specific documentation or API references
- Searching for recent news or updates
- Need fast results (< 5 seconds)
- Single-query research

**Use GPT-Researcher when**:
- Complex multi-faceted research questions
- Need comprehensive analysis across multiple sources
- Want synthesized reports with citations
- Deep-dive investigations requiring 4+ search engine coordination
- Multi-step research workflows

## Available Tools

### `exa/search` - Neural Web Search
**Purpose**: Find relevant web content using semantic understanding

**Parameters**:
- `query`: Search query (natural language)
- `num_results`: Number of results to return (default: 10)
- `use_autoprompt`: Let Exa optimize the query (default: true)
- `search_type`: "neural" (semantic) or "keyword" (traditional)
- `contents`: Include page content in results (default: false)

**Features**:
- Neural ranking for semantic relevance
- Auto-query optimization
- Domain filtering capabilities
- Recency control

**Example**:
```
exa/search:
  query: "React Server Components best practices 2025"
  num_results: 5
  search_type: "neural"
```

### `exa/find_similar` - Similarity Search
**Purpose**: Find content similar to a given URL

**Parameters**:
- `url`: Reference URL to find similar content
- `num_results`: Number of similar pages to return

**Use Case**: Find related articles, alternative documentation sources

**Example**:
```
exa/find_similar:
  url: "https://react.dev/blog/2023/03/22/react-labs-what-we-have-been-working-on-march-2023"
  num_results: 5
```

### `exa/get_contents` - Extract Page Content
**Purpose**: Retrieve clean, parsed content from URLs

**Parameters**:
- `ids`: List of Exa result IDs from previous search
- `text`: Extract plain text content
- `highlights`: Get key excerpts

**Use Case**: Extract full content from search results for analysis

## Best Practices

### Query Optimization
```
# Natural language works well:
"How to implement authentication in Next.js 14 with server actions"

# Exa's autoprompt will optimize it for better results
```

### Domain Filtering
```
# Limit to specific domains for authoritative sources:
query: "TypeScript utility types"
include_domains: ["typescriptlang.org", "github.com/microsoft/TypeScript"]
```

### Recency Control
```
# Find recent content:
query: "Claude AI features"
start_published_date: "2024-01-01"  # Only 2024+ content
```

## Integration with SuperClaude Commands

Exa replaces SuperClaude's Tavily for simple searches:

- `/sc:research` → Uses Exa for quick initial searches, GPT-Researcher for deep analysis
- `/sc:explain` → Uses Exa to find authoritative documentation
- `/sc:implement` → Uses Exa to find framework best practices
- `/sc:troubleshoot` → Uses Exa to search for error messages and solutions

## Performance

- **Response Time**: Typically 1-3 seconds
- **Result Quality**: Neural ranking provides highly relevant results
- **Coverage**: Billions of web pages indexed
- **Freshness**: Real-time indexing of new content

## Limitations

- Requires EXA_API_KEY environment variable
- API rate limits apply (depends on plan)
- Best for simple queries (complex research → use GPT-Researcher)
- Returns web results only (no synthesis or analysis)

## Example Workflows

### Quick Documentation Lookup
```
1. Search with Exa for "Next.js App Router data fetching"
2. Review top 3 results
3. Extract content from official Next.js docs
4. Use in implementation
```

### Error Message Research
```
1. Search with Exa for exact error message
2. Filter to Stack Overflow and GitHub Issues
3. Find solutions from community
4. Apply fix
```

### Framework Comparison
```
1. Search "Vue vs React 2025 comparison"
2. Get recent articles and benchmarks
3. Review multiple perspectives
4. Make informed decision
```

---

**Status**: ✅ Operational in Dopemux
**Replaces**: SuperClaude's Tavily MCP (for simple searches)
**Enhancement**: Neural semantic search vs keyword-only
**Partner Tool**: GPT-Researcher (for complex research)
