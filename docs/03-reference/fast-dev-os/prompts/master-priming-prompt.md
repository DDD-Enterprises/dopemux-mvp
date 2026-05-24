---
id: fast-dev-os-master-priming-prompt
title: Fast Dev OS — Master Priming Prompt
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Top-level supervisor priming for the Fast Dev OS executor prompt pack — establishes truth order, authority hierarchy, lane routing matrix, and hard nope rules before any implementer prompt is dispatched.
---
# Fast Dev OS — Master Priming Prompt

## Relationship to governance

This prompt **operationalizes** the governance layer at [`codex-authority-refresh.md`](../../governance/codex-authority-refresh.md) and [`codex-prompt-pack.md`](../../governance/codex-prompt-pack.md); it **does not override** them. When this prompt and the governance layer conflict, the governance layer wins.

## Lane

**L0–L6 (all lanes)**. This is operator-side priming, not implementer execution.

## Purpose

Use this prompt at the start of any Fast Dev OS session to brief the supervisor (you, the human operator, or a coordinating agent) on:

1. The truth order (AGENTS.md §2).
2. The authority hierarchy that determines whose word counts when sources conflict.
3. The L0–L6 lane taxonomy and the routing matrix from lane to implementer.
4. The hard nope rules that prevent foreseeable mistakes.

## Block 1 — Truth order (AGENTS.md §2)

When any two sources disagree, the one higher in this list wins:

1. Latest user instruction.
2. **Active Task Packet** (the TP file currently driving execution).
3. Runtime code, config, tests, compose, entrypoints (the live repo).
4. `TRUTH_*.md` / `docs/03-reference/truth/*` (canonical truth docs).
5. `RULES.md` / `PROJECT.md` / `ARCHITECTURE.md` / `SYSTEM_BOUNDARIES.md` / `PM_PLANE.md` / `SERVICE_CATALOG.md` / `SYSTEM_*.md` (canonical guidance docs).
6. Historical / generated / advisory / uploaded / external docs (Fast Dev OS layer is here).
7. Assumptions.

If a Fast Dev OS ledger contradicts runtime code, **runtime wins**.

## Block 2 — Authority hierarchy

- Governance layer (`docs/03-reference/governance/*`) outranks the Fast Dev OS operational layer (`docs/03-reference/fast-dev-os/*`).
- Repo-tracked artifacts outrank external evidence bases (e.g., the chat-context-v2 corpus — operator-local path documented in `evidence-notes.md`; never assume the path on a fresh checkout).
- Live `gh pr view` outranks any snapshot ledger in `pr-ledger.md`.
- Live `task-packets/INDEX.md` outranks `packet-ledger.md`.
- Live `proof/**/PROOF.json` outranks `proof-ledger.md`.
- The chat-context-v2 corpus is **advisory only**: claims derived from it must be marked `CLAIMED_CHAT` or `NEEDS_LIVE_VALIDATION`, never `OBSERVED`.

## Block 3 — Lane taxonomy (per project-constitution.md)

This taxonomy is **canonical** per `project-constitution.md`. Do not invent a different one in prompts/templates.

| Lane | Use when | Reviewer | Proof |
|------|----------|----------|-------|
| **L0: Design only** | No repo mutation | None | Citations + UNKNOWNs |
| **L1: Docs / prompt / packet** | Governance docs, prompt packs, task templates | Optional | diff, docs check, schema check |
| **L2: Bounded implementation** | Small source/test/config with clear owner | Default off | targeted tests, diff, precommit |
| **L3: Runtime spine** | CLI, dopetask, task-orchestrator, RTE, PM writes | Yes if risk ≥ medium | focused tests + integration proof |
| **L4: Boundary-sensitive** | PM, memory, retrieval, bridge, Cockpit gates, agents | Yes | boundary audit + tests |
| **L5: Security / provider / secrets** | Auth, secrets, CI, provider behavior, live extraction | Yes (security reviewer) | security scan + official docs |
| **L6: Parallel backlog** | Multiple independent low/medium packets | Spot review | branch matrix + PR checks |

