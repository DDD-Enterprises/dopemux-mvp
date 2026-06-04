# GPT Researcher MCP Container Update Proof - 2026-06-04

## Status

VERIFIED_TARGETED for the local Docker container implementation. Commit SHA and PR URL are recorded in the publish response because they are generated after this proof content is finalized.

## Scope

- Task Packet: `TP-DMX-GPTR-MCP-CONTAINER-UPDATE-001`
- Task Packet path: `task-packets/generated/TP-DMX-GPTR-MCP-CONTAINER-UPDATE-001.json`
- Worktree: `/Users/hue/code/dopemux-mvp/.worktrees/gptr-mcp-container-update-20260604`
- Branch: `codex/gptr-mcp-container-update-20260604`
- Base branch: `origin/main`
- Base commit: `8571c33873d5c78eead660be9caa6178b5d8b1e3`

## Authority Used

- Latest user instruction: fix and update GPT Researcher in the Dopemux MVP Docker container implementation.
- `AGENTS.md`: worktree, Task Packet, proof, validation, and truthful finality requirements.
- Runtime/config truth: `compose.yml`, `docker/mcp-servers-source/gptr-mcp/Dockerfile`, running container `dopemux-mcp-gptr-mcp`.
- Package truth: PyPI reported `gpt-researcher==0.15.1` as the current release at implementation time.
- GPT Researcher skill guidance: package config and MCP/runtime context only.

## Analysis Performed

Observed before implementation:

- `compose.yml` service `gptr-mcp` builds from `docker/mcp-servers/gptr-mcp/Dockerfile`.
- `docker/mcp-servers` is a symlink to `docker/mcp-servers-source`; the tracked Dockerfile authority is `docker/mcp-servers-source/gptr-mcp/Dockerfile`.
- Running container `dopemux-mcp-gptr-mcp` was healthy, but only for its long-running `/app/gptr-mcp/server.py` command path.
- Running container had `gpt-researcher==0.14.8`.
- Running container did not have `/app/server.py`, while a stale MCP client command used `docker exec -i dopemux-mcp-gptr-mcp python /app/server.py`.

Challenge result:

- A wrapper that only runs `/app/gptr-mcp/server.py` would preserve the container service but would not satisfy stdio MCP clients using `docker exec -i`.
- The wrapper therefore defaults to stdio for bare `python /app/server.py` and the long-lived Docker `CMD` explicitly sets `DOPEMUX_GPTR_TRANSPORT=sse`.
- The first clean-cache Docker build exposed a separate Dockerfile drift: `uv pip install .[services]` now requires all `pyproject.toml` package trees, not just `src/dopemux/__init__.py`.

## Changes

- `docker/mcp-servers-source/gptr-mcp/Dockerfile`
  - Copies `src/` and `tools/` before installing `.[services]`, matching the current package layout.
  - Updates `ARG GPT_RESEARCHER_VERSION` from `0.14.8` to `0.15.1`.
  - Adds `/app/server.py` compatibility wrapper.
  - Runs the long-lived container service as SSE via `DOPEMUX_GPTR_TRANSPORT=sse exec python /app/server.py`.
- `tests/docker/test_gptr_mcp_dockerfile.py`
  - Adds a focused Dockerfile regression test for the package pin, package-tree copy, and legacy entrypoint wrapper.
- `task-packets/generated/TP-DMX-GPTR-MCP-CONTAINER-UPDATE-001.json`
  - Adds the scoped Task Packet.
- `task-packets/INDEX.md`
  - Registers the Task Packet.

## Validation Performed

### PASS

Task Packet JSON syntax:

```text
python -m json.tool task-packets/generated/TP-DMX-GPTR-MCP-CONTAINER-UPDATE-001.json >/dev/null
exit: 0
```

Task Packet schema:

```text
python -m jsonschema -i task-packets/generated/TP-DMX-GPTR-MCP-CONTAINER-UPDATE-001.json docs/03-reference/spec/dopetask/dopetask-canonical-spec.json
exit: 0
note: jsonschema CLI emitted a deprecation warning only.
```

TDD pre-fix static test failure:

```text
python -m pytest -q tests/docker/test_gptr_mcp_dockerfile.py
exit: 1
result: failed because the Dockerfile still pinned gpt-researcher 0.14.8 and did not provide /app/server.py.
```

Post-fix static test:

```text
python -m pytest -q tests/docker/test_gptr_mcp_dockerfile.py
exit: 0
output: ... [100%]
```

Compose syntax:

```text
docker compose -f compose.yml config --quiet
exit: 0
note: compose emitted unset environment variable warnings for ANTHROPIC_API_KEY, LITELLM_MASTER_KEY, LEANTIME_TOKEN, HOST_CODE_PARENT_DIR, and HOST_PROJECT_RELATIVE_PATH.
```

Clean-cache build failure found during implementation:

```text
docker compose -f compose.yml build gptr-mcp
exit: 1
error: package directory 'src/conport' does not exist
resolution: copy src/ and tools/ into the build context before uv pip install .[services].
```

Final Docker build:

