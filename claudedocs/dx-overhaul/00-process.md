# DX Overhaul — Process & Phase Gates

**Initiative**: End-to-end managed developer experience — "one slash command, everything works under the hood" across Claude Code, Codex, Copilot, Gemini, opencode, Grok, and the ChatGPT supervisor, in any worktree of any project.

**Started**: 2026-06-11
**Workstream**: branch `feat/dx-overhaul` (cut from main 2026-06-11). All initiative artifacts commit here until Phase 4 splits into TP-scoped branches.
**Status**: Phases 1–2 COMPLETE (research + workflow maps, PAL-validated). Next gate: operator approval to start Phase 3 (architecture).

## Phases

| Phase | Deliverable | Validation gate | Status |
|---|---|---|---|
| 1. Research | Holistic systems map + inventory/bloat audit (`01-research-synthesis.md`) | 7-domain parallel exploration, OBSERVED/INFERRED/ASPIRATIONAL labeling | ✅ DONE 2026-06-11 |
| 2. Workflow mapping | As-is vs. target journey maps (`02-workflow-maps.md`): 11 workflows, 8 primitives | PAL analyze (gemini-2.5-pro) ✅ PASS w/ 4 adopted amendments | ✅ DONE 2026-06-11 — awaiting operator gate to Phase 3 |
| 3. Architecture | Unified DX automation architecture: command set, hook spine, MCP topology, cross-tool parity layer, git/CI/PR/supervisor automation | PAL `thinkdeep → challenge → consensus`; operator approval REQUIRED before any implementation | ⏳ |
| 4. Design + load | Design specs, ADR(s), task-packet series + load plan into task-orchestrator | PAL `planner → challenge`; schema-valid TPs; operator approval of load plan | ⏳ |
| 5+. Implementation | Per-TP execution waves with proof bundles | Per AGENTS.md §4–5 (codereview → precommit per packet) | ⏳ |

## Operating rules for this initiative

- Governance per [AGENTS.md](../../AGENTS.md): Truth Order, proof-and-finality, canonical writers. Runtime evidence outranks docs.
- **Hard invariants that this initiative must NOT touch**: `DCP-RED-MERGE-SEAM-0001` (queue_drain execute seam + batch_resolve_and_merge stay blocked); `LIVE_WRITE_READY` stays UNDEFINED and blocking. Automation designs stop short of unattended merge execution.
- External validation: PAL chains at each phase gate (chain per AGENTS.md §5 risky variant for architecture).
- Every phase ends with an explicit operator approval checkpoint before the next begins.
- Model economy: Haiku for mechanical sweeps, Sonnet for synthesis/implementation, Opus/strong models for architecture judgment and audits.

## Scope decisions (operator-approved 2026-06-11)

1. **Tool strategy: Claude Code-first.** Full magic (hooks+skills+MCP) in Claude Code; other tools (Codex/Copilot/Gemini/opencode/Grok) get a synced doctrine layer + MCP access + callable repo scripts — same machinery, no per-tool hook replication.
2. **Bloat removal: hard delete.** tm:* (57), OpenMemory commands (7), aspirational orphans (~13), dead hook scripts (6), ghost MCP entries, dead config — removed in an early cleanup TP; git history is the archive.
3. **PR automation: automate to the merge button.** Auto-fix lanes for recurring CI failure classes, evidence-package assembly, supervisor verdict ingestion (signed artifact), readiness dashboard. Human/supervisor performs the merge. Hard invariants preserved (DCP-RED-MERGE-SEAM-0001, LIVE_WRITE_READY blocking).
4. **Tracking: full TP series + task-orchestrator load** with proof bundles per packet.

## Approval log

| Date | Gate | Decision | By |
|---|---|---|---|
| 2026-06-11 | Phase 1 complete; scope questions answered | 4/4 recommended options approved (see above) | operator |
| — | Phase 2 → 3 | pending | operator |

## Artifacts

- `01-research-synthesis.md` — Phase 1 synthesis (systems map, inventories, pain points, redesign levers)
- (Phase 2+) `02-workflow-maps.md`, `03-architecture.md`, ADRs in `docs/90-adr/`, TPs in `task-packets/`
