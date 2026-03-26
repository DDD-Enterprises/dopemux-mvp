---
id: explanation-overview
title: Explanation Overview
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-11'
last_review: '2026-03-26'
next_review: '2026-06-26'
prelude: Understanding-oriented explanation index for architecture, design rationale, and system behavior.
---
# Explanation Overview

Explanation docs provide architecture and design context for why the system works the way it does.

## Core Explanation Areas

- `architecture/` for system-level design
- `technical-deep-dives/` for subsystem internals
- `design-decisions/` for implementation rationale
- `pr-merge-queue-orchestration.md` for PR merge specialist queue-state and remediation rationale
- `../90-adr/` for architecture decisions, including the PM-plane ADR index
- `../planes/pm/` for PM-plane authority, write-adjudication, and normalized tool-surface contracts

## Update Policy

Any PR that changes runtime behavior, architecture boundaries, or policy decisions must update explanation docs alongside reference/how-to docs.

`templates/skills/pr-docgen-sync/` enforces explanation coverage as a required document type.
