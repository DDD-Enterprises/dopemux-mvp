---
id: fast-dev-os-prompts-readme
title: Fast Dev OS — Executor Prompt Pack
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Landing page for the Fast Dev OS executor prompt pack — reusable prompts for routing work across multiple implementers (Codex, Claude Code, Gemini, Grok, Jules, GitHub Copilot) with brand-safe boundaries and proof discipline.
---
# Fast Dev OS — Executor Prompt Pack

This directory contains **reusable, brand-safe prompts** for routing repo-changing or read-only work across multiple implementers under the Fast Dev OS doctrine. Each prompt enforces the same truth-posture, lane discipline, and proof requirements as the rest of the layer.

## Relationship to governance

This directory **operationalizes** the governance layer at [`codex-authority-refresh.md`](../../governance/codex-authority-refresh.md) and the existing prompt pack at [`codex-prompt-pack.md`](../../governance/codex-prompt-pack.md); it **does not override** them. When this directory and the governance layer conflict, the governance layer wins.

## Files

### Operator-side priming (run these first)

| File | Purpose |
|------|---------|
| [`master-priming-prompt.md`](master-priming-prompt.md) | Top-level supervisor primer — truth order, authority hierarchy, lane routing matrix, hard nope rules |
| [`role-priming-prompts.md`](role-priming-prompts.md) | Per-role briefs (supervisor, implementer, reviewer, auditor, operator) |

### Per-implementer prompts (route work to these)

| File | Implementer | Schema slot | Lane fit (per constitution) |
|------|-------------|-------------|------------------------------|
| [`template-codex-single-run-prompt.md`](template-codex-single-run-prompt.md) | OpenAI Codex CLI | `execution.agent="codex"` | L1–L6 (first-class) |
| [`gemini-auditor-prompt.md`](gemini-auditor-prompt.md) | Google Gemini (via PAL chain) | `execution.agent="gemini"` (requires `pal_chain.enabled=true`) | L1–L6 audit (first-class) |
| [`claude-code-implementer-prompt.md`](claude-code-implementer-prompt.md) | Anthropic Claude Code | NOT IN SCHEMA — routed via operator | L1–L4 (operator-routed) |
| [`grok-build-bounded-prompt.md`](grok-build-bounded-prompt.md) | xAI Grok | NOT IN SCHEMA — routed via operator | L1–L2 (bounded) |
| [`jules-bounded-github-prompt.md`](jules-bounded-github-prompt.md) | Google Jules | NOT IN SCHEMA — routed via operator | L1–L3 (branch-isolated) |
| [`github-copilot-agent-prompt.md`](github-copilot-agent-prompt.md) | GitHub Copilot (autonomous agent) | NOT IN SCHEMA — routed via operator | L1–L2 (autonomous bounded) |

> **RISK-SCHEMA**: `dopetask-canonical-spec.json` `execution.agent` enum is `{gemini, codex, vibe, shell}`. Claude Code, Grok, Jules, and Copilot are routed via operator narrative (not by schema enum) until a future TP extends the enum. Tasks executed under those agents should still cite `execution.agent="codex"` or `"shell"` in the TP for schema compliance, with the operator-side routing documented in the PR body.

### Operator templates (use after execution)

| File | Purpose |
|------|---------|
| [`template-implementation-report.md`](template-implementation-report.md) | Standard shape for an implementer's post-execution report |
| [`template-audit-prompt.md`](template-audit-prompt.md) | Standard shape for an auditor's review prompt |
| [`template-acceptance-decision.md`](template-acceptance-decision.md) | Standard shape for the operator's accept/reject decision record |

## Lane taxonomy (cross-reference)

All prompts reference the L0–L6 risk lane taxonomy defined in [`project-constitution.md`](../project-constitution.md). Every prompt includes a `Lane:` line indicating which lanes it is appropriate for. **Do not** use a prompt for a lane it was not authored for.

| Lane | Use when | Reviewer | Proof |
|------|----------|----------|-------|
| **L0: Design only** | No repo mutation | None | Citations + UNKNOWNs |
| **L1: Docs / prompt / packet** | Governance docs, prompt packs, task templates | Optional | diff, docs check, schema check |
| **L2: Bounded implementation** | Small source/test/config with clear owner | Default off | targeted tests, diff, precommit |
| **L3: Runtime spine** | CLI, dopetask, task-orchestrator, RTE, PM writes | Yes if risk ≥ medium | focused tests + integration proof |
| **L4: Boundary-sensitive** | PM, memory, retrieval, bridge, Cockpit gates, agents | Yes | boundary audit + tests |
| **L5: Security / provider / secrets** | Auth, secrets, CI, provider behavior, live extraction | Yes (security reviewer) | security scan + official docs |
| **L6: Parallel backlog** | Multiple independent low/medium packets | Spot review | branch matrix + PR checks |

Higher lanes require stronger PAL chains, more reviewers, and tighter proof discipline.

## Truth posture (all prompts honor this)

> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say done/complete/no issues without evidence.

> Distinguish observed vs inferred vs proposed vs unknown. If evidence is missing, say so explicitly, fail closed, mark unresolved authority as `UNKNOWN`.

> Authority order per AGENTS.md §2 applies to every prompt in this pack: latest user instruction > active Task Packet > runtime code > truth docs > guidance docs > generated/external docs > assumptions.

## How to use this pack

1. **Pick the lane** (L0–L6) appropriate to your task. See `project-constitution.md` for guidance.
2. **Pick the implementer** appropriate to the lane and the tool's capability. See `master-priming-prompt.md` for the routing matrix.
3. **Brief the implementer** with the per-implementer prompt (and role-priming if needed).
4. **Receive their implementation report** using the `template-implementation-report.md` shape.
5. **Audit (if lane ≥ L3)** using `template-audit-prompt.md`.
6. **Make the accept/reject decision** using `template-acceptance-decision.md`.

## Subsequent packets in this series

- `TP-DMX-FDOS-004-AUTHORITY-REFRESH` (merged via PR #675) — operational ledgers + project constitution.
- **TP-DMX-FDOS-005-EXECUTOR-PROMPT-PACK** — this packet (prompts under `prompts/`).
- `TP-DMX-FDOS-006-PACKET-PROOF-TEMPLATES` (planned) — reusable templates under `proof/` and root (TASK_PACKET_TEMPLATE, PROOF_BUNDLE_TEMPLATE, PR_BODY_TEMPLATE, VALIDATION_COMMAND_LIBRARY, RUNTIME_DEPENDENCY_CONES).
