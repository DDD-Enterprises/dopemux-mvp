---
id: REPO_TARGET_MATRIX
title: Repo Target Matrix
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Repo Target Matrix (explanation) for dopemux documentation and developer
  workflows.
---
# Repo Target Matrix

## Pilot Repositories

| Repository | Criticality | Sophistication | Initial Tier | Purpose |
| :--- | :--- | :--- | :---: | :--- |
| `dopemux-mvp` | High | High | Tier 1 | Internal dogfooding and validation. |
| `dopemux-web` | Medium | Medium | Tier 0 | Low-risk volume testing. |
| `dopemux-cli` | Medium | High | Tier 1 | CLI-focused remediation. |

## Pilot Agent Environments

| Agent | Surface | Initial Tier | Scope |
| :--- | :--- | :---: | :--- |
| **Codex** | CLI / API | Tier 1 | Full remediation loops. |
| **Claude Code** | Terminal | Tier 1 | Verification and local fix loops. |
| **Copilot** | IDE | Tier 0 | Advice and plan inspection. |
| **Cursor** | Editor | Tier 0 | Contextual PR advice. |
| **Jules** | GitHub-Native | Tier 0 | Advisory-only autonomous tasks. |
