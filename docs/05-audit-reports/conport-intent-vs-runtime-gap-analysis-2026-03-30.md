---
id: conport-intent-vs-runtime-gap-analysis-2026-03-30
title: Conport Intent Vs Runtime Gap Analysis 2026 03 30
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-31'
last_review: '2026-03-31'
next_review: '2026-06-29'
prelude: Conport Intent Vs Runtime Gap Analysis 2026 03 30 (reference) for dopemux
  documentation and developer workflows.
---
# ConPort Intent vs Runtime Gap Analysis

## 1. Scope

This document reconstructs the intended ConPort system from current docs, archived docs, repo-truth artifacts, historical commits, and current runtime code.

It answers four questions:

1. What ConPort was supposed to be built as.
2. Which implementation line actually existed in code at different points.
3. What is runtime-real in the current workspace.
4. What the remaining gaps are between intent and current reality.

## 2. Evidence Sources

### Current runtime authority

- `docker/mcp-servers-source/conport/enhanced_server.py`
- `docker/mcp-servers-source/conport/server.py`
- `docker/mcp-servers-source/conport/conport_mcp_stdio.py`
- `docker/mcp-servers-source/conport/schema.sql`
- `docker/mcp-servers-source/conport/unified_queries.py`
- `compose.adhd-stack.yml`
- `docker/mcp-servers-source/conport/start_with_info.sh`

### Current architecture and drift docs

