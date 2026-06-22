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

## Residual Risk

- The live `mcp-conport` container was rebuilt from packet 105's `origin/main`-based worktree. It validates packet 105, but it does not prove coexistence with unmerged packet 104 custom-data MCP additions.
- The seeded live validation intentionally wrote one decision record to workspace `packet-105-live` to prove live search behavior.
- Full suite validation was not run; validation stayed packet-scoped per allowlist and blast radius.

## Commit / PR

- Implementation commit: `33691c7be53903caafd7eb0b3261bfc19d0349e8`
- PR: `https://github.com/DDD-Enterprises/dopemux-mvp/pull/959`
- Note: this proof file was updated after PR creation in a proof-only follow-up commit, so the branch tip may be newer than the implementation commit above.
