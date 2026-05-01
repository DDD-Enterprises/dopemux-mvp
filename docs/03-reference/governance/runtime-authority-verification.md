# Runtime Authority Verification

## Purpose

`config/runtime_authority_manifest.json` and `scripts/verify_runtime_authority.py` provide the first static verification layer for Dopemux runtime authority claims.

The verifier records observed runtime pointers, ports, known conflicts, wrapper drift, and non-authority surfaces. It is designed to block later packets from silently promoting bridges, shims, wrappers, mirrors, retrieval results, or stale ports into canonical authority.

## Authority Hierarchy

The verifier follows the packet authority order:

1. Runtime code, config, compose wiring, tests, and active entrypoints
2. `TRUTH_*.md`
3. `RULES.md`, `PROJECT.md`, `ARCHITECTURE.md`, `SYSTEM_BOUNDARIES.md`, `PM_PLANE.md`, and `SERVICE_CATALOG.md`
4. `SYSTEM_*.md`
5. PAL, TP, proof, and adapter contracts
6. Generated navigation and meta docs
7. Everything else

When docs and runtime disagree, runtime evidence wins. The manifest preserves conflict instead of normalizing it.

## What Static Checks Prove

The static verifier proves that:

- required authority pointer paths still exist
- known conflict markers are still present in the expected files
- stale port drift represented in the manifest is still visible
- forbidden paths are not also declared with canonical roles in the same manifest entry
- output ordering is stable and filterable by system

It does not call services, Docker, network endpoints, or external tools.

## What Static Checks Do Not Prove

The static verifier does not prove that:

- Docker images build
- services boot
- HTTP, MCP, WebSocket, Redis, PostgreSQL, Qdrant, or Leantime endpoints respond
- PM writes reconcile correctly at runtime
- ConPort, dope-memory, dope-context, Serena, or task-orchestrator storage semantics are healthy
- bridge-proxied payloads are canonical domain truth

Runtime proof must be supplied by later packets.

## How To Run

Run all static checks:

```bash
python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --check static
```

Run one system:

```bash
python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --system task-orchestrator --check static
python scripts/verify_runtime_authority.py --manifest config/runtime_authority_manifest.json --system ConPort --check static
```

System matching is case-insensitive and ignores punctuation.

## Known Conflicts Preserved

The manifest intentionally preserves these conflicts:

- `task-orchestrator`: active runtime code is `services/task-orchestrator/app/main.py`, while unsupported legacy `services/task-orchestrator/task_orchestrator/app.py` remains present and port evidence still includes `3014` versus `8000`.
- `ConPort`: Docker-packaged ConPort and `src/conport/memory_server.py` both exist, and PM access paths still use both `3004` and `3005`.
- `dope-memory`: active HTTP runtime is `3020`, while the stdio adapter still targets legacy `8096`.
- `taskx`: `scripts/taskx` is a compatibility shim only.
- `dopecon-bridge`: bridge exposes broad PM/KG/DDG routes but is transport-only for domain truth.
- `dope-context`: Docker uses `python -m src.mcp.server`, while a wrapper still invokes `python /app/server.py`.
- `Serena`: compose points to the Docker wrapper, while `services/serena` remains a larger local implementation tree with unresolved canonicality.

## Downstream Consumers

These packets should consume this verifier before making stronger runtime claims:

- `TP-DMX-TASKORCH-RUNTIME-001`
- `TP-DMX-CONPORT-AUTH-001`
- `TP-DMX-PM-PORTS-001`

## Proof Expectations

For any packet changing runtime authority:

- update the manifest only when runtime/config evidence changes
- keep conflict entries until the conflicting path or marker is actually removed or superseded
- run the static verifier for all systems and for the touched system filter
- run targeted runtime validation separately when claiming live behavior
- do not mark bridge, shim, wrapper, mirror, or retrieval output as canonical authority without direct runtime evidence
