# Dopemux MVP

Dopemux is an operator-facing control surface and composed multi-system
workspace for development workflows. It coordinates local startup, routing,
workspace context, execution handoff, PM workflow, structured context,
chronicle memory, retrieval, and repo-truth extraction across several distinct
systems.

Dopemux is not a monolithic assistant and not a single PM, memory, retrieval,
or agent brain. Its current architecture is explicitly split-authority:
different systems own different slices of truth, and adapter or retrieval
layers do not become source truth by exposing a route.

This README is repo-grounded as of 2026-05-18. Runtime code, config, compose
wiring, tests, and active entrypoints remain stronger than this document. Where
the repository does not prove a claim, the claim is marked `UNKNOWN` or
`NEEDS_REPO_VERIFICATION`.

## What Is In This Repository

- `src/dopemux/`: the `dopemux` CLI package and operator control surface.
- `scripts/taskx` and `scripts/dopetask`: local execution handoff wrappers;
  `taskx` is a compatibility shim and `dopetask` installs/runs the pinned
  external `dopetask` CLI from `.dopetask-pin`.
- `services/task-orchestrator/`: workflow coordination and workflow transition
  service surfaces.
- `services/dopecon-bridge/`: bridge, proxy, compatibility, and event-transport
  surfaces. It is not PM, workflow, decision, progress, memory, or retrieval
  authority.
- `services/dope-context/`: code/docs indexing and retrieval. Retrieval output
  is derived and does not outrank source files.
- `services/working-memory-assistant/`: dope-memory chronicle runtime and
  adjacent working-memory support code.
- `services/adhd_engine/`: operator-support and cognitive-state service.
- `services/repo-truth-extractor/`: Repo Truth Extractor audit and extraction
  runtime. Its artifacts are evidence, not higher authority than runtime.
- `compose.yml` and `services/registry.yaml`: current local service wiring,
  service names, default ports, and health paths.
- `docs/`: active documentation, reference material, governance docs, truth
  extracts, historical docs, and archives.

## Authority Model

Treat authority by domain, not by brand name:

| Domain | Strongest observed authority | Do not overclaim |
| --- | --- | --- |
| Operator control and startup | `dopemux` CLI in `src/dopemux/cli.py` and command modules | Does not own PM, durable memory, retrieval, or execution after handoff. |
| Execution after handoff | External `dopetask` via `scripts/dopetask` | `scripts/taskx` is only a compatibility shim. |
| PM metadata | Leantime through dopemux PM adapters | Workflow legality is not Leantime's slice. |
| Workflow transitions | task-orchestrator workflow surfaces | task-orchestrator does not own all PM state. |
| Decisions, progress, structured context | ConPort | ConPort is not all memory and not PM metadata authority. |
| Historical receipts and chronicle | dope-memory chronicle ledger | dope-memory is not current PM state authority. |
| Code/docs retrieval | dope-context and ConPort retrieval surfaces | Retrieval output is derived, not source truth. |
| Bridge, proxy, event transport | dopecon-bridge | Bridge routes are not source truth. |
| Operator support | ADHD Engine | ADHD Engine is not PM or memory authority. |
| Repo audit/extraction | Repo Truth Extractor runtime | Extraction artifacts do not outrank runtime. |
| Agent ownership | `UNKNOWN` | Do not document a single repo-wide agent authority without a runtime pass. |

## Quick Start

For the short operator path, see [QUICK_START.md](QUICK_START.md). The
documentation tutorial version is [docs/01-tutorials/quickstart.md](docs/01-tutorials/quickstart.md).

Minimal setup:

```bash
git clone https://github.com/DDD-Enterprises/dopemux-mvp
cd dopemux-mvp
uv sync --frozen --extra dev
```

Manual compose startup uses the canonical root compose file:

```bash
docker network inspect dopemux-network >/dev/null 2>&1 \
  || docker network create dopemux-network
docker compose -f compose.yml up -d --build
```

Then run the operator CLI:

```bash
dopemux start
```

`dopemux start` is the operator cockpit entrypoint. The inspected CLI code
shows routing, MCP/server coordination, agent validation, context, and launch
behavior. It does not prove that the full compose stack is created for every
profile; use the explicit compose command above when you need the compose
services.

