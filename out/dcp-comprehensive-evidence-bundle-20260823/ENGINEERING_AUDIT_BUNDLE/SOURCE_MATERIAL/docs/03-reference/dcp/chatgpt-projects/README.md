---
id: README
title: Readme
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-04'
last_review: '2026-06-04'
next_review: '2026-09-02'
prelude: Readme (reference) for dopemux documentation and developer workflows.
---
# ChatGPT Projects and Supervisor Setup Reference

This directory contains instructions and file-upload sets for configuring ChatGPT Projects as specialized agent workspaces (Supervisors).

> [!WARNING]
> **ChatGPT Projects are context docks, NOT source truth.**
> Uploaded files never outrank the repository runtime code, configuration, or tests. Do not treat ChatGPT Project memory/context as authoritative repository truth.

## Supervisor Projects Overview

We define four distinct ChatGPT Projects to support development and verification:

1. **[DCP Core Supervisor](file://[LOCAL_PATH_REDACTED] Generic, contract-locking coordinator. Focuses on core schemas, universal red lanes, and provenance metadata.
2. **[Dopemux Supervisor](file://[LOCAL_PATH_REDACTED] Dopemux-specific coordinator. Understands split-authority, PM writes, and task-orchestrator boundary limits.
3. **[dNh-CRM Supervisor](file://[LOCAL_PATH_REDACTED] CRM-specific coordinator. Operates in isolation from Dopemux; dNh paths and red lanes are treated as UNKNOWN until repo-truth TP completes.
4. **[DCP Packet Lab](file://[LOCAL_PATH_REDACTED] A temporary, ultra-lean workspace focused on a single active task packet + audit verification.

---

## Directory Contents

- **[Upload Sets](file://[LOCAL_PATH_REDACTED] Details the contents of each project's file-upload manifest.
- **[Project Instructions](file://[LOCAL_PATH_REDACTED] The exact prompt blocks to paste into the Custom Instructions for each project.

## Invariants and Safety
- **No Secrets**: Never upload credentials, keys, or `.env` files.
- **Auditor != Implementer**: No project may self-certify.
- **Read-Only**: Under v1, all supervisor interactions assume a read-only, dry-run posture.
