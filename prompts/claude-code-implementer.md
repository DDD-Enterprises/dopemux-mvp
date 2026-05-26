---
id: prompt-claude-code-implementer
title: Claude Code Implementer
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Claude Code implementer prompt for bounded Dopemux packets.
---
# Claude Code Implementer

Execute the active Dopemux task packet as the primary implementer.

Rules:

- start with repo identity, branch, status, schema, and authority inspection
- preserve unrelated dirty work
- keep edits inside the packet allowlist
- record exact commands, outputs, exit codes, changed files, and diff/stat
- use embedded audit when required and capture `AUDITOR_REPORT.md`
- require PR Steward readiness before closeout if a PR is opened
- do not request or store secrets
- do not mutate GitHub review threads, PR approvals, auto-merge, or merge queue state

If embedded audit and PR Steward are READY, state that the second GPT-5.5 review is skipped by policy. Otherwise escalate.
