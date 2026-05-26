---
id: ops-drift-log
title: DevOps AutoPR Drift Log
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Drift and unresolved authority notes for MP-DMX-DEVOPS-AUTOPR-001.
---
# DevOps AutoPR Drift Log

## Current Drift

| ID | Label | Drift | Handling |
| --- | --- | --- | --- |
| DRIFT-SCHEMA-PATH | OBSERVED | The packet's required first action checks `dopetask-cannonical-spec.json`, but that misspelled root file is absent. | Use observed canonical schema at `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json`. |
| DRIFT-GH-AUTH | OBSERVED | `gh` is installed, but local auth can be invalid. | PR Steward fails closed when GitHub state cannot be harvested. |
| DRIFT-AGY-MODEL | OBSERVED | `agy --help` proves print invocation but not a Sonnet model flag in captured output. | Prefer Claude Code Sonnet when model selection must be proven. |
| DRIFT-TASK-ORCH | OBSERVED | Task-orchestrator authority and packaging drift are documented in repo truth files. | Do not let PR Steward or bridge docs claim workflow authority beyond observed surfaces. |
| DRIFT-AGENT-AUTHORITY | UNKNOWN | Repo-wide agent runtime authority remains unresolved across multiple code families. | Treat agents as helpers unless a runtime path proves stronger authority. |

## Resolution Notes

- 2026-05-26: PR #704 repair updated `task-packets/generated/MP-DMX-DEVOPS-AUTOPR-001.json` S1 to check `docs/03-reference/spec/dopetask/dopetask-canonical-spec.json` directly. The original user packet still contains the misspelled first-action probe as historical input, but generated packet execution no longer depends on the absent root alias.

## Update Rule

Append drift rather than rewriting it away. If a future runtime implementation resolves an item, add a dated resolution note with evidence path, validation command, and commit/PR reference.
