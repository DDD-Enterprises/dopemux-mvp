---
id: truth-canonicals
title: Truth Canonicals
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-31'
last_review: '2026-03-31'
next_review: '2026-06-29'
prelude: Truth Canonicals (explanation) for dopemux documentation and developer workflows.
---
# TRUTH_CANONICALS

Static inspection only. Recommendations below are based on checked-in runtime code, config, tests, and docs, not on live execution.

## Commands Used

- `rg --files ...`
- `rg -n ...`
- `sed -n ...`

## 1. working-memory-assistant vs dope-memory

### Candidates

- `services/working-memory-assistant/dope_memory_main.py`
- `services/working-memory-assistant/main.py`
- `services/working-memory-assistant/mcp/server.py`

### Evidence

- Fact: `dope_memory_main.py` says it is `the canonical entry point for the Dope-Memory service`.
- Fact: `canonical_ledger.py` says all Dope-Memory writes must target one canonical ledger path.
- Fact: `chronicle/store.py` says it is the canonical SQLite storage for Dope-Memory.
- Fact: `main.py` exposes a different API family centered on snapshot/recover/context/preferences/adhd endpoints.
- Fact: `mcp/server.py` duplicates tool logic that also exists inline in `dope_memory_main.py`.

### Recommendation

- Recommend `dope-memory` as the canonical runtime/service identity.
- Recommend `services/working-memory-assistant/dope_memory_main.py` as canonical runtime entrypoint.
- Recommend `services/working-memory-assistant/main.py` be treated as legacy or alternate until runtime authority is explicitly re-declared.
- Recommend `services/working-memory-assistant/mcp/server.py` be treated as duplicate implementation surface, not naming authority.

### Confidence

- HIGH

### Unresolved questions

- Unknown whether `main.py` still has active operators or deployment wiring outside this repo.
- Unknown whether the duplicated `mcp/server.py` is imported by external tooling not visible in static inspection.

## 2. conport vs dope-query

### Candidates

- `conport` surfaces:
  - `src/dopemux/mcp/registry.yaml`
  - `src/dopemux/conport/wire_project.py`
  - `scripts/mcp-wrappers/conport-wrapper.sh`
  - `docker/mcp-servers-source/conport/*`
  - `services/dopecon-bridge/dopecon_bridge/clients.py`
- `dope-query` surface:
  - `services/dope-query/*`

### Evidence

- Fact: dopemux MCP registry contains a live `conport` server definition.
- Fact: dopemux project wiring writes Claude MCP config for `conport`.
- Fact: dopecon-bridge proxies KG routes to active ConPort REST.
- Fact: Serena bridge integration uses DopeconBridge rather than any dope-query runtime.
- Fact: static inspection of `services/dope-query` found `auth/models.py` and tests, but no active runtime entrypoint, app, or CLI.

### Recommendation

- Recommend `conport` as the canonical runtime authority for this split.
- Recommend `dope-query` be treated as non-authoritative in current repo truth unless a checked-in runtime entrypoint is restored or separately documented.

### Confidence

- HIGH

### Unresolved questions

- Unknown whether `dope-query` exists as an external/private package or service not vendored here.
- Unknown which checked-in ConPort server file is the intended canonical MCP surface: unprefixed versus prefixed tool names remain split.

## 3. adhd_engine vs adhd-engine

### Candidates

- Runtime/service path: `services/adhd_engine`
- Doc/index naming: `adhd-engine` keying in `docs/docs_index.yaml`

### Evidence

- Fact: runtime code lives under `services/adhd_engine`.
- Fact: CLI path is `services/adhd_engine/cli/adhd.py`.
- Fact: API schemas and routes live under `services/adhd_engine/api`.
- Fact: docs index uses `adhd-engine` as a documentation key pointing back to `services/adhd_engine/README.md`.

### Recommendation

- Recommend `adhd_engine` as canonical filesystem/runtime identifier.
- Recommend `adhd-engine` remain only a display/docs label where needed.
- Recommend docs and config avoid presenting `adhd-engine` as if it were the import path or runtime package name.

### Confidence

- HIGH

### Unresolved questions

- Unknown whether any deployment manifests outside this inspection use `adhd-engine` as a container or service name.

## 4. Hyphen / underscore duplicates impacting runtime or docs

### Candidates

- `adhd_engine` vs `adhd-engine`
- `working-memory-assistant` directory name vs `dope-memory` runtime identity
- `dopemux-claude-context` vs `dope-context`

