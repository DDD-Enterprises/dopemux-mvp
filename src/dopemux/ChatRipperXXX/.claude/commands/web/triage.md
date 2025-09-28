# web/triage
Use **exa** (exa-mcp-server) and **duckduckgo** (duckduckgo-mcp-server) to triage a topic.

**Args**: `$ARGUMENTS` = `<QUERY>`

**Steps**
1) Use Exa to get high-signal results (max 5). Then use DuckDuckGo to diversify (max 5).
2) Deduplicate by domain/title. For the best 3, use DDG fetch_content (or Exa + content tool) to pull text.
3) Return a merged brief: 3–5 bullets with links, plus a “What to do next” recommendation.

**Tools**: exa + duckduckgo only.

> Token thrift:
- **Exa**: avoid broad/generic queries; include specific lib, function, or exact error text.
