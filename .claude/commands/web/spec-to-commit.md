# web/spec-to-commit
Fetch a spec (web) then propose a precise commit plan (git).

**Args**: `$ARGUMENTS` = `<SPEC QUERY>`

**Steps**
1) Use search_web to find the **latest official spec or repo**; pull a short excerpt via fetch_content or read page tools.
2) Produce a minimal patch plan (files/functions) aligned to the spec, with test stubs.
3) Show a draft conventional commit message and granular messages per file.
4) Offer to open diffs and stage changes (upon confirmation).

**Tools**: WebSearch + git_local. No actual commits without confirmation.

> Token thrift:
- **WebSearch**: avoid broad/generic queries; include specific lib, function, or exact error text.
