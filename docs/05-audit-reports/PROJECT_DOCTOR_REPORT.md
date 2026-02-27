---
id: PROJECT_DOCTOR_REPORT
title: Project Doctor Report
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-25'
last_review: '2026-02-25'
next_review: '2026-05-26'
prelude: Project Doctor Report (reference) for dopemux documentation and developer
  workflows.
---
# PROJECT_DOCTOR_REPORT

- project_dir: /Users/hue/code/dopemux-mvp/.taskx/instructions
- status: pass
- detected_mode: both

## Checks

- id: files_present
  - status: pass
  - message: All required project instruction files are present
  - files: (none)
- id: sentinel_integrity
  - status: pass
  - message: TaskX/ChatX sentinel blocks are present and well-formed
  - files: AGENTS.md, CLAUDE.md, CODEX.md, PROJECT_INSTRUCTIONS.md
- id: pack_status_consistency
  - status: pass
  - message: Pack status is consistent (mode=both)
  - files: AGENTS.md, CLAUDE.md, CODEX.md, PROJECT_INSTRUCTIONS.md
- id: supervisor_prompt
  - status: pass
  - message: Supervisor prompt matches mode 'both'
  - files: /Users/hue/code/dopemux-mvp/.taskx/instructions/generated/SUPERVISOR_PRIMING_PROMPT.txt

## Per-file Status

- AGENTS.md: taskx=enabled chatx=enabled
- CLAUDE.md: taskx=enabled chatx=enabled
- CODEX.md: taskx=enabled chatx=enabled
- PROJECT_INSTRUCTIONS.md: taskx=enabled chatx=enabled

## Actions Taken

- mode_applied:both
- supervisor_prompt_generated:SUPERVISOR_PRIMING_PROMPT.txt
