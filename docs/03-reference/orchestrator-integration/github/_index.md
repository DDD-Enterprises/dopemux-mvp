---
id: orchestrator-github-index
title: GitHub Adapter Integration
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference for GitHub adapter methods driving pull request queueing and comments.
related_packets:
  - TP-DMX-ORCH-013
  - TP-DMX-ORCH-013-LIVE
---

# GitHub Adapter Reference

The GitHub adapter coordinates live pull request reads and comment mutations through the CLI and JSON adapters.

## Adapter Architecture
*   **Reads (T0/T1)**: Fetches PR checks, review states, and branch age using shell-escaped `gh` CLI subprocess calls.
*   **Writes (T5)**: Appends automated PR status comments gated behind the typed approval phrase.
*   **Fail-Closed Behavior**: If `gh` is unauthenticated or missing, the adapter rejects queries and falls back safely to in-memory `--pr` parsing.
