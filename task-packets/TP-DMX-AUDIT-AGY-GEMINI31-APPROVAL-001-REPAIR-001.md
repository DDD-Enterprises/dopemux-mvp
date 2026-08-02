---
id: TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001
title: AGY Gemini 3.1 Pro High Model Authority Repair
type: explanation
owner: '@hu3mann'
author: '@codex'
date: '2026-07-31'
prelude: Repair PR 1165 to bind exact AGY Gemini model authority.
last_review: '2026-08-02'
next_review: '2026-10-31'
---
# TP-DMX-AUDIT-AGY-GEMINI31-APPROVAL-001-REPAIR-001

## Decision

Repair the existing draft PR #1165 in place.

## Objective

Repair PR #1165 so the canonical embedded-audit schema approves the exact AGY Gemini 3.1 Pro High selector only for auditor_tool=agy.

## Commit Topology

C1: repair commit (schema, docs, tests, packets)
C2: proof-only commit (proof/pr_merge/embedded-audit/pr-1165/**)

## Stop Conditions

- Exact AGY high selector absent
- gemini-3.1-pro-preview remains approved
- Audit verdict FAIL
- PR Steward not READY
