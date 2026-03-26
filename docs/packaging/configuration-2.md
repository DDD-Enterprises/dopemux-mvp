---
id: CONFIGURATION
title: Configuration
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Configuration (explanation) for dopemux documentation and developer workflows.
---
# Configuration Guide

## Policy Surfaces
The PR Merge Specialist is configured via two primary surfaces:

1. **Environment**: Authentication via `gh` CLI.
2. **Policy Map**: (Coming Soon) A YAML-based policy for CI triage, command mapping, and resolution guards.

## Modes of Operation
- **Advisory (Default)**: Generates plans and artifacts but performs no mutations.
- **Live-Safe**: Performs safe mutations (metadata updates, local verification) but gates high-risk actions.
- **Dry-Run**: Equivalent to Advisory, used for pre-execution inspection.