### Evidence

- Fact: `adhd_engine` is the runtime path; `adhd-engine` appears in docs indexing.
- Fact: the service directory is `working-memory-assistant`, but canonical runtime file declares `Dope-Memory`.
- Fact: MCP registry contains both `dopemux-claude-context` and `dope-context` pointing to the same docker service.

### Recommendation

- Recommend one naming rule per plane:
  - runtime/import/filesystem: underscore or actual checked-in path names
  - operator-facing service name: explicit canonical service label if the runtime declares one
  - MCP registry key: one canonical key per runtime
- Applied here:
  - runtime path `services/adhd_engine`, display label `adhd-engine`
  - runtime path `services/working-memory-assistant`, service authority `dope-memory`
  - MCP key authority should converge on `dope-context`

### Confidence

- MEDIUM

### Unresolved questions

- Unknown whether `dopemux-claude-context` is intentionally preserved as a compatibility alias for downstream clients.
- Unknown whether any automation or external scripts depend on the older names.

## 5. Duplicate MCP surface affecting authority

### Candidates

- `dope-context` vs `dopemux-claude-context`
- ConPort unprefixed tools vs ConPort prefixed tools
- Dope-Memory inline MCP server vs `services/working-memory-assistant/mcp/server.py`
- Task-orchestrator canonical app vs unsupported runtimes

### Evidence

- Fact: `registry.yaml` defines both `dope-context` and `dopemux-claude-context` for the same docker service.
- Fact: ConPort checked-in sources expose both prefixed and unprefixed tool families.
- Fact: tests disagree on which ConPort names are authoritative.
- Fact: Dope-Memory has duplicated MCP server logic in two files.
- Fact: task-orchestrator has `app/main.py` plus two explicit unsupported runtimes.

### Recommendation

- Recommend single MCP identity per runtime:
  - `dope-context` for context retrieval
  - one ConPort tool naming family, preferably the prefixed family if cross-server namespace isolation matters
  - one Dope-Memory MCP implementation, preferably the one attached to canonical `dope_memory_main.py`
  - `services/task-orchestrator/app/main.py` as the only valid runtime entrypoint

### Confidence

- MEDIUM

### Unresolved questions

- Unknown whether prefixed ConPort names break current local clients expecting unprefixed names.
- Unknown whether `dopemux-claude-context` is relied on by generated client config.

## 6. Duplicate eventbus / authority split

### Candidates

- canonical chronicle ledger in `.dopemux/chronicle.sqlite`
- optional Redis event stream fan-out from `emit_capture_event()`
- dopecon-bridge event routes

### Evidence

- Fact: `canonical_ledger.py` says the SQLite chronicle ledger is canonical.
- Fact: `emit_capture_event()` writes ledger first and only optionally emits Redis stream events based on `DOPEMUX_CAPTURE_EMIT_EVENTBUS`.
- Fact: dopecon-bridge states it is adapter/proxy only and not canonical authority for task/workflow/decision/progress.

### Recommendation

- Recommend chronicle SQLite ledger remain canonical event capture authority.
- Recommend Redis stream and bridge events be treated as derived or transport surfaces, not source-of-truth state.

### Confidence

- HIGH

### Unresolved questions

- Unknown which downstream consumers require Redis stream events for live behavior.

## 7. Additional canonical recommendation: repo-truth entrypaths

### Candidates

- `dopemux upgrades run`
- `dopemux extract truth-run`
- `dopemux truth`
- `dopemux extractor`

### Evidence

- Fact: repo-truth README prefers `dopemux upgrades run --pipeline-version v5`.
- Fact: `dopemux extractor` explicitly self-labels as legacy.
- Fact: `dopemux extract truth-run` directly launches `run_extraction_v5.py`.
- Fact: `dopemux truth` still exists and uses `PipelineRunner`.

### Recommendation

- Recommend `dopemux upgrades run` as canonical operator-facing CLI family because repo docs already prefer it.
- Recommend `dopemux extract truth-run` be treated as direct runtime execution path for v5 when low-level control is desired.
- Recommend `dopemux extractor` be treated as legacy only.
- Recommend `dopemux truth` be treated as compatibility wrapper unless its authority is explicitly restated.

### Confidence

- MEDIUM

### Unresolved questions

- Unknown whether `dopemux truth` is still used by existing automation or operator playbooks.
