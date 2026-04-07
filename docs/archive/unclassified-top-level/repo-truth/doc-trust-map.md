---
id: doc-trust-map
title: Doc Trust Map
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-31'
last_review: '2026-03-31'
next_review: '2026-06-29'
prelude: Doc Trust Map (explanation) for dopemux documentation and developer workflows.
---
# Doc Trust Map

Scope:
- Trust levels below cover the docs inspected for this architecture-focused audit, including historical docs explicitly reviewed because they still overlap current architecture topics.
- Ratings are based on repo truth from code/config/runtime wiring, not document polish or recency labels.

Trust levels:
- `HIGH`: directly aligns with inspected runtime/config/code authority for the topic.
- `MEDIUM`: useful, but readers must cross-check specific claims or account for drift.
- `LOW`: contains enough drift that it should only be used with active code open beside it.
- `DO NOT TRUST`: architecture-affecting drift is large enough that the doc should not guide current decisions.

## Active / Current Docs

| Doc | Scope | Trust level | Reason | Recommended usage |
|---|---|---|---|---|
| `services/dopecon-bridge/README.md` | active | HIGH | Matches the active bridge boundary in `dopecon_bridge/routes.py`: adapter/proxy only, not a canonical authority. | safe reference |
| `services/taskmaster/README.md` | active | HIGH | Aligns with current PM boundary code: Taskmaster is a producer/wrapper surface and defers lifecycle state to canonical PM writes. | safe reference |
| `docs/90-adr/adr-conport-as-decision-progress-and-context-authority.md` | active | HIGH | Boundary aligns with current ConPort usage and PM write routing. | safe reference |
| `docs/90-adr/adr-dope-memory-as-chronicle-memory-authority.md` | active | HIGH | Matches canonical dope-memory runtime and chronicle ledger shape. | safe reference |
| `docs/90-adr/adr-task-orchestrator-as-workflow-authority.md` | active | HIGH | Matches current PM write split and Task Orchestrator workflow role. | safe reference |
| `docs/90-adr/adr-dope-context-as-search-and-retrieval-plane.md` | active | HIGH | Search/retrieval boundary matches the implemented dope-context server. | safe reference |
| `docs/systems/conport/preferred-canonical-surface.md` | active | HIGH | Matches current bridge/client behavior that treats ConPort REST `/api/*` as backend contract and MCP as wrapper transport. | safe reference |
| `docs/systems/conport-kg/runtime-reality.md` | active | HIGH | Correctly states that `conport-kg` is not runtime-real in the current workspace. | safe reference |
| `docs/systems/conport-kg/role-decision-and-authority-boundary.md` | active | HIGH | Correctly fail-closes graph projections out of canonical authority until a runtime exists. | safe reference |
| `docs/90-adr/adr-pm-001-canonical-task-object.md` | active | MEDIUM | Core status/lifecycle decision aligns with `src/dopemux/pm/models.py`, but the doc cites evidence-pack artifacts instead of live source files. | partial reference |
| `docs/90-adr/adr-memory-trinity-authority-and-interaction-model.md` | active | MEDIUM | The three-plane split is useful, but the `ConPort / DopeQuery` naming is stale because dope-query is not runtime-real. | partial reference |
| `docs/90-adr/adr-serena-as-technical-context-plane.md` | active | MEDIUM | Boundary is directionally correct, but the doc itself acknowledges deployment/runtime drift that is still unresolved. | partial reference |
| `docs/systems/conport/surface-equivalence-and-drift.md` | active | MEDIUM | Useful parity map, but it depends on wrapper drift details that still need code-by-code checking when integrating. | partial reference |
| `docs/systems/serena/callable-surface-inventory.md` | active | MEDIUM | Correctly narrows active Serena runtime to wrapper surfaces, but it is still a sanctioned-surface summary rather than the compose/runtime source of truth itself. | partial reference |
| `docs/systems/serena/deployment-alignment-and-sanctioned-contract.md` | active | MEDIUM | Main conclusion is right, but deployment evidence inside the doc points at `docker/mcp-servers-source/serena/*` while compose uses `docker/mcp-servers/serena/*`. | partial reference |
| `docs/03-reference/services/task-orchestrator.md` | active | MEDIUM | Correct on runtime module and workflow endpoints, but omits mounted PM write and queue/blocker/state endpoints. | partial reference |
| `docs/02-how-to/operations/pm-plane-runtime-recovery.md` | active | MEDIUM | Useful runbook framing, but it compresses runtime port and startup realities that still drift between compose and direct script defaults. | partial reference |
| `services/dope-context/README.md` | active | MEDIUM | Capability descriptions mostly map to implemented tools, but the doc uses connector-style tool names and is not the canonical source for tool inventory. | partial reference |
| `README.md` | active | LOW | Project overview is still usable, but architecture, event-bus, authority, and dopeTask sections drift from current code/config truth. | partial reference |
| `INSTALL.md` | active | LOW | Installer exists, but stack-selection and TaskX/kernel sections drift from `install.sh`, `.dopetask-pin`, and current wrapper behavior. | partial reference |
| `QUICK_START.md` | active | LOW | Documents a real MVP stack file, but not the canonical runtime/service-registry view; readers need explicit context that this is an alternate stack. | partial reference |
| `docs/00-MASTER-INDEX.md` | active | LOW | Navigation index mixes trustworthy and stale docs without any trust signal, so it is unsafe as a canonical map. | partial reference |
| `docs/docs_index.yaml` | active | LOW | Machine-readable index is valuable structurally, but it routes tools toward several stale architecture docs with no trust annotations. | partial reference |
| `docs/02-how-to/mcp-service-discovery-guide.md` | active | LOW | Pattern is still useful, but rollout counts and server inventory are stale relative to current `/info` surfaces. | partial reference |
| `docs/systems/task-orchestrator/coordination.md` | active | LOW | Contains real endpoint names, but deploy/runtime assumptions are stale enough to mislead operators. | partial reference |
| `services/adhd_engine/README.md` | active | LOW | Conceptual overview is recognizable, but route shapes and active-runtime packaging drift from the actual API and compose wiring. | partial reference |
| `services/adhd-dashboard/README.md` | active | LOW | Concrete startup instructions, defaults, and endpoint inventory drift from the implemented backend. | partial reference |
| `docs/systems/dope-context/api-reference.md` | active | LOW | Signature examples are partially useful, but the claimed tool inventory is outdated. | partial reference |
| `docs/systems/dope-context/architecture.md` | active | LOW | High-level retrieval ideas still help, but the doc mixes architecture with quantitative claims not established by the inspected runtime/config surfaces. | partial reference |
| `docs/04-explanation/technical-deep-dives/dope-memory-deep-dive-2.md` | active | LOW | Entry-point and ledger framing help, but the doc still imports stale `DopeQuery` framing into the active architecture. | partial reference |
| `docs/03-reference/mcp-tools-overview.md` | active | DO NOT TRUST | MCP server inventory and naming no longer match the canonical MCP registry. | avoid |
| `services/working-memory-assistant/README.md` | active | DO NOT TRUST | Describes the legacy WMA prototype as the primary service, which is false for current runtime understanding. | avoid |
| `services/task-orchestrator/docs/pm-plane-architecture.md` | active | DO NOT TRUST | PM authority boundaries, ConPort role, Taskmaster role, and runtime entrypoint all drift from current repo truth. | avoid |
| `docs/02-how-to/serena-v2-production-deployment.md` | active | DO NOT TRUST | Models an undeployed local Serena implementation as the production runtime. | avoid |
| `docs/04-explanation/architecture/dopemux-architecture-overview.md` | active | DO NOT TRUST | High-level system picture is materially stale across service inventory, data stores, and communication model. | avoid |

