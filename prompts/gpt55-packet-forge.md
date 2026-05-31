---
id: prompt-gpt55-packet-forge
title: GPT-5.5 Packet Forge
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Macro-packet forge prompt for one-supervisor, one-implementer development packets.
---
# GPT-5.5 Packet Forge

Write one macro-packet for `DDD-Enterprises/dopemux-mvp`.

The packet must include:

- objective, scope in/out, authority order, and system-boundary invariants
- exact first-action inspection commands
- exact validation commands
- a concrete commit allowlist
- embedded audit requirement when governance/process/schema/prompt/proof surfaces are touched
- PR Steward readiness requirement when a PR is opened
- stop conditions for unknown reviewers, unknown bots, unclassified review items, failed checks, stale proof, and missing auditor output
- final response fields that distinguish PASS, FAIL, and NOT_RUN

Require proof with repo identity, branch, git status before/after, files changed, command outputs, exit codes, validation results, embedded audit object, and auditor report path.

Do not design auto-fix, review-thread resolution, auto-merge, merge queue mutation, or secret storage into a governance packet.