```text
docker compose -f compose.yml build gptr-mcp
exit: 0
key output:
Built dopemux @ file:///app
+ gpt-researcher==0.15.1
Image dopemux-gptr-mcp Built
```

Container restart:

```text
docker compose -f compose.yml up -d gptr-mcp
exit: 0
key output:
Container dopemux-mcp-gptr-mcp Recreated
Container dopemux-mcp-gptr-mcp Started
```

Container package and wrapper verification:

```text
docker exec dopemux-mcp-gptr-mcp test -f /app/server.py && echo SERVER_WRAPPER_PRESENT
docker exec dopemux-mcp-gptr-mcp python -m py_compile /app/server.py /app/gptr-mcp/server.py && echo SERVER_COMPILES
docker exec -i dopemux-mcp-gptr-mcp python - <<'PY'
import importlib.metadata as m
for name in ("gpt-researcher", "mcp", "fastmcp", "dopemux"):
    print(f"{name}=={m.version(name)}")
PY
exit: 0
output:
SERVER_WRAPPER_PRESENT
SERVER_COMPILES
gpt-researcher==0.15.1
mcp==1.27.2
fastmcp==3.4.0
dopemux==0.1.0
```

Container status and health:

```text
docker inspect --format 'status={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} image={{.Config.Image}} cmd={{json .Config.Cmd}}' dopemux-mcp-gptr-mcp
exit: 0
output:
status=running health=healthy image=dopemux-gptr-mcp cmd=["sh","-c","DOPEMUX_GPTR_TRANSPORT=sse exec python /app/server.py"]
```

HTTP health:

```text
curl -fsS http://localhost:3009/health
exit: 0
output:
{"status":"healthy","service":"mcp-server"}
```

Container log trace:

```text
docker logs --tail 80 dopemux-mcp-gptr-mcp
exit: 0
key output:
Starting GPT Researcher MCP Server with sse transport...
Starting MCP server 'GPT Researcher' with transport 'sse' on http://0.0.0.0:3009/sse
```

Legacy stdio MCP path:

```text
docker exec -i dopemux-mcp-gptr-mcp python /app/server.py
exit: 0
input: one JSON-RPC initialize request
output:
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","capabilities":{"experimental":{},"logging":{},"prompts":{"listChanged":false},"resources":{"subscribe":false,"listChanged":false},"tools":{"listChanged":true},"extensions":{"io.modelcontextprotocol/ui":{}}},"serverInfo":{"name":"GPT Researcher","version":"3.4.0"}}}
```

Image identity and health:

```text
docker image inspect --format 'id={{.Id}} created={{.Created}}' dopemux-gptr-mcp:latest
curl -fsS http://localhost:3009/health
exit: 0
output:
id=sha256:1a4899e879d8b8bd03220c859551fbfb2d988e04543f1e1c5a8db9d48c6cac8a created=2026-06-04T19:30:12.47933667Z
{"status":"healthy","service":"mcp-server"}
```

### FAIL

- The first Docker rebuild failed because the Dockerfile copied too little of the current repository package layout. This was fixed by copying `src/` and `tools/` before `uv pip install .[services]`.

### NOT_RUN

- End-to-end real research request through the GPT Researcher tool: not run because it would require provider/network execution beyond the container repair proof.

## Security Note

During local process inspection outside this repository, API key material was visible in another process command line. This proof does not repeat those values. Recommended remediation is to rotate exposed keys and move secrets out of command arguments or other process-list-visible surfaces.

## Precommit Status

PASS:

```text
pre-commit run --files docker/mcp-servers-source/gptr-mcp/Dockerfile tests/docker/test_gptr_mcp_dockerfile.py task-packets/INDEX.md task-packets/generated/TP-DMX-GPTR-MCP-CONTAINER-UPDATE-001.json claudedocs/gptr-mcp-container-update-proof-2026-06-04.md
exit: 0
result: all configured hooks passed or skipped for no matching files.
```

## Codereview Status

Self-review completed before this proof file:

- Allowlist scope is limited to the GPT Researcher MCP Dockerfile, packet/index, narrow test, and proof.
- The upstream `gptr-mcp` repository ref remains pinned.
- The wrapper does not silently change the container service transport; Docker `CMD` sets SSE explicitly.
- Bare `/app/server.py` defaults to stdio for MCP client compatibility.

## Remaining Uncertainty / Risk

- Provider-backed research behavior was not exercised.
- The `gpt-researcher` update from `0.14.8` to `0.15.1` was validated for import/package installation and MCP server startup, not full research workflow semantics.
- Existing MCP client configs outside this repo may still carry stale assumptions other than `/app/server.py`.

## Rollback Plan

Revert this branch or restore these paths from `origin/main`:

- `docker/mcp-servers-source/gptr-mcp/Dockerfile`
- `tests/docker/test_gptr_mcp_dockerfile.py`
- `task-packets/INDEX.md`
- `task-packets/generated/TP-DMX-GPTR-MCP-CONTAINER-UPDATE-001.json`
- `claudedocs/gptr-mcp-container-update-proof-2026-06-04.md`

Then rebuild and restart `gptr-mcp` from the restored Dockerfile if local container state must be reverted.