- `docs/systems/conport/preferred-canonical-surface.md`
- `docs/systems/conport/surface-equivalence-and-drift.md`
- `docs/systems/conport/callable-surface-inventory.md`
- `docs/systems/conport/authority-invariants-and-dark-methods.md`
- `docs/systems/conport-kg/runtime-reality.md`
- `docs/90-adr/adr-conport-as-decision-progress-and-context-authority.md`
- `repo-truth-pack/conport/EXECUTIVE_SUMMARY.md`
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md`
- `repo-truth-pack/conport/DRIFT_REPORT.md`

### Historical design and implementation docs

- `docs/archive/implementation-history/conport-kg-2-0-master-plan.md`
- `docs/archive/services/history/conport-master-history.md`
- `docs/05-audit-reports/phase2-conport-deep-analysis.md`
- `docs/archive/history/sourceFiles/docs__rfc__RFC-001-unified-memory-graph.md`
- `docs/archive/history/sourceFiles/docs__91-rfc__rfc-002-intelligent-memory-layer.md`
- `docs/archive/history/sourceFiles/docs__MEMORY_STACK_DEPLOYMENT_SUCCESS.md`

### Historical code snapshots

- `services/conport_kg/*` at commit `c9fcdeca8`
- `docker/mcp-servers/conport/*` at commits `3fc797116`, `16616dbba`
- `src/conport/memory_server.py` at commit `fd1c5cddf`

## 3. Executive Finding

There was not one single ConPort implementation trajectory. There were three materially different ConPort lines:

1. `conport_kg`: an AGE/Cypher knowledge-graph service intended as a multi-agent memory hub.
2. `docker/mcp-servers-source/conport`: a PM-plane REST server using PostgreSQL plus Redis, with FastMCP wrappers on top.
3. `src/conport/memory_server.py`: a separate unified-memory MCP server using PostgreSQL plus Milvus for `mem.*` and `graph.*` tools.

The repo currently treats the second line as runtime-real and canonical for PM-plane decisions, progress, and context.

The first line is historically real but currently quarantined.

The third line exists in source but is not repo-proven as the active ConPort runtime. It is best classified as an alternate or incomplete implementation line, not the canonical ConPort service.

## 4. Timeline Reconstruction

## 4.1 Era A: Graph-native ConPort-KG

The older design and code line envisioned ConPort as a knowledge graph centered on Apache AGE and Cypher.

Observed evidence:

- `docs/archive/implementation-history/conport-kg-2-0-master-plan.md` describes PostgreSQL + AGE as the storage backbone, with RLS, JWT auth, agent integrations, and event processing.
- `docs/archive/services/history/conport-master-history.md` explicitly says the latest version was “V2.0 (PostgreSQL/AGE/Qdrant)” and describes AGE graph traversal and Qdrant vectors.
- `docs/05-audit-reports/phase2-conport-deep-analysis.md` describes `services/conport_kg/age_client.py`, `queries/*`, and `orchestrator.py` as production-ready AGE-based infrastructure.
- Historical commit `c9fcdeca8` contains `services/conport_kg/age_client.py`, `services/conport_kg/orchestrator.py`, and `services/conport_kg/queries/*`.

What that line was supposed to build:

- AGE-backed decision graph using Cypher.
- Multi-workspace graph creation and traversal.
- ADHD-friendly progressive-disclosure query tiers.
- Event-driven orchestrator behavior.
- Authentication, RLS, and multi-tenant agent memory hub behavior.

What is true now:

- `docs/systems/conport-kg/runtime-reality.md` explicitly says `conport-kg` is not runtime-real in the current workspace.
- The active `services/conport_kg/` source is no longer present as runnable repo-truth source.

Conclusion:

- The AGE/Cypher implementation was real historically.
- It is not the current active ConPort runtime.
- Any doc that still describes active ConPort as AGE/Cypher without qualification is stale or historical.

## 4.2 Era B: PM-plane ConPort REST server

The later ConPort line pivoted away from the graph-native service toward a PM-plane authority server for decisions, progress, and context.

Observed evidence:

- `docker/mcp-servers-source/conport/enhanced_server.py` is the current durable runtime entrypoint.
- `docker/mcp-servers-source/conport/server.py` and `conport_mcp_stdio.py` are thin FastMCP wrappers over the REST API.
- `docs/systems/conport/preferred-canonical-surface.md` says REST `/api/*` is the preferred canonical surface.
- `docs/90-adr/adr-conport-as-decision-progress-and-context-authority.md` marks ConPort as the intended canonical authority for decisions, progress, and structured context.
- `repo-truth-pack/conport/ARCHITECTURE_AND_INTENDED_USES.md` describes a three-process container with `enhanced_server.py` on `3004`, FastMCP proxy on `3005`, and info server on `4004`.

What that line was supposed to build:

- Durable PM-plane authority for decisions, progress, and context.
- PostgreSQL truth store plus Redis cache.
- REST as canonical backend contract.
- FastMCP wrappers for conversational or agent transport.
- Worktree-aware instance isolation.
- Event publishing into DopeconBridge.
- Cross-workspace query support.

What is true now:

- This is the current runtime-real ConPort line.
- It does not use Cypher in the main request path.
- It does not use Milvus or Qdrant in the current runtime code.

Conclusion:

- The repo has effectively redefined ConPort from “knowledge-graph service” to “PM-plane context authority service”.
- That architectural shift is real in code, even though many historical docs still describe the older KG identity.

## 4.3 Era C: Unified Memory Graph / Milvus line

A third design and code line exists around `src/conport/memory_server.py`.

Observed evidence:

- `docs/archive/history/sourceFiles/docs__rfc__RFC-001-unified-memory-graph.md` specifies `mem.upsert`, `mem.search`, `graph.link`, and `graph.neighbors` using SQL truth plus Milvus vectors.
- `docs/archive/history/sourceFiles/docs__91-rfc__rfc-002-intelligent-memory-layer.md` extends that into an implicit event-capture memory system.
- `docs/archive/history/sourceFiles/docs__MEMORY_STACK_DEPLOYMENT_SUCCESS.md` claims the unified memory stack was deployed and operational on port `3010`.
- `src/conport/memory_server.py` implements exactly that tool surface with PostgreSQL plus Milvus.
- Historical commit `fd1c5cddf` already contains this memory-server implementation line.

What that line was supposed to build:

- A generalized project-memory MCP server.
- PostgreSQL as graph truth plus Milvus as vector search.
- Memory tools aimed at semantic recall and graph traversal.
- Possibly conversation-log ingestion and auto-promotion logic.

What is true now:

- The source file still exists.
- The active Docker ConPort runtime does not launch it.
- Current compose and start scripts point at `docker/mcp-servers-source/conport/*`, not `src/conport/memory_server.py`.
- Current ConPort docs largely do not treat `mem.*` as the active surface.

Conclusion:

- The Milvus memory server was intended and implemented as a separate line.
- It is not currently the active ConPort runtime in this workspace.
- It appears to have been sidelined rather than fully adopted as the canonical ConPort service.

## 5. Current Runtime Reality

The current repo-proven runtime is:

- `enhanced_server.py` on port `3004`
- `server.py` on port `3005`
- `info_server.py` on port `4004`

Current runtime storage model:

- PostgreSQL for durable state
- Redis for caching
- no runtime-proven Milvus usage in the active ConPort service
- no runtime-proven AGE/Cypher traversal in the active ConPort request path

Current runtime responsibility:

- decisions
- progress
- workspace context
- recent activity and active work
- admin worktree operations
- some cross-workspace summary/query behavior via `unified_queries.py`

Current runtime does not match the old ConPort-KG vision and does not match the Milvus memory-server vision.

## 6. Design Intent by Surface

| implementation line | intended authority | intended storage | intended transport | current status |
|---|---|---|---|---|
| `services/conport_kg` | graph-native memory hub | PostgreSQL + AGE, plus Qdrant/Redis in docs | internal clients, bridge-style integrations | historical, not runtime-real |
| `docker/mcp-servers-source/conport` | PM-plane decisions/progress/context authority | PostgreSQL + Redis | REST canonical, FastMCP wrappers | current runtime-real line |
| `src/conport/memory_server.py` | unified semantic memory graph | PostgreSQL + Milvus | MCP stdio and HTTP/SSE | implemented source, not repo-proven active runtime |

## 7. Gap Analysis

## 7.1 Gap A: Identity drift

The largest gap is not a missing function. It is unresolved product identity.

Competing identities found in repo history:

- ConPort as graph-native KG.
- ConPort as PM-plane authority service.
- ConPort as unified semantic memory graph.

Impact:

- Different docs promise different storage backends.
- Different tool surfaces are treated as canonical.
- Users can plausibly expect Cypher support, Milvus search, or plain REST PM operations depending on which docs they read.

Assessment:

- This is the root drift problem.

## 7.2 Gap B: AGE/Cypher intent vs current runtime

What was supposed to exist:

- Graph-native decision traversal through Apache AGE.
- Workspace-specific graph creation.
- AGE-backed query tiers and orchestration.

What exists now:

- Current runtime uses relational tables and REST handlers.
- `unified_queries.py` and some migrations still reference `ag_catalog`.
- Current runtime docs still mention AGE ambiguity as a deployment risk.

Observed gap:

- AGE survives as residue and assumption, not as a coherent active architecture.

Assessment:

- The AGE-based implementation was not merely “not finished”.
- It was superseded or abandoned as the active runtime, but not fully retired from docs and helper code.

## 7.3 Gap C: Milvus unified-memory intent vs current runtime

What was supposed to exist:

- `mem.upsert`, `mem.search`, `graph.link`, `graph.neighbors`.
- PostgreSQL truth plus Milvus vector retrieval.
- Possibly importers and conversation-centered memory workflows.

What exists now:

- `src/conport/memory_server.py` implements this line.
- Current ConPort runtime does not start or advertise it.
- Current PM-plane ConPort docs do not recognize it as the canonical ConPort surface.

Observed gap:

- The Milvus-based memory-server line was built, but it is orphaned from the active runtime contract.

Assessment:

- This is not just “unfinished hardening”.
- It is an architectural branch that never became the canonical deployed ConPort.

## 7.4 Gap D: Surface standardization remains incomplete

The PM-plane ConPort line standardized on REST as canonical, but drift remains even inside that line.

Observed evidence from current docs and truth pack:

- JSON-RPC and FastMCP wrappers have historical payload/default mismatches.
- `workspace_summary` parity has been incomplete across surfaces.
- dark/admin methods remain exposed.
- current docs explicitly warn that JSON-RPC is compatibility-only.

Assessment:

- Even after the pivot to the PM-plane service, surface unification is incomplete.

## 7.5 Gap E: Authority claims outrun implementation

Observed evidence:

- `adr-conport-as-decision-progress-and-context-authority.md` is still `status: proposed`.
- `repo-truth-pack/conport/DRIFT_REPORT.md` says authority invariants are aspirational rather than enforced.
- append-only and “formal authority” semantics are not technically guaranteed.

Assessment:

- ConPort is treated as canonical by policy and docs, but not fully enforced as canonical by the runtime boundaries.

## 7.6 Gap F: Cross-workspace and multi-tenancy are partial and inconsistent

What was supposed to exist:

- multi-workspace isolation
- user/workspace RBAC
- cross-workspace query layer

What exists now:

- migrations for user/workspace tables
- `workspace_summary`
- `unified_queries.py`
- worktree instance operations

Observed gap:

- multi-tenancy exists in schema and helper code, but it is not consistently enforced across the runtime.
- some code still assumes `ag_catalog`.
- docs and code disagree on how complete this layer is.

## 7.7 Gap G: Security and operational hardening remain incomplete

Observed evidence:

- multiple docs call out missing auth or incomplete hardening.
- older docs identified Cypher injection in the AGE line.
- current PM-plane line still has no repo-proven auth gate across active surfaces.
- TLS was not consistently implemented until recent work on `src/conport/memory_server.py`, and that file is not the runtime-real ConPort service.

Assessment:

- Security work was pursued across different ConPort lines, but not consolidated into one clearly authoritative runtime.

## 8. What Was Supposed to Have Been Built

The strongest evidence-supported answer is:

ConPort was originally supposed to be a graph-native, multi-agent memory and decision system built on PostgreSQL AGE and related query/orchestration code.

Then the repo pivoted toward a narrower but more runtime-real PM-plane authority service on PostgreSQL plus Redis.

Separately, a generalized Milvus-backed memory-server line was designed and implemented, but it did not become the repo-proven active ConPort runtime.

So the answer is not “ConPort was supposed to use Cypher” or “ConPort was supposed to use Milvus” in the singular.

The repo shows successive intended architectures:

1. AGE/Cypher knowledge graph.
2. PM-plane REST authority service.
3. Unified memory server with Milvus.

Only the second one is currently runtime-real.

## 9. What the Repo Currently Lacks

If the goal is a coherent ConPort system, the repo currently lacks:

1. A single explicit architectural decision that retires the losing implementation lines.
2. A canonical statement on whether ConPort is:
   - a PM-plane authority service,
   - a general semantic memory graph,
   - or both, with clearly separated planes.
3. A cleanup pass removing stale AGE assumptions from current PM-plane code where they are no longer real.
4. A disposition for `src/conport/memory_server.py`:
   - adopt and wire it,
   - split it into a different product/runtime,
   - or archive it as superseded.
5. Runtime-proofed hardening for auth, tenancy, and transport consistency on the active ConPort line.

## 10. Recommended Decision Tree

## Option 1: ConPort is PM-plane only

If this is the intended future:

- retain `docker/mcp-servers-source/conport` as canonical
- remove or quarantine AGE-era docs from active reference surfaces
- remove or explicitly archive `src/conport/memory_server.py`
- eliminate residual `ag_catalog` assumptions from PM-plane runtime unless strictly proven necessary

## Option 2: ConPort is unified memory plus PM authority

If this is the intended future:

- explicitly define two sub-surfaces:
  - PM authority surface
  - semantic memory surface
- wire `src/conport/memory_server.py` into runtime or move it into the Docker ConPort package
- define canonical writer boundaries between PM records and semantic-memory graph records

## Option 3: Restore graph-native ConPort-KG

If this is the intended future:

- promote the AGE/Cypher line back into runtime-real source
- replace or integrate the PM-plane service as an adapter layer over the graph authority
- retire contradictory docs that describe purely relational PM authority as the endpoint architecture

## 11. Recommended Next Actions

1. Write an ADR that answers, unambiguously: “What is ConPort now?”
2. Mark one implementation line as canonical and the others as:
   - archived
   - derived
   - experimental
   - or pending migration
3. Remove stale active-reference docs that still describe non-canonical lines as current.
4. Audit current runtime code for residual `ag_catalog` assumptions and classify each as:
   - required,
   - stale,
   - or blocked on migration.
5. Decide the fate of `src/conport/memory_server.py` before investing more hardening into it.

## 12. Bottom Line

Yes, your instinct was correct: ConPort was at one point very much supposed to use Cypher through Apache AGE.

That was a real implementation line, not just a speculative doc.

But the current repo has pivoted away from that line as the runtime-real ConPort service. The active ConPort runtime is now the PostgreSQL-plus-Redis PM-plane server under `docker/mcp-servers-source/conport/`.

Separately, there is also a Milvus-backed memory-server line in `src/conport/memory_server.py`, which appears to be a later or parallel semantic-memory effort that never fully displaced the PM-plane ConPort runtime.

The main gap is therefore architectural drift and unresolved canonical identity, not just a few missing features.
