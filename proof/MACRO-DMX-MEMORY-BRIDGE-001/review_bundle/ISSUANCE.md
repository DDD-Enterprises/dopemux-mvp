# MACRO-DMX-MEMORY-BRIDGE-001 — Issuance Record

**Issued**: 2026-10-23T20:06Z by a Control Tower supervisor side session (Claude Code desktop, `claude-sonnet-5-5`, effort `high` observed via `$CLAUDE_EFFORT`).
**Operator instruction**: relayed by the session that started this one: issue, do **not** execute, a MacroPacket for the Memory Bridge mod (opportunity map builds M3 and M4).
**Source**: `claudedocs/dopemux-mods-plugins-opportunity-map-2026-10-16.md` §3, §4.1 (M3, M4), §5 rows 1-6, §6 (P3).
**Base**: `origin/main` = `93050d135ffc2592000c1d0edef82b2912935525` (fetched 2026-10-23; equals the HEAD this package was written on).
**Authority**: NONE. This record and the package grant no execution authority.

## Execution gate

Implementation starts only after the operator types, in chat:

```
AUTHORIZE_MACRO_DMX_MEMORY_BRIDGE_001_EXECUTION=YES
```

That one line authorizes W01 and the **mechanical** dispatch of W02-W05 by the gate table below. It does not authorize push, PR, signing, merge or the final-audit route; those stay separate operator gates.

## Package members (immutable; the macro pins each by SHA-256)

| Member | SHA-256 |
|---|---|
| `MACRO_PACKET.json` | `46ce5f239c0d7ce9c21e6d531d413452eaf79288fb88f43a4295ffe98958f966` |
| `EXECUTION_BINDING.json` (coordinator) | `7ced3ef9fe99a99f1624beac7541dce5938519834f091ae6a8686f5bcf337621` |
| `WORKSTREAMS/W01/TASK_PACKET.json` | `d49c5e6b9818d20468721e9dbaec9115bc957f4903b4ad7008d71f48e167f447` |
| `WORKSTREAMS/W02/TASK_PACKET.json` | `51f4ce8f617fba4dd46a08bbbdd14e7753010cc6860ddaa562c784d1960aa2a2` |
| `WORKSTREAMS/W03/TASK_PACKET.json` | `7cf31d5aae87d736319a0ab9b420647b8dd6dc209203f51ba54c47fe3260bb55` |
| `WORKSTREAMS/W04/TASK_PACKET.json` | `102caeabcf1ac6f5cf1ffaeddd9aa0332593d4e184ac0afd98e56daf6d1c7698` |
| `WORKSTREAMS/W05/TASK_PACKET.json` | `bcb8f32495a359affe9783c418c4a4e99c46ae388431638247ba357b6e53b3bc` |

This file is not referenced by the macro and is not part of the pinned subject.

## Workstreams and TP_ROUTE

| WS | Objective | Write allowlist | Deps | Group | Route (preferred → fallback) |
|---|---|---|---|---|---|
| W01 | Read-only go / no-go on recap, outbox, replay, band; ends in a machine-readable `GATE_TABLE` | `proof/MACRO-DMX-MEMORY-BRIDGE-001/review_bundle/W01_FINDINGS.md` (its only write) | — | P1 | claude-sonnet-5-5 |
| W02 | No-store core: JSONL outbox, pending-count status line, welcome-back band | `plugins/dopemux-memory-bridge/**` (plugin.json, hooks.json, register.tsx, register.test.ts, README.md; `types/index.d.ts` only if `$.state` is used) | W01 | P2 | claude-sonnet-5-5 |
| W03 | Replay to dope-memory `/tools/memory_store` and the `dopemux capture emit` ledger route (allowed sinks only), explicit fail-closed identity | same plugin files | W02 | P3 | claude-sonnet-5-5 |
| W04 | Session-start recap (dope-memory + ConPort, 1-2 s, ≤5 lines, store-down lines) | same plugin files | W02, W03 | P4 | claude-sonnet-5-5 |
| W05 | How-to `docs/02-how-to/memory-bridge.md` | that file | W02, W03, W04 | P5 | claude-haiku-5-5 → claude-sonnet-5-5 (fallback only on an evidence-backed STOP) |