## Block 4 — Routing matrix (lane → implementer)

| Lane | Constitution meaning | Preferred implementer(s) | Reviewer |
|------|----------------------|--------------------------|----------|
| L0 | Design only (no mutation) | n/a (read-only) | None |
| L1 | Docs/prompt/packet | Codex CLI, Claude Code | Optional |
| L2 | Bounded implementation | Codex CLI, Claude Code; Gemini auditor recommended | Default off |
| L3 | Runtime spine | Codex CLI primary; Gemini auditor mandatory if risk ≥ medium | Yes |
| L4 | Boundary-sensitive (PM, memory, retrieval, bridge, Cockpit gates, agents) | Codex CLI; Gemini auditor mandatory | Yes |
| L5 | Security/provider/secrets | Codex CLI primary; **no Cockpit, no bridge**; security reviewer mandatory | Yes (security) |
| L6 | Parallel backlog (multiple independent low/medium packets) | Per-packet implementer choice; spot review | Spot review |

> **No permanent three-agent ceremony.** Reviewer is only added when the lane earns it.
> **No dual implementer on one packet.** One primary implementer per TP.
> **No Cockpit execution authority.** Cockpit is a display surface (out of scope for this prompt pack).
> **No bridge-as-truth.** `dopecon-bridge` is adapter / proxy / event transport only.

## Block 5 — Hard nope rules (do not violate)

1. **No implementation without a packet.** Every repo-changing run requires a schema-valid TP JSON.
2. **No merge without proof.** Every PR must have a `proof/<series>/<TP>/PROOF.json` containing all AGENTS.md §9 required fields.
3. **No "done" without VERIFIED.** Final confidence requires evidence; never claim done from intuition.
4. **No invented paths/commands/branches/PRs/tests/capabilities/tool behavior.** Cite or stop.
5. **No live extraction / Docker startup / runtime health checks** unless the TP explicitly authorizes them.
6. **No secrets, credentials, tokens, or user-specific paths** in TP, PROOF, prompts, or PR body.
7. **No `execution.agent` values outside the schema enum** (`gemini|codex|vibe|shell`). Claude Code / Grok / Jules / Copilot route via operator narrative until the enum is extended.
8. **No silent smoothing of `AGENTS.md §10` known dangers** (bridge surfaces, task-orchestrator drift, memory overlap, agent authority UNKNOWN, dopetask/TaskX naming drift, MCP/proxy config drift). Carry them forward as UNRESOLVED in `unknown-conflicting-stale.md`.
9. **No scope creep.** Every TP has an explicit allowlist; commits outside it are forbidden.
10. **Fresh worktree per packet.** Never reuse a worktree across packets.

## Block 6 — Session opening sequence

When starting a Fast Dev OS session, the supervisor must:

1. Read `AGENTS.md` (full file, especially §2, §4, §9, §10).
2. Read the active TP (if any) at `task-packets/generated/TP-*.json`.
3. Read `project-constitution.md` to confirm the lane.
4. Read `thread00-current-operating-ledger.md` for the most recent operating context (mark as snapshot, not live truth).
5. Read `unknown-conflicting-stale.md` for unresolved authority drift.
6. Select the implementer prompt(s) per the routing matrix.
7. Brief the implementer with their prompt + the relevant TP.
8. After execution, collect the implementation report; audit if lane ≥ L3; record the acceptance decision.

## Truth posture

> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say done/complete/no issues without evidence.

> Distinguish observed vs inferred vs proposed vs unknown. If evidence is missing, say so explicitly, fail closed, mark unresolved authority as `UNKNOWN`.

## After this prompt

Dispatch the matching implementer prompt from this directory and the relevant TP. Do not mix implementer prompts in one execution (one prompt per implementer, one implementer per TP).
