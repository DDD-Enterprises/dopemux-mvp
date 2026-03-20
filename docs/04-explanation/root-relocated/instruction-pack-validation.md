---
id: INSTRUCTION_PACK_VALIDATION
title: Instruction Pack Validation
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Instruction Pack Validation (explanation) for dopemux documentation and developer
  workflows.
---
# Instruction Pack Validation

## Overview
This document validates that all platform-specific adapters for the PR Merge Specialist adhere to the **Canonical Operator Contract**.

## Coverage Matrix

| Agent | Purpose | Rules | Sequence | Evidence | Escalation | Output |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Codex** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Claude Code** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Copilot** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Cursor** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Mistral Vibe** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Gemini** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Jules** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

## Validation Results
- **Codex**: AGENTS.md is concise; detailed workflow in SKILL.md.
- **Claude Code**: Subagent prompt maps all core mandates; hooks defined for pre-resolution checks.
- **Copilot**: Custom agent profile includes tool mapping and authoritative policy rule.
- **Cursor**: Project rule ensures persistent context; skill provides dynamic logic.
- **Mistral Vibe**: Agent instructions distinguish Plan vs Execute modes.
- **Gemini**: GEMINI.md tailored for CLI; Custom Commands for Code Assist.
- **Jules**: Task and API session templates provide autonomous guidance.

## Audit Trails
All artifacts emitted to `proof/pr_merge/instructions/`.