- **Runner**: every child runs as `claude-code-agent`; effort is `UNKNOWN` (not settable per child from this runner). Coordinator: `claude-code-desktop`, `claude-sonnet-5-5`, `high`.
- **Parallelism**: `max_mutating_workstreams` = 1. All mod workstreams write one `register.tsx`, so they are serialized. `ct validate-macro` first flagged W03/W04 `WRITE_OVERLAP`; the fix is the explicit dependency chain W03 → W04 → W05. A dependency on a workstream the gate did not dispatch is satisfied by its recorded `SKIPPED_BY_GATE` state.
- **Lane**: L2 for all. Exactly one final independent audit, different family from the Claude implementers, operator-gated route.
- **Cost basis**: UNKNOWN (no current price evidence recorded). Selection basis: W01 is Sonnet because every downstream workstream hangs on its verdicts (a wrong GO costs up to three builds); builds follow the Pulse precedent; only the docs step is Haiku (Sonnet fallback).

```
TP_ROUTE   (coordinator, this issuance)
runner=claude-code-desktop
model=claude-sonnet-5-5
effort=high
skills=task-packet,plugin-authoring
why=session pin observed in the environment; packet authoring at a judgment tier adequate for a serialized, gate-table-driven macro

TP_ROUTE   (W01 / W02 / W03 / W04)
runner=claude-code-agent
model=claude-sonnet-5-5
effort=UNKNOWN
skills=plugin-authoring (W02-W04), task-packet
why=W01 judgment-critical gate; W02-W04 hook code with security-relevant I/O, Pulse precedent; cost UNKNOWN

TP_ROUTE   (W05)
runner=claude-code-agent
model=claude-haiku-5-5   (fallback claude-sonnet-5-5 on an evidence-backed STOP only)
effort=UNKNOWN
skills=NONE
why=docs derived from committed files; cheapest adequate; Pulse W03 precedent
```

## Gate table (W01 → dispatch)

W01 ends its findings with a `GATE_TABLE` JSON block. Verdicts are `GO | GO_REDUCED | NO_GO | UNKNOWN`; **UNKNOWN counts as NO_GO**. The team lead applies this mechanically:

| Workstream | Runs iff |
|---|---|
| W02 | `outbox` is GO / GO_REDUCED (band built iff `band` is GO / GO_REDUCED; status-line count always) |
| W03 | W02 committed and `replay.ledger_emit` or `replay.dope_memory_store` is GO / GO_REDUCED (only those sinks) |
| W04 | W02 committed and `recap.injection` and `recap.identity` are GO / GO_REDUCED and (`recap.dope_memory_recall` or `recap.conport_context`) is GO / GO_REDUCED; else the recap is `NOT_BUILT` |
| W05 | W02 ran |
| **Stop** | `outbox` NO_GO/UNKNOWN, a non-empty `authority_conflicts`, or an interface proposed that is neither named in the packets nor confirmed in source → `NEEDS_SUPERVISOR`, nothing further dispatched |

## Facts the design rests on (checked 2026-10-23, static only)

