# web/spec-to-commit
Fetch a spec (web) then propose a precise commit plan (git).

**Args**: `$ARGUMENTS` = `<SPEC QUERY>`

**Steps**
1) Use Exa to find the **latest official spec or repo**; pull a short excerpt via DDG content.
2) Produce a minimal patch plan (files/functions) aligned to the spec, with test stubs.
3) Show a draft conventional commit message and granular messages per file.
4) Offer to open diffs and stage changes (upon confirmation).

**Tools**: exa + duckduckgo + git_local. No actual commits without confirmation.

> Token thrift:
- **Exa**: avoid broad/generic queries; include specific lib, function, or exact error text.
