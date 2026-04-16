---
id: UX_STYLE_GUIDE
title: Ux Style Guide
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Ux Style Guide (explanation) for dopemux documentation and developer workflows.
---
# UX Style Guide: Spaceage Operationalism

This guide is subordinate to [../branding/cli-ux-design-spec.md](../branding/cli-ux-design-spec.md).
Use it for supplemental framing only. If this guide conflicts with the CLI UX spec or runtime voice gates, the CLI UX spec and code win.

## Design Philosophy
The operator interface should feel like a futuristic cockpit: sleek, high-signal, and mission-focused. It must convey authority and technical precision without being distracting.

## Visual Elements

### 1. Status Chips
Use bracketed badges for primary states:
- `[  READY   ]` (Green)
- `[ BLOCKED  ]` (Red)
- `[ DEFERRED ]` (Yellow)
- `[SUPERVISED]` (Blue)

### 2. Tables
All multi-item data (blockers, role outputs, metrics) must be presented in clean, borders-inclusive tables for fast scanning.

### 3. Progress Indicators
Use step-based timelines for staged flows:
`[INTAKE] --> [PLAN] --> [EXECUTE] --> [VERIFY] --> [QUEUE]`

### 4. Typography and Alignment
- Use monospace alignment for all columns.
- Group related information into 'Summary Cards' separated by horizontal dividers.

## Rule: Color as Secondary
Color (ANSI) is used to highlight severity, but the text and symbols must always carry the primary meaning for accessibility and log-file readability.
