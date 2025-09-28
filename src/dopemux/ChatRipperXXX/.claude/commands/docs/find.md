# docs/find
Use **Exa** to find authoritative docs/snippets with runnable examples.

**Args**: `$ARGUMENTS` = `<QUERY>`

**Steps**
1) Exa.search for `<QUERY>` (aim for SDK docs, RFCs, or official guides).
2) Return top 5 with: title, source, short summary, and a minimal code sample if present.
3) Suggest integration points in this repo (files/functions) where the example applies.

**Tools**: Exa only.

> Token thrift:
- **Exa**: avoid broad/generic queries; include specific lib, function, or exact error text.
