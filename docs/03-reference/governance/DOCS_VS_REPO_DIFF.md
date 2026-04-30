---
id: DOCS_VS_REPO_DIFF
title: Docs Vs Repo Diff
type: reference
owner: '@hu3mann'
author: codex
date: '2026-04-30'
last_review: '2026-04-30'
next_review: '2026-07-29'
prelude: Runtime-backed drift ledger comparing documentation claims with current repository truth.
---
# DOCS_VS_REPO_DIFF

## Scope

This ledger records documentation/runtime mismatches found during `TP-DMX-DOC-TRUST-001`. It does not change runtime behavior.

Required columns:

- claim
- repo truth
- mismatch type
- severity
- source path
- required TP

Severity meanings:

| Severity | Meaning |
| --- | --- |
| P0 | Authority, runtime, or port drift that can misroute operators, agents, or services. |
| P1 | Contract or documentation drift likely to cause wrong implementation decisions. |
| P2 | Naming, generated-doc, legacy, or advisory drift with lower immediate runtime risk. |
| P3 | Cleanup or archival hygiene issue. |

## Drift Ledger

| ID | Claim | Repo truth | Mismatch type | Severity | Source path(s) | Required TP |
| --- | --- | --- | --- | --- | --- | --- |
| DVSRD-001 | Task-orchestrator can be described as a clean single runtime surface. | `services/task-orchestrator/app/main.py`, `services/task-orchestrator/Dockerfile`, `compose.yml`, and `services/registry.yaml` now align on `app.main:app` and port `8000`, but legacy/runtime-conflict surfaces still exist and the verifier still reports expected task-orchestrator conflicts. | CONFLICTING runtime pointer / legacy surface | P0 | `config/runtime_authority_manifest.json`; `services/task-orchestrator/app/main.py`; `services/task-orchestrator/Dockerfile`; `services/task-orchestrator/task_orchestrator/app.py`; `docker/mcp-servers-source/services/task-orchestrator/Dockerfile`; `services/mcp-integration-bridge/main.py` | TP-DMX-RUNTIME-VERIFY-001 follow-up to remove or quarantine legacy `3014` and hard-failing entrypoint references after compatibility review. |
| DVSRD-002 | Task-orchestrator legacy module is a usable runtime target. | `services/task-orchestrator/task_orchestrator/app.py` hard-fails and tells operators to use `app/main.py` on port `8000`. | DO NOT TRUST runtime entrypoint | P0 | `services/task-orchestrator/task_orchestrator/app.py`; `services/task-orchestrator/Dockerfile`; `docs/03-reference/truth/truth-canonicals.md` | TP-DMX-RUNTIME-VERIFY-001 follow-up to ensure all launch docs and packaging exclude `task_orchestrator.app:app`. |
| DVSRD-003 | Task-orchestrator PM adapters and service ports can be documented as `3014`. | Current `src/dopemux/pm/adapters/orchestrator.py`, `compose.yml`, `services/registry.yaml`, and `services/task-orchestrator/Dockerfile` use `8000`; verifier still finds stale `3014` references in legacy MCP bridge surfaces. | Port drift | P0 | `src/dopemux/pm/adapters/orchestrator.py`; `compose.yml`; `services/registry.yaml`; `config/runtime_authority_manifest.json`; `services/mcp-integration-bridge/main.py`; `docker/mcp-servers-source/services/task-orchestrator/Dockerfile` | TP-DMX-RUNTIME-VERIFY-001 follow-up to eliminate or explicitly label all `3014` references as legacy. |
| DVSRD-004 | ConPort has one unambiguous canonical runtime pointer. | The verifier reports an expected runtime pointer conflict: tracked truth docs cite `src/conport/memory_server.py`, while compose builds through `docker/mcp-servers/conport/Dockerfile`, which points into `docker/mcp-servers-source/conport/*`. | CONFLICTING runtime pointer | P0 | `config/runtime_authority_manifest.json`; `docs/03-reference/truth/truth-canonicals.md`; `compose.yml`; `docker/mcp-servers/conport/Dockerfile`; `docker/mcp-servers-source/conport/enhanced_server.py`; `src/conport/memory_server.py` | TP-DMX-CONPORT-RUNTIME-CANONICALITY-001 to select or explicitly split source-level and deployed ConPort authority. |
| DVSRD-005 | ConPort can be treated as sole memory, PM, or universal graph authority. | Current system docs and truth docs limit ConPort to structured decision/progress/context/custom-data roles and preserve `UNKNOWN` for repo-wide exclusivity and relationship write authority. | Overbroad authority claim | P0 | `docs/assembled/chatgpt_project_top40_upload_files/16_SYSTEM_ConPort.md`; `docs/03-reference/truth/truth-data-events.md`; `src/dopemux/pm/writes.py`; `src/dopemux/pm/reads.py` | TP-DMX-CONPORT-RUNTIME-CANONICALITY-001 plus doc cleanup of any sole-authority phrasing. |
| DVSRD-006 | Bridge routes imply dopecon-bridge owns PM, task, workflow, decision, or progress truth. | Active bridge module says it is an adapter/proxy layer only and must not act as canonical task, workflow, decision, or progress authority. It exposes `/route/pm`, `/kg/*`, and `/ddg/*`, which creates authority confusion but not ownership. | Bridge authority confusion | P0 | `services/dopecon-bridge/dopecon_bridge/routes.py`; `docs/03-reference/truth/truth-gaps.md`; `docs/03-reference/planes/pm/pm-plane.md`; `docs/03-reference/systems/system-boundaries.md` | TP-DMX-BRIDGE-AUTHORITY-LANGUAGE-001 to rewrite bridge docs that imply source-truth ownership. |
| DVSRD-007 | PM plane has one canonical writer or one canonical PM service. | `src/dopemux/pm/writes.py` splits PM writes: Leantime for passive metadata, task-orchestrator for workflow transitions, ConPort for progress/decision logging, and dope-memory for mirror receipts. | Split authority not normalized | P0 | `src/dopemux/pm/writes.py`; `src/dopemux/pm/reads.py`; `docs/03-reference/planes/pm/pm-plane.md`; `docs/03-reference/systems/system-boundaries.md` | TP-DMX-PM-PLANE-CONTRACT-001 to preserve per-slice writer rules and reject unified-writer claims. |
| DVSRD-008 | PM ports are consistent across task-orchestrator, ConPort, and adapter layers. | Current task-orchestrator PM adapter defaults to `8000`; ConPort adapter defaults to `3004`; ConPort context client defaults to `3005`; compose sets task-orchestrator `8000`, ConPort HTTP `3004`, and ConPort MCP `3005`. Any doc collapsing these ports is wrong. | Port/interface split | P0 | `src/dopemux/pm/adapters/orchestrator.py`; `src/dopemux/pm/adapters/conport.py`; `src/dopemux/pm/reads.py`; `compose.yml`; `services/registry.yaml` | TP-DMX-PM-PORTS-001 to document PM read/write URL defaults and environment override rules. |
| DVSRD-009 | dope-memory stdio transport targets the active dope-memory service port. | `services/dope-memory/mcp_stdio_adapter.py` hard-codes `http://localhost:8096/tools`; compose and registry expose dope-memory on `3020`; verifier reports this as expected port conflict. | Memory transport drift | P0 | `services/dope-memory/mcp_stdio_adapter.py`; `scripts/mcp_smoke.sh`; `compose.yml`; `services/registry.yaml`; `config/runtime_authority_manifest.json` | TP-DMX-MEMORY-TRANSPORT-001 to either update the adapter target or mark it unsupported. |
| DVSRD-010 | dope-memory is PM status authority because it stores PM-related receipts. | Runtime PM writes mirror progress/decision activity into dope-memory after ConPort writes; docs identify dope-memory as historical receipt/chronicle sink, not current PM status authority. | Mirror treated as source truth | P0 | `src/dopemux/pm/writes.py`; `docs/03-reference/truth/truth-systems.md`; `docs/03-reference/planes/pm/pm-plane.md`; `services/working-memory-assistant/dope_memory_main.py` | TP-DMX-PM-PLANE-CONTRACT-001 to keep mirror receipt semantics explicit. |
| DVSRD-011 | Generated assembled docs are source authority. | `docs/assembled/chatgpt_project_top40_upload_files/32_CHATGPT_PROJECT_UPLOAD_SET.md` states generated meta files are navigation/upload context and not source authority. | Generated doc promoted too far | P1 | `docs/assembled/*`; `docs/assembled/chatgpt_project_top40_upload_files/32_CHATGPT_PROJECT_UPLOAD_SET.md`; `docs/03-reference/governance/DOC_TRUST_MAP.md` | TP-DMX-DOC-TRUST-001 follow-up only if generated docs are linked as authority elsewhere. |
| DVSRD-012 | Top-level `RULES.md`, `TRUTH_*.md`, `SYSTEM_*.md`, and PAL docs in this checkout are settled tracked authority. | `git status` shows many packet/source files as untracked in the current worktree; the assembled upload set describes them as promoted or user-provided for an upload pass. | Untracked/promoted source uncertainty | P1 | `RULES.md`; `TRUTH_*.md`; `SYSTEM_*.md`; `PAL_*.md`; `dopetask-cannonical-spec.json`; `docs/assembled/chatgpt_project_top40_upload_files/32_CHATGPT_PROJECT_UPLOAD_SET.md` | TP-DMX-DOC-CANON-PROMOTION-001 to decide whether these files become tracked canonical docs or remain upload artifacts. |
| DVSRD-013 | `dopemux truth` and extractor v5 are equivalent repo-truth paths. | Truth docs state `dopemux extractor` / `dopemux upgrades` resolve to `run_extraction_v5.py`, while `dopemux truth` uses legacy `PipelineRunner`. | Legacy CLI drift | P1 | `docs/03-reference/truth/truth-canonicals.md`; `docs/03-reference/truth/truth-interfaces.md`; `services/repo-truth-extractor/run_extraction_v5.py`; `src/dopemux/cli.py`; `src/dopemux/commands/extractor_commands.py` | TP-DMX-EXTRACTOR-CLI-ALIGN-001 to resolve or document the legacy shortcut. |
| DVSRD-014 | Agent architecture is unified. | Truth docs identify at least three agent families and mark agent authority `UNKNOWN`. | UNKNOWN canonical owner | P1 | `docs/03-reference/truth/truth-canonicals.md`; `docs/03-reference/truth/truth-gaps.md`; `services/agents`; `src/dopemux/agent_orchestrator.py`; `services/task-orchestrator/task_orchestrator/agents` | TP-DMX-AGENT-AUTHORITY-001 to identify the operator-facing agent authority. |
| DVSRD-015 | Serena has a settled repo-local implementation authority. | Truth docs keep Serena canonicality `UNKNOWN`, with deployment leaning toward Docker wrapper surfaces and in-repo implementation unresolved. | UNKNOWN canonical owner | P1 | `docs/03-reference/truth/truth-canonicals.md`; `compose.yml`; `docker/mcp-servers-source/serena`; `services/serena`; `mcp-proxy-config*.yaml`; `mcp-proxy-config.json` | TP-DMX-SERENA-AUTHORITY-001 to resolve deployment vs in-repo implementation authority. |
| DVSRD-016 | dope-context launch docs can rely on missing `run_mcp.sh`. | Truth docs record `mcp-proxy-config*.{json,yaml}` references to missing `services/dope-context/run_mcp.sh`, while Dockerfile/tests indicate `python -m src.mcp.server`. | Missing launch target | P1 | `docs/03-reference/truth/truth-gaps.md`; `docs/03-reference/truth/truth-data-events.md`; `services/dope-context/Dockerfile`; `services/dope-context/src/mcp/server.py`; `mcp-proxy-config*.yaml`; `mcp-proxy-config.json` | TP-DMX-DOPE-CONTEXT-LAUNCH-001 to align proxy config and supported launch docs. |
| DVSRD-017 | `taskx` is a separate task runtime. | `scripts/taskx` is a compatibility shim to `scripts/dopetask`; `scripts/dopetask` enforces `.dopetaskroot` and `.dopetask-pin`. | Naming drift | P2 | `scripts/taskx`; `scripts/dopetask`; `.dopetask-pin`; `docs/03-reference/truth/truth-canonicals.md`; `src/dopemux/commands/kernel_commands.py` | TP-DMX-DOPETASK-NAMING-001 to decide operator-facing TaskX vs dopetask language. |
| DVSRD-018 | Working-memory-assistant and dope-memory are one authority surface. | Truth docs split dope-memory chronicle authority from working-memory-assistant snapshot/recovery support; non-ledger WMA persistence remains `UNKNOWN`. | Overlap / UNKNOWN persistence | P2 | `services/working-memory-assistant/dope_memory_main.py`; `services/working-memory-assistant/main.py`; `services/working-memory-assistant/mcp/server.py`; `docs/03-reference/truth/truth-systems.md`; `docs/03-reference/truth/truth-data-events.md` | TP-DMX-MEMORY-AUTHORITY-001 to classify WMA runtime, MCP logic, and dope-memory chronicle roles. |

## Verifier Evidence

The runtime authority verifier was run as:

```bash
python3 scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static
```

Result:

- `ok: true`
- `errors: 0`
- `warnings: 6`

Warnings were for expected conflicts in:

- ConPort runtime pointer split.
- dope-memory stale `8096` adapter/smoke references versus `3020`.
- task-orchestrator expected conflict and stale `3014` legacy references versus `8000`.

The packet command using `python` was also attempted and failed in this shell because no `python` executable is installed. Validation therefore used `python3`.

## Non-Normalization Rule

Rows in this document intentionally preserve `UNKNOWN`, `CONFLICTING`, and `DO NOT TRUST` states. A row should not be interpreted as a fix. It is a required follow-up target or a boundary condition for future task packets.