## Historical Docs

| Doc | Scope | Trust level | Reason | Recommended usage |
|---|---|---|---|---|
| `docs/archive/history/sourceFiles/docs__90-adr__039-decisions-authority-conport.md` | historical | MEDIUM | Historical framing still matches the current rule that ConPort owns decisions, but surrounding Task-Master-era sync assumptions are old. | partial reference |
| `docs/archive/history/sourceFiles/docs__master-architecture.md` | historical | DO NOT TRUST | Describes a materially different architecture centered on Claude-flow, Letta, and implementation-ready claims that do not match current runtime truth. | avoid |
| `docs/archive/history/sourceFiles/docs__rfc__RFC-001-unified-memory-graph.md` | historical | DO NOT TRUST | Memory stack assumptions are from an older Milvus/Zep/Letta era, not the current ConPort/dope-memory/dope-context split. | avoid |
| `docs/archive/blueprints/task-orchestrator-dopemux.md` | historical | DO NOT TRUST | Assumes Task Orchestrator owns a tactical execution loop and old entrypoints that are not current runtime authority. | avoid |
| `docs/archive/blueprints/conport-dopemux.md` | historical | DO NOT TRUST | Promotes ConPort into workflow/work-queue authority that current PM boundaries explicitly reject. | avoid |
| `docs/archive/history/sourceFiles/docs__90-adr__038-subtask-authority-taskmaster.md` | historical | DO NOT TRUST | Historical Task-Master-first next-action authority conflicts with the current Task Orchestrator workflow model. | avoid |

## Practical Use Order

Safest current reading order for architecture work:
1. PM and authority ADRs under `docs/90-adr/` that match current boundaries.
2. `services/dopecon-bridge/README.md` for bridge boundary.
3. `src/dopemux/pm/*.py`, `src/dopemux/mcp/registry.yaml`, `services/working-memory-assistant/dope_memory_main.py`, and `services/dope-context/src/mcp/server.py` for direct repo truth.
4. Low-trust overview docs only for historical context, never as architecture authority.
