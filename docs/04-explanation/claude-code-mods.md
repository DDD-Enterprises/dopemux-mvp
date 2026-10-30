---
id: EXPLAIN-CLAUDE-CODE-MODS
title: Dopemux Claude Code Mods
type: explanation
owner: '@hu3mann'
author: claude-code
date: '2026-10-29'
last_review: '2026-10-29'
next_review: '2027-01-27'
prelude: What a Dopemux Claude Code mod is, why the first three (Pulse, Route Ledger, Memory Bridge) exist, how they differ and overlap, how far each is proven, and where the detail lives.
---
# Dopemux Claude Code Mods

## What a mod is here

A mod is a Claude Code plugin under `plugins/dopemux-*` that changes what the person sees or what gets recorded while they work. Each one has the same shape:

- `.claude-plugin/plugin.json` names the plugin and declares its user-configurable options.
- `hooks/hooks.json` loads one module, `./register.tsx`.
- `register.tsx` registers function hooks against the host's `EngineInterface` (for example `session.start`, `command.run`, `ui.render`, `turn.complete`) and draws on the screen through `$.ui.status`, toasts and the `AbovePrompt` component.
- A `register.test.ts` runs the module against a mocked host.

Mods are Claude Code only. Codex, Gemini and OpenCode do not load them. They are loaded explicitly with `claude --plugin-dir plugins/<name>`; they are not part of `enabledPlugins` and nothing installs them by default.

## The design rule behind the first three

A mod is the right place for screen and capture. Logic, storage and policy stay in Python and in services. The three mods follow it:

| Mod | What it puts on screen | What it reads or records | Dependency outside Claude Code |
|---|---|---|---|
| **Pulse** | Status line (focus clock, energy, attention, minutes), a focus band above the prompt, toasts | Polls the ADHD engine's `/api/v1/state` every 60 s. Persists nothing. | The ADHD engine over HTTP (default `127.0.0.1:3025`) |
| **Route Ledger** | A status segment (`agents N`, advisor count), a `/route-ledger` table, toasts for unpinned Agent calls and advisor budgets | Writes receipts to `.control-tower/state/route-ledger/<sessionId>.jsonl` | None |
| **Memory Bridge** | A status line (pending count), a welcome-back band, `/bridge-note` | Writes a local outbox at `.dopemux/memory-bridge/outbox-<sessionId>.jsonl` and replays rows with `dopemux capture emit` | The `dopemux` CLI and the repo's `.dopemux/` directory |

Pulse is a reader of an existing service. Route Ledger is a recorder with no service behind it. Memory Bridge is a recorder that hands rows to an existing capture path.

## What they share, and where they could collide

All three degrade visibly instead of silently: Pulse shows `ADHD engine unreachable`, Route Ledger shows `ledger off`, Memory Bridge shows `outbox write failed` or `memory-only`.

Three surfaces are shared, and the behavior when two mods use one is **UNKNOWN**, because no mod has ever run in a real session:

- **Status line.** Each mod sets the whole status text itself (`$.ui.status(...)`). None reads or merges another's text. Whether the host composes, replaces or alternates them is not known.
- **`AbovePrompt` band.** Pulse and Memory Bridge both draw above the prompt and pass through `next(e)`. Which one draws first is not known.
- **Slash commands.** Names are `/pulse-focus`, `/break`, `/done`, `/route-ledger` (plus a best-effort `/route` alias a build may refuse) and `/bridge-note`.

The live-verification runbook includes a step for each of these.

## How far each is proven

| | Pulse | Route Ledger | Memory Bridge |
|---|---|---|---|
| Carried by | PR #1472 | PR #1482 (draft) | PR #1483 (draft) |
| Independent audit | Grok `grok-cli` / `grok-4.5`, tool-less, one attempt: `PASS_WITH_RISKS` | same route: `PASS_WITH_RISKS` | same route: `PASS_WITH_RISKS`, auditor Q9 = FAIL |
| Findings | Open, not accepted by the operator | 10, all `ACCEPTED_RISK` | 7, all `ACCEPTED_RISK` |
| Offline tests (mocked host) | 29 pass | 53 pass | 105 pass |
| Run in a real session | **NOT_RUN** | **NOT_RUN** | **NOT_RUN** |

"Offline tests pass" means the module behaves as written against a mock. It does not show that the host calls the hooks in the order the mod assumes. Every finding marked HIGH or labelled N1 or N7 in the references is that gap.

## How they ship

Each mod ships as its own PR with a signed local embedded-audit proof bound to the audited head. That binding, plus the repository's up-to-date rule on `main`, decides the merge order: see [Merging Signed-Proof PRs Under the Up-to-Date Rule](../92-runbooks/signed-proof-merge-order.md).

Repairing any audit finding changes the audited subject and needs a new audit on an operator-approved route. Findings the operator has accepted are tracked as follow-ups in each mod's `review_bundle/FOLLOWUPS.md`.

## Where the detail lives

- Reference, one per mod: [Pulse](../03-reference/mods/pulse.md), [Route Ledger](../03-reference/mods/route-ledger.md), [Memory Bridge](../03-reference/mods/memory-bridge.md)
- Running them for the first time: [Claude Code Mods Live Verification](../92-runbooks/claude-code-mods-live-verification.md)
- Agent guidance: `.claude/modules/shared/plugin-integration.md`, section "Repo-local mods"
- Related quality gate for slash commands: [Command Drift Gate](../03-reference/command-drift-gate.md)