- **Mod API 2.1.304** (the map assumed 2.1.299), declaration sha256 `652e8b9b5ad4d2d7b8936a46c760bf93ab20dc7b72f4334cf3f39dd0b6109385`. Hook names confirmed: `session.start`, `session.compact`, `session.end`, `turn.complete`, `prompt.compose`, `prompt.context`, `session.append`, `ui.render` (AbovePrompt). `SessionStartResult` is `{ cwd }` echoed by core: **a hook's own value does not change the session**, so the recap cannot ride the return value (needs `$.session.append` or a `prompt.compose` section; W01 decides).
- `$.fs` has read / write / list / exists / stat and **no append or rename**; `write` replaces the whole content and `read` rejects over 4 MiB. The JSONL outbox is therefore read-modify-write (or per-session files). `$.store` is the alternative (JSON, 4 MiB). There is **no plugin data directory**; `$.plugin.root` is the mod's own source folder.
- `HttpInit` has **no timeout**. The 1-2 s limit is `Promise.race` against `$.clock.after`, as Pulse does, and Pulse's audit finding F1 (a raced fetch is not cancelled) is baked into the build packets (M03).
- `TurnCompleteInput` carries `answer` (final visible text), `reason`, `durationMs`, `usage`, `agentId`. "Files touched" needs observe-only `tool.call` hooks. "Detected decisions" has no deterministic source except an explicit marker in `answer`; the packets choose marker-only and forbid `$.model.*`.
- `$.process` is documented **CLI only**. `$.ui.status` is one line per plugin (coexists with Pulse).
- **dope-memory REST** (`services/working-memory-assistant/dope_memory_main.py`): port 3020 (`services/registry.yaml`), `POST /tools/memory_store` (1180) and `/tools/memory_recap` (1206), request models at 795-870; defaults `workspace_id="default"`, `instance_id="A"` (57-58). `mcp_http.py` also serves streamable-HTTP `/mcp`; that is not the `$.http.fetch` path.
- **Identity mismatch (P3)**: `capture_client.py:501-504` derives `workspace_id` from the repo root and `instance_id` from `DOPEMUX_INSTANCE_ID`, so a mod calling the service with its defaults would not see hook-captured rows. W01 must state what ids are proven.
- **Ledger route**: `dopemux capture emit --event <json> --mode plugin|cli|mcp|auto` (`src/dopemux/commands/capture_group_commands.py:34-66`); promotable set in `capture_client.py:41-55` and `promotion.py:23-37` (decision.logged, task.completed, manual.memory_store, and eight others).
- **ConPort**: `server.py` is the FastMCP wrapper (SSE `:3005`) over a REST data plane; `start_with_info.sh` names `enhanced_server.py` as the `:3004` HTTP plane. W01 confirms `/api/context/{ws}`, `/api/decisions`, `/api/recent-activity/{ws}` there. SSE cannot be read with `$.http.fetch`.
- **Stop / PreCompact save nothing outside an active workflow**: `native_hooks.py:610` (`_on_stop`), `:643` (`_on_pre_compact`), `:651` (`_on_session_end`) all return early without workflow state; hook captures use `emit_event_bus=False` (`:226`).
- **Recap blocker**: `claudedocs/mcp-feature-triage-2026-07.md:20` — "SessionStart recap injection (TP-MCF-004; blocked by MEMSPINE-IDENTITY-005)". `task-packets/DMX-MEMSPINE-IDENTITY-005.json` is a codex packet (series `codex/svcfin-memspine`); a git-log search found no implementing commit on main. W01 re-verifies in code.
- **Live**: conport (SSE), dope-memory, dope-context, gpt-researcher and task-orchestrator connectors failed to connect in this session. Every live-state claim is NOT_RUN.

## What I expect to be blocked and what is buildable now

| Sub-feature | Expectation | Why |
|---|---|---|
| Recap injection (W04) | **Likely NO_GO / NOT_BUILT** | injection mechanism undecided (`session.start` cannot return text); identity fail-closed packet appears open; P3 unproven; both stores unreachable here |
| Outbox + pending-count status (W02) | **Buildable now** | local file, no store dependency; needs W01's write model (no append) and location |
| Welcome-back band (W02) | **Buildable now, git segment degrades** | built from outbox data; `git status` needs `$.process` (CLI only) |
| Replay to dope-memory (W03) | **GO_REDUCED likely** | REST shape known; must run with explicit userConfig identity (fail closed); duplicate risk if `memory_store` is not idempotent |
| Ledger emit via `dopemux capture emit` (W03) | **Uncertain** | PATH `dopemux` has been stale; W01 checks `command -v` and `--help` |
| Decision detection | **Marker-only** | no deterministic source otherwise; model extraction deliberately excluded |
| `task.completed` events | **Possibly NOT_BUILT** | no deterministic signal until W01 finds one (for example a TodoWrite completion) |
| ConPort writes | **Out of scope** | doctrine says "Decisions: log in ConPort only"; the mod writes none |

## Validation at issuance

| Check | Result |
|---|---|
| `ct validate-macro --file MACRO_PACKET.json` | PASS — `STATIC_VALID`, 0 errors (first run FAIL: W03/W04 `WRITE_OVERLAP`, fixed by serializing the chain) |
| `ct bind-record --file EXECUTION_BINDING.json` | PASS — recorded to `.control-tower/state/bindings/MACRO-DMX-MEMORY-BRIDGE-001.json` (gitignored, worktree-local; content identical to the package file) |
| `ct validate-binding` (package file and recorded copy) | PASS ×2 |
| `task_packet.v2` schema W01-W05 | PASS ×5 |
| Macro pins (5 task packets + binding) | MATCH |
| Child bindings | NOT_RUN by design: created with `ct bind-record` per child before dispatch (AGENTS.md §4.7) |
| DCP route / Task Orchestrator state | NOT_RUN (task-orchestrator unreachable) |
| Live probes (conport, dope-memory, ADHD engine) | NOT_RUN |

## Decisions the issuer took (the operator may overrule before authorizing)

