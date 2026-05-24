---
id: dopemux-documentation-source-map
title: Dopemux Documentation Source Map
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-18'
last_review: '2026-05-18'
next_review: '2026-08-16'
prelude: Repo-grounded source map for the Dopemux documentation forge.
---
# Dopemux Documentation Source Map

This map records the source hierarchy used by the documentation forge series
`DMX-DOCS-FORGE-001`. It is documentation-only. It does not change runtime
authority and does not make generated or derived docs stronger than the
runtime files they describe.

## Authority Rules

- Active task packets control the current work slice, allowlist, validation
  obligations, stop conditions, and dependency order.
- Runtime code, config, compose wiring, tests, and active entrypoints govern
  behavior claims.
- Tracked truth references under `docs/03-reference/truth/` and current system
  references under `docs/03-reference/systems/` are orientation and evidence
  sources. They do not outrank runtime code, config, or tests.
- Historical, generated, archived, uploaded, exploratory, and design docs are
  advisory unless a runtime or tracked truth source independently supports the
  claim.
- `UNKNOWN`, drift, and contradiction must stay visible until runtime
  verification settles them.

## Source Classification

| Source | Classification | Observed use in this series | Handling rule |
| --- | --- | --- | --- |
| `task-packets/generated/TP-DMX-DOCS-FORGE-001-SOURCE-MAP-GAPS.json` | Active task packet | Current packet scope, branch, allowlist, validation commands, and proof expectations. | Strongest authority for packet 001 execution scope only. |
| `/Users/hue/code/dopemux-mvp/task-packets/dopemux_docs_forge_task_packets.json` | Intake source outside this worktree | Source array for the four-packet series. Validated against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`. | Use as packet source input; copy the active packet body into `task-packets/generated/` before implementation. |
| `AGENTS.md` | Repo workflow authority | Defines truth order, end-to-end packet workflow, task-packet rules, proof requirements, and known dangers. | Follow for workflow and final proof. It does not override the active packet allowlist. |
| `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` | Schema contract | Strict task-packet structure. | Validate every generated packet JSON against this schema before executing packet content. |
| `pyproject.toml`, `src/dopemux/cli.py`, `src/dopemux/commands/*` | Runtime/source authority | Console entrypoints, command groups, RTE command wiring, kernel delegation, routing, and operator CLI behavior. | Use for behavior claims. Docs must not overclaim beyond these files. |
| `scripts/dopetask`, `scripts/taskx`, `.dopetask-pin` | Runtime/source authority | `scripts/taskx` is a compatibility shim; `scripts/dopetask` installs and executes the pinned external `dopetask` CLI. | Document the wrapper chain explicitly. Do not treat TaskX as a separate runner. |
| `compose.yml`, `services/registry.yaml` | Runtime/config authority | Current compose services, ports, health paths, and service names. | Use for startup and port claims, while preserving drift with code defaults. |
| `src/dopemux/pm/reads.py`, `src/dopemux/pm/writes.py` | Runtime/source authority | PM read/write split across task-orchestrator, Leantime, ConPort, and dope-memory mirror receipts. | Use for PM authority claims. Do not invent one PM owner. |
| `services/task-orchestrator/app/main.py`, `services/task-orchestrator/app/*`, `services/task-orchestrator/Dockerfile`, `services/task-orchestrator/task_orchestrator/app.py` | Runtime/source authority with conflict | Active app code, Docker startup target, and hard-failing legacy module disagree. | Preserve runtime-packaging conflict. Do not declare task-orchestrator drift closed. |
| `services/dopecon-bridge/dopecon_bridge/*` | Runtime/source authority | Bridge routes, proxies, compatibility surfaces, and event transport. | Document as adapter/proxy/event transport only. It is not PM, workflow, decision, or progress authority. |
| `services/working-memory-assistant/dope_memory_main.py`, `services/working-memory-assistant/chronicle/*` | Runtime/source authority | Active dope-memory chronicle runtime and SQLite ledger behavior. | Treat as chronicle authority only, not all memory or PM truth. |
| `docker/mcp-servers-source/conport/*`, `src/conport/memory_server.py` | Runtime/source authority with unresolved deployment split | ConPort structured context/decision/progress/custom-data surfaces and alternate active-looking source tree. | Treat ConPort as structured memory authority for implemented surfaces; preserve deployment/runtime ambiguity. |
| `services/dope-context/src/mcp/server.py` | Runtime/source authority | Code/docs indexing, search, autoindex, and retrieval surfaces. | Retrieval output is derived. Source files remain source truth. |
| `services/adhd_engine/*`, `src/dopemux/adhd/*`, `services/adhd-engine/` | Runtime/source authority with duplicate family | ADHD Engine service, dopemux-side support utilities, and duplicate hyphenated tree. | Treat ADHD Engine as operator support only. Do not promote it to PM or memory authority. |
| `services/repo-truth-extractor/run_extraction_v5.py` | Runtime/source authority | Strongest repo-truth extraction runtime. | RTE artifacts are evidence outputs, not stronger than the code they analyze. |
| `PROJECT.md`, `ARCHITECTURE.md`, `PM_PLANE.md`, `SERVICE_CATALOG.md` | Current repo reference docs | Project shape, architecture planes, PM split, service tiers, and known drift. | Use for orientation after checking runtime. Preserve `UNKNOWN`. |
| `docs/03-reference/truth/*.md` | Tracked truth/reference docs | Truth scope, systems, canonicals, interfaces, data events, and gaps. | High-value evidence layer, but may lag runtime and must not outrank code/config. |
| `docs/03-reference/systems/*/system-*.md`, `docs/03-reference/systems/system-boundaries.md` | System reference docs | Component-specific authority boundaries and drift notes. | Use for system overview and boundary discipline; verify contract-sensitive claims in runtime. |
| `docs/03-reference/governance/doc-trust-map.md` | Governance reference | Classifies documentation families by trust level. | Use for docs trust posture and handling rules. |
| `docs/03-reference/governance/authority-map.md`, `docs/03-reference/governance/conflict-ledger.md` | Governance reference, older | General governance and conflict process. | Useful but less precise than current truth docs and runtime verifier outputs. |
| `README.md`, `QUICK_START.md`, `docs/01-tutorials/quickstart.md` | Operator-facing docs | Onboarding and quickstart guidance. | Treat as advisory until checked against runtime/config. Packet 002 should reconcile drift. |
| `docs/archive/*`, `reports/*`, `repo-truth-pack/*`, `out/*`, generated extraction outputs | Historical/generated/evidence artifacts | Past scans, reports, recovered docs, and generated proof. | Do not use as current authority unless runtime/tracked truth confirms the claim. |

## Canonical Writers And Non-Authority Boundaries

| Domain | Canonical or strongest observed writer | Non-authority warning |
| --- | --- | --- |
| Operator control and startup | `dopemux` CLI in `src/dopemux/cli.py` and command modules. | Does not own PM truth, durable memory, retrieval truth, or external execution after handoff. |
| Execution after handoff | External `dopetask` through `scripts/dopetask`. | `scripts/taskx` is a compatibility shim, not a separate execution engine. |
| PM metadata | Leantime through dopemux PM adapters. | Task-orchestrator and bridge routes must not be documented as metadata authority. |
| Workflow transitions | task-orchestrator workflow surfaces. | Task-orchestrator does not own all PM state. Runtime packaging conflict remains. |
| Decisions, progress, project context, custom data | ConPort implemented surfaces. | ConPort is not all memory, not PM metadata, and not chronicle truth. |
| Historical PM receipts and chronicle | dope-memory SQLite chronicle ledger. | dope-memory mirror receipts do not define current PM state. |
| Code/docs retrieval | dope-context indexing and search. | Retrieval output is derived and does not become source truth. |
| Routing, proxying, event transport | dopecon-bridge. | Bridge routes do not become canonical task, workflow, decision, progress, PM, chronicle, or retrieval authority. |
| Operator support and cognitive-state surfaces | ADHD Engine. | ADHD Engine does not own PM truth, ConPort authority, dope-memory chronicle truth, or retrieval authority. |
| Repo-truth extraction artifacts | Repo Truth Extractor runtime. | Extracted artifacts are evidence, not runtime truth. |
| Agents | `UNKNOWN` across multiple families. | Do not publish a single agent authority claim without a separate runtime pass. |

## Documentation Placement Result

Packet 001 proposed two governance reference docs:

- `docs/03-reference/governance/dopemux-documentation-source-map.md`
- `docs/03-reference/governance/documentation-gap-register.md`

These paths are under `docs/03-reference/`, which is an allowed canonical root in
`config/docs_hygiene/docs_placement_policy.yaml`. No remap was required for
packet 001.

## Sources Inspected

The packet-001 source map was built from these repo sources:

- `AGENTS.md`
- `README.md`
- `PROJECT.md`
- `ARCHITECTURE.md`
- `PM_PLANE.md`
- `SERVICE_CATALOG.md`
- `BRAND_SYSTEM.md`
- `compose.yml`
- `services/registry.yaml`
- `config/docs_hygiene/docs_placement_policy.yaml`
- `docs/INDEX.md`
- `docs/00-MASTER-INDEX.md`
- `docs/01-tutorials/quickstart.md`
- `docs/03-reference/governance/doc-trust-map.md`
- `docs/03-reference/governance/authority-map.md`
- `docs/03-reference/governance/conflict-ledger.md`
- `docs/03-reference/governance/rules.md`
- `docs/03-reference/systems/system-boundaries.md`
- `docs/03-reference/systems/*/system-*.md`
- `docs/03-reference/truth/*.md`
- `src/dopemux/pm/reads.py`
- `src/dopemux/pm/writes.py`
- `scripts/dopetask`
- `scripts/taskx`
- `.dopetask-pin`
- `pyproject.toml`

## Packet-001 Use

Use this source map as the first-pass navigation and trust map for the rest of
the Documentation Forge series. It is not a substitute for runtime inspection.
If a later packet finds runtime truth that contradicts this document, the later
packet must preserve the contradiction and update the gap register rather than
flattening the story.
