---
id: STATUS_AND_SEVERITY_MODEL
title: Status And Severity Model
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Status And Severity Model (explanation) for dopemux documentation and developer
  workflows.
---
# Status and Severity Model

## Status Mapping

| State | Visual Badge | Severity Level |
| :--- | :--- | :--- |
| **READY** | `[  READY   ]` | INFO |
| **BLOCKED** | `[ BLOCKED  ]` | HIGH |
| **DEFERRED** | `[ DEFERRED ]` | MEDIUM |
| **SUPERVISED** | `[SUPERVISED]` | INFO |
| **INCIDENT** | `[ INCIDENT ]` | CRITICAL |
| **UNKNOWN** | `[  UNKNOWN  ]` | LOW |

## Severity Mapping

| Level | ANSI Color | Purpose |
| :--- | :--- | :--- |
| **CRITICAL** | Red + Bold | Safety breaches, system failure. |
| **HIGH** | Red | Direct blockers, failing checks. |
| **MEDIUM** | Yellow | Warnings, deferrals, non-critical risks. |
| **LOW** | Cyan | Information, minor hygiene suggestions. |
| **INFO** | Blue/Green | Success, progress, metadata. |
