---
id: codex-refresh-gap-register
title: Codex Refresh Gap Register
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Gap register for unresolved Codex authority refresh risks in dopemux repo work.
---
# Codex Refresh Gap Register

This register lists Codex-refresh gaps that must remain unresolved until proved by runtime code, config, tests, compose wiring, or active entrypoints. It is intentionally not a cleanup story.

## Gaps

| ID | Status | Gap | Evidence Boundary | Codex Handling |
| --- | --- | --- | --- | --- |
| CG-001 | `CONFLICTING` | Root-vs-docs authority path drift remains. Root files such as `AGENTS.md`, `PROJECT.md`, and `ARCHITECTURE.md` coexist with tracked docs under `docs/03-reference/*`, and some historical requested paths are absent or moved. | `AGENTS.md`; `PROJECT.md`; `ARCHITECTURE.md`; `docs/03-reference/governance/rules.md`; `docs/03-reference/systems/system-boundaries.md` | Cite exact paths used. Do not normalize root and docs authority into one source. |
| CG-002 | `CONFLICTING` | TaskX vs dopetask naming drift remains. `scripts/taskx` exists, but it is a compatibility shim to `scripts/dopetask`; older docs, tests, and packets may still say TaskX. | `scripts/taskx`; `scripts/dopetask`; `PROJECT.md`; `ARCHITECTURE.md` | For execution claims, trace the live wrapper path: `dopemux` to `scripts/taskx` to `scripts/dopetask` to external `dopetask`. |
| CG-003 | `CONFLICTING` | task-orchestrator runtime/package drift remains. The canonical observed runtime is `services/task-orchestrator/app/main.py`, Docker runs `app.main:app`, and legacy `task_orchestrator/app.py` hard-fails. | `services/task-orchestrator/app/main.py`; `services/task-orchestrator/Dockerfile`; `services/task-orchestrator/task_orchestrator/app.py`; `compose.yml` | Use the observed runtime path for behavior claims. Preserve the package/path conflict in docs and proof. |
| CG-004 | `UNKNOWN` | Agent authority UNKNOWN remains. The repo has multiple agent families and no inspected runtime path proves a single repo-wide agent authority. | `services/agents/*`; `src/dopemux/agent_orchestrator.py`; `services/task-orchestrator/task_orchestrator/agents/*`; `AGENTS.md` | Do not claim a unified agent runtime. Treat agent ownership as UNKNOWN unless a packet proves a specific runtime path. |
| CG-005 | `OBSERVED_RISK` | dopecon-bridge authority confusion risk remains. Bridge routes, proxies, adapts, and transports events, but broad PM/KG/ConPort surfaces can look canonical. | `services/dopecon-bridge/dopecon_bridge/routes.py`; `services/dopecon-bridge/kg_authority.py`; `PROJECT.md`; `ARCHITECTURE.md` | State the upstream canonical writer before any bridge-mediated write or claim. Never treat bridge proxy output as source truth by itself. |
| CG-006 | `OBSERVED_RISK` | Proof/CI insufficiency risk remains. CI, GitHub checks, commits, and PR state prove delivery signals, not semantic correctness, authority ownership, replay safety, or runtime health. | `AGENTS.md`; `docs/03-reference/governance/rules.md`; active Task Packet validation obligations | Return exact validation commands, exit codes, diff scope, PR evidence, residual risks, and UNKNOWNs. Do not say CI alone proves correctness. |
| CG-007 | `CONFLICTING` | ConPort access-contract drift remains. PM reads/writes use ConPort surfaces, while authority docs preserve split HTTP/MCP or port assumptions. | `src/dopemux/pm/writes.py`; `src/dopemux/pm/reads.py`; `services/dopecon-bridge/dopecon_bridge/routes.py`; `PROJECT.md`; `ARCHITECTURE.md` | Classify ConPort as structured decisions/progress/context authority, but keep access/port details path-specific. |
| CG-008 | `CONFLICTING` | dope-memory and working-memory-assistant naming/runtime overlap remains. The observed dope-memory HTTP runtime lives under `services/working-memory-assistant`, with adjacent memory surfaces beside it. | `services/working-memory-assistant/dope_memory_main.py`; `services/working-memory-assistant/main.py`; `services/working-memory-assistant/mcp/server.py` | Treat dope-memory as chronicle/receipt authority only where the runtime path proves it. Preserve broader memory ownership UNKNOWN. |
| CG-009 | `CONFLICTING` | Cockpit/dopeUI authority remains split or absent. Cockpit runtime-render code and tests are present; the focused source/docs search did not observe a current named `dopeUI` authority path. | `src/dopemux/ui/cockpit/*`; `src/dopemux/commands/cockpit_commands.py`; `tests/unit/dopemux/ui/cockpit/*`; focused `rg` search for `dopeUI|dope-ui|dopeui` | Do not claim Cockpit and dopeUI are one system. Mark dopeUI UNKNOWN until a live source path is proved. |
| CG-010 | `UNKNOWN` | Live-provider, live extraction, live preflight, Docker startup, and account-specific runtime state are not exercised in docs-only Codex refresh work. | Packet invariants and validation scope | Mark these as NOT_RUN in proof. Do not infer service health from static inspection. |

## Closeout Rule

These gaps close only when a later packet provides direct runtime/code/config/test evidence and validates the affected path. Until then, Codex must preserve `UNKNOWN` and `CONFLICTING` labels in analysis, proof, PR text, and handoff notes.