1. **W01's one write.** W01 is read-only toward code and services; its single write is `W01_FINDINGS.md` in the flat proof review bundle, so the go / no-go survives a deleted scratchpad (the Pulse lesson). The alternative is a pure-return W01 with the team lead writing the file.
2. **Gate table decides, no mid-macro operator stop.** The single AUTHORIZE line covers the mechanical dispatch. If you would rather see W01's verdicts first, authorize and then stop me after W01 (the macro stops at J01 anyway on any escalation condition).
3. **Marker-only decision capture, no model calls**, so the macro needs no model-call budget. A cheap-model extractor at compaction (map §4.1 "optional") is a follow-up packet.
4. **No slash commands, no ConPort writes, no `dopemux` calls in W02.**
5. **Authority note to settle**: emitting `decision.logged` to the capture ledger sits next to the doctrine "Decisions: log in ConPort only". W01 reports it as `authority_conflicts` if it finds a conflict, which stops the macro.

## Open items before authorizing

1. **Declaration file.** Each mod workstream needs this build's `claude-code.d.ts`, which the `plugin-authoring` skill writes when loaded. The coordinator loads the skill and hands over the path at dispatch (the path is session-specific). The one checked here is 2.1.304, hash above.
2. **No live proof.** Nothing here runs a real session with the mod against running stores: NOT_RUN by design and the operator's step.
3. **Audit route.** `agy gemini-3.1-pro-high` is absent; `gemini-4-argon-high` hit a 429 until about 2026-10-24T03:30Z; the Grok CLI tool-less recipe (`reference_grok_cli_contained_audit_recipe`) needs explicit approval. Copy all raw audit streams into the flat review bundle at once.
4. **Placement (Pulse lessons).** This package must not stay under `task-packets/` in the branch (preflight rejects GEC v2 packets there); the team lead flattens it into `proof/MACRO-DMX-MEMORY-BRIDGE-001/review_bundle/` and re-verifies the hashes. Proof-only closure allows only `PROOF.json`, `.sig`, `AUDITOR_REPORT.md` and flat `review_bundle/` files. Do not commit while a sibling worker edits the same worktree.
5. **Pulse overlap.** PR #1472 (Pulse) is separate. Both mods use `$.ui.status` (one per plugin) and an AbovePrompt hook; W01 Q10 checks coexistence. Nothing in this macro touches `plugins/dopemux-pulse/`.
6. **Out of scope** (separate packets): P3 identity-key repair itself (`DMX-MEMSPINE-IDENTITY-005`), model-extracted decisions, ConPort writes, re-entry buttons, the cockpit pane (M8), a marketplace manifest.

## Delegation and routing receipt (this issuance)

| Item | Value |
|---|---|
| Subagents / children spawned | 0. The evidence needed to write exact packets was a bounded set of reads that I did directly; a child would have needed the same context and added a handoff. |
| `advisor` calls | 1 (pre-writing, by the issuing session; it proposed the serialized W01-W05 structure and the d.ts-derived constraints now in the packets). Children's budget: 0, stated in every packet as C03. |
| Requested vs observed model | coordinator requested and observed `claude-sonnet-5-5` per the session environment; effort `high` from `$CLAUDE_EFFORT`; provider-attested identity UNKNOWN. |
| Files written | `task-packets/MACRO-DMX-MEMORY-BRIDGE-001/` only (uncommitted), plus the gitignored local binding record. |

## Execution outline (after the gate)

1. Fresh worktree `.worktrees/memory-bridge-001` on `feat/memory-bridge-001` from freshly fetched `origin/main` (expected `93050d135…`; if it moved and a cited file changed, stop). HEAD hard-equal; clean porcelain. Flatten this package into `proof/MACRO-DMX-MEMORY-BRIDGE-001/review_bundle/` and re-verify the SHA-256s.
2. `ct bind-record` + `ct validate-binding` for the coordinator and then each child before its dispatch.
3. Dispatch W01 (Sonnet, read-only probes). Commit its findings file. Apply the gate table (J01); write the dispatch decision beside the findings.
4. Dispatch W02, then W03, then W04 as the table allows (one at a time, each starting from the previous commit), then W05. Children never commit, push or call `advisor`; the team lead re-reads each diff, parses transcripts for advisor use, and commits one workstream per commit with an explicit pathspec.
5. Gates: `claude plugin validate/test`, `tsc -p` if types are laid, pre-commit, `validate_change_contract` plus the proof-only form, `git diff --check`. Freeze (J02), then one final audit on the operator-approved route, then the proof bundle.
6. Aggregate return (authority NONE) preserving each child's state, including `SKIPPED_BY_GATE` / `NOT_BUILT`. Push, PR, signing and merge remain operator gates.
