---
id: CUSTOM_COMMANDS
title: Custom Commands
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Custom Commands (explanation) for dopemux documentation and developer workflows.
---
# Gemini Code Assist: Custom Commands

## Command: `/pr-diagnose`
**Prompt**: "Run `pr-fix` on the current PR, analyze the blockers in `READINESS_DECISION.json`, and suggest a remediation plan."

## Command: `/pr-verify`
**Prompt**: "Extract requested verification from `VERIFICATION_REQUESTS.json`, map to local commands via `CommandMapper`, and execute with evidence capture."

## Command: `/pr-resolve`
**Prompt**: "Draft evidence-backed replies for all unresolved threads using `ReviewReplyComposer` and identify resolution-ready threads via `ThreadResolutionGuard`."
