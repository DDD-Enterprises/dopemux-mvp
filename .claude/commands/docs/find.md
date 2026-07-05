# docs/find
Use **WebSearch** to find authoritative docs/snippets with runnable examples.

**Args**: `$ARGUMENTS` = `<QUERY>`

**Steps**
1) Use search_web for `<QUERY>` (aim for SDK docs, RFCs, or official guides).
2) Return top 5 with: title, source, short summary, and a minimal code sample if present.
3) Suggest integration points in this repo (files/functions) where the example applies.

**Tools**: WebSearch only.

> Token thrift:
- **WebSearch**: avoid broad/generic queries; include specific lib, function, or exact error text.
