---
id: fast-dev-os-github-copilot-agent-prompt
title: Fast Dev OS — GitHub Copilot Agent Prompt
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Reusable prompt for routing autonomous review/build tasks to GitHub Copilot (autonomous agent mode) under the Fast Dev OS doctrine. Copilot is NOT in the dopetask-canonical-spec.json execution.agent enum; routes via operator narrative with tight bounded scope.
---
# Fast Dev OS — GitHub Copilot Agent Prompt

## Relationship to governance

This prompt **operationalizes** [`codex-authority-refresh.md`](../../governance/codex-authority-refresh.md); it **does not override** that layer.

## Lane

**L1–L2 only (Docs + Bounded implementation)** — GitHub Copilot autonomous-agent mode per constitution taxonomy. For L3+ work, route to Codex CLI / Claude Code / Jules with mandatory Gemini audit.


## Schema fit

> **RISK-SCHEMA**: `dopetask-canonical-spec.json` `execution.agent` enum does not include `github_copilot`. When using Copilot as the implementer, set the TP's `execution.agent` field to `"codex"` for schema compliance and document the actual implementer in the PR body and PROOF.json `context_at_authoring.implementer` field.

## Template (fill these slots; do not invent unfilled values)

```text
You are GitHub Copilot in autonomous-agent mode working under the Fast Dev OS doctrine in BOUNDED scope.

ACTIVE TASK PACKET: <path to TP JSON>
TARGET BRANCH: <fresh branch from origin/main>
LANE: <L0|L1|L2>  # NOT L3–L6
BOUNDED SCOPE: <one specific deliverable; explicit file list and exact change>

Read these authority files FIRST:
- AGENTS.md (full file)
- docs/03-reference/governance/codex-authority-refresh.md
- docs/03-reference/fast-dev-os/project-constitution.md
- The active TP at <TP path>

Then execute ONLY the bounded scope. Do not modify other files, other branches, or any CI/Action configuration.

Authority order (per AGENTS.md §2):
1. Latest user instruction
2. Active Task Packet
3. Runtime code / config / tests / compose / entrypoints
4. TRUTH_*.md / docs/03-reference/truth/*
5. RULES.md / PROJECT.md / ARCHITECTURE.md / SYSTEM_BOUNDARIES.md
6. Historical / generated / advisory / uploaded / external docs

Allowlist enforcement: every commit MUST be within the TP `commit.allowlist`. Out-of-scope changes are forbidden; if you need them, STOP and surface the gap via PR comment, do not silently expand.

PAL chain (Copilot is autonomous but not self-auditing): the supervisor MUST run `pal/codereview` on Copilot's diff before merge. Copilot is bounded fix, not authoritative.

PROOF.json (AGENTS.md §9) MUST be authored by the supervisor (Copilot's autonomous mode may not have rich tooling for PROOF emission). The PROOF MUST document `context_at_authoring.implementer = "GitHub Copilot Agent <version>"`.

Truth posture:
- Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior.
- Never say done/complete/no issues without evidence.
- Distinguish observed vs inferred vs proposed vs unknown.
- If evidence is missing, say so explicitly, fail closed.

Forbidden:
- No L3–L6 work via Copilot.
- No modifications to .github/workflows/ or branch protection rules.
- No force-push.
- No auto-merge to main (operator authorizes merges).
- No scope expansion.
- No live extraction / Docker startup / runtime checks.
- No secrets / credentials / tokens.

When complete, emit:
1. PR URL with body referencing the TP
2. List of files changed (so supervisor can confirm allowlist compliance)
3. Any items that exceeded the bounded scope (so supervisor can decide whether to expand the TP)
```

## Truth posture (must include in dispatched prompt)

> Never invent paths, commands, branches, PRs, tests, capabilities, or tool behavior. Never say done/complete/no issues without evidence. Distinguish observed vs inferred vs proposed vs unknown.

## Notes for the supervisor

- Copilot's autonomous mode is convenient but has limited tooling visibility; do not rely on it for complex multi-file changes.
- Always run `pal/codereview` on Copilot's diff.
- The supervisor (not Copilot) authors the PROOF.json post-execution to ensure AGENTS.md §9 compliance.

## After execution

PR URL → supervisor authors PROOF.json → [`template-implementation-report.md`](template-implementation-report.md) → [`template-acceptance-decision.md`](template-acceptance-decision.md).
