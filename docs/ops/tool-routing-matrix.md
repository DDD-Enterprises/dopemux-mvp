---
id: ops-tool-routing-matrix
title: DevOps AutoPR Tool Routing Matrix
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Tool and model routing matrix for macro-packet, implementation, embedded audit, and PR Steward intake.
---
# DevOps AutoPR Tool Routing Matrix

## Routing Rules

| Need | Preferred Tool | Fallback | Required Proof |
| --- | --- | --- | --- |
| Macro-packet authoring | GPT-5.5 Pro | human supervisor | Packet text, schema-valid generated packet, explicit allowlist. |
| Repo implementation | Codex in dedicated branch/worktree | Claude Code implementer through the same packet | Repo identity, branch, diff, command outputs, exit codes, proof. |
| Embedded audit | AGY/Antigravity Sonnet if invocation and model are locally proven | Claude Code Sonnet, Claude Code Opus, Gemini CLI | Invocation, exit code, auditor model, report path, findings, risks. |
| PR review intake | PR Steward check-only workflow | human PR steward | Harvested PR metadata, review item ledger, thread dispositions, CI triage, merge readiness. |
| Second supervisor review | skipped when gates are READY | GPT-5.5 Pro acceptance reviewer | Gate evidence or escalation rationale. |

## Local Help Constraints

OBSERVED during this packet:

- `agy --help` proves non-interactive print invocation flags (`--print`, `--prompt`) but does not expose a model-selection flag in the captured help.
- `claude --help` proves `-p/--print` and `--model <model>`, including aliases such as `sonnet` and `opus`.
- `gemini --help` proves `-p/--prompt` and `--model`.
- `gh auth status` can fail even when `gh` is installed; PR Steward must fail closed on unauthenticated GitHub state.

## Anti-Guessing Rule

Do not hardcode AGY, Antigravity, Claude Code, Gemini CLI, or GitHub CLI flags unless local help output or official docs prove them for the current run. If invocation cannot be proven, record the audit as `SKIPPED` and set the run status to `NEEDS_SUPERVISOR`.
