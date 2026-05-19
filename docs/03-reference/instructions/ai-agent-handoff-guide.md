---
id: ai-agent-handoff-guide
title: AI Agent Handoff Guide
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: Handoff guidance for AI agents working in Dopemux without becoming authority owners.
---
# AI Agent Handoff Guide

This guide is for AI agents contributing to Dopemux. Agents are workflow
participants, not source-truth owners.

## Ground Rules

- Do not invent repo facts, tests, files, commits, PRs, or runtime behavior.
- Do not expose hidden chain-of-thought. Provide concise reasoning summaries,
  evidence, commands, and outcomes instead.
- Do not treat prompts, generated artifacts, retrieval output, or older docs as
  stronger than runtime/source truth.
- Do not promote dopecon-bridge to PM, workflow, decision, progress, memory, or
  retrieval authority.
- Do not treat dope-memory as all memory.
- Do not treat dope-context retrieval as source truth.
- Do not treat Repo Truth Extractor artifacts as higher authority than runtime.
- Preserve `UNKNOWN` when agent authority or runtime ownership is unresolved.

## Required Handoff Fields

A handoff should include:

- active Task Packet ID
- branch and commit SHA
- PR URL or blocker
- changed files
- validations and exit codes
- `PASS`, `FAIL`, and `NOT_RUN` sections
- residual risks
- unresolved `UNKNOWN`s
- rollback path
- next requested action

## Authority Reminder

Use the truth hierarchy from `docs/03-reference/governance/governance-model.md`:

1. Active Task Packet for execution scope.
2. Runtime code, config, compose wiring, tests, and active entrypoints.
3. Current truth/reference docs.
4. Governance and system docs.
5. Historical or generated docs.
6. Explicit assumptions only when marked.

## PM Handoff Classification

When handing off PM work, name the writer:

- Leantime for passive metadata.
- task-orchestrator for workflow transitions.
- ConPort for decisions, progress, project context, and custom data.
- dope-memory for historical receipt/chronicle.

If a bridge route was used, state the upstream authority behind the route.

## Agent Authority Warning

Repo-wide agent runtime authority is `UNKNOWN`. Evidence exists across multiple
families, including `services/agents`, `src/dopemux/agent_orchestrator.py`, and
task-orchestrator agent surfaces. Do not claim a single canonical agent runtime
unless a later packet verifies it.

## Handoff Template

```text
Task Packet:
Branch:
Commit:
PR:
Files Changed:
Validation PASS:
Validation FAIL:
Validation NOT_RUN:
Residual Risks:
UNKNOWNs:
Rollback:
Requested Next Step:
```

## Completion Bar

An agent handoff is acceptable only when a reviewer can reproduce what happened
from repo evidence. If validation did not run, say `NOT_RUN`. If evidence is
missing, say `UNKNOWN`. If a command failed outside scope, record it instead of
expanding scope silently.
