# DMX-CONPORT-OPTIMAL-105 MCP Surface Search Proof

## Scope

- Packet: `task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-105-mcp-surface-search.json`
- Worktree: `/Users/hue/.codex/worktrees/conport-optimal-105-mcp-surface-search`
- Branch: `codex/conport-optimal-105-mcp-surface-search`
- Base HEAD observed before implementation: `db3eb365ea0116aa36cf80efbf4cbbbd61eb4b57`

## Change Summary

- Added `search_content(workspace_id, query)` FastMCP tools in:
  - `docker/mcp-servers-source/conport/server.py`
  - `docker/mcp-servers-source/conport/conport_mcp_stdio.py`
- Added `conport_search_content` JSON-RPC schema and dispatch in:
  - `docker/mcp-servers-source/conport/enhanced_server.py`
- Added focused MCP search tests in:
  - `docker/mcp-servers-source/conport/tests/test_mcp_search.py`

## Post-Review Restack + Encoding Fix (2026-06-22)

During PR review the branch was rebased onto packet 104
(`codex/conport-optimal-104-mcp-surface-custom-data`, tip `c6434014e`) so the two
ConPort-surface PRs stack and merge conflict-free. The conflicts were purely
additive (shared import line, dispatch dict, tool-method block, schema tail) and
were resolved as unions of both tool families.

A correctness defect was found and fixed during the restack:

- **Bug**: `search_content` injected `workspace_id` raw into the
  `/api/search/{workspace_id}` path. aiohttp routes `{workspace_id}` as a single
  path segment, so a real path-shaped workspace id (e.g.
  `/Users/hue/code/dopemux-mvp`) produced `/api/search//Users/...` and 404'd. The
  original proof masked this by seeding under the slash-free slug
  `packet-105-live`.
- **Fix**: percent-encode the workspace id with `quote(workspace_id, safe='')` at
  all three call sites (`enhanced_server._search_content_tool`,
  `conport_mcp_stdio.search_content`, `server.search_content`).
- **Regression coverage**: added
  `test_jsonrpc_search_content_url_encodes_path_workspace_id` and
  `test_fastmcp_search_content_url_encodes_path_workspace_id`, which assert the
  built URL contains `%2FUsers%2F...` and never `/api/search//Users`.

## Analysis Performed

- Read `AGENTS.md`.
- Read packet 105 JSON and verified allowlist/validation obligations.
- Inspected existing ConPort REST search handler and JSON-RPC dispatch pattern.
- Verified existing search path had no uncommented `ag_catalog` references in the inspected source paths.
- Confirmed implementation proxies to the existing `GET /api/search/{workspace_id}?q=...` endpoint instead of adding a second search implementation.

## TDD Evidence

RED:

```text
python3 -m pytest docker/mcp-servers-source/conport/tests/test_mcp_search.py -q
```

Result: FAIL, 3 expected failures before implementation for missing `conport_search_content` schema/dispatch and missing FastMCP `search_content` tool.

GREEN:

```text
python3 -m pytest docker/mcp-servers-source/conport/tests/test_mcp_search.py -q
```

Result: PASS.

## Validation

PASS:

```text
python3 -m pytest docker/mcp-servers-source/conport/tests/test_mcp_search.py -q
```

PASS:

```text
python3 -m py_compile \
  docker/mcp-servers-source/conport/server.py \
  docker/mcp-servers-source/conport/conport_mcp_stdio.py \
  docker/mcp-servers-source/conport/enhanced_server.py
```

PASS:

```text
python3 -m json.tool task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-105-mcp-surface-search.json >/dev/null
python3 -m jsonschema \
  -i task-packets/generated/DMX-CONPORT-OPTIMAL/DMX-CONPORT-OPTIMAL-105-mcp-surface-search.json \
  docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
```

PASS:

```text
git diff --check
```

PASS:

```text
pre-commit run --files \
  docker/mcp-servers-source/conport/server.py \
  docker/mcp-servers-source/conport/conport_mcp_stdio.py \
  docker/mcp-servers-source/conport/enhanced_server.py \
  docker/mcp-servers-source/conport/tests/test_mcp_search.py \
  proof/conport-optimal-105-mcp-surface-search/DMX-CONPORT-OPTIMAL-105-mcp-surface-search/PROOF.md
```

PASS with existing allowlisted match only:

