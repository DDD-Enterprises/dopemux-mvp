---
id: orchestrator-pr-readiness
title: Pull Request Queue & Readiness Workflow
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-28'
prelude: Reference detailing PR queue management, check verification, and readiness classification.
related_packets:
  - TP-DMX-ORCH-013
  - TP-DMX-ORCH-013-LIVE
---

# PR Queue & Readiness Workflow

This document details the PR readiness classifier which consumes live `gh` data feeds and maps open Pull Requests to structured safety states.

## PR Readiness States

The classifier maps each PR to one of the following states:
*   `MERGEABLE`: PR tests are passing, no merge conflicts are present, and valid proof is linked.
*   `BLOCKED`: Active blockers exist in the dependency tree.
*   `STALE`: PR branch age exceeds the policy threshold (e.g. 7 days without updates).
*   `DANGEROUS`: Changes contain pre-staged allowlist violations.
*   `NEEDS_MORE_EVIDENCE`: No validated `PROOF.json` file is found.
