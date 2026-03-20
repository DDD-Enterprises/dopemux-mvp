---
id: CREATION_MODE_RULES
title: Creation Mode Rules
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-14'
last_review: '2026-03-14'
next_review: '2026-06-12'
prelude: Rules defining the PR creation modes for pr-prep-specialist.
---
# Creation Mode Rules

The PR Prep Specialist supports four canonical creation modes. The mode is determined by the final validation decision and repo policy.

## Modes

1. **PACKAGE_ONLY**
   - **Trigger**: Policy forbids live creation, or the transport mechanism fails.
   - **Action**: Emit the PR payload and handoff bundle without communicating with the Git forge.

2. **CREATE_DRAFT_PR**
   - **Trigger**: Final prep decision is `DRAFT_RECOMMENDED`, high-risk flags exist, or ambiguity is medium (but non-blocking).
   - **Action**: Create a PR marked explicitly as "Draft".

3. **CREATE_FINAL_PR**
   - **Trigger**: Final prep decision is `CREATE_READY` and policy allows it.
   - **Action**: Create a standard (non-draft) PR.

4. **BLOCKED_NO_CREATE**
   - **Trigger**: Final prep decision is any `BLOCKED_*` state.
   - **Action**: Halt the creation pipeline. The handoff bundle will indicate that manual remediation is required. No PR is created.