## Default Local Service Checks

The observed compose and registry defaults include:

| Service | Default host port | Health path |
| --- | ---: | --- |
| dopecon-bridge | `3016` | `/health` |
| ConPort HTTP | `3004` | `/health` |
| dope-context | `3010` | `/health` |
| dope-memory | `3020` | `/health` |
| task-orchestrator | `8000` | `/health` |
| ADHD Engine | `3025` | `/health` |
| Leantime | `8080` | `/` |
| Qdrant | `6333` | `/` |

Example checks after compose startup:

```bash
curl -fsS http://localhost:3016/health
curl -fsS http://localhost:3004/health
curl -fsS http://localhost:3010/health
curl -fsS http://localhost:3020/health
curl -fsS http://localhost:8000/health
curl -fsS http://localhost:3025/health
```

These are compose-backed defaults, not proof that every local profile uses the
same overrides. If a local `.env` changes ports, follow the runtime environment
and record the override.

## Common Workflows

- Start the operator cockpit: `dopemux start`
- Inspect CLI command groups: `dopemux --help`
- Delegate kernel execution: `dopemux kernel <command>`
- Use the canonical Repo Truth Extractor command family: `dopemux rte ...`
- Use legacy RTE compatibility only when needed: `dopemux upgrades ...`
- Start compose services manually: `docker compose -f compose.yml up -d --build`
- Check compose service state: `docker compose -f compose.yml ps`
- Validate docs before closing documentation work:

```bash
bash scripts/lint-docs.sh
python scripts/docs_validator.py
python scripts/docs_frontmatter_guard.py
python scripts/check_root_hygiene.py
git diff --check
```

## Documentation Map

- [Documentation Index](docs/INDEX.md)
- [Master Documentation Index](docs/00-MASTER-INDEX.md)
- [Quick Start](QUICK_START.md)
- [Tutorial Quickstart](docs/01-tutorials/quickstart.md)
- [Developer Onboarding](docs/02-how-to/developer-onboarding.md)
- [Project Description](PROJECT.md)
- [Architecture](ARCHITECTURE.md)
- [PM Plane](PM_PLANE.md)
- [System Boundaries](docs/03-reference/systems/system-boundaries.md)
- [Documentation Source Map](docs/03-reference/governance/dopemux-documentation-source-map.md)
- [Documentation Gap Register](docs/03-reference/governance/documentation-gap-register.md)
- [Documentation Trust Map](docs/03-reference/governance/doc-trust-map.md)

## Known Drift And Limits

- task-orchestrator runtime authority is still conflicted across active app
  code, Docker/startup wiring, and older references. Do not declare that drift
  closed without runtime validation.
- ConPort surfaces are split across HTTP/API and MCP/SSE style ports. Use the
  port and route that matches the operation.
- dope-memory and working-memory-assistant naming overlap. Treat dope-memory as
  chronicle authority unless a specific runtime path proves more.
- dopecon-bridge exposes broad PM and knowledge-graph-looking routes, but it is
  still bridge/proxy/event transport only.
- dope-context retrieval output is useful context, not source truth.
- Repo Truth Extractor artifacts are evidence outputs, not stronger than the
  runtime they describe.
- Broader agent runtime ownership is `UNKNOWN`.
- Some live startup and health behavior remains `NEEDS_REPO_VERIFICATION`
  because this documentation packet does not start the full runtime stack.

## Contributor Notes

- Read `AGENTS.md` before non-trivial repo work.
- Use an active Task Packet for scoped repo-changing work.
- Preserve the packet allowlist and avoid runtime code, service code, compose,
  dependency, or test edits unless a packet explicitly allows them.
- Inspect runtime/source truth before editing docs.
- Preserve contradictions and `UNKNOWN` instead of smoothing drift into a
  cleaner story.
- Run narrow validators first, then broader validators when the packet requires
  them.

## Status And License

The package metadata currently marks this project as alpha and MIT-licensed in
`pyproject.toml`. The repository contains operational code and active docs, but
this README does not claim production readiness.
