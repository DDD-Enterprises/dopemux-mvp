---
id: explanation-overview
title: Explanation Overview
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-19'
last_review: '2026-03-30'
next_review: '2026-06-30'
prelude: Understanding-oriented explanation index for architecture, design rationale, and system behavior.
---
# Explanation Overview

Explanation docs provide architecture and design context for why the system works the way it does.

## Core Explanation Areas

- `architecture/` for system-level design
- `technical-deep-dives/` for subsystem internals
- `design-decisions/` for implementation rationale
- `../90-adr/` for architecture decisions, including the PM-plane ADR index
- `../planes/pm/` for PM-plane authority, write-adjudication, and normalized tool-surface contracts

## Highlighted Active Topics

- [Memory And Persistence Deep Dive](technical-deep-dives/memory-and-persistence-deep-dive.md)
- [Workflow Kit Architecture](workflow-kit-architecture.md)
- [PR Merge Queue Orchestration](pr-merge-queue-orchestration.md)
- [Workflow Kit Transfer RFC](../91-rfc/workflow-kit-pickle-mechanics-transfer.md)

## Update Policy

Any PR that changes runtime behavior, architecture boundaries, or policy decisions must update explanation docs alongside reference/how-to docs.

`templates/skills/pr-docgen-sync/` enforces explanation coverage as a required document type.
