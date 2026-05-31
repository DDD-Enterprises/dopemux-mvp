---
id: orchestrator-plugins-index
title: Task-Orchestrator Declarative Plugins
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference for declarative plugin hooks and event hooks within the Task Orchestrator.
related_packets:
  - TP-DMX-ORCH-007
---

# Declarative Plugins & Hooks

This reference describes the declarative hook registry and safe execution boundaries used by Task Orchestrator plugins.

## Hook Events
Plugins register for discrete lifecycle events:
*   `SessionStart`: Fires at launcher startup, refreshing context.
*   `PostEdit`: Triggered after file writes, raising a nudge for linting.
*   `PreCommit`: Evaluates allowlist integrity before staging.
