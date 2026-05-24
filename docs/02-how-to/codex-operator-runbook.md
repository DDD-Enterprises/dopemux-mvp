---
id: codex-operator-runbook
title: Codex Operator Runbook
type: how-to
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Operator runbook for bounded Codex macro-packet execution in Dopemux.
---
# Codex Operator Runbook

This runbook controls how to use Codex for Dopemux macro-packet development. It does not replace `AGENTS.md`, active Task Packets, runtime code, config, tests, compose wiring, schemas, or active entrypoints. If this guide conflicts with repo truth, stop and use the stronger authority.

## Authority Boundary

Codex is a bounded implementer and reviewer for scoped repo work. It is not PM authority, memory authority, retrieval authority, bridge authority, workflow authority, runtime authority, or a repo-wide agent authority.

For Dopemux work, Codex must preserve these labels:

| Label | Meaning |
| --- | --- |
| `OBSERVED` | Direct repo evidence supports the claim. |
| `CONFLICTING` | Repo evidence shows multiple unresolved paths or owners. |
| `UNKNOWN` | Repo evidence does not prove the claim. |
| `NOT_RUN` | A requested or relevant check was intentionally not executed. |

## Codex Cloud Setup Checklist

Use this checklist before assigning a Task Packet in a Codex cloud environment:

1. Connect the environment to `DDD-Enterprises/dopemux-mvp` through the current official Codex/GitHub setup path.
2. Select the intended repository and base branch for the packet.
3. Ensure the environment can read `AGENTS.md`, `.dopetaskroot`, `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`, and the active Task Packet.
4. Keep no secrets in prompts, setup scripts, checked-in files, proof artifacts, logs, or PR text.
5. Use the setup script only for dependency installation or deterministic local tool preparation required by the packet.
6. Keep internet off during the agent phase unless the Task Packet explicitly authorizes network access and names the reason.
7. Do not add provider credentials, account tokens, or private operator material to make a packet easier to run.
8. Confirm the packet branch, proof path, and commit allowlist before starting.

Official Codex product behavior and environment controls can change. Treat the current official Codex documentation and UI as product authority, and treat this repo as authority only for Dopemux packet gates.

Product references checked for this runbook:

- [Using Codex with your ChatGPT plan](https://help.openai.com/en/articles/11369540/)
- [Enterprise admin getting started guide for Codex](https://help.openai.com/en/articles/11390924)
- [Codex changelog](https://help.openai.com/en/articles/11428266-codex-changelog)

## Minimal Operator Workflow

Use one macro-packet per meaningful outcome.

1. Assign one active Task Packet to Codex.
2. Include the packet JSON or a link to the tracked packet, plus the hard rules from `AGENTS.md`.
3. Wait for the PR and proof return. Do not start a follow-on cleanup packet while the same packet can absorb corrections.
4. Paste Codex proof to the supervisor/reviewer exactly enough to preserve commands, exit codes, changed files, diff stat, commit SHA, PR URL or blocker, residual risks, and `UNKNOWN`s.
5. Request same-packet fixes only when review finds gaps inside the existing packet scope.
6. Merge only after human acceptance, not merely because Codex opened a PR or checks passed.

## Branch, PR, And Proof Requirements

Every repo-changing Codex packet must:

- work from a dedicated branch named by the Task Packet
- confirm `.dopetaskroot` before editing
- confirm remotes identify `DDD-Enterprises/dopemux-mvp`
- validate the generated Task Packet against `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`
- edit only files listed in `commit.allowlist`
- run the packet-declared validation commands
- run codereview before precommit
- run `git diff --check` and `git diff --cached --check`
- commit only allowlisted files
- push and open a PR when authenticated
- return proof with exact commands, exit codes, changed files, diff stat, commit SHA, PR URL or exact blocker, residual risks, `UNKNOWN`s, and cleanup status

## Prohibited Without Explicit Packet Authorization

Codex must not run or claim:

- runtime or service validation
- Docker startup
- live provider calls
- live extraction
- live preflight against account-specific systems
- secret inspection
- runtime, service, compose, dependency, test, or provider-configuration edits

If a packet explicitly authorizes one of these actions, Codex must still preserve least privilege, avoid printing secret values, and mark any skipped or blocked check as `NOT_RUN`.

## Same-Packet Fix Rule

Review comments, missing proof, validator failures, and documentation gaps stay in the same packet when the requested correction is inside the packet target and allowlist. Open a new packet only when the requested work changes the outcome, touches a new authority surface, or requires files outside the current allowlist.

Same-packet fixes must refresh the proof artifact and PR evidence. Do not hide the earlier failure; record it as a failed command or resolved review finding.

## Stop Conditions

Stop and report evidence when:

- repo identity, branch, marker, or dependency preflight fails
- the Task Packet is missing, malformed, or fails schema validation
- a requested edit is outside `commit.allowlist`
- runtime authority conflicts with docs
- validation fails and the cause is not understood
- proof cannot be produced truthfully
- the operator asks Codex to merge or accept its own work
- a fix would require live provider calls, live extraction, Docker startup, or account-specific checks not authorized by the packet

## Merge Discipline

Codex may prepare a PR and request review. Codex must not treat its own proof as acceptance, and must not merge unless a human operator explicitly authorizes that merge after reviewing proof and residual risk.
