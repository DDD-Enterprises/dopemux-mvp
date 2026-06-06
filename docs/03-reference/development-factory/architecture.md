# Development Factory — Architecture

> **Note**: All component statuses reflect static analysis only (`runtime_process_verified: false` on all entries). Compose-wiring indicates deployment intent, not confirmed running processes.

## Control Plane Hierarchy

```
Operator
  → GPT-5.5 Pro Supervisor
  → Development Factory Controller
  → Project Registry
  → Workstream Registry
  → Obligation Ledger
  → Model Routing Policy
  → Execution Capsule Compiler
  → Worktree/Branch/PR Lease Manager
  → Audit Router
  → PR Steward Intake
  → Learning Candidate Queue
```

## Component Roles

Source: Patched DCP Component Census v1.1, static analysis only.

| Component | Authority Slice | Must Not Own | Status | Evidence |
|-----------|----------------|--------------|--------|----------|
| **dopemux-core** (`src/dopemux/`, `scripts/dopetask`) | Operator control plane: CLI entrypoint, task dispatch, session management, hook dispatch | task storage (ConPort), PM metadata (Leantime), workflow transitions (task-orchestrator-kotlin-mcp), chronicle (dope-memory), code intelligence (Serena) | ACTIVE_DRIFTED | OBSERVED |
| **DCP Core** (`schemas/dcp/`, `queue_drain.py` HARD-BLOCKED) | Contract definition for live-write automation: MERGE_READINESS, LIVE_WRITE_READY, DCP_RED_MERGE_SEAM enforcement | workflow execution, PR merge while DCP-RED-MERGE-SEAM-0001 active | ACTIVE_DRIFTED | OBSERVED |
| **DCP Read-Only Facade** (`services/dcp-readonly-facade/`) | Read-only MCP surface over ConPort, dope-memory, dope-context, task-orchestrator — never writes | write operations to any system, live-write authority | ACTIVE | OBSERVED |
| **dopetask** (`scripts/dopetask`, `.dopetask-pin`) | Task execution engine — receives handoff from dopemux CLI, runs external task definitions | task storage (ConPort), workflow coordination (task-orchestrator-kotlin-mcp) | ACTIVE | OBSERVED |
| **task-orchestrator — Kotlin MCP** (external `ghcr.io/jpicklyk/task-orchestrator`, 14 tools, stdio wrapper) | Workflow transitions: queue management, task lifecycle, dependency tracking, BLOCKS DAG — canonical writer for workflow state (14 tools: 7 read-only, 4 write-non-destructive, 3 write-destructive) | task storage structure (ConPort), PM metadata (Leantime), code execution (dopetask), chronicle (dope-memory) | ACTIVE_DRIFTED | OBSERVED |
| **task-orchestrator — Python FastAPI** (`services/task-orchestrator/app/main.py`, port 8000) | REST coordination API for cross-plane operations — DISTINCT from Kotlin MCP. Authority boundary relative to Kotlin MCP is UNKNOWN | MCP tool surface (Kotlin MCP owns 14 tools), canonical task storage (ConPort) | ACTIVE | OBSERVED |
| **ConPort** (`src/conport/memory_server.py`, ports 3004/3005) | Structured decisions, progress entries, system patterns, custom data, KG relationships — canonical writer for architectural decisions | chronicle (dope-memory), workflow transitions (task-orchestrator), PM metadata (Leantime) | ACTIVE_DRIFTED | INFERRED (compose-wiring) |
| **dope-memory** (`services/working-memory-assistant/dope_memory_main.py`, port 3020) | Chronicle ledger: append-only event history, session persistence, snapshot/recovery | decisions (ConPort), workflow transitions (task-orchestrator), PM metadata (Leantime) | ACTIVE_DRIFTED | INFERRED (compose-wiring) |
| **dope-context** (`services/dope-context/`, port 3010) | AST-aware semantic code + docs retrieval — read-only | write operations, PM authority | ACTIVE | INFERRED (compose-wiring) |
| **dopecon-bridge** (`services/dopecon-bridge/`, port 3016) | Routing/proxy ONLY — `/kg/*`, `/ddg/*`, `/route/pm` are proxies, not authoritative. DANGEROUS: routes appear authoritative | canonical data, PM metadata authority, KG authority (ConPort) | ACTIVE_DRIFTED | INFERRED (compose-wiring) |
| **Repo Truth Extractor** (`services/repo-truth-extractor/run_extraction_v5.py`) | Extraction/audit subsystem: 8 phases (A/C/D/H/R/S/T/X), read-only analysis — never canonical writer | canonical PM state, live writes to production | ACTIVE_DRIFTED | OBSERVED |
| **PR Steward** (`tools/pr_steward/`, advisory only) | Advisory PR intake: emits MERGE_READINESS artifacts — CHECK-ONLY, read permissions only | live merge authority, queue_drain.py invocation | ACTIVE | OBSERVED |
| **AI Review Runner** (`tools/auditor_router/`, `.github/workflows/embedded-audit.yml`) | AI-driven code review: PAL clink (external), embedded audit (CI), security review | merge authority, live write operations | ACTIVE | OBSERVED |
| **GitHub/CI** (`.github/workflows/`, 6 required gates) | CI enforcement: 6 required gates (code-quality, tests, extractor-smoke, audit-validator, extractor-full, auditor-router) + advisory gates | live merge automation (blocked by DCP-RED-MERGE-SEAM) | ACTIVE | OBSERVED |
| **agents** (`services/agents/`, `src/dopemux/agent_orchestrator.py`) | UNKNOWN — three competing families, no declared operator-facing authority. ZERO dedicated test files for `services/agents/` | anything without declared authority (currently UNKNOWN) | ACTIVE_DRIFTED | UNKNOWN |
| **cockpit** (`scripts/dopemux_dashboard.py`) | Operator visualization — display only, no write authority | merge authority, task storage writes | ACTIVE_DRIFTED | INFERRED |

## Task-Orchestrator Contradiction

Two distinct services share the name "task-orchestrator". This is a live authority ambiguity requiring resolution.

**Kotlin MCP** — the external component:
- Docker image: `ghcr.io/jpicklyk/task-orchestrator`
- 14 tools (7 read-only, 4 write-non-destructive, 3 write-destructive)
- Protocol: MCP over stdio wrapper (`scripts/mcp-wrappers/task-orchestrator-current-stdio.sh`)
- Authority: canonical writer for workflow state (queue management, task lifecycle, BLOCKS DAG)

**Python FastAPI** — the internal service:
- Source: `services/task-orchestrator/app/main.py`
- Port: 8000
- Protocol: REST coordination API
- Declared in `compose.yml`

**The authority boundary between these two is UNKNOWN.** No documentation defines when to call each, which has precedence when they disagree, or what happens if both attempt to write the same workflow state. Callers cannot know which service they will reach without inspecting the transport layer.

This contradiction is documented for resolution in `TP-DMX-ORCH-NAMING-BOUNDARY-001`. Until resolved:
- The Kotlin MCP is the canonical authority for workflow transitions.
- The Python FastAPI service must not write workflow state that the Kotlin MCP also manages.
- Any factory component that routes to "task-orchestrator" must specify which one.
