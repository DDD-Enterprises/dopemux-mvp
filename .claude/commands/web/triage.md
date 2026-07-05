# web/triage
Use **WebSearch** to triage a topic.

**Args**: `$ARGUMENTS` = `<QUERY>`

**Steps**
1) Use search_web to get high-signal results (max 5).
2) Deduplicate by domain/title. For the best 3, use fetch_content or read page tools to pull text.
3) Return a merged brief: 3–5 bullets with links, plus a “What to do next” recommendation.

**Tools**: WebSearch only.

> Token thrift:
- **WebSearch**: avoid broad/generic queries; include specific lib, function, or exact error text.
