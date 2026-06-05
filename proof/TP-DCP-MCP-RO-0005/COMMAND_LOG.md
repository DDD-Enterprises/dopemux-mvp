# COMMAND_LOG — TP-DCP-MCP-RO-0005 (ConPort + dope-memory read adapters)

Worktree .worktrees/chatgpt-mcp-ro-0005; branch off origin/main (876d0c624, which has 0004).

## $ git rev-parse --show-toplevel && git branch --show-current && git rev-parse HEAD
/Users/hue/code/dopemux-mvp/.worktrees/chatgpt-mcp-ro-0005
dcp/chatgpt-mcp-ro-0005-conport-and-dope-memory-read-ada
876d0c624bee8f4f838a990a119ab1f1e9521bf5

## $ python -m pytest -q services/dcp-readonly-facade/tests
.................................s...................................... [ 87%]
..........                                                               [100%]
=========================== short test summary info ============================
SKIPPED [1] services/dcp-readonly-facade/tests/test_live_optional.py:26: set DCP_FACADE_LIVE_TESTS=1 to run live tests

## $ python -m compileall -q services/dcp-readonly-facade
exit=0

## Denylist grep (packet verify) over the ADAPTER CALL PATHS — expect (clean)
(clean — denied tokens only in route_manifest.py + tests)

## httpx import is lazy (only inside the transport function)
services/dcp-readonly-facade/src/dcp_facade/http_client.py:87:    import httpx  # lazy import — only needed for real calls

## No writes/shell in 0005 code (only 0004 gitstate subprocess)
(none in 0005 adapters)

## Diff name-only vs origin/main (allowlist)
docs/03-reference/dcp/chatgpt-mcp-readonly/FACADE_LOCAL_RUN.md
services/dcp-readonly-facade/conftest.py
services/dcp-readonly-facade/src/dcp_facade/conport.py
services/dcp-readonly-facade/src/dcp_facade/dope_memory.py
services/dcp-readonly-facade/src/dcp_facade/envelope.py
services/dcp-readonly-facade/src/dcp_facade/http_client.py
services/dcp-readonly-facade/src/dcp_facade/route_manifest.py
services/dcp-readonly-facade/src/dcp_facade/tools.py
services/dcp-readonly-facade/src/mcp/server.py
services/dcp-readonly-facade/tests/test_adapter_tools.py
services/dcp-readonly-facade/tests/test_adapters.py
services/dcp-readonly-facade/tests/test_http_client.py
services/dcp-readonly-facade/tests/test_live_optional.py
services/dcp-readonly-facade/tests/test_route_denylist.py
## Outside allowlist? (expect none)
(none — within allowlist)
## Forbidden files? (expect none)
(none)
