# Independent AGY/Claude Final Audit Report

- Packet: `TP-DMX-MCP-DOPE-CONTEXT-QDRANT-COMPAT-001`
- Audit ID: `TP-DMX-MCP-DOPE-CONTEXT-QDRANT-COMPAT-001-FINAL-L3-R1`
- Content head: `8d88cc3e7f0fea65c5d5b878c3813a5a81eff356`
- Content tree: `8e06364d311371224aa4b3c74fc007bff446e86c`
- Runner: AGY `1.1.22`
- Requested/configured model: `claude-sonnet-4-6`
- Response-claimed model: `claude-sonnet-4-6-thinking`
- Proxy-reported model: `UNKNOWN`
- Provider-attested model: `UNKNOWN`
- Conversation: `beed2e44-c805-4145-a36a-12ac75baea8c`
- Exit code: `0`
- Verdict: **PASS_WITH_RISKS**

## Repository access

Auditor proved mounted worktree readability, repository remote identity, exact content head/tree, base ancestry, exact two-file commit, and canonical packet bytes/hash before substantive review.

## Summary

Auditor passed substantive review: production change removes only unused `SearchRequest`; regression test uses real SDK in subprocess and preserves parent `sys.modules` binding; protected dependency/build files remain unchanged; deterministic test, image, runtime, MCP, workspace, non-provider, foreign-container, late-materialization, and secret receipts are coherent.

## Open finding

### F-001 — HIGH — OPEN

Auditor computed raw Git patch SHA-256 `665dacc300b00b4c88b78f1efcc962ac2295f05f40493392d72b2bea7ae1e64c`, differing from packet value `5dee0a6410608cdf310c1370941a778c8ccd3d5755ef1a438aef09b705ea7ad9`.

Deterministic post-audit investigation explained source: `rtk proxy git diff --binary BASE HEAD` yields raw hash `665dacc3…`; mandatory `rtk git diff --binary BASE HEAD` yields normalized hash `5dee0a64…`. Packet binds latter but does not name RTK-normalized hash domain. Both retained. No second model audit performed.

## Passed audit checks

- Exact one-line production removal; symbol unused.
- Real Qdrant SDK subprocess import; parent module binding unchanged.
- Exactly two substantive paths; protected files unchanged.
- Existing-container pre-fix `SearchRequest` ImportError receipt coherent.
- Locked 1.17.1 and ephemeral 1.19.0 focused suites passed.
- Full dope-context suite passed with disclosed skips/xfail.
- Image build and disposable import probe passed.
- Final container healthy with restart count 0 and original data/log/workspace binds.
- MCP initialize, initialized notification, tools/list, and provider-free workspace status passed.
- No application-provider call invoked; PyPI FastMCP metadata check classified separately.
- Foreign Task Orchestrator, ConPort, dope-memory, Serena, Qdrant, and dNh CRM container IDs unchanged.
- Packet late materialization disclosed.
- Secret scan and canonical packet hash passed.

## Remaining risks

- Diff hash domain ambiguity remains HIGH and OPEN.
- A1/A2/A3 separate source text remains `UNKNOWN`.
- Proxy/provider model identity remains `UNKNOWN`.
- Credential value equality remains `UNKNOWN`; values intentionally not inspected.
- Current workspace active Qdrant collections are absent; no mutation was authorized.

Raw structured output: `review_bundle/AGY_RAW_OUTPUT.json`.
