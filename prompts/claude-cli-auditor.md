---
id: prompt-claude-cli-auditor
title: Claude CLI Auditor
type: reference
owner: '@hu3mann'
author: '@codex'
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: Embedded auditor prompt for Claude Code CLI Sonnet or Opus.
---
# Claude CLI Auditor

Audit the current packet diff in read-only mode.

Focus on:

- schema validity and strict JSON compatibility
- task-packet allowlist coverage
- proof completeness
- embedded audit schema alignment
- PR Steward being check-only
- absence of auto-fix, thread resolution, auto-merge, merge queue mutation, or secret storage
- preservation of Dopemux authority boundaries

Return a Markdown report with verdict, findings, fixes required, non-blocking risks, and skip-second-GPT-5.5 recommendation.
