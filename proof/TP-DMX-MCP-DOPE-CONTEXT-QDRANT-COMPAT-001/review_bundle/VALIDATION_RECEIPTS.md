# Sanitized validation and runtime receipts

All values below were observed during supervisor-authorized execution on 2026-08-27. Secret values and full environments were neither inspected nor recorded.

## Git and packet identity

- Repo root: `/Users/hue/code/dopemux-mvp/.worktrees/dope-context-qdrant-compat-001`
- Branch: `fix/dope-context-qdrant-compat-001`
- Remote: `https://github.com/DDD-Enterprises/dopemux-mvp.git`
- Base: `c7bc2fb479d7386825df73e028acdce723ee3388`
- Content head: `8d88cc3e7f0fea65c5d5b878c3813a5a81eff356`
- Content tree: `8e06364d311371224aa4b3c74fc007bff446e86c`
- Base is ancestor of content head: exit 0
- Exact content paths:
  - `services/dope-context/src/search/dense_search.py`
  - `services/dope-context/tests/test_qdrant_sdk_contract.py`
- `git diff --binary BASE HEAD | shasum -a 256`: `5dee0a6410608cdf310c1370941a778c8ccd3d5755ef1a438aef09b705ea7ad9`
- Canonical packet hash: `bc24427a71a600b2bb57c6c6322caf2f06ba0531928f84af470b6f6be2dde662`
- Content worktree clean after commit; branch one commit ahead of local `origin/main`.
- Changed-contract validator: `status=PASS`, `max_lane=L2`, `model_audit_required=True`, `proof_only=False`, `paths=2`.

## Deterministic validation

- Locked qdrant-client 1.17.1 focused suite: exit 0; `13 passed, 1 skipped in 1.05s`.
- Ephemeral qdrant-client 1.19.0 focused suite: exit 0; `13 passed, 1 skipped in 0.84s`.
- Full locked dope-context suite: exit 0; `116 passed, 2 skipped, 1 xfailed in 2.12s`.
- Expected skips: hybrid search not invoked; live Qdrant opt-in unset.
- Expected xfail: existing F-001 vector-space model mismatch.
- Changed-file pre-commit: exit 0; all applicable hooks passed, non-applicable hooks skipped.
- `git diff --check`: exit 0.
- Gitleaks over exact binary diff: exit 0; `no leaks found`.
- Task Packet JSON schema validation against `dopetask-canonical-spec.json`: exit 0.

Invocation correction: first focused test attempt omitted required `PYTHONPATH` and failed only with `ModuleNotFoundError: No module named 'src.search'`. Exact packet command was then run and passed. This invocation error is not represented as code-path PASS.

## Historical negative evidence

Before recreation, existing container `mcp-dope-context` was restart-looping:

- Container ID: `3d2d16901749...`
- Restart count: `464`
- State: `restarting`, health `unhealthy`
- Repeated traceback terminal cause:
  `ImportError: cannot import name 'SearchRequest' from 'qdrant_client.http.models'`

This observed existing-container log is preserved negative evidence. Negative control was not deliberately rerun.

## Image and runtime

- `docker compose build dope-context`: exit 0.
- Built image manifest-list digest: `sha256:2e081f484423628bd3e6c4735615fcde4c18cf25ac1802de595ba54ac4e13ea5`.
- Installed image qdrant-client shown by build: `1.19.0`.
- Disposable no-deps image import probe: exit 0; `IMAGE_IMPORT_PROBE=PASS`.
- Only `mcp-dope-context` recreated; no dependencies or orphans recreated/removed.
- Final container ID: `00409768ff5a...`.
- Final image: `sha256:2e081f484423628bd3e6c4735615fcde4c18cf25ac1802de595ba54ac4e13ea5`.
- Final state: running, healthy, restart count 0.
- Health HTTP: `{"status":"healthy","service":"dope-context","version":"1.0.0",...}`.
- Final mounts:
  - `/Users/hue/code/dopemux-mvp/services/dope-context/data` -> `/app/data`
  - `/Users/hue/code/dopemux-mvp/services/dope-context/logs` -> `/app/logs`
  - `/Users/hue/code` -> `/workspaces`
- Container filesystem: `WORKSPACE_EXISTS=True`, `MARKER_EXISTS=True` for `/workspaces/dopemux-mvp`.
- MCP initialize: HTTP 200; protocol `2024-11-05`; server `dope-context` version `3.4.7`.
- MCP initialized notification: HTTP 202.
- MCP tools/list: HTTP 200; normal tool catalog returned.
- Provider-free `get_index_status` for `/workspaces/dopemux-mvp`: HTTP 200; `workspace_count=1`, `workspace_exists=true`, `isError=false`.
- Active code/docs collections were absent in Qdrant and reported 404/unavailable. No collection was created, deleted, indexed, or mutated.
- FastMCP startup log showed one `GET https://pypi.org/pypi/fastmcp/json` returning 200. No Voyage, Anthropic, OpenAI, XAI, Gemini, or other application-provider call was invoked by operator validation.

Mount correction disclosure: first authorized recreation resolved relative data/log binds under worktree. Health passed, but preservation check failed. Operator immediately recreated only dope-context again with primary project directory and `--no-build`, restoring exact original data/log bind sources while retaining validated image. Worktree remained clean; no data/log files appeared there. Final audit subject and final runtime receipts are after correction.

## Foreign non-mutation identity

IDs below were unchanged between pre- and post-recreation snapshots:

- Main Python Task Orchestrator: `04f4445af473`
- Leased dopemux-mvp Task Orchestrator: `6876145c8c8`
- dNh CRM Task Orchestrator: `ee85254ef7dd`
- Main ConPort: `24955f4c22c4`
- dNh CRM ConPort: `e4249293851a`
- Main dope-memory: `d34ee7c82c1f`
- dNh CRM dope-memory: `f611e7af0623`
- dNh mirror dope-memory: `61b3e0c7b291`
- Serena: `54f1431d8202`
- Qdrant: `3926a279f231`

No Task Orchestrator, ConPort, dope-memory, Serena, Qdrant, dNh CRM, credential, permission, or GitHub mutation command was issued.

## Explicit unknowns

- Exact separate supervisor amendment A1/A2/A3 source text: `UNKNOWN`; not supplied separately from canonical packet.
- Credential value equality before/after recreation: `UNKNOWN`; values were intentionally not inspected. Existing primary `.env` was reused without modification.
- Provider-attested AGY model identity: depends on AGY output; record `UNKNOWN` if absent.
