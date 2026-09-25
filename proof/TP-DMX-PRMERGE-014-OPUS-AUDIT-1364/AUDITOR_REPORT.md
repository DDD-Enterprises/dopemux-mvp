# Auditor Report — PR #1364 / PAL AnyIO 4.11.0 → 4.14.2

**Verdict:** **PASS_WITH_RISKS**  
**Scope:** audit evidence only; never readiness/merge authority  
**Base:** `35df148a55864b0efc5ada79753f987207b2936c`  
**Head:** `902e22aa08b0a6c9129b67bb75b66eca54449eaf`

## Scope and evidence

Only `docker/mcp-servers-source/pal/pal-mcp-server/uv.lock` changes. PAL requires Python `>=3.10` and directly depends on `mcp>=1.28.1,<2`; no direct PAL AnyIO import or `pytest.mark.anyio` use was found.

The diff changes AnyIO 4.11.0 → 4.14.2, removes AnyIO's direct `sniffio` edge, normalizes the `exceptiongroup -> typing-extensions` marker, and makes Uvicorn's `click`/`h11` edges unconditional without changing those package versions. The top-level resolution-marker change is ordering only.

`uv lock --check --offline` passed. A frozen external PAL venv synced 46 packages successfully and imported AnyIO 4.14.2, MCP 1.29.0, Starlette 1.3.1, Uvicorn 0.37.0, HTTPX 0.28.1, and Sniffio 1.3.1. An AnyIO memory-stream smoke also passed. No PAL/Docker service or container was started.

## Findings

- **LOW / open:** Python 3.10 path for the exceptiongroup marker reshaping was not exercised.
- **LOW / open:** Windows, emscripten, and the Linux PAL container image were not synced.
- **INFO / accepted risk:** transitive AnyIO cancellation/task-group/transport behavior was not exercised.

The successful universal lock check materially supports marker consistency, but the single macOS/Python 3.12 sync is not proof for all PAL-supported Python/platform combinations.

## Route receipt

Claude Code 2.1.282, selector `opus`, high effort, restricted mode, strict empty MCP config, zero tools, one turn. Native metadata reports only `claude-opus-5-5`, provider `firstParty`, no web requests, no subagents, exit 0, cost $0.1478038. Claude Code 2.1.282 states thinking tokens are included inside `outputTokens`; derived visible final output is 4,334 tokens, within the 5,000-token bound.

No repository/GitHub/workflow/service/container/signing/commit/mark-ready/close/merge effect occurred.
