# Dopemux Beta-Readiness — Agent-Wrapping Spec

HEAD `755bf3846` · 2026-05-29 · Decision: **codex/copilot/claude live + vanilla are ALL in beta.**

## Status: SPEC DEFERRED → `BETA-WRAP-00`

The dedicated spec agent hit a session usage limit before producing the sized work-breakdown. A full spec must be (re)run as **`BETA-WRAP-00`** (orchestrator id `3ebf520d`, Wave: Agent-Wrapping epic) — preferably by exercising each wrapping path end-to-end, not read-only. The epic's build items (`BETA-WRAP-01..04`) are **blocked by WRAP-00** in the orchestrator.

## Current state (from earlier discovery — NOT a full spec)

| surface | observed state | source |
|---------|----------------|--------|
| **claude** | Live passthrough — `src/dopemux/claude/launcher.py` spawns Claude Code via `subprocess.Popen` with generated MCP config + routing flags (`--grok`/`--codex`/`--altp`, `cli.py:1224-1365`). Closest to "works". | discovery |
| **codex** | **Absent** — no live wrapper/launcher found (only string references). Net-new build. | discovery |
| **copilot** | **Post-hoc only** — `src/dopemux/memory/adapters/copilot.py` ingests `~/.copilot/session-state/.../events.jsonl` transcripts. Not a live wrapper. | discovery |
| **vanilla** | **Unverified** — whether dopemux's hooks/MCP config degrade cleanly when claude/codex/copilot are used *outside* dopemux is untested. Ties to **BETA-HOOK-02** (unguarded hook imports can crash a clean Claude Code session). | inferred |

## Target (to be detailed in WRAP-00)
"`dopemux` CLI runs codex/copilot/claude as managed live agents (MCP config, routing, capture) **and** everything still works when those agents are used vanilla." Gap delta + sized breakdown to be produced by WRAP-00.

## Sized work-breakdown (placeholder → orchestrator epic)
| id | item | size | gate |
|----|------|------|------|
| BETA-WRAP-00 | Spec: map current, define target, size build | M | int |
| BETA-WRAP-01 | Claude live-wrapping hardening (launcher exists) | M | int |
| BETA-WRAP-02 | Codex live wrapping (build — absent today) | L/XL | int |
| BETA-WRAP-03 | Copilot live wrapping (build — ingestion only today) | L | int |
| BETA-WRAP-04 | Vanilla-passthrough compatibility (ties to BETA-HOOK-02) | M | int+pub |
