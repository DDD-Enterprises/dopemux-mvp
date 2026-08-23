---
id: codex-prompt-pack
title: Codex Prompt Pack
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Reusable Codex prompts for bounded Dopemux Task Packet execution, review, fixes, and proof return.
---
# Codex Prompt Pack

This prompt pack is reusable operator copy for Dopemux macro-packet development. It does not replace `AGENTS.md`, active Task Packets, runtime code, config, tests, compose wiring, schemas, or active entrypoints.

Codex is a bounded implementer/reviewer. Codex is not PM authority, memory authority, retrieval authority, bridge authority, repo-wide agent authority, or runtime authority.

## Master Codex Packet Execution Prompt

```text
You are Codex running in a dedicated worktree for DDD-Enterprises/dopemux-mvp.

Execute exactly the Task Packet below.

Hard rules:
- Read AGENTS.md first.
- Confirm you are inside the intended worktree, not the primary checkout.
- Confirm repo remote is DDD-Enterprises/dopemux-mvp.
- Confirm .dopetaskroot exists.
- Treat runtime code, config, tests, compose, schemas, and active entrypoints as stronger than docs.
- Preserve OBSERVED, CONFLICTING, UNKNOWN, and NOT_RUN.
- Do not modify files outside commit.allowlist.
- Do not run live provider calls, live extraction, live preflight, Docker startup, account-specific checks, or secret inspection unless the Task Packet explicitly authorizes them.
- Validate the generated packet against docs/03-reference/spec/dopetask/dopetask-canonical-spec.json.
- Work in commit-sized slices.
- Run codereview before precommit.
- Always run git diff --check and git diff --cached --check.
- Commit allowed files only.
- Push the branch and open a PR if authenticated.
- Return proof with commands, exit codes, changed files, diff stat, commit SHA, PR URL or exact blocker, residual risks, UNKNOWNs, and cleanup status.

If any preflight check fails, STOP and report evidence. Do not improvise.

Task Packet:
<paste packet JSON here>
```

## Codex PR Review Comment Prompt

Use this as a GitHub PR comment when a Codex review is wanted:

```text
@codex review

Review this PR against:
- AGENTS.md
- the active Task Packet and commit.allowlist
- runtime code/config/tests/compose/schemas/active entrypoints over docs
- proof completeness
- validation commands and exit codes
- preservation of OBSERVED, CONFLICTING, UNKNOWN, and NOT_RUN

Prioritize correctness, determinism, replayability, auditability, proof gaps, and unauthorized scope.
Do not request cosmetic refactors unless they block the packet.
```

## Same-Packet Fix Prompt

```text
Continue the same Task Packet. Do not create a new packet.

Fix only the reviewed gap below, and only inside the existing commit.allowlist.
Refresh proof in the same proof artifact.
Preserve the original failure or review finding in the proof trail.
Rerun the smallest relevant validation first, then rerun packet-required validation.
Run codereview before precommit.

Reviewed gap:
<paste exact review finding or failed command here>

STOP if the fix requires files outside commit.allowlist, runtime/provider/live extraction/Docker/account-specific checks not authorized by the packet, or a new outcome.
```

## Proof-Return Template

````text
proof-return

Task Packet:
- id:
- path:

Repo:
- worktree:
- branch:
- remote identity:
- .dopetaskroot:

Change Summary:
- <summary>

Authority Used:
- AGENTS.md:
- Task Packet:
- runtime/config/tests/compose/schemas checked:
- docs/reference checked:

Analysis Performed:
- <analysis>

Validation Performed:
PASS:
- command:
  exit_code:
  output:

FAIL:
- command:
  exit_code:
  output:

NOT_RUN:
- runtime/service validation:
- Docker startup:
- live provider calls:
- live extraction:
- account-specific checks:
- secret inspection:

Changed Files:
- <path>

Diff Stat:
```text
<paste git diff --stat or git diff --cached --stat>
```

Codereview:
- status:
- evidence:

Precommit:
- status:
- evidence:

Commit:
- sha:
- message:

PR:
- url or exact blocker:

Residual Risks / UNKNOWNs:
- <risk or UNKNOWN>

Cleanup Status:
- <status>

Rollback Plan:
- <plan>
````

## STOP Conditions

Codex must STOP when:

- repo identity, branch, marker, or dependency preflight fails
- the Task Packet fails schema validation
- the requested edit is outside `commit.allowlist`
- a command would inspect or print secret values
- a command would run live provider calls, live extraction, live preflight, Docker startup, or account-specific checks without packet authorization
- runtime truth conflicts with docs and the packet does not authorize resolving the conflict
- validation fails and the cause is unknown
- proof would require inventing commands, files, commits, PRs, runtime behavior, or test results
- the operator asks Codex to accept or merge its own work without explicit human acceptance

Report exact evidence and leave the worktree unchanged beyond already-authorized packet artifacts.

## Independent Review Triggers

Request independent review before merge when a packet touches or claims:

- schemas, manifests, migrations, serializers, APIs, MCP tools, or queue/checkpoint payloads
- workflow transitions, approvals, retries, replay, projections, or idempotency
- runtime authority, canonical writers, PM truth, memory truth, retrieval truth, bridge authority, or agent authority
- provider credentials, account-specific checks, network permissions, or secret handling
- broad docs canon changes that could weaken `AGENTS.md` or active Task Packet authority
- same-packet fixes after a failed validation whose cause was not obvious

Docs-only packets can still require independent review when they change authority language or proof gates.

## Macro-Packet Rule

Use one macro-packet per meaningful outcome. Do not create permanent three-agent theater as the default workflow. Planner/reviewer/testgen style roles are useful only when the packet risk justifies them and the handoff preserves the same packet, same allowlist, and same proof trail.