```text
rg -n "(sk-proj-[A-Za-z0-9_-]+|sk-svcacct-[A-Za-z0-9_-]+|ghp_[A-Za-z0-9_]+|postgres(ql)?://[^[:space:]]+:[^[:space:]@]+@)" \
  docker/mcp-servers-source/conport/server.py \
  docker/mcp-servers-source/conport/conport_mcp_stdio.py \
  docker/mcp-servers-source/conport/enhanced_server.py \
  docker/mcp-servers-source/conport/tests/test_mcp_search.py \
  proof/conport-optimal-105-mcp-surface-search/DMX-CONPORT-OPTIMAL-105-mcp-surface-search/PROOF.md
```

Observed only the pre-existing `# pragma: allowlist secret` local development Postgres URL in `enhanced_server.py`.

PASS:

```text
docker compose --env-file /Users/hue/code/dopemux-mvp/.env -f compose.yml build conport
docker compose --env-file /Users/hue/code/dopemux-mvp/.env -f compose.yml up -d --no-deps conport
curl http://localhost:3004/health
```

Observed: `health_http=200`.

PASS:

```text
curl -sS -X POST http://localhost:3004/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Observed: `conport_search_content` advertised.

PASS:

Seeded live decision in workspace `packet-105-live` with keyword `packet105needle1782158062`, then called:

```text
curl -sS -X POST http://localhost:3004/mcp \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"conport_search_content","arguments":{"workspace_id":"packet-105-live","query":"packet105needle1782158062"}}}'
```

Observed: JSON-RPC search result contained the seeded keyword.

### Integrated coexistence + path-workspace e2e (post-restack, 2026-06-22)

Run against the rebased branch (104 + 105 stacked) without disturbing the live
`mcp-conport` container.

PASS — full conport unit suite on the combined branch:

```text
python3 -m pytest docker/mcp-servers-source/conport/tests/ -q
```

Observed: 42 passed (104 `test_mcp_custom_data` + 105 `test_mcp_search` coexisting).

PASS — built the combined image and ran an ephemeral container on alt port
`3014:3004` against the real DB/network:

```text
docker build -f docker/mcp-servers/conport/Dockerfile -t dopemux-conport:stack105 .
docker run -d --name conport-stack105-test --network dopemux-network -p 3014:3004 <db/redis/qdrant env> dopemux-conport:stack105
```

- `tools/list` advertised all 13 tools including `conport_search_content` and the
  three `conport_*_custom_data` tools.
- `conport_search_content` with a **path-shaped** workspace
  (`/tmp/conport-stack105-e2e`) returned a seeded decision — the exact case that
  404'd before the encoding fix.
- `conport_save/get/delete_custom_data` round-trip succeeded under the same path
  workspace.
- Negative control: `GET /api/search/<raw-path>` → 404; `GET /api/search/<%2F-encoded>` → 200.

Cleanup: seeded throwaway decision deleted from the DB (`DELETE 1`, verified 0
remaining), ephemeral container and `dopemux-conport:stack105` image removed, live
`mcp-conport` confirmed still healthy (`health=200`).

## Residual Risk

- Coexistence with packet 104 is now proven: the combined image advertises and
  serves both tool families over JSON-RPC, validated end-to-end under a path-shaped
  workspace.
- The original `packet-105-live` seeded decision (slug workspace) from the
  pre-restack validation remains in the DB; harmless, isolated under a non-path
  workspace id.
- The raw-path-segment pattern is shared by pre-existing tools
  (`get_active_work`/`get_recent_activity`/`get_context`) which avoid the bug only
  because `enhanced_server` dispatches them in-process. They remain latently
  affected for any future HTTP self-call refactor — flagged as a separate
  follow-up, intentionally out of scope here.
- Full repository suite was not run; validation stayed conport-surface-scoped per
  blast radius.

## Commit / PR

- Original implementation commit: `33691c7be53903caafd7eb0b3261bfc19d0349e8`
- Post-restack: rebased onto `codex/conport-optimal-104-mcp-surface-custom-data`
  (`c6434014e`); implementation commit replayed as `c76dfbf3e` with the
  workspace_id encoding fix folded into the conflict resolution.
- PR: `https://github.com/DDD-Enterprises/dopemux-mvp/pull/959` — base retargeted to
  the packet 104 branch so it stacks and merges conflict-free; auto-retargets to
  `main` once 104 merges.
- Note: this proof was updated post-restack; see "Post-Review Restack + Encoding
  Fix" and "Integrated coexistence + path-workspace e2e".
