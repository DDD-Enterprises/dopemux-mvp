# ━━━◆ Ø ◆━━━

Status: [LIVE] Multi-System Workspace

# Dopemux MVP

Dopemux is an operator-facing control surface and composed multi-system workspace. It is designed to coordinate and route development workflows across a distributed set of specialized systems, ensuring that context, decisions, and execution history are preserved.

**Dopemux is not a monolithic application.** It is an orchestrator that explicitly splits authority across execution, project management (PM), memory, retrieval, and operator-support planes. There is no single "magical brain" here—only deterministic routing, structured ledgers, and distinct service boundaries.

## 1. What This Repository Contains

This repository is a mixed workspace containing:
- The `dopemux` CLI and control package (in `src/dopemux`).
- Major service implementations (in `services/`): `task-orchestrator`, `dopecon-bridge`, `dope-context`, `working-memory-assistant` (dope-memory), `adhd_engine`, and `repo-truth-extractor`.
- Configuration, compose wiring, and operational scripts for local startup.

## 2. Major Systems and Authority

The stack is composed of cooperating systems with explicit boundaries:

- **Control Plane (`dopemux`)**: Owns CLI entrypoints, local startup, MCP/server coordination, and downstream routing. It is the coordinator, not the system of record.
- **Execution Plane (`dopetask`)**: The external execution engine, reached locally via wrapper scripts (`scripts/taskx` -> `scripts/dopetask`).
- **PM Plane (Split Authority)**:
  - **Leantime**: Owns passive work-item metadata and project/ticket snapshots.
  - **task-orchestrator**: Owns workflow-significant transitions, queue state, and blockers.
  - **ConPort**: Owns structured decision, progress, and custom-data context tied to work.
  - **dope-memory**: Owns mirrored historical receipts and chronicle append logs.
- **Memory Plane**: Split between `dope-memory` (durable chronicle ledger) and `ConPort` (structured and mutable project memory).
- **Retrieval Plane**: Split between `dope-context` (deterministic code/docs indexing) and `ConPort` (semantic retrieval).
- **Bridge/Adapter Plane (`dopecon-bridge`)**: Proxies routes and event transport. **It is an operational bridge, not the source of truth.**
- **Operator-Support Plane (`ADHD Engine`)**: Serves cognitive-state, workload, and accommodation projections. It does not own PM or memory truth.
- **Extraction/Audit Plane (`repo-truth-extractor`)**: Extracts and generates evidence-backed artifacts about repo architecture (`run_extraction_v5.py`).

## 3. Getting Started

See [Quick Start](docs/01-tutorials/quickstart.md) for the shortest credible path to running the stack.

**Basic Setup:**
```bash
git clone https://github.com/DDD-Enterprises/dopemux-mvp
cd dopemux-mvp
uv sync --frozen --extra dev
```

**Starting the Stack:**
The recommended operational entrypoint is through the CLI and docker compose:
```bash
dopemux start
# OR manually:
docker compose -f compose.yml up -d
```

## 4. Key Commands

- `dopemux start`: Initiates local services and configures the environment.
- `dopemux kernel <command>`: Routes execution to the dopetask kernel.
- `dopemux routing <mode>`: Toggles model routing modes.
- `dopemux workspace switch <path>`: Switches context across configured workspaces.
- `dopemux truth`: (Legacy path) Extracts repo truth. See `repo-truth-extractor` for canonical v5 extraction.

## 5. Truth Hierarchy and Documentation Trust

To understand where authority lives, follow this precedence:
1. **Runtime code, config, and tests** (`compose.yml`, `src/`, `services/`).
2. **`TRUTH_*.md`** (Extracted evidence ledgers).
3. **Core Architecture Docs**: `ARCHITECTURE.md`, `PM_PLANE.md`, `SYSTEM_BOUNDARIES.md`, `PROJECT.md`, `BRAND_SYSTEM.md`.
4. **`SYSTEM_*.md` and `SERVICE_CATALOG.md`** in `docs/03-reference/`.

**Contribution Warning:** Do not invent a unified architecture. If a service acts as a proxy, adapter, or mirror, document it as such. Do not collapse split systems into one layer.

## 6. Known Architectural Drift (Reality Check)

This repo contains active drift. The following are proven realities in the codebase:
- **Bridge Overreach**: `dopecon-bridge` exposes PM and KG routes. Do not treat it as the canonical PM/memory authority.
- **Task Orchestrator Runtime**: Runtime packaging and startup authority are conflicted between `app/main.py`, legacy `task_orchestrator/app.py`, and Docker targets.
- **Agent Ownership**: Canonical agent ownership remains unresolved across three different families in the codebase.
- **Serena Implementation**: Canonical authority remains ambiguous between the Docker wrapper and the in-repo source.
- **Duplicate Services**: `services/adhd-engine` is a duplicate of `services/adhd_engine`. `services/dope-query` and `services/taskmaster` are legacy.

Trust the code. Read `SERVICE_CATALOG.md` and `SYSTEM_BOUNDARIES.md` before making architectural claims.
